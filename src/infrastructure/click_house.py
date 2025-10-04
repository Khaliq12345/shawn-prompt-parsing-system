import datetime
from typing import Optional
import clickhouse_connect
from src.config import config


class ClickHouse:
    def __init__(self) -> None:
        self.client = clickhouse_connect.get_client(
            host=config.CLICKHOUSE_HOST,
            user=config.CLICKHOUSE_USER,
            password=config.CLICKHOUSE_PASSWORD,
            secure=True,
        )
        self.today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_db(self):
        query = self.client.query("SHOW databases")
        results = query.named_results()
        print(list(results))

    def get_brand_mention(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str = "all",
        start_date: str = "",
    ) -> Optional[dict]:
        """Get total mention based on selected date"""
        start_date = start_date if start_date else self.today
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
            return None
        return {"data": query.first_item.get("total_mentions")}

    def get_brand_sov(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str = "all",
        start_date: str = "",
    ) -> Optional[dict]:
        """Get the brand shared of voice based on selected date"""
        start_date = start_date if start_date else self.today
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
            return None
        return {"data": query.first_item.get("sov")}

    def get_brand_coverage(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str = "all",
        start_date: str = "",
    ) -> Optional[dict]:
        """Get the brand coverage percentage"""
        start_date = start_date if start_date else self.today

        # Total lignes dans l'échantillon
        total_stmt = f"""
            SELECT COUNT(*) AS total_rows
            FROM default.brands
            WHERE brand_report_id = '{brand_report_id}'
              AND date <= '{start_date}' AND date >= '{end_date}'
              {"AND model = '" + model + "'" if model != "all" else ""}
        """

        # Lignes où mention_count >= 1 pour la marque
        mention_stmt = f"""
            SELECT COUNT(*) AS mentioned_rows
            FROM default.brands
            WHERE brand = '{brand}'
              AND brand_report_id = '{brand_report_id}'
              AND mention_count >= 1
              AND date <= '{start_date}' AND date >= '{end_date}'
              {"AND model = '" + model + "'" if model != "all" else ""}
        """

        total = self.client.query(total_stmt).first_item.get("total_rows") or 0
        mentioned = (
            self.client.query(mention_stmt).first_item.get("mentioned_rows")
            or 0
        )
        coverage = (mentioned / total) * 100
        return {"data": coverage}

    def get_brand_position(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str = "all",
        start_date: str = "",
    ) -> Optional[dict]:
        """Get the brand position"""
        start_date = start_date if start_date else self.today

        stmt = f"""
            SELECT 
                SUM(position) AS sum_positions,
                SUM(mention_count) AS sum_mentions
            FROM default.brands
            WHERE brand = '{brand}'
              AND brand_report_id = '{brand_report_id}'
              AND mention_count >= 1
              AND date <= '{start_date}' AND date >= '{end_date}'
              {"AND model = '" + model + "'" if model != "all" else ""}
        """

        result = self.client.query(stmt).first_item
        sum_positions = result.get("sum_positions") or 0
        sum_mentions = result.get("sum_mentions") or 0

        if sum_mentions == 0:
            return None

        position = (sum_positions / sum_mentions) * 100
        return {"data": position}

    def get_brand_ranking(self) -> Optional[list]:
        """Get ranking of all brands by mention_count (with ties, standard competition ranking)"""

        stmt = """
            SELECT 
                brand,
                SUM(mention_count) AS total_mentions
            FROM default.brands
            GROUP BY brand
            ORDER BY total_mentions DESC
        """

        query = self.client.query(stmt)
        if not query.row_count:
            return None

        results = query.named_results()
        ranking = []

        prev_mentions = None
        rank = 0
        skip = 1  # nombre de marques ayant le même rang

        for row in results:
            mentions = row["total_mentions"] or 0
            if mentions == prev_mentions:
                # même nombre de mentions → même rang
                skip += 1
            else:
                # nouveau nombre → rang = rang précédent + nombre de doublons
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


if __name__ == "__main__":
    clickHouse = ClickHouse()

    mentions = clickHouse.get_brand_mention(
        "Nike", "br_016", end_date="2025-09-01", model="ChatGPT"
    )
    sov = clickHouse.get_brand_sov(
        "Nike", "br_016", end_date="2025-09-01", model="ChatGPT"
    )
    print("Mentions:", mentions)
    print("Share of Voice:", sov)

    coverage = clickHouse.get_brand_coverage(
        "Nike", "br_016", end_date="2025-09-01", model="ChatGPT"
    )
    position = clickHouse.get_brand_position(
        "Nike", "br_016", end_date="2025-09-01", model="ChatGPT"
    )
    ranking = clickHouse.get_brand_ranking()

    print("Brand Ranking Dictionary:", ranking)
    print("Brand Coverage:", coverage)
    print("Brand Position:", position)
