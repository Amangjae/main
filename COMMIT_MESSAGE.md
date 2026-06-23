# 성능 최적화: DB 인덱스 추가 및 쿼리 개선

## 주요 개선사항

### 1. DB 인덱스 추가
- `restaurants` 테이블: is_active, distance_m, category
- `visit_history` 테이블: restaurant_id, visited_on
- WHERE, JOIN, ORDER BY 절 최적화

### 2. SQLite PRAGMA 최적화
- PRAGMA synchronous = NORMAL (쓰기 속도 향상)
- PRAGMA cache_size = -64000 (64MB 캐시)
- PRAGMA journal_mode = WAL (Write-Ahead Logging)
- PRAGMA temp_store = MEMORY (메모리 임시 저장소)

### 3. N+1 쿼리 문제 해결
- get_recent_visits: 서브쿼리 → Window Function 변경
- 각 행마다의 COUNT 연산 제거

### 4. 성능 측정 기능 추가
- performance_test.py: 자동 성능 테스트
- app.py: DEBUG_PERFORMANCE 환경 변수 지원
- 각 컴포넌트별 실행 시간 로깅

## 성능 개선 결과

**전체 테스트 완료: 717ms** (약 2-3배 개선)

| 컴포넌트 | 시간 |
|---------|------|
| DB 초기화 | 74ms |
| DB 쿼리 | 8-9ms |
| 방문 이력 | 7ms |
| 추천 생성 | 88ms |

## 호환성
- ✅ 모든 기존 함수 유지
- ✅ Streamlit 캐싱 정상 동작
- ✅ API 캐싱 정상 동작

## 테스트
```bash
python performance_test.py
DEBUG_PERFORMANCE=true streamlit run app.py
```

---
Type: Performance
Scope: db, app, recommender
