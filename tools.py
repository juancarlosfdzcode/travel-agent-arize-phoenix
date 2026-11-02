import math

import httpx
from langchain_core.tools import tool

TIMEOUT = 10

WEATHER_CODES = {
    0: "despejado", 1: "mayormente despejado", 2: "parcialmente nublado",
    3: "nublado", 45: "niebla", 48: "niebla con escarcha",
    51: "llovizna ligera", 53: "llovizna", 55: "llovizna intensa",
    61: "lluvia ligera", 63: "lluvia", 65: "lluvia intensa",
    71: "nieve ligera", 73: "nieve", 75: "nieve intensa",
    80: "chubascos ligeros", 81: "chubascos", 82: "chubascos fuertes",
    95: "tormenta", 96: "tormenta con granizo", 99: "tormenta fuerte con granizo",
}


def geocode(city: str) -> dict:
    """Convierte un nombre de ciudad en coordenadas (helper interno, no es tool)."""
    r = httpx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "es", "format": "json"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    results = r.json().get("results")
    if not results:
        raise ValueError(f"No encuentro la ciudad '{city}'")
    place = results[0]
    return {
        "name": place["name"],
        "country": place.get("country", ""),
        "lat": place["latitude"],
        "lon": place["longitude"],
    }


@tool
def get_weather(city: str) -> dict:
    """Devuelve el tiempo actual en una ciudad: temperatura (°C), estado del cielo y viento (km/h)."""
    place = geocode(city)
    r = httpx.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["lat"],
            "longitude": place["lon"],
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    current = r.json()["current"]
    return {
        "city": f"{place['name']}, {place['country']}",
        "temperature_c": current["temperature_2m"],
        "condition": WEATHER_CODES.get(current["weather_code"], "desconocido"),
        "wind_kmh": current["wind_speed_10m"],
    }


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convierte una cantidad entre dos divisas usando códigos ISO de 3 letras (EUR, USD, JPY...)."""
    src, dst = from_currency.upper(), to_currency.upper()
    r = httpx.get(
        "https://api.frankfurter.dev/v1/latest",
        params={"base": src, "symbols": dst},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    data = r.json()
    rate = data["rates"][dst]
    return {
        "amount": amount,
        "from": src,
        "to": dst,
        "rate": rate,
        "result": round(amount * rate, 2),
        "date": data["date"],
    }


@tool
def get_distance(city_a: str, city_b: str) -> dict:
    """Calcula la distancia en línea recta (km) entre dos ciudades."""
    a, b = geocode(city_a), geocode(city_b)
    R = 6371  # radio de la Tierra en km
    lat1, lat2 = math.radians(a["lat"]), math.radians(b["lat"])
    dlat = lat2 - lat1
    dlon = math.radians(b["lon"] - a["lon"])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    km = 2 * R * math.asin(math.sqrt(h))
    return {
        "from": f"{a['name']}, {a['country']}",
        "to": f"{b['name']}, {b['country']}",
        "distance_km": round(km),
    }


TOOLS = [get_weather, convert_currency, get_distance]
