from __future__ import annotations

import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def sample_weather() -> dict:
    return {
        "category": "clear",
        "summary": "맑음",
        "temperature_c": 24,
        "note": "무난한 날씨라 이동이 편한 점심 코스를 추천합니다.",
    }


def _classify_weather(code: int, temperature_c: int) -> tuple[str, str, str]:
    rainy_codes = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
    cloudy_codes = {1, 2, 3, 45, 48}

    if code in rainy_codes:
        return "rainy", "비", "비가 와서 실내 좌석과 가까운 거리를 우선 반영했습니다."
    if code in cloudy_codes:
        return "cloudy", "흐림", "흐린 날이라 이동과 식사 균형이 좋은 식당을 골랐습니다."
    if temperature_c >= 28:
        return "hot", "덥고 습함", "더운 날씨라 시원한 메뉴와 실내 좌석에 가점을 줬습니다."
    if temperature_c <= 5:
        return "cold", "쌀쌀함", "추운 날씨라 따뜻한 메뉴에 가점을 줬습니다."
    return "clear", "맑음", "무난한 날씨라 평소 점심으로 가기 편한 곳을 골랐습니다."


def get_lunch_weather(latitude: float | None = None, longitude: float | None = None) -> dict:
    if latitude is None or longitude is None:
        return sample_weather()

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,weather_code",
                "timezone": "Asia/Seoul",
            },
            timeout=5,
        )
        response.raise_for_status()
        current = response.json().get("current", {})
        temperature_c = round(float(current.get("temperature_2m", 24)))
        weather_code = int(current.get("weather_code", 0))
        category, summary, note = _classify_weather(weather_code, temperature_c)
        return {
            "category": category,
            "summary": summary,
            "temperature_c": temperature_c,
            "note": note,
        }
    except Exception:
        return sample_weather()
