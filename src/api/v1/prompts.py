from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/report/prompts", responses={404: {"description": "Not found"}}
)


@router.get("/outputs")
def get_outputs() -> dict:
    output = {"snapshot_url": "", "markdown": ""}
    return {"details": output}


# @router.get("/citation")

# @router.get("/sentiment")
