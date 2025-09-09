from fastapi import APIRouter, HTTPException

from src.infrastructure.database import (
    get_brand_coverage_db,
    get_brand_mentions_db,
    get_brand_position_db,
    get_brand_ranking_db,
    get_brand_sov_db,
)

router = APIRouter(prefix="", responses={404: {"description": "Not found"}})


# Brand Mentions
@router.get("/brand-mentions")
async def get_brand_mentions(prompt_id: str, brand: str):
    try:
        result = await get_brand_mentions_db(prompt_id, brand)
        return {"data": {"mentions": result}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Brand Share of Voice
@router.get("/brand-share-of-voice")
async def get_brand_sov(prompt_id: str, brand: str):
    try:
        result = await get_brand_sov_db(prompt_id, brand)
        return {"data": {"sov": result}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Brand Coverage
@router.get("/brand-coverage")
async def get_brand_coverage(prompt_id: str, brand: str):
    try:
        result = await get_brand_coverage_db(prompt_id, brand)
        return {"data": {"coverage": result}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")


# Brand Position
@router.get("/brand-position")
async def get_brand_position(prompt_id: str, brand: str):
    try:
        result = await get_brand_position_db(prompt_id, brand)
        return {"data": {"position": result}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# Brand Ranking
@router.get("/metrics/brand-ranking")
async def get_brand_ranking(prompt_id: str):
    try:
        result = await get_brand_ranking_db(prompt_id)
        return {"data": {"ranking": result}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")