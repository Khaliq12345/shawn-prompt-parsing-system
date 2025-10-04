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
    ) -> dict:
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
            return {"data": 0}
        return {"data": query.first_item.get("total_mentions") or 0}

    def get_brand_sov(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str = "all",
        start_date: str = "",
    ) -> dict:
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
            return {"data": 0.0}
        return {"data": query.first_item.get("sov") or 0.0}

    def get_brand_coverage(
        self,
        brand: str,
        brand_report_id: str,
        end_date: str,
        model: str = "all",
        start_date: str = "",
    ) -> dict:
        start_date = start_date if start_date else self.today

        total_stmt = f"""
            SELECT COUNT(*) AS total_rows
            FROM default.brands
            WHERE brand_report_id = '{brand_report_id}'
              AND date <= '{start_date}' AND date >= '{end_date}'
              {"AND model = '" + model + "'" if model != "all" else ""}
        """
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
        mentioned = self.client.query(mention_stmt).first_item.get("mentioned_rows") or 0

        coverage = (mentioned / total) * 100 if total > 0 else 0.0
        return {"data": coverage}

    def get_brand_position(
        self,
        brand: str,
        brand_report_id: str = "",
        start_date: str = "",
        end_date: str = "",
        model: str = "all"
    ) -> dict:
        """Calcule la position relative d'une marque dans l'échantillon filtré en pourcentage."""

        # Construction des filtres SQL
        where_clauses = ["mention_count >= 1"]
        if brand_report_id:
            where_clauses.append(f"brand_report_id = '{brand_report_id}'")
        if start_date:
            where_clauses.append(f"date >= '{start_date}'")
        if end_date:
            where_clauses.append(f"date <= '{end_date}'")
        if model != "all":
            where_clauses.append(f"model = '{model}'")
        
        where_sql = " AND ".join(where_clauses)

        # Somme des positions de la marque
        brand_stmt = f"""
            SELECT SUM(position) AS brand_sum_positions
            FROM default.brands
            WHERE brand = '{brand}' AND {where_sql}
        """
        brand_sum_positions = self.client.query(brand_stmt).first_item.get("brand_sum_positions") or 0

        # Somme des positions de toutes les marques dans l'échantillon filtré
        total_stmt = f"""
            SELECT SUM(position) AS total_sum_positions
            FROM default.brands
            WHERE {where_sql}
        """
        total_sum_positions = self.client.query(total_stmt).first_item.get("total_sum_positions") or 0

        # Calcul de la position relative en pourcentage
        position = (brand_sum_positions / total_sum_positions) * 100 if total_sum_positions > 0 else 0.0

        return {"data": position}
    

    def get_brand_ranking(
            self,
            brand_report_id: str = "",
            start_date: str = "",
            end_date: str = "",
            model: str = "all"
        ) -> list:
        # Construction de la clause WHERE selon les arguments fournis
        where_clauses = []
        if brand_report_id:
            where_clauses.append(f"brand_report_id = '{brand_report_id}'")
        if start_date:
            where_clauses.append(f"date >= '{start_date}'")
        if end_date:
            where_clauses.append(f"date <= '{end_date}'")
        if model != "all":
            where_clauses.append(f"model = '{model}'")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        stmt = f"""
            SELECT 
                brand,
                SUM(mention_count) AS total_mentions
            FROM default.brands
            {where_sql}
            GROUP BY brand
            ORDER BY total_mentions DESC
        """

        query = self.client.query(stmt)
        if not query.row_count:
            return []

        results = query.named_results()
        ranking = []

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
            ranking.append({
                "rank": rank,
                "brand_name": row["brand"],
                "mention_count": mentions
            })
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
    coverage = clickHouse.get_brand_coverage(
        "Nike", "br_016", end_date="2025-09-01", model="ChatGPT"
    )
    position = clickHouse.get_brand_position(
        "Nike", "br_016", end_date="2025-09-01", model="ChatGPT"
    )
    ranking = clickHouse.get_brand_ranking()

    print("Mentions:", mentions)
    print("Share of Voice:", sov)
    print("Brand Coverage:", coverage)
    print("Brand Position:", position)
    print("Brand Ranking Dictionary:", ranking)
