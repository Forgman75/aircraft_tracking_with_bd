"""Репозиторий для работы с PostgreSQL."""

import logging
from pathlib import Path
from typing import Any, Iterable

import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

from database.exceptions import SchemaInitializationError

logger = logging.getLogger(__name__)


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

    def schema_exists(self) -> bool:
        """
        Проверяет, существуют ли ключевые таблицы схемы в базе данных.
        Возвращает True, если все обязательные таблицы уже созданы.
        """
        required_tables = {"countries", "aircraft"}
        
        try:
            with self.connection.cursor() as cursor:
                # Запрашиваем information_schema — системный каталог PostgreSQL
                cursor.execute(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                      AND table_name = ANY(%s)
                    """,
                    (list(required_tables),)
                )
                existing_tables = {row[0] for row in cursor.fetchall()}
                
                # Проверяем, что все обязательные таблицы присутствуют
                return required_tables <= existing_tables
                
        except psycopg2.Error as e:
            logger.error("Ошибка при проверке существования схемы: %s", e)
            return False

    def initialize_schema(self, schema_path: str | Path | None = None) -> None:
        """Выполняет SQL-скрипт создания таблиц и индексов."""
        path = (
            Path(schema_path)
            if schema_path
            else Path(__file__).with_name("schema.sql")
        )
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(path.read_text(encoding="utf-8"))
            self.connection.commit()

        except Exception as e:
            # Если произошла ошибка, откатываем транзакцию, чтобы соединение
            #  не "зависло"
            self.connection.rollback()
            logger.error(
                "Откат транзакции из-за ошибки в SQL-скрипте: %s", path.name
            )

            error_msg = f"Не удалось выполнить инициализацию схемы БД."

            raise SchemaInitializationError(
                error_msg, file_path=str(path)
            ) from e

    def upsert_country(
        self, name: str, south: float, north: float, west: float, east: float
    ) -> int:
        """Добавляет страну или обновляет её границы; возвращает ID."""
        sql = """
            INSERT INTO countries (name, south, north, west, east)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                south = EXCLUDED.south, north = EXCLUDED.north,
                west = EXCLUDED.west, east = EXCLUDED.east
            RETURNING country_id
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (name, south, north, west, east))
            country_id = cursor.fetchone()[0]
        self.connection.commit()
        return country_id

    def upsert_aircraft(
        self, country_id: int, aircraft_list: Iterable[Any]
    ) -> int:
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
        sql = """
            INSERT INTO aircraft (country_id, callsign, speed, altitude) VALUES %s
            ON CONFLICT (country_id, callsign) DO UPDATE SET
                speed = EXCLUDED.speed, altitude = EXCLUDED.altitude,
                last_seen = CURRENT_TIMESTAMP
        """
        with self.connection.cursor() as cursor:
            execute_values(cursor, sql, rows)
        self.connection.commit()
        return len(rows)

    def get_countries_and_aircraftes_count(self) -> list[dict[str, Any]]:
        """Возвращает страны и количество самолётов, включая страны с нулём."""
        sql = """
            SELECT c.country_id, c.name AS country,
                    COUNT(a.aircraft_id)::INTEGER AS aeroplanes_count
            FROM countries c LEFT JOIN aircraft a ON a.country_id = c.country_id
            GROUP BY c.country_id, c.name ORDER BY c.name
        """
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]

    def get_all_aircraftes(self) -> list[dict[str, Any]]:
        """Возвращает все самолёты вместе со страной наблюдения."""
        sql = """
            SELECT a.aircraft_id, c.name AS country, a.callsign, a.speed,
                    a.altitude, a.last_seen
            FROM aircraft a JOIN countries c ON c.country_id = a.country_id
            ORDER BY c.name, a.callsign
        """
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]

    def get_avg_speed(self) -> float | None:
        """Возвращает среднюю скорость или None, если таблица пуста."""
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT AVG(speed) AS avg_speed FROM aircraft")
            row = cursor.fetchone()
        return (
            float(row["avg_speed"])
            if row and row["avg_speed"] is not None
            else None
        )

    def get_aircraftes_with_higher_speed(self) -> list[dict[str, Any]]:
        """Возвращает самолёты со скоростью выше средней по всей таблице."""
        sql = """
            WITH avg_speed AS (SELECT AVG(speed) AS value FROM aircraft)
            SELECT a.aircraft_id, c.name AS country, a.callsign, a.speed,
                a.altitude, a.last_seen
            FROM aircraft a JOIN countries c ON c.country_id = a.country_id
            CROSS JOIN avg_speed av
            WHERE av.value IS NOT NULL AND a.speed > av.value
            ORDER BY a.speed DESC, c.name, a.callsign
        """
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]

    def get_aircraftes_with_keyword(self, keyword: str) -> list[dict[str, Any]]:
        """Ищет позывные по подстроке без учёта регистра."""
        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError("Ключевое слово не должно быть пустым.")
        sql = '''
            SELECT a.aircraft_id, c.name AS country, a.callsign, a.speed,
                    a.altitude, a.last_seen
            FROM aircraft a JOIN countries c ON c.country_id = a.country_id
            WHERE a.callsign ILIKE %s ORDER BY c.name, a.callsign
        '''
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, (f"%{keyword.strip()}%",))
            return [dict(row) for row in cursor.fetchall()]
    
