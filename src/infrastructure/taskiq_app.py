from src.infrastructure.llm_service import LLMService
import taskiq_fastapi
from taskiq import ZeroMQBroker

broker = ZeroMQBroker()

taskiq_fastapi.init(broker, "src.api.app:app")


# LLM Run Task
@broker.task
async def run_llm_task(prompt_id: str, process_id: str, s3_key: str):
    llm_class = LLMService(prompt_id, process_id)
    await llm_class.main(s3_key)
