"""
Команды CLI для kv-store.
"""

import json
import sys
from typing import Any, Optional
from abc import ABC, abstractmethod

from ..core.store import KVStore
from ..core.exceptions import KVStoreError, KeyNotFoundError


class BaseCommand(ABC):
    """Базовый класс для команд CLI."""
    
    def __init__(self, store: KVStore):
        self.store = store
    
    @abstractmethod
    def execute(self, args: list[str]) -> None:
        """Выполняет команду."""
        pass
    
    def _print_error(self, message: str) -> None:
        """Выводит сообщение об ошибке."""
        print(f"Ошибка: {message}", file=sys.stderr)
    
    def _print_success(self, message: str) -> None:
        """Выводит сообщение об успехе."""
        print(f"✓ {message}")
    
    def _print_json(self, data: Any) -> None:
        """Выводит данные в JSON формате."""
        print(json.dumps(data, ensure_ascii=False, indent=2))


class PutCommand(BaseCommand):
    """Команда для сохранения значения."""
    
    def execute(self, args: list[str]) -> None:
        if len(args) < 2:
            self._print_error("Использование: put <ключ> <значение>")
            return
        
        key = args[0]
        value = args[1]
        
        try:
            # Пытаемся распарсить JSON если возможно
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                # Если не JSON, оставляем как строку
                pass
            
            self.store.put(key, value)
            self._print_success(f"Значение сохранено: {key} = {value}")
            
        except KVStoreError as e:
            self._print_error(str(e))


class GetCommand(BaseCommand):
    """Команда для получения значения."""
    
    def execute(self, args: list[str]) -> None:
        if len(args) < 1:
            self._print_error("Использование: get <ключ>")
            return
        
        key = args[0]
        
        try:
            value = self.store.get(key)
            self._print_json(value)
            
        except KeyNotFoundError:
            self._print_error(f"Ключ '{key}' не найден")
        except KVStoreError as e:
            self._print_error(str(e))


class DeleteCommand(BaseCommand):
    """Команда для удаления значения."""
    
    def execute(self, args: list[str]) -> None:
        if len(args) < 1:
            self._print_error("Использование: delete <ключ>")
            return
        
        key = args[0]
        
        try:
            old_value = self.store.delete(key)
            self._print_success(f"Ключ '{key}' удален (значение: {old_value})")
            
        except KeyNotFoundError:
            self._print_error(f"Ключ '{key}' не найден")
        except KVStoreError as e:
            self._print_error(str(e))


class ListCommand(BaseCommand):
    """Команда для вывода всех ключей."""
    
    def execute(self, args: list[str]) -> None:
        try:
            keys = list(self.store.keys())
            if not keys:
                print("Хранилище пусто")
                return
            
            print(f"Найдено ключей: {len(keys)}")
            for key in keys:
                try:
                    value = self.store.get(key)
                    print(f"  {key}: {value}")
                except KeyNotFoundError:
                    print(f"  {key}: <ошибка чтения>")
                    
        except KVStoreError as e:
            self._print_error(str(e))


class ClearCommand(BaseCommand):
    """Команда для очистки хранилища."""
    
    def execute(self, args: list[str]) -> None:
        try:
            size = self.store.size()
            self.store.clear()
            self._print_success(f"Хранилище очищено (удалено {size} элементов)")
            
        except KVStoreError as e:
            self._print_error(str(e))


class LogCommand(BaseCommand):
    """Команда для работы с логами транзакций."""
    
    def execute(self, args: list[str]) -> None:
        if not args:
            self._print_error("Использование: log <команда>")
            self._print_error("Команды: show, clear, stats")
            return
        
        command = args[0].lower()
        
        try:
            if command == "show":
                self._show_logs(args[1:])
            elif command == "clear":
                self.store._logger.clear_log()
                self._print_success("Лог транзакций очищен")
            elif command == "stats":
                self._show_stats()
            else:
                self._print_error(f"Неизвестная команда: {command}")
                
        except Exception as e:
            self._print_error(f"Ошибка выполнения команды лога: {e}")
    
    def _show_logs(self, args: list[str]) -> None:
        """Показывает логи транзакций."""
        operation = args[0] if args else None
        key = args[1] if len(args) > 1 else None
        limit = int(args[2]) if len(args) > 2 else None
        
        transactions = self.store._logger.get_transactions(
            operation=operation,
            key=key,
            limit=limit
        )
        
        if not transactions:
            print("Логи транзакций пусты")
            return
        
        print(f"Найдено транзакций: {len(transactions)}")
        self._print_json(transactions)
    
    def _show_stats(self) -> None:
        """Показывает статистику."""
        transactions = self.store._logger.get_transactions()
        
        stats = {
            "общее_количество_транзакций": len(transactions),
            "размер_хранилища": self.store.size(),
            "операции": {}
        }
        
        # Подсчитываем операции
        for transaction in transactions:
            op = transaction.get("operation", "unknown")
            stats["операции"][op] = stats["операции"].get(op, 0) + 1
        
        self._print_json(stats)
