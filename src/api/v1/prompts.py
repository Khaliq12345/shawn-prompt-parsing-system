from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from src.infrastructure.database import DataBase
from src.infrastructure.aws_storage import AWSStorage
from typing import Optional

aws_storage = AWSStorage(bucket_name="browser-outputs")

router = APIRouter(
    prefix="/report/prompts",
    responses={404: {"description": "Not found"}}
)


# Paramètres communs
def common_parameters(
    brand_report_id: str = Query(..., description="ID du rapport de la marque"),
    date: Optional[str] = Query(None, description="Date du rapport au format YYYY-MM-DD (facultatif)"),
    model: str = Query("all", description="Nom du modèle (par défaut 'all')"),
):
    return {
        "brand_report_id": brand_report_id,
        "date": date,
        "model": model,
    }

@router.get("/outputs")
def get_outputs(
    arguments: Annotated[dict, Depends(common_parameters)],
    db: Annotated[DataBase, Depends(DataBase)]
):
    """
    Récupère le snapshot et le markdown d'un rapport depuis la base.
    Retourne les URLs complètes via AWS S3.
    """
    report = db.get_report_outputs(
        arguments["brand_report_id"], arguments["date"], arguments["model"]
    )

    if not report:
        raise HTTPException(status_code=404, detail="Output report not found")

    snapshot_url = aws_storage.get_presigned_url(report["snapshot"])
    markdown_url = aws_storage.get_presigned_url(report["markdown"])

    return {
        "snapshot_url": snapshot_url,
        "markdown": markdown_url
    }
    

@router.get("/citations")
def get_citations(
    arguments: Annotated[dict, Depends(common_parameters)],
    db: Annotated[DataBase, Depends(DataBase)]
):
    """
    Récupère les citations pour un rapport donné.
    """
    citations = db.get_citations(
        arguments["brand_report_id"],
        arguments["date"],
        arguments["model"]
    )

    if not citations:
        raise HTTPException(status_code=404, detail="No citations found")

    # Retourner les citations sous forme de dict simple
    return {"citations": citations}

@router.get("/sentiments")
def get_sentiments(
    arguments: Annotated[dict, Depends(common_parameters)],
    db: Annotated[DataBase, Depends(DataBase)]
):
    sentiments = db.get_sentiments(
        arguments["brand_report_id"],
        arguments["date"],
        arguments["model"]
    )

    if not sentiments:
        raise HTTPException(status_code=404, detail="No sentiments found")

    # Ajouter le count des phrases positives et négatives
    for sentiment in sentiments:
        sentiment["count_positive_phrases"] = len(sentiment.get("positive_phrases", []))
        sentiment["count_negative_phrases"] = len(sentiment.get("negative_phrases", []))

    return {"sentiments": sentiments}
