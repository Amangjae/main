# Google Sheets 설정 가이드

이 문서는 `점심 추천` 사이트를 GitHub Pages + Google Sheets 구조로 실제 연결하는 방법을 정리한 문서입니다.

## 1. Google Sheets 만들기

구글 시트를 하나 새로 만들고 이름은 예를 들어 `lunch_recommender_data` 로 둡니다.

필요한 시트 탭은 3개입니다.

1. `config`
2. `visits`
3. `restaurants`

`restaurants` 는 워크플로가 자동으로 채우므로 처음엔 비워도 됩니다.

## 2. config 시트 입력

`config` 시트는 아래처럼 입력합니다.

| key | value |
| --- | --- |
| title | 점심 추천 |
| base_address | 서울특별시 중구 을지로 16 |
| search_radius_meters | 1500 |

주의:
- 헤더는 반드시 `key`, `value`
- `search_radius_meters` 는 숫자 문자열로 입력

## 3. visits 시트 입력

`visits` 시트는 아래 헤더를 사용합니다.

| restaurant_key | restaurant_name | visited_on | meal_type | visit_count |
| --- | --- | --- | --- | --- |

예시:

| restaurant_key | restaurant_name | visited_on | meal_type | visit_count |
| --- | --- | --- | --- | --- |
| sample-1 | 을지로국밥 | 2026-06-20 | 점심 | 2 |
| sample-6 | 을지로중화반점 | 2026-06-18 | 점심 | 1 |

설명:
- `restaurant_key`
  샘플 데이터는 `sample-1`, `sample-2` 같은 키를 사용
  카카오 데이터는 보통 `kakao-장소ID` 형태
- `visited_on`
  `YYYY-MM-DD` 형식
- `meal_type`
  현재는 보통 `점심`
- `visit_count`
  같은 날 방문 횟수

## 4. Google Cloud 서비스 계정 만들기

1. `Google Cloud Console` 접속
2. 새 프로젝트 생성
3. `API 및 서비스 > 라이브러리`
4. `Google Sheets API` 활성화
5. `Google Drive API` 활성화
6. `API 및 서비스 > 사용자 인증 정보`
7. `서비스 계정` 생성
8. `키 추가 > JSON` 으로 키 파일 발급

이 JSON 파일 내용을 그대로 GitHub Secret에 넣게 됩니다.

## 5. 서비스 계정에 시트 공유

발급된 JSON 안에 `client_email` 값이 있습니다.

예시:

```json
{
  "client_email": "lunch-bot@my-project.iam.gserviceaccount.com"
}
```

이 이메일을 복사해서 Google Sheets의 `공유` 버튼으로 편집자 권한을 부여해야 합니다.

이걸 안 하면 워크플로가 시트를 읽지 못합니다.

## 6. GitHub Secrets 등록

저장소에서 아래 위치로 이동합니다.

`Settings > Secrets and variables > Actions`

다음 3개를 등록합니다.

### `KAKAO_REST_API_KEY`

카카오 REST API 키 문자열 그대로 입력합니다.

### `GOOGLE_SHEETS_ID`

구글 시트 URL에서 ID 부분만 넣습니다.

예시 URL:

```text
https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890/edit#gid=0
```

등록값:

```text
1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
```

### `GOOGLE_SERVICE_ACCOUNT_JSON`

서비스 계정 JSON 전체를 한 줄 문자열로 넣습니다.

예시:

```json
{"type":"service_account","project_id":"my-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"lunch-bot@my-project.iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/lunch-bot%40my-project.iam.gserviceaccount.com"}
```

## 7. GitHub Pages 설정

`Settings > Pages`

- `Source`: `Deploy from a branch`
- `Branch`: `master`
- `Folder`: `/docs`

## 8. 첫 실행 방법

1. 시트 준비
2. 서비스 계정 공유
3. GitHub Secrets 등록
4. GitHub 저장소 `Actions` 탭 이동
5. `Update Pages Data` 워크플로 선택
6. `Run workflow` 실행

정상 실행되면:

- `docs/data/site-data.json` 이 갱신됨
- `restaurants` 시트가 자동 채워짐
- GitHub Pages 화면에서 추천/날씨/방문 기록이 반영됨

## 9. 자주 막히는 지점

### 시트가 비어 있고 데이터가 안 바뀜

- 서비스 계정 이메일을 시트에 공유했는지 확인
- `GOOGLE_SHEETS_ID` 가 맞는지 확인

### 카카오 식당이 안 들어옴

- `KAKAO_REST_API_KEY` 확인
- 기준 주소가 카카오 주소 검색에서 정상 변환되는지 확인

### GitHub Pages 화면은 뜨는데 내용이 안 바뀜

- Actions 실행 성공 여부 확인
- 최신 커밋에 `docs/data/site-data.json` 변경이 포함됐는지 확인

## 10. 시트 열기 버튼 연결

`docs/config.js` 에 아래처럼 실제 시트 URL을 넣으면 됩니다.

```js
window.LUNCH_DATA_URL = "./data/site-data.json";
window.LUNCH_SHEET_URL = "https://docs.google.com/spreadsheets/d/실제시트ID/edit#gid=0";
```
