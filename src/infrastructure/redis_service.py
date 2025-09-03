import redis
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


def main():
    redis_client = RedisBase("process_123")
    redis_client.set_log("Process started")
    redis_client.set_log("Still running...")
    logs = redis_client.get_log()
    print("Logs:\n", logs)


if __name__ == "__main__":
    main()
