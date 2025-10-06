"""
Тесты для CLI команд.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from io import StringIO
import sys

from kv_store.cli.commands import (
    PutCommand,
    GetCommand,
    DeleteCommand,
    ListCommand,
    ClearCommand,
    LogCommand
)
from kv_store.core.store import KVStore
from kv_store.core.exceptions import KeyNotFoundError, InvalidKeyError


class TestCLICommands:
    """Тесты для CLI команд."""
    
    @pytest.fixture
    def mock_store(self):
        """Создает mock хранилища."""
        store = Mock(spec=KVStore)
        store._logger = Mock()
        return store
    
    @pytest.fixture
    def put_command(self, mock_store):
        """Создает команду put."""
        return PutCommand(mock_store)
    
    @pytest.fixture
    def get_command(self, mock_store):
        """Создает команду get."""
        return GetCommand(mock_store)
    
    @pytest.fixture
    def delete_command(self, mock_store):
        """Создает команду delete."""
        return DeleteCommand(mock_store)
    
    @pytest.fixture
    def list_command(self, mock_store):
        """Создает команду list."""
        return ListCommand(mock_store)
    
    @pytest.fixture
    def clear_command(self, mock_store):
        """Создает команду clear."""
        return ClearCommand(mock_store)
    
    @pytest.fixture
    def log_command(self, mock_store):
        """Создает команду log."""
        return LogCommand(mock_store)
    
    def test_put_command_success(self, put_command, mock_store, capsys):
        """Тест успешного выполнения команды put."""
        put_command.execute(["key1", "value1"])
        
        mock_store.put.assert_called_once_with("key1", "value1")
        
        captured = capsys.readouterr()
        assert "Значение сохранено: key1 = value1" in captured.out
    
    def test_put_command_json_value(self, put_command, mock_store):
        """Тест команды put с JSON значением."""
        put_command.execute(["key1", '{"name": "test"}'])
        
        # Проверяем что JSON был распарсен
        call_args = mock_store.put.call_args
        assert call_args[0][0] == "key1"
        assert call_args[0][1] == {"name": "test"}
    
    def test_put_command_insufficient_args(self, put_command, capsys):
        """Тест команды put с недостаточными аргументами."""
        put_command.execute(["key1"])
        
        captured = capsys.readouterr()
        assert "Использование: put <ключ> <значение>" in captured.err
    
    def test_put_command_error(self, put_command, mock_store, capsys):
        """Тест команды put с ошибкой."""
        mock_store.put.side_effect = InvalidKeyError("", "пустой ключ")
        
        put_command.execute(["", "value1"])
        
        captured = capsys.readouterr()
        assert "Недопустимый ключ" in captured.err
    
    def test_get_command_success(self, get_command, mock_store, capsys):
        """Тест успешного выполнения команды get."""
        mock_store.get.return_value = "test_value"
        
        get_command.execute(["key1"])
        
        mock_store.get.assert_called_once_with("key1")
        
        captured = capsys.readouterr()
        assert "test_value" in captured.out
    
    def test_get_command_key_not_found(self, get_command, mock_store, capsys):
        """Тест команды get с отсутствующим ключом."""
        mock_store.get.side_effect = KeyNotFoundError("key1")
        
        get_command.execute(["key1"])
        
        captured = capsys.readouterr()
        assert "Ключ 'key1' не найден" in captured.err
    
    def test_get_command_insufficient_args(self, get_command, capsys):
        """Тест команды get с недостаточными аргументами."""
        get_command.execute([])
        
        captured = capsys.readouterr()
        assert "Использование: get <ключ>" in captured.err
    
    def test_delete_command_success(self, delete_command, mock_store, capsys):
        """Тест успешного выполнения команды delete."""
        mock_store.delete.return_value = "deleted_value"
        
        delete_command.execute(["key1"])
        
        mock_store.delete.assert_called_once_with("key1")
        
        captured = capsys.readouterr()
        assert "Ключ 'key1' удален" in captured.out
        assert "deleted_value" in captured.out
    
    def test_delete_command_key_not_found(self, delete_command, mock_store, capsys):
        """Тест команды delete с отсутствующим ключом."""
        mock_store.delete.side_effect = KeyNotFoundError("key1")
        
        delete_command.execute(["key1"])
        
        captured = capsys.readouterr()
        assert "Ключ 'key1' не найден" in captured.err
    
    def test_delete_command_insufficient_args(self, delete_command, capsys):
        """Тест команды delete с недостаточными аргументами."""
        delete_command.execute([])
        
        captured = capsys.readouterr()
        assert "Использование: delete <ключ>" in captured.err
    
    def test_list_command_with_data(self, list_command, mock_store, capsys):
        """Тест команды list с данными."""
        mock_store.keys.return_value = ["key1", "key2"]
        mock_store.get.side_effect = ["value1", "value2"]
        
        list_command.execute([])
        
        captured = capsys.readouterr()
        assert "Найдено ключей: 2" in captured.out
        assert "key1: value1" in captured.out
        assert "key2: value2" in captured.out
    
    def test_list_command_empty(self, list_command, mock_store, capsys):
        """Тест команды list с пустым хранилищем."""
        mock_store.keys.return_value = []
        
        list_command.execute([])
        
        captured = capsys.readouterr()
        assert "Хранилище пусто" in captured.out
    
    def test_clear_command_success(self, clear_command, mock_store, capsys):
        """Тест успешного выполнения команды clear."""
        mock_store.size.return_value = 5
        
        clear_command.execute([])
        
        mock_store.clear.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Хранилище очищено (удалено 5 элементов)" in captured.out
    
    def test_log_command_show(self, log_command, mock_store, capsys):
        """Тест команды log show."""
        mock_transactions = [
            {"operation": "PUT", "key": "key1", "value": "value1"},
            {"operation": "GET", "key": "key1", "value": "value1"}
        ]
        mock_store._logger.get_transactions.return_value = mock_transactions
        
        log_command.execute(["show"])
        
        captured = capsys.readouterr()
        assert "Найдено транзакций: 2" in captured.out
        assert "PUT" in captured.out
        assert "GET" in captured.out
    
    def test_log_command_show_empty(self, log_command, mock_store, capsys):
        """Тест команды log show с пустыми логами."""
        mock_store._logger.get_transactions.return_value = []
        
        log_command.execute(["show"])
        
        captured = capsys.readouterr()
        assert "Логи транзакций пусты" in captured.out
    
    def test_log_command_clear(self, log_command, mock_store, capsys):
        """Тест команды log clear."""
        log_command.execute(["clear"])
        
        mock_store._logger.clear_log.assert_called_once()
        
        captured = capsys.readouterr()
        assert "Лог транзакций очищен" in captured.out
    
    def test_log_command_stats(self, log_command, mock_store, capsys):
        """Тест команды log stats."""
        mock_store._logger.get_transactions.return_value = [
            {"operation": "PUT"},
            {"operation": "PUT"},
            {"operation": "GET"},
            {"operation": "DELETE"}
        ]
        mock_store.size.return_value = 10
        
        log_command.execute(["stats"])
        
        captured = capsys.readouterr()
        assert "общее_количество_транзакций" in captured.out
        assert "размер_хранилища" in captured.out
        assert "операции" in captured.out
    
    def test_log_command_invalid(self, log_command, capsys):
        """Тест команды log с недопустимой подкомандой."""
        log_command.execute(["invalid"])
        
        captured = capsys.readouterr()
        assert "Неизвестная команда: invalid" in captured.err
    
    def test_log_command_no_args(self, log_command, capsys):
        """Тест команды log без аргументов."""
        log_command.execute([])
        
        captured = capsys.readouterr()
        assert "Использование: log <команда>" in captured.err


class TestIntegrationCLI:
    """Интеграционные тесты CLI с реальным хранилищем."""
    
    def test_full_workflow(self, capsys):
        """Тест полного рабочего процесса."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            store = KVStore(data_file=temp_file)
            
            # Тест put команды
            put_cmd = PutCommand(store)
            put_cmd.execute(["user:1", "Иван Петров"])
            put_cmd.execute(["user:2", "Мария Сидорова"])
            put_cmd.execute(["config:theme", "dark"])
            
            # Тест get команды
            get_cmd = GetCommand(store)
            get_cmd.execute(["user:1"])
            
            captured = capsys.readouterr()
            assert "Иван Петров" in captured.out
            
            # Тест list команды
            list_cmd = ListCommand(store)
            list_cmd.execute([])
            
            captured = capsys.readouterr()
            assert "Найдено ключей: 3" in captured.out
            assert "user:1: Иван Петров" in captured.out
            
            # Тест delete команды
            delete_cmd = DeleteCommand(store)
            delete_cmd.execute(["user:2"])
            
            captured = capsys.readouterr()
            assert "Ключ 'user:2' удален" in captured.out
            
            # Проверяем что данные действительно удалены
            with pytest.raises(KeyNotFoundError):
                store.get("user:2")
            
            # Проверяем что остальные данные на месте
            assert store.get("user:1") == "Иван Петров"
            assert store.get("config:theme") == "dark"
            
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
