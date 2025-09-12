import os
from dotenv import load_dotenv

load_dotenv()

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-flash")
BUCKET_NAME = os.getenv("BUCKET_NAME", "browser-outputs")
# Database
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_HOST = os.getenv("DB_HOST")
# AWS
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
# REDIS
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
# APP
ENV = os.getenv("ENV", "dev")
APP_PORT = int(os.getenv("APP_PORT", 8000))
