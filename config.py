import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # PostgreSQL 配置
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

    # Redis 配置
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))

    # API 服务端口
    QUERY_API_PORT = int(os.getenv("QUERY_API_PORT", 5000))
    CONSUMER_SERVICE_PORT = int(os.getenv("CONSUMER_SERVICE_PORT", 5001))

    # MTA API 配置
    MTA_API_URL = os.getenv("MTA_API_URL")
    FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", 30))