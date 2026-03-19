# Mission 18 백엔드 API 명세서 (API.md)

이 문서는 다른 클라이언트나 FE 환경에서 Mission18 서버 API에 연결하여 기능을 제어할 때 참고할 수 있도록 작성되었습니다.

#### 백엔드 기본 접속 (FastAPI)

| 환경 | 주소 | 설명 |
|---|---|---|
| Base URL (로컬) | `http://127.0.0.1:8019` | FastAPI 백엔드 서버의 기본 URL 접속 위치 (응용 시 변경 가능) |
| Swagger UI | `http://127.0.0.1:8019/docs` | 백엔드 내장 자동화 API 테스트 사이트 |

🔥 **안내**: 본 서비스의 모든 API 통신 메커니즘은 `POST` 메서드를 사용하며, 응답은 통일된 포맷(`datalist`, `datacount`, `code`, `ok`)의 JSON으로 반환됩니다.

---

### 공통 응답 (Common Response Format)

정상 응답이든 에러 응답이든 서버는 되도록 다음과 같은 기본 JSON 구조를 응답으로 내립니다:

```json
{
  "code": "OK",              // 정상이면 "OK", 에러 시 "Error"
  "ok": true,                // 내부 요청 성공 여부 (true/false)
  "message": "",             // 에러 발생 시의 원장 메시지
  "datalist": [...],         // 데이터 배열 (단건 응답의 경우는 딕셔너리가 들어갈 수도 있음)
  "datacount": 10            // `datalist`에 들어있는 데이터의 개수 또는 총 집계 카운트 결과
}
```

---

### REST API 엔드포인트 세부 명세

#### 1. 영화 목록 조회
- **URL**: `POST /accessdata/getmovies`
- **Request Body (JSON)**:
  ```json
  {
      "COUNT": "10",                // (옵션) 한 번에 불러올 한계 개수
      "START": "0",                 // (옵션) 오프셋 (페이지네이션)
      "TITLE": "영화 제목",         // (옵션) 제목 조건 필터
      "DIRECTOR": "감독 이름",      // (옵션) 감독 조건 필터
      "ACTOR": "배우 이름",         // (옵션) 배우 조건 필터
      "RELEASE_START": "YYYY-MM-DD",// (옵션) 개봉일 시작 필터
      "RELEASE_END": "YYYY-MM-DD"   // (옵션) 개봉일 종료 필터
  }
  ```
- **Response**: `datalist` 안에 영화 메타 데이터들 배열 리턴

#### 2. 영화 건수만 조회 (페이징 총량용)
- **URL**: `POST /accessdata/getmoviescount`
- **Request Body (JSON)**: `getmovies`와 동일하지만 `COUNT`, `START` 불필요. 필터만 전송.
- **Response**: `datacount` 값에 현재 조건문과 일치하는 총 영화 데이터 개수 리턴.

#### 3. 영화 등록
- **URL**: `POST /accessdata/createmovie`
- **Request Body (JSON)**:
  ```json
  {
      "docid": "",              // 고유 문서 ID 문자열
      "title": "영화 제목",     // (필수)
      "releaseDate": "YYYY-MM-DD",  
      "directorNm": "감독",
      "genre": "장르",
      "posterUrl": "포스터링크",
      "actorNm": "배우들"
  }
  ```

#### 4. 영화 정보 수정
- **URL**: `POST /accessdata/updatemovie`
- **Request Body (JSON)**:
  ```json
  {
      "movieId": 1,             // (필수) 수정하려는 목표 PK 
      "title": "수정할 영화 제목",
      "releaseDate": "YYYY-MM-DD",
      "directorNm": "새 감독",
      "actorNm": "새 배우",
      "genre": "새 장르",
      "posterUrl": "새 포스터"
  }
  ```

#### 5. 영화 삭제 (종속된 리뷰 모두 포함)
- **URL**: `POST /accessdata/deletemovie`
- **Request Body (JSON)**:
  ```json
  {
      "movieId": 1              // (필수) 삭제 대상 PK
  }
  ```

---

#### 6. 특정 영화에 종속된 감성 리뷰 리스트 확인
- **URL**: `POST /accessdata/getreviews`
- **Request Body (JSON)**:
  ```json
  {
      "movieId": 1              // (필수) 대조할 영화 PK ID 번호
  }
  ```
- **Response**: `datalist` 내부에 `sentimentLabel`, `sentimentScore`, `authorName`, `content` 등이 포함된 배열 반환

#### 7. 리뷰 등록 (이때 백그라운드 AI 평가 연동됨)
- **URL**: `POST /accessdata/createreview`
- **Request Body (JSON)**:
  ```json
  {
      "movieId": 1,             // (필수) 대상 영화 PK
      "authorName": "작성자",   // (필수) 
      "content": "이 영화 정말 재미있어요!" // (필수)
  }
  ```
- **특이사항**: 서버측에서 `content` 필드 분석 후 DB에 자동으로 AI 감성 결과 스코어/라벨을 주입해줍니다. 시간 지연이 1초 이상 생길 수 있습니다.

#### 8. 독립 리뷰 수정 (AI 재평가 방식)
- **URL**: `POST /accessdata/updatereview`
- **Request Body (JSON)**:
  ```json
  {
      "reviewId": 12,           // (필수) 고유 리뷰 PK
      "authorName": "작성자 닉수정",
      "content": "생각해보니 다시 보니 별로네요" 
  }
  ```
- **특이사항**: 내용(`content`)이 다시 백엔드로 발송되어 AI 감성 점수가 즉시 재평가 후 교체 적용됩니다. 결괏값 또한 덮어씌워집니다.

#### 9. 독립 리뷰 삭제
- **URL**: `POST /accessdata/deletereview`
- **Request Body (JSON)**:
  ```json
  {
      "reviewId": 12            // (필수) 타겟 단위 리뷰 PK
  }
  ```

#### 10. 모든 리뷰 통합 검색 및 필터링 기능
- **URL**: `POST /accessdata/getallreviews`
- **Request Body (JSON)**:
  ```json
  {
      "COUNT": "10",                // (옵션)
      "START": "0",                 // (옵션)
      "MOVIE_TITLE": "매트릭스",    // (옵션) 연관 영화 제목 기준 검색
      "AUTHOR_NAME": "홍길동",      // (옵션) 작성자 필터
      "CONTENT": "재미",            // (옵션) 리뷰 내용 필터
      "SENTIMENT_LABEL": "negative",// (옵션) 감성 검색 필터. (all, positive, neutral, negative)
      "SENTIMENT_SCORE": "1",       // (옵션) 평점 스코어 필터 (all, 1~5 정수형 값 지원)
      "CREATED_START": "YYYY-MM-DD",// (옵션) 리뷰 등록일 검색 범위 시작
      "CREATED_END": "YYYY-MM-DD"   // (옵션) 리뷰 등록일 검색 범위 종료
  }
  ```

#### 11. 통합 리뷰 건수 집계 확인 (페이징용 카운터)
- **URL**: `POST /accessdata/getallreviewscount`
- **Request Body (JSON)**: `getallreviews` 요청과 동일, 단 `COUNT` 및 `START` 값을 무시.
