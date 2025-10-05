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
    
    def get_output_report(self, brand_report_id: str, date: str, model: str) -> None:
        with Session(self.engine) as session:
            statement = (
                select(Output_Reports)
                .where(Output_Reports.brand_report_id == brand_report_id)
                .where(Output_Reports.date == date)
                .where(Output_Reports.model == model)
            )
            result = session.exec(statement).first()

            if not result:
                return None

            return {
                "snapshot": result.snapshot,
                "markdown": result.markdown
            }

if __name__ == "__main__":


    db = DataBase()


    with Session(db.engine) as session:
        all_reports = session.exec(select(Output_Reports)).all()
        for r in all_reports:
            print(r.brand_report_id, r.date, r.model)

    output = db.get_output_report("br_12345", "2023-01-01", "Chatgpt")
    print(output)


