import logging
import psycopg2

from config import get_database_config
from database.db_manager import DBManager
from src.nominatim_api import NominatimAPI
from src.opensky_api import OpenSkyAPI
from database.data_loader import AircraftDataLoader
from database.exceptions import DatabaseError, SchemaInitializationError


def main() -> None:
    """Создаёт таблицы, загружает данные и демонстрирует методы DBManager."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger = logging.getLogger("db_logger")

    db_config = get_database_config()
    logger.info("Попытка подключения с конфигурацией: %s", {**db_config, "password": "***"})

    try:
        with DBManager(db_config) as db:
            logger.info("Подключение к БД успешно установлено!")
            # db.initialize_schema()
            # logger.info("Схема БД успешно инициализирована.")
            loader = AircraftDataLoader(NominatimAPI(), OpenSkyAPI(), db)
            print("Статистика загрузки:", loader.load_countries())

    except psycopg2.OperationalError as e:
        logger.error("Ошибка подключения к БД: %s", e)
    except SchemaInitializationError as e:
        logger.error("Ошибка создания таблиц БД: %s", e)
        logger.debug("Технические детали ошибки:", exc_info=True)
    except DatabaseError as e:
        # Сюда попадут любые другие ошибки, которые мы явно пометим как DatabaseError
        logger.error("Ошибка работы с базой данных: %s", e)

    except Exception as e:
        logger.critical("Неожиданная критическая ошибка: %s", e, exc_info=True)




if __name__ == "__main__":
    main()
