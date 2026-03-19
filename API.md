#### 백엔드 접속 주소

| 구분 | 주소 | 설명 |
|---|---|---|
| Backend Base URL (로컬) | `http://127.0.0.1:8000` | FastAPI 서버 기본 접속 주소 |
| Swagger UI | `http://127.0.0.1:8000/docs` | API 테스트 및 스키마 확인 |
| ReDoc | `http://127.0.0.1:8000/redoc` | 문서형 API 명세 화면 |
| Health Check | `http://127.0.0.1:8000/health` | 서버 상태 확인 엔드포인트 |

#### REST API 주소 및 파라미터

| Method | REST API 주소 | 역할 | Path 파라미터 | Query 파라미터 | Body 파라미터(JSON) |
|---|---|---|---|---|---|
| GET | `/health` | 서버 상태 확인 | 없음 | 없음 | 없음 |
| GET | `/api/v1/movies` | 영화 전체 목록 조회 (전체 필드) | 없음 | `page`, `size` | 없음 |
| GET | `/api/v1/movies/summary` | 영화 요약 목록 조회 (프론트 목록 화면용) | 없음 | `page`, `size` | 없음 |
| POST | `/api/v1/movies` | 영화 등록 | 없음 | 없음 | 필수: `docid`, `title` / 선택: 나머지 영화 필드 |
| GET | `/api/v1/movies/{movieId}` | 영화 단건 상세 조회 | `movieId(int, 필수)` | 없음 | 없음 |
| PATCH | `/api/v1/movies/{movieId}` | 영화 정보 부분 수정 (보낸 필드만 변경) | `movieId(int, 필수)` | 없음 | 선택: 수정할 영화 필드만 전달 |
| DELETE | `/api/v1/movies/{movieId}` | 영화 삭제 (연결된 리뷰 포함) | `movieId(int, 필수)` | 없음 | 없음 |
| GET | `/api/v1/movies/{movieId}/rating` | 영화 평균 감성 점수 및 리뷰 수 조회 | `movieId(int, 필수)` | 없음 | 없음 |
| GET | `/api/v1/movies/{movieId}/reviews` | 영화에 달린 리뷰 목록 조회 | `movieId(int, 필수)` | 없음 | 없음 |
| POST | `/api/v1/movies/{movieId}/reviews` | 리뷰 등록 (자동 감성 분석 포함) | `movieId(int, 필수)` | 없음 | `authorName`, `content` |
| DELETE | `/api/v1/reviews/{reviewId}` | 리뷰 삭제 | `reviewId(int, 필수)` | 없음 | 없음 |

요약표의 파라미터는 가독성을 위해 축약 표기했습니다. 각 필드의 상세 타입/필수 여부는 아래 엔드포인트별 섹션을 참고하세요.

#### 페이지네이션 사용 예시

| 기능 | 요청 예시 |
|---|---|
| 영화 목록 1페이지(기본) | `GET /api/v1/movies` |
| 영화 목록 2페이지, 10개씩 | `GET /api/v1/movies?page=2&size=10` |

#### REST API 응답 형식 (Frontend 명세)

##### 1) GET `/health`

| HTTP 상태 | 응답 형식 | 항목 | 의미 |
|---|---|---|---|
| 200 | JSON Object | `status` | 서버 상태 (`ok`) |
| 200 | JSON Object | `service` | 서비스 이름 |

응답 예시:

```json
{
	"status": "ok",
	"service": "Mission18 Backend"
}
```

##### 2) GET `/api/v1/movies`

| HTTP 상태 | 응답 형식 | 항목 | 의미 |
|---|---|---|---|
| 200 | JSON Array | `[]` | 영화 객체 배열 |
| 200 | JSON Array | `[].<movieField>` | 아래 `Movie 객체 필드` 표 참고 |

응답 예시:

```json
[
	{
		"movieId": 1,
		"docid": "K12345",
		"title": "영화 제목",
		"genre": "드라마",
		"createdAt": "2026-03-17T10:20:30"
	}
]
```

##### 2-1) GET `/api/v1/movies/summary`

| HTTP 상태 | 응답 형식 | 항목 | 의미 |
|---|---|---|---|
| 200 | JSON Array | `[]` | 프론트 목록용 요약 영화 배열 |
| 200 | JSON Array | `[].movieId` | 영화 내부 PK |
| 200 | JSON Array | `[].docid` | KMDB 문서 고유 ID |
| 200 | JSON Array | `[].title` | 영화명 |
| 200 | JSON Array | `[].releaseDate` | 개봉일 |
| 200 | JSON Array | `[].directorNm` | 감독명 |
| 200 | JSON Array | `[].genre` | 장르 |
| 200 | JSON Array | `[].averageSentimentScore` | 평균 감성 점수 (리뷰 없으면 null) |

응답 예시:

```json
[
	{
		"movieId": 1,
		"docid": "K12345",
		"title": "육군포병학교",
		"releaseDate": "2000-01-01",
		"directorNm": "방의석",
		"genre": "군사",
		"averageSentimentScore": null
	}
]
```

##### 3) POST `/api/v1/movies`

| HTTP 상태 | 응답 형식 | 항목 | 의미 |
|---|---|---|---|
| 201 | JSON Object | `<movieField>` | 생성된 영화 객체 (`Movie 객체 필드` 표 참고) |

응답 예시:

```json
{
	"movieId": 2,
	"docid": "K67890",
	"title": "새 영화",
	"genre": "액션",
	"createdAt": "2026-03-17T10:30:00"
}
```

##### 4) GET `/api/v1/movies/{movieId}`

| HTTP 상태 | 응답 형식 | 항목 | 의미 |
|---|---|---|---|
| 200 | JSON Object | `<movieField>` | 단일 영화 객체 (`Movie 객체 필드` 표 참고) |
| 404 | JSON Object | `detail` | 에러 메시지 (`Movie not found`) |

##### 5) PATCH `/api/v1/movies/{movieId}`

> 지정한 필드만 부분 업데이트합니다. 보내지 않은 필드는 변경되지 않습니다.

| HTTP 상태 | 응답 형식 | 항목 | 의미 |
|---|---|---|---|
| 200 | JSON Object | `<movieField>` | 수정된 영화 객체 (`Movie 객체 필드` 표 참고) |
| 404 | JSON Object | `detail` | 에러 메시지 (`Movie not found`) |

요청 예시:

```json
{
	"genre": "액션",
	"plot": "수정된 줄거리 내용"
}
```

##### 6) DELETE `/api/v1/movies/{movieId}`

| HTTP 상태 | 응답 형식 | 항목 | 의미 |
|---|---|---|---|
| 204 | Empty Body | 없음 | 삭제 성공, 응답 바디 없음 |
| 404 | JSON Object | `detail` | 에러 메시지 (`Movie not found`) |

##### 7) GET `/api/v1/movies/{movieId}/rating`

| HTTP 상태 | 응답 형식 | 항목 | 의미 |
|---|---|---|---|
| 200 | JSON Object | `movieId` | 영화 내부 PK |
| 200 | JSON Object | `averageScore` | 평균 감성 점수 |
| 200 | JSON Object | `reviewCount` | 리뷰 개수 |
| 404 | JSON Object | `detail` | 에러 메시지 (`Movie not found`) |

응답 예시:

```json
{
	"movieId": 1,
	"averageScore": 0.83,
	"reviewCount": 12
}
```

##### 8) GET `/api/v1/movies/{movieId}/reviews`

| HTTP 상태 | 응답 형식 | 항목 | 의미 |
|---|---|---|---|
| 200 | JSON Array | `[]` | 리뷰 객체 배열 |
| 200 | JSON Array | `[].<reviewField>` | 아래 `Review 객체 필드` 표 참고 |
| 404 | JSON Object | `detail` | 에러 메시지 (`Movie not found`) |

##### 9) POST `/api/v1/movies/{movieId}/reviews`

| HTTP 상태 | 응답 형식 | 항목 | 의미 |
|---|---|---|---|
| 201 | JSON Object | `<reviewField>` | 생성된 리뷰 객체 (`Review 객체 필드` 표 참고) |
| 404 | JSON Object | `detail` | 에러 메시지 (`Movie not found`) |

##### 10) DELETE `/api/v1/reviews/{reviewId}`

| HTTP 상태 | 응답 형식 | 항목 | 의미 |
|---|---|---|---|
| 204 | Empty Body | 없음 | 삭제 성공, 응답 바디 없음 |
| 404 | JSON Object | `detail` | 에러 메시지 (`Review not found`) |

##### Movie 객체 필드

| 항목 | 타입 | 의미 |
|---|---|---|
| movieId | int | 영화 내부 PK (DB 자동증가) |
| collection | str/null | KMDB 결과 메타: 컬렉션명 |
| pageNo | int/null | KMDB 결과 메타: 현재 페이지 |
| numOfRows | int/null | KMDB 결과 메타: 페이지당 건수 |
| totalCount | int/null | KMDB 결과 메타: 총 검색 건수 |
| rowValue | int/null | KMDB 결과 메타: 결과 내 일련번호 |
| docid | str | KMDB 문서 고유 ID |
| kmdbMovieId | str/null | KMDB 등록ID (원본 `movieId`) |
| movieSeq | str/null | KMDB 등록SEQ |
| title | str | 영화명 |
| titleEng | str/null | 영문제명 |
| titleOrg | str/null | 원제명 |
| titleEtc | str/null | 기타제명 |
| directorNm | str/null | 감독명 |
| directorEnNm | str/null | 감독명(영문) |
| directorId | str/null | 감독등록번호 |
| actorNm | str/null | 배우명 |
| actorEnNm | str/null | 배우명(영문) |
| actorId | str/null | 배우등록번호 |
| nation | str/null | 제작국가 |
| company | str/null | 제작사 |
| prodYear | str/null | 제작년도 |
| plot | str/null | 줄거리 |
| runtime | str/null | 상영시간 |
| rating | str/null | 대표관람등급 |
| genre | str/null | 장르 |
| kmdbUrl | str/null | KMDB 상세 링크 |
| movieType | str/null | 유형구분 (원본 `type`) |
| movieUse | str/null | 용도구분 (원본 `use`) |
| episodes | str/null | 영상 내 에피소드 |
| ratedYn | str/null | 심의여부 |
| repRatDate | str/null | 대표심의일 |
| repRlsDate | str/null | 대표개봉일 |
| ratingMain | str/null | 대표심의정보 여부 |
| ratingDate | str/null | 심의일 |
| ratingNo | str/null | 심의번호 |
| ratingGrade | str/null | 관람기준 |
| releaseDate | str/null | 개봉일자 |
| keywords | str/null | 키워드 |
| posterUrl | str/null | 포스터 URL |
| stillUrl | str/null | 스틸 이미지 URL |
| staffNm | str/null | 스텝이름 |
| staffRoleGroup | str/null | 스텝크레딧명 |
| staffRole | str/null | 스텝배역 |
| staffEtc | str/null | 스텝기타 |
| staffId | str/null | 스텝등록번호 |
| vodClass | str/null | VOD 구분 |
| vodUrl | str/null | VOD URL |
| openThtr | str/null | 개봉극장 |
| screenArea | str/null | 관람지역 |
| screenCnt | str/null | 스크린수 |
| salesAcc | str/null | 누적매출액 |
| audiAcc | str/null | 누적관람인원 |
| statSouce | str/null | 출처 |
| statDate | str/null | 기준일 |
| themeSong | str/null | 주제곡 |
| soundtrack | str/null | 삽입곡 |
| fLocation | str/null | 촬영장소 |
| awards1 | str/null | 영화제 수상 내역 |
| awards2 | str/null | 기타 수상 내역 |
| regDate | str/null | 등록일 |
| modDate | str/null | 최종수정일 |
| codeNm | str/null | 외부코드명 |
| codeNo | str/null | 외부코드 |
| commCodes | str/null | 대표외부코드 |
| createdAt | datetime string | DB 생성 시각 (ISO 8601) |

##### Review 객체 필드

| 항목 | 타입 | 의미 |
|---|---|---|
| reviewId | int | 리뷰 PK |
| movieId | int | 연결된 영화 내부 PK |
| authorName | str | 작성자 이름 |
| content | str | 리뷰 본문 |
| sentimentLabel | str | 감성 라벨 |
| sentimentScore | float | 감성 점수 |
| createdAt | datetime string | 생성 시각 (ISO 8601) |

##### 공통 에러 응답 형식

| HTTP 상태 | 응답 예시 |
|---|---|
| 404 | `{ "detail": "Movie not found" }` 또는 `{ "detail": "Review not found" }` |
| 422 | `{ "detail": [...] }` (요청 파라미터/바디 유효성 검증 실패) |

#### KMDB 원본 필드명 매핑표

| KMDB 원본명 (TECH 8.3) | 저장/응답 필드명 | 비고 |
|---|---|---|
| `movieId` | `kmdbMovieId` | DB PK `movieId(int)`와 충돌 방지 |
| `type` | `movieType` | Python 예약어 회피 |
| `use` | `movieUse` | 의미 명확화 |
| `StaffNm` | `staffNm` | camelCase 소문자 통일 |
| `StaffRole` | `staffRole` | camelCase 소문자 통일 |
| `StaffEtc` | `staffEtc` | camelCase 소문자 통일 |
| `StaffId` | `staffId` | camelCase 소문자 통일 |
| `Awards1` | `awards1` | camelCase 소문자 통일 |
| `Awards2` | `awards2` | camelCase 소문자 통일 |
| `CodeNm` | `codeNm` | camelCase 소문자 통일 |
| `CodeNo` | `codeNo` | camelCase 소문자 통일 |
| `CommCodes` | `commCodes` | camelCase 소문자 통일 |
| `Result.Collection` | `collection` | 수집 메타 |
| `Result.PageNo` | `pageNo` | 수집 메타 |
| `Result.NumOfRow` | `numOfRows` | 수집 메타 |
| `Result.TotalCount` | `totalCount` | 수집 메타 |
| `Row Value` | `rowValue` | 수집 메타 |
