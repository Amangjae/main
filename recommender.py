from __future__ import annotations

from datetime import date, datetime


def _days_since(last_visited_on: str | None) -> int:
    if not last_visited_on:
        return 999
    last_date = datetime.strptime(last_visited_on, "%Y-%m-%d").date()
    return (date.today() - last_date).days


def _weather_bonus(restaurant: dict, weather: dict) -> tuple[float, str]:
    category = weather.get("category", "clear")
    score = 0.0

    if category == "rainy":
        score += restaurant.get("indoor_score", 3) * 0.8
        score += restaurant.get("soup_score", 2) * 0.6
        return score, "비 오는 날이라 실내 좌석과 국물 메뉴를 더 반영했습니다."
    if category == "hot":
        score += restaurant.get("noodle_score", 2) * 0.7
        score += restaurant.get("indoor_score", 3) * 0.5
        return score, "더운 날씨라 시원한 면류와 실내 식당을 더 반영했습니다."
    if category == "cold":
        score += restaurant.get("soup_score", 2) * 0.8
        score += restaurant.get("rice_score", 2) * 0.4
        return score, "쌀쌀한 날씨라 따뜻한 국물과 든든한 식사를 더 반영했습니다."

    score += restaurant.get("rice_score", 2) * 0.4
    return score, "무난한 날씨라 대중적인 점심 메뉴를 반영했습니다."


def _history_score(total_visits: int, last_visited_on: str | None) -> tuple[float, str]:
    days = _days_since(last_visited_on)

    if total_visits == 0:
        return 1.0, "아직 방문 기록이 없어 새로운 후보로 분류했습니다."

    score = min(total_visits * 0.4, 2.0)
    if days <= 7:
        return score - 2.5, "최근 7일 이내 방문 기록이 있어 중복 방문 점수를 낮췄습니다."
    if days <= 14:
        return score - 1.0, "최근 2주 이내 방문 기록이 있어 소폭 감점했습니다."

    score += min(days / 10, 3.0)
    return score, "한동안 가지 않았던 식당이라 재방문 후보로 올렸습니다."


def _distance_score(distance_m: int) -> float:
    return max(0.0, 2.0 - (distance_m / 1000))


def _visit_index(visits: list[dict]) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for visit in visits:
        key = visit.get("restaurant_key") or visit.get("restaurant_name") or ""
        if not key:
            continue
        item = index.setdefault(key, {"total_visits": 0, "last_visited_on": None})
        item["total_visits"] += int(visit.get("visit_count") or 1)
        visited_on = visit.get("visited_on")
        if visited_on and (item["last_visited_on"] is None or visited_on > item["last_visited_on"]):
            item["last_visited_on"] = visited_on
    return index


def recommend_lunches(restaurants: list[dict], visits: list[dict], weather: dict, limit: int = 4) -> list[dict]:
    visit_index = _visit_index(visits)
    visited = []
    unvisited = []

    for restaurant in restaurants:
        restaurant_key = restaurant.get("external_id") or restaurant.get("kakao_place_id") or restaurant.get("name")
        history = visit_index.get(restaurant_key) or visit_index.get(restaurant.get("name", ""), {})
        total_visits = int(history.get("total_visits") or 0)
        last_visited_on = history.get("last_visited_on")

        weather_score, weather_reason = _weather_bonus(restaurant, weather)
        history_score, history_reason = _history_score(total_visits, last_visited_on)
        distance_score = _distance_score(int(restaurant.get("distance_m", 0)))
        total_score = weather_score + history_score + distance_score

        item = {
            "id": restaurant_key,
            "name": restaurant.get("name", ""),
            "category": restaurant.get("category", ""),
            "distance_m": int(restaurant.get("distance_m", 0)),
            "price_level": restaurant.get("price_level", "보통"),
            "main_menu": restaurant.get("main_menu") or "대표 메뉴 추정 불가",
            "estimated_calories": int(restaurant.get("estimated_calories") or 0),
            "score": round(total_score, 2),
            "reason": f"{weather_reason} / {history_reason} / 기준 주소에서 약 {restaurant.get('distance_m', 0)}m 거리입니다.",
            "total_visits": total_visits,
        }

        if total_visits > 0:
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

    if len(selected) < limit:
        remaining = [*visited_sorted[3:], *unvisited_sorted[1:]]
        for item in remaining:
            if item not in selected:
                item["recommendation_type"] = item.get("recommendation_type", "추가 후보")
                selected.append(item)
            if len(selected) == limit:
                break

    return selected[:limit]
