from google import genai
from abc import ABC
from contextlib import ContextDecorator
from typing import List
from src.infrastructure.redis_service import RedisBase
# from src.infrastructure.aws_storage import AWSStorage
from src.infrastructure.models import BrandMention
import re
from src.config import config
from google.genai.types import GenerateContentConfig


def clean_markdown(content: str) -> str:
    cleaned = re.sub(r"!\[.*?\]\(.*?\)", "", content)
    return cleaned.strip()


class LLMService(ContextDecorator, ABC):
    def __init__(
        self,
        process_id: str,
    ) -> None:
        self.process_id = process_id
        self.bucket = "prompt-parsing"
        self.redis = RedisBase(process_id)
        # self.storage = AWSStorage(self.bucket)
        self.uid = self.process_id.split("_")[1]

    def get_brand_mentions(self, content: str) -> List[BrandMention]:
        result = []
        clean_content = clean_markdown(content)
        print(f"api key : {config.GEMINI_API_KEY}")
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
                Count how many times each brand (with aliases) is mentioned in the following text.
                Apply the rules:
                Count all mentions of the brand and its aliases.
                Case-insensitive, diacritics-insensitive.
                Scope: main answer text only, exclude links/citations.
                Output the total count per brand as an integer.
                Example Input:
                "Adidas Adizero Evo SL and the Adidas Ultraboost Light are both excellent.
                The Nike Pegasus is also great."
                Example Output:
                {{
                "Adidas": 2,
                "Nike": 1,
                "Puma": 10
                }}
                Here is the text :
                {clean_content}
                """,
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[BrandMention],
                system_instruction=[
                    """
                    You are an assistant that calculates Brand Mentions in responses.
                    Follow these rules carefully:
                    Definition
                    Brand Mentions = Total number of times a brand (including aliases) appears across all main answer texts within the selected time window.
                    Unit/Type: Integer (count).
                    Formula
                    Brand Mentions = SUM(occurrences of brand in the content)
                    Rules
                    Aliases count toward the main brand -
                    Example:
                    Adidas → {Adizero, Ultraboost, Adizero Evo SL, Adidas Ultraboost Light}
                    Nike → {Pegasus, Invincible}
                    Scope: Count only the main answer text, exclude citations, footnotes, and links.
                    Case-insensitive: Treat Adidas, adidas, ADIDAS as the same.
                    Diacritics-insensitive: Treat Adìdas = Adidas.
                    Include all variants and repetitions. Each occurrence counts separately.
                    Common Errors to Avoid
                    ❌ Missing alias mapping (e.g., “Ultraboost” not counted as Adidas).
                    ❌ Counting in citations, sources, or links.
                    ❌ Case-sensitive counting (e.g., ignoring adidas).
                    ❌ Deduplicating mentions (we count every mention, not just unique ones).
                    ❌ Ignoring diacritics (e.g., “Adìdas” should be counted).                  
                    """,
                ],
            ),
        )
        result: list[BrandMention] = response.parsed if response else []
        return result
