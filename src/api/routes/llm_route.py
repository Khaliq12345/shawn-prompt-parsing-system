import time
from fastapi import APIRouter, HTTPException
from src.infrastructure.llm_service import LLMService

router = APIRouter(prefix="", responses={404: {"description": "Not found"}})


# Get Logs
@router.get("/get-brand-mentions")
async def get_mentions(content: str):
    # Adidas Adizero Evo SL and the Adidas Ultraboost Light are both excellent. The Nike Pegasus is also great. ![Alt text](https://olaila.png "Optional Title") [GitHub](http://github.com)
    try:
        timestamp = int(time.time())
        process_id = f"run_{timestamp}"
        llm_class = LLMService(process_id)
        results = await llm_class.get_brand_mentions(content)
        return {"process_id": process_id, "details": results}
    except Exception as e:
        raise HTTPException(500, detail=str(e))
