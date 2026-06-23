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

## GitHub Pages

`GitHub Pages` 에서 바로 보이도록 `docs/` 정적 데모 사이트도 추가했습니다.

설정 방법:

1. GitHub 저장소 `Settings`
2. `Pages`
3. `Build and deployment` 에서
   - `Source`: `Deploy from a branch`
   - `Branch`: `master`
   - `Folder`: `/docs`
4. 저장

배포가 끝나면 아래 주소 형태로 열립니다.

- `https://amangjae.github.io/main/`

주의:

- Pages 버전은 정적 데모입니다.
- FastAPI, SQLite, Kakao API 실시간 호출은 GitHub Pages 단독으로는 실행되지 않습니다.
- 실제 서버 기능까지 공개하려면 Render, Railway, EC2 같은 Python 호스팅이 별도로 필요합니다.

## Render 배포

이 저장소에는 Render 배포용 [`render.yaml`](</G:/내 드라이브/VScode/lunck_recommender/render.yaml>) 과 [`Procfile`](</G:/내 드라이브/VScode/lunck_recommender/Procfile>) 이 포함되어 있습니다.

1. Render에서 `New +` → `Blueprint` 또는 `Web Service`를 선택합니다.
2. GitHub 저장소 `Amangjae/main` 을 연결합니다.
3. `render.yaml` 을 읽도록 두거나, 수동 생성 시 아래를 사용합니다.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - Health Check Path: `/api/health`
4. 환경 변수에 아래 값을 설정합니다.
   - `KAKAO_REST_API_KEY`
   - `WEATHER_API_KEY`
   - `LUNCH_BASE_ADDRESS`
   - `SEARCH_RADIUS_METERS`
   - `DB_PATH`

참고:
- `DB_PATH=data/lunch_recommender.db` 는 배포 환경의 로컬 디스크를 사용합니다.
- Render 무료 인스턴스는 재배포/재시작 시 로컬 SQLite 데이터가 유지되지 않을 수 있습니다.
- 운영용으로는 PostgreSQL 같은 외부 DB로 옮기는 것이 안전합니다.

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
