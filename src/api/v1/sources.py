from datetime import datetime, timedelta
from typing import Annotated, Optional
from fastapi import APIRouter, Depends
from src.infrastructure.aws_storage import AWSStorage
import dateparser
from src.api.dependencies import database_depends
from collections import Counter
from urllib.parse import urlparse
import asyncio

from src.infrastructure.shared import extract_clean_links


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
    start_date: str = get_date(),
    end_date: str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
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


def extract_domain(clean_url):
    parsed = urlparse(clean_url)
    domain_parts = parsed.netloc.lower().split(".")

    # Extract the main domain (e.g., nike.com from shop.nike.com)
    if len(domain_parts) >= 2:
        domain = ".".join(domain_parts[-2:])
    else:
        domain = parsed.netloc.lower()
    return domain


def extract_url_data(text):
    """
    Extract all URLs from text and return normalized URL, count, and main domain.
    """
    # Regex for http(s) URLs
    urls = extract_clean_links(text)
    urls = [u["url"] for u in urls]
    print(urls)
    print(f"URLS - {len(urls)}")
    # Count how many times each URL appears
    url_counts = Counter(urls)

    results = []
    for url, count in url_counts.items():
        clean_url = url.replace(")", "")
        domain = extract_domain(clean_url)
        results.append({"normalised_url": clean_url, "count": count, "domain": domain})

    return results


def normalize_domain(d: str) -> str:
    if not d:
        return ""
    d = d.lower().strip()
    domain = extract_domain(d)
    return domain


@router.get("/citation-coverage")
async def get_domain_citation(
    parameters: Annotated[dict, Depends(common_parameters)],
    database: database_depends,
):
    aws = AWSStorage()

    brand_report_id = parameters.get("brand_report_id", "")
    start_date = parameters.get("start_date", "")
    end_date = parameters.get("end_date", "")
    domain = normalize_domain(parameters.get("domain", ""))
    model = parameters.get("model", "")

    citations = database.get_citations_by_report(
        brand_report_id, start_date, end_date, model
    )
    print(citations)

    s3_keys = database.get_markdown_s3_keys(
        brand_report_id=brand_report_id,
        start_date=start_date,
        end_date=end_date,
        model=model,
    )

    if not s3_keys:
        return {
            "details": {
                "citation": 0,
                "coverage": 0.0,
                "url_data": [],
            }
        }

    # ---- ASYNC FETCH ----
    semaphore = asyncio.Semaphore(20)

    async def fetch_s3(key):
        async with semaphore:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, aws.get_file_content, key)

    outputs = await asyncio.gather(*(fetch_s3(k) for k in s3_keys))

    # ---- PROCESS RESULTS ----
    valid_outputs = []
    valid_keys = []
    all_url_records = []
    coverage_num = 0

    for key, output in zip(s3_keys, outputs):
        if not output or output == "Ai overview not visible":
            continue

        valid_outputs.append(output)
        valid_keys.append(key)

        urls = extract_url_data(output)
        all_url_records.extend(urls)

        if any(u["domain"] == domain for u in urls):
            coverage_num += 1

    if not valid_keys:
        return {
            "details": {
                "citation": 0,
                "coverage": 0.0,
                "url_data": [],
            }
        }

    all_markdown = " ".join(valid_outputs)

    url_records = extract_url_data(all_markdown)
    citation_count = sum(r["count"] for r in url_records if r["domain"] == domain)

    coverage = round((coverage_num / len(valid_keys)) * 100, 2)

    return {
        "details": {
            "citation": citation_count,
            "coverage": coverage,
            "url_data": url_records,
        }
    }
