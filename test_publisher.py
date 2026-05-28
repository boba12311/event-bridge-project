# test_publisher.py
import pika, json, time
from message_contract import TEST_VIP_EVENT, RegistrationEvent

def send_test_event(event: dict, routing_key: str):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    # Exchange можно объявить здесь. Pika пропустит, если он уже есть.
    channel.exchange_declare(exchange='event_topic_exchange', exchange_type='topic', durable=True)
    
    channel.basic_publish(
        exchange='event_topic_exchange',
        routing_key=routing_key,
        body=json.dumps(event),
        properties=pika.BasicProperties(delivery_mode=2) # persistent
    )
    print(f" [x] Отправлено событие с routing_key='{routing_key}'")
    connection.close()

if __name__ == '__main__':
    # Тест VIP
    send_test_event(TEST_VIP_EVENT, 'event.registered.vip')
    time.sleep(1)
    # Тест Regular
    reg = RegistrationEvent(is_vip=False, user_email="test@local.ru", user_name="Андрей", event_name="Meetup")
    send_test_event(reg.model_dump(), 'event.registered.regular')