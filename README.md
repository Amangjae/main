# 점심 추천

이 프로젝트는 GitHub Pages에서 바로 열리는 점심 추천 홈페이지입니다.

쉽게 말하면:

- 화면은 GitHub 홈페이지처럼 바로 열립니다.
- 식당 정보는 Google Sheets와 Kakao API를 이용해 갱신됩니다.
- 추천 결과는 GitHub Pages 화면에 보여집니다.

## 이 프로젝트가 하는 일

1. 기준 주소 주변의 식당을 찾습니다.
2. 오늘 날씨를 반영합니다.
3. 방문 기록을 반영합니다.
4. 점심 추천 4곳을 보여줍니다.

## 현재 구조

- `docs/`
  실제 홈페이지 화면 파일이 들어 있습니다.
- `docs/data/site-data.json`
  홈페이지가 읽는 데이터 파일입니다.
- `.github/workflows/update-pages-data.yml`
  GitHub가 자동으로 데이터를 다시 만드는 설정 파일입니다.
- `scripts/build_pages_data.py`
  Google Sheets, 날씨, 식당 정보를 합쳐서 홈페이지용 데이터를 만드는 파일입니다.

## 처음 설정할 때 꼭 볼 문서

- [SETUP_GUIDE.md](/G:/내%20드라이브/VScode/lunck_recommender/SETUP_GUIDE.md)
  처음 연결하는 방법을 순서대로 적어둔 문서
- [WORKLOG.md](/G:/내%20드라이브/VScode/lunck_recommender/WORKLOG.md)
  최근에 무엇을 바꿨는지 적어둔 문서
- [CHANGELOG.md](/G:/내%20드라이브/VScode/lunck_recommender/CHANGELOG.md)
  프로젝트에 큰 변화가 있었던 기록

## 어떻게 움직이는지

1. GitHub Actions가 자동으로 실행됩니다.
2. Google Sheets에서 설정과 방문 기록을 읽습니다.
3. Kakao API로 주변 식당을 찾습니다.
4. 날씨 정보도 같이 가져옵니다.
5. 추천 결과를 계산합니다.
6. 그 결과를 GitHub Pages가 보여줍니다.

## 지금 바로 확인할 것

1. GitHub Pages가 `master /docs` 로 설정되어 있는지 확인
2. GitHub Secrets 3개가 등록되어 있는지 확인
3. Google Sheets에 서비스 계정 공유가 되어 있는지 확인
4. `Actions > Update Pages Data` 를 한 번 실행

## 필요한 GitHub Secrets

- `KAKAO_REST_API_KEY`
- `GOOGLE_SHEETS_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

설정 방법은 [SETUP_GUIDE.md](/G:/내%20드라이브/VScode/lunck_recommender/SETUP_GUIDE.md)에 자세히 적혀 있습니다.

## GitHub Pages 설정

GitHub 저장소에서 아래처럼 설정하면 됩니다.

- `Settings > Pages`
- `Source`: `Deploy from a branch`
- `Branch`: `master`
- `Folder`: `/docs`

## 화면에서 확인할 점

- `점심 추천` 제목 아래에 설정 영역이 보이면 정상입니다.
- `구글 시트 열기` 버튼이 있으면 시트 연결 화면도 준비된 상태입니다.
- 추천 카드가 2칸씩 보이면 PC 화면 기준 정상입니다.
