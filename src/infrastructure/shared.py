from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse
import dateparser
import markdown2
from markdownify import markdownify as md
import re
import httpx
from selectolax.parser import HTMLParser
import tldextract

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
    """Extract and clean links from markdown content (including citations and Google redirects)"""

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

    # Helper to process and filter individual URLs
    def process_url(url: str, title: str = ""):
        # Resolve Google /goto redirect links before blocking/parsing
        if model == "Google" and ("/goto?" in url or "google.com/goto" in url):
            url = resolve_google_goto_url(url)

        parsed = urlparse(url)
        domain = normalize_domain(url)

        if any(blocked in domain for blocked in BLOCKED_DOMAINS):
            return None

        clean_url = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, "")
        )

        return {"title": title, "domain": domain, "url": clean_url}

    # -----------------------------
    # 1. Extract reference citations (e.g. [^1]: https://...)
    # -----------------------------
    citation_pattern = re.findall(r"\[\^\d+\]:\s*(https?://[^\s]+)", full_content)

    for url in citation_pattern:
        link_data = process_url(url, title="")
        if link_data:
            links.append(link_data)

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

        title = link_node.text(separator=" ").strip()
        link_data = process_url(href, title=title)
        if link_data:
            links.append(link_data)

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


def normalize_domain(d: str) -> str:
    if not d:
        return ""
    d = d.lower().strip()
    domain_node = tldextract.extract(d)
    domain = domain_node.domain
    suffix = domain_node.suffix
    return f"{domain}.{suffix}"


def resolve_google_goto_url(goto_url: str, timeout: float = 30.0) -> str | None:
    """Resolves a Google /goto redirect URL to its final destination using httpx."""
    if goto_url.startswith("/"):
        goto_url = "https://www.google.com" + goto_url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        # follow_redirects=True ensures httpx automatically walks the redirect chain
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            response = client.get(goto_url, headers=headers)
            return str(response.url)
    except httpx.HTTPError as e:
        print(f"Failed to resolve URL: {e}")
        return None
