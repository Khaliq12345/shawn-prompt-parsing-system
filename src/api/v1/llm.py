import time
from fastapi import APIRouter, HTTPException
from src.infrastructure.database import (
    get_llm_process_status,
)
from src.infrastructure.taskiq_app import run_llm_task

router = APIRouter(responses={404: {"description": "Not found"}})


# Start and record BrandMentions
@router.get("/extract-brand-info")
async def extract_brand_mentions(prompt_id: str, s3_key: str):
    try:
        process_id = f"{prompt_id}_{int(time.time())}"
        # Run in background using taskiq
        await run_llm_task.kiq(prompt_id, process_id, s3_key)
        return {
            "prompt_id": prompt_id,
            "process_id": process_id,
            "details": "parsing started",
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# Get Process Status
@router.get("/get-process-status")
async def get_pricess_status(prompt_id: str, process_id: str):
    try:
        status = await get_llm_process_status(process_id, prompt_id)
        return {
            "prompt_id": prompt_id,
            "process_id": process_id,
            "status": status,
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))
