from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse
import dateparser
import markdown2
from markdownify import markdownify as md
import re

from selectolax.parser import HTMLParser

CANONICAL_MAP = {
    "google": [
        "google",
        "google ai overviews",
        "google aio",
        "aio",
        "ai overviews",
    ],
    "chatgpt": [
        "chatgpt",
        "chat gpt",
        "gpt",
    ],
    "perplexity": [
        "perplexity",
    ],
    "freshworks": [
        "freshworks",
        "fresh works",
    ],
}


def to_canonical(brand: str):
    brand = brand.lower().strip()

    for canonical, variants in CANONICAL_MAP.items():
        if brand in variants:
            return canonical

    return brand  # fallback


def remove_links(content: str | None = None):
    """
    Remove all URLs from text
    """
    # Pattern to match URLs (http, https, ftp, www, and common domain patterns)
    url_pattern = r"https?://\S+|www\.\S+|ftp://\S+"

    # Remove URLs
    text_without_urls = re.sub(url_pattern, "", content if content else "")

    # Clean up extra whitespace that might be left behind
    text_without_urls = re.sub(r"\s+", " ", text_without_urls).strip()
    return text_without_urls


def clean_markdown(content: str | None = None) -> str:
    if not content:
        return ""
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


def super_clean(content: str, model: str):
    if model.lower() == "google":
        content = content.split("* []")[0]
    content = remove_links(clean_markdown(content))
    return content


def extract_clean_links(content: str, model: str = "", google_citations: str = ""):
    """Extract and clean links from markdown content (including citations)"""

    BLOCKED_DOMAINS = {
        "www.google.com",
        "google.com",
        "gstatic.com",
        "www.gstatic.com",
        "accounts.google.com",
        "support.google.com",
    }

    if not content:
        return []

    full_content = f"{content} {google_citations}" if model == "Google" else content

    links = []

    # -----------------------------
    # 1. Extract reference citations (e.g. [^1]: https://...)
    # -----------------------------
    citation_pattern = re.findall(r"\[\^\d+\]:\s*(https?://[^\s]+)", full_content)

    for url in citation_pattern:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if any(blocked in domain for blocked in BLOCKED_DOMAINS):
            continue

        clean_url = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, "")
        )

        links.append(
            {
                "title": "",  # citations usually don’t have titles
                "domain": domain,
                "url": clean_url,
            }
        )

    # -----------------------------
    # 2. Extract normal markdown links via HTML parsing
    # -----------------------------
    html_content = markdown2.markdown(full_content)
    html = HTMLParser(html_content)
    link_nodes = html.css("a")

    for link_node in link_nodes:
        href = link_node.attributes.get("href")

        if not href or href.strip() in {"://", "#", "/"}:
            continue

        parsed = urlparse(href)
        domain = parsed.netloc.lower()

        if any(blocked in domain for blocked in BLOCKED_DOMAINS):
            continue

        clean_url = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                "",
            )
        )

        title = link_node.text(separator=" ").strip()

        links.append(
            {
                "title": title,
                "domain": domain,
                "url": clean_url,
            }
        )

    return links


def get_date() -> str:
    """Get date"""
    date_node = dateparser.parse("7 days Ago")
    if date_node:
        return date_node.strftime("%Y-%m-%d %H:%M:%S")
    return ""


def common_parameters(
    brand: str,
    brand_report_id: str,
    end_date: str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
    start_date: str = get_date(),
    model: str = "all",
):
    return {
        "brand": brand,
        "brand_report_id": brand_report_id,
        "start_date": start_date,
        "end_date": end_date,
        "model": model,
    }
