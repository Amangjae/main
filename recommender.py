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
        return score, "\ube44 \uc624\ub294 \ub0a0\uc774\ub77c \uc2e4\ub0b4 \uc88c\uc11d\uacfc \uad6d\ubb3c \uba54\ub274\uc5d0 \uac00\uc810\uc744 \ubc18\uc601\ud588\uc2b5\ub2c8\ub2e4"
    if category == "hot":
        score += restaurant["noodle_score"] * 0.7
        score += restaurant["indoor_score"] * 0.5
        return score, "\ub354\uc6b4 \ub0a0\uc528\ub77c \uc2dc\uc6d0\ud55c \uba74\ub958\uc640 \uc2e4\ub0b4 \uc120\ud638\ub97c \ubc18\uc601\ud588\uc2b5\ub2c8\ub2e4"
    if category == "cold":
        score += restaurant["soup_score"] * 0.8
        score += restaurant["rice_score"] * 0.4
        return score, "\ucd94\uc6b4 \ub0a0\uc528\ub77c \ub530\ub73b\ud55c \uad6d\ubb3c\uacfc \ub4e0\ub4e0\ud55c \uc2dd\uc0ac\ub97c \ubc18\uc601\ud588\uc2b5\ub2c8\ub2e4"

    score += restaurant["rice_score"] * 0.4
    return score, "\ubb34\ub09c\ud55c \ub0a0\uc528\ub77c \ub300\uc911\uc801\uc778 \uc810\uc2ec \uba54\ub274 \uc120\ud638\ub97c \ubc18\uc601\ud588\uc2b5\ub2c8\ub2e4"



def _history_score(restaurant: dict) -> tuple[float, str]:
    total_visits = restaurant["total_visits"] or 0
    days = _days_since(restaurant["last_visited_on"])

    if total_visits == 0:
        return 1.0, "\uc544\uc9c1 \ubc29\ubb38 \uc774\ub825\uc774 \uc5c6\uc5b4 \uc0c8\ub85c\uc6b4 \uc120\ud0dd\uc9c0\ub85c \ubd84\ub958\ud588\uc2b5\ub2c8\ub2e4"

    score = min(total_visits * 0.4, 2.0)
    if days <= 7:
        return score - 2.5, "\ucd5c\uadfc 7\uc77c \ub0b4 \ubc29\ubb38 \uc774\ub825\uc774 \uc788\uc5b4 \uc911\ubcf5 \ubc29\ubb38\uc744 \uc904\uc774\ub3c4\ub85d \uac10\uc810\ud588\uc2b5\ub2c8\ub2e4"
    if days <= 14:
        return score - 1.0, "2\uc8fc \ub0b4 \ubc29\ubb38 \uc774\ub825\uc774 \uc788\uc5b4 \uc57d\ud55c \uac10\uc810\uc744 \ubc18\uc601\ud588\uc2b5\ub2c8\ub2e4"

    score += min(days / 10, 3.0)
    return score, "\ud55c\ub3d9\uc548 \uc548 \uac00\ubcf8 \uc775\uc219\ud55c \uc2dd\ub2f9\uc774\ub77c \uc7ac\ubc29\ubb38 \ud6c4\ubcf4\ub85c \uc62c\ub838\uc2b5\ub2c8\ub2e4"



def _distance_score(distance_m: int) -> float:
    return max(0.0, 2.0 - (distance_m / 1000))



def _build_reason(restaurant: dict, weather_reason: str, history_reason: str) -> str:
    parts = [
        weather_reason,
        history_reason,
        f"\uae30\uc900 \uc8fc\uc18c\uc5d0\uc11c \uc57d {restaurant['distance_m']}m \uac70\ub9ac\uc785\ub2c8\ub2e4",
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
        item["recommendation_type"] = "\uc7ac\ubc29\ubb38 \ucd94\ucc9c"
        selected.append(item)

    for item in unvisited_sorted[:1]:
        item["recommendation_type"] = "\uc0c8\ub85c\uc6b4 \ub3c4\uc804"
        selected.append(item)

    if len(selected) < 4:
        remaining = [*visited_sorted[3:], *unvisited_sorted[1:]]
        for item in remaining:
            if item not in selected:
                item["recommendation_type"] = item.get("recommendation_type", "\ucd94\uac00 \ud6c4\ubcf4")
                selected.append(item)
            if len(selected) == 4:
                break

    return selected[:4]