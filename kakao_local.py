import os
import time
from typing import Any

import requests


DEFAULT_ADDRESS = "서울특별시 중구 을지로 16"
DEFAULT_RADIUS = int(os.getenv("SEARCH_RADIUS_METERS", "1500"))
ADDRESS_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"
CATEGORY_KEYWORD_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
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
    {"match": ["국밥", "순대국", "해장국"], "menu": "국밥", "calories": 700},
    {"match": ["칼국수"], "menu": "칼국수", "calories": 600},
    {"match": ["짬뽕"], "menu": "짬뽕", "calories": 800},
    {"match": ["파스타"], "menu": "크림 파스타", "calories": 850},
    {"match": ["돈까스"], "menu": "돈까스", "calories": 900},
    {"match": ["제육"], "menu": "제육볶음", "calories": 820},
    {"match": ["비빔밥"], "menu": "비빔밥", "calories": 650},
    {"match": ["샐러드"], "menu": "닭가슴살 샐러드", "calories": 350},
    {"match": ["초밥", "스시"], "menu": "모둠초밥", "calories": 520},
    {"match": ["쌀국수"], "menu": "소고기 쌀국수", "calories": 480},
]

CATEGORY_DEFAULTS = [
    {"match": ["한식"], "menu": "백반", "calories": 700},
    {"match": ["중식"], "menu": "짜장면", "calories": 790},
    {"match": ["일식"], "menu": "돈부리", "calories": 720},
    {"match": ["양식"], "menu": "파스타", "calories": 820},
    {"match": ["면요리"], "menu": "잔치국수", "calories": 520},
    {"match": ["샐러드"], "menu": "샐러드볼", "calories": 320},
]


def has_kakao_api_key() -> bool:
    return bool(os.getenv("KAKAO_REST_API_KEY", "").strip())


def _api_headers() -> dict[str, str]:
    api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()
    if not api_key:
        raise KakaoLocalError("KAKAO_REST_API_KEY가 설정되어 있지 않습니다.")
    return {"Authorization": f"KakaoAK {api_key}"}


def _cache_get(cache: dict, key: str):
    cached = cache.get(key)
    if not cached:
        return None
    timestamp, value = cached
    if time.time() - timestamp > CACHE_TTL_SECONDS:
        del cache[key]
        return None
    return value


def _cache_set(cache: dict, key: str, value) -> None:
    cache[key] = (time.time(), value)


def infer_menu_and_calories(name: str, category: str) -> tuple[str, int]:
    combined = f"{name} {category}"
    for rule in MENU_RULES:
        if any(keyword in combined for keyword in rule["match"]):
            return rule["menu"], rule["calories"]
    for rule in CATEGORY_DEFAULTS:
        if any(keyword in category for keyword in rule["match"]):
            return rule["menu"], rule["calories"]
    return "대표 메뉴 추정 불가", 0


def _sample_restaurants() -> list[dict[str, Any]]:
    samples = [
        ("sample-1", "을지로국밥", "한식", "서울 중구 을지로 일대", 250),
        ("sample-2", "명동칼국수", "면요리", "서울 중구 명동 일대", 780),
        ("sample-3", "충무로돈까스", "일식", "서울 중구 충무로 일대", 920),
        ("sample-4", "을지로제육식당", "한식", "서울 중구 을지로 일대", 430),
        ("sample-5", "시청샐러드랩", "샐러드", "서울 중구 시청 일대", 1380),
        ("sample-6", "을지로짬뽕", "중식", "서울 중구 을지로 일대", 640),
        ("sample-7", "회현비빔밥", "한식", "서울 중구 회현 일대", 1490),
        ("sample-8", "을지로파스타", "양식", "서울 중구 을지로 일대", 580),
    ]

    rows = []
    for external_id, name, category, address, distance_m in samples:
        main_menu, estimated_calories = infer_menu_and_calories(name, category)
        rows.append(
            {
                "external_id": external_id,
                "kakao_place_id": None,
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
                "is_active": 1,
            }
        )
    return rows


def search_nearby_restaurants(address: str | None = None, radius_m: int = DEFAULT_RADIUS, keyword: str = "맛집") -> list[dict[str, Any]]:
    return _sample_restaurants()


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
    except requests.RequestException as exc:
        raise KakaoLocalError(f"주소 변환 API 호출에 실패했습니다: {exc}") from exc

    documents = response.json().get("documents", [])
    if not documents:
        try:
            fallback_response = _session.get(
                CATEGORY_KEYWORD_URL,
                headers=_api_headers(),
                params={"query": address, "size": 1},
                timeout=REQUEST_TIMEOUT,
            )
            fallback_response.raise_for_status()
            documents = fallback_response.json().get("documents", [])
        except requests.RequestException as exc:
            raise KakaoLocalError(f"주소 키워드 검색 API 호출에 실패했습니다: {exc}") from exc

    if not documents:
        raise KakaoLocalError("기준 주소를 좌표로 변환하지 못했습니다.")

    result = {
        "address_name": documents[0].get("address_name")
        or documents[0].get("road_address_name")
        or address,
        "x": documents[0].get("x", ""),
        "y": documents[0].get("y", ""),
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
            raise KakaoLocalError(f"음식점 검색 API 호출에 실패했습니다: {exc}") from exc

        data = response.json()
        for item in data.get("documents", []):
            place_id = item.get("id")
            if not place_id or place_id in seen_ids:
                continue
            seen_ids.add(place_id)
            category = item.get("category_name") or item.get("category_group_name") or "음식점"
            name = item.get("place_name", "")
            main_menu, estimated_calories = infer_menu_and_calories(name, category)
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
                    "is_active": 1,
                }
            )

        if data.get("meta", {}).get("is_end", True):
            break
        page += 1

    _cache_set(_search_cache, cache_key, restaurants)
    return restaurants


def fetch_nearby_restaurants(address: str | None = None, radius_m: int | None = None) -> list[dict[str, Any]]:
    address = address or os.getenv("LUNCH_BASE_ADDRESS", DEFAULT_ADDRESS)
    radius = radius_m or int(os.getenv("SEARCH_RADIUS_METERS", str(DEFAULT_RADIUS)))
    coordinates = geocode_address(address)
    restaurants = search_food_places_by_category(coordinates["x"], coordinates["y"], radius)
    if not restaurants:
        raise KakaoLocalError("카카오 API로 조회된 식당이 없습니다.")
    return restaurants
