import sys
from typing import Optional

sys.path.append(".")
import asyncio
from google import genai
from abc import ABC
from contextlib import ContextDecorator
from src.infrastructure.aws_storage import AWSStorageAsync
from src.infrastructure.database import (
    save_brand_mention,
    update_llm_process_status,
)
from src.infrastructure.prompt import SYSTEM_PROMPT, get_user_prompt
from src.infrastructure.redis_service import AsyncRedisBase, RedisLogHandler
from src.infrastructure.models import BrandModel, BrandDB
import markdown2
from markdownify import markdownify as md
from src.config import config
from google.genai.types import GenerateContentConfig
from datetime import datetime
import logging


class LLMService(ContextDecorator, ABC):
    def __init__(self, prompt_id: str, process_id: str) -> None:
        self.prompt_id = prompt_id
        self.process_id = process_id
        self.bucket = config.BUCKET_NAME
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.storage = AWSStorageAsync(self.bucket)
        redis_logger = AsyncRedisBase(process_id)
        # Setup logger
        self.logger = logging.getLogger(f"{__name__}")
        self.logger.setLevel(logging.INFO)
        # Redis log handler
        self.redis_handler = RedisLogHandler(redis_logger)
        self.redis_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
        )
        self.logger.addHandler(self.redis_handler)

    def clean_markdown(self, content: str) -> str:
        html_content = markdown2.markdown(content)
        cleaned_markdown = md(
            html_content,
            strip=[
                "img",
                "picture",
                "figure",
                "source",
                "svg",
                "object",
                "embed",
                "iframe",
            ],
        )
        return cleaned_markdown.strip()

    async def save_mentions_to_db(self, results: list[BrandModel]):
        """Save the brand return by LLM into a database"""
        responses: list[BrandDB] = [
            BrandDB(
                prompt_id=self.prompt_id,
                process_id=self.process_id,
                brand_name=result.brand_name,
                mention_count=result.mention_count,
                position=result.position,
                date=datetime.now(),
            )
            for result in results
        ]
        await save_brand_mention(responses)
        self.logger.info(f"- Successfully saved {len(results)} item(s)")

    async def extract_brand_mentions(self, content: str):
        results = []
        self.logger.info(
            "- Starting the LLM prompt parsing system \n - Cleaning Markdown ..."
        )
        clean_content = self.clean_markdown(content)
        self.logger.info(
            "- Markdown Successfully Cleaned \n - Now Generationg Content ..."
        )
        response = await self.client.aio.models.generate_content(
            model=config.MODEL_NAME,
            contents=get_user_prompt(clean_content),
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[BrandModel],
                system_instruction=[
                    SYSTEM_PROMPT,
                ],
            ),
        )
        results = response.parsed if response else []
        self.logger.info("- Successfully Generated Content \n - Now Saving in DB ...")
        return results

    async def main(self, s3_key: str) -> Optional[list[BrandModel]]:
        """Download content from s3 and send to LLM for brand extraction"""
        outputs = []
        try:
            await update_llm_process_status(self.process_id, self.prompt_id, "running")
            content = await self.storage.get_file_content(s3_key)
            if not content:
                return None
            clean_content = self.clean_markdown(content)
            outputs = await self.extract_brand_mentions(clean_content)
            if isinstance(outputs, list):
                await self.save_mentions_to_db(outputs)
            await update_llm_process_status(self.process_id, self.prompt_id, "success")
        except Exception as e:
            self.logger.error(f"- Error While Generationg Content : {e}")
            await update_llm_process_status(self.process_id, self.prompt_id, "failed")
        finally:
            self.logger.removeHandler(self.redis_handler)


if __name__ == "__main__":

    async def main():
        s3_key = "chatgpt/1756805263/output.txt"
        llm_service = LLMService("prompt_12345", "process_12345")
        output = await llm_service.main(s3_key)
        print(output)

    asyncio.run(main())
