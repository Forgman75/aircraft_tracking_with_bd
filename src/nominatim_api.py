from requests import get
from src.base_classes import APIAdapter


class NominatimAPI(APIAdapter):
    """Класс для работы с API Nominatim OpenStreetMap."""

    def __init__(self):
        self.url = "https://nominatim.openstreetmap.org/search"

    def get_data(self, country: str) -> list:
        headers = {"User-Agent": "test-app/1.0"}

        params = {
            "country": country,
            "format": "json",
            "limit": 1,
        }

        response = get(url=self.url, params=params, headers=headers)

        response.raise_for_status()

        data = response.json()

        if not data:
            raise ValueError(f"Не удалось найти координаты страны: {country}")

        return data[0]["boundingbox"]
