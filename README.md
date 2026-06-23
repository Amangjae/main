# Lunch Recommender

서울 중구 을지로 16 기준 반경 1.5km 식당을 추천하는 FastAPI + SQLite 웹 앱입니다. 샘플 데이터로 바로 실행할 수 있고, Kakao Local API 키가 있으면 실제 주변 음식점을 가져와 저장하고 추천에 반영합니다.

## 주요 기능

- 최근 방문 이력과 점심시간 날씨를 반영한 4곳 추천
- 샘플 식당 데이터 자동 시드
- Kakao Local API 기반 주소 변환 + FD6 음식점 검색
- SQLite 저장, 중복 방지, 최근 방문 기록 관리
- 브라우저에서 바로 볼 수 있는 HTML/CSS/JS 웹 UI

## 실행 방법

```bash
pip install -r requirements.txt
python app.py
```

브라우저에서 `http://localhost:8000` 으로 접속합니다.

## 환경 변수

`.env` 파일 예시:

```env
KAKAO_REST_API_KEY=your_kakao_rest_api_key
WEATHER_API_KEY=your_weather_api_key
LUNCH_BASE_ADDRESS=서울특별시 중구 을지로 16
SEARCH_RADIUS_METERS=1500
DB_PATH=data/lunch_recommender.db
PORT=8000
```

## API 요약

- `GET /api/config`
- `GET /api/weather`
- `GET /api/recommendations`
- `GET /api/visits?limit=10`
- `GET /api/restaurants`
- `POST /api/visit/{restaurant_id}`
- `POST /api/import-kakao`
- `POST /api/reset-data`
- `POST /api/clear-cache`

## 성능 개선 포인트

- SQLite WAL 모드, 인덱스, 메모리 캐시 PRAGMA 적용
- API 응답용 TTL 캐시 적용
- Kakao 주소 변환/카테고리 검색 결과 캐시 적용
- Kakao 식당 저장 시 배치 중복 검사와 일괄 insert 적용

## 주의 사항

- `.env`, `data/*.db`, `.venv/` 는 Git에 포함하지 않도록 `.gitignore`로 제외했습니다.
- GitHub 저장소만으로는 FastAPI 서버가 실행되지 않으므로, 실제 웹 서비스 공개에는 Render, Railway, EC2 같은 Python 실행 환경이 추가로 필요합니다.
