import config
import pika
import json
import logging
import time
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, create_engine, Session, select
from pydantic import BaseModel, ValidationError, ConfigDict, Field as PydanticField

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# Модель данных для SQLModel (таблица в БД)
class Registration(SQLModel, table=True):
    __tablename__ = "registrations"

    id: Optional[int] = Field(default=None, primary_key=True)
    registration_id: str = Field(unique=True, index=True, min_length=1, max_length=100)
    event_name: str = Field(min_length=1, max_length=255)
    user_email: str = Field(min_length=5, max_length=255, index=True)
    user_name: Optional[str] = Field(default=None, max_length=255)  # Может быть пустым
    is_vip: bool = Field(default=False)
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    def __repr__(self): 
        return f"<Registration(id='{self.registration_id}', email='{self.user_email}')>"

# Pydantic модель для валидации входящих данных из RabbitMQ
class RegistrationPayload(BaseModel):
    registration_id: str = PydanticField(..., min_length=1, max_length=100)
    event_name: str = PydanticField(..., min_length=1, max_length=200)
    user_email: str = PydanticField(..., min_length=5, max_length=100)
    user_name: Optional[str] = PydanticField(default=None, max_length=100)
    is_vip: bool = PydanticField(default=False)
    timestamp: Optional[datetime] = PydanticField(default=None)
    
    # Игнорируем лишние поля
    model_config = ConfigDict(extra='ignore')

# Подключение к БД и создание таблицы, если её нет
# Создание engine
engine = create_engine(
    config.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={
        'client_encoding': 'UTF8',
        'sslmode': 'disable'
    }
)

# Создание таблицы, если её ещё нет
SQLModel.metadata.create_all(engine)
logger.info("Таблица '%s' готова", Registration.__tablename__)

# Функция сохранения данных в БД
def save_registration(data: dict) -> bool:
    try:
        with Session(engine) as session:
            statement = select(Registration).where(
                Registration.registration_id == data["registration_id"]
            )
            existing = session.exec(statement).first()

            if existing:
                logger.warning(
                    f"Дубликат: {data['registration_id']} — пропускаем"
                )
                return True

            registration = Registration(**data)
            session.add(registration)
            session.commit()
            session.refresh(registration)

            logger.info(
                f"Сохранено: {registration.registration_id} ({registration.user_email})"
            )
            return True

    except Exception as e:
        logger.error(f"Ошибка БД: {e}")
        return False

# Обработчик сообщений из RabbitMQ
def on_message(ch, method, properties, body):
    try:
        raw_data = json.loads(body)
        logger.info(f"Получено сообщение: {raw_data.get('registration_id', '<unknown>')}")

        validated = RegistrationPayload(**raw_data)
        data_dict = validated.model_dump(exclude_none=True)

        success = save_registration(data_dict)
        
        if success:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info("Сообщение подтверждено (ack)")
        else:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            logger.warning("Сообщение возвращено в очередь")
            
    except json.JSONDecodeError as e:
        logger.error(f"Битый JSON: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except ValidationError as e:
        logger.error(f"Ошибка валидации полей: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

# Подключение к RabbitMQ 
def connect_rabbitmq():
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            credentials = pika.PlainCredentials(
                config.RABBITMQ_USER,
                config.RABBITMQ_PASS
            )
            parameters = pika.ConnectionParameters(
                host=config.RABBITMQ_HOST,
                port=config.RABBITMQ_PORT,
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


def main():
    logger.info("Database Service запущен")
    logger.info(f"Очередь: {config.QUEUE_NAME}")
    logger.info(f"БД: {config.DATABASE_URL.split('@')[1] if '@' in config.DATABASE_URL else config.DATABASE_URL}")
    
    # Подключение к RabbitMQ
    try:
        connection = connect_rabbitmq()
    except Exception as e:
        logger.error(f"Не удалось подключиться к RabbitMQ: {e}")
        return
    
    channel = connection.channel()
    channel.queue_declare(queue=config.QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=config.QUEUE_NAME, on_message_callback=on_message,auto_ack=False)

    logger.info(f"Готов принимать сообщения из {config.QUEUE_NAME}")
    logger.info("Нажмите Ctrl+C для остановки")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    finally:
        channel.close()
        connection.close()
        logger.info("Сервис остановлен")

if __name__ == "__main__":
    main()