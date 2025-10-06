"""
Установочный скрипт для kv-store CLI утилиты.
"""

from setuptools import setup, find_packages
import os

# Читаем README для описания
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Читаем requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="kv-store",
    version="1.0.0",
    author="KV-Store Team",
    author_email="team@kv-store.dev",
    description="CLI утилита для работы с ключ-значение хранилищем",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/kv-store/kv-store",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Основные зависимости (встроенные в Python)
        # pytest и другие тестовые зависимости в dev_requires
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "isort>=5.10.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
        "profiling": [
            "memory-profiler>=0.60.0",
            "line-profiler>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "kv-store=kv_store.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="cli key-value store database thread-safe concurrent",
    project_urls={
        "Bug Reports": "https://github.com/kv-store/kv-store/issues",
        "Source": "https://github.com/kv-store/kv-store",
        "Documentation": "https://kv-store.readthedocs.io/",
    },
)
