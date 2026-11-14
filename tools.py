
"""Travel tools exposed to the agent: weather, currency conversion and distance."""

import math

import httpx
from langchain_core.tools import tool

REQUEST_TIMEOUT_SECONDS = 10
EARTH_RADIUS_KM = 6371

WEATHER_CODES = {
    0: "clear sky", 1: "mainly clear", 2: "partly cloudy",
    3: "overcast", 45: "fog", 48: "depositing rime fog",
    51: "light drizzle", 53: "drizzle", 55: "dense drizzle",
    61: "light rain", 63: "rain", 65: "heavy rain",
    71: "light snow", 73: "snow", 75: "heavy snow",
    80: "light showers", 81: "showers", 82: "violent showers",
    95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm with hail",
}


def geocode(city: str) -> dict:
    """Resolve a city name to coordinates (internal helper, not exposed as a tool)."""
    response = httpx.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    results = response.json().get("results")
    if not results:
        raise ValueError(f"City not found: '{city}'")
    place = results[0]
    return {
        "name": place["name"],
        "country": place.get("country", ""),
        "lat": place["latitude"],
        "lon": place["longitude"],
    }


@tool
def get_weather(city: str) -> dict:
    """Get the current weather in a city: temperature (°C), sky condition and wind speed (km/h)."""
    place = geocode(city)
    response = httpx.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["lat"],
            "longitude": place["lon"],
            "current": "temperature_2m,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    current = response.json()["current"]
    return {
        "city": f"{place['name']}, {place['country']}",
        "temperature_c": current["temperature_2m"],
        "condition": WEATHER_CODES.get(current["weather_code"], "unknown"),
        "wind_kmh": current["wind_speed_10m"],
    }


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount between two currencies using 3-letter ISO codes (EUR, USD, JPY...)."""
    source_currency = from_currency.upper()
    target_currency = to_currency.upper()
    response = httpx.get(
        "https://api.frankfurter.dev/v1/latest",
        params={"base": source_currency, "symbols": target_currency},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    rate = data["rates"][target_currency]
    return {
        "amount": amount,
        "from": source_currency,
        "to": target_currency,
        "rate": rate,
        "result": round(amount * rate, 2),
        "date": data["date"],
    }


@tool
def get_distance(city_a: str, city_b: str) -> dict:
    """Compute the straight-line (great-circle) distance in km between two cities."""
    origin = geocode(city_a)
    destination = geocode(city_b)

    # Haversine formula
    lat_origin = math.radians(origin["lat"])
    lat_destination = math.radians(destination["lat"])
    delta_lat = lat_destination - lat_origin
    delta_lon = math.radians(destination["lon"] - origin["lon"])
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_origin) * math.cos(lat_destination) * math.sin(delta_lon / 2) ** 2
    )
    distance_km = 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(haversine))

    return {
        "from": f"{origin['name']}, {origin['country']}",
        "to": f"{destination['name']}, {destination['country']}",
        "distance_km": round(distance_km),
    }


TOOLS = [get_weather, convert_currency, get_distance]
