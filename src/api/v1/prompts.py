from fastapi import APIRouter, HTTPException, Query
from src.infrastructure.database import DataBase
from src.infrastructure.aws_storage import get_presigned_url  # fonction pour générer l'URL S3

router = APIRouter(
    prefix="/report/prompts",
    responses={404: {"description": "Not found"}}
)

# Instance de la base de données
db = DataBase()

@router.get("/outputs")
def get_outputs(
    brand_report_id: str = Query(..., description="ID du rapport de la marque"),
    date: str = Query(..., description="Date du rapport au format YYYY-MM-DD"),
    model: str = Query(..., description="Nom du modèle")
) -> dict:
    """
    Récupère le snapshot et le markdown d'un rapport.
    Retourne l'URL complète du snapshot via AWS S3.
    """
    # Récupérer snapshot et markdown depuis la base
    report = db.get_output_report(brand_report_id, date, model)
    if not report:
        raise HTTPException(status_code=404, detail="Output report not found")

    # Générer l'URL complète du snapshot
    snapshot_url = get_presigned_url(report["snapshot"])

    return {
        "snapshot_url": snapshot_url,
        "markdown": report["markdown"]
    }
