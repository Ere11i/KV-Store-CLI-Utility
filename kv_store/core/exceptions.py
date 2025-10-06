"""
Исключения для kv-store.
"""


class KVStoreError(Exception):
    """Базовое исключение для kv-store."""
    pass


class KeyNotFoundError(KVStoreError):
    """Исключение при отсутствии ключа."""
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Ключ '{key}' не найден")


class InvalidKeyError(KVStoreError):
    """Исключение при недопустимом ключе."""
    def __init__(self, key: str, reason: str = ""):
        self.key = key
        super().__init__(f"Недопустимый ключ '{key}': {reason}")


class InvalidValueError(KVStoreError):
    """Исключение при недопустимом значении."""
    def __init__(self, value, reason: str = ""):
        self.value = value
        super().__init__(f"Недопустимое значение '{value}': {reason}")


class TransactionError(KVStoreError):
    """Исключение при ошибке транзакции."""
    pass
