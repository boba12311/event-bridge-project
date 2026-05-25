"""Тестовый модуль для проверки Analytics Service"""

import json
import time
import redis
import pika
import requests
from typing import Dict, Any, List
from datetime import datetime
import sys
import os

# Добавляем путь для импорта config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analytics_service.config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB,
    RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASS,
    RABBITMQ_QUEUE
)


class AnalyticsServiceTester:
    """Тестировщик Analytics Service"""
    
    def __init__(self):
        self.redis_client = None
        self.rabbit_connection = None
        self.rabbit_channel = None
        self.test_results = []
        
    def connect_redis(self) -> bool:
        """Подключение к Redis"""
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            print("✅ Подключено к Redis")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к Redis: {e}")
            return False
    
    def connect_rabbitmq(self) -> bool:
        """Подключение к RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
            parameters = pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=30,
                blocked_connection_timeout=30
            )
            self.rabbit_connection = pika.BlockingConnection(parameters)
            self.rabbit_channel = self.rabbit_connection.channel()
            
            # Убеждаемся, что очередь существует
            self.rabbit_channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            
            print("✅ Подключено к RabbitMQ")
            return True
        except Exception as e:
            print(f"❌ Ошибка подключения к RabbitMQ: {e}")
            return False
    
    def clear_redis_stats(self):
        """Очистка статистики в Redis перед тестами"""
        if self.redis_client:
            self.redis_client.delete('total_registrations')
            self.redis_client.delete('vip_registrations')
            self.redis_client.delete('registrations_per_event')
            print("🗑️  Статистика в Redis очищена")
    
    def publish_test_message(self, event_name: str, is_vip: bool, 
                            user_email: str = "test@example.com",
                            user_name: str = "Test User") -> bool:
        """Публикация тестового сообщения в RabbitMQ"""
        try:
            message = {
                "event_name": event_name,
                "user_email": user_email,
                "user_name": user_name,
                "is_vip": is_vip,
                "registration_id": f"test_{datetime.now().timestamp()}",
                "registration_time": datetime.now().isoformat(),
                "body": {"test": True, "timestamp": time.time()}
            }
            
            routing_key = "event.registered.vip" if is_vip else "event.registered.regular"
            
            self.rabbit_channel.basic_publish(
                exchange="event_topic_exchange",
                routing_key=routing_key,
                body=json.dumps(message).encode('utf-8'),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # persistent
                    content_type='application/json'
                )
            )
            
            print(f"   📨 Отправлено сообщение: {routing_key} -> {event_name} (VIP={is_vip})")
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка публикации: {e}")
            return False
    
    def get_redis_stats(self) -> Dict[str, Any]:
        """Получение текущей статистики из Redis"""
        try:
            stats = {
                'total_registrations': int(self.redis_client.get('total_registrations') or 0),
                'vip_registrations': int(self.redis_client.get('vip_registrations') or 0),
                'registrations_per_event': self.redis_client.hgetall('registrations_per_event') or {}
            }
            return stats
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    def wait_for_analytics(self, expected_total: int, timeout: int = 10) -> bool:
        """Ожидание обновления статистики"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            stats = self.get_redis_stats()
            if stats['total_registrations'] >= expected_total:
                return True
            time.sleep(0.5)
        return False
    
    def test_1_single_regular_event(self) -> Dict[str, Any]:
        """Тест 1: Одно обычное событие"""
        print("\n📝 ТЕСТ 1: Обычное событие (1 сообщение)")
        print("-" * 50)
        
        event_name = "Python Conference"
        
        # Отправляем сообщение
        success = self.publish_test_message(event_name, is_vip=False)
        if not success:
            return {"status": "FAIL", "error": "Не удалось отправить сообщение"}
        
        # Ждем обработки
        time.sleep(2)
        
        # Проверяем статистику
        stats = self.get_redis_stats()
        
        result = {
            "status": "PASS" if stats['total_registrations'] >= 1 else "FAIL",
            "expected_total": 1,
            "actual_total": stats['total_registrations'],
            "event_count": stats['registrations_per_event'].get(event_name, 0),
            "vip_count": stats['vip_registrations']
        }
        
        self._print_test_result(result, event_name)
        return result
    
    def test_2_multiple_regular_events(self) -> Dict[str, Any]:
        """Тест 2: Несколько обычных событий"""
        print("\n📝 ТЕСТ 2: Несколько обычных событий (3 сообщения)")
        print("-" * 50)
        
        events = [
            ("Web Dev Workshop", False),
            ("Mobile Dev Conf", False),
            ("Cloud Summit", False)
        ]
        
        initial_stats = self.get_redis_stats()
        initial_total = initial_stats['total_registrations']
        
        # Отправляем сообщения
        for event_name, is_vip in events:
            self.publish_test_message(event_name, is_vip)
            time.sleep(0.5)
        
        # Ждем обработки
        time.sleep(3)
        
        stats = self.get_redis_stats()
        expected_total = initial_total + 3
        
        result = {
            "status": "PASS" if stats['total_registrations'] == expected_total else "FAIL",
            "expected_total": expected_total,
            "actual_total": stats['total_registrations'],
            "events_processed": len(stats['registrations_per_event']),
            "vip_count": stats['vip_registrations']
        }
        
        self._print_test_result(result, f"{len(events)} событий")
        return result
    
    def test_3_vip_events(self) -> Dict[str, Any]:
        """Тест 3: VIP события"""
        print("\n📝 ТЕСТ 3: VIP события (2 VIP сообщения)")
        print("-" * 50)
        
        vip_events = [
            ("VIP Gala Night", True),
            ("CEO Summit", True)
        ]
        
        initial_stats = self.get_redis_stats()
        initial_vip = initial_stats['vip_registrations']
        
        # Отправляем VIP сообщения
        for event_name, is_vip in vip_events:
            self.publish_test_message(event_name, is_vip)
            time.sleep(0.5)
        
        # Ждем обработки
        time.sleep(3)
        
        stats = self.get_redis_stats()
        expected_vip = initial_vip + 2
        
        result = {
            "status": "PASS" if stats['vip_registrations'] == expected_vip else "FAIL",
            "expected_vip": expected_vip,
            "actual_vip": stats['vip_registrations'],
            "total_registrations": stats['total_registrations'],
            "events": stats['registrations_per_event']
        }
        
        self._print_test_result(result, "VIP события")
        return result
    
    def test_4_mixed_events(self) -> Dict[str, Any]:
        """Тест 4: Смешанные события (обычные + VIP)"""
        print("\n📝 ТЕСТ 4: Смешанные события (2 обычных + 2 VIP)")
        print("-" * 50)
        
        mixed_events = [
            ("Tech Talk", False),
            ("VIP Workshop", True),
            ("Community Meetup", False),
            ("Executive Roundtable", True)
        ]
        
        initial_stats = self.get_redis_stats()
        initial_total = initial_stats['total_registrations']
        initial_vip = initial_stats['vip_registrations']
        
        # Отправляем смешанные сообщения
        for event_name, is_vip in mixed_events:
            self.publish_test_message(event_name, is_vip)
            time.sleep(0.3)
        
        # Ждем обработки
        time.sleep(3)
        
        stats = self.get_redis_stats()
        regular_count = sum(1 for _, vip in mixed_events if not vip)
        vip_count = sum(1 for _, vip in mixed_events if vip)
        
        result = {
            "status": "PASS" if (
                stats['total_registrations'] == initial_total + len(mixed_events) and
                stats['vip_registrations'] == initial_vip + vip_count
            ) else "FAIL",
            "expected_total": initial_total + len(mixed_events),
            "actual_total": stats['total_registrations'],
            "expected_vip": initial_vip + vip_count,
            "actual_vip": stats['vip_registrations'],
            "regular_count": regular_count,
            "vip_count": vip_count
        }
        
        self._print_test_result(result, "Смешанные события")
        return result
    
    def test_5_duplicate_events(self) -> Dict[str, Any]:
        """Тест 5: Повторяющиеся события (проверка счетчика)"""
        print("\n📝 ТЕСТ 5: Повторяющиеся события (3x одно событие)")
        print("-" * 50)
        
        event_name = "Popular Workshop"
        
        initial_stats = self.get_redis_stats()
        initial_count = int(initial_stats['registrations_per_event'].get(event_name, 0))
        
        # Отправляем 3 одинаковых события
        for i in range(3):
            self.publish_test_message(event_name, is_vip=False)
            time.sleep(0.3)
        
        # Ждем обработки
        time.sleep(3)
        
        stats = self.get_redis_stats()
        final_count = int(stats['registrations_per_event'].get(event_name, 0))
        expected_count = initial_count + 3
        
        result = {
            "status": "PASS" if final_count == expected_count else "FAIL",
            "event_name": event_name,
            "expected_count": expected_count,
            "actual_count": final_count,
            "total_registrations": stats['total_registrations']
        }
        
        self._print_test_result(result, f"Повторения: {event_name}")
        return result
    
    def _print_test_result(self, result: Dict[str, Any], test_name: str):
        """Вывод результата теста"""
        if result['status'] == 'PASS':
            print(f"   ✅ ТЕСТ ПРОЙДЕН: {test_name}")
            for key, value in result.items():
                if key != 'status':
                    print(f"      {key}: {value}")
        else:
            print(f"   ❌ ТЕСТ НЕ ПРОЙДЕН: {test_name}")
            for key, value in result.items():
                if key != 'status':
                    print(f"      {key}: {value}")
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("\n" + "="*60)
        print("🧪 ЗАПУСК ТЕСТОВ ANALYTICS SERVICE")
        print("="*60)
        print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Подключаемся к сервисам
        print("\n🔌 ПРОВЕРКА ПОДКЛЮЧЕНИЙ:")
        if not self.connect_redis():
            print("❌ Невозможно продолжить - Redis не доступен")
            return False
        
        if not self.connect_rabbitmq():
            print("❌ Невозможно продолжить - RabbitMQ не доступен")
            return False
        
        # Очищаем статистику
        self.clear_redis_stats()
        
        print("\n" + "="*60)
        print("📊 ВЫПОЛНЕНИЕ ТЕСТОВ")
        print("="*60)
        
        # Запускаем тесты
        tests = [
            ("Обычное событие", self.test_1_single_regular_event),
            ("Множественные события", self.test_2_multiple_regular_events),
            ("VIP события", self.test_3_vip_events),
            ("Смешанные события", self.test_4_mixed_events),
            ("Повторяющиеся события", self.test_5_duplicate_events)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                time.sleep(1)  # Пауза между тестами
            except Exception as e:
                print(f"\n❌ ОШИБКА в тесте '{test_name}': {e}")
                results.append((test_name, {"status": "ERROR", "error": str(e)}))
        
        # Выводим итоги
        self.print_summary(results)
        
        # Закрываем соединения
        self.close_connections()
        
        return True
    
    def print_summary(self, results: List[tuple]):
        """Вывод итогов тестирования"""
        print("\n" + "="*60)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ ANALYTICS SERVICE")
        print("="*60)
        
        passed = sum(1 for _, r in results if r.get('status') == 'PASS')
        failed = sum(1 for _, r in results if r.get('status') == 'FAIL')
        errors = sum(1 for _, r in results if r.get('status') == 'ERROR')
        
        print(f"\n📈 СТАТИСТИКА ТЕСТОВ:")
        print(f"   ✅ Пройдено: {passed}")
        print(f"   ❌ Не пройдено: {failed}")
        print(f"   ⚠️  Ошибок: {errors}")
        print(f"   📊 Всего: {len(results)}")
        
        # Финальная статистика из Redis
        print(f"\n📊 ФИНАЛЬНАЯ СТАТИСТИКА REDIS:")
        final_stats = self.get_redis_stats()
        print(f"   📝 Всего регистраций: {final_stats['total_registrations']}")
        print(f"   ⭐ VIP регистраций: {final_stats['vip_registrations']}")
        print(f"   🎯 Обычных регистраций: {final_stats['total_registrations'] - final_stats['vip_registrations']}")
        
        if final_stats['registrations_per_event']:
            print(f"\n📋 РЕГИСТРАЦИИ ПО МЕРОПРИЯТИЯМ:")
            for event, count in sorted(final_stats['registrations_per_event'].items(), 
                                      key=lambda x: x[1], reverse=True):
                print(f"   • {event}: {count}")
        
        print("\n" + "="*60)
        if passed == len(results):
            print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print(f"⚠️  ПРОЙДЕНО {passed}/{len(results)} ТЕСТОВ")
            print("   Проверьте логи analytics_service для диагностики:")
            print("   docker logs eventbridge_analytics --tail=50")
        print("="*60)
    
    def close_connections(self):
        """Закрытие соединений"""
        try:
            if self.rabbit_channel and self.rabbit_channel.is_open:
                self.rabbit_channel.close()
            if self.rabbit_connection and self.rabbit_connection.is_open:
                self.rabbit_connection.close()
            if self.redis_client:
                self.redis_client.close()
            print("\n🔌 Соединения закрыты")
        except:
            pass


def run_analytics_tests():
    """Основная функция для запуска тестов аналитики"""
    tester = AnalyticsServiceTester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(run_analytics_tests())