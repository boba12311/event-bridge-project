"""Публикует сообщение в очередь"""

from typing import Any
import pika
import json
import time
from dotenv import load_dotenv
import time
import os

# Загружаем переменные из .env
load_dotenv()


class RabbitMQPublisher:
    def __init__(self, host: str = "localhost", port:int = 5672, max_retries: int = 10, retry_delay: int = 3, credentials: tuple[str, str] = ("guest", "guest")):
        self.host: str = host
        self.port: int = port
        self.credentials = pika.PlainCredentials(*credentials)
        self.connection: Any = None
        self.channel: Any = None
        self.max_retries: int = max_retries
        self.retry_delay: int = retry_delay

    def connect(self) -> None:
        if self.connection is not None and not self.connection.is_closed:
            return
        
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host = self.host,port = self.port, credentials=self.credentials))
        self.channel = self.connection.channel()

    def connect_with_retry(self) -> None:
            """Подключается с retry-механизмом, ожидая готовность Orchestrator'а"""
            for attempt in range(1, self.max_retries + 1):
                try:
                    self.connect()
                    return
                except pika.exceptions.AMQPConnectionError:
                    print("⏳ RabbitMQ ещё не готов (попытка %d/%d). Ждём %d сек...", end=" ")
                    print(    "⏳ RabbitMQ ещё не готов (попытка %d/%d). Ждём %d сек...",
                        attempt, self.max_retries, self.retry_delay
                    )
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                    else:
                        raise

    def publish(self, routing_key: str, message: dict[str, Any]) -> None:
        if self.channel is None or self.channel.is_closed:
            self.connect()

        self.channel.basic_publish(
            exchange="event_topic_exchange",
            routing_key=routing_key,
            body=json.dumps(message).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def close(self) -> None:
        if self.connection is not None and not self.connection.is_closed:
            self.connection.close()

# Настройки подключения
HOST = os.getenv("RABBITMQ_HOST", "localhost")
PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
USER = os.getenv("RABBITMQ_USER", "guest")
PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

rabbitmq = RabbitMQPublisher(host=HOST, port = PORT, credentials = (USER,PASSWORD))
