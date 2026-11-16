import logging
import psycopg2

from config import get_database_config
from database.db_manager import DBManager
from src.nominatim_api import NominatimAPI
from src.opensky_api import OpenSkyAPI
from database.data_loader import AircraftDataLoader
from database.exceptions import DatabaseError, SchemaInitializationError


def print_rows(title: str, rows: list[dict]) -> None:
    """Печатает результаты SQL-запроса."""
    print(f"\\n{title}")
    if not rows:
        print("Данных нет.")
    for row in rows:
        print(" | ".join(f"{key}: {value}" for key, value in row.items()))


def show_menu():
    """Выводит главное меню."""
    print("\n" + "-" * 60)
    print("МЕНЮ:")
    print("1. Вывести страны и количество самолетов над каждой")
    print("2. Показать все сохраненные самолеты")
    print("3. Вывести среднюю скорость всех самолетов")
    print("4. Вывести все самолеты, движущиеся со скоростью выше средней")
    print("5. Найти самолеты по части позывного")
    print("6. Выход")
    print("-" * 60)


def get_menu_choice() -> str:
    """Получает выбор пользователя."""
    return input("Выберите действие (1-6): ").strip()


def search_by_sub_callsign(db: DBManager):
    """
    Получает от пользователя часть позывного для поиска самолетов
    """
    keyword = input("Часть позывного для поиска (например DLH): ").strip()
    if keyword:
        print_rows("Результат поиска", db.get_aircraftes_with_keyword(keyword))


def handle_menu_choice(
    choice: str, db: DBManager
) -> bool:
    """
    Обрабатывает выбор пользователя.

    Возвращает False, если нужно завершить программу.
    """
    if choice == "1":
        print_rows("Страны и количество самолётов", db.get_countries_and_aircraftes_count())

    elif choice == "2":
        print_rows("Все самолёты", db.get_all_aircraftes())

    elif choice == "3":
        print("Средняя скорость:", db.get_avg_speed())

    elif choice == "4":
        print_rows("Самолёты быстрее средней", db.get_aircraftes_with_higher_speed())

    elif choice == "5":
        search_by_sub_callsign(db)

    elif choice == "6":
        print("Выход из программы. До свидания!")
        return False

    else:
        print("Неверный выбор. " "Пожалуйста, введите число от 1 до 6.")

    return True


def run_interactive_client(db: DBManager):
    """
    Функция выводит в цикле меню, получает выбор пользователя
    и вызывает соответствующий метод DBManager-а или завершает
    выполнение программы
    """

    while True:
        show_menu()
    
        choice = get_menu_choice()
    
        if not handle_menu_choice(choice, db):
            break



def main() -> None:
    """Создаёт таблицы, загружает данные и демонстрирует методы DBManager."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logger = logging.getLogger("db_logger")

    db_config = get_database_config()
    logger.info("Попытка подключения с конфигурацией: %s", {**db_config, "password": "***"})

    try:
        with DBManager(db_config) as db:
            logger.info("Подключение к БД успешно установлено!")
            if db.schema_exists():
                logger.info("Схема БД уже существует. Пропускаем инициализацию.")
            else:
                db.initialize_schema()
                logger.info("Схема БД успешно инициализирована.")
            loader = AircraftDataLoader(NominatimAPI(), OpenSkyAPI(), db)
            print("Статистика загрузки:", loader.load_countries())
            run_interactive_client(db)

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
