import os
import time
from datetime import datetime

import requests


OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_LAT = 37.5663
DEFAULT_LON = 126.9922
CACHE_TTL_SECONDS = 1800
_cached_weather: tuple[float, dict] | None = None


def _sample_weather() -> dict:
    month = datetime.now().month
    if month in (12, 1, 2):
        return {
            "category": "cold",
            "summary": "쌀쌀하고 건조함",
            "temperature_c": 3,
            "note": "따뜻한 국물 음식에 가점",
        }
    if month in (6, 7, 8):
        return {
            "category": "hot",
            "summary": "덥고 습함",
            "temperature_c": 29,
            "note": "실내 좌석과 가벼운 메뉴에 가점",
        }
    return {
        "category": "clear",
        "summary": "맑음",
        "temperature_c": 18,
        "note": "무난한 점심 메뉴 중심 추천",
    }


def _classify_weather(description: str, temperature_c: int) -> tuple[str, str, str]:
    desc = description.lower()
    if "rain" in desc or "drizzle" in desc or "thunderstorm" in desc:
        return "rainy", "비 또는 소나기", "실내 좌석과 국물 메뉴에 가점"
    if temperature_c >= 28:
        return "hot", "덥고 습함", "시원한 면류와 실내 좌석에 가점"
    if temperature_c <= 5:
        return "cold", "쌀쌀하고 건조함", "따뜻한 국물 음식에 가점"
    return "clear", "맑음", "무난한 점심 메뉴 중심 추천"


def _fetch_openweather(lat: float, lon: float, api_key: str) -> dict:
    response = requests.get(
        OPENWEATHER_API_URL,
        params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
        timeout=5,
    )
    response.raise_for_status()
    payload = response.json()
    temperature_c = round(payload["main"]["temp"])
    category, summary, note = _classify_weather(payload["weather"][0]["main"], temperature_c)
    return {
        "category": category,
        "summary": summary,
        "temperature_c": temperature_c,
        "note": note,
    }


def get_lunch_weather() -> dict:
    global _cached_weather

    api_key = os.getenv("WEATHER_API_KEY", "").strip()
    if not api_key:
        return _sample_weather()

    now = time.time()
    if _cached_weather and now - _cached_weather[0] < CACHE_TTL_SECONDS:
        return _cached_weather[1]

    try:
        weather = _fetch_openweather(DEFAULT_LAT, DEFAULT_LON, api_key)
    except Exception:
        weather = _sample_weather()

    _cached_weather = (now, weather)
    return weather
