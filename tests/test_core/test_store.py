"""
Тесты для основного хранилища kv-store.
"""

import pytest
import threading
import time
import json
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from kv_store.core.store import KVStore
from kv_store.core.exceptions import KeyNotFoundError, InvalidKeyError, InvalidValueError


class TestKVStore:
    """Тесты для KVStore."""
    
    def test_basic_operations(self):
        """Тест базовых операций."""
        store = KVStore()
        
        # Тест put и get
        store.put("key1", "value1")
        assert store.get("key1") == "value1"
        
        # Тест перезаписи
        store.put("key1", "value2")
        assert store.get("key1") == "value2"
        
        # Тест delete
        old_value = store.delete("key1")
        assert old_value == "value2"
        
        # Тест исключения при отсутствии ключа
        with pytest.raises(KeyNotFoundError):
            store.get("key1")
    
    def test_invalid_operations(self):
        """Тест недопустимых операций."""
        store = KVStore()
        
        # Пустой ключ
        with pytest.raises(InvalidKeyError):
            store.put("", "value")
        
        # None ключ
        with pytest.raises(InvalidKeyError):
            store.put(None, "value")
        
        # None значение
        with pytest.raises(InvalidValueError):
            store.put("key", None)
    
    def test_multiple_keys(self):
        """Тест работы с несколькими ключами."""
        store = KVStore()
        
        # Добавляем несколько ключей
        test_data = {
            "user:1": "Иван",
            "user:2": "Мария",
            "config:theme": "dark",
            "config:lang": "ru"
        }
        
        for key, value in test_data.items():
            store.put(key, value)
        
        # Проверяем все ключи
        assert store.size() == len(test_data)
        
        for key, expected_value in test_data.items():
            assert store.get(key) == expected_value
        
        # Проверяем итераторы
        keys = list(store.keys())
        assert len(keys) == len(test_data)
        assert all(key in keys for key in test_data.keys())
    
    def test_clear(self):
        """Тест очистки хранилища."""
        store = KVStore()
        
        # Добавляем данные
        store.put("key1", "value1")
        store.put("key2", "value2")
        assert store.size() == 2
        
        # Очищаем
        store.clear()
        assert store.size() == 0
        
        # Проверяем что ключи действительно удалены
        with pytest.raises(KeyNotFoundError):
            store.get("key1")
    
    def test_exists(self):
        """Тест проверки существования ключа."""
        store = KVStore()
        
        assert not store.exists("nonexistent")
        
        store.put("existing", "value")
        assert store.exists("existing")
        
        store.delete("existing")
        assert not store.exists("existing")


class TestRaceConditions:
    """Тесты на race conditions с многопоточностью."""
    
    def test_concurrent_puts(self):
        """Тест одновременных операций put."""
        store = KVStore()
        num_threads = 10
        num_operations = 100
        
        def put_worker(thread_id):
            """Рабочая функция для put операций."""
            for i in range(num_operations):
                key = f"thread_{thread_id}_key_{i}"
                value = f"value_{thread_id}_{i}"
                store.put(key, value)
        
        # Запускаем потоки
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=put_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем что все данные сохранены
        assert store.size() == num_threads * num_operations
        
        # Проверяем что нет дубликатов
        keys = list(store.keys())
        assert len(keys) == len(set(keys))
    
    def test_concurrent_gets_and_puts(self):
        """Тест одновременных операций get и put."""
        store = KVStore()
        
        # Инициализируем некоторые данные
        initial_data = {f"key_{i}": f"value_{i}" for i in range(10)}
        for key, value in initial_data.items():
            store.put(key, value)
        
        def get_worker():
            """Рабочая функция для get операций."""
            for _ in range(50):
                for key in initial_data.keys():
                    try:
                        value = store.get(key)
                        assert value is not None
                    except KeyNotFoundError:
                        # Может возникнуть если ключ удален во время чтения
                        pass
        
        def put_worker():
            """Рабочая функция для put операций."""
            for i in range(50):
                key = f"new_key_{i}"
                value = f"new_value_{i}"
                store.put(key, value)
        
        # Запускаем потоки
        threads = []
        
        # Потоки для чтения
        for _ in range(3):
            thread = threading.Thread(target=get_worker)
            threads.append(thread)
        
        # Потоки для записи
        for _ in range(2):
            thread = threading.Thread(target=put_worker)
            threads.append(thread)
        
        # Запускаем все потоки
        for thread in threads:
            thread.start()
        
        # Ждем завершения
        for thread in threads:
            thread.join()
        
        # Проверяем что данные не повреждены
        assert store.size() >= 10  # Как минимум начальные данные
    
    def test_concurrent_deletes(self):
        """Тест одновременных операций delete."""
        store = KVStore()
        
        # Инициализируем данные
        test_data = {f"key_{i}": f"value_{i}" for i in range(20)}
        for key, value in test_data.items():
            store.put(key, value)
        
        def delete_worker(keys_to_delete):
            """Рабочая функция для delete операций."""
            for key in keys_to_delete:
                try:
                    store.delete(key)
                except KeyNotFoundError:
                    # Ключ уже удален другим потоком
                    pass
        
        # Разделяем ключи между потоками
        keys = list(test_data.keys())
        chunk_size = len(keys) // 4
        key_chunks = [keys[i:i + chunk_size] for i in range(0, len(keys), chunk_size)]
        
        # Запускаем потоки
        threads = []
        for chunk in key_chunks:
            thread = threading.Thread(target=delete_worker, args=(chunk,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения
        for thread in threads:
            thread.join()
        
        # Проверяем что все ключи удалены
        assert store.size() == 0
    
    def test_read_write_lock_behavior(self):
        """Тест поведения read-write блокировок."""
        store = KVStore()
        
        # Инициализируем данные
        store.put("test_key", "initial_value")
        
        read_results = []
        write_completed = False
        
        def reader():
            """Функция читателя."""
            nonlocal read_results
            for _ in range(10):
                try:
                    value = store.get("test_key")
                    read_results.append(value)
                except KeyNotFoundError:
                    read_results.append("NOT_FOUND")
                time.sleep(0.01)
        
        def writer():
            """Функция писателя."""
            nonlocal write_completed
            for i in range(5):
                store.put("test_key", f"updated_value_{i}")
                time.sleep(0.02)
            write_completed = True
        
        # Запускаем потоки
        reader_thread = threading.Thread(target=reader)
        writer_thread = threading.Thread(target=writer)
        
        reader_thread.start()
        writer_thread.start()
        
        # Ждем завершения
        reader_thread.join()
        writer_thread.join()
        
        # Проверяем что нет повреждений данных
        assert len(read_results) == 10
        assert write_completed
        
        # Финальное значение должно быть корректным
        final_value = store.get("test_key")
        assert final_value.startswith("updated_value_")
    
    def test_thread_pool_executor(self):
        """Тест с использованием ThreadPoolExecutor."""
        store = KVStore()
        
        def operation(operation_type, key, value=None):
            """Выполняет операцию."""
            if operation_type == "put":
                store.put(key, value)
                return f"PUT {key}={value}"
            elif operation_type == "get":
                try:
                    result = store.get(key)
                    return f"GET {key}={result}"
                except KeyNotFoundError:
                    return f"GET {key}=NOT_FOUND"
            elif operation_type == "delete":
                try:
                    result = store.delete(key)
                    return f"DELETE {key}={result}"
                except KeyNotFoundError:
                    return f"DELETE {key}=NOT_FOUND"
        
        # Создаем задачи
        tasks = []
        
        # Задачи записи
        for i in range(10):
            tasks.append(("put", f"key_{i}", f"value_{i}"))
        
        # Задачи чтения
        for i in range(5):
            tasks.append(("get", f"key_{i}"))
        
        # Задачи удаления
        for i in range(3):
            tasks.append(("delete", f"key_{i}"))
        
        # Выполняем задачи в пуле потоков
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for task in tasks:
                future = executor.submit(operation, *task)
                futures.append(future)
            
            # Собираем результаты
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(f"ERROR: {e}")
        
        # Проверяем что операции выполнены
        assert len(results) == len(tasks)
        
        # Проверяем что хранилище в консистентном состоянии
        assert store.size() >= 7  # 10 - 3 удаленных


class TestPersistence:
    """Тесты персистентности данных."""
    
    def test_file_persistence(self):
        """Тест сохранения в файл."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            # Создаем хранилище с файлом
            store1 = KVStore(data_file=temp_file)
            
            # Добавляем данные
            test_data = {"key1": "value1", "key2": "value2", "key3": 123}
            for key, value in test_data.items():
                store1.put(key, value)
            
            # Создаем новое хранилище с тем же файлом
            store2 = KVStore(data_file=temp_file)
            
            # Проверяем что данные загружены
            assert store2.size() == len(test_data)
            for key, expected_value in test_data.items():
                assert store2.get(key) == expected_value
                
        finally:
            # Очищаем временный файл
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_log_persistence(self):
        """Тест сохранения логов в файл."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_log_file = f.name
        
        try:
            # Создаем хранилище с логом
            store = KVStore(log_file=temp_log_file)
            
            # Выполняем операции
            store.put("key1", "value1")
            store.get("key1")
            store.put("key1", "value2")
            store.delete("key1")
            
            # Проверяем что лог создан и содержит данные
            assert os.path.exists(temp_log_file)
            
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            assert len(logs) >= 4  # Как минимум 4 операции
            assert all("operation" in log for log in logs)
            assert any(log["operation"] == "PUT" for log in logs)
            assert any(log["operation"] == "GET" for log in logs)
            assert any(log["operation"] == "DELETE" for log in logs)
                
        finally:
            # Очищаем временный файл
            if os.path.exists(temp_log_file):
                os.unlink(temp_log_file)
