import sys
from typing import Optional

sys.path.append(".")
import asyncio
from google import genai
from abc import ABC
from contextlib import ContextDecorator
from src.infrastructure.aws_storage import AWSStorage
from src.infrastructure.database import DataBase
from src.infrastructure.prompt import SYSTEM_PROMPT, get_user_prompt
from src.infrastructure.redis_service import AsyncRedisBase, RedisLogHandler
from src.infrastructure.models import Citations
from sqlmodel import select
import markdown2
from markdownify import markdownify as md
from src.config import config
from google.genai.types import GenerateContentConfig
from datetime import datetime
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class LLMService(ContextDecorator, ABC):
    def __init__(self, brand_report_id: str, date: str, model: str, brand: str) -> None:
        # report ids
        self.brand_report_id = brand_report_id
        self.date = date
        self.model = model
        self.brand = brand
        # initialise others
        self.bucket = config.BUCKET_NAME
        # self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.storage = AWSStorage(self.bucket)
        # redis
        # # redis_logger = Asyncis_logger)
        # self.redis_handler.setFormatter(
        #     logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
        # )
        # self.logger.addHandler(self.redis_handler)
        # content
        self.content = ""
        # initialise db
        self.database = DataBase()

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

    

    def save_citation(self, citations: list[Citations]):
        """Sauvegarder les citations dans la base de données"""
        for cit in citations:
            self.database.session.add(cit)
        self.database.session.commit()

    def main(self, s3_key: str) -> Optional[list[Citations]]:
        """Télécharger le contenu depuis S3, nettoyer, extraire liens/titres et sauvegarder"""
        content = self.storage.get_file_content(s3_key)
        if not content:
            return None
        clean_content = self.clean_markdown(content)
        html_content = markdown2.markdown(clean_content)
        selector = BeautifulSoup(html_content, 'html.parser')
        links = [a.get('href') for a in selector.select('a') if a.get('href')]
        titles = [h.get_text() for h in selector.select('h1, h2, h3, h4, h5, h6')]
        citations = []
        for i, link in enumerate(links):
            domain = urlparse(link).netloc if link else None
            title = titles[i] if i < len(titles) else None
            citation = Citations(
                brand_report_id=self.brand_report_id,
                date=self.date,
                model=self.model,
                brand=self.brand,
                rank=i + 1,
                title=title,
                domain=domain,
                norm_url=link
            )
            citations.append(citation)
        self.save_citation(citations)
        return citations

    # async def save_mentions_to_db(self, results: list[BrandModel]):
    #     """Save the brand return by LLM into a database"""
    #     responses: list[BrandDB] = [
    #         BrandDB(
    #             prompt_id=self.prompt_id,
    #             process_id=self.process_id,
    #             brand_name=result.brand_name,
    #             mention_count=result.mention_count,
    #             position=result.position,
    #             date=datetime.now(),
    #         )
    #         for result in results
    #     ]
    #     await save_brand_mention(responses)
    #     self.logger.info(f"- Successfully saved {len(results)} item(s)")

    # async def extract_brand_mentions(self, content: str):
    #     results = []
    #     self.logger.info(
    #         "- Starting the LLM prompt parsing system \n - Cleaning Markdown ..."
    #     )
    #     clean_content = self.clean_markdown(content)
    #     self.logger.info(
    #         "- Markdown Successfully Cleaned \n - Now Generationg Content ..."
    #     )
    #     response = await self.client.aio.models.generate_content(
    #         model=config.MODEL_NAME,
    #         contents=get_user_prompt(clean_content),
    #         config=GenerateContentConfig(
    #             response_mime_type="application/json",
    #             response_schema=list[BrandModel],
    #             system_instruction=[
    #                 SYSTEM_PROMPT,
    #             ],
    #         ),
    #     )
    #     results = response.parsed if response else []
    #     self.logger.info("- Successfully Generated Content \n - Now Saving in DB ...")
    #     return results

    # async def main(self, s3_key: str) -> Optional[list[BrandModel]]:
    #     """Download content from s3 and send to LLM for brand extraction"""
    #     outputs = []
    #     try:
    #         await update_llm_process_status(self.process_id, self.prompt_id, "running")
    #         content = await self.storage.get_file_content(s3_key)
    #         if not content:
    #             return None
    #         clean_content = self.clean_markdown(content)
    #         outputs = await self.extract_brand_mentions(clean_content)
    #         if isinstance(outputs, list):
    #             await self.save_mentions_to_db(outputs)
    #         await update_llm_process_status(self.process_id, self.prompt_id, "success")
    #     except Exception as e:
    #         self.logger.error(f"- Error While Generationg Content : {e}")
    #         await update_llm_process_status(self.process_id, self.prompt_id, "failed")
    #     finally:
    #         self.logger.removeHandler(self.redis_handler)


if __name__ == "__main__":
    s3_key = "perplexity/1758452292/output.txt"
    llm_service = LLMService("prompt_12345", "2023-01-01", "model_name", "brand_name")
    output = llm_service.main(s3_key)
    if output:
        for cit in output:
            print(f"Citation: rank={cit.rank}, title={cit.title}, domain={cit.domain}, url={cit.norm_url}")
    else:
        print("No citations found or content not available.")
    print("Checking database...")
    stmt = select(Citations).where(Citations.brand_report_id == "prompt_12345")
    db_citations = llm_service.database.session.exec(stmt).all()
    print(f"Found {len(db_citations)} citations in database.")
    for cit in db_citations:
        print(f"DB Citation: id={cit.id}, rank={cit.rank}, title={cit.title}, domain={cit.domain}, url={cit.norm_url}")
