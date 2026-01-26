import sys
import re

sys.path.append(".")

import json
import logging
from urllib.parse import urlparse
import time
import markdown2
from markdownify import markdownify as md
from dateparser import parse
from google import genai
from google.genai.types import GenerateContentConfig
from selectolax.parser import HTMLParser

from src.config import config
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
        """
        Count occurrences of a word in text, including the word with 's
        """
        # \b ensures we match whole words only
        pattern = r"\b" + re.escape(word) + r"('s)?\b"

        # Find all matches (case-insensitive)
        matches = re.findall(pattern, content, re.IGNORECASE)
        return len(matches)

    def remove_links(self):
        """
        Remove all URLs from text
        """
        # Pattern to match URLs (http, https, ftp, www, and common domain patterns)
        url_pattern = r"https?://\S+|www\.\S+|ftp://\S+"

        # Remove URLs
        text_without_urls = re.sub(url_pattern, "", self.clean_content)

        # Clean up extra whitespace that might be left behind
        text_without_urls = re.sub(r"\s+", " ", text_without_urls).strip()
        return text_without_urls

    def google_content_splitter(self):
        """
        Converts markdown to HTML and separates citations.
        """
        # Split content and citations at "*   []"
        citation_pattern = r"\*\s+\[\]"
        if not self.content:
            return None
        parts = re.split(citation_pattern, self.content, maxsplit=1)

        self.content = parts[0].strip()
        self.google_citations = parts[1].strip() if len(parts) > 1 else ""

    def clean_markdown(self) -> str:
        self.logger.info("Cleaning Content")
        if not self.content:
            return ""
        html_content = markdown2.markdown(self.content)
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
        content = self.remove_links()
        if self.model.lower() == "google":
            content = content.split("Show all")[0]

        response = self.client.models.generate_content(
            model=config.MODEL_NAME,
            contents=get_user_prompt(content),
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

        # validating
        results = json.loads(response.model_dump_json())
        results = response.parsed if response else []
        if not isinstance(results, list):
            return None

        # putting it for the brand metrics
        for brand in results:
            brand_mention_count = self.count_word_with_apostrophe(brand.brand, content)
            parsed_results.append(
                {
                    "brand_report_id": self.brand_report_id,
                    "prompt_id": self.prompt_id,
                    "brand": brand.brand,
                    "mention_count": brand_mention_count,
                    "position": brand.position,
                    "date": parse(self.date),
                    "model": self.model,
                }
            )

        # Save to database
        print(parsed_results)
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
        sentiments = response.parsed if response.parsed else []

        print(sentiments)
        if not isinstance(sentiments, list):
            return None
        for idx, sentiment in enumerate(sentiments):
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
        """Convert markdown to html and extract links"""
        self.logger.info("Getting the citations")
        citations = []
        if self.model == "Google":
            html_content = (
                markdown2.markdown(f"{self.content} {self.google_citations}")
                if self.content
                else ""
            )
        else:
            html_content = markdown2.markdown(self.content) if self.content else ""
        html = HTMLParser(html_content)
        link_nodes = html.css("a")
        for i, link_node in enumerate(link_nodes):
            link = link_node.css_first("a")
            if not link:
                continue
            title = link.text(separator=" ")
            link = link.attributes.get("href")
            domain = urlparse(link).netloc if link else None
            if domain == "www.google.com":
                continue
            parsed = urlparse(link)
            clean_url = clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            citation = Citations(
                id=f"{self.process_id}-{i}",
                brand_report_id=self.brand_report_id,
                prompt_id=self.prompt_id,
                date=self.date,
                model=self.model,
                brand=self.brand,
                rank=i + 1,
                title=title,
                domain=domain,
                norm_url=clean_url,
            )
            citations.append(citation)

        print(f"Found -> {len(citations)} citations")
        # once citations have been validated then save
        if self.save_to_db:
            self.database.save_citations(citations)

    def main(self) -> None:
        """Start the whole parser workflow"""
        self.logger.info("Starting the whole workflow")
        # download the content from s3

        self.logger.info("Downloaiding content from S3")
        self.content = self.storage.get_file_content(self.text_key)
        if not self.content:
            return None

        # clean the content
        if self.model == "Google":
            self.google_content_splitter()
        self.clean_content = self.clean_markdown()

        # get and save parsed data
        self.extract_brand_mentions()
        self.get_citations()
        self.get_sentiments()
        self.save_brand_report_output()


#
# if __name__ == "__main__":
#     llm_service = LLMService(
#         save_to_db=False,
#         process_id=str(time.time_ns()),
#         brand_report_id="br_12345",
#         prompt_id="pt_12345",
#         date="2025-10-05",
#         model="Google",
#         brand="Nike",
#         s3_key="google/google-brand_report_20-Prompt_202-1769104643",
#         logger=logging.Logger(name="TESTING: "),
#     )
#     llm_service.main()
