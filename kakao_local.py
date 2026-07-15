from __future__ import annotations

import os
import time
from typing import Any

import requests


DEFAULT_ADDRESS = os.getenv("LUNCH_BASE_ADDRESS", "서울특별시 중구 을지로 16")
DEFAULT_RADIUS = int(os.getenv("SEARCH_RADIUS_METERS", "1500"))
ADDRESS_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KEYWORD_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
CATEGORY_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/category.json"
FOOD_CATEGORY_CODE = "FD6"
REQUEST_TIMEOUT = 10
CACHE_TTL_SECONDS = 1800

_session = requests.Session()
_geocode_cache: dict[str, tuple[float, dict[str, str]]] = {}
_search_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}


class KakaoLocalError(Exception):
    pass


MENU_RULES = [
    {"match": ["국밥", "해장국", "순대국"], "menu": "국밥", "calories": 700},
    {"match": ["칼국수", "국수"], "menu": "칼국수", "calories": 600},
    {"match": ["김밥"], "menu": "김밥", "calories": 520},
    {"match": ["비빔밥"], "menu": "비빔밥", "calories": 650},
    {"match": ["돈까스"], "menu": "돈까스", "calories": 820},
    {"match": ["초밥", "스시", "참치"], "menu": "모둠초밥", "calories": 520},
    {"match": ["파스타"], "menu": "크림 파스타", "calories": 850},
    {"match": ["샐러드"], "menu": "치킨 샐러드", "calories": 350},
    {"match": ["카레"], "menu": "카레라이스", "calories": 740},
    {"match": ["제육"], "menu": "제육볶음", "calories": 820},
]

CATEGORY_DEFAULTS = [
    {"match": ["한식"], "menu": "백반", "calories": 700},
    {"match": ["중식"], "menu": "짜장면", "calories": 790},
    {"match": ["일식"], "menu": "가정식 정식", "calories": 720},
    {"match": ["양식"], "menu": "파스타", "calories": 820},
    {"match": ["분식"], "menu": "떡볶이", "calories": 520},
    {"match": ["샐러드"], "menu": "샐러드 볼", "calories": 320},
]

SMALL_GROUP_KEYWORDS = ("김밥", "분식", "샐러드", "카페", "버거", "죽")
LARGE_GROUP_KEYWORDS = ("고기", "구이", "뷔페", "전골", "족발", "보쌈", "호텔")


def has_kakao_api_key() -> bool:
    return bool(os.getenv("KAKAO_REST_API_KEY", "").strip())


def _api_headers() -> dict[str, str]:
    api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()
    if not api_key:
        raise KakaoLocalError("KAKAO_REST_API_KEY가 설정되어 있지 않습니다.")
    return {"Authorization": f"KakaoAK {api_key}"}


def _cache_get(cache: dict[str, tuple[float, Any]], key: str) -> Any | None:
    cached = cache.get(key)
    if not cached:
        return None
    timestamp, value = cached
    if time.time() - timestamp > CACHE_TTL_SECONDS:
        del cache[key]
        return None
    return value


def _cache_set(cache: dict[str, tuple[float, Any]], key: str, value: Any) -> None:
    cache[key] = (time.time(), value)


def infer_menu_and_calories(name: str, category: str) -> tuple[str, int]:
    combined = f"{name} {category}"
    for rule in MENU_RULES:
        if any(keyword in combined for keyword in rule["match"]):
            return rule["menu"], rule["calories"]
    for rule in CATEGORY_DEFAULTS:
        if any(keyword in category for keyword in rule["match"]):
            return rule["menu"], rule["calories"]
    return "대표 메뉴 정보 없음", 0


def infer_party_size_range(name: str, category: str) -> tuple[int, int]:
    combined = f"{name} {category}"
    if any(keyword in combined for keyword in LARGE_GROUP_KEYWORDS):
        return 2, 8
    if any(keyword in combined for keyword in SMALL_GROUP_KEYWORDS):
        return 1, 2
    return 1, 4


def _extract_dong(document: dict[str, Any], fallback: str) -> str:
    address = document.get("address") or {}
    road_address = document.get("road_address") or {}
    for source in (road_address, address):
        region_3depth_name = source.get("region_3depth_name")
        if region_3depth_name:
            return region_3depth_name
    address_name = document.get("address_name") or document.get("road_address_name") or fallback
    parts = address_name.split()
    return parts[2] if len(parts) >= 3 else address_name


def sample_restaurants() -> list[dict[str, Any]]:
    samples = [
        ("sample-1", "을지칼국수", "한식", "서울특별시 중구 을지로 16", 180),
        ("sample-2", "명동김밥", "분식", "서울특별시 중구 을지로 22", 320),
        ("sample-3", "광화문샐러드", "샐러드", "서울특별시 중구 세종대로 30", 480),
        ("sample-4", "시청제육식당", "한식", "서울특별시 중구 을지로 8", 540),
        ("sample-5", "을지초밥", "일식", "서울특별시 중구 무교로 14", 610),
        ("sample-6", "무교동국밥", "한식", "서울특별시 중구 무교로 22", 710),
        ("sample-7", "시청파스타", "양식", "서울특별시 중구 태평로 1가 23", 840),
        ("sample-8", "을지로불고기", "한식", "서울특별시 중구 을지로 29", 980),
    ]
    rows: list[dict[str, Any]] = []
    for external_id, name, category, address, distance_m in samples:
        main_menu, estimated_calories = infer_menu_and_calories(name, category)
        party_size_min, party_size_max = infer_party_size_range(name, category)
        rows.append(
            {
                "external_id": external_id,
                "kakao_place_id": "",
                "name": name,
                "category": category,
                "address": address,
                "road_address": address,
                "distance_m": distance_m,
                "phone": "",
                "place_url": "",
                "x": "",
                "y": "",
                "source": "sample",
                "main_menu": main_menu,
                "estimated_calories": estimated_calories,
                "indoor_score": 4,
                "spicy_score": 2,
                "soup_score": 2,
                "noodle_score": 2,
                "rice_score": 2,
                "price_level": "보통",
                "party_size_min": party_size_min,
                "party_size_max": party_size_max,
                "is_active": 1,
            }
        )
    return rows


def geocode_address(address: str) -> dict[str, str]:
    cached = _cache_get(_geocode_cache, address)
    if cached:
        return cached

    try:
        response = _session.get(
            ADDRESS_SEARCH_URL,
            headers=_api_headers(),
            params={"query": address},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        documents = response.json().get("documents", [])

        if not documents:
            keyword_response = _session.get(
                KEYWORD_SEARCH_URL,
                headers=_api_headers(),
                params={"query": address, "size": 1},
                timeout=REQUEST_TIMEOUT,
            )
            keyword_response.raise_for_status()
            documents = keyword_response.json().get("documents", [])
    except requests.RequestException as exc:
        raise KakaoLocalError(f"주소 검색 API 호출에 실패했습니다: {exc}") from exc

    if not documents:
        raise KakaoLocalError("기준 주소를 좌표로 변환하지 못했습니다.")

    first = documents[0]
    result = {
        "address_name": first.get("address_name") or first.get("road_address_name") or address,
        "dong_name": _extract_dong(first, address),
        "x": first.get("x", ""),
        "y": first.get("y", ""),
    }
    _cache_set(_geocode_cache, address, result)
    return result


def search_food_places_by_category(x: str, y: str, radius_m: int) -> list[dict[str, Any]]:
    cache_key = f"{x}:{y}:{radius_m}"
    cached = _cache_get(_search_cache, cache_key)
    if cached:
        return cached

    restaurants: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    page = 1
    max_pages = 3

    while page <= max_pages:
        try:
            response = _session.get(
                CATEGORY_SEARCH_URL,
                headers=_api_headers(),
                params={
                    "category_group_code": FOOD_CATEGORY_CODE,
                    "x": x,
                    "y": y,
                    "radius": radius_m,
                    "sort": "distance",
                    "page": page,
                    "size": 15,
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise KakaoLocalError(f"카테고리 검색 API 호출에 실패했습니다: {exc}") from exc

        data = response.json()
        for item in data.get("documents", []):
            place_id = str(item.get("id") or "").strip()
            if not place_id or place_id in seen_ids:
                continue
            seen_ids.add(place_id)

            category = item.get("category_name") or item.get("category_group_name") or "음식점"
            name = item.get("place_name", "")
            main_menu, estimated_calories = infer_menu_and_calories(name, category)
            party_size_min, party_size_max = infer_party_size_range(name, category)
            restaurants.append(
                {
                    "external_id": f"kakao-{place_id}",
                    "kakao_place_id": place_id,
                    "name": name,
                    "category": category,
                    "address": item.get("address_name", ""),
                    "road_address": item.get("road_address_name", ""),
                    "phone": item.get("phone", ""),
                    "place_url": item.get("place_url", ""),
                    "x": item.get("x", ""),
                    "y": item.get("y", ""),
                    "distance_m": int(item.get("distance", 0)),
                    "source": "kakao",
                    "main_menu": main_menu,
                    "estimated_calories": estimated_calories,
                    "indoor_score": 4,
                    "spicy_score": 2,
                    "soup_score": 2,
                    "noodle_score": 2,
                    "rice_score": 2,
                    "price_level": "보통",
                    "party_size_min": party_size_min,
                    "party_size_max": party_size_max,
                    "is_active": 1,
                }
            )

        if data.get("meta", {}).get("is_end", True):
            break
        page += 1

    _cache_set(_search_cache, cache_key, restaurants)
    return restaurants


def fetch_nearby_restaurants(
    address: str | None = None,
    radius_m: int | None = None,
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    if not has_kakao_api_key():
        raise KakaoLocalError("KAKAO_REST_API_KEY가 설정되어 있지 않습니다.")

    address = address or os.getenv("LUNCH_BASE_ADDRESS", DEFAULT_ADDRESS)
    radius = radius_m or int(os.getenv("SEARCH_RADIUS_METERS", str(DEFAULT_RADIUS)))
    location = geocode_address(address)
    restaurants = search_food_places_by_category(location["x"], location["y"], radius)
    if not restaurants:
        raise KakaoLocalError("카카오 API로 조회된 식당이 없습니다.")
    return location, restaurants
