#!/usr/bin/env python3
"""
Главный исполняемый файл для kv-store CLI утилиты.

Использование:
    python kv_store_cli.py [команда] [аргументы]
    python kv_store_cli.py --help
"""

if __name__ == "__main__":
    from kv_store.cli.main import main
    main()
