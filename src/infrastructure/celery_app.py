from celery import Celery
import logging
from src.infrastructure.redis_service import RedisBase, RedisLogHandler
from src.config.config import REDIS_URL
from src.infrastructure.llm_service import LLMService

app = Celery(
    "tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
)


@app.task
def run_browser(
    process_id: str,
    brand_report_id: str,
    model: str,
    brand: str,
    s3_key: str,
    languague: str,
    date: str,
):
    redis_handler = None
    # Redis log wrapper
    redis_logger = RedisBase(process_id)

    # Crée un logger spécifique pour cette tâche
    task_logger = logging.getLogger(f"{__name__}.{process_id}")
    task_logger.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    task_logger.addHandler(console)

    # Ajoute le handler Redis si pas déjà présent
    if not any(isinstance(h, RedisLogHandler) for h in task_logger.handlers):
        redis_handler = RedisLogHandler(redis_logger)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        redis_handler.setFormatter(formatter)
        task_logger.addHandler(redis_handler)

    task_logger.info("Parsing logger initialised")

    matching_scraper = LLMService(
        process_id=process_id,
        brand_report_id=brand_report_id,
        date=date,
        model=model,
        brand=brand,
        s3_key=s3_key,
        logger=task_logger,
    )
    matching_scraper.main()
    if redis_handler:
        task_logger.removeHandler(redis_handler)
        task_logger.removeHandler(console)
