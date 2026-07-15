# 점심 추천

이 프로젝트는 GitHub Pages에서 바로 열리는 점심 추천 홈페이지입니다.

## 한눈에 보기

- 화면은 `docs/` 폴더의 정적 파일로 보여집니다.
- 데이터는 GitHub Actions가 만들어 `docs/data/site-data.json`에 저장합니다.
- 식당 정보는 Kakao API와 Google Sheets를 같이 사용합니다.
- 변경 기록은 `WORKLOG.md`에 계속 남깁니다.

## 주요 폴더와 파일

- `docs/`
  실제 홈페이지 화면 파일
- `docs/data/site-data.json`
  홈페이지가 읽는 데이터 파일
- `scripts/build_pages_data.py`
  Google Sheets, 날씨, 식당 정보를 모아 JSON을 만드는 스크립트
- `.github/workflows/update-pages-data.yml`
  GitHub Actions 자동 갱신 설정
- `WORKLOG.md`
  작업 내역과 다음 할 일을 쉬운 말로 적는 기록 파일

## 처음 설정하는 방법

1. Google Sheets를 만들고 `config`, `visits`, `restaurants` 탭을 준비합니다.
2. GitHub Secrets에 아래 3개를 등록합니다.
3. Google Sheets에 서비스 계정 이메일을 편집자로 공유합니다.
4. GitHub Actions에서 `Update Pages Data`를 한 번 실행합니다.

필요한 GitHub Secrets:

- `KAKAO_REST_API_KEY`
- `GOOGLE_SHEETS_ID`
- `GOOGLE_SERVICE_ACCOUNT_JSON`

## GitHub Pages 설정

GitHub 저장소에서 아래처럼 설정하면 됩니다.

- `Settings > Pages`
- `Source`: `Deploy from a branch`
- `Branch`: `master`
- `Folder`: `/docs`

## 화면에서 확인할 점

- `점심 추천` 제목 아래에 설정 영역이 보이면 정상입니다.
- `구글 시트 열기` 버튼이 보이면 시트 연결 준비가 된 상태입니다.
- 추천 카드가 PC에서는 2칸, 모바일에서는 1칸으로 보이면 정상입니다.

## 기록 규칙

앞으로 코드나 설정이 바뀌면 `WORKLOG.md`에 아래 내용을 쉬운 말로 남깁니다.

- 무엇을 바꿨는지
- 왜 바꿨는지
- 어디서 확인하면 되는지
- 다음에 무엇을 하면 되는지
