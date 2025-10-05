import clickhouse_connect
from src.config import config
import pandas as pd


class ClickHouse:
    def __init__(self) -> None:
        self.client = clickhouse_connect.get_client(
            host=config.CLICKHOUSE_HOST,
            user=config.CLICKHOUSE_USER,
            password=config.CLICKHOUSE_PASSWORD,
            secure=True,
        )

    def get_db(self):
        query = self.client.query("SHOW databases")
        results = query.named_results()
        print(list(results))

    def insert_into_db(self, records: list[dict]) -> None:
        """Convert data into dataframe and send to clickhouse"""
        print("Getting the dataframe and sending to clickhouse")
        df = pd.DataFrame(records)
        self.client.insert_df("brands", df=df, database="default")

    def get_brand_mention(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str,
        start_date: str,
    ) -> dict:
        stmt = f"""
            SELECT SUM(mention_count) AS total_mentions, toDateTime(date) AS date
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
              AND date >= '{start_date}' AND date <= '{end_date}'
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

        position = (brand_position / all_positions) * 100
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
