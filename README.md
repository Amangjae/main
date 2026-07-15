# 점심 추천

이 프로젝트는 GitHub Pages에서 바로 열 수 있는 회사 점심 추천 페이지입니다.

식당 목록은 카카오 로컬 API로 모으고, 데이터는 Google Sheets와 `docs/data/site-data.json`을 함께 사용합니다. 화면에서는 참석 인원을 선택한 뒤 오늘 추천 4곳을 보고, `선택` 또는 `오늘은 가지 않음`을 기록할 수 있습니다.

## 현재 구조

- `docs/`
  GitHub Pages에 올라가는 실제 웹 화면 파일
- `docs/data/site-data.json`
  추천 화면이 읽는 데이터 파일
- `scripts/build_pages_data.py`
  카카오 API, Google Sheets, 날씨 정보를 읽어 JSON을 만드는 스크립트
- `scripts/google_apps_script_example.gs`
  선택 버튼을 누를 때 Google Sheets에 기록하기 위한 Apps Script 예제
- `WORKLOG.md`
  변경 내역을 쉬운 말로 남기는 기록 파일

## 추천 방식

- 기준 주소 반경 안의 식당을 사용합니다.
- 최근 1주일 안에 `선택`된 식당은 추천에서 제외합니다.
- 참석 인원과 오늘 날씨를 함께 반영합니다.
- 추천은 총 4곳이며, 가능하면 다시 가도 좋은 곳 3곳과 새로운 후보 1곳을 우선 보여줍니다.

## 꼭 필요한 설정

GitHub Actions Secrets:

- `KAKAO_REST_API_KEY`
- `GOOGLE_SHEETS_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

Google Sheets `config` 시트 예시:

- `title` / `점심 추천`
- `base_address` / `서울특별시 중구 을지로 16`
- `search_radius_meters` / `1500`
- `party_size_default` / `2`
- `selection_endpoint` / `배포한 Google Apps Script 웹앱 주소`

## 선택 저장 방식

GitHub Pages는 정적 사이트라서 브라우저에서 바로 Google Sheets에 안전하게 쓰기 어렵습니다.

그래서 아래 구조를 사용합니다.

- 화면: GitHub Pages
- 저장소 역할: Google Sheets
- 저장 API 역할: Google Apps Script

`scripts/google_apps_script_example.gs` 파일 내용을 Apps Script에 넣고 웹앱으로 배포한 뒤, 나온 주소를 `selection_endpoint`에 넣으면 `선택` 버튼 기록이 저장됩니다.

## Pages 설정

GitHub 저장소에서 아래처럼 설정하면 됩니다.

- `Settings > Pages`
- `Source`: `Deploy from a branch`
- `Branch`: `master`
- `Folder`: `/docs`

## 작업 기록 원칙

앞으로 변경이 생기면 `WORKLOG.md`에 아래 내용을 쉬운 말로 적습니다.

- 무엇을 바꿨는지
- 왜 바꿨는지
- 어디서 확인하면 되는지
- 다음에는 무엇을 하면 되는지
