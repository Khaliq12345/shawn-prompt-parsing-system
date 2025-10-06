from sqlmodel import Session, create_engine, select
from src.infrastructure.models import Output_Reports, SQLModel, Citations, Sentiments
from src.config import config
from typing import Optional
import dateparser
from datetime import datetime, timedelta, date

class DataBase:
    def __init__(self) -> None:
        self.engine = create_engine(
            f"postgresql+psycopg://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:5432/{config.DB_NAME}"
        )

    def create_all_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def save_citations(self, citations: list[Citations]) -> None:
        print("Saving citations")
        with Session(self.engine) as session:
            session.add_all(citations)
            session.commit()

    def save_sentiments(self, sentiments: list[Sentiments]) -> None:
        print("Saving Sentiments")
        with Session(self.engine) as session:
            session.add_all(sentiments)
            session.commit()

    def save_output_reports(self, output_report: Output_Reports) -> None:
        print("Saving Output report")
        with Session(self.engine) as session:
            session.add(output_report)
            session.commit()
    
    def get_report_outputs(self, brand_report_id: str, date: Optional[str] = None, model: str = "all") -> dict | None:
        with Session(self.engine) as session:

            # Si la date n'est pas fournie → prendre la plus récente
            if date is None:
                latest_date = session.exec(
                    select(Output_Reports.date)
                    .where(Output_Reports.brand_report_id == brand_report_id)
                    .order_by(Output_Reports.date.desc())
                ).first()

                if not latest_date:
                    return None

                date = latest_date

            statement = select(Output_Reports).where(
                Output_Reports.brand_report_id == brand_report_id,
                Output_Reports.date == date
            )

            if model.lower() != "all":
                statement = statement.where(Output_Reports.model == model)

            result = session.exec(statement).first()

            if not result:
                return None

            return {
                "snapshot": result.snapshot,
                "markdown": result.markdown
            }

    def get_citations(self, brand_report_id: str, date: Optional[str] = None, model: str = "all") -> list[dict]:
        with Session(self.engine) as session:

            # Si la date n'est pas fournie → prendre la plus récente
            if date is None:
                latest_date = session.exec(
                    select(Citations.date)
                    .where(Citations.brand_report_id == brand_report_id)
                    .order_by(Citations.date.desc())
                ).first()

                if not latest_date:
                    return []

                date = latest_date

            statement = select(Citations).where(
                Citations.brand_report_id == brand_report_id,
                Citations.date == date
            )

            if model.lower() != "all":
                statement = statement.where(Citations.model == model)

            results = session.exec(statement).all()

        return [r.dict() for r in results]


    def get_sentiments(self, brand_report_id: str, date: Optional[str] = None, model: str = "all") -> list[dict]:
        """
        Récupère les sentiments depuis la table Sentiments avec filtres optionnels.
        Si date est None, sélectionne automatiquement la plus récente.
        """
        with Session(self.engine) as session:

            # Si la date n'est pas fournie, récupérer la date la plus récente
            if date is None:
                latest_date = session.exec(
                    select(Sentiments.date)
                    .where(Sentiments.brand_report_id == brand_report_id)
                    .order_by(Sentiments.date.desc())
                ).first()

                if not latest_date:
                    return []  # Aucun résultat

                date = latest_date

            # Construire la requête principale
            statement = select(Sentiments).where(
                Sentiments.brand_report_id == brand_report_id,
                Sentiments.date == date
            )

            if model.lower() != "all":
                statement = statement.where(Sentiments.model == model)

            # Exécuter la requête
            results = session.exec(statement).all()

        # Transformer en dictionnaire
        sentiments = [r.dict() for r in results]
        return sentiments

    def get_report_dates(self, max_dates: str = "7 days ago") -> list[str]:
        with Session(self.engine) as session:
            today = datetime.today().date()
            start_date_node = dateparser.parse(max_dates)
            start_date = start_date_node.date() if start_date_node else today - timedelta(days=7)

            statement = select(Output_Reports.date).where(
                Output_Reports.date >= start_date
            ).order_by(Output_Reports.date.desc())

            results = session.exec(statement).all()  # Liste de dates ou strings

            # Supprimer les doublons et trier
            unique_dates = sorted(set(results), reverse=True)

            # Si ce sont des dates, convertir en str, sinon juste retourner
            unique_dates_str = [
                d.strftime("%Y-%m-%d") if isinstance(d, (datetime, date)) else str(d)
                for d in unique_dates
            ]

        return unique_dates_str
