from src.config import config
from src.infrastructure.llm_service import LLMService
from taskiq_redis import RedisAsyncResultBackend, ListQueueBroker

# Redis Backend
result_backend = RedisAsyncResultBackend(
    redis_url=config.REDIS_URL,
    result_ex_time=86400,
)

# Redis Broker
broker = ListQueueBroker(
    url=config.REDIS_URL,
).with_result_backend(result_backend)


# LLM Run Task
@broker.task
async def run_llm_task(prompt_id: str, process_id: str, s3_key: str):
    llm_class = LLMService(prompt_id, process_id)
    await llm_class.main(s3_key)
