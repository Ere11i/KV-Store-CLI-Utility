"""
Модуль для логирования транзакций в JSON формате.
"""

import json
import threading
from typing import Any, Optional, Dict
from datetime import datetime
from pathlib import Path


class TransactionLogger:
    """
    Логгер транзакций с поддержкой JSON формата.
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Инициализация логгера транзакций.
        
        Args:
            log_file: Путь к файлу лога (опционально)
        """
        self._log_file = Path(log_file) if log_file else None
        self._lock = threading.Lock()
        self._transaction_counter = 0
        
        # Создаем файл лога если указан
        if self._log_file:
            self._log_file.parent.mkdir(parents=True, exist_ok=True)
            self._initialize_log_file()
    
    def _initialize_log_file(self) -> None:
        """Инициализирует файл лога."""
        if not self._log_file.exists():
            with open(self._log_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
    
    def log_transaction(
        self,
        operation: str,
        key: Optional[str] = None,
        value: Optional[Any] = None,
        old_value: Optional[Any] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Логирует транзакцию в JSON формате.
        
        Args:
            operation: Тип операции (PUT, GET, DELETE, CLEAR)
            key: Ключ (если применимо)
            value: Новое значение (если применимо)
            old_value: Старое значение (если применимо)
            timestamp: Временная метка (по умолчанию текущее время)
            metadata: Дополнительные метаданные
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        with self._lock:
            self._transaction_counter += 1
            
            transaction = {
                "transaction_id": self._transaction_counter,
                "operation": operation,
                "timestamp": timestamp.isoformat(),
                "key": key,
                "value": self._serialize_value(value),
                "old_value": self._serialize_value(old_value),
                "metadata": metadata or {}
            }
            
            # Удаляем None значения для чистоты лога
            transaction = {k: v for k, v in transaction.items() if v is not None}
            
            if self._log_file:
                self._write_to_file(transaction)
            else:
                # Если файл не указан, выводим в консоль
                print(json.dumps(transaction, ensure_ascii=False, indent=2))
    
    def _serialize_value(self, value: Any) -> Any:
        """Сериализует значение для JSON."""
        try:
            # Пробуем сериализовать в JSON для проверки
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            # Если не удается сериализовать, преобразуем в строку
            return str(value)
    
    def _write_to_file(self, transaction: Dict[str, Any]) -> None:
        """Записывает транзакцию в файл."""
        try:
            # Читаем существующие транзакции
            transactions = []
            if self._log_file.exists():
                with open(self._log_file, 'r', encoding='utf-8') as f:
                    try:
                        transactions = json.load(f)
                        if not isinstance(transactions, list):
                            transactions = []
                    except json.JSONDecodeError:
                        transactions = []
            
            # Добавляем новую транзакцию
            transactions.append(transaction)
            
            # Записываем обратно
            with open(self._log_file, 'w', encoding='utf-8') as f:
                json.dump(transactions, f, ensure_ascii=False, indent=2)
                
        except IOError as e:
            print(f"Ошибка записи в лог файл: {e}")
    
    def get_transactions(
        self,
        operation: Optional[str] = None,
        key: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list[Dict[str, Any]]:
        """
        Получает транзакции из лога.
        
        Args:
            operation: Фильтр по операции
            key: Фильтр по ключу
            limit: Максимальное количество транзакций
            
        Returns:
            Список транзакций
        """
        if not self._log_file or not self._log_file.exists():
            return []
        
        with self._lock:
            try:
                with open(self._log_file, 'r', encoding='utf-8') as f:
                    transactions = json.load(f)
                
                if not isinstance(transactions, list):
                    return []
                
                # Применяем фильтры
                filtered_transactions = []
                for transaction in transactions:
                    if operation and transaction.get("operation") != operation:
                        continue
                    if key and transaction.get("key") != key:
                        continue
                    filtered_transactions.append(transaction)
                
                # Применяем лимит
                if limit:
                    filtered_transactions = filtered_transactions[-limit:]
                
                return filtered_transactions
                
            except (IOError, json.JSONDecodeError):
                return []
    
    def clear_log(self) -> None:
        """Очищает лог транзакций."""
        if self._log_file and self._log_file.exists():
            with self._lock:
                with open(self._log_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
