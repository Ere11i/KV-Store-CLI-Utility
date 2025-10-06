# Makefile для kv-store CLI утилиты

.PHONY: help install install-dev test test-cov test-race lint format clean build docs

# Переменные
PYTHON := python3
PIP := pip3
PYTEST := pytest
BLACK := black
FLAKE8 := flake8
MYPY := mypy
ISORT := isort

# Цвета для вывода
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Показать справку по командам
	@echo "$(GREEN)KV-Store CLI - Доступные команды:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Установить пакет
	@echo "$(GREEN)Установка kv-store...$(NC)"
	$(PIP) install -e .

install-dev: ## Установить пакет для разработки
	@echo "$(GREEN)Установка kv-store для разработки...$(NC)"
	$(PIP) install -e .[dev]

install-docs: ## Установить зависимости для документации
	@echo "$(GREEN)Установка зависимостей для документации...$(NC)"
	$(PIP) install -e .[docs]

install-profiling: ## Установить зависимости для профилирования
	@echo "$(GREEN)Установка зависимостей для профилирования...$(NC)"
	$(PIP) install -e .[profiling]

test: ## Запустить все тесты
	@echo "$(GREEN)Запуск тестов...$(NC)"
	$(PYTEST) tests/ -v

test-core: ## Запустить тесты основного модуля
	@echo "$(GREEN)Запуск тестов основного модуля...$(NC)"
	$(PYTEST) tests/test_core/ -v

test-cli: ## Запустить тесты CLI
	@echo "$(GREEN)Запуск тестов CLI...$(NC)"
	$(PYTEST) tests/test_cli/ -v

test-race: ## Запустить тесты на race conditions
	@echo "$(GREEN)Запуск тестов на race conditions...$(NC)"
	$(PYTEST) tests/test_race_conditions/ -v -s

test-cov: ## Запустить тесты с покрытием кода
	@echo "$(GREEN)Запуск тестов с покрытием кода...$(NC)"
	$(PYTEST) tests/ --cov=kv_store --cov-report=html --cov-report=term-missing

test-cov-open: test-cov ## Запустить тесты с покрытием и открыть отчет
	@echo "$(GREEN)Открытие отчета покрытия...$(NC)"
	@if command -v xdg-open > /dev/null; then \
		xdg-open htmlcov/index.html; \
	elif command -v open > /dev/null; then \
		open htmlcov/index.html; \
	else \
		echo "Отчет покрытия создан в htmlcov/index.html"; \
	fi

test-stress: ## Запустить стресс-тесты
	@echo "$(GREEN)Запуск стресс-тестов...$(NC)"
	$(PYTEST) tests/test_race_conditions/test_concurrent_operations.py::TestConcurrentOperations::test_thread_pool_stress_test -v -s

test-contention: ## Запустить тесты высокой конкуренции
	@echo "$(GREEN)Запуск тестов высокой конкуренции...$(NC)"
	$(PYTEST) tests/test_race_conditions/test_concurrent_operations.py::TestConcurrentOperations::test_high_contention_operations -v -s

lint: ## Запустить линтеры
	@echo "$(GREEN)Запуск линтеров...$(NC)"
	$(FLAKE8) kv_store/ tests/
	$(MYPY) kv_store/

format: ## Форматировать код
	@echo "$(GREEN)Форматирование кода...$(NC)"
	$(BLACK) kv_store/ tests/
	$(ISORT) kv_store/ tests/

format-check: ## Проверить форматирование кода
	@echo "$(GREEN)Проверка форматирования кода...$(NC)"
	$(BLACK) --check kv_store/ tests/
	$(ISORT) --check-only kv_store/ tests/

clean: ## Очистить временные файлы
	@echo "$(GREEN)Очистка временных файлов...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -f kv_store_data.json
	rm -f kv_store_log.json
	rm -f *.tmp
	rm -f *.temp

build: clean ## Собрать пакет
	@echo "$(GREEN)Сборка пакета...$(NC)"
	$(PYTHON) setup.py sdist bdist_wheel

build-install: build ## Собрать и установить пакет
	@echo "$(GREEN)Установка собранного пакета...$(NC)"
	$(PIP) install dist/*.whl

docs: ## Создать документацию
	@echo "$(GREEN)Создание документации...$(NC)"
	@if [ ! -d "docs" ]; then \
		echo "$(YELLOW)Создание структуры документации...$(NC)"; \
		mkdir -p docs; \
		sphinx-quickstart -q -p "KV-Store" -a "KV-Store Team" -v "1.0.0" -r "1.0.0" -l "ru" docs/; \
	fi
	$(MAKE) -C docs html

docs-open: docs ## Создать и открыть документацию
	@echo "$(GREEN)Открытие документации...$(NC)"
	@if command -v xdg-open > /dev/null; then \
		xdg-open docs/_build/html/index.html; \
	elif command -v open > /dev/null; then \
		open docs/_build/html/index.html; \
	else \
		echo "Документация создана в docs/_build/html/index.html"; \
	fi

run: ## Запустить CLI в интерактивном режиме
	@echo "$(GREEN)Запуск KV-Store CLI...$(NC)"
	$(PYTHON) -m kv_store.cli.main

run-example: ## Запустить пример использования
	@echo "$(GREEN)Запуск примера использования...$(NC)"
	@echo "$(YELLOW)Выполняем пример команд:$(NC)"
	@echo "put user:1 'Иван Петров'"
	@echo "put config:theme 'dark'"
	@echo "put settings:timeout 30"
	@echo "list"
	@echo "get user:1"
	@echo "log show"
	@echo "log stats"
	@echo ""
	$(PYTHON) -m kv_store.cli.main --command put user:1 "Иван Петров"
	$(PYTHON) -m kv_store.cli.main --command put config:theme "dark"
	$(PYTHON) -m kv_store.cli.main --command put settings:timeout 30
	$(PYTHON) -m kv_store.cli.main --command list
	$(PYTHON) -m kv_store.cli.main --command get user:1
	$(PYTHON) -m kv_store.cli.main --command log show
	$(PYTHON) -m kv_store.cli.main --command log stats

benchmark: ## Запустить бенчмарки
	@echo "$(GREEN)Запуск бенчмарков...$(NC)"
	$(PYTEST) tests/test_race_conditions/test_concurrent_operations.py::TestConcurrentOperations::test_high_contention_operations -v -s --tb=short
	$(PYTEST) tests/test_race_conditions/test_concurrent_operations.py::TestConcurrentOperations::test_thread_pool_stress_test -v -s --tb=short

profile: ## Запустить профилирование
	@echo "$(GREEN)Запуск профилирования...$(NC)"
	@echo "$(YELLOW)Для профилирования установите зависимости: make install-profiling$(NC)"
	$(PYTHON) -m memory_profiler -m kv_store.cli.main --command put test_key "test_value"

check: format-check lint test ## Полная проверка кода
	@echo "$(GREEN)Все проверки пройдены успешно!$(NC)"

ci: install-dev check test-cov ## Команды для CI/CD
	@echo "$(GREEN)CI/CD проверки завершены!$(NC)"

# Специальные команды для разработки
dev-setup: install-dev ## Настройка окружения для разработки
	@echo "$(GREEN)Настройка окружения для разработки...$(NC)"
	@echo "$(YELLOW)Установка pre-commit хуков...$(NC)"
	@if command -v pre-commit > /dev/null; then \
		pre-commit install; \
	else \
		echo "$(RED)pre-commit не установлен. Установите: pip install pre-commit$(NC)"; \
	fi

watch-test: ## Запуск тестов при изменении файлов
	@echo "$(GREEN)Запуск тестов при изменении файлов...$(NC)"
	@echo "$(YELLOW)Для этого установите: pip install pytest-watch$(NC)"
	@if command -v ptw > /dev/null; then \
		ptw tests/; \
	else \
		echo "$(RED)pytest-watch не установлен. Установите: pip install pytest-watch$(NC)"; \
	fi

# Информационные команды
version: ## Показать версию
	@echo "$(GREEN)Версия KV-Store:$(NC)"
	@$(PYTHON) -c "import kv_store; print(kv_store.__version__)"

info: ## Показать информацию о проекте
	@echo "$(GREEN)Информация о проекте KV-Store:$(NC)"
	@echo "Версия: $(shell $(PYTHON) -c 'import kv_store; print(kv_store.__version__)' 2>/dev/null || echo 'Не установлен')"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Расположение: $(shell pwd)"
	@echo "Файлы данных:"
	@ls -la *.json 2>/dev/null || echo "  Файлы данных не найдены"

# Помощь по командам
help-test: ## Показать справку по тестам
	@echo "$(GREEN)Доступные тесты:$(NC)"
	@echo "  make test           - Все тесты"
	@echo "  make test-core      - Тесты основного модуля"
	@echo "  make test-cli       - Тесты CLI"
	@echo "  make test-race      - Тесты на race conditions"
	@echo "  make test-cov       - Тесты с покрытием кода"
	@echo "  make test-stress    - Стресс-тесты"
	@echo "  make test-contention - Тесты высокой конкуренции"

help-dev: ## Показать справку по разработке
	@echo "$(GREEN)Команды для разработки:$(NC)"
	@echo "  make install-dev    - Установка для разработки"
	@echo "  make dev-setup      - Настройка окружения"
	@echo "  make format         - Форматирование кода"
	@echo "  make lint           - Проверка кода"
	@echo "  make check          - Полная проверка"
	@echo "  make watch-test     - Тесты при изменении файлов"
