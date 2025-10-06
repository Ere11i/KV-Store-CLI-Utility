# KV-Store CLI - Быстрый Старт

## 🚀 Установка и Запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Запуск в интерактивном режиме
```bash
python kv_store_cli.py
```

### 3. Примеры команд
```bash
# Сохранить данные
put user:1 "Иван Петров"
put config:theme "dark"
put settings:timeout 30

# Получить данные
get user:1
get config:theme

# Показать все ключи
list

# Показать логи
log show
log stats

# Выход
exit
```

## 🧪 Запуск тестов

### Все тесты
```bash
pytest tests/ -v
```

### Тесты на race conditions
```bash
pytest tests/test_race_conditions/ -v -s
```

### Тесты с покрытием
```bash
pytest tests/ --cov=kv_store --cov-report=html
```

## 📊 Примеры использования

### Базовые операции
```python
from kv_store.core.store import KVStore

store = KVStore()
store.put("key1", "value1")
value = store.get("key1")
store.delete("key1")
```

### Concurrent операции
```python
import threading
from kv_store.core.store import KVStore

store = KVStore()

def worker():
    for i in range(100):
        store.put(f"key_{i}", f"value_{i}")

# Запуск в 10 потоков
threads = []
for _ in range(10):
    thread = threading.Thread(target=worker)
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

print(f"Размер хранилища: {store.size()}")
```

## 🔧 Команды Make

```bash
make help          # Показать все команды
make install-dev   # Установка для разработки
make test          # Запуск тестов
make test-race     # Тесты на race conditions
make format        # Форматирование кода
make lint          # Проверка кода
make check         # Полная проверка
make run           # Запуск CLI
make run-example   # Пример использования
```

## 📁 Структура файлов

После запуска создадутся файлы:
- `kv_store_data.json` - файл с данными
- `kv_store_log.json` - файл с логами транзакций

## ⚡ Производительность

Типичные показатели:
- PUT: ~1000+ операций/сек
- GET: ~2000+ операций/сек
- Concurrent: ~800+ операций/сек

## 🆘 Помощь

- `help` в CLI - справка по командам
- `README.md` - полная документация
- `examples/basic_usage.py` - примеры кода
- Тесты в `tests/` - примеры использования API
