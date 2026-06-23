import os
from datetime import datetime, timedelta
import time
import logging
from functools import lru_cache

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

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

# ============ 로깅 ============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============ 설정 ============
TITLE = "회사 점심 추천기"
BASE_ADDRESS = os.getenv("LUNCH_BASE_ADDRESS", "서울특별시 중구 을지로 16")
SEARCH_RADIUS_METERS = int(os.getenv("SEARCH_RADIUS_METERS", "1500"))

# ============ FastAPI 앱 초기화 ============
app = FastAPI(title=TITLE)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static 파일 마운팅
app.mount("/static", StaticFiles(directory="static"), name="static")

# ============ 캐싱 ============
class CacheManager:
    """간단한 캐싱 매니저"""
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key, ttl_seconds):
        """TTL이 지나지 않은 캐시 데이터 반환"""
        if key not in self.cache:
            return None
        elapsed = time.time() - self.timestamps[key]
        if elapsed > ttl_seconds:
            del self.cache[key]
            del self.timestamps[key]
            return None
        return self.cache[key]
    
    def set(self, key, value):
        """캐시 데이터 저장"""
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self, key=None):
        """캐시 초기화"""
        if key:
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
        else:
            self.cache.clear()
            self.timestamps.clear()

cache_manager = CacheManager()

def get_cached_data(key, func, ttl_seconds):
    """데이터 캐시 래퍼"""
    cached = cache_manager.get(key, ttl_seconds)
    if cached is not None:
        return cached
    data = func()
    cache_manager.set(key, data)
    return data

# ============ 부트스트랩 ============
def bootstrap():
    """DB 초기화"""
    start = time.time()
    init_db()
    if get_restaurant_count() == 0:
        logger.info("초기 데이터 시딩 시작...")
        seed_data()
    elapsed = (time.time() - start) * 1000
    logger.info(f"✓ Bootstrap 완료: {elapsed:.2f}ms")

# ============ API 엔드포인트 ============

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 DB 초기화"""
    bootstrap()

@app.get("/", response_class=HTMLResponse)
async def root():
    """메인 페이지"""
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/config")
async def get_config():
    """앱 설정 반환"""
    return {
        "title": TITLE,
        "base_address": BASE_ADDRESS,
        "search_radius_meters": SEARCH_RADIUS_METERS,
        "has_kakao_api": has_kakao_api_key(),
    }

@app.get("/api/weather")
async def get_weather():
    """날씨 정보 (캐시: 3600초)"""
    try:
        def fetch():
            return get_lunch_weather()
        weather = get_cached_data("weather", fetch, 3600)
        return weather
    except Exception as e:
        logger.error(f"날씨 조회 실패: {e}")
        return {
            "category": "unknown",
            "summary": "날씨 정보를 가져올 수 없습니다.",
            "temperature_c": "-",
            "note": "오류",
        }

@app.get("/api/recommendations")
async def get_recommendations():
    """추천 식당 4곳 (캐시: 300초)"""
    try:
        def fetch():
            return recommend_lunches()
        recommendations = get_cached_data("recommendations", fetch, 300)
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"추천 식당 조회 실패: {e}")
        return {"recommendations": [], "error": str(e)}

@app.get("/api/visits")
async def get_visits(limit: int = 10):
    """최근 방문 이력 (캐시: 300초)"""
    try:
        def fetch():
            return get_recent_visits(limit=limit)
        visits = get_cached_data(f"visits_{limit}", fetch, 300)
        return {"visits": visits}
    except Exception as e:
        logger.error(f"방문 이력 조회 실패: {e}")
        return {"visits": [], "error": str(e)}

@app.get("/api/restaurants")
async def get_restaurants():
    """전체 식당 목록 (캐시: 600초)"""
    try:
        def fetch():
            return list_restaurants()
        restaurants = get_cached_data("restaurants", fetch, 600)
        return {"restaurants": restaurants, "count": len(restaurants)}
    except Exception as e:
        logger.error(f"식당 목록 조회 실패: {e}")
        return {"restaurants": [], "count": 0, "error": str(e)}

@app.post("/api/visit/{restaurant_id}")
async def record_visit(restaurant_id: int):
    """방문 기록 추가"""
    try:
        add_visit(restaurant_id)
        cache_manager.clear("visits_10")
        cache_manager.clear("recommendations")
        return {"status": "success", "message": "방문 이력이 저장되었습니다."}
    except Exception as e:
        logger.error(f"방문 기록 저장 실패: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/import-kakao")
async def import_kakao():
    """카카오 API에서 주변 식당 가져오기"""
    try:
        if not has_kakao_api_key():
            return {
                "status": "error",
                "message": "KAKAO_REST_API_KEY가 설정되지 않았습니다.",
            }
        
        restaurants = fetch_nearby_restaurants(
            address=BASE_ADDRESS,
            radius_m=SEARCH_RADIUS_METERS,
        )
        result = save_kakao_restaurants(restaurants)
        cache_manager.clear()
        
        return {
            "status": "success",
            "inserted": result["inserted"],
            "skipped": result["skipped"],
            "address": BASE_ADDRESS,
            "radius": SEARCH_RADIUS_METERS,
        }
    except KakaoLocalError as e:
        logger.error(f"카카오 API 오류: {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"카카오 임포트 실패: {e}")
        return {"status": "error", "message": f"예상하지 못한 오류: {e}"}

@app.post("/api/reset-data")
async def reset_data():
    """초기 데이터 리셋"""
    try:
        seed_data(reset=True)
        cache_manager.clear()
        return {
            "status": "success",
            "message": "식당과 방문 이력이 초기화되었습니다.",
        }
    except Exception as e:
        logger.error(f"데이터 초기화 실패: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/clear-cache")
async def clear_cache():
    """캐시 초기화"""
    try:
        cache_manager.clear()
        return {"status": "success", "message": "캐시가 초기화되었습니다."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============ 실행 ============
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
