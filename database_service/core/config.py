import os
from dotenv import load_dotenv

load_dotenv()

def env(name: str):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing env: {name}")
    return value

DB_USER = env("DB_USER")
DB_PASSWORD = env("DB_PASSWORD")
DB_HOST = env("DB_HOST")
DB_PORT = env("DB_PORT")
DB_NAME = env("DB_NAME")

DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

RABBITMQ_HOST = env("RABBITMQ_HOST")
RABBITMQ_PORT = int(env("RABBITMQ_PORT"))
RABBITMQ_USER = env("RABBITMQ_USER")
RABBITMQ_PASS = env("RABBITMQ_PASS")

QUEUE_NAME = env("QUEUE_NAME")