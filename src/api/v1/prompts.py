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
    db: Annotated[DataBase, Depends(DataBase)],
    max_date: str = "7 days ago"  # Valeur par défaut pour récupérer les dates des 7 derniers jours
):
    """
    Récupère le snapshot et le markdown d'un rapport depuis la base.
    Retourne les URLs complètes via AWS S3, ainsi que toutes les dates disponibles.

    Paramètres :
        max_date (str, optionnel) : limite inférieure pour récupérer les dates disponibles.
                                     Ex: "7 days ago" ou "2023-01-01"
    """
    # Récupérer le rapport
    report = db.get_report_outputs(
        arguments["brand_report_id"], arguments["date"], arguments["model"]
    )

    if not report:
        raise HTTPException(status_code=404, detail="Output report not found")

    # Générer les URLs AWS S3
    snapshot_url = aws_storage.get_presigned_url(report["snapshot"])
    markdown_url = aws_storage.get_presigned_url(report["markdown"])

    # Récupérer toutes les dates uniques disponibles selon max_date
    available_dates = db.get_report_dates(max_dates=max_date)

    return {
        "snapshot_url": snapshot_url,
        "markdown": markdown_url,
        "available_dates": available_dates
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
