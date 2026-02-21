from time import time
from typing import Annotated, Optional

import dateparser
from fastapi import APIRouter, Depends, HTTPException, Query

from src.infrastructure import celery_app
from src.infrastructure.aws_storage import AWSStorage
from src.infrastructure.database import DataBase

router = APIRouter(
    prefix="/report/prompts", responses={404: {"description": "Not found"}}
)


def get_date() -> str:
    """Get date"""
    date_node = dateparser.parse("7 days Ago")
    if date_node:
        return date_node.strftime("%Y-%m-%d %H:%M:%S")
    return ""


# Shared query parameters
def common_parameters(
    brand_report_id: str = Query(..., description="Brand report ID"),
    date: Optional[str] = Query(None, description="Report date"),
    model: str = Query("all", description="Model name (default: 'all')"),
):
    return {
        "brand_report_id": brand_report_id,
        "date": date,
        "model": model,
    }


@router.post("/parse")
def parse_output(
    brand_report_id: str,
    prompt_id: str,
    model: str,
    brand: str,
    s3_key: str,
    languague: str,
    date: str,
) -> dict:
    """Start the worflow"""
    try:
        timestamp = int(time())
        process_id = f"{brand_report_id}-{model}-{brand}-{timestamp}"
        celery_app.run_browser.apply_async(
            args=(
                process_id,
                brand_report_id,
                prompt_id,
                model,
                brand,
                s3_key,
                languague,
                date,
            )
        )
        return {"details": "Parser started", "process": process_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")


@router.get("/reports")
def get_reports(
    db: Annotated[DataBase, Depends(DataBase)],
    brand_report_id: str,
    limit: int = 20,
    page: int = 1,
):
    offset = (page - 1) * limit
    results = db.get_reports(brand_report_id, limit, offset)
    return results


@router.get("/outputs")
def get_outputs(
    prompt_id: str,
    db: Annotated[DataBase, Depends(DataBase)],
    brand_report_id: str = Query(..., description="Brand report ID"),
    date: Optional[str] = Query(None, description="Report date"),
    model: str = Query("chatgpt", description="Model name"),
    max_date: str = "7 days ago",
):
    """
    Retrieve the snapshot and markdown of a report from the database.
    Returns fully-qualified AWS S3 URLs, along with all available report dates.

    Parameters:
        max_date (str, optional): Lower bound for available report dates.
                                  Example: "7 days ago" or "2023-01-01"
    """
    try:
        aws_storage = AWSStorage()
        report = db.get_report_outputs(
            brand_report_id,
            prompt_id,
            date,
            model,
        )
        if not report:
            raise HTTPException(status_code=404, detail="Output report not found")

        # Generate AWS S3 pre-signed URLs
        print("GETTING PRESIGNED URLS")
        snapshot_url = aws_storage.get_presigned_url(report["snapshot"])
        markdown = aws_storage.get_file_content(report["markdown"])
        print("URLS GOTTEN")

        # Retrieve all unique available dates according to max_date
        print("GETTING ALL DATES")
        available_dates = db.get_report_dates(max_dates=max_date, prompt_id=prompt_id)
        print("ALL DATES RETRIEVED")

        return {
            "snapshot_url": snapshot_url,
            "markdown": markdown,
            "available_dates": available_dates,
        }
    except HTTPException as _:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")


@router.get("/citations")
def get_citations(
    db: Annotated[DataBase, Depends(DataBase)], prompt_id: str, date: str, model: str
):
    """
    Retrieve citations for a given report.
    """
    try:
        citations = db.get_citations(prompt_id, date, model)
        print(citations)
        return {"citations": citations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")


@router.get("/sentiments")
def get_sentiments(
    db: Annotated[DataBase, Depends(DataBase)], prompt_id: str, date: str, model: str
):
    """
    Retrieve sentiment analysis results for a given report.
    Adds helper counters for positive and negative phrases.
    """
    try:
        sentiments = db.get_sentiments(prompt_id, date, model)

        for sentiment in sentiments:
            sentiment["count_positive_phrases"] = len(
                sentiment.get("positive_phrases", [])
            )
            sentiment["count_negative_phrases"] = len(
                sentiment.get("negative_phrases", [])
            )

        return {"sentiments": sentiments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")
