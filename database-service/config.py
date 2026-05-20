from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv()

def get_env_value(name: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and (value is None or value.strip() == ""):
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

DB_USER = get_env_value("DB_USER", required=True)
DB_PASSWORD = get_env_value("DB_PASSWORD", required=True)
DB_HOST = get_env_value("DB_HOST", required=True)
DB_PORT = get_env_value("DB_PORT", required=True)
DB_NAME = get_env_value("DB_NAME", required=True)

RABBITMQ_HOST = get_env_value("RABBITMQ_HOST", required=True)
RABBITMQ_PORT = int(get_env_value("RABBITMQ_PORT", required=True))
RABBITMQ_USER = get_env_value("RABBITMQ_USER", required=True)
RABBITMQ_PASS = get_env_value("RABBITMQ_PASS", required=True)

QUEUE_NAME = get_env_value("QUEUE_NAME", required=True)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = (
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )