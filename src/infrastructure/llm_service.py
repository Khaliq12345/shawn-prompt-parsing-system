from google import genai
from abc import ABC
from contextlib import ContextDecorator
from src.infrastructure.aws_storage import AWSStorageAsync
from src.infrastructure.database import save_brand_mention
from src.infrastructure.prompt import SYSTEM_PROMPT, USER_PROMPT
from src.infrastructure.redis_service import AsyncRedisBase
from src.infrastructure.models import BrandMention, BrandMentionDB
import markdown2
from markdownify import markdownify as md
from src.config import config
from google.genai.types import GenerateContentConfig
from datetime import datetime


def clean_markdown(content: str) -> str:
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


def use_prompt(clean_content: str) -> str:
    return f"""
        {USER_PROMPT}
        Here is the text :
        {clean_content}
        """


class LLMService(ContextDecorator, ABC):
    def __init__(
        self,
        prompt_id: str,
    ) -> None:
        self.prompt_id = prompt_id
        self.bucket = config.BUCKET_NAME
        self.redis = AsyncRedisBase(prompt_id)
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.storage = AWSStorageAsync(self.bucket)

    async def get_brand_mentions(self, content: str):
        try:
            results = []
            await self.redis.set_log("- Starting the LLM prompt parsing system")
            await self.redis.set_log("- Cleaning Markdown ...")
            clean_content = clean_markdown(content)
            await self.redis.set_log("- Markdown Successfully Cleaned ")
            await self.redis.set_log("- Now Generationg Content ...")
            response = self.client.models.generate_content(
                model=config.MODEL_NAME,
                contents=use_prompt(clean_content),
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=list[BrandMention],
                    system_instruction=[
                        SYSTEM_PROMPT,
                    ],
                ),
            )
            results = response.parsed if response else []
            await self.redis.set_log("- Successfully Generated Content")
            await self.redis.set_log("- Now Saving in DB ...")
            for i, result in enumerate(results):
                item = BrandMentionDB(
                    prompt_id=self.prompt_id,
                    brand_name=result.brand_name,
                    mention_count=result.mention_count,
                    date=datetime.now(),
                )
                await save_brand_mention(item)
                await self.redis.set_log(
                    f"- Already saved {i + 1} item(s) on {len(results)}"
                )
            await self.redis.set_log("- Process Successfully Ended")
            return results
        except Exception as e:
            await self.redis.set_log(f"- Error While Generationg Content : {e}")
            return []
