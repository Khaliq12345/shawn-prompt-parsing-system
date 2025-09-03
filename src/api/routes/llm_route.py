from fastapi import APIRouter, HTTPException
from src.infrastructure.llm_service import LLMService

router = APIRouter(prefix="", responses={404: {"description": "Not found"}})


# Get Logs
@router.get("/get-brand-mentions")
def get_mentions(content: str):
    try:
        llm_class = LLMService('run_00012')
        results = llm_class.get_brand_mentions(content)
        print(f"Got result {results}")
        return results
    except Exception as e:
        raise HTTPException(500, detail=str(e))

