from fastapi import APIRouter, Depends, HTTPException, Query
from src.infrastructure.database import DataBase
from src.infrastructure.aws_storage import get_presigned_url  # fonction pour générer l'URL S3

router = APIRouter(
    prefix="/report/prompts",
    responses={404: {"description": "Not found"}}
)

# Paramètres communs
def common_parameters(
    brand_report_id: str = Query(..., description="ID du rapport de la marque"),
    date: str = Query(..., description="Date du rapport au format YYYY-MM-DD"),
    model: str = Query(..., description="Nom du modèle"),
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
        
    snapshot_url = get_presigned_url(report["snapshot"])
    markdown_url = get_presigned_url(report["markdown"])

    return {
        "snapshot_url": snapshot_url,
        "markdown": markdown_url
    }
    