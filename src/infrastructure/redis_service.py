import redis
import logging
from src.config import config


class RedisBase:
    def __init__(self, process_id: str):
        self.host = config.REDIS_HOST
        self.port = config.REDIS_PORT
        self.process_id = process_id
        self.redis_db = config.REDIS_DB

    # Redis session (synchronous)
    def redis_session(self):
        return redis.Redis(
            host=self.host,
            port=self.port,
            db=self.redis_db,
            decode_responses=True,
        )

    # To set a log (sync)
    def set_log(self, message: str):
        session = self.redis_session()
        try:
            session.lpush(self.process_id, message)
        except Exception as e:
            print(f"REDIS: Session error {e}")
        finally:
            session.close()

    # To retrieve logs (sync)
    def get_log(self) -> str:
        session = self.redis_session()
        try:
            values = session.lrange(self.process_id, 0, -1)
            values.reverse()
            return " \n".join(values)
        except Exception as e:
            print(f"REDIS: Session error {e}")
            return ""
        finally:
            session.close()


class RedisLogHandler(logging.Handler):
    def __init__(self, redis_logger: RedisBase):
        super().__init__()
        self.redis_logger = redis_logger

    def emit(self, record):
        try:
            log_entry = self.format(record)
            self.redis_logger.set_log(log_entry)
        except Exception as e:
            print(f"RedisLogHandler error: {e}")

