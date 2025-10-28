import sys

sys.path.append(".")

from urllib.parse import urlparse
from google import genai
from src.infrastructure.aws_storage import AWSStorage
from src.infrastructure.database import DataBase
from src.infrastructure.prompt import (
    SENTIMENT_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    get_sentiment_user_prompt,
    get_user_prompt,
    get_domain_user_prompt,
)
import json

from src.infrastructure.models import (
    Brand_Metrics,
    Citations,
    Output_Reports,
    SentimentBody,
    Sentiments,
    Domain_Model,
)
import markdown2
from markdownify import markdownify as md
from src.config import config
from google.genai.types import GenerateContentConfig
import logging
from selectolax.parser import HTMLParser
from src.infrastructure.click_house import ClickHouse
from dateparser import parse


class LLMService:
    def __init__(
        self,
        process_id: str,
        brand_report_id: str,
        date: str,
        model: str,
        brand: str,
        s3_key: str,
        logger: logging.Logger,
    ) -> None:
        # report ids
        self.process_id = process_id
        self.brand_report_id = brand_report_id
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
        # initialise db
        self.database = DataBase()
        # initialise clickhouse
        self.clickhouse = ClickHouse()
        # initialise logger
        self.logger = logger

    def clean_markdown(self, content: str) -> str:
        self.logger.info("Cleaning Content")
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

    def extract_brand_mentions(self):
        logging.info("- Starting the LLM prompt parsing system")
        parsed_results = []
        response = self.client.models.generate_content(
            model=config.MODEL_NAME,
            contents=get_user_prompt(self.clean_content),
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[Brand_Metrics],
                system_instruction=[
                    SYSTEM_PROMPT,
                ],
            ),
        )
        # validating and saving to clickhouse
        results = json.loads(response.model_dump_json())
        results = response.parsed if response else []
        if not isinstance(results, list):
            return None
        for result in results:
            parsed_results.append(
                {
                    "brand_report_id": self.brand_report_id,
                    "brand": result.brand,
                    "mention_count": result.mention_count,
                    "position": result.position,
                    "date": parse(self.date),
                    "model": self.model,
                }
            )
        self.clickhouse.insert_into_db(parsed_results)

    def save_brand_report_output(self):
        """Get the brand report outputs"""
        self.logger.info("Getting and saving the brand report")
        output_report = Output_Reports(
            id=self.process_id,
            brand_report_id=self.brand_report_id,
            date=self.date,
            model=self.model,
            snapshot=self.image_key,
            markdown=self.text_key,
        )

        # saving the output report
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

        # Validate sentiments
        sentiments = response.parsed if response.parsed else []
        if not isinstance(sentiments, list):
            return None
        for idx, sentiment in enumerate(sentiments):
            parsed_sentiments.append(
                Sentiments(
                    id=f"{self.process_id}-{idx}",
                    brand_report_id=self.brand_report_id,
                    date=self.date,
                    model=self.model,
                    brand=sentiment.brand,
                    brand_model=sentiment.brand_model,
                    positive_phrases=sentiment.positive_phrases,
                    negative_phrases=sentiment.negative_phrases,
                )
            )

        # save the sentiments
        self.database.save_sentiments(parsed_sentiments)
        return None

    def get_citations(self):
        """Convert markdown to html and extract links"""
        self.logger.info("Getting the citations")
        citations = []
        html_content = markdown2.markdown(self.clean_content)
        html = HTMLParser(html_content)
        link_nodes = html.css("a")
        for i, link_node in enumerate(link_nodes):
            link = link_node.css_first("a")
            if not link:
                continue
            title = link.text(separator=" ")
            link = link.attributes.get("href")
            domain = urlparse(link).netloc if link else None
            parsed = urlparse(link)
            clean_url = clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            citation = Citations(
                id=f"{self.process_id}-{i}",
                brand_report_id=self.brand_report_id,
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
        self.database.save_citations(citations)

    def get_domain_competitor(self, prompt_urls: list[str], domain: str):
        """Get the competitors of any domain among a list of urls"""
        self.logger.info("Getting Competitor domain(s) with LLM")
        response = self.client.models.generate_content(
            model=config.MODEL_NAME,
            contents=get_domain_user_prompt(prompt_urls, domain),
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[Domain_Model],
            ),
        )

        # Validate sentiments
        results = response.parsed if response.parsed else []
        return results

    def main(self) -> None:
        """Start the whole parser workflow"""
        self.logger.info("Starting the whole workflow")
        # download the content from s3

        self.logger.info("Downloaiding content from S3")
        content = self.storage.get_file_content(self.text_key)
        if not content:
            return None

        # clean the content
        self.clean_content = self.clean_markdown(content)

        # get and save parsed data
        self.extract_brand_mentions()
        self.get_citations()
        self.get_sentiments()
        self.save_brand_report_output()


# if __name__ == "__main__":
#     llm_service = LLMService(
#         "br_12345", "2025-10-05", "Chatgpt", "Nike", "chatgpt/1758754781"
#     )
#     llm_service.main()
