import sys
from typing import Optional
from urllib.parse import urlparse

sys.path.append(".")
from parsel import Selector
from src.infrastructure.aws_storage import AWSStorage
from src.infrastructure.database import DataBase
from src.infrastructure.models import Citations
import markdown2
from src.config import config


class LLMService:
    def __init__(self, brand_report_id: str, date: str, model: str, brand: str) -> None:
        # report ids
        self.brand_report_id = brand_report_id
        self.date = date
        self.model = model
        self.brand = brand
        # initialise others
        self.bucket = config.BUCKET_NAME
        self.storage = AWSStorage(self.bucket)
        # content
        self.content = ""
        # initialise db
        self.database = DataBase()

    def _download_and_clean_content(self, s3_key: str) -> str | None:
        self.content = self.storage.get_file_content(s3_key)
        if not self.content:
            return None
        # The original clean_markdown function was complex and tried to convert back to markdown.
        # The new logic just needs HTML, so we simplify.
        return markdown2.markdown(self.content)

    def get_citations_from_s3_path(self, s3_key: str) -> list[Citations]:
        html_content = self._download_and_clean_content(s3_key)
        if not html_content:
            return []

        selector = Selector(text=html_content)
        links = selector.css("a")
        
        citations_list = []
        for i, link in enumerate(links, start=1):
            url = link.css("::attr(href)").get()
            if not url:
                continue
            
            title = link.css("::text").get()
            domain = urlparse(url).netloc

            citation = Citations(
                brand_report_id=self.brand_report_id,
                date=self.date,
                model=self.model,
                brand=self.brand,
                rank=i,
                title=title.strip() if title else "",
                domain=domain,
                norm_url=url,
            )
            citations_list.append(citation)
        
        return citations_list


if __name__ == "__main__":
        # Bon j fait le test voi 

    def main():
        test_s3_key = "perplexity/1758452292/output.txt"
        test_brand_report_id = "report-123"
        test_date = "2025-10-04"
        test_model = "gemini-1.5"
        test_brand = "TestBrand"

        print("--- Initialisation du service ---")
        llm_service = LLMService(
            brand_report_id=test_brand_report_id,
            date=test_date,
            model=test_model,
            brand=test_brand,
        )

        print("--- Création des tables de la base de données (si nécessaire) ---")
        db = llm_service.database
        db.create_all_tables()

        print(f"--- Démarrage de l'extraction pour le fichier : {test_s3_key} ---")
        citations = llm_service.get_citations_from_s3_path(test_s3_key)

        if citations:
            print(f"--- {len(citations)} citations extraites. Sauvegarde en cours... ---")
            db.save_citations(citations)
            print("--- Sauvegarde terminée avec succès. ---")
        else:
            print("--- Aucune citation n'a été extraite. ---")
        
        print("--- Processus terminé. ---")

    main()
