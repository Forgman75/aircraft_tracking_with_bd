from requests import get
from src.base_classes import APIAdapter


class OpenSkyAPI(APIAdapter):
    """Класс для работы с API OpenSky Network."""

    def __init__(self):
        self.url = "https://opensky-network.org/api/states/all"

    def get_data(self, boundingbox: list) -> list:
        params = {
            "lamin": boundingbox[0],
            "lamax": boundingbox[1],
            "lomin": boundingbox[2],
            "lomax": boundingbox[3],
        }

        response = get(url=self.url, params=params)

        if response.status_code == 429:
            raise RuntimeError("Превышен лимит запросов к OpenSky Network.")

        response.raise_for_status()

        data = response.json()

        states_data = data.get("states")
        if states_data:
            return states_data
        return []
