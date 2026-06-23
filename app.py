import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from db import (
    add_visit,
    get_recent_visits,
    get_restaurant_count,
    init_db,
    list_restaurants,
    save_kakao_restaurants,
)
from kakao_local import KakaoLocalError, fetch_nearby_restaurants, has_kakao_api_key
from recommender import recommend_lunches
from seed import seed_data
from weather import get_lunch_weather


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TITLE = "회사 점심 추천기"
BASE_ADDRESS = os.getenv("LUNCH_BASE_ADDRESS", "서울특별시 중구 을지로 16")
SEARCH_RADIUS_METERS = int(os.getenv("SEARCH_RADIUS_METERS", "1500"))
PORT = int(os.getenv("PORT", "8000"))


class TTLCache:
    def __init__(self) -> None:
        self._data: dict[str, tuple[float, Any]] = {}

    def get_or_set(self, key: str, ttl_seconds: int, factory):
        import time

        now = time.time()
        cached = self._data.get(key)
        if cached and now - cached[0] < ttl_seconds:
            return cached[1]
        value = factory()
        self._data[key] = (now, value)
        return value

    def clear(self, prefix: str | None = None) -> None:
        if prefix is None:
            self._data.clear()
            return
        for key in list(self._data):
            if key.startswith(prefix):
                del self._data[key]


cache = TTLCache()
app = FastAPI(title=TITLE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def bootstrap() -> None:
    init_db()
    if get_restaurant_count() == 0:
        logger.info("No restaurants found. Seeding sample data.")
        seed_data()


@app.on_event("startup")
def startup_event() -> None:
    bootstrap()


@app.get("/")
def root() -> FileResponse:
    return FileResponse(BASE_DIR / "templates" / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    return {
        "title": TITLE,
        "base_address": BASE_ADDRESS,
        "search_radius_meters": SEARCH_RADIUS_METERS,
        "has_kakao_api": has_kakao_api_key(),
    }


@app.get("/api/weather")
def weather_api() -> dict[str, Any]:
    try:
        return cache.get_or_set("weather", 1800, get_lunch_weather)
    except Exception as exc:
        logger.exception("Failed to load weather")
        return {
            "category": "unknown",
            "summary": "날씨 정보를 불러오지 못했습니다.",
            "temperature_c": "-",
            "note": str(exc),
        }


@app.get("/api/recommendations")
def recommendations_api() -> dict[str, Any]:
    try:
        data = cache.get_or_set("recommendations", 180, recommend_lunches)
        return {"recommendations": data}
    except Exception as exc:
        logger.exception("Failed to load recommendations")
        return {"recommendations": [], "error": str(exc)}


@app.get("/api/visits")
def visits_api(limit: int = 10) -> dict[str, Any]:
    try:
        data = cache.get_or_set(f"visits:{limit}", 180, lambda: get_recent_visits(limit=limit))
        return {"visits": data}
    except Exception as exc:
        logger.exception("Failed to load visits")
        return {"visits": [], "error": str(exc)}


@app.get("/api/restaurants")
def restaurants_api() -> dict[str, Any]:
    try:
        data = cache.get_or_set("restaurants", 300, list_restaurants)
        return {"restaurants": data, "count": len(data)}
    except Exception as exc:
        logger.exception("Failed to load restaurants")
        return {"restaurants": [], "count": 0, "error": str(exc)}


@app.post("/api/visit/{restaurant_id}")
def record_visit(restaurant_id: int) -> JSONResponse:
    try:
        add_visit(restaurant_id)
        cache.clear("visits:")
        cache.clear("recommendations")
        return JSONResponse({"status": "success", "message": "방문 이력을 저장했습니다."})
    except Exception as exc:
        logger.exception("Failed to save visit")
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


@app.post("/api/import-kakao")
def import_from_kakao() -> JSONResponse:
    try:
        if not has_kakao_api_key():
            return JSONResponse(
                {"status": "error", "message": "KAKAO_REST_API_KEY가 설정되어 있지 않습니다."},
                status_code=400,
            )

        restaurants = fetch_nearby_restaurants(address=BASE_ADDRESS, radius_m=SEARCH_RADIUS_METERS)
        result = save_kakao_restaurants(restaurants)
        cache.clear()
        return JSONResponse(
            {
                "status": "success",
                "inserted": result["inserted"],
                "skipped": result["skipped"],
                "address": BASE_ADDRESS,
                "radius": SEARCH_RADIUS_METERS,
            }
        )
    except KakaoLocalError as exc:
        logger.warning("Kakao import failed: %s", exc)
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=400)
    except Exception as exc:
        logger.exception("Unexpected Kakao import failure")
        return JSONResponse(
            {"status": "error", "message": f"예상하지 못한 오류가 발생했습니다: {exc}"},
            status_code=500,
        )


@app.post("/api/reset-data")
def reset_data() -> JSONResponse:
    try:
        seed_data(reset=True)
        cache.clear()
        return JSONResponse({"status": "success", "message": "샘플 식당과 방문 이력을 다시 세팅했습니다."})
    except Exception as exc:
        logger.exception("Failed to reset data")
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


@app.post("/api/clear-cache")
def clear_cache() -> dict[str, str]:
    cache.clear()
    return {"status": "success", "message": "서버 캐시를 비웠습니다."}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
