from google import genai
from abc import ABC
from contextlib import ContextDecorator
from typing import List
from src.infrastructure.aws_storage import AWSStorageAsync
from src.infrastructure.prompt import SYSTEM_PROMPT, USER_PROMPT
from src.infrastructure.redis_service import AsyncRedisBase
from src.infrastructure.models import BrandMention
import markdown2
from markdownify import markdownify as md
from src.config import config
from google.genai.types import GenerateContentConfig


def clean_markdown(content: str) -> str:
    html_content = markdown2.markdown(content)
    print(f"html_content : {html_content}")
    cleaned_markdown = md(html_content)  # , strip=["img"])
    print(f"cleaned_markdown : {cleaned_markdown}")
    return cleaned_markdown.strip()


class LLMService(ContextDecorator, ABC):
    def __init__(
        self,
        process_id: str,
    ) -> None:
        self.process_id = process_id
        self.bucket = config.BUCKET_NAME
        self.redis = AsyncRedisBase(process_id)
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.storage = AWSStorageAsync(self.bucket)

    async def get_brand_mentions(self, content: str) -> List[BrandMention]:
        result = []
        clean_content = clean_markdown(content)
        response = self.client.models.generate_content(
            model=config.MODEL_NAME,
            contents=f"""
                {USER_PROMPT}
                Here is the text :
                {clean_content}
                """,
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[BrandMention],
                system_instruction=[
                    SYSTEM_PROMPT,
                ],
            ),
        )
        result: list[BrandMention] = response.parsed if response else []
        return result
