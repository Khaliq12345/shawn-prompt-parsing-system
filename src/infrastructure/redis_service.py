import asyncio
from contextlib import asynccontextmanager
import redis.asyncio as redis

from src.config import config


class AsyncRedisBase:
    def __init__(self, process_id: str):
        self.host = config.REDIS_HOST
        self.port = config.REDIS_PORT
        self.process_id = process_id
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
            await session.lpush(self.process_id, message)

    # To retrieve logs (async)
    async def get_log(self) -> str:
        async with self.redis_session() as session:
            values = await session.lrange(self.process_id, 0, -1)
            values.reverse()
            return " \n".join(values)


async def main():
    redis_client = AsyncRedisBase("process_123")
    await redis_client.set_log("Process started")
    await redis_client.set_log("Still running...")
    logs = await redis_client.get_log()
    print("Logs:\n", logs)


if __name__ == "__main__":
    asyncio.run(main())
