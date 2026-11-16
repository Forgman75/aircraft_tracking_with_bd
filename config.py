"""Конфигурация подключения к PostgreSQL."""
import os
from dotenv import load_dotenv


def get_database_config() -> dict:
    """Возвращает настройки PostgreSQL из .env или окружения."""
    load_dotenv()
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "aircraft_tracking"),
        "user": os.getenv("DB_USER", "dispatcher"),
        "password": os.getenv("DB_PASSWORD", ""),
    }
