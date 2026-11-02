
from tools import convert_currency, get_distance, get_weather

print(get_weather.invoke({"city": "Lisboa"}))
print(convert_currency.invoke({"amount": 100, "from_currency": "EUR", "to_currency": "JPY"}))
print(get_distance.invoke({"city_a": "Madrid", "city_b": "Tokio"}))
