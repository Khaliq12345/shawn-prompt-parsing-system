from fastapi import APIRouter, HTTPException
from src.infrastructure.redis_service import AsyncRedisBase

router = APIRouter(prefix="", responses={404: {"description": "Not found"}})


@router.get("/{prompt_id}")
async def get_logs(prompt_id: str):
    try:
        # Get Matching Instance
        redis_base = AsyncRedisBase(prompt_id)
        # Get Logs
        logs = await redis_base.get_log()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unable to retrieve Logs : {e}"
        )
    return {"details": logs}
