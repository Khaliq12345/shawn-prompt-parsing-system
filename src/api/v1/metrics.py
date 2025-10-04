from fastapi import APIRouter, HTTPException
from src.infrastructure.click_house import ClickHouse

clickhouse = ClickHouse()

router = APIRouter(
    prefix="/report/metrics",
    responses={404: {"description": "Not found"}}
)


# Brand Mentions
@router.get("/mentions")
def brand_mentions(
    brand: str,
    brand_report_id: str,
    start_date: str = "",
    end_date: str = "",
    model: str = "all"
):
    try:
        result = clickhouse.get_brand_mention(
            brand=brand,
            brand_report_id=brand_report_id,
            start_date=start_date,
            end_date=end_date,
            model=model
        )
        return {"data": {"mentions": result.get("data", 0)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Brand Share of Voice
@router.get("/share-of-voice")
def brand_sov(
    brand: str,
    brand_report_id: str,
    start_date: str = "",
    end_date: str = "",
    model: str = "all"
):
    try:
        result = clickhouse.get_brand_sov(
            brand=brand,
            brand_report_id=brand_report_id,
            start_date=start_date,
            end_date=end_date,
            model=model
        )
        return {"data": {"sov": result.get("data", 0.0)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Brand Coverage
@router.get("/coverage")
def brand_coverage(
    brand: str,
    brand_report_id: str,
    start_date: str = "",
    end_date: str = "",
    model: str = "all"
):
    try:
        result = clickhouse.get_brand_coverage(
            brand=brand,
            brand_report_id=brand_report_id,
            start_date=start_date,
            end_date=end_date,
            model=model
        )
        return {"data": {"coverage": result.get("data", 0.0)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Brand Position
@router.get("/position")
def brand_position(
    brand: str,
    brand_report_id: str,
    start_date: str = "",
    end_date: str = "",
    model: str = "all"
):
    try:
        result = clickhouse.get_brand_position(
            brand=brand,
            brand_report_id=brand_report_id,
            start_date=start_date,
            end_date=end_date,
            model=model
        )
        return {"data": {"position": result.get("data", 0.0)}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Brand Ranking
@router.get("/ranking")
def brand_ranking(
    brand_report_id = "",
    start_date: str = "",
    end_date: str = "",
    model: str = "all"
):
    try:
        result = clickhouse.get_brand_ranking(
            brand_report_id=brand_report_id,
            start_date=start_date,
            end_date=end_date,
            model=model
        )
        return {"data": {"ranking": result or []}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}"
)
