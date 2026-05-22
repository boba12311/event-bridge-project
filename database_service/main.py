"""
Database Service — Микросервис сохранения регистраций.

Запускает потребитель сообщений из RabbitMQ и сохраняет данные в PostgreSQL.
"""

import logging

from core.config import QUEUE_NAME, DATABASE_URL
from db.db_utils import init_db
from messaging.rabbitmq import start_consuming, on_message

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Точка входа в сервис."""
    logger.info("=" * 60)
    logger.info("Database Service запущен")
    logger.info(f"Очередь: {QUEUE_NAME}")
    logger.info(f"БД: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
    logger.info("=" * 60)
    
    init_db()
    
    start_consuming(on_message_callback=on_message)


if __name__ == "__main__":
    main()