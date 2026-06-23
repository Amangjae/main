import os
import requests
from datetime import datetime
from functools import lru_cache
import time


OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
CACHE_TTL = 3600  # 1시간


def _sample_weather() -> dict:
    month = datetime.now().month
    if month in (12, 1, 2):
        return {
            "category": "cold",
            "summary": "저저하고 건조함",
            "temperature_c": 3,
            "note": "따뜻한 국물 음식에 가깝",
        }
    if month in (6, 7, 8):
        return {
            "category": "hot",
            "summary": "덥고 습함",
            "temperature_c": 29,
            "note": "실내 좌석과 가벼운 메뉴에 가깝",
        }
    return {
        "category": "clear",
        "summary": "맑음",
        "temperature_c": 18,
        "note": "무난한 점심 메뉴 중심 추천",
    }


def _get_openweather(lat: float, lon: float, api_key: str) -> dict:
    """OpenWeather API 호출 (실제 날씨 데이터)"""
    try:
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
        }
        response = requests.get(OPENWEATHER_API_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        temp = int(data["main"]["temp"])
        description = data["weather"][0]["main"].lower()
        
        # 날씨에 따라 카테고리 판단
        if "rain" in description or "drizzle" in description:
            category = "rainy"
            summary = "비가 오거나 흐림"
            note = "따뜻한 국물 음식에 가깝"
        elif "clear" in description or "sunny" in description:
            category = "clear"
            summary = "맑음"
            note = "무난한 점심 메뉴 중심 추천"
        elif temp > 25:
            category = "hot"
            summary = "덥고 습함"
            note = "실내 좌석과 가벼운 메뉴에 가깝"
        elif temp < 5:
            category = "cold"
            summary = "저저하고 건조함"
            note = "따뜻한 국물 음식에 가깝"
        else:
            category = "clear"
            summary = "맑음"
            note = "무난한 점심 메뉴 중심 추천"
        
        return {
            "category": category,
            "summary": summary,
            "temperature_c": temp,
            "note": note,
        }
    except Exception as e:
        print(f"Weather API 호출 실패: {e}")
        return _sample_weather()


class WeatherCache:
    """간단한 시간 기반 캐시"""
    def __init__(self, ttl: int = 3600):
        self.cache = None
        self.cache_time = 0
        self.ttl = ttl
    
    def get(self, func, *args, **kwargs):
        now = time.time()
        if self.cache is None or (now - self.cache_time) > self.ttl:
            self.cache = func(*args, **kwargs)
            self.cache_time = now
        return self.cache


_weather_cache = WeatherCache(ttl=CACHE_TTL)


def get_lunch_weather() -> dict:
    api_key = os.getenv("WEATHER_API_KEY", "").strip()
    
    # 좌표 (서울 을지로 기준)
    lat = 37.5642
    lon = 126.9988
    
    if api_key:
        return _weather_cache.get(_get_openweather, lat, lon, api_key)
    else:
        return _sample_weather()
