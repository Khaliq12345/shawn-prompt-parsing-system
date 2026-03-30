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

# Your existing settings
app.conf.worker_prefetch_multiplier = 1
app.conf.task_acks_late = True

# --- Crash & restart resilience ---
app.conf.worker_max_tasks_per_child = (
    200  # Restart worker process after N tasks (prevents memory leaks)
)
app.conf.worker_max_memory_per_child = (
    200_000  # Restart if worker exceeds 200MB (in KB)
)

# --- Connection resilience ---
app.conf.broker_connection_retry_on_startup = True
app.conf.broker_connection_retry = True
app.conf.broker_connection_max_retries = None  # Retry forever
app.conf.broker_transport_options = {
    "visibility_timeout": 3600,  # 1 hour — match your longest task
    "socket_keepalive": True,
    "retry_on_timeout": True,
}

# --- Task failure resilience ---
app.conf.task_reject_on_worker_lost = (
    True  # Re-queue tasks if worker dies mid-execution
)
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"

# --- Heartbeat & health ---
app.conf.broker_heartbeat = 10  # Detect dead broker connections faster
app.conf.broker_heartbeat_checkrate = 2


@app.task
def run_browser(
    process_id: str,
    brand_report_id: str,
    prompt_id: str,
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
        prompt_id=prompt_id,
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
