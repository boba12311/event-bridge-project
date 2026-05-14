import pika
import sys
import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Настройки подключения
HOST = os.getenv("RABBITMQ_HOST", "localhost")
PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
USER = os.getenv("RABBITMQ_USER", "guest")
PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")

# Настройки RabbitMQ
EXCHANGE_NAME = 'event_topic_exchange'
EXCHANGE_TYPE = 'topic' 

# Список очередей
QUEUES = [
    'email_queue',
    'db_log_queue',
    'excel_report_queue',
    'console_monitor_queue',
    'critical_alert_queue',
    'analytics_queue',
    'pdf_ticket_queue',
    'slack_notify_queue',
]

# Правила маршрутизации: { 'routing_key': [список_очередей] }
BINDINGS = {
    'event.registered.#': [
        'email_queue',
        'db_log_queue',
        'excel_report_queue',
        'pdf_ticket_queue',
    ],
    'event.#': [
        'console_monitor_queue',
        'analytics_queue',
    ],
    'event.registered.vip': [
        'critical_alert_queue',
        'slack_notify_queue',
    ],
}


def setup_infrastructure():
    """Подключается к RabbitMQ и создаёт всю инфраструктуру."""
    
    # 1. Подключение
    credentials = pika.PlainCredentials(USER, PASSWORD)
    parameters = pika.ConnectionParameters(
        host=HOST,
        port=PORT,
        credentials=credentials,
    )
    
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        print("Подключено к RabbitMQ")
        
        # 2. Создаём Exchange (обменник)
        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type=EXCHANGE_TYPE,
            durable=True
        )
        print(f"Exchange '{EXCHANGE_NAME}' создан")
        
        # 3. Создаём очереди
        for queue_name in QUEUES:
            channel.queue_declare(
                queue=queue_name,
                durable=True,
                auto_delete=False
            )
            print(f"Очередь '{queue_name}' создана")
        
        # 4. Создаём связки (bindings)
        for routing_key, queue_list in BINDINGS.items():
            for queue_name in queue_list:
                channel.queue_bind(
                    exchange=EXCHANGE_NAME,
                    queue=queue_name,
                    routing_key=routing_key
                )
                print(f" Binding: '{routing_key}' → '{queue_name}'")
        
        print("\n Инфраструктура готова! Можно запускать сервисы.")
        
        connection.close()
        
    except pika.exceptions.AMQPConnectionError:
        print("Ошибка: Не удалось подключиться к RabbitMQ", file=sys.stderr)
        print("Убедитесь, что RabbitMQ запущен (docker-compose up -d)", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при настройке: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    setup_infrastructure()
