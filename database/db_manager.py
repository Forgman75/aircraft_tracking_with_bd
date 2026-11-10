"""Репозиторий для работы с PostgreSQL."""
from pathlib import Path
from typing import Any, Iterable

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values


class DBManager:
    """Управляет соединением, схемой, записью и выборкой данных."""

    def __init__(self, db_config: dict[str, Any]) -> None:
        """Подключается к PostgreSQL с переданными параметрами."""
        self.connection = psycopg2.connect(**db_config)

    def __enter__(self) -> "DBManager":
        """Возвращает менеджер для использования в with."""
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Закрывает соединение при выходе из with."""
        self.close()

    def close(self) -> None:
        """Закрывает соединение, если оно ещё открыто."""
        if self.connection and not self.connection.closed:
            self.connection.close()

    def initialize_schema(self, schema_path: str | Path | None = None) -> None:
        """Выполняет SQL-скрипт создания таблиц и индексов."""
        path = Path(schema_path) if schema_path else Path(__file__).with_name("schema.sql")
        with self.connection.cursor() as cursor:
            cursor.execute(path.read_text(encoding="utf-8"))
        self.connection.commit()

