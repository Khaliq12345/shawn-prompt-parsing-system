from datetime import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from src.infrastructure import aws_storage
from src.infrastructure.aws_storage import AWSStorage
from src.config.config import BUCKET_NAME
import dateparser
from src.api.dependencies import database_depends
import re
from collections import Counter
from urllib.parse import urlparse

router = APIRouter(
    prefix="/report/sources/domain",
    responses={404: {"description": "Not found"}},
)


def get_date() -> str:
    """Get date"""
    date_node = dateparser.parse("7 days Ago")
    if date_node:
        return date_node.strftime("%Y-%m-%d %H:%M:%S")
    return ""


def common_parameters(
    brand_report_id: str,
    domain: str,
    model: str = "all",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    if not start_date:
        start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not end_date:
        end_date = get_date()
    return {
        "brand_report_id": brand_report_id,
        "start_date": start_date,
        "end_date": end_date,
        "model": model,
        "domain": domain,
    }


def extract_url_data(text):
    """
    Extract all URLs from text and return normalized URL, count, and main domain.
    """
    # Regex for http(s) URLs
    url_pattern = r'https?://[^\s"\'<>]+'
    urls = re.findall(url_pattern, text, flags=re.IGNORECASE)

    # Count how many times each URL appears
    url_counts = Counter(urls)

    results = []
    for url, count in url_counts.items():
        clean_url = url.replace(")", "")
        parsed = urlparse(clean_url)
        domain_parts = parsed.netloc.lower().split(".")

        # Extract the main domain (e.g., nike.com from shop.nike.com)
        if len(domain_parts) >= 2:
            domain = ".".join(domain_parts[-2:])
        else:
            domain = parsed.netloc.lower()

        results.append(
            {"normalised_url": clean_url, "count": count, "domain": domain}
        )

    return results


@router.get("/citation-coverage")
def get_domain_citation(
    parameters: Annotated[dict, Depends(common_parameters)],
    database: database_depends,
):
    brand_report_id = parameters.get("brand_report_id", "")
    start_date = parameters.get("start_date", "")
    end_date = parameters.get("end_date", "")
    domain = parameters.get("domain", "")
    model = parameters.get("model", "")
    s3_keys = database.get_domain_citation(
        brand_report_id=brand_report_id,
        start_date=start_date,
        end_date=end_date,
        model=model,
    )
    markdown = ""
    aws = AWSStorage()
    coverage_num = 0
    for s3_key in s3_keys:
        print(f"LOADING KEY - {s3_key}")
        output = aws.get_file_content(s3_key)
        markdown = f"{markdown} {output}".strip()
        if domain in markdown:
            coverage_num += 1

    pattern = (
        rf"(?:https?://)?(?:[\w-]+\.)*{re.escape(domain)}(?:/[^\s\"'<>]*)?"
    )

    matches = re.findall(pattern, markdown, flags=re.IGNORECASE)
    coverage = (coverage_num / len(s3_keys)) * 100
    coverage = round(coverage, 2)
    url_data = extract_url_data(markdown)
    return {
        "details": {
            "citation": len(matches),
            "coverage": coverage,
            "url_data": url_data,
        }
    }
