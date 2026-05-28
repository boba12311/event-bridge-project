# email-service/main.py
import pika
import json
import smtplib
import logging
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', SMTP_USER)

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'guest')

EXCHANGE_NAME = 'event_topic_exchange'
QUEUE_NAME = 'email_queue'
ROUTING_KEYS = ['event.registered.vip', 'event.registered.regular']


def send_email(user_email: str, user_name: str, event_name: str) -> bool:
    subject = f"Подтверждение регистрации на {event_name}"
    body = f"Здравствуйте, {user_name}! Вы успешно зарегистрированы."

    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = user_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, user_email, msg.as_string())
        logger.info(f"Email успешно отправлен на {user_email}")
        return True
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Невалидный email {user_email}: {e}")
        return False
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Ошибка аутентификации SMTP: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP ошибка при отправке на {user_email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отправке email на {user_email}: {e}")
        return False


def process_message(ch, method, properties, body):
    logger.info(f"Получено сообщение: {body.decode('utf-8')}")

    try:
        event = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    user_email = event.get('user_email')
    user_name = event.get('user_name')
    event_name = event.get('event_name')

    if not all([user_email, user_name, event_name]):
        logger.error("Некорректное сообщение: отсутствуют обязательные поля")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    success = send_email(user_email, user_name, event_name)

    if success:
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("Сообщение подтверждено (ack)")
    else:
        # Постоянные ошибки (например, неверные SMTP-данные или невалидный email)
        # не исправятся при повторной попытке, поэтому не возвращаем в очередь
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        logger.warning("Сообщение отклонено (nack без requeue) из-за ошибки отправки")


MAX_RETRIES = 15
RETRY_DELAY = 3


def start_consumer():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )

    connection = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            connection = pika.BlockingConnection(parameters)
            break
        except pika.exceptions.AMQPConnectionError:
            logger.warning(f"⏳ RabbitMQ недоступен (попытка {attempt}/{MAX_RETRIES}). Ждём {RETRY_DELAY} сек...")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logger.error("❌ Не удалось подключиться к RabbitMQ после всех попыток")
                return

    try:
        channel = connection.channel()

        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='topic', durable=True)

        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        for routing_key in ROUTING_KEYS:
            channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=routing_key)
            logger.info(f"Очередь '{QUEUE_NAME}' привязана к '{EXCHANGE_NAME}' с routing_key='{routing_key}'")

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_message)

        logger.info(f"Сервис запущен. Ожидание сообщений из очереди '{QUEUE_NAME}'...")
        channel.start_consuming()

    except KeyboardInterrupt:
        logger.info("Сервис остановлен пользователем")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
    finally:
        if connection and connection.is_open:
            connection.close()
            logger.info("Соединение с RabbitMQ закрыто")


if __name__ == '__main__':
    start_consumer()
