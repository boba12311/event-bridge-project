"""
monitor_all_queues.py
Задача: Слушать ВСЕ очереди проекта и выводить сообщения в консоль в реальном времени.
Использование: python monitor_all_queues.py
"""

import pika
import json
import sys
import os
import time
from dotenv import load_dotenv


# Загружаем .env
load_dotenv()

# Конфиг из окружения
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

# Список очередей для мониторинга
QUEUES_TO_MONITOR = [
    'email_queue',
    'db_log_queue',
    'excel_report_queue',
    'console_monitor_queue',
    'critical_alert_queue',
    'analytics_queue',
    'pdf_ticket_queue',
    'slack_notify_queue',
]


def on_message_callback(ch, method, properties, body, queue_name):
    """
    Callback: вызывается при получении сообщения из ЛЮБОЙ очереди.
    """
    
    print(f"\n[{time.strftime('%H:%M:%S')}] 📨 {queue_name}")
    print(f"{'─'*60}")

    
    raw = body.decode('utf-8', errors='replace')
    print(raw)
    
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_monitor(queues: list):
    """Подписывается на все указанные очереди и запускает мониторинг."""
    
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=600
    )
    
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        # 2. Подписываемся на КАЖДУЮ очередь отдельно
        for queue_name in queues:
            channel.basic_consume(
                queue=queue_name,
                on_message_callback=lambda ch, method, props, body, qn=queue_name: 
                    on_message_callback(ch, method, props, body, qn),
                auto_ack=False
            )

        
        # 3. Настраиваем QoS: по 1 сообщению за раз на консьюмер
        channel.basic_qos(prefetch_count=1)
        
        print(f"\nМониторинг запущен! Ожидание сообщений...")
        print(f"Нажми Ctrl+C для остановки\n")
        
        # 4. Запускаем ЕДИНЫЙ цикл потребления — он будет мультиплексировать все очереди
        channel.start_consuming()
        
    except KeyboardInterrupt:
        print(f"\nОстановка по запросу пользователя")
    except pika.exceptions.AMQPConnectionError:
        print(f"Не удалось подключиться к RabbitMQ", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'connection' in locals() and not connection.is_closed:
            connection.close()
            print(f"Соединение закрыто")


if __name__ == '__main__':

    print(f"RabbitMQ Multi-Queue Monitor")
    print(f"Очереди: {', '.join(QUEUES_TO_MONITOR)}\n")
    
    start_monitor(QUEUES_TO_MONITOR)