#!/usr/bin/env python3
"""
Демонстрационный скрипт для kv-store CLI утилиты.
Показывает основные возможности и производительность.
"""

import time
import threading
import json
from kv_store.core.store import KVStore


def demo_basic_operations():
    """Демонстрация базовых операций."""
    print("🔧 Демонстрация базовых операций")
    print("-" * 40)
    
    store = KVStore()
    
    # PUT операции
    print("📝 Сохранение данных...")
    store.put("user:1", "Иван Петров")
    store.put("user:2", "Мария Сидорова")
    store.put("config:theme", "dark")
    store.put("settings:timeout", 30)
    store.put("data:complex", {"nested": {"array": [1, 2, 3]}})
    
    print(f"✅ Сохранено {store.size()} элементов")
    
    # GET операции
    print("\n📖 Получение данных...")
    print(f"Пользователь 1: {store.get('user:1')}")
    print(f"Тема: {store.get('config:theme')}")
    print(f"Сложные данные: {json.dumps(store.get('data:complex'), ensure_ascii=False)}")
    
    # EXISTS проверки
    print(f"\n🔍 Проверка существования:")
    print(f"user:1 существует: {store.exists('user:1')}")
    print(f"user:999 существует: {store.exists('user:999')}")
    
    # LIST операции
    print(f"\n📋 Все ключи:")
    for key in store.keys():
        print(f"  {key}")
    
    # DELETE операции
    print(f"\n🗑️ Удаление данных...")
    deleted = store.delete("user:2")
    print(f"Удален: {deleted}")
    print(f"Размер после удаления: {store.size()}")


def demo_concurrent_operations():
    """Демонстрация concurrent операций."""
    print("\n🚀 Демонстрация concurrent операций")
    print("-" * 40)
    
    store = KVStore()
    
    results = {"success": 0, "errors": 0}
    
    def worker(worker_id, num_ops):
        """Рабочая функция."""
        for i in range(num_ops):
            try:
                key = f"worker_{worker_id}_key_{i}"
                value = f"value_{worker_id}_{i}"
                
                # PUT
                store.put(key, value)
                
                # GET
                retrieved = store.get(key)
                
                # DELETE (каждый 5-й)
                if i % 5 == 0:
                    store.delete(key)
                
                results["success"] += 1
                
            except Exception as e:
                results["errors"] += 1
    
    # Запуск 5 потоков по 20 операций
    print("🔄 Запуск 5 потоков по 20 операций...")
    start_time = time.time()
    
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker, args=(i, 20))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ Успешных операций: {results['success']}")
    print(f"❌ Ошибок: {results['errors']}")
    print(f"⏱️ Время выполнения: {duration:.3f} сек")
    print(f"📊 Производительность: {results['success']/duration:.0f} операций/сек")
    print(f"📦 Финальный размер хранилища: {store.size()}")


def demo_transaction_logging():
    """Демонстрация логирования транзакций."""
    print("\n📝 Демонстрация логирования транзакций")
    print("-" * 40)
    
    # Создаем хранилище с логом
    store = KVStore(log_file="demo_log.json")
    
    print("📝 Выполняем операции...")
    store.put("demo:key1", "значение 1")
    store.get("demo:key1")
    store.put("demo:key1", "обновленное значение")
    store.put("demo:key2", "значение 2")
    store.delete("demo:key1")
    
    # Получаем логи
    transactions = store._logger.get_transactions()
    print(f"📊 Записано {len(transactions)} транзакций")
    
    print("\n📋 Последние 3 транзакции:")
    for tx in transactions[-3:]:
        print(f"  {tx['operation']} {tx.get('key', 'N/A')} - {tx['timestamp']}")
    
    # Показываем статистику
    stats = {"PUT": 0, "GET": 0, "DELETE": 0}
    for tx in transactions:
        op = tx.get("operation", "UNKNOWN")
        stats[op] = stats.get(op, 0) + 1
    
    print(f"\n📈 Статистика операций:")
    for op, count in stats.items():
        print(f"  {op}: {count}")


def demo_performance():
    """Демонстрация производительности."""
    print("\n⚡ Демонстрация производительности")
    print("-" * 40)
    
    store = KVStore()
    
    # Тест PUT операций
    print("📝 Тест PUT операций...")
    start_time = time.time()
    num_ops = 1000
    
    for i in range(num_ops):
        store.put(f"perf_key_{i}", f"perf_value_{i}")
    
    put_time = time.time() - start_time
    put_ops_per_sec = num_ops / put_time
    print(f"✅ PUT: {put_ops_per_sec:.0f} операций/сек")
    
    # Тест GET операций
    print("📖 Тест GET операций...")
    start_time = time.time()
    
    for i in range(num_ops):
        store.get(f"perf_key_{i}")
    
    get_time = time.time() - start_time
    get_ops_per_sec = num_ops / get_time
    print(f"✅ GET: {get_ops_per_sec:.0f} операций/сек")
    
    # Тест DELETE операций
    print("🗑️ Тест DELETE операций...")
    start_time = time.time()
    
    for i in range(num_ops):
        store.delete(f"perf_key_{i}")
    
    delete_time = time.time() - start_time
    delete_ops_per_sec = num_ops / delete_time
    print(f"✅ DELETE: {delete_ops_per_sec:.0f} операций/сек")
    
    print(f"📦 Финальный размер: {store.size()}")


def demo_error_handling():
    """Демонстрация обработки ошибок."""
    print("\n🛡️ Демонстрация обработки ошибок")
    print("-" * 40)
    
    store = KVStore()
    
    # Валидные операции
    store.put("valid_key", "valid_value")
    print("✅ Валидная операция выполнена")
    
    # Недопустимый ключ
    try:
        store.put("", "empty_key_value")
    except Exception as e:
        print(f"❌ Ошибка пустого ключа: {type(e).__name__}")
    
    # Недопустимое значение
    try:
        store.put("valid_key", None)
    except Exception as e:
        print(f"❌ Ошибка None значения: {type(e).__name__}")
    
    # Получение несуществующего ключа
    try:
        store.get("nonexistent_key")
    except Exception as e:
        print(f"❌ Ошибка несуществующего ключа: {type(e).__name__}")
    
    # Удаление несуществующего ключа
    try:
        store.delete("nonexistent_key")
    except Exception as e:
        print(f"❌ Ошибка удаления несуществующего ключа: {type(e).__name__}")
    
    print("✅ Все ошибки обработаны корректно")


def main():
    """Главная функция демонстрации."""
    print("🎯 KV-Store CLI - Демонстрация возможностей")
    print("=" * 50)
    
    try:
        demo_basic_operations()
        demo_concurrent_operations()
        demo_transaction_logging()
        demo_performance()
        demo_error_handling()
        
        print("\n" + "=" * 50)
        print("🎉 Демонстрация завершена успешно!")
        print("\n📚 Для запуска CLI используйте:")
        print("   python kv_store_cli.py")
        print("\n🧪 Для запуска тестов используйте:")
        print("   pytest tests/ -v")
        
    except Exception as e:
        print(f"\n❌ Ошибка при демонстрации: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
