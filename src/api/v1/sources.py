from collections import defaultdict
from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter, Depends
import dateparser
from src.api.dependencies import database_depends
from collections import Counter
from urllib.parse import urlparse

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
        domain = domain if domain else parsed.path
    return domain


def extract_url_data(text):
    """
    Extract all URLs from text and return normalized URL, count, and main domain.
    """
    # Regex for http(s) URLs
    urls = extract_clean_links(text)
    urls = [u["url"] for u in urls]
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
    brand_report_id = parameters.get("brand_report_id", "")
    start_date = parameters.get("start_date", "")
    end_date = parameters.get("end_date", "")
    domain = normalize_domain(parameters.get("domain", ""))
    model = parameters.get("model", "")

    citations = database.get_citations_by_report(
        brand_report_id, start_date, end_date, model
    )

    if not citations:
        return {
            "details": {
                "citation": 0,
                "coverage": 0.0,
                "url_data": [],
            }
        }

    url_counter = defaultdict(int)
    domain_counter = defaultdict(int)

    # 🔑 COVERAGE TRACKING (BY S3 KEY)
    all_s3_keys = set()
    s3_with_domain = set()

    for c in citations:
        norm_domain = c["domain"]
        url = c["norm_url"]
        s3_key = c["s3_key"]

        # Track all documents
        all_s3_keys.add(s3_key)

        # Count URLs
        url_counter[(url, norm_domain)] += 1
        domain_counter[norm_domain] += 1

        # Coverage: mark if domain appears in this S3 doc
        if norm_domain == domain:
            s3_with_domain.add(s3_key)

    # ---- BUILD URL DATA ----
    url_records = [
        {
            "normalised_url": url,
            "count": count,
            "domain": d,
        }
        for (url, d), count in url_counter.items()
    ]

    # ---- FINAL METRICS ----
    citation_count = domain_counter.get(domain)
    coverage = (
        round((len(s3_with_domain) / len(all_s3_keys)) * 100, 2) if all_s3_keys else 0.0
    )

    return {
        "details": {
            "citation": citation_count,
            "coverage": coverage,
            "url_data": url_records,
        }
    }
