from collections import defaultdict
import clickhouse_connect
import sqlmodel as db
from sqlmodel import MetaData, create_engine
from clickhouse_connect.cc_sqlalchemy.ddl.tableengine import MergeTree
from clickhouse_connect.cc_sqlalchemy.datatypes.sqltypes import (
    Int64,
    String,
    DateTime,
)
from src.config import config
import pandas as pd


class ClickHouse:
    def __init__(self) -> None:
        self.client = clickhouse_connect.get_client(
            host=config.CLICKHOUSE_HOST,
            user=config.CLICKHOUSE_USER,
            password=config.CLICKHOUSE_PASSWORD,
            # secure=True,
        )
        self.engine = create_engine(
            f"clickhousedb://{config.CLICKHOUSE_USER}:{config.CLICKHOUSE_PASSWORD}@{config.CLICKHOUSE_HOST}:{config.CLICKHOUSE_PORT}/{config.CLICKHOUSE_DB}?compression=zstd"
        )
        self.table = "brands"

    def create_table(self):
        # Tables
        with self.engine.begin() as conn:
            metadata = MetaData(schema=config.CLICKHOUSE_DB)
            table = db.Table(
                self.table,
                metadata,
                db.Column("brand_report_id", String),
                db.Column("brand", String),
                db.Column("mention_count", Int64),
                db.Column("position", Int64),
                db.Column("date", DateTime),
                db.Column("model", String),
                MergeTree(order_by="date"),
            )
            table.create(conn, checkfirst=True)

    def get_db(self):
        query = self.client.query("SHOW databases")
        results = query.named_results()
        print(list(results))

    def insert_into_db(self, records: list[dict]) -> None:
        """Convert data into dataframe and send to clickhouse"""
        print("Getting the dataframe and sending to clickhouse")
        df = pd.DataFrame(records)
        if df.empty:
            return None
        self.client.insert_df(self.table, df=df, database="default")

    def get_brand_mention(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str,
        start_date: str,
    ) -> dict:
        print(start_date, end_date)
        stmt = f"""
            SELECT SUM(mention_count) AS total_mentions
            FROM default.brands
            WHERE brand = '{brand}'
              AND brand_report_id = '{brand_report_id}'
              AND date <= '{start_date}' AND date >= '{end_date}'
              {"AND model = '" + model + "'" if model != "all" else ""}
            GROUP BY date
        """
        query = self.client.query(stmt)
        if not query.row_count:
            return {"data": 0}
        return {"data": query.first_item.get("total_mentions") or 0}

    def get_brand_sov(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str,
        start_date: str,
    ) -> dict:
        stmt = f"""
            SELECT
                (SUM(CASE WHEN brand = '{brand}' THEN mention_count ELSE 0 END)
                 / SUM(mention_count)) * 100 AS sov,  toDateTime(date) AS date
            FROM default.brands
            WHERE brand_report_id = '{brand_report_id}'
                AND date <= '{start_date}' AND date >= '{end_date}'
                {"AND model = '" + model + "'" if model != "all" else ""}
            GROUP BY date
        """
        query = self.client.query(stmt)
        if not query.row_count:
            return {"data": 0.0}
        return {"data": query.first_item.get("sov") or 0.0}

    def get_brand_coverage(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str,
        start_date: str,
    ) -> dict:
        stmt = f"""
            SELECT
                COUNT(*) AS total_rows,
                countIf(mention_count >= 1 AND brand = '{brand}') AS mentioned_rows
            FROM default.brands
            WHERE brand_report_id = '{brand_report_id}'
                AND date <= '{start_date}' AND date >= '{end_date}'
                {"AND model = '" + model + "'" if model != "all" else ""}
        """

        result = self.client.query(stmt).first_item
        total = result.get("total_rows", 0)
        mentioned = result.get("mentioned_rows", 0)

        coverage = (mentioned / total) * 100 if total > 0 else 0.0
        return {"data": coverage}

    def get_brand_position(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str,
        start_date: str,
    ) -> dict:
        stmt = f"""
            SELECT
                SUM(brands.position) as all_position,
                sumIf(brands.position, brands.brand = '{brand}') as brand_position
            FROM default.brands
            WHERE brand_report_id = '{brand_report_id}'
              AND date <= '{start_date}' AND date >= '{end_date}'
              {"AND model = '" + model + "'" if model != "all" else ""}
        """
        result = self.client.query(stmt).first_item
        all_positions = result.get("all_position") or 0
        brand_position = result.get("brand_position") or 0
        print(all_positions, brand_position)

        position = brand_position / all_positions
        return {"data": position}

    def get_brand_ranking(
        self,
        brand_report_id: str,
        start_date: str,
        end_date: str,
        model: str,
    ) -> list:
        stmt = f"""
            SELECT brands.brand, SUM(brands.mention_count) as total_mentions
            FROM default.brands
            WHERE brand_report_id = '{brand_report_id}'
              AND date <= '{start_date}' AND date >= '{end_date}'
              {"AND model = '" + model + "'" if model != "all" else ""}
            GROUP BY brands.brand
            ORDER BY total_mentions DESCENDING
        """
        query = self.client.query(stmt)
        if not query.row_count:
            return []

        results = query.named_results()
        ranking = []

        # calculate the ranking of the brands
        prev_mentions = None
        rank = 0
        skip = 1
        for row in results:
            mentions = row["total_mentions"] or 0
            if mentions == prev_mentions:
                skip += 1
            else:
                rank += skip
                skip = 1
            ranking.append(
                {
                    "rank": rank,
                    "brand_name": row["brand"],
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
        stmt = f"""
            SELECT
                date,
                brands.brand,
                SUM(brands.mention_count) AS total_mentions
            FROM default.brands
            WHERE brand_report_id = '{brand_report_id}'
            AND date <= '{start_date}' AND date >= '{end_date}'
            {"AND model = '" + model + "'" if model != "all" else ""}
            GROUP BY date, brands.brand
            ORDER BY date ASC, total_mentions DESC
        """

        query = self.client.query(stmt)
        if not query.row_count:
            return []

        results = query.named_results()
        ranking_over_time = []

        # group results by date

        grouped = defaultdict(list)
        for row in results:
            grouped[row["date"]].append(row)

        # calculate competition ranking per date
        for date, rows in grouped.items():
            prev_mentions = None
            rank = 0
            skip = 1
            date_rankings = []

            for row in rows:
                mentions = row["total_mentions"] or 0
                if mentions == prev_mentions:
                    skip += 1
                else:
                    rank += skip
                    skip = 1
                date_rankings.append(
                    {
                        "date": date,
                        "rank": rank,
                        "brand_name": row["brand"],
                        "mention_count": mentions,
                    }
                )
                prev_mentions = mentions

            ranking_over_time.extend(date_rankings)

        return ranking_over_time
