import logging

from src.base_classes import APIAdapter
from src.aircraft import Aircraft
from database.db_manager import DBManager

logger = logging.getLogger(__name__)

COUNTRIES = (
    "Germany", "France", "Netherlands", "Belgium", 
    "Spain", "Italy", "Austria", "Switzerland", 
)


class AircraftDataLoader:
    """Оркестрирует получение границ стран и данных самолётов."""

    def __init__(self, nominatim_api: APIAdapter, opensky_api: APIAdapter, db_manager: DBManager) -> None:
        self.nominatim_api = nominatim_api
        self.opensky_api = opensky_api
        self.db_manager = db_manager

    def load_countries(self, countries: tuple[str, ...] = COUNTRIES) -> dict[str, int]:
        """Загружает страны и данные о самолётах, игнорируя ошибки по отдельным странам."""
        stats = {"countries_saved": 0, "aircraft_upserted": 0, "countries_failed": 0}
        
        for country_name in countries:
            try:
                # Получаем границы. NominatimAPI возвращает список из 4 строк: [south, north, west, east]
                bounds = self.nominatim_api.get_data(country=country_name)
                south, north, west, east = map(float, bounds)  # Преобразуем строки в float
                
                # Сохраняем страну и получаем её ID
                country_id = self.db_manager.upsert_country(country_name, south, north, west, east)
                stats["countries_saved"] += 1
                
                # Получаем список самолётов.
                states = self.opensky_api.get_data([south, north, west, east])
                
                # Преобразуем сырые данные в объекты и фильтруем пустые позывные
                objects = Aircraft.cast_to_object_list(states)
                normalized = [
                    Aircraft(country=country_name, callsign=obj.callsign,
                             speed=obj.speed, altitude=obj.altitude)
                    for obj in objects if str(getattr(obj, "callsign", "")).strip()
                ]
                
                # Массово сохраняем самолёты в БД
                stats["aircraft_upserted"] += self.db_manager.upsert_aircraft(country_id, normalized)
                logger.info(" %s: получено самолётов: %s", country_name, len(normalized))
                
            except Exception:
                stats["countries_failed"] += 1
                logger.exception(" Не удалось обработать страну: %s", country_name)
                
        return stats
