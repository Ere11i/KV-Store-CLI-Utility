"""
Основной модуль kv-store.
Содержит базовую логику хранилища и логирования транзакций.
"""

from .store import KVStore
from .transaction_logger import TransactionLogger
from .exceptions import (
    KVStoreError,
    KeyNotFoundError,
    InvalidKeyError,
    InvalidValueError,
    TransactionError
)

__all__ = [
    "KVStore",
    "TransactionLogger", 
    "KVStoreError",
    "KeyNotFoundError",
    "InvalidKeyError",
    "InvalidValueError",
    "TransactionError"
]
