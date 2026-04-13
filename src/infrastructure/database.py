from collections import defaultdict
import sys

sys.path.append("..")

import json
from datetime import date, datetime, timedelta
from typing import List, Optional

import dateparser
from sqlmodel import Session, and_, create_engine, select, text

from src.config import config
from src.infrastructure.models import (
    Brands,
    Citations,
    Output_Reports,
    Sentiments,
    SQLModel,
    Token_Reports,
)


class DataBase:
    def __init__(self) -> None:
        self.engine = create_engine(
            f"postgresql+psycopg://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}:5432/{config.DB_NAME}"
        )
        self.create_all_tables()

    def create_all_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def save_all(
        self,
        brands: list[Brands],
        citations: list[Citations],
        sentiments: list[Sentiments],
        output_report: Output_Reports,
    ):
        print("Bulk Saving all data …")
        with Session(self.engine) as session:
            session.add_all(brands)
            session.add_all(citations)
            session.add_all(sentiments)
            session.add(output_report)
            session.commit()
            session.close()

    def save_brands(self, brands: list[Brands]) -> None:
        """Bulk-insert a list of record dicts into the brands table."""
        print("Saving analysis data …")
        with Session(self.engine) as session:
            session.add_all(brands)
            session.commit()
            session.close()

    def save_citations(self, citations: list[Citations]) -> None:
        print("Saving citations")
        with Session(self.engine) as session:
            session.add_all(citations)
            session.commit()
            session.close()

    def save_sentiments(self, sentiments: list[Sentiments]) -> None:
        print("Saving Sentiments")
        with Session(self.engine) as session:
            session.add_all(sentiments)
            session.commit()
            session.close()

    def save_output_reports(self, output_report: Output_Reports) -> None:
        print("Saving Output report")
        with Session(self.engine) as session:
            session.add(output_report)
            session.commit()
            session.close()

    def save_token_usage(self, token_data: Token_Reports) -> None:
        print("Saving token usage")
        with Session(self.engine) as session:
            session.add(token_data)
            session.commit()
            session.close()

    def get_reports(
        self, brand_report_id: str, limit: int = 20, offset: int = 0
    ) -> list[dict]:
        """Get all the reports from the output_reports table"""
        with Session(self.engine) as session:
            stmt = (
                select(Output_Reports)
                .where(Output_Reports.brand_report_id == brand_report_id)
                .limit(limit)
                .offset(offset)
            )
            results = session.exec(stmt).all()
            session.close()

        reports = [json.loads(result.model_dump_json()) for result in results]
        return reports

    def get_report_outputs(
        self,
        brand_report_id: str,
        prompt_id: str,
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
                    .where(
                        and_(
                            Output_Reports.brand_report_id == brand_report_id,
                            Output_Reports.prompt_id == prompt_id,
                        )
                    )
                    .order_by(Output_Reports.date.desc())
                ).first()

                if not latest_date:
                    return None

                date = latest_date

            print(date)
            # Base query
            statement = select(Output_Reports).where(
                Output_Reports.brand_report_id == brand_report_id,
                Output_Reports.prompt_id == prompt_id,
                Output_Reports.date == date,
            )

            # Apply optional model filter
            if model.lower() != "all":
                statement = statement.where(Output_Reports.model == model)

            result = session.exec(statement).first()

            session.close()

            if not result:
                return None

            return {"snapshot": result.snapshot, "markdown": result.markdown}

    def get_citations(
        self,
        prompt_id: str,
        date: Optional[str] = None,
        model: str = "all",
    ) -> list[dict]:
        """
        Retrieve a list of citations for a given report.

        Args:
            prompt_id (str): Identifier of the brand report.
            date (str | None): Optional specific date. If not provided, the most recent date is used.
            model (str): Optional model filter. Use "all" to ignore model filtering.

        Returns:
            list[dict]: List of citation objects as dictionaries.
        """
        with Session(self.engine) as session:
            if date is None:
                latest_date = session.exec(
                    select(Citations.date)
                    .where(Citations.prompt_id == prompt_id)
                    .order_by(Citations.date.desc())
                ).first()

                if not latest_date:
                    return []

                date = latest_date

            statement = select(Citations).where(
                Citations.prompt_id == prompt_id,
                Citations.date == date,
            )

            if model.lower() != "all":
                statement = statement.where(Citations.model == model)

            results = session.exec(statement).all()
            session.close()

        citations = [json.loads(result.model_dump_json()) for result in results]
        return citations

    def get_citations_by_report(
        self,
        brand_report_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        model: str = "all",
    ) -> List[dict]:
        print(start_date, end_date)
        """
        Retrieve citations for a given brand report within a date range.

        Args:
            brand_report_id (str): Identifier of the brand report.
            start_date (str | None): Start date filter.
            end_date (str | None): End date filter.
            model (str): Optional model filter. Use "all" to ignore.

        Returns:
            list[dict]: List of citation objects.
        """

        with Session(self.engine) as session:
            statement = select(Citations).where(
                Citations.brand_report_id == brand_report_id
            )

            # ---- Date filtering ----
            if start_date:
                statement = statement.where(Citations.date >= start_date)

            if end_date:
                statement = statement.where(Citations.date <= end_date)

            # ---- Model filtering ----
            if model.lower() != "all":
                statement = statement.where(Citations.model == model)

            results = session.exec(statement).all()
            session.close()

        citations = [json.loads(result.model_dump_json()) for result in results]
        return citations

    def get_sentiments(
        self,
        prompt_id: str,
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
                    .where(Sentiments.prompt_id == prompt_id)
                    .order_by(Sentiments.date.desc())
                ).first()

                if not latest_date:
                    return []

                date = latest_date

            statement = select(Sentiments).where(
                Sentiments.prompt_id == prompt_id,
                Sentiments.date == date,
            )

            if model.lower() != "all":
                statement = statement.where(Sentiments.model == model)

            results = session.exec(statement).all()
            session.close()

        sentiments = [json.loads(result.model_dump_json()) for result in results]
        return sentiments

    def get_report_dates(
        self, prompt_id: str, max_dates: str = "7 days ago"
    ) -> list[str]:
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
                .where(
                    and_(
                        Output_Reports.date >= start_date,
                        Output_Reports.prompt_id == prompt_id,
                    )
                )
                .order_by(Output_Reports.date.desc())
            )

            results = session.exec(
                statement
            ).all()  # Returns a list of date or string values

            # Remove duplicates and sort in descending order
            unique_dates = sorted(set(results), reverse=True)

            # Normalize all values into "YYYY-MM-DD" formatted strings
            unique_dates_str = [
                (
                    unique_date.strftime("%Y-%m-%d")
                    if isinstance(unique_date, (datetime, date))
                    else str(unique_date)
                )
                for unique_date in unique_dates
            ]

            session.close()

        return unique_dates_str

    # ------------------------DOMAIN-----------------------------------

    def get_markdown_s3_keys(
        self,
        brand_report_id: str,
        start_date: str,
        end_date: str,
        model: str,
    ):
        """Get the citation for a particular domain"""
        s3_keys = []
        with Session(self.engine) as session:
            # get all s3 keys of the selected brand_report_id
            stmt = select(Output_Reports.markdown).where(
                Output_Reports.brand_report_id == brand_report_id
            )
            if start_date:
                stmt.where(Output_Reports.date <= start_date)
            if end_date:
                stmt.where(Output_Reports.date <= end_date)
            if model != "all":
                stmt = stmt.where(Output_Reports.model == model)
            results = session.exec(stmt).all()
            for result in results:
                s3_keys.append(result)

            session.close()
        return s3_keys

    # ------------------------PROMPT-------------------------
    def get_prompt(self, prompt_id: str) -> str:
        with Session(self.engine) as session:
            query = text(
                f"SELECT prompt FROM schedules WHERE prompt_id = '{prompt_id}'"
            )
            result = session.execute(query).scalar()
            return str(result) if result is not None else ""

    # --------------------------ANALYTICS------------------------------
    def get_brand_mention(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str,
        start_date: str,
    ) -> dict:
        model_filter = "AND model = :model" if model != "all" else ""
        stmt = text(
            f"""
            SELECT COALESCE(SUM(mention_count), 0) AS total_mentions
            FROM brands
            WHERE LOWER(brand)    = LOWER(:brand)
              AND brand_report_id = :brand_report_id
              AND date            >= CAST(:start_date AS DATE)
              AND date            <= CAST(:end_date AS DATE)
              {model_filter}
        """
        )
        params = dict(
            brand=brand,
            brand_report_id=brand_report_id,
            start_date=start_date,
            end_date=end_date,
        )
        if model != "all":
            params["model"] = model

        with Session(self.engine) as session:
            row = session.exec(stmt.bindparams(**params)).first()
            return {"data": row[0] if row else 0}

    def get_brand_sov(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str,
        start_date: str,
    ) -> dict:
        model_filter = "AND model = :model" if model != "all" else ""
        stmt = text(
            f"""
            SELECT
                (
                    SUM(
                        CASE
                            WHEN LOWER(brand) = LOWER(:brand)
                            THEN COALESCE(mention_count, 0)::FLOAT
                            ELSE 0
                        END
                    )
                    /
                    NULLIF(SUM(COALESCE(mention_count, 0)::FLOAT), 0)
                ) * 100 AS sov
            FROM brands
            WHERE brand_report_id = :brand_report_id
                AND date >= CAST(:start_date AS DATE)
                AND date <= CAST(:end_date AS DATE)
                {model_filter}
        """
        )
        params = dict(
            brand=brand,
            brand_report_id=brand_report_id,
            start_date=start_date,
            end_date=end_date,
        )
        if model != "all":
            params["model"] = model

        with Session(self.engine) as session:
            row = session.exec(stmt.bindparams(**params)).first()
            sov = row[0] if row else None
            return {"data": round(float(sov), 2) if sov else 0.0}

    def get_brand_coverage(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str,
        start_date: str,
    ) -> dict:
        model_filter = "AND model = :model" if model != "all" else ""
        stmt = text(
            f"""
            SELECT
                COUNT(*) AS total_s3_keys,
                COUNT(*) FILTER (WHERE has_mention = 1) AS mentioned_s3_keys
            FROM (
                SELECT
                    s3_key,
                    MAX(
                        CASE
                            WHEN LOWER(brand) = LOWER(:brand)
                                 AND COALESCE(mention_count, 0) >= 1
                            THEN 1 ELSE 0
                        END
                    ) AS has_mention
                FROM brands
                WHERE brand_report_id = :brand_report_id
                  AND date >= CAST(:start_date AS DATE)
                  AND date <= CAST(:end_date AS DATE)
                  {model_filter}
                GROUP BY s3_key
            ) subquery
        """
        )
        params = dict(
            brand=brand,
            brand_report_id=brand_report_id,
            start_date=start_date,
            end_date=end_date,
        )
        if model != "all":
            params["model"] = model

        with Session(self.engine) as session:
            row = session.exec(stmt.bindparams(**params)).first()
            total = row[0] if row else 0
            mentioned = row[1] if row else 0
            coverage = (mentioned / total) * 100 if total else 0
            return {"data": coverage}

    def get_brand_position(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str,
        start_date: str,
    ) -> dict:
        model_filter = "AND model = :model" if model != "all" else ""
        stmt = text(
            f"""
            SELECT
                SUM(position) FILTER (WHERE LOWER(brand) = LOWER(:brand)) AS total_position,
                COUNT(*)      FILTER (WHERE LOWER(brand) = LOWER(:brand)) AS brand_count
            FROM brands
            WHERE brand_report_id = :brand_report_id
                AND date >= CAST(:start_date AS DATE)
                AND date <= CAST(:end_date AS DATE)
                {model_filter}
        """
        )
        params = dict(
            brand=brand,
            brand_report_id=brand_report_id,
            start_date=start_date,
            end_date=end_date,
        )
        if model != "all":
            params["model"] = model

        with Session(self.engine) as session:
            row = session.exec(stmt.bindparams(**params)).first()
            total_position = row[0] or 0
            brand_count = row[1] or 0
            if brand_count == 0:
                return {"data": 0}
            avg_position = total_position / brand_count
            return {"data": int(avg_position)}


    def get_brand_ranking(
        self,
        brand_report_id: str,
        start_date: str,
        end_date: str,
        model: str,
    ) -> list:
        model_filter = "AND model = :model" if model != "all" else ""
        stmt = text(
            f"""
            SELECT brand, SUM(mention_count) AS total_mentions
            FROM brands
            WHERE brand_report_id = :brand_report_id
                AND date >= CAST(:start_date AS DATE)
                AND date <= CAST(:end_date AS DATE)
                {model_filter}
            GROUP BY brand
            ORDER BY total_mentions DESC
        """
        )
        params = dict(
            brand_report_id=brand_report_id,
            start_date=start_date,
            end_date=end_date,
        )
        if model != "all":
            params["model"] = model

        with Session(self.engine) as session:
            rows = session.exec(stmt.bindparams(**params)).fetchall()

        if not rows:
            return []

        ranking = []
        prev_mentions = None
        rank = 0
        skip = 1
        for row in rows:
            mentions = row[1] or 0
            if mentions == prev_mentions:
                skip += 1
            else:
                rank += skip
                skip = 1
            ranking.append(
                {
                    "rank": rank,
                    "brand_name": row[0],
                    "mention_count": mentions,
                }
            )
            prev_mentions = mentions
        return ranking


    def get_brand_ranking_over_time(
        self,
        brand_report_id: str,
        start_date: str,
        end_date: str,
        model: str,
    ) -> list:
        model_filter = "AND model = :model" if model != "all" else ""
        stmt = text(
            f"""
            SELECT
                date::DATE AS day,
                brand,
                SUM(mention_count) AS total_mentions
            FROM brands
            WHERE brand_report_id = :brand_report_id
                AND date >= CAST(:start_date AS DATE)
                AND date <= CAST(:end_date AS DATE)
                {model_filter}
            GROUP BY day, brand
            ORDER BY day ASC, total_mentions DESC
        """
        )
        params = dict(
            brand_report_id=brand_report_id,
            start_date=start_date,
            end_date=end_date,
        )
        if model != "all":
            params["model"] = model

        with Session(self.engine) as session:
            rows = session.exec(stmt.bindparams(**params)).fetchall()

        if not rows:
            return []

        grouped_by_date = defaultdict(list)
        for row in rows:
            grouped_by_date[row[0]].append(row)

        brand_points = defaultdict(list)
        for day in sorted(grouped_by_date.keys()):
            day_rows = grouped_by_date[day]
            prev_mentions = None
            rank = 0
            skip = 1
            for row in day_rows:
                mentions = row[2] or 0
                if mentions == prev_mentions:
                    skip += 1
                else:
                    rank += skip
                    skip = 1
                brand_points[row[1]].append(
                    {
                        "date": day,
                        "rank": rank,
                        "mention_count": mentions,
                    }
                )
                prev_mentions = mentions

        return [
            {"brand_name": brand_name, "points": points}
            for brand_name, points in brand_points.items()
        ]
