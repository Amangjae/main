from __future__ import annotations

from datetime import date, datetime
from typing import Any


RECENT_EXCLUDE_DAYS = 7


def _parse_visit_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value[:10], fmt).date()
        except ValueError:
            continue
    return None


def _days_since(value: str | None) -> int:
    parsed = _parse_visit_date(value)
    if parsed is None:
        return 999
    return (date.today() - parsed).days


def _weather_bonus(restaurant: dict[str, Any], weather: dict[str, Any]) -> tuple[float, str]:
    category = str(weather.get("category", "clear"))
    score = 0.0

    if category == "rainy":
        score += float(restaurant.get("indoor_score", 3)) * 0.9
        score += float(restaurant.get("soup_score", 2)) * 0.6
        return score, "비 오는 날이라 실내 식사와 국물 메뉴에 가점을 줬습니다."

    if category == "hot":
        score += float(restaurant.get("indoor_score", 3)) * 0.7
        score += float(restaurant.get("noodle_score", 2)) * 0.5
        return score, "더운 날이라 시원하게 먹기 쉬운 메뉴와 실내 좌석을 반영했습니다."

    if category == "cold":
        score += float(restaurant.get("soup_score", 2)) * 0.9
        score += float(restaurant.get("rice_score", 2)) * 0.4
        return score, "추운 날이라 든든한 식사와 국물 메뉴에 가점을 줬습니다."

    score += float(restaurant.get("rice_score", 2)) * 0.4
    return score, "무난한 날씨라 평소 점심으로 먹기 편한 메뉴를 반영했습니다."


def _distance_score(distance_m: int) -> float:
    return max(0.0, 2.2 - (distance_m / 900))


def _party_size_bonus(restaurant: dict[str, Any], party_size: int) -> tuple[float, str]:
    minimum = int(restaurant.get("party_size_min") or 1)
    maximum = int(restaurant.get("party_size_max") or 4)

    if minimum <= party_size <= maximum:
        return 1.6, f"{party_size}명 식사에 비교적 잘 맞는 곳입니다."

    if party_size < minimum:
        return -1.4, f"{party_size}명이 가기엔 조금 큰 매장으로 판단했습니다."

    return -2.2, f"{party_size}명이 가기엔 좌석 여유가 부족할 수 있습니다."


def _build_visit_index(visits: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}

    for visit in visits:
        decision = str(visit.get("decision", "selected")).strip() or "selected"
        if decision != "selected":
            continue

        key = (
            str(visit.get("restaurant_id") or "").strip()
            or str(visit.get("restaurant_key") or "").strip()
            or str(visit.get("restaurant_name") or "").strip()
        )
        if not key:
            continue

        item = index.setdefault(
            key,
            {
                "restaurant_name": str(visit.get("restaurant_name") or "").strip(),
                "total_visits": 0,
                "last_selected_on": "",
            },
        )
        item["total_visits"] += 1

        visited_on = str(
            visit.get("date")
            or visit.get("visited_on")
            or visit.get("selected_at")
            or ""
        ).strip()
        if visited_on and visited_on > item["last_selected_on"]:
            item["last_selected_on"] = visited_on

    return index


def _history_score(total_visits: int, last_selected_on: str | None) -> tuple[float, str]:
    if total_visits <= 0:
        return 1.2, "아직 선택 기록이 적어서 새로운 후보로 올렸습니다."

    days = _days_since(last_selected_on)
    if days <= RECENT_EXCLUDE_DAYS:
        return -5.0, "최근 1주일 안에 선택된 식당이라 우선 제외 대상입니다."

    score = min(total_visits * 0.35, 1.8)
    score += min(days / 12, 2.8)
    return score, f"최근 방문 후 {days}일 지나 다시 가도 부담이 적습니다."


def _is_recently_selected(last_selected_on: str | None) -> bool:
    return _days_since(last_selected_on) <= RECENT_EXCLUDE_DAYS


def recommend_lunches(
    restaurants: list[dict[str, Any]],
    visits: list[dict[str, Any]],
    weather: dict[str, Any],
    limit: int = 4,
    party_size: int = 2,
) -> list[dict[str, Any]]:
    visit_index = _build_visit_index(visits)
    visited_candidates: list[dict[str, Any]] = []
    new_candidates: list[dict[str, Any]] = []

    for restaurant in restaurants:
        restaurant_id = (
            str(restaurant.get("external_id") or "").strip()
            or str(restaurant.get("kakao_place_id") or "").strip()
            or str(restaurant.get("name") or "").strip()
        )
        if not restaurant_id:
            continue

        history = visit_index.get(restaurant_id) or visit_index.get(
            str(restaurant.get("name") or "").strip(),
            {},
        )
        total_visits = int(history.get("total_visits") or 0)
        last_selected_on = str(history.get("last_selected_on") or "").strip()

        if total_visits > 0 and _is_recently_selected(last_selected_on):
            continue

        weather_score, weather_reason = _weather_bonus(restaurant, weather)
        history_score, history_reason = _history_score(total_visits, last_selected_on)
        party_score, party_reason = _party_size_bonus(restaurant, party_size)
        distance_m = int(restaurant.get("distance_m") or 0)
        distance_score = _distance_score(distance_m)
        total_score = weather_score + history_score + party_score + distance_score

        item = {
            "id": restaurant_id,
            "name": restaurant.get("name", ""),
            "category": restaurant.get("category", ""),
            "distance_m": distance_m,
            "price_level": restaurant.get("price_level", "보통"),
            "main_menu": restaurant.get("main_menu") or "대표 메뉴 정보 없음",
            "estimated_calories": int(restaurant.get("estimated_calories") or 0),
            "party_size_min": int(restaurant.get("party_size_min") or 1),
            "party_size_max": int(restaurant.get("party_size_max") or 4),
            "place_url": restaurant.get("place_url", ""),
            "address": restaurant.get("road_address") or restaurant.get("address") or "",
            "score": round(total_score, 2),
            "reason": " / ".join(
                [
                    weather_reason,
                    history_reason,
                    party_reason,
                    f"기준 주소에서 약 {distance_m}m 거리입니다.",
                ]
            ),
            "total_visits": total_visits,
        }

        if total_visits > 0:
            visited_candidates.append(item)
        else:
            new_candidates.append(item)

    visited_sorted = sorted(
        visited_candidates,
        key=lambda item: (-item["score"], item["distance_m"], item["name"]),
    )
    new_sorted = sorted(
        new_candidates,
        key=lambda item: (-item["score"], item["distance_m"], item["name"]),
    )

    selected: list[dict[str, Any]] = []

    for item in visited_sorted[:3]:
        item["recommendation_type"] = "다시 가도 좋은 곳"
        selected.append(item)

    for item in new_sorted[:1]:
        item["recommendation_type"] = "새로운 후보"
        selected.append(item)

    if len(selected) < limit:
        remaining = [*visited_sorted[3:], *new_sorted[1:]]
        for item in remaining:
            if item in selected:
                continue
            item["recommendation_type"] = item.get("recommendation_type", "추가 후보")
            selected.append(item)
            if len(selected) >= limit:
                break

    return selected[:limit]
