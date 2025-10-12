import json
from sqlmodel import Column, Session, create_engine, select
from src.infrastructure.models import (
    Output_Reports,
    SQLModel,
    Citations,
    Sentiments,
)
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

    def get_report_outputs(
        self,
        brand_report_id: str,
        date: Optional[str] = None,
        model: str = "all",
    ) -> dict | None:
        """
        Retrieve the snapshot and markdown URLs for a given report.

        Args:
            brand_report_id (str): Identifier of the brand report.
            date (str | None): Optional specific date. If not provided, the most recent date is used.
            model (str): Optional model filter. Use "all" to ignore model filtering.

        Returns:
            dict | None: Dictionary with 'snapshot' and 'markdown' keys, or None if no match is found.
        """
        with Session(self.engine) as session:
            # If no date is provided, retrieve the most recent date for this brand_report_id
            if date is None:
                latest_date = session.exec(
                    select(Output_Reports.date)
                    .where(Output_Reports.brand_report_id == brand_report_id)
                    .order_by(Column(Output_Reports.date).desc())
                ).first()

                if not latest_date:
                    return None

                date = latest_date

            # Base query
            statement = select(Output_Reports).where(
                Output_Reports.brand_report_id == brand_report_id,
                Output_Reports.date == date,
            )

            # Apply optional model filter
            if model.lower() != "all":
                statement = statement.where(Output_Reports.model == model)

            result = session.exec(statement).first()

            if not result:
                return None

            return {"snapshot": result.snapshot, "markdown": result.markdown}

    def get_citations(
        self,
        brand_report_id: str,
        date: Optional[str] = None,
        model: str = "all",
    ) -> list[dict]:
        """
        Retrieve a list of citations for a given report.

        Args:
            brand_report_id (str): Identifier of the brand report.
            date (str | None): Optional specific date. If not provided, the most recent date is used.
            model (str): Optional model filter. Use "all" to ignore model filtering.

        Returns:
            list[dict]: List of citation objects as dictionaries.
        """
        with Session(self.engine) as session:
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
                Citations.date == date,
            )

            if model.lower() != "all":
                statement = statement.where(Citations.model == model)

            results = session.exec(statement).all()

        citations = [json.loads(result.model_dump_json()) for result in results]
        return citations

    def get_sentiments(
        self,
        brand_report_id: str,
        date: Optional[str] = None,
        model: str = "all",
    ) -> list[dict]:
        """
        Retrieve sentiment results for a given report.

        Args:
            brand_report_id (str): Identifier of the brand report.
            date (str | None): Optional specific date. If not provided, the most recent date is used.
            model (str): Optional model filter. Use "all" to ignore model filtering.

        Returns:
            list[dict]: List of sentiment analysis results as dictionaries.
        """
        with Session(self.engine) as session:
            if date is None:
                latest_date = session.exec(
                    select(Sentiments.date)
                    .where(Sentiments.brand_report_id == brand_report_id)
                    .order_by(Sentiments.date.desc())
                ).first()

                if not latest_date:
                    return []

                date = latest_date

            statement = select(Sentiments).where(
                Sentiments.brand_report_id == brand_report_id,
                Sentiments.date == date,
            )

            if model.lower() != "all":
                statement = statement.where(Sentiments.model == model)

            results = session.exec(statement).all()

        sentiments = [json.loads(result.model_dump_json()) for result in results]
        return sentiments

    def get_report_dates(self, max_dates: str = "7 days ago") -> list[str]:
        """
        Retrieve all unique report dates from Output_Reports table,
        greater than or equal to the given max_dates.

        Args:
            max_dates (str): Human-readable date limit.
                             Example: "7 days ago", "2023-01-01". Defaults to "7 days ago".

        Returns:
            list[str]: List of unique dates formatted as "YYYY-MM-DD", sorted descending.
        """
        with Session(self.engine) as session:
            # Get today's date
            today = datetime.today().date()

            # Convert the provided max_dates string into a date object
            start_date_node = dateparser.parse(max_dates)
            start_date = (
                start_date_node.date()
                if start_date_node
                else today - timedelta(days=7)  # Fallback if parsing fails
            )

            # Build the SQL query to fetch all dates >= start_date
            statement = (
                select(Output_Reports.date)
                .where(Output_Reports.date >= start_date)
                .order_by(Output_Reports.date.desc())
            )

            results = session.exec(
                statement
            ).all()  # Returns a list of date or string values

            # Remove duplicates and sort in descending order
            unique_dates = sorted(set(results), reverse=True)

            # Normalize all values into "YYYY-MM-DD" formatted strings
            unique_dates_str = [
                unique_date.strftime("%Y-%m-%d")
                if isinstance(unique_date, (datetime, date))
                else str(unique_date)
                for unique_date in unique_dates
            ]

        return unique_dates_str
