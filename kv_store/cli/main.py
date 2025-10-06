"""
Главный модуль CLI для kv-store.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .commands import (
    PutCommand,
    GetCommand,
    DeleteCommand,
    ListCommand,
    ClearCommand,
    LogCommand
)
from ..core.store import KVStore


class KVStoreCLI:
    """Основной класс CLI интерфейса."""
    
    def __init__(self, data_file: Optional[str] = None, log_file: Optional[str] = None):
        """
        Инициализация CLI.
        
        Args:
            data_file: Путь к файлу данных
            log_file: Путь к файлу логов
        """
        self.store = KVStore(data_file, log_file)
        self.commands = {
            "put": PutCommand(self.store),
            "get": GetCommand(self.store),
            "delete": DeleteCommand(self.store),
            "list": ListCommand(self.store),
            "clear": ClearCommand(self.store),
            "log": LogCommand(self.store)
        }
    
    def run_command(self, command: str, args: list[str]) -> None:
        """
        Выполняет команду.
        
        Args:
            command: Название команды
            args: Аргументы команды
        """
        if command not in self.commands:
            print(f"Неизвестная команда: {command}", file=sys.stderr)
            self.show_help()
            return
        
        try:
            self.commands[command].execute(args)
        except Exception as e:
            print(f"Неожиданная ошибка: {e}", file=sys.stderr)
    
    def show_help(self) -> None:
        """Показывает справку по командам."""
        help_text = """
KV-Store CLI - Утилита для работы с ключ-значение хранилищем

Доступные команды:
  put <ключ> <значение>     - Сохранить значение по ключу
  get <ключ>                - Получить значение по ключу
  delete <ключ>             - Удалить значение по ключу
  list                      - Показать все ключи и значения
  clear                     - Очистить хранилище
  log show [операция] [ключ] [лимит] - Показать логи транзакций
  log clear                 - Очистить логи транзакций
  log stats                 - Показать статистику
  help                      - Показать эту справку
  exit                      - Выйти из программы

Примеры:
  put user:1 "Иван Петров"
  get user:1
  put config:theme "dark"
  list
  log show PUT
  log stats
        """
        print(help_text)


def create_parser() -> argparse.ArgumentParser:
    """Создает парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="KV-Store CLI - утилита для работы с ключ-значение хранилищем",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--data-file",
        type=str,
        help="Путь к файлу данных (по умолчанию: kv_store_data.json)"
    )
    
    parser.add_argument(
        "--log-file", 
        type=str,
        help="Путь к файлу логов транзакций (по умолчанию: kv_store_log.json)"
    )
    
    parser.add_argument(
        "--command",
        type=str,
        help="Команда для выполнения (если не указана, запускается интерактивный режим)"
    )
    
    parser.add_argument(
        "args",
        nargs="*",
        help="Аргументы команды"
    )
    
    return parser


def main() -> None:
    """Главная функция CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Устанавливаем пути по умолчанию
    data_file = args.data_file or "kv_store_data.json"
    log_file = args.log_file or "kv_store_log.json"
    
    # Создаем CLI
    cli = KVStoreCLI(data_file, log_file)
    
    # Если указана команда, выполняем её и выходим
    if args.command:
        cli.run_command(args.command, args.args)
        return
    
    # Интерактивный режим
    print("KV-Store CLI - Интерактивный режим")
    print("Введите 'help' для справки, 'exit' для выхода")
    print("-" * 50)
    
    try:
        while True:
            try:
                line = input("kv-store> ").strip()
                
                if not line:
                    continue
                
                if line.lower() in ("exit", "quit", "q"):
                    print("До свидания!")
                    break
                
                if line.lower() in ("help", "?"):
                    cli.show_help()
                    continue
                
                # Парсим команду и аргументы
                parts = line.split()
                command = parts[0]
                command_args = parts[1:] if len(parts) > 1 else []
                
                cli.run_command(command, command_args)
                
            except KeyboardInterrupt:
                print("\nВыход...")
                break
            except EOFError:
                print("\nДо свидания!")
                break
                
    except Exception as e:
        print(f"Критическая ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
