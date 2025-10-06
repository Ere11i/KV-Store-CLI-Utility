"""
Утилиты для CLI.
"""

import json
import sys
from typing import Any, Optional


def format_output(data: Any, format_type: str = "auto") -> str:
    """
    Форматирует вывод данных.
    
    Args:
        data: Данные для форматирования
        format_type: Тип форматирования (auto, json, pretty)
        
    Returns:
        Отформатированная строка
    """
    if format_type == "json":
        return json.dumps(data, ensure_ascii=False, indent=2)
    elif format_type == "pretty":
        return _format_pretty(data)
    else:  # auto
        if isinstance(data, (dict, list)):
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:
            return str(data)


def _format_pretty(data: Any) -> str:
    """Красивое форматирование данных."""
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                value_str = str(value)
            lines.append(f"{key}: {value_str}")
        return "\n".join(lines)
    elif isinstance(data, list):
        return "\n".join(str(item) for item in data)
    else:
        return str(data)


def print_error(message: str, prefix: str = "Ошибка") -> None:
    """Выводит сообщение об ошибке."""
    print(f"{prefix}: {message}", file=sys.stderr)


def print_success(message: str, prefix: str = "✓") -> None:
    """Выводит сообщение об успехе."""
    print(f"{prefix} {message}")


def print_warning(message: str, prefix: str = "⚠") -> None:
    """Выводит предупреждение."""
    print(f"{prefix} {message}")


def print_info(message: str, prefix: str = "ℹ") -> None:
    """Выводит информационное сообщение."""
    print(f"{prefix} {message}")


def confirm_action(message: str) -> bool:
    """
    Запрашивает подтверждение действия.
    
    Args:
        message: Сообщение для подтверждения
        
    Returns:
        True если пользователь подтвердил
    """
    while True:
        response = input(f"{message} (y/n): ").strip().lower()
        if response in ("y", "yes", "да", "д"):
            return True
        elif response in ("n", "no", "нет", "н"):
            return False
        else:
            print("Пожалуйста, введите 'y' или 'n'")


def read_multiline_input(prompt: str = "Введите данные (завершите пустой строкой):") -> str:
    """
    Читает многострочный ввод от пользователя.
    
    Args:
        prompt: Приглашение для ввода
        
    Returns:
        Введенный текст
    """
    print(prompt)
    lines = []
    
    try:
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
    except (KeyboardInterrupt, EOFError):
        pass
    
    return "\n".join(lines)
