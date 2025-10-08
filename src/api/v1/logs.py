from fastapi import APIRouter, HTTPException
from src.infrastructure.redis_service import RedisBase

router = APIRouter(prefix="/logs")


@router.get("/{process_id}")
def get_logs(process_id: str):
    try:
        # Get Matching Instance
        redis_base = RedisBase(process_id)
        # Get Logs
        logs = redis_base.get_log()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Unable to retrieve Logs : {e}"
        )
    return {"details": logs}
