import asyncio
from contextlib import asynccontextmanager
import redis.asyncio as redis
import logging
from src.config import config


class AsyncRedisBase:
    def __init__(self, prompt_id: str):
        self.host = config.REDIS_HOST
        self.port = config.REDIS_PORT
        self.prompt_id = prompt_id
        self.redis_db = config.REDIS_DB

    @asynccontextmanager
    async def redis_session(self):
        session = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.redis_db,
            decode_responses=True,
        )
        try:
            yield session
        except Exception as e:
            print(f"REDIS: Session error {e}")
        finally:
            await session.aclose()

    # To set a log (async)
    async def set_log(self, message: str):
        async with self.redis_session() as session:
            await session.lpush(self.prompt_id, message)
            await session.expire(self.prompt_id, 86400)  # 24 Hours Expiry

    # To retrieve logs (async)
    async def get_log(self) -> str:
        async with self.redis_session() as session:
            values = await session.lrange(self.prompt_id, 0, -1)
            values.reverse()
            return " \n".join(values)


class RedisLogHandler(logging.Handler):
    def __init__(self, redis_logger: AsyncRedisBase):
        super().__init__()
        self.redis_logger = redis_logger

    def emit(self, record):
        msg = self.format(record)
        asyncio.create_task(self.redis_logger.set_log(msg))
