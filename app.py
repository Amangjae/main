import logging
import os
from datetime import datetime, time as dt_time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from db import (
    add_visit,
    backfill_restaurant_metadata,
    clear_all,
    get_app_state,
    get_last_sync,
    get_recent_visits,
    get_restaurant_count,
    init_db,
    list_restaurants,
    save_kakao_restaurants,
    set_app_state,
    set_last_sync,
)
from kakao_local import KakaoLocalError, fetch_nearby_restaurants, geocode_address, has_kakao_api_key, infer_menu_and_calories
from recommender import recommend_lunches
from seed import seed_data
from weather import get_lunch_weather


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TITLE = "점심 추천"
DEFAULT_BASE_ADDRESS = os.getenv("LUNCH_BASE_ADDRESS", "서울특별시 중구 을지로 16")
DEFAULT_RADIUS = int(os.getenv("SEARCH_RADIUS_METERS", "1500"))
PORT = int(os.getenv("PORT", "8000"))
SEOUL_TZ = ZoneInfo("Asia/Seoul")


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


def get_runtime_base_address() -> str:
    address = get_app_state("base_address") or DEFAULT_BASE_ADDRESS
    if not address or address.count("?") >= 3:
        set_app_state("base_address", DEFAULT_BASE_ADDRESS)
        return DEFAULT_BASE_ADDRESS
    return address


def set_runtime_base_address(address: str) -> None:
    set_app_state("base_address", address)


def get_runtime_radius() -> int:
    return DEFAULT_RADIUS


def daily_sync_key(address: str) -> str:
    return f"kakao_restaurants_daily_sync::{address}"


def bootstrap() -> None:
    init_db()
    if not get_app_state("base_address"):
        set_runtime_base_address(DEFAULT_BASE_ADDRESS)
    if get_restaurant_count() == 0:
        logger.info("No restaurants found. Seeding sample data.")
        seed_data()
    backfill_restaurant_metadata(infer_menu_and_calories)
    ensure_daily_restaurant_sync()


def should_sync_today(now: datetime, last_synced_at: str | None) -> bool:
    if now.time() < dt_time(hour=9, minute=0):
        return False
    if not last_synced_at:
        return True
    try:
        last_sync = datetime.fromisoformat(last_synced_at)
    except ValueError:
        return True
    return last_sync.date() < now.date()


def get_current_location() -> dict[str, str]:
    return geocode_address(get_runtime_base_address())


def get_current_weather() -> dict[str, Any]:
    location = get_current_location()
    weather = cache.get_or_set(
        f"weather::{get_runtime_base_address()}",
        1800,
        lambda: get_lunch_weather(float(location["y"]), float(location["x"])),
    )
    return {
        **weather,
        "dong_name": location.get("dong_name", ""),
        "base_address": get_runtime_base_address(),
    }


def ensure_daily_restaurant_sync() -> dict[str, Any]:
    if not has_kakao_api_key():
        return {"status": "skipped", "reason": "missing_api_key"}

    base_address = get_runtime_base_address()
    now = datetime.now(SEOUL_TZ)
    sync_key = daily_sync_key(base_address)
    last_synced_at = get_last_sync(sync_key)
    if not should_sync_today(now, last_synced_at):
        return {"status": "skipped", "reason": "not_due"}

    try:
        restaurants = fetch_nearby_restaurants(address=base_address, radius_m=get_runtime_radius())
        result = save_kakao_restaurants(restaurants)
        set_last_sync(sync_key, now.isoformat())
        cache.clear()
        logger.info("Daily Kakao sync complete: inserted=%s skipped=%s", result["inserted"], result["skipped"])
        return {"status": "success", **result}
    except Exception as exc:
        logger.exception("Daily Kakao sync failed")
        return {"status": "error", "message": str(exc)}


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
        "base_address": get_runtime_base_address(),
        "search_radius_meters": get_runtime_radius(),
        "has_kakao_api": has_kakao_api_key(),
    }


@app.post("/api/base-address")
async def set_base_address(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    address = str(payload.get("address", "")).strip()
    if not address:
        return JSONResponse({"status": "error", "message": "기준 주소를 입력해 주세요."}, status_code=400)

    try:
        geocode_address(address)
    except KakaoLocalError:
        if has_kakao_api_key():
            return JSONResponse({"status": "error", "message": "입력한 주소를 확인해 주세요."}, status_code=400)

    set_runtime_base_address(address)
    cache.clear()
    return JSONResponse({"status": "success", "address": address})


@app.get("/api/weather")
def weather_api() -> dict[str, Any]:
    try:
        return get_current_weather()
    except Exception as exc:
        logger.exception("Failed to load weather")
        return {
            "category": "unknown",
            "summary": "날씨 정보를 불러오지 못했습니다.",
            "temperature_c": "-",
            "note": str(exc),
            "dong_name": "",
            "base_address": get_runtime_base_address(),
        }


@app.get("/api/recommendations")
def recommendations_api() -> dict[str, Any]:
    ensure_daily_restaurant_sync()
    try:
        weather = get_current_weather()
        data = cache.get_or_set(
            f"recommendations::{get_runtime_base_address()}",
            180,
            lambda: recommend_lunches(weather=weather),
        )
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
    ensure_daily_restaurant_sync()
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
        cache.clear("recommendations::")
        return JSONResponse({"status": "success", "message": "오늘 방문 기록을 저장했습니다."})
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

        base_address = get_runtime_base_address()
        restaurants = fetch_nearby_restaurants(address=base_address, radius_m=get_runtime_radius())
        result = save_kakao_restaurants(restaurants)
        set_last_sync(daily_sync_key(base_address), datetime.now(SEOUL_TZ).isoformat())
        cache.clear()
        return JSONResponse(
            {
                "status": "success",
                "inserted": result["inserted"],
                "skipped": result["skipped"],
                "address": base_address,
                "radius": get_runtime_radius(),
            }
        )
    except KakaoLocalError as exc:
        logger.warning("Kakao import failed: %s", exc)
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=400)
    except Exception as exc:
        logger.exception("Unexpected Kakao import failure")
        return JSONResponse({"status": "error", "message": f"예상하지 못한 오류가 발생했습니다: {exc}"}, status_code=500)


@app.post("/api/reset-data")
def reset_data() -> JSONResponse:
    try:
        clear_all()
        seed_data(reset=False)
        cache.clear()
        return JSONResponse({"status": "success", "message": "샘플 데이터를 다시 세팅했습니다."})
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
