import os
import time
from typing import Any

import requests


DEFAULT_ADDRESS = "서울특별시 중구 을지로 16"
DEFAULT_RADIUS = int(os.getenv("SEARCH_RADIUS_METERS", "1500"))
ADDRESS_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"
CATEGORY_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/category.json"
FOOD_CATEGORY_CODE = "FD6"
REQUEST_TIMEOUT = 10
CACHE_TTL_SECONDS = 1800
_session = requests.Session()
_geocode_cache: dict[str, tuple[float, dict[str, str]]] = {}
_search_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}


class KakaoLocalError(Exception):
    pass


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


def _sample_restaurants() -> list[dict[str, Any]]:
    return [
        {
            "external_id": "sample-1",
            "kakao_place_id": None,
            "name": "을지로국밥",
            "category": "한식",
            "address": "서울 중구 을지로 일대",
            "road_address": "서울 중구 을지로 일대",
            "distance_m": 250,
            "phone": "",
            "place_url": "",
            "x": "",
            "y": "",
            "source": "sample",
            "indoor_score": 5,
            "spicy_score": 2,
            "soup_score": 5,
            "noodle_score": 1,
            "rice_score": 4,
            "price_level": "보통",
            "is_active": 1,
        },
        {
            "external_id": "sample-2",
            "kakao_place_id": None,
            "name": "명동칼국수",
            "category": "면요리",
            "address": "서울 중구 명동 일대",
            "road_address": "서울 중구 명동 일대",
            "distance_m": 780,
            "phone": "",
            "place_url": "",
            "x": "",
            "y": "",
            "source": "sample",
            "indoor_score": 4,
            "spicy_score": 1,
            "soup_score": 4,
            "noodle_score": 5,
            "rice_score": 1,
            "price_level": "보통",
            "is_active": 1,
        },
        {
            "external_id": "sample-3",
            "kakao_place_id": None,
            "name": "충무로돈까스",
            "category": "일식",
            "address": "서울 중구 충무로 일대",
            "road_address": "서울 중구 충무로 일대",
            "distance_m": 920,
            "phone": "",
            "place_url": "",
            "x": "",
            "y": "",
            "source": "sample",
            "indoor_score": 4,
            "spicy_score": 1,
            "soup_score": 1,
            "noodle_score": 1,
            "rice_score": 3,
            "price_level": "보통",
            "is_active": 1,
        },
        {
            "external_id": "sample-4",
            "kakao_place_id": None,
            "name": "을지로제육식당",
            "category": "한식",
            "address": "서울 중구 을지로 일대",
            "road_address": "서울 중구 을지로 일대",
            "distance_m": 430,
            "phone": "",
            "place_url": "",
            "x": "",
            "y": "",
            "source": "sample",
            "indoor_score": 4,
            "spicy_score": 5,
            "soup_score": 2,
            "noodle_score": 1,
            "rice_score": 5,
            "price_level": "보통",
            "is_active": 1,
        },
        {
            "external_id": "sample-5",
            "kakao_place_id": None,
            "name": "시청샐러드랩",
            "category": "샐러드",
            "address": "서울 중구 시청 일대",
            "road_address": "서울 중구 시청 일대",
            "distance_m": 1380,
            "phone": "",
            "place_url": "",
            "x": "",
            "y": "",
            "source": "sample",
            "indoor_score": 4,
            "spicy_score": 1,
            "soup_score": 1,
            "noodle_score": 1,
            "rice_score": 1,
            "price_level": "약간높음",
            "is_active": 1,
        },
        {
            "external_id": "sample-6",
            "kakao_place_id": None,
            "name": "을지로짬뽕",
            "category": "중식",
            "address": "서울 중구 을지로 일대",
            "road_address": "서울 중구 을지로 일대",
            "distance_m": 640,
            "phone": "",
            "place_url": "",
            "x": "",
            "y": "",
            "source": "sample",
            "indoor_score": 5,
            "spicy_score": 4,
            "soup_score": 4,
            "noodle_score": 4,
            "rice_score": 2,
            "price_level": "보통",
            "is_active": 1,
        },
        {
            "external_id": "sample-7",
            "kakao_place_id": None,
            "name": "회현비빔밥",
            "category": "한식",
            "address": "서울 중구 회현 일대",
            "road_address": "서울 중구 회현 일대",
            "distance_m": 1490,
            "phone": "",
            "place_url": "",
            "x": "",
            "y": "",
            "source": "sample",
            "indoor_score": 3,
            "spicy_score": 2,
            "soup_score": 1,
            "noodle_score": 1,
            "rice_score": 5,
            "price_level": "보통",
            "is_active": 1,
        },
        {
            "external_id": "sample-8",
            "kakao_place_id": None,
            "name": "을지로파스타",
            "category": "양식",
            "address": "서울 중구 을지로 일대",
            "road_address": "서울 중구 을지로 일대",
            "distance_m": 580,
            "phone": "",
            "place_url": "",
            "x": "",
            "y": "",
            "source": "sample",
            "indoor_score": 5,
            "spicy_score": 1,
            "soup_score": 1,
            "noodle_score": 3,
            "rice_score": 1,
            "price_level": "약간높음",
            "is_active": 1,
        },
    ]


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
        raise KakaoLocalError("기준 주소를 좌표로 변환하지 못했습니다.")

    result = {
        "address_name": documents[0].get("address_name", address),
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
            restaurants.append(
                {
                    "external_id": f"kakao-{place_id}",
                    "kakao_place_id": place_id,
                    "name": item.get("place_name", ""),
                    "category": item.get("category_name") or item.get("category_group_name") or "음식점",
                    "address": item.get("address_name", ""),
                    "road_address": item.get("road_address_name", ""),
                    "phone": item.get("phone", ""),
                    "place_url": item.get("place_url", ""),
                    "x": item.get("x", ""),
                    "y": item.get("y", ""),
                    "distance_m": int(item.get("distance", 0)),
                    "source": "kakao",
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
