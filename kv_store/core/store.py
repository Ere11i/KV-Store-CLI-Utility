"""
Основное хранилище ключ-значение с thread-safe операциями.
"""

import json
import threading
from typing import Any, Optional, Dict, Iterator
from datetime import datetime
from pathlib import Path

from .exceptions import KeyNotFoundError, InvalidKeyError, InvalidValueError, TransactionError
from .transaction_logger import TransactionLogger


class KVStore:
    """
    Thread-safe хранилище ключ-значение с поддержкой транзакций.
    """
    
    def __init__(self, data_file: Optional[str] = None, log_file: Optional[str] = None):
        """
        Инициализация KV-хранилища.
        
        Args:
            data_file: Путь к файлу данных (опционально)
            log_file: Путь к файлу логов транзакций (опционально)
        """
        self._data: Dict[str, Any] = {}
        self._lock = threading.RwLock()
        self._data_file = Path(data_file) if data_file else None
        self._logger = TransactionLogger(log_file)
        
        # Загружаем данные при инициализации
        if self._data_file and self._data_file.exists():
            self._load_data()
    
    def _load_data(self) -> None:
        """Загружает данные из файла."""
        try:
            with open(self._data_file, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise TransactionError(f"Ошибка загрузки данных: {e}")
    
    def _save_data(self) -> None:
        """Сохраняет данные в файл."""
        if not self._data_file:
            return
            
        try:
            with open(self._data_file, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise TransactionError(f"Ошибка сохранения данных: {e}")
    
    def _validate_key(self, key: str) -> None:
        """Валидация ключа."""
        if not isinstance(key, str):
            raise InvalidKeyError(key, "ключ должен быть строкой")
        if not key.strip():
            raise InvalidKeyError(key, "ключ не может быть пустым")
    
    def _validate_value(self, value: Any) -> None:
        """Валидация значения."""
        if value is None:
            raise InvalidValueError(value, "значение не может быть None")
    
    def put(self, key: str, value: Any) -> None:
        """
        Сохраняет значение по ключу.
        
        Args:
            key: Ключ
            value: Значение для сохранения
        """
        self._validate_key(key)
        self._validate_value(value)
        
        with self._lock.write_lock:
            old_value = self._data.get(key)
            self._data[key] = value
            self._save_data()
            
            # Логируем транзакцию
            self._logger.log_transaction(
                operation="PUT",
                key=key,
                value=value,
                old_value=old_value,
                timestamp=datetime.now()
            )
    
    def get(self, key: str) -> Any:
        """
        Получает значение по ключу.
        
        Args:
            key: Ключ
            
        Returns:
            Значение, связанное с ключом
            
        Raises:
            KeyNotFoundError: Если ключ не найден
        """
        self._validate_key(key)
        
        with self._lock.read_lock:
            if key not in self._data:
                raise KeyNotFoundError(key)
            
            value = self._data[key]
            
            # Логируем транзакцию
            self._logger.log_transaction(
                operation="GET",
                key=key,
                value=value,
                timestamp=datetime.now()
            )
            
            return value
    
    def delete(self, key: str) -> Any:
        """
        Удаляет значение по ключу.
        
        Args:
            key: Ключ
            
        Returns:
            Удаленное значение
            
        Raises:
            KeyNotFoundError: Если ключ не найден
        """
        self._validate_key(key)
        
        with self._lock.write_lock:
            if key not in self._data:
                raise KeyNotFoundError(key)
            
            old_value = self._data.pop(key)
            self._save_data()
            
            # Логируем транзакцию
            self._logger.log_transaction(
                operation="DELETE",
                key=key,
                old_value=old_value,
                timestamp=datetime.now()
            )
            
            return old_value
    
    def keys(self) -> Iterator[str]:
        """Возвращает итератор по всем ключам."""
        with self._lock.read_lock:
            return iter(self._data.keys())
    
    def values(self) -> Iterator[Any]:
        """Возвращает итератор по всем значениям."""
        with self._lock.read_lock:
            return iter(self._data.values())
    
    def items(self) -> Iterator[tuple[str, Any]]:
        """Возвращает итератор по всем парам ключ-значение."""
        with self._lock.read_lock:
            return iter(self._data.items())
    
    def clear(self) -> None:
        """Очищает все данные."""
        with self._lock.write_lock:
            self._data.clear()
            self._save_data()
            
            # Логируем транзакцию
            self._logger.log_transaction(
                operation="CLEAR",
                timestamp=datetime.now()
            )
    
    def size(self) -> int:
        """Возвращает количество элементов."""
        with self._lock.read_lock:
            return len(self._data)
    
    def exists(self, key: str) -> bool:
        """Проверяет существование ключа."""
        self._validate_key(key)
        
        with self._lock.read_lock:
            return key in self._data
