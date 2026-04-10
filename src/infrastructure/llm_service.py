import sys
import re


sys.path.append(".")

import logging
import time
import markdown2
from markdownify import markdownify as md
from dateparser import parse
from google import genai
from google.genai.types import GenerateContentConfig

from src.config import config
from src.infrastructure.shared import to_canonical, extract_clean_links
from src.infrastructure.aws_storage import AWSStorage
from src.infrastructure.click_house import ClickHouse
from src.infrastructure.database import DataBase
from src.infrastructure.models import (
    Citations,
    Output_Reports,
    SentimentBody,
    Sentiments,
    Token_Reports,
    Brand_List,
)
from src.infrastructure.prompt import (
    SENTIMENT_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    get_sentiment_user_prompt,
    get_user_prompt,
)


class LLMService:
    def __init__(
        self,
        process_id: str,
        brand_report_id: str,
        prompt_id: str,
        date: str,
        model: str,
        brand: str,
        s3_key: str,
        logger: logging.Logger,
        save_to_db: bool = True,
    ) -> None:
        # report ids
        self.process_id = process_id
        self.brand_report_id = brand_report_id
        self.prompt_id = prompt_id
        self.date = date
        self.model = model
        self.brand = brand
        self.s3_key = s3_key
        self.text_key = f"{s3_key}/output.txt"
        self.image_key = f"{s3_key}/screenshot.png"

        # initialise others
        self.bucket = config.BUCKET_NAME
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.storage = AWSStorage()
        self.content = ""
        self.clean_content = ""
        self.google_citations = ""
        # initialise db
        self.database = DataBase()
        # initialise clickhouse
        self.clickhouse = ClickHouse()
        # initialise logger
        self.logger = logger
        self.save_to_db = save_to_db
        print(config.MODEL_NAME)

    def count_word_with_apostrophe(self, word: str, content: str):
        pattern = r"\b" + re.escape(word) + r"(?:'s)?\b"
        return len(re.findall(pattern, content, flags=re.IGNORECASE))

    def remove_links(self, content: str | None = None):
        """
        Remove all URLs from text
        """
        # Pattern to match URLs (http, https, ftp, www, and common domain patterns)
        url_pattern = r"https?://\S+|www\.\S+|ftp://\S+"

        # Remove URLs
        text_without_urls = re.sub(
            url_pattern, "", content if content else self.clean_content
        )

        # Clean up extra whitespace that might be left behind
        text_without_urls = re.sub(r"\s+", " ", text_without_urls).strip()
        return text_without_urls

    def clean_markdown(self, content: str | None = None) -> str:
        self.logger.info("Cleaning Content")
        if not self.content:
            return ""
        html_content = markdown2.markdown(content if content else self.content)
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

    def extract_brand_mentions(self):
        logging.info("- Starting the LLM prompt parsing system")
        parsed_results = []
        if self.model.lower() == "google":
            content = self.content.split("* []")[0]
            content = self.remove_links(self.clean_markdown(content))
        else:
            content = self.remove_links()

        prompt = self.database.get_prompt(self.prompt_id)
        if not prompt:
            return None
        response = self.client.models.generate_content(
            model=config.MODEL_NAME,
            contents=get_user_prompt(content, prompt),
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[Brand_List],
                system_instruction=[
                    SYSTEM_PROMPT,
                ],
            ),
        )
        # Access the usage metadata
        usage = response.usage_metadata
        if usage:
            token_data = Token_Reports(
                id=str(time.time_ns()),
                brand_report_id=self.brand_report_id,
                prompt_id=self.prompt_id,
                date=self.date,
                model=self.model,
                total_token_count=getattr(usage, "total_token_count", 0),
                prompt_token_count=getattr(usage, "prompt_token_count", 0),
                output_token_count=getattr(usage, "candidates_token_count", 0),
                action="get_brand_mentions",
            )
            if self.save_to_db:
                self.database.save_token_usage(token_data)

        dedup = {}
        results = response.parsed if response else []

        if not isinstance(results, list):
            return None

        content_lower = content.lower()

        # STEP 1: collect unique brands with index
        for r in results:
            raw_brand = r.brand.lower().strip()
            brand_clean = to_canonical(raw_brand)
            if brand_clean.endswith("."):
                brand_clean = brand_clean.rstrip(".")
            if brand_clean in dedup:
                continue

            index = content_lower.find(brand_clean)
            dedup[brand_clean] = index if index != -1 else None

        # STEP 2: build ordered list (ONLY brands found in content)
        brand_positions = [
            (brand, idx) for brand, idx in dedup.items() if idx is not None
        ]

        brand_positions.sort(key=lambda x: x[1])

        # STEP 3: ranking
        rank_map = {brand: i + 1 for i, (brand, _) in enumerate(brand_positions)}

        # STEP 4: build final results (preserve dict order)
        parsed_results = []

        for brand, index in dedup.items():
            mention_count = self.count_word_with_apostrophe(brand, content)
            if mention_count == 0:
                continue
            if not (rank_map.get(brand)):
                continue
            parsed_results.append(
                {
                    "brand_report_id": self.brand_report_id,
                    "prompt_id": self.prompt_id,
                    "brand": brand.title(),
                    "mention_count": mention_count,
                    "position": rank_map.get(brand),  # None if not found
                    "date": parse(self.date),
                    "model": self.model,
                    "s3_key": self.text_key,
                }
            )

        # Save to database
        if self.save_to_db:
            self.clickhouse.insert_into_db(parsed_results)

    def save_brand_report_output(self):
        """Get the brand report outputs"""
        self.logger.info("Getting and saving the brand report")
        output_report = Output_Reports(
            id=self.process_id,
            brand_report_id=self.brand_report_id,
            prompt_id=self.prompt_id,
            date=self.date,
            model=self.model,
            snapshot=self.image_key,
            markdown=self.text_key,
        )

        # saving the output report
        if self.save_to_db:
            self.database.save_output_reports(output_report)

    def get_sentiments(self):
        """Get the sentiment with LLM"""
        self.logger.info("Getting Sentiments with LLM")
        parsed_sentiments = []
        response = self.client.models.generate_content(
            model=config.MODEL_NAME,
            contents=get_sentiment_user_prompt(self.clean_content),
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[SentimentBody],
                system_instruction=[
                    SENTIMENT_SYSTEM_PROMPT,
                ],
            ),
        )
        # Access the usage metadata
        usage = response.usage_metadata
        if usage:
            token_data = Token_Reports(
                id=str(time.time_ns()),
                brand_report_id=self.brand_report_id,
                prompt_id=self.prompt_id,
                date=self.date,
                model=self.model,
                total_token_count=getattr(usage, "total_token_count", 0),
                prompt_token_count=getattr(usage, "prompt_token_count", 0),
                output_token_count=getattr(usage, "candidates_token_count", 0),
                action="get_sentiments",
            )
            self.database.save_token_usage(token_data)

        # Validate sentiments
        dedup = set()
        sentiments = response.parsed if response.parsed else []
        if not isinstance(sentiments, list):
            return None

        for idx, sentiment in enumerate(sentiments):
            brand_name = sentiment.brand.strip().lower()
            if brand_name in dedup:
                continue

            dedup.add(brand_name)
            parsed_sentiments.append(
                Sentiments(
                    id=f"{self.process_id}-{idx}",
                    brand_report_id=self.brand_report_id,
                    prompt_id=self.prompt_id,
                    date=self.date,
                    model=self.model,
                    brand=sentiment.brand,
                    brand_model=sentiment.brand_model,
                    positive_phrases=sentiment.positive_phrases,
                    negative_phrases=sentiment.negative_phrases,
                )
            )

        # save the sentiments
        if self.save_to_db:
            self.database.save_sentiments(parsed_sentiments)
        return None

    def get_citations(self):
        """Build and store citations"""

        self.logger.info("Getting the citations")

        links = extract_clean_links(
            content=self.content if self.content else "",
            model=self.model,
            google_citations=self.google_citations,
        )

        citations = []

        for rank, link in enumerate(links, start=1):
            citation = Citations(
                id=f"{self.process_id}-{rank}",
                brand_report_id=self.brand_report_id,
                prompt_id=self.prompt_id,
                date=self.date,
                model=self.model,
                brand=self.brand,
                rank=rank,
                title=link["title"],
                domain=link["domain"],
                norm_url=link["url"],
                s3_key=self.s3_key,
            )
            citations.append(citation)

        print(f"Found -> {len(citations)} citations")

        if self.save_to_db:
            self.database.save_citations(citations)

        return citations

    def main(self) -> None:
        """Start the whole parser workflow"""
        self.logger.info("Starting the whole workflow")
        # download the content from s3

        self.logger.info("Downloaiding content from S3")
        self.content = self.storage.get_file_content(self.text_key)
        if not self.content:
            return None

        # clean the content
        self.clean_content = self.clean_markdown()

        # get and save parsed data
        self.extract_brand_mentions()
        self.get_citations()
        self.get_sentiments()
        self.save_brand_report_output()


if __name__ == "__main__":
    llm_service = LLMService(
        save_to_db=False,
        process_id=str(time.time_ns()),
        brand_report_id="br_12345",
        prompt_id="c05f8db6-f1c2-4457-b990-9aac8bc0551e",
        date="2025-10-05",
        model="chatgpt",
        brand="",
        s3_key="chatgpt/chatgpt-45fb90b8-0fd7-4b8d-ae56-f91c97a3ea18-c05f8db6-f1c2-4457-b990-9aac8bc0551e-1775715300",
        logger=logging.Logger(name="TESTING: "),
    )
    llm_service.main()
