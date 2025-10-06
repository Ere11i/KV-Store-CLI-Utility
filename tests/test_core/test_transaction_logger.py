"""
Тесты для логгера транзакций.
"""

import pytest
import json
import tempfile
import os
import threading
from datetime import datetime

from kv_store.core.transaction_logger import TransactionLogger


class TestTransactionLogger:
    """Тесты для TransactionLogger."""
    
    def test_basic_logging(self):
        """Тест базового логирования."""
        logger = TransactionLogger()
        
        # Логируем транзакцию
        logger.log_transaction(
            operation="PUT",
            key="test_key",
            value="test_value",
            timestamp=datetime.now()
        )
        
        # Проверяем что счетчик увеличился
        assert logger._transaction_counter == 1
    
    def test_file_logging(self):
        """Тест логирования в файл."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            logger = TransactionLogger(log_file=temp_file)
            
            # Логируем несколько транзакций
            logger.log_transaction("PUT", "key1", "value1")
            logger.log_transaction("GET", "key1", "value1")
            logger.log_transaction("DELETE", "key1", old_value="value1")
            
            # Проверяем файл
            assert os.path.exists(temp_file)
            
            with open(temp_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            assert len(logs) == 3
            assert logs[0]["operation"] == "PUT"
            assert logs[1]["operation"] == "GET"
            assert logs[2]["operation"] == "DELETE"
            assert all("transaction_id" in log for log in logs)
            assert all("timestamp" in log for log in logs)
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_get_transactions(self):
        """Тест получения транзакций."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            logger = TransactionLogger(log_file=temp_file)
            
            # Логируем транзакции
            logger.log_transaction("PUT", "key1", "value1")
            logger.log_transaction("PUT", "key2", "value2")
            logger.log_transaction("GET", "key1", "value1")
            logger.log_transaction("DELETE", "key2", old_value="value2")
            
            # Получаем все транзакции
            all_transactions = logger.get_transactions()
            assert len(all_transactions) == 4
            
            # Фильтруем по операции
            put_transactions = logger.get_transactions(operation="PUT")
            assert len(put_transactions) == 2
            
            # Фильтруем по ключу
            key1_transactions = logger.get_transactions(key="key1")
            assert len(key1_transactions) == 2
            
            # Фильтруем по операции и ключу
            put_key1 = logger.get_transactions(operation="PUT", key="key1")
            assert len(put_key1) == 1
            
            # Тест лимита
            limited = logger.get_transactions(limit=2)
            assert len(limited) == 2
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_clear_log(self):
        """Тест очистки лога."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            logger = TransactionLogger(log_file=temp_file)
            
            # Логируем транзакции
            logger.log_transaction("PUT", "key1", "value1")
            logger.log_transaction("PUT", "key2", "value2")
            
            # Проверяем что лог не пустой
            assert len(logger.get_transactions()) == 2
            
            # Очищаем лог
            logger.clear_log()
            
            # Проверяем что лог пустой
            assert len(logger.get_transactions()) == 0
            
            # Проверяем файл
            with open(temp_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            assert logs == []
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_serialization(self):
        """Тест сериализации различных типов данных."""
        logger = TransactionLogger()
        
        # Тест различных типов значений
        test_values = [
            "string",
            123,
            45.67,
            True,
            False,
            None,
            {"nested": "object"},
            ["list", "of", "items"],
            {"complex": {"nested": [1, 2, 3]}}
        ]
        
        for i, value in enumerate(test_values):
            logger.log_transaction(
                operation="PUT",
                key=f"key_{i}",
                value=value
            )
        
        # Проверяем что все значения корректно обработаны
        assert logger._transaction_counter == len(test_values)
    
    def test_concurrent_logging(self):
        """Тест многопоточного логирования."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            logger = TransactionLogger(log_file=temp_file)
            
            def log_worker(worker_id, num_operations):
                """Рабочая функция для логирования."""
                for i in range(num_operations):
                    logger.log_transaction(
                        operation="PUT",
                        key=f"worker_{worker_id}_key_{i}",
                        value=f"value_{worker_id}_{i}"
                    )
            
            # Запускаем несколько потоков
            num_threads = 5
            num_operations = 20
            threads = []
            
            for i in range(num_threads):
                thread = threading.Thread(
                    target=log_worker,
                    args=(i, num_operations)
                )
                threads.append(thread)
                thread.start()
            
            # Ждем завершения всех потоков
            for thread in threads:
                thread.join()
            
            # Проверяем что все транзакции залогированы
            expected_total = num_threads * num_operations
            assert logger._transaction_counter == expected_total
            
            # Проверяем файл
            transactions = logger.get_transactions()
            assert len(transactions) == expected_total
            
            # Проверяем что нет дублированных ID
            transaction_ids = [t["transaction_id"] for t in transactions]
            assert len(transaction_ids) == len(set(transaction_ids))
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_metadata_logging(self):
        """Тест логирования с метаданными."""
        logger = TransactionLogger()
        
        metadata = {
            "user_id": "user123",
            "session_id": "session456",
            "ip_address": "192.168.1.1"
        }
        
        logger.log_transaction(
            operation="PUT",
            key="user:123",
            value="profile_data",
            metadata=metadata
        )
        
        # Проверяем что метаданные сохранены
        assert logger._transaction_counter == 1
    
    def test_corrupted_log_file_recovery(self):
        """Тест восстановления после поврежденного файла."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            # Создаем поврежденный JSON файл
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write("invalid json content")
            
            # Создаем логгер - должен обработать поврежденный файл
            logger = TransactionLogger(log_file=temp_file)
            
            # Логируем новую транзакцию
            logger.log_transaction("PUT", "key1", "value1")
            
            # Проверяем что новая транзакция записана
            transactions = logger.get_transactions()
            assert len(transactions) == 1
            assert transactions[0]["operation"] == "PUT"
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_timestamp_handling(self):
        """Тест обработки временных меток."""
        logger = TransactionLogger()
        
        # Логируем с явной временной меткой
        custom_time = datetime(2023, 12, 25, 15, 30, 45)
        logger.log_transaction(
            operation="PUT",
            key="timestamp_test",
            value="test_value",
            timestamp=custom_time
        )
        
        # Логируем без временной метки (должна быть текущая)
        logger.log_transaction(
            operation="GET",
            key="timestamp_test",
            value="test_value"
        )
        
        # Проверяем что временные метки корректны
        assert logger._transaction_counter == 2
