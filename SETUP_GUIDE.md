# Google Sheets 설정 가이드

이 문서는 "점심 추천 홈페이지를 실제로 연결하는 방법"을 아주 쉬운 순서로 적어둔 문서입니다.

## 전체 흐름 먼저 보기

이 프로젝트는 아래 순서로 움직입니다.

1. Google Sheets에 설정값과 방문 기록을 적어둡니다.
2. GitHub가 그 내용을 읽습니다.
3. 카카오 API로 주변 식당을 찾습니다.
4. 추천 결과를 만들어 GitHub Pages 화면에 보여줍니다.

즉, Google Sheets는 "간단한 데이터 보관함" 역할을 합니다.

## 1. Google Sheets 만들기

구글 시트를 새로 하나 만듭니다.

이름 예시:

`lunch_recommender_data`

그리고 시트 탭을 3개 준비합니다.

1. `config`
2. `visits`
3. `restaurants`

설명:

- `config`: 기본 설정을 적는 곳
- `visits`: 방문 기록을 적는 곳
- `restaurants`: 자동으로 채워지는 식당 목록

`restaurants`는 직접 안 적어도 됩니다.

## 2. config 시트 입력

`config` 시트에는 아래처럼 적습니다.

| key | value |
| --- | --- |
| title | 점심 추천 |
| base_address | 서울특별시 중구 을지로 16 |
| search_radius_meters | 1500 |

주의할 점:

- 첫 줄 제목은 꼭 `key`, `value`
- 주소는 실제 기준 주소를 넣으면 됩니다
- 반경은 숫자로 넣으면 됩니다

## 3. visits 시트 입력

`visits` 시트 첫 줄은 아래처럼 적습니다.

| restaurant_key | restaurant_name | visited_on | meal_type | visit_count |
| --- | --- | --- | --- | --- |

예시:

| restaurant_key | restaurant_name | visited_on | meal_type | visit_count |
| --- | --- | --- | --- | --- |
| sample-1 | 을지로국밥 | 2026-06-20 | 점심 | 2 |
| sample-6 | 을지로중화반점 | 2026-06-18 | 점심 | 1 |

뜻 설명:

- `restaurant_key`
  식당을 구분하는 이름표 같은 값입니다.
- `restaurant_name`
  화면에 보이는 식당 이름입니다.
- `visited_on`
  방문한 날짜입니다.
- `meal_type`
  보통 `점심`이라고 쓰면 됩니다.
- `visit_count`
  그날 몇 번 갔는지 적는 숫자입니다.

## 4. Google Cloud에서 서비스 계정 만들기

이 단계는 "GitHub가 Google Sheets를 읽을 수 있게 허가증을 만드는 과정"이라고 생각하면 됩니다.

순서:

1. `Google Cloud Console` 접속
2. 새 프로젝트 만들기
3. `Google Sheets API` 활성화
4. `Google Drive API` 활성화
5. `서비스 계정` 만들기
6. `JSON 키 파일` 발급받기

여기서 받은 JSON 파일은 아주 중요합니다.  
이 파일 내용이 나중에 GitHub Secret으로 들어갑니다.

## 5. Google Sheets에 서비스 계정 공유하기

JSON 파일 안에는 `client_email` 이라는 값이 있습니다.

예시:

```json
{
  "client_email": "lunch-bot@my-project.iam.gserviceaccount.com"
}
```

이 이메일 주소를 복사해서 Google Sheets의 `공유` 버튼으로 편집 권한을 줘야 합니다.

이걸 하지 않으면 GitHub가 시트를 읽지 못합니다.

## 6. GitHub Secrets 등록하기

GitHub 저장소에서 아래로 들어갑니다.

`Settings > Secrets and variables > Actions`

여기에 3개를 등록합니다.

### 1) `KAKAO_REST_API_KEY`

카카오 REST API 키를 그대로 넣습니다.

### 2) `GOOGLE_SHEETS_ID`

구글 시트 주소에서 중간 ID만 복사해서 넣습니다.

예시 주소:

```text
https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890/edit#gid=0
```

여기서 넣을 값:

```text
1AbCdEfGhIjKlMnOpQrStUvWxYz1234567890
```

### 3) `GOOGLE_SERVICE_ACCOUNT_JSON`

서비스 계정 JSON 파일 안의 내용을 통째로 복사해서 넣습니다.

예시:

```json
{"type":"service_account","project_id":"my-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"lunch-bot@my-project.iam.gserviceaccount.com","client_id":"..."}
```

## 7. GitHub Pages 켜기

GitHub 저장소에서 아래처럼 설정합니다.

`Settings > Pages`

- `Source`: `Deploy from a branch`
- `Branch`: `master`
- `Folder`: `/docs`

이렇게 하면 `docs/` 안의 파일이 실제 홈페이지로 열립니다.

## 8. 첫 실행 방법

1. Google Sheets 준비
2. 서비스 계정 만들기
3. 시트에 서비스 계정 공유
4. GitHub Secrets 등록
5. GitHub `Actions` 탭 이동
6. `Update Pages Data` 실행

정상이라면 아래가 됩니다.

- `docs/data/site-data.json` 파일이 갱신됨
- `restaurants` 시트에 식당 목록이 들어감
- GitHub Pages 화면에 추천 결과가 보임

## 9. 자주 막히는 경우

### 식당 목록이 안 들어올 때

- 카카오 API 키가 맞는지 확인
- 기준 주소가 맞는지 확인

### 시트는 있는데 데이터가 안 바뀔 때

- 서비스 계정 이메일을 시트에 공유했는지 확인
- `GOOGLE_SHEETS_ID`가 맞는지 확인

### 홈페이지는 뜨는데 내용이 오래된 것 같을 때

- GitHub Actions가 최근에 성공했는지 확인
- `docs/data/site-data.json`이 최근에 바뀌었는지 확인

## 10. 구글 시트 열기 버튼 연결

`docs/config.js` 파일에 실제 구글 시트 주소를 넣으면 됩니다.

예시:

```js
window.LUNCH_DATA_URL = "./data/site-data.json";
window.LUNCH_SHEET_URL = "https://docs.google.com/spreadsheets/d/실제시트ID/edit#gid=0";
```

그러면 홈페이지에서 `구글 시트 열기` 버튼을 눌러 바로 시트를 볼 수 있습니다.
