from __future__ import annotations

from datetime import date, datetime

from db import get_restaurants_with_history
from weather import get_lunch_weather


def _days_since(last_visited_on: str | None) -> int:
    if not last_visited_on:
        return 999
    last_date = datetime.strptime(last_visited_on, "%Y-%m-%d").date()
    return (date.today() - last_date).days


def _weather_bonus(restaurant: dict, weather: dict) -> tuple[float, str]:
    category = weather["category"]
    score = 0.0

    if category == "rainy":
        score += restaurant["indoor_score"] * 0.8
        score += restaurant["soup_score"] * 0.6
        return score, "비 오는 날이라 실내 좌석과 국물 메뉴에 가점을 반영했습니다"
    if category == "hot":
        score += restaurant["noodle_score"] * 0.7
        score += restaurant["indoor_score"] * 0.5
        return score, "더운 날씨라 시원한 면류와 실내 선호를 반영했습니다"
    if category == "cold":
        score += restaurant["soup_score"] * 0.8
        score += restaurant["rice_score"] * 0.4
        return score, "추운 날씨라 따뜻한 국물과 든든한 식사를 반영했습니다"

    score += restaurant["rice_score"] * 0.4
    return score, "무난한 날씨라 대중적인 점심 메뉴 선호를 반영했습니다"


def _history_score(restaurant: dict) -> tuple[float, str]:
    total_visits = restaurant["total_visits"] or 0
    days = _days_since(restaurant["last_visited_on"])

    if total_visits == 0:
        return 1.0, "아직 방문 이력이 없어 새로운 선택지로 분류했습니다"

    score = min(total_visits * 0.4, 2.0)
    if days <= 7:
        return score - 2.5, "최근 7일 내 방문 이력이 있어 중복 방문을 줄이도록 감점했습니다"
    if days <= 14:
        return score - 1.0, "2주 내 방문 이력이 있어 약한 감점을 반영했습니다"

    score += min(days / 10, 3.0)
    return score, "한동안 안 가본 익숙한 식당이라 재방문 후보로 올렸습니다"


def _distance_score(distance_m: int) -> float:
    return max(0.0, 2.0 - (distance_m / 1000))


def _build_reason(restaurant: dict, weather_reason: str, history_reason: str) -> str:
    parts = [
        weather_reason,
        history_reason,
        f"기준 주소에서 약 {restaurant['distance_m']}m 거리입니다",
    ]
    return " / ".join(parts)


def recommend_lunches() -> list[dict]:
    weather = get_lunch_weather()
    restaurants = get_restaurants_with_history()

    visited = []
    unvisited = []

    for restaurant in restaurants:
        weather_score, weather_reason = _weather_bonus(restaurant, weather)
        history_score, history_reason = _history_score(restaurant)
        distance_score = _distance_score(restaurant["distance_m"])
        total_score = weather_score + history_score + distance_score

        item = {
            "id": restaurant["id"],
            "name": restaurant["name"],
            "category": restaurant["category"],
            "distance_m": restaurant["distance_m"],
            "price_level": restaurant["price_level"],
            "main_menu": restaurant.get("main_menu") or "대표 메뉴 추정 불가",
            "estimated_calories": restaurant.get("estimated_calories") or 0,
            "score": round(total_score, 2),
            "reason": _build_reason(restaurant, weather_reason, history_reason),
        }

        if (restaurant["total_visits"] or 0) > 0:
            visited.append(item)
        else:
            unvisited.append(item)

    visited_sorted = sorted(visited, key=lambda x: (-x["score"], x["distance_m"], x["name"]))
    unvisited_sorted = sorted(unvisited, key=lambda x: (-x["score"], x["distance_m"], x["name"]))

    selected = []
    for item in visited_sorted[:3]:
        item["recommendation_type"] = "재방문 추천"
        selected.append(item)

    for item in unvisited_sorted[:1]:
        item["recommendation_type"] = "새로운 도전"
        selected.append(item)

    if len(selected) < 4:
        remaining = [*visited_sorted[3:], *unvisited_sorted[1:]]
        for item in remaining:
            if item not in selected:
                item["recommendation_type"] = item.get("recommendation_type", "추가 후보")
                selected.append(item)
            if len(selected) == 4:
                break

    return selected[:4]
