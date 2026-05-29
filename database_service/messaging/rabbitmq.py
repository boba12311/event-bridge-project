"""
Функциональность для работы с RabbitMQ.
"""

import pika
import json
import logging
import time
from typing import Callable, Optional

from core.config import (
    RABBITMQ_HOST, RABBITMQ_PORT,
    RABBITMQ_USER, RABBITMQ_PASS,
    QUEUE_NAME
)
from models import RegistrationPayload
from db.db_utils import save_registration

logger = logging.getLogger(__name__)


def connect_rabbitmq(max_retries: int = 10) -> Optional[pika.BlockingConnection]:
    """
    Подключение к RabbitMQ с автоповтором.
    
    Args:
        max_retries: Максимальное количество попыток
        
    Returns:
        pika.BlockingConnection или None если не удалось
    """
    for attempt in range(1, max_retries + 1):
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            connection = pika.BlockingConnection(parameters)
            logger.info("Подключено к RabbitMQ")
            return connection
            
        except pika.exceptions.AMQPConnectionError as e:
            logger.warning(f"Попытка {attempt}/{max_retries}: Не удалось подключиться к RabbitMQ")
            if attempt == max_retries:
                logger.error("Превышено количество попыток подключения")
                raise
            time.sleep(5)
    
    return None


def on_message(ch, method, properties, body: bytes):
    """
    Callback-обработчик сообщений из очереди.
    
    Логика:
    1. Парсинг JSON
    2. Валидация через Pydantic
    3. Сохранение в БД
    4. Подтверждение (ack) или возврат (nack)
    """
    try:
        # 1. Парсинг JSON
        raw_data = json.loads(body)
        logger.info(f"Получено: {raw_data.get('registration_id', '<unknown>')}")
        
        # 2. Валидация через Pydantic
        validated = RegistrationPayload(**raw_data)
        data_dict = validated.model_dump(exclude_none=True)
        
        # 3. Сохранение в БД
        success = save_registration(data_dict)
        
        # 4. Подтверждение
        if success:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Сообщение подтверждено (ack)")
        else:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            logger.warning("Сообщение возвращено в очередь")
            
    except json.JSONDecodeError as e:
        logger.error(f"Битый JSON: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def start_consuming(on_message_callback: Callable = None) -> None:
    """
    Запускает прослушивание очереди.
    
    Args:
        on_message_callback: Опциональная функция-обработчик (по умолчанию on_message)
    """
    callback = on_message_callback or on_message
    
    connection = connect_rabbitmq()
    if not connection:
        logger.error("Не удалось подключиться к RabbitMQ")
        return
    
    channel = connection.channel()
    
    # Объявляем очередь (создаст, если нет)
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
        auto_ack=False  # Ручное подтверждение
    )
    
    logger.info(f"Готов принимать сообщения из {QUEUE_NAME}")
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        channel.close()
        connection.close()
        logger.info("Соединение с RabbitMQ закрыто")