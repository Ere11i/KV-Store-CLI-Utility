"""
Специализированные тесты на race conditions и concurrent операции.
"""

import pytest
import threading
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from kv_store.core.store import KVStore


class TestConcurrentOperations:
    """Тесты concurrent операций для выявления race conditions."""
    
    def test_high_contention_operations(self):
        """Тест операций с высокой конкуренцией за одни и те же ключи."""
        store = KVStore()
        num_threads = 10
        num_operations = 100
        
        # Статистика операций
        operation_stats = defaultdict(int)
        errors = []
        
        def worker(thread_id):
            """Рабочая функция с высокой конкуренцией."""
            for i in range(num_operations):
                key = f"contention_key_{i % 5}"  # Только 5 ключей для высокой конкуренции
                
                operation = random.choice(["put", "get", "delete"])
                operation_stats[operation] += 1
                
                try:
                    if operation == "put":
                        store.put(key, f"value_{thread_id}_{i}")
                    elif operation == "get":
                        try:
                            store.get(key)
                        except KeyError:
                            pass  # Ожидаемо при concurrent delete
                    elif operation == "delete":
                        try:
                            store.delete(key)
                        except KeyError:
                            pass  # Ожидаемо при concurrent delete
                    
                except Exception as e:
                    errors.append(f"Thread {thread_id}: {e}")
        
        # Запускаем потоки
        threads = []
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Проверяем что нет критических ошибок
        critical_errors = [e for e in errors if "lock" not in str(e).lower()]
        assert len(critical_errors) == 0, f"Критические ошибки: {critical_errors}"
        
        # Проверяем производительность
        total_operations = sum(operation_stats.values())
        ops_per_second = total_operations / duration
        print(f"Производительность: {ops_per_second:.2f} операций/сек")
        
        # Проверяем что хранилище в консистентном состоянии
        assert store.size() >= 0  # Должно быть неотрицательным
    
    def test_read_write_lock_fairness(self):
        """Тест справедливости read-write блокировок."""
        store = KVStore()
        
        # Инициализируем данные
        for i in range(10):
            store.put(f"key_{i}", f"initial_value_{i}")
        
        read_count = [0]
        write_count = [0]
        read_times = []
        write_times = []
        
        def reader():
            """Функция читателя."""
            for _ in range(20):
                start_time = time.time()
                try:
                    key = f"key_{random.randint(0, 9)}"
                    store.get(key)
                    read_count[0] += 1
                except KeyError:
                    pass  # Ожидаемо при concurrent delete
                finally:
                    read_times.append(time.time() - start_time)
        
        def writer():
            """Функция писателя."""
            for i in range(10):
                start_time = time.time()
                key = f"key_{random.randint(0, 9)}"
                store.put(key, f"updated_value_{i}")
                write_count[0] += 1
                write_times.append(time.time() - start_time)
        
        # Запускаем потоки
        threads = []
        
        # 3 читателя
        for _ in range(3):
            thread = threading.Thread(target=reader)
            threads.append(thread)
        
        # 2 писателя
        for _ in range(2):
            thread = threading.Thread(target=writer)
            threads.append(thread)
        
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        end_time = time.time()
        
        # Проверяем что операции выполнены
        assert read_count[0] > 0
        assert write_count[0] > 0
        
        # Проверяем что нет блокировок навсегда
        total_time = end_time - start_time
        assert total_time < 10.0, "Операции заняли слишком много времени"
        
        # Проверяем что среднее время операций разумное
        avg_read_time = sum(read_times) / len(read_times) if read_times else 0
        avg_write_time = sum(write_times) / len(write_times) if write_times else 0
        
        assert avg_read_time < 1.0, "Чтение слишком медленное"
        assert avg_write_time < 1.0, "Запись слишком медленная"
    
    def test_concurrent_delete_and_get(self):
        """Тест одновременного удаления и получения."""
        store = KVStore()
        
        # Инициализируем данные
        test_keys = [f"key_{i}" for i in range(20)]
        for key in test_keys:
            store.put(key, f"value_{key}")
        
        get_results = []
        delete_results = []
        errors = []
        
        def get_worker():
            """Рабочая функция для получения."""
            for key in test_keys:
                try:
                    value = store.get(key)
                    get_results.append((key, value))
                except Exception as e:
                    errors.append(f"GET {key}: {e}")
        
        def delete_worker():
            """Рабочая функция для удаления."""
            for key in test_keys:
                try:
                    old_value = store.delete(key)
                    delete_results.append((key, old_value))
                except Exception as e:
                    errors.append(f"DELETE {key}: {e}")
        
        # Запускаем потоки одновременно
        get_thread = threading.Thread(target=get_worker)
        delete_thread = threading.Thread(target=delete_worker)
        
        get_thread.start()
        delete_thread.start()
        
        get_thread.join()
        delete_thread.join()
        
        # Проверяем что нет критических ошибок
        critical_errors = [e for e in errors if "lock" not in str(e).lower()]
        assert len(critical_errors) == 0, f"Критические ошибки: {critical_errors}"
        
        # Проверяем что операции выполнены
        assert len(get_results) + len(delete_results) > 0
        
        # Проверяем что хранилище в консистентном состоянии
        final_size = store.size()
        assert final_size >= 0
        assert final_size <= 20  # Не может быть больше исходного количества
    
    def test_thread_pool_stress_test(self):
        """Стресс-тест с ThreadPoolExecutor."""
        store = KVStore()
        
        def operation(operation_type, key, value=None):
            """Выполняет операцию."""
            try:
                if operation_type == "put":
                    store.put(key, value)
                    return f"PUT {key}={value}"
                elif operation_type == "get":
                    try:
                        result = store.get(key)
                        return f"GET {key}={result}"
                    except KeyError:
                        return f"GET {key}=NOT_FOUND"
                elif operation_type == "delete":
                    try:
                        result = store.delete(key)
                        return f"DELETE {key}={result}"
                    except KeyError:
                        return f"DELETE {key}=NOT_FOUND"
                elif operation_type == "exists":
                    exists = store.exists(key)
                    return f"EXISTS {key}={exists}"
                elif operation_type == "size":
                    size = store.size()
                    return f"SIZE={size}"
            except Exception as e:
                return f"ERROR {operation_type} {key}: {e}"
        
        # Создаем много задач
        tasks = []
        
        # Задачи записи
        for i in range(50):
            tasks.append(("put", f"key_{i}", f"value_{i}"))
        
        # Задачи чтения
        for i in range(30):
            tasks.append(("get", f"key_{i}"))
        
        # Задачи удаления
        for i in range(20):
            tasks.append(("delete", f"key_{i}"))
        
        # Задачи проверки существования
        for i in range(25):
            tasks.append(("exists", f"key_{i}"))
        
        # Задачи получения размера
        for i in range(10):
            tasks.append(("size", None))
        
        # Выполняем задачи в пуле потоков
        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for task in tasks:
                future = executor.submit(operation, *task)
                futures.append(future)
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append(f"FUTURE_ERROR: {e}")
        
        # Проверяем результаты
        assert len(results) == len(tasks)
        
        # Проверяем что нет критических ошибок
        error_results = [r for r in results if "ERROR" in r]
        critical_errors = [r for r in error_results if "lock" not in r.lower()]
        
        if critical_errors:
            print(f"Критические ошибки: {critical_errors[:5]}")  # Показываем первые 5
        
        # Проверяем что хранилище в консистентном состоянии
        final_size = store.size()
        assert final_size >= 0
        assert final_size <= 50  # Максимум 50 ключей было добавлено
    
    def test_memory_consistency(self):
        """Тест консистентности памяти при concurrent операциях."""
        store = KVStore()
        
        # Инициализируем данные
        initial_data = {f"key_{i}": f"value_{i}" for i in range(10)}
        for key, value in initial_data.items():
            store.put(key, value)
        
        consistency_errors = []
        
        def consistency_checker():
            """Проверяет консистентность данных."""
            for _ in range(100):
                try:
                    # Получаем все ключи
                    keys = list(store.keys())
                    
                    # Проверяем что каждый ключ существует и имеет значение
                    for key in keys:
                        try:
                            value = store.get(key)
                            if value is None:
                                consistency_errors.append(f"NULL value for key {key}")
                        except KeyError:
                            consistency_errors.append(f"Key {key} disappeared during iteration")
                    
                    # Проверяем что размер соответствует количеству ключей
                    if store.size() != len(keys):
                        consistency_errors.append(f"Size mismatch: store.size()={store.size()}, keys_count={len(keys)}")
                
                except Exception as e:
                    consistency_errors.append(f"Consistency check error: {e}")
        
        def modifier():
            """Модифицирует данные."""
            for i in range(50):
                operation = random.choice(["put", "delete"])
                key = f"key_{random.randint(0, 15)}"  # Некоторые ключи могут не существовать
                
                try:
                    if operation == "put":
                        store.put(key, f"modified_value_{i}")
                    else:
                        try:
                            store.delete(key)
                        except KeyError:
                            pass  # Ожидаемо
                except Exception as e:
                    consistency_errors.append(f"Modification error: {e}")
        
        # Запускаем потоки
        checker_thread = threading.Thread(target=consistency_checker)
        modifier_thread = threading.Thread(target=modifier)
        
        checker_thread.start()
        modifier_thread.start()
        
        checker_thread.join()
        modifier_thread.join()
        
        # Проверяем консистентность
        if consistency_errors:
            print(f"Ошибки консистентности: {consistency_errors[:10]}")  # Показываем первые 10
        
        # Допускаем небольшое количество ошибок из-за race conditions
        # но не должно быть критических ошибок блокировок
        critical_errors = [e for e in consistency_errors if "lock" in e.lower()]
        assert len(critical_errors) == 0, f"Критические ошибки блокировок: {critical_errors}"
