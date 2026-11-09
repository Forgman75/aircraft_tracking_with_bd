from functools import total_ordering


@total_ordering
class Aircraft:
    """Класс, представляющий самолет с валидацией и методами сравнения."""

    def __init__(
        self, country: str, callsign: str, speed: float, altitude: float
    ):
        self.country = self._validate_str(country, "Страна регистрации")
        self.callsign = self._validate_str(callsign, "Позывной")
        self.speed = self._validate_float(speed, "Скорость полета")
        self.altitude = self._validate_float(altitude, "Высота полета")

    @staticmethod
    def _validate_str(value, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} должна быть непустой строкой.")
        return value.strip()

    @staticmethod
    def _validate_float(value, field_name: str) -> float:
        try:
            # OpenSky API иногда возвращает None, заменяем на 0.0
            val = float(value) if value is not None else 0.0
            if val < 0:
                raise ValueError(f"{field_name} не может быть отрицательной.")
            return val
        except (TypeError, ValueError):
            raise ValueError(
                f"{field_name} должна быть неотрицательным числом."
            )

    # Сравнение по высоте (используется для сортировки)
    def __lt__(self, other):
        if not isinstance(other, Aircraft):
            return NotImplemented
        return self.altitude < other.altitude

    def __gt__(self, other):
        if not isinstance(other, Aircraft):
            return NotImplemented
        return self.altitude > other.altitude

    def __eq__(self, other):
        if not isinstance(other, Aircraft):
            return NotImplemented
        return self.altitude == other.altitude and self.speed == other.speed

    # Дополнительный метод для сравнения по скорости
    def is_faster_than(self, other: "Aircraft") -> bool:
        if not isinstance(other, Aircraft):
            raise TypeError("Сравнивать можно только с объектом Aircraft")
        return self.speed > other.speed

    def to_dict(self) -> dict:
        return {
            "country": self.country,
            "callsign": self.callsign,
            "speed": self.speed,
            "altitude": self.altitude,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Aircraft":
        return cls(**data)

    @classmethod
    def cast_to_object_list(cls, raw_api_data: list) -> list:
        """
        Преобразует данные OpenSky API в список объектов Aircraft.

        Индексы OpenSky:
        1 — callsign
        2 — origin_country
        9 — velocity
        13 — geo_altitude
        """
        result = []

        if not isinstance(raw_api_data, list):
            return result

        for item in raw_api_data:
            if len(item) < 14:
                continue

            try:
                aircraft_dict = {
                    "country": item[2],
                    "callsign": item[1],
                    "speed": item[9],
                    "altitude": item[13],
                }

                one_aircraft = cls.from_dict(aircraft_dict)
                result.append(one_aircraft)
            except (ValueError, TypeError):
                continue

        return result

    def __repr__(self):
        return (
            f"Aircraft("
            f"country={self.country!r}, "
            f"callsign={self.callsign!r}, "
            f"speed={self.speed}, "
            f"altitude={self.altitude})"
        )

    def __str__(self):
        return (
            f"Позывной: {self.callsign:8} "
            f"Страна: {self.country:15} "
            f"Высота: {self.altitude:6.0f} м "
            f"Скорость: {self.speed:5.0f} м/с"
        )
