# 점심 추천

GitHub Pages에서 바로 열리는 점심 추천 사이트입니다.  
데이터는 `Google Sheets + GitHub Actions + Kakao Local API` 흐름으로 갱신되고, 화면은 `docs/` 정적 파일로 배포됩니다.

## 구조

- `docs/`
  실제 GitHub Pages 홈페이지 파일
- `docs/data/site-data.json`
  화면이 읽는 정적 데이터 파일
- `.github/workflows/update-pages-data.yml`
  매일 오전 9시(KST) 자동 갱신 워크플로
- `scripts/build_pages_data.py`
  Google Sheets, Kakao API, 날씨 데이터를 합쳐 JSON 생성
- [SETUP_GUIDE.md](/G:/내%20드라이브/VScode/lunck_recommender/SETUP_GUIDE.md)
  구글 시트, 서비스 계정, GitHub Secrets 설정 가이드
- [WORKLOG.md](/G:/내%20드라이브/VScode/lunck_recommender/WORKLOG.md)
  작업 메모
- [CHANGELOG.md](/G:/내%20드라이브/VScode/lunck_recommender/CHANGELOG.md)
  변경 히스토리

## 동작 방식

1. GitHub Actions가 매일 오전 9시(KST)에 실행됩니다.
2. Google Sheets의 `config`, `visits` 시트를 읽습니다.
3. 기준 주소를 카카오 API로 좌표 변환하고 반경 1.5km 식당을 조회합니다.
4. 결과를 Google Sheets `restaurants` 시트에 다시 반영합니다.
5. 날씨와 방문 기록을 반영해 추천 4곳을 계산합니다.
6. 결과를 `docs/data/site-data.json`으로 저장하고 커밋합니다.
7. GitHub Pages가 그 JSON을 읽어 홈페이지를 보여줍니다.

## 빠른 체크리스트

1. GitHub Pages를 `master /docs` 로 설정
2. GitHub Secrets 3개 등록
3. Google Sheets에 서비스 계정 공유
4. `Actions > Update Pages Data` 수동 실행
5. `docs/data/site-data.json` 갱신 확인

## GitHub Secrets

- `KAKAO_REST_API_KEY`
- `GOOGLE_SHEETS_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

자세한 등록 예시는 [SETUP_GUIDE.md](/G:/내%20드라이브/VScode/lunck_recommender/SETUP_GUIDE.md)에 정리해 두었습니다.

## GitHub Pages 설정

`Settings > Pages`

- `Source`: `Deploy from a branch`
- `Branch`: `master`
- `Folder`: `/docs`

## 참고

- 설정 영역은 메인 타이틀 바로 아래에 배치되어 있습니다.
- Pages는 정적 사이트라 Python 서버 없이 바로 열립니다.
- `docs/config.js` 의 `window.LUNCH_SHEET_URL` 에 실제 시트 URL을 넣으면 `구글 시트 열기` 버튼이 활성화됩니다.
