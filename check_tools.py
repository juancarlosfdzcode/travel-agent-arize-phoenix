
"""Smoke test: call each tool directly, without the LLM."""

from tools import convert_currency, get_distance, get_weather

print(get_weather.invoke({"city": "Lisbon"}))
print(convert_currency.invoke({"amount": 100, "from_currency": "EUR", "to_currency": "JPY"}))
print(get_distance.invoke({"city_a": "Madrid", "city_b": "Tokyo"}))
