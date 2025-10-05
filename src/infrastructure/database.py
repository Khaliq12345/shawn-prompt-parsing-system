from sqlmodel import Session, create_engine, select
from src.infrastructure.models import Output_Reports, SQLModel, Citations, Sentiments
from src.config import config


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
    
    def get_report_outputs(self, brand_report_id: str, date: str, model: str) -> dict | None:
        """
        Récupère snapshot et markdown d'un rapport depuis la base.
        Le filtre `model` est appliqué seulement si model != "all".
        """
        with Session(self.engine) as session:
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

    def get_citations(self, brand_report_id: str, date: str, model: str = "all") -> list[dict]:
        with Session(self.engine) as session:
            statement = select(Citations).where(
                Citations.brand_report_id == brand_report_id,
                Citations.date == date
            )

            if model.lower() != "all":
                statement = statement.where(Citations.model == model)

            results = session.exec(statement).all()

        # Transformer en dict
        citations = [r.dict() for r in results]  # SQLModel fournit .dict()
        return citations

    def get_sentiments(self, brand_report_id: str, date: str, model: str = "all") -> list[dict]:
        """
        Récupère les sentiments depuis la table Sentiments avec filtres optionnels.
        """
        with Session(self.engine) as session:
            statement = select(Sentiments).where(
                Sentiments.brand_report_id == brand_report_id,
                Sentiments.date == date
            )

            if model.lower() != "all":
                statement = statement.where(Sentiments.model == model)

            results = session.exec(statement).all()
        sentiments = [r.dict() for r in results]
        return sentiments
