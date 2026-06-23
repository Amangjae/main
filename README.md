# 점심 추천

서울특별시 중구 을지로 16을 기본 기준 주소로 사용하는 FastAPI + SQLite 기반 점심 추천 앱입니다. 기준 주소를 화면에서 직접 바꿀 수 있고, 카카오 로컬 API로 반경 1.5km 내 식당을 가져와 추천과 방문 기록에 반영합니다.

## 주요 기능

- 오늘 점심 추천 4곳 제공
- 기존 방문 식당 3곳, 미방문 식당 1곳 우선 추천
- 실제 날씨와 최근 방문 이력 반영
- 추천 카드에서 `선택` 버튼 클릭 시 당일 방문 횟수 저장
- 카카오 로컬 API로 주변 식당 수집 및 SQLite 저장
- 기준 주소의 동 이름과 실제 날씨 표시
- PC 2열, 모바일 1열 반응형 카드 레이아웃

## 실행 방법

```bash
pip install -r requirements.txt
python app.py
```

브라우저에서 `http://localhost:8000` 으로 접속합니다.

## 환경 변수

`.env` 예시:

```env
KAKAO_REST_API_KEY=your_kakao_rest_api_key
WEATHER_API_KEY=your_weather_api_key
LUNCH_BASE_ADDRESS=서울특별시 중구 을지로 16
SEARCH_RADIUS_METERS=1500
DB_PATH=data/lunch_recommender.db
PORT=8000
```

## API

- `GET /api/config`
- `GET /api/weather`
- `GET /api/recommendations`
- `GET /api/visits`
- `POST /api/base-address`
- `POST /api/visit/{restaurant_id}`
- `POST /api/import-kakao`
- `POST /api/reset-data`
- `POST /api/clear-cache`

## GitHub Pages

`docs/` 폴더에는 GitHub Pages용 정적 화면이 포함되어 있습니다. 실제 API 서버와 연결하려면 `docs/config.js` 에 아래처럼 API 주소를 넣으면 됩니다.

```js
window.LUNCH_API_BASE = "https://your-api-domain";
```
