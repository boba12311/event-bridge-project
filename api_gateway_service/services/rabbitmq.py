"""Публикует сообщение в очередь"""

from typing import Any
import pika
import json


class RabbitMQPublisher:
    def __init__(self, host: str = "localhost"):
        self.host: str = host
        self.connection: Any = None
        self.channel: Any = None

    def connect(self) -> None:
        if self.connection is not None and not self.connection.is_closed:
            return

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.host))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(
            exchange="event_topic_exchange", exchange_type="topic", durable=True
        )

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


rabbitmq = RabbitMQPublisher()
