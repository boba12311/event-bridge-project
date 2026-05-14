## 🧪 Как запустить
1. Запустить RabbitMQ: `docker-compose up -d`
2. Установить зависимости: `pip install -r requirements.txt`
3. Настроить `.env` (ниже приведён пример)
4. Запустить оркестратор: `python orchestrator.py`
5. Открыть RabbitMQ UI: `http://localhost:15672` (guest/guest)
6. Убедиться, что:
   - Вкладка **Exchanges** → есть `event_topic_exchange` (type: topic, durable: ✓)
   - Вкладка **Queues** → все 8 очередей созданы (durable: ✓)
   - В bindings exchange → 3 правила маршрутизации

## Пример .env
```
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
```
