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
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(path.read_text(encoding="utf-8"))
            self.connection.commit()
            print("Схема БД успешно инициализирована.")
        except Exception as e:
            # Если произошла ошибка, откатываем транзакцию, чтобы соединение не "зависло"
            self.connection.rollback()
            raise RuntimeError(f"Ошибка при инициализации схемы БД: {e}") from e

    def upsert_country(self, name: str, south: float, north: float,
                       west: float, east: float) -> int:
        """Добавляет страну или обновляет её границы; возвращает ID."""
        sql = '''
            INSERT INTO countries (name, south, north, west, east)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                south = EXCLUDED.south, north = EXCLUDED.north,
                west = EXCLUDED.west, east = EXCLUDED.east
            RETURNING country_id
        '''
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (name, south, north, west, east))
            country_id = cursor.fetchone()[0]
        self.connection.commit()
        return country_id

    def upsert_aircraft(self, country_id: int, aircraft_list: Iterable[Any]) -> int:
        """Вставляет самолёты или обновляет их по стране и позывному."""
        rows = []
        for aircraft in aircraft_list:
            callsign = str(getattr(aircraft, "callsign", "")).strip()
            if not callsign:
                continue
            speed = float(getattr(aircraft, "speed", 0) or 0)
            altitude = float(getattr(aircraft, "altitude", 0) or 0)
            if speed >= 0 and altitude >= 0:
                rows.append((country_id, callsign, speed, altitude))
        if not rows:
            return 0
        sql = '''
            INSERT INTO aircraft (country_id, callsign, speed, altitude) VALUES %s
            ON CONFLICT (country_id, callsign) DO UPDATE SET
                speed = EXCLUDED.speed, altitude = EXCLUDED.altitude,
                last_seen = CURRENT_TIMESTAMP
        '''
        with self.connection.cursor() as cursor:
            execute_values(cursor, sql, rows)
        self.connection.commit()
        return len(rows)



