import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def sample_weather() -> dict:
    return {
        "category": "clear",
        "summary": "맑음",
        "temperature_c": 18,
        "note": "무난한 날씨라 가볍게 고르기 좋은 점심입니다.",
    }


def _classify_weather(code: int, temperature_c: int) -> tuple[str, str, str]:
    rainy_codes = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
    if code in rainy_codes:
        return "rainy", "비", "실내 좌석과 국물 메뉴가 잘 어울리는 날씨입니다."
    if temperature_c >= 28:
        return "hot", "덥고 습함", "시원한 메뉴나 실내 식당이 잘 어울립니다."
    if temperature_c <= 5:
        return "cold", "쌀쌀함", "따뜻한 국물과 든든한 식사가 잘 어울립니다."
    return "clear", "맑음", "무난한 날씨라 가볍게 고르기 좋은 점심입니다."


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
        temperature_c = round(float(current.get("temperature_2m", 18)))
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
