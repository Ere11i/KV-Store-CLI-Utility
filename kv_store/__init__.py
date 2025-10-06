"""
KV-Store - CLI утилита для работы с ключ-значение хранилищем.

Основные возможности:
- put/get/delete операции
- JSON-логирование транзакций
- Thread-safe операции с RwLock
- CLI интерфейс
"""

__version__ = "1.0.0"
__author__ = "KV-Store Team"

from .core.store import KVStore
from .core.transaction_logger import TransactionLogger
from .cli.main import main

__all__ = ["KVStore", "TransactionLogger", "main"]
