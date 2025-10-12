from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from src.infrastructure.database import DataBase
from src.infrastructure import celery_app
from src.infrastructure.aws_storage import AWSStorage
from src.config.config import BUCKET_NAME
from time import time
import dateparser

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


@router.get("/outputs")
def get_outputs(
    arguments: Annotated[dict, Depends(common_parameters)],
    db: Annotated[DataBase, Depends(DataBase)],
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
        aws_storage = AWSStorage(bucket_name=BUCKET_NAME)
        report = db.get_report_outputs(
            arguments["brand_report_id"], arguments["date"], arguments["model"]
        )

        if not report:
            raise HTTPException(status_code=404, detail="Output report not found")

        # Generate AWS S3 pre-signed URLs
        snapshot_url = aws_storage.get_presigned_url(report["snapshot"])
        markdown_url = aws_storage.get_presigned_url(report["markdown"])

        # Retrieve all unique available dates according to max_date
        available_dates = db.get_report_dates(max_dates=max_date)

        return {
            "snapshot_url": snapshot_url,
            "markdown": markdown_url,
            "available_dates": available_dates,
        }
    except HTTPException as _:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")


@router.get("/citations")
def get_citations(
    arguments: Annotated[dict, Depends(common_parameters)],
    db: Annotated[DataBase, Depends(DataBase)],
):
    """
    Retrieve citations for a given report.
    """
    try:
        citations = db.get_citations(
            arguments["brand_report_id"], arguments["date"], arguments["model"]
        )
        return {"citations": citations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {e}")


@router.get("/sentiments")
def get_sentiments(
    arguments: Annotated[dict, Depends(common_parameters)],
    db: Annotated[DataBase, Depends(DataBase)],
):
    """
    Retrieve sentiment analysis results for a given report.
    Adds helper counters for positive and negative phrases.
    """
    try:
        sentiments = db.get_sentiments(
            arguments["brand_report_id"], arguments["date"], arguments["model"]
        )

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
