import time
from fastapi import APIRouter, HTTPException
from src.infrastructure.database import get_all_brand_mentions
from src.infrastructure.llm_service import LLMService

router = APIRouter(prefix="", responses={404: {"description": "Not found"}})


# Start and record BrandMentions
@router.get("/extract-brand-info")
async def extract_brand_mentions(prompt_id: str, s3_key: str):
    # Adidas Adizero Evo SL and the Adidas Ultraboost Light are both excellent. The Nike Pegasus is also great. ![Alt text](https://olaila.png "Optional Title") [GitHub](http://github.com)
    try:
        process_id = f"{prompt_id}_{int(time.time())}"
        llm_class = LLMService(prompt_id, process_id)
        await llm_class.main(s3_key)
        return {
            "prompt_id": prompt_id,
            "process_id": process_id,
            "details": "parsing started",
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# Retrieve all BrandMentions from a prompt_id
@router.get("/get-db-brand-mentions")
async def get_db_mentions(prompt_id: str):
    try:
        results = await get_all_brand_mentions(prompt_id)
        return {"prompt_id": prompt_id, "details": results}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


# Retrieve a AWS stored file's content
@router.get("/extract-file-content")
async def extract_content(key: str):
    try:
        llm_class = LLMService("test")
        print(f"Buccket {llm_class.bucket}")
        # await llm_class.storage.save_file("README.md", "README.md")
        results = await llm_class.storage.get_file_content("README.md")
        return {"details": results}
    except Exception as e:
        raise HTTPException(500, detail=str(e))
