# 🗄️ Database Service

> Микросервис для сохранения регистраций пользователей в PostgreSQL через RabbitMQ.

---

# 📋 Оглавление

1. [📌 Описание](#-описание)
2. [🛠 Используемые технологии](#-используемые-технологии)
3. [📁 Структура проекта](#-структура-проекта)
4. [⚙️ Переменные окружения](#️-переменные-окружения)
5. [🐳 Запуск PostgreSQL и RabbitMQ через Docker](#-запуск-postgresql-и-rabbitmq-через-docker)
6. [🚀 Запуск сервиса](#-запуск-сервиса)
7. [📨 Формат входящего сообщения](#-формат-входящего-сообщения)
8. [🧪 Тестирование](#-тестирование)
9. [🗃 Структура таблицы](#-структура-таблицы)
10. [🛡 Обработка ошибок](#-обработка-ошибок)

---

# 📌 Описание

`database-service` — это микросервис, который:

- подключается к RabbitMQ;
- слушает очередь регистраций;
- валидирует входящие JSON-сообщения;
- сохраняет данные в PostgreSQL;
- предотвращает дублирование регистраций;
- подтверждает сообщения через `basic_ack`.

---

# 🛠 Используемые технологии

| Технология | Назначение |
|---|---|
| Python 3.12+ | Основной язык |
| PostgreSQL | Хранение данных |
| RabbitMQ | Брокер сообщений |
| SQLModel | ORM |
| SQLAlchemy | Работа с БД |
| Pydantic v2 | Валидация данных |
| Pika | Работа с RabbitMQ |
| Docker | Контейнеризация |

---

# 📁 Структура проекта

```text
database-service/
├── main.py
├── config.py
├── requirements.txt
├── .env
└── README.md
```

---

# ⚙️ Переменные окружения

Создайте файл `.env`:

```env
# PostgreSQL
DB_USER=event_user
DB_PASSWORD=1234
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=event_bridge

# RabbitMQ
RABBITMQ_HOST=127.0.0.1
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

# Queue
QUEUE_NAME=registrations
```

---

# 🐳 Запуск PostgreSQL и RabbitMQ через Docker

## PostgreSQL

```bash
docker run --name event-postgres ^
-e POSTGRES_USER=event_user ^
-e POSTGRES_PASSWORD=1234 ^
-e POSTGRES_DB=event_bridge ^
-p 5432:5432 ^
-d postgres:16
```

---

## RabbitMQ

```bash
docker run --name event-rabbitmq ^
-p 5672:5672 ^
-p 15672:15672 ^
-d rabbitmq:3-management
```

---

## RabbitMQ Web UI

После запуска панель RabbitMQ доступна по адресу:

```text
http://localhost:15672
```

### Данные для входа

```text
login: guest
password: guest
```

---

# 🚀 Запуск сервиса

## 1. Создание виртуального окружения

### Windows PowerShell

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

---

## 3. Запуск сервиса

```bash
python main.py
```

---

## ✅ Успешный запуск

```text
INFO - Таблица 'registrations' готова
INFO - Database Service запущен
INFO - Подключено к RabbitMQ
INFO - Готов принимать сообщения из registrations
```

---

# 📨 Формат входящего сообщения

Сервис принимает JSON-сообщения из RabbitMQ.

## Пример сообщения

```json
{
  "registration_id": "90b54255-2e8f-4d0d-bab0-c8810b7f7d6c",
  "event_name": "Python Conference 2026",
  "user_email": "student@example.com",
  "user_name": "Matvey",
  "is_vip": true
}
```

---

# 🧪 Тестирование

## Тестовый publisher

Создайте файл `test_publisher.py`:

```python
import pika
import json
import uuid

message = {
    "registration_id": str(uuid.uuid4()),
    "event_name": "Python Conference 2026",
    "user_email": "test@example.com",
    "user_name": "Matvey",
    "is_vip": True
}

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="127.0.0.1")
)

channel = connection.channel()

channel.queue_declare(queue="registrations", durable=True)

channel.basic_publish(
    exchange="",
    routing_key="registrations",
    body=json.dumps(message),
    properties=pika.BasicProperties(
        delivery_mode=2
    )
)

print("Сообщение отправлено:")
print(json.dumps(message, indent=2))

connection.close()
```

---

## Запуск теста

```bash
python test_publisher.py
```

---

# 🗃 Структура таблицы

Таблица `registrations` создаётся автоматически.

| Поле | Тип |
|---|---|
| id | INTEGER |
| registration_id | VARCHAR |
| event_name | VARCHAR |
| user_email | VARCHAR |
| user_name | VARCHAR |
| is_vip | BOOLEAN |
| timestamp | TIMESTAMP |

---

# 🛡 Обработка ошибок

Сервис поддерживает:

- повторное подключение к RabbitMQ;
- обработку битого JSON;
- валидацию входящих данных;
- защиту от дубликатов;
- ручное подтверждение сообщений (`basic_ack`);
- возврат сообщений в очередь (`basic_nack`).

---

# ✅ Пример успешной обработки

```text
INFO - Получено сообщение: 90b54255-2e8f-4d0d-bab0-c8810b7f7d6c
INFO - Сохранено: 90b54255-2e8f-4d0d-bab0-c8810b7f7d6c (test@example.com)
INFO - Сообщение подтверждено (ack)
```

---

# 📦 requirements.txt

```txt
fastapi>=0.115.0
sqlmodel>=0.0.22
sqlalchemy>=2.0.36
psycopg[binary]>=3.2.0
pika>=1.3.2
pydantic>=2.9.0
python-dotenv>=1.0.1
```

---

# 🎯 Особенности сервиса

✅ PostgreSQL + RabbitMQ  
✅ Docker-ready  
✅ SQLModel ORM  
✅ Pydantic validation  
✅ Retry connection logic  
✅ Duplicate protection  
✅ Graceful shutdown  
✅ Logging system  
✅ Manual ACK/NACK handling