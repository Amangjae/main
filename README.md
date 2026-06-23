# 점심 추천

GitHub Pages에서 바로 보여지는 점심 추천 사이트입니다. 데이터는 `Google Sheets + GitHub Actions + Kakao Local API` 흐름으로 갱신되고, 화면은 `docs/` 정적 파일로 배포됩니다.

## 현재 구조

- `docs/`
  GitHub Pages에 실제로 올라가는 정적 홈페이지
- `docs/data/site-data.json`
  페이지가 읽는 정적 데이터 파일
- `.github/workflows/update-pages-data.yml`
  매일 오전 9시(KST) 기준으로 데이터를 다시 생성하는 워크플로
- `scripts/build_pages_data.py`
  Google Sheets 설정값, 방문 기록, 카카오 식당 데이터, 날씨 데이터를 합쳐 `site-data.json`을 생성

## 동작 방식

1. GitHub Actions가 매일 오전 9시(KST)에 실행됩니다.
2. Google Sheets의 `config`, `visits` 시트를 읽습니다.
3. 기준 주소를 카카오 API로 좌표 변환한 뒤 반경 1.5km 식당을 조회합니다.
4. 결과를 다시 Google Sheets `restaurants` 시트에 반영합니다.
5. 날씨와 방문 기록을 반영해 추천 4곳을 계산합니다.
6. 최종 결과를 `docs/data/site-data.json`으로 저장하고 커밋합니다.
7. GitHub Pages는 그 JSON을 읽어 실제 홈페이지처럼 표시합니다.

## GitHub Secrets

저장소 `Settings > Secrets and variables > Actions`에 아래 값을 등록해야 합니다.

- `KAKAO_REST_API_KEY`
- `GOOGLE_SHEETS_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

## Google Sheets 시트 구성

### `config` 시트

| key | value |
| --- | --- |
| title | 점심 추천 |
| base_address | 서울특별시 중구 을지로 16 |
| search_radius_meters | 1500 |

### `visits` 시트

| restaurant_key | restaurant_name | visited_on | meal_type | visit_count |
| --- | --- | --- | --- | --- |
| sample-1 | 을지로국밥 | 2026-06-20 | 점심 | 2 |

### `restaurants` 시트

워크플로가 자동으로 갱신합니다.

## GitHub Pages 설정

`Settings > Pages` 에서 아래처럼 설정하면 됩니다.

- `Source`: `Deploy from a branch`
- `Branch`: `master`
- `Folder`: `/docs`

## 메모

- 설정 영역은 타이틀 바로 아래에 배치되어 있습니다.
- Pages는 정적 사이트이므로 Python 서버 없이 바로 열립니다.
- `docs/config.js`의 `window.LUNCH_SHEET_URL`에 시트 URL을 넣으면 화면의 `구글 시트 열기` 버튼이 활성화됩니다.
