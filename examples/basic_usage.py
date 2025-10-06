#!/usr/bin/env python3
"""
Примеры базового использования kv-store CLI утилиты.
"""

import json
import threading
import time
from kv_store.core.store import KVStore


def basic_operations_example():
    """Пример базовых операций с хранилищем."""
    print("=== Пример базовых операций ===")
    
    # Создаем хранилище
    store = KVStore()
    
    # Добавляем данные
    store.put("user:1", "Иван Петров")
    store.put("user:2", "Мария Сидорова")
    store.put("config:theme", "dark")
    store.put("config:language", "ru")
    store.put("settings:timeout", 30)
    
    print(f"Размер хранилища: {store.size()}")
    
    # Получаем данные
    print(f"Пользователь 1: {store.get('user:1')}")
    print(f"Тема: {store.get('config:theme')}")
    
    # Проверяем существование
    print(f"Пользователь 3 существует: {store.exists('user:3')}")
    
    # Показываем все ключи
    print("Все ключи:")
    for key in store.keys():
        print(f"  {key}: {store.get(key)}")
    
    # Удаляем данные
    deleted_user = store.delete("user:2")
    print(f"Удален пользователь: {deleted_user}")
    
    print(f"Размер после удаления: {store.size()}")


def json_data_example():
    """Пример работы с JSON данными."""
    print("\n=== Пример работы с JSON данными ===")
    
    store = KVStore()
    
    # Сложные данные
    user_profile = {
        "name": "Алексей Смирнов",
        "age": 28,
        "email": "alexey@example.com",
        "preferences": {
            "theme": "dark",
            "language": "ru",
            "notifications": True
        },
        "hobbies": ["программирование", "чтение", "путешествия"]
    }
    
    store.put("user:alexey", user_profile)
    
    # Получаем и выводим данные
    profile = store.get("user:alexey")
    print("Профиль пользователя:")
    print(json.dumps(profile, ensure_ascii=False, indent=2))


def concurrent_operations_example():
    """Пример concurrent операций."""
    print("\n=== Пример concurrent операций ===")
    
    store = KVStore()
    
    # Результаты операций
    results = []
    errors = []
    
    def worker(worker_id, num_operations):
        """Рабочая функция."""
        for i in range(num_operations):
            try:
                key = f"worker_{worker_id}_key_{i}"
                value = f"value_{worker_id}_{i}"
                
                # PUT операция
                store.put(key, value)
                
                # GET операция
                retrieved = store.get(key)
                
                # Проверяем корректность
                if retrieved == value:
                    results.append(f"Worker {worker_id}: OK {key}")
                else:
                    errors.append(f"Worker {worker_id}: Mismatch {key}")
                
                # Небольшая задержка для демонстрации concurrent
                time.sleep(0.001)
                
            except Exception as e:
                errors.append(f"Worker {worker_id}: Error {e}")
    
    # Запускаем 5 потоков по 10 операций каждый
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i, 10))
        threads.append(thread)
        thread.start()
    
    # Ждем завершения всех потоков
    for thread in threads:
        thread.join()
    
    print(f"Успешных операций: {len(results)}")
    print(f"Ошибок: {len(errors)}")
    print(f"Финальный размер хранилища: {store.size()}")
    
    if errors:
        print("Ошибки:")
        for error in errors[:5]:  # Показываем первые 5 ошибок
            print(f"  {error}")


def persistence_example():
    """Пример работы с персистентностью."""
    print("\n=== Пример персистентности ===")
    
    # Создаем хранилище с файлом данных
    data_file = "example_data.json"
    log_file = "example_log.json"
    
    store = KVStore(data_file=data_file, log_file=log_file)
    
    # Добавляем данные
    store.put("persistent:key1", "Значение 1")
    store.put("persistent:key2", {"nested": "объект"})
    store.put("persistent:key3", [1, 2, 3, 4, 5])
    
    print(f"Добавлено данных: {store.size()}")
    
    # Создаем новое хранилище с теми же файлами
    store2 = KVStore(data_file=data_file, log_file=log_file)
    
    print(f"Загружено данных: {store2.size()}")
    
    # Проверяем что данные загружены
    print(f"Ключ 1: {store2.get('persistent:key1')}")
    print(f"Ключ 2: {store2.get('persistent:key2')}")
    print(f"Ключ 3: {store2.get('persistent:key3')}")
    
    # Показываем логи транзакций
    transactions = store2._logger.get_transactions()
    print(f"\nКоличество транзакций в логе: {len(transactions)}")
    
    # Очищаем временные файлы
    import os
    if os.path.exists(data_file):
        os.unlink(data_file)
    if os.path.exists(log_file):
        os.unlink(log_file)
    
    print("Временные файлы очищены")


def performance_example():
    """Пример измерения производительности."""
    print("\n=== Пример измерения производительности ===")
    
    store = KVStore()
    
    # Тест PUT операций
    start_time = time.time()
    num_operations = 1000
    
    for i in range(num_operations):
        store.put(f"perf_key_{i}", f"perf_value_{i}")
    
    put_time = time.time() - start_time
    put_ops_per_sec = num_operations / put_time
    
    print(f"PUT операции: {put_ops_per_sec:.2f} операций/сек")
    
    # Тест GET операций
    start_time = time.time()
    
    for i in range(num_operations):
        store.get(f"perf_key_{i}")
    
    get_time = time.time() - start_time
    get_ops_per_sec = num_operations / get_time
    
    print(f"GET операции: {get_ops_per_sec:.2f} операций/сек")
    
    # Тест DELETE операций
    start_time = time.time()
    
    for i in range(num_operations):
        store.delete(f"perf_key_{i}")
    
    delete_time = time.time() - start_time
    delete_ops_per_sec = num_operations / delete_time
    
    print(f"DELETE операции: {delete_ops_per_sec:.2f} операций/сек")
    
    print(f"Финальный размер хранилища: {store.size()}")


def main():
    """Главная функция с примерами."""
    print("KV-Store CLI - Примеры использования")
    print("=" * 50)
    
    try:
        basic_operations_example()
        json_data_example()
        concurrent_operations_example()
        persistence_example()
        performance_example()
        
        print("\n" + "=" * 50)
        print("Все примеры выполнены успешно!")
        
    except Exception as e:
        print(f"Ошибка при выполнении примеров: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
