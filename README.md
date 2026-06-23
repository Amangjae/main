# Lunch Recommender - FastAPI 웹앱

FastAPI + SQLite 기반 회사 점심 추천 웹애플리케이션입니다.

## 기능

- 🍽️ **오늘의 추천**: 최근 방문 식당 + 미방문 식당 4곳 추천
- 🌤️ **날씨 연동**: 점심시간 날씨 기반 추천
- 📍 **카카오 API**: 주변 식당 자동 검색 (선택)
- 📝 **방문 기록**: 방문 이력 자동 관리
- ⚡ **성능 최적화**: 캐싱 및 DB 인덱싱

## 기본 설정

- 기준 주소: 서울 중구 을지로 16
- 검색 반경: 1.5km
- 추천 식당: 4곳 (최근 방문 3 + 미방문 1)
- 고려 요소: 방문 이력 + 점심시간 날씨

## 프로젝트 구조

```text
.
├── app.py                    # FastAPI 애플리케이션
├── db.py                     # SQLite 데이터베이스 계층
├── recommender.py            # 추천 엔진
├── weather.py                # 날씨 API
├── kakao_local.py            # 카카오 로컬 API
├── seed.py                   # 초기 데이터
├── requirements.txt          # Python 의존성
├── .env.example              # 환경 변수 예시
├── templates/
│   └── index.html            # 웹 UI
└── static/
    ├── style.css             # 스타일시트
    └── app.js                # 클라이언트 스크립트
```

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일 생성 (또는 `.env.example` 참고):

```bash
KAKAO_REST_API_KEY=your_kakao_api_key  # 선택사항
WEATHER_API_KEY=your_weather_api_key    # 선택사항
LUNCH_BASE_ADDRESS=서울특별시 중구 을지로 16
SEARCH_RADIUS_METERS=1500
DB_PATH=data/lunch_recommender.db
PORT=8000
```

### 3. 앱 실행

```bash
python app.py
```

또는 Uvicorn 직접 실행:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 4. 브라우저 접속

http://localhost:8000

## API 엔드포인트

### 조회 API

- `GET /api/config` - 앱 설정
- `GET /api/weather` - 날씨 정보 (캐시: 1시간)
- `GET /api/recommendations` - 추천 식당 (캐시: 5분)
- `GET /api/visits?limit=10` - 방문 이력 (캐시: 5분)
- `GET /api/restaurants` - 전체 식당 목록 (캐시: 10분)

### 액션 API

- `POST /api/visit/{restaurant_id}` - 방문 기록 추가
- `POST /api/import-kakao` - 카카오 API에서 식당 가져오기
- `POST /api/reset-data` - 초기 데이터 리셋
- `POST /api/clear-cache` - 캐시 초기화

## 웹 UI

- 📱 반응형 디자인 (모바일 / 태블릿 / 데스크톱)
- 🎨 깔끔한 그라데이션 스타일
- ⚡ 실시간 API 호출
- 🔄 5분마다 자동 새로고침

## 주요 특징

✅ **Streamlit 앱에서 FastAPI로 마이그레이션**
- 독립적인 웹서버
- 더 빠른 응답 속도
- 모바일 친화적 UI

✅ **캐싱 시스템**
- 메모리 기반 TTL 캐싱
- API 호출 최소화

✅ **최적화된 DB 쿼리**
- SQLite PRAGMA 최적화
- 인덱싱 적용

✅ **API 키 선택 사항**
- API 없이도 샘플 데이터로 동작
- Kakao API 활성화 시 실제 주변 식당 검색

## 환경 변수

| 변수 | 설명 | 필수 | 기본값 |
|------|------|------|--------|
| `KAKAO_REST_API_KEY` | 카카오 로컬 API 키 | ❌ | - |
| `WEATHER_API_KEY` | 날씨 API 키 | ❌ | - |
| `LUNCH_BASE_ADDRESS` | 기준 주소 | ❌ | 서울특별시 중구 을지로 16 |
| `SEARCH_RADIUS_METERS` | 검색 반경 | ❌ | 1500 |
| `DB_PATH` | DB 파일 경로 | ❌ | data/lunch_recommender.db |
| `PORT` | 서버 포트 | ❌ | 8000 |

## 성능

- 초기 로드: ~500ms (캐시 미적중 시)
- API 응답: <100ms (캐시 적중 시)
- 데이터 새로고침: 5분 자동 갱신

## 배포

### Heroku

```bash
git push heroku main
```

### Docker

```bash
docker build -t lunch-recommender .
docker run -p 8000:8000 lunch-recommender
```

### 클라우드 플랫폼

- Railway
- Render
- PythonAnywhere
- AWS (EC2, Lambda)

## 라이선스

MIT