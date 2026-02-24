import markdown2
from markdownify import markdownify as md
import re


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
