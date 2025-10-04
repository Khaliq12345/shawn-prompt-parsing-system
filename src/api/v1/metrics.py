from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from src.infrastructure.click_house import ClickHouse
from datetime import datetime
import dateparser

router = APIRouter(
    prefix="/report/metrics", responses={404: {"description": "Not found"}}
)


def get_today() -> str:
    """Get today's date"""
    date_node = dateparser.parse("Last 7 days")
    if date_node:
        return date_node.strftime("%Y-%m-%d %H:%M:%S")
    return ""


def common_parameters(
    brand: str,
    brand_report_id: str,
    start_date: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    end_date: str = get_today(),
    model: str = "all",
):
    return {
        "brand": brand,
        "brand_report_id": brand_report_id,
        "start_date": start_date,
        "end_date": end_date,
        "model": model,
    }


# Brand Mentions
@router.get("/mentions")
def brand_mentions(
    arguments: Annotated[dict, Depends(common_parameters)],
    clickhouse: Annotated[ClickHouse, ClickHouse],
):
    try:
        result = clickhouse.get_brand_mention(
            brand=arguments["brand"],
            brand_report_id=arguments["brand_report_id"],
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            model=arguments["model"],
        )
        return {"data": {"mentions": result.get("data", 0)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Brand Share of Voice
@router.get("/share-of-voice")
def brand_sov(
    arguments: Annotated[dict, Depends(common_parameters)],
    clickhouse: Annotated[ClickHouse, ClickHouse],
):
    try:
        result = clickhouse.get_brand_sov(
            brand=arguments["brand"],
            brand_report_id=arguments["brand_report_id"],
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            model=arguments["model"],
        )
        return {"data": {"sov": result.get("data", 0.0)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Brand Coverage
@router.get("/coverage")
def brand_coverage(
    arguments: Annotated[dict, Depends(common_parameters)],
    clickhouse: Annotated[ClickHouse, ClickHouse],
):
    try:
        result = clickhouse.get_brand_coverage(
            brand=arguments["brand"],
            brand_report_id=arguments["brand_report_id"],
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            model=arguments["model"],
        )
        return {"data": {"coverage": result.get("data", 0.0)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Brand Position
@router.get("/position")
def brand_position(
    arguments: Annotated[dict, Depends(common_parameters)],
    clickhouse: Annotated[ClickHouse, ClickHouse],
):
    try:
        result = clickhouse.get_brand_position(
            brand=arguments["brand"],
            brand_report_id=arguments["brand_report_id"],
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            model=arguments["model"],
        )
        return {"data": {"position": result.get("data", 0.0)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Brand Ranking
@router.get("/ranking")
def brand_ranking(
    arguments: Annotated[dict, Depends(common_parameters)],
    clickhouse: Annotated[ClickHouse, ClickHouse],
):
    try:
        result = clickhouse.get_brand_ranking(
            brand_report_id=arguments["brand_report_id"],
            start_date=arguments["start_date"],
            end_date=arguments["end_date"],
            model=arguments["model"],
        )
        return {"data": {"ranking": result or []}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
