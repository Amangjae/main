import os
from datetime import datetime, timedelta
import time

import streamlit as st
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

# ============ 성능 로깅 ============
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TITLE = "회사 점심 추천기"
BASE_ADDRESS = os.getenv("LUNCH_BASE_ADDRESS", "서울특별시 중구 을지로 16")
SEARCH_RADIUS_METERS = int(os.getenv("SEARCH_RADIUS_METERS", "1500"))

st.set_page_config(page_title=TITLE, page_icon=":fork_and_knife:", layout="wide")


def bootstrap() -> None:
    """DB 초기화 (캐싱)"""
    start = time.time()
    init_db()
    if get_restaurant_count() == 0:
        seed_data()
    elapsed = (time.time() - start) * 1000
    logger.info(f"✓ bootstrap: {elapsed:.2f}ms")


def render_header() -> None:
    st.title(TITLE)
    st.caption(
        f"기준 주소: {BASE_ADDRESS} | 반경 {SEARCH_RADIUS_METERS}m 식당 대상"
    )


# ============ 캐싱된 API/DB 조회 함수 ============
@st.cache_data(ttl=3600)
def _get_cached_weather():
    """날씨 데이터 캐싱 (1시간)"""
    return get_lunch_weather()


@st.cache_data(ttl=300)
def _get_cached_recommendations():
    """추천 데이터 캐싱 (5분)"""
    return recommend_lunches()


@st.cache_data(ttl=300)
def _get_cached_recent_visits():
    """최근 방문 이력 캐싱 (5분)"""
    return get_recent_visits(limit=10)


@st.cache_data(ttl=600)
def _get_cached_restaurants():
    """식당 목록 캐싱 (10분)"""
    return list_restaurants()


# ============ UI 렌더링 함수 ============
def render_weather_card() -> None:
    weather = _get_cached_weather()
    icon_map = {
        "rainy": ":umbrella:",
        "clear": ":sun_behind_small_cloud:",
        "hot": ":sunny:",
        "cold": ":snowflake:",
    }
    icon = icon_map.get(weather["category"], ":cloud:")
    st.info(
        f"{icon} 오늘 점심 날씨: {weather['summary']} "
        f"(기온 {weather['temperature_c']}°C, 추천 포인트: {weather['note']})"
    )


def render_recommendations() -> None:
    st.subheader("오늘의 추천 4곳")
    recommendations = _get_cached_recommendations()

    if not recommendations:
        st.warning("추천할 식당 데이터가 없습니다. 먼저 초기 데이터를 준비해주세요.")
        return

    cols = st.columns(2)
    for index, item in enumerate(recommendations):
        with cols[index % 2]:
            with st.container(border=True):
                st.markdown(f"### {item['name']}")
                st.write(f"카테고리: {item['category']}")
                st.write(f"거리: 약 {item['distance_m']}m")
                st.write(f"추천 유형: {item['recommendation_type']}")
                st.write(f"추천 점수: {item['score']}")
                st.write(f"추천 이유: {item['reason']}")
                st.write(f"예상 예산: {item['price_level']}")
                if st.button(f"{item['name']} 방문 기록 추가", key=f"visit-{item['id']}"):
                    add_visit(item["id"])
                    st.success(f"{item['name']} 방문 이력을 저장했습니다.")
                    st.cache_data.clear()
                    st.rerun()


def render_visit_history() -> None:
    st.subheader("최근 방문 이력")
    visits = _get_cached_recent_visits()
    if not visits:
        st.write("아직 방문 이력이 없습니다.")
        return

    for visit in visits:
        st.write(
            f"- {visit['visited_on']} | {visit['restaurant_name']} | "
            f"{visit['meal_type']} | 누적 {visit['visit_count']}회 방문"
        )


def render_restaurant_list() -> None:
    with st.expander("등록된 식당 보기"):
        restaurants = _get_cached_restaurants()
        st.write(f"총 {len(restaurants)}곳")
        for restaurant in restaurants:
            address = restaurant.get("road_address") or restaurant.get("address") or "-"
            source = restaurant.get("source") or "sample"
            label = (
                f"- {restaurant['name']} / {restaurant['category']} / "
                f"{restaurant['distance_m']}m / {address} / source={source}"
            )
            st.write(label)
            if restaurant.get("place_url"):
                st.caption(restaurant["place_url"])


def import_restaurants_from_kakao() -> None:
    try:
        restaurants = fetch_nearby_restaurants(
            address=BASE_ADDRESS,
            radius_m=SEARCH_RADIUS_METERS,
        )
        result = save_kakao_restaurants(restaurants)
        st.session_state["kakao_import_result"] = {
            "status": "success",
            "inserted": result["inserted"],
            "skipped": result["skipped"],
            "address": BASE_ADDRESS,
            "radius": SEARCH_RADIUS_METERS,
        }
        st.cache_data.clear()
    except KakaoLocalError as exc:
        st.session_state["kakao_import_result"] = {
            "status": "error",
            "message": str(exc),
        }
    except Exception as exc:
        st.session_state["kakao_import_result"] = {
            "status": "error",
            "message": f"예상하지 못한 오류가 발생했습니다: {exc}",
        }


def render_import_result() -> None:
    result = st.session_state.get("kakao_import_result")
    if not result:
        return

    if result["status"] == "success":
        st.sidebar.success(
            "카카오 API 조회 완료 | "
            f"새로 추가: {result['inserted']}곳 | "
            f"중복 건너뛰기: {result['skipped']}곳"
        )
        st.sidebar.caption(
            f"기준 주소: {result['address']} | 반경 {result['radius']}m"
        )
    else:
        st.sidebar.error(result["message"])


def render_sidebar() -> None:
    st.sidebar.header("관리")
    st.sidebar.write("API 키가 없어도 샘플 데이터 기반으로 동작합니다.")

    api_enabled = has_kakao_api_key()
    if st.sidebar.button(
        "카카오 API로 주변 식당 가져오기",
        disabled=not api_enabled,
        use_container_width=True,
    ):
        import_restaurants_from_kakao()
        st.rerun()

    if not api_enabled:
        st.sidebar.warning("KAKAO_REST_API_KEY가 없어서 카카오 불러오기 버튼이 비활성화됩니다.")

    if st.sidebar.button("초기 데이터 다시 세팅"):
        seed_data(reset=True)
        st.session_state["kakao_import_result"] = {
            "status": "success",
            "inserted": 0,
            "skipped": 0,
            "address": BASE_ADDRESS,
            "radius": SEARCH_RADIUS_METERS,
        }
        st.sidebar.success("식당과 방문 이력을 다시 세팅했습니다.")
        st.cache_data.clear()
        st.rerun()

    if st.sidebar.button("추천 새로고침"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    render_import_result()
    st.sidebar.write("환경 변수 예시")
    st.sidebar.code(
        "\n".join(
            [
                "KAKAO_REST_API_KEY=...",
                "WEATHER_API_KEY=...",
                "LUNCH_BASE_ADDRESS=서울특별시 중구 을지로 16",
                "SEARCH_RADIUS_METERS=1500",
                "DB_PATH=data/lunch_recommender.db",
            ]
        )
    )


def main() -> None:
    start_time = time.time()
    
    logger.info("=== 앱 시작 ===")
    bootstrap()
    render_sidebar()
    render_header()
    
    # 날씨 카드 표시
    render_weather_card()
    
    # 추천 식당 표시
    render_recommendations()
    st.markdown("---")
    
    # 최근 이력과 식당 목록을 병렬로 표시
    col1, col2 = st.columns(2)
    with col1:
        render_visit_history()
    with col2:
        render_restaurant_list()
    
    # 성능 정보 출력 (디버그 모드)
    if os.getenv("DEBUG_PERFORMANCE", "false").lower() == "true":
        total_time = (time.time() - start_time) * 1000
        st.markdown("---")
        st.write(f"### ⏱️ 총 로드 시간: {total_time:.2f}ms")
        logger.info(f"=== 앱 완료: {total_time:.2f}ms ===")


if __name__ == "__main__":
    main()
