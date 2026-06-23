#!/usr/bin/env python3
"""성능 테스트 스크립트"""

import os
import sys
import time
from pathlib import Path

# 프로젝트 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent))

os.environ["DEBUG_PERFORMANCE"] = "true"

def test_db_performance():
    """DB 성능 테스트"""
    print("\n=== DB 성능 테스트 ===\n")
    
    from db import init_db, get_restaurant_count, list_restaurants, get_recent_visits, get_restaurants_with_history
    
    # 1. init_db
    start = time.time()
    init_db()
    elapsed = (time.time() - start) * 1000
    print(f"✓ init_db: {elapsed:.2f}ms")
    
    # 2. get_restaurant_count
    start = time.time()
    count = get_restaurant_count()
    elapsed = (time.time() - start) * 1000
    print(f"✓ get_restaurant_count: {elapsed:.2f}ms (결과: {count}개)")
    
    # 3. list_restaurants
    start = time.time()
    restaurants = list_restaurants()
    elapsed = (time.time() - start) * 1000
    print(f"✓ list_restaurants: {elapsed:.2f}ms (결과: {len(restaurants)}개)")
    
    # 4. get_restaurants_with_history
    start = time.time()
    restaurants_with_hist = get_restaurants_with_history()
    elapsed = (time.time() - start) * 1000
    print(f"✓ get_restaurants_with_history: {elapsed:.2f}ms (결과: {len(restaurants_with_hist)}개)")
    
    # 5. get_recent_visits
    start = time.time()
    visits = get_recent_visits(limit=10)
    elapsed = (time.time() - start) * 1000
    print(f"✓ get_recent_visits: {elapsed:.2f}ms (결과: {len(visits)}개)")


def test_recommender_performance():
    """추천 엔진 성능 테스트"""
    print("\n=== 추천 엔진 성능 테스트 ===\n")
    
    from recommender import recommend_lunches
    from weather import get_lunch_weather
    
    # 1. get_lunch_weather
    start = time.time()
    weather = get_lunch_weather()
    elapsed = (time.time() - start) * 1000
    print(f"✓ get_lunch_weather: {elapsed:.2f}ms (카테고리: {weather['category']})")
    
    # 2. recommend_lunches
    start = time.time()
    recommendations = recommend_lunches()
    elapsed = (time.time() - start) * 1000
    print(f"✓ recommend_lunches: {elapsed:.2f}ms (결과: {len(recommendations)}개)")
    
    if recommendations:
        print(f"  - {recommendations[0]['name']}: {recommendations[0]['score']} 점수")


def test_api_performance():
    """API 성능 테스트"""
    print("\n=== API 성능 테스트 ===\n")
    
    from kakao_local import search_nearby_restaurants
    from seed import seed_data
    
    # 1. search_nearby_restaurants (샘플 데이터)
    start = time.time()
    restaurants = search_nearby_restaurants()
    elapsed = (time.time() - start) * 1000
    print(f"✓ search_nearby_restaurants: {elapsed:.2f}ms (결과: {len(restaurants)}개)")


def main():
    """전체 성능 테스트"""
    print("\n" + "="*60)
    print("  점심 추천 앱 - 성능 테스트")
    print("="*60)
    
    total_start = time.time()
    
    try:
        test_db_performance()
        test_api_performance()
        test_recommender_performance()
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    total_elapsed = (time.time() - total_start) * 1000
    print("\n" + "="*60)
    print(f"  ✓ 전체 테스트 완료: {total_elapsed:.2f}ms")
    print("="*60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
