from __future__ import annotations

import configparser
import secrets
from pathlib import Path
from typing import Any

from backend.db.dbclient import DbClient
from backend.models.huggingface_model import HuggingFaceSentimentModel
from backend.models.ollama_model import OllamaSentimentModel
from common.defines import (
    DEFAULT_HUGGINGFACE_MODEL,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_OLLAMA_TIMEOUT_SEC,
    SENTIMENT_MAX_RATING,
    SENTIMENT_MIN_RATING,
    SENTIMENT_NEGATIVE_KEYWORDS,
    SENTIMENT_NEUTRAL_RATING,
    SENTIMENT_POSITIVE_KEYWORDS,
)
from common.util import QS, error_response, ok_response, to_map


# API 요청을 처리하고 DB와 연동하는 비즈니스 로직 클래스
class Api2Db:
    def __init__(self):
        # 감성 분석 모델 인스턴스 캐시
        self._sentimentModelCache: dict[str, Any] = {}

    # 리뷰 수정 처리 (감성 분석 재실행 포함)
    def editReview(self, req_param: dict[str, Any]) -> dict[str, Any]:
        req_map = self._to_map(req_param)
        reviewId = int(req_map.get("reviewId") or req_map.get("id") or 0)
        authorName = str(req_map.get("authorName") or req_map.get("author") or "").strip()
        content = str(req_map.get("content") or "").strip()
        
        # 필수 인자 검증
        if reviewId <= 0:
            return self._err("리뷰 ID가 올바르지 않습니다.")
        if not authorName:
            return self._err("작성자 이름이 필요합니다.")
        if not content:
            return self._err("리뷰 내용이 필요합니다.")

        client = DbClient()
        # 내용 변경에 따른 감성 분석 다시 수행
        sentimentLabel, sentimentScore = self._analyze_review_with_model(content)
        
        # 리뷰 정보 업데이트 쿼리 실행
        updateSql = (
            "UPDATE REVIEWS SET "
            f"authorName = '{self._to_sql_text(authorName)}', "
            f"content = '{self._to_sql_text(content)}', "
            f"sentimentLabel = '{self._to_sql_text(sentimentLabel)}', "
            f"sentimentScore = {sentimentScore} "
            f"WHERE reviewId = {reviewId}"
        )
        updated = client.ExecuteSQL(updateSql)
        if updated:
            return self._ok({"reviewId": reviewId})
        return self._err("리뷰 수정에 실패했습니다.")

    # 성공 응답 생성 유틸
    def _ok(self,extra: dict[str, Any] | None = None) -> dict[str, Any]:
        return ok_response(extra)

    # 에러 응답 생성 유틸
    def _err(self, message: str) -> dict[str, Any]:
        return error_response(message)

    # 요청 파라미터를 맵으로 변환
    def _to_map(self, req_param: str | dict[str, Any]) -> dict[str, Any]:
        return to_map(req_param)

    # SQL 인젝션 방지를 위한 텍스트 이스케이프 (홑따옴표 처리)
    @staticmethod
    def _to_sql_text(valueData: Any) -> str:
        if valueData is None:
            return ""
        return str(valueData).strip().replace("'", "''")

    # 개봉일 포맷 정규화 (숫자만 추출하여 8자리로 절삭)
    @staticmethod
    def _normalize_release_date(valueData: Any) -> str:
        textValue = "" if valueData is None else str(valueData).strip()
        digitOnly = "".join(ch for ch in textValue if ch.isdigit())
        if len(digitOnly) >= 8:
            return digitOnly[:8]
        return digitOnly

    # 자동 생성용 docid 후보 문자열 생성
    @staticmethod
    def _make_docid_candidate() -> str:
        return f"AUTO_{secrets.token_hex(8)}"

    # 중복되지 않는 고유 docid 생성 (최대 30회 시도)
    def _make_unique_docid(self, client: DbClient) -> str:
        for _ in range(30):
            candidateDocId = self._make_docid_candidate()
            checkSql = f"SELECT 1 FROM MOVIES WHERE docid = '{candidateDocId}' LIMIT 1"
            existRows = client.SelectSQL(checkSql)
            if not existRows:
                return candidateDocId
        raise ValueError("docid 생성에 실패했습니다.")

    # 별점 점수를 기반으로 감성 라벨 결정
    @staticmethod
    def _rating_to_label(ratingValue: int) -> str:
        if ratingValue <= 2:
            return "negative"
        if ratingValue == SENTIMENT_NEUTRAL_RATING:
            return "neutral"
        return "positive"

    # 0~1 사이 소수점 스코어를 1~5 별점으로 변환
    @staticmethod
    def _score_to_rating(scoreValue: float) -> int:
        normalizedScore = max(0.0, min(1.0, scoreValue))
        return max(SENTIMENT_MIN_RATING, min(SENTIMENT_MAX_RATING, int(normalizedScore * 5) + 1))

    # 숫자형 데이터를 정해진 별점 범위(1~5) 내 정수로 보정
    @staticmethod
    def _normalize_rating(valueData: Any) -> int:
        try:
            numericValue = float(valueData)
        except (TypeError, ValueError):
            return SENTIMENT_NEUTRAL_RATING
        return max(SENTIMENT_MIN_RATING, min(SENTIMENT_MAX_RATING, int(round(numericValue))))

    # 키워드 기반 단순 감성 분석 (AI 모델 실패 시 Fallback용)
    def _analyze_review(self, contentText: str) -> tuple[str, int]:
        normalizedText = contentText.strip()
        positiveCount = sum(1 for keyword in SENTIMENT_POSITIVE_KEYWORDS if keyword in normalizedText)
        negativeCount = sum(1 for keyword in SENTIMENT_NEGATIVE_KEYWORDS if keyword in normalizedText)

        if positiveCount > negativeCount:
            ratingValue = min(SENTIMENT_MAX_RATING, SENTIMENT_NEUTRAL_RATING + positiveCount)
            return self._rating_to_label(ratingValue), ratingValue
        if negativeCount > positiveCount:
            ratingValue = max(SENTIMENT_MIN_RATING, SENTIMENT_NEUTRAL_RATING - negativeCount)
            return self._rating_to_label(ratingValue), ratingValue
        return "neutral", SENTIMENT_NEUTRAL_RATING

    # m18.ini 설정 파일에서 감성 분석 모델 설정 로드
    @staticmethod
    def _read_sentiment_config() -> dict[str, Any]:
        projectRootDir = Path(__file__).resolve().parent.parent
        iniPath = projectRootDir / "common" / "m18.ini"

        configData = configparser.ConfigParser()
        configData.read(iniPath, encoding="utf-8")

        provider = configData.get("sentiment", "usemodel", fallback="huggingface").strip().lower()
        hfModelName = configData.get("huggingface", "huggingface_model", fallback=DEFAULT_HUGGINGFACE_MODEL).strip()
        ollamaModelName = configData.get("ollama", "ollama_model", fallback=DEFAULT_OLLAMA_MODEL).strip()
        ollamaBaseUrl = configData.get("ollama", "ollama_base_url", fallback=DEFAULT_OLLAMA_BASE_URL).strip()
        ollamaTimeoutSec = configData.getint("ollama", "ollama_timeout_sec", fallback=DEFAULT_OLLAMA_TIMEOUT_SEC)

        return {
            "provider": provider,
            "huggingface_model": hfModelName or DEFAULT_HUGGINGFACE_MODEL,
            "ollama_model": ollamaModelName or DEFAULT_OLLAMA_MODEL,
            "ollama_base_url": ollamaBaseUrl or DEFAULT_OLLAMA_BASE_URL,
            "ollama_timeout_sec": ollamaTimeoutSec,
        }

    # 설정에 맞는 감성 분석 모델 인스턴스 가져오기 (싱글톤 패턴 유사)
    def _get_sentiment_model(self):
        configMap = self._read_sentiment_config()
        provider = str(configMap.get("provider", "huggingface")).strip().lower()

        if provider == "ollama":
            cacheKey = "|".join([provider, str(configMap.get("ollama_model")), str(configMap.get("ollama_base_url"))])
            if cacheKey not in self._sentimentModelCache:
                self._sentimentModelCache[cacheKey] = OllamaSentimentModel(
                    str(configMap.get("ollama_model")),
                    str(configMap.get("ollama_base_url")),
                    int(configMap.get("ollama_timeout_sec")),
                )
            return self._sentimentModelCache[cacheKey]

        cacheKey = "|".join(["huggingface", str(configMap.get("huggingface_model"))])
        if cacheKey not in self._sentimentModelCache:
            self._sentimentModelCache[cacheKey] = HuggingFaceSentimentModel(str(configMap.get("huggingface_model")))
        return self._sentimentModelCache[cacheKey]

    # AI 모델을 사용한 감성 분석 실행 (실패 시 키워드 분석으로 전환)
    def _analyze_review_with_model(self, contentText: str) -> tuple[str, int]:
        try:
            model = self._get_sentiment_model()
            resultMap = model.doAnalyzeReview(contentText)
            ratingValue = self._normalize_rating(resultMap.get("sentimentScore", SENTIMENT_NEUTRAL_RATING))
            labelValue = str(resultMap.get("sentimentLabel", self._rating_to_label(ratingValue))).strip().lower()

            if labelValue not in ["positive", "neutral", "negative"]:
                labelValue = self._rating_to_label(ratingValue)
            return labelValue, ratingValue
        except Exception:
            return self._analyze_review(contentText)

    # 기존 모든 리뷰의 감성 분석 결과 재계산 및 업데이트
    def recalculate_all_review_sentiments(self) -> dict[str, int]:
        client = DbClient()
        reviewRows = client.SelectSQL("SELECT reviewId, content FROM REVIEWS ORDER BY reviewId")
        if not reviewRows:
            return {"totalCount": 0, "updatedCount": 0}

        updateSqlList: list[str] = []
        for reviewRow in reviewRows:
            reviewIdValue = QS.Obj2Int(reviewRow.get("reviewId"))
            if reviewIdValue <= 0: continue
            contentText = str(reviewRow.get("content", "")).strip()
            label, score = self._analyze_review_with_model(contentText)
            updateSqlList.append(f"UPDATE REVIEWS SET sentimentLabel='{label}', sentimentScore={score} WHERE reviewId={reviewIdValue}")

        updatedCount = client.ExecuteSQLEx(updateSqlList) if updateSqlList else 0
        return {"totalCount": len(reviewRows), "updatedCount": int(updatedCount)}

    # ID로 단건 영화 정보 조회
    def _get_movie_by_id(self, client: DbClient, movieIdValue: int) -> dict[str, Any]:
        selectSql = f"SELECT * FROM MOVIES WHERE movieId = {movieIdValue} LIMIT 1"
        rows = client.SelectSQL(selectSql)
        if not rows:
            raise ValueError("영화를 찾을 수 없습니다.")
        return rows[0]

    # 영화 검색을 위한 WHERE 절 생성 로직
    def _build_movie_where_clause(self, req_map: dict[str, Any]) -> str:
        title = self._to_sql_text(req_map.get("TITLE") or req_map.get("title"))
        director = self._to_sql_text(req_map.get("DIRECTOR") or req_map.get("director") or req_map.get("directorNm"))
        actor = self._to_sql_text(req_map.get("ACTOR") or req_map.get("actor") or req_map.get("actorNm"))
        relStart = self._to_sql_text(self._normalize_release_date(req_map.get("RELEASE_START") or req_map.get("releaseStart")))
        relEnd = self._to_sql_text(self._normalize_release_date(req_map.get("RELEASE_END") or req_map.get("releaseEnd")))

        whereList = []
        if title: whereList.append(f"title LIKE '%{title}%'")
        if director: whereList.append(f"directorNm LIKE '%{director}%'")
        if actor: whereList.append(f"actorNm LIKE '%{actor}%'")
        if relStart: whereList.append(f"repRlsDate >= '{relStart}'")
        if relEnd: whereList.append(f"repRlsDate <= '{relEnd}'")

        return " WHERE " + " AND ".join(whereList) if whereList else ""

    # 영화 목록 조회 (페이징 지원)
    def getMovies(self, req_param):
        req_map = self._to_map(req_param)
        nstart = QS.Obj2Int(req_map.get("START"))
        ncount = QS.Obj2Int(req_map.get("COUNT")) or 10
        client = DbClient()
        whereClause = self._build_movie_where_clause(req_map)
        sql = f"SELECT * FROM MOVIES{whereClause} ORDER BY repRlsDate DESC LIMIT {ncount} OFFSET {nstart}"
        return client.SelectSQL(sql)
        
    # 검색 조건에 맞는 영화 총 개수 확인
    def getMoviesCount(self, req_param):
        req_map = self._to_map(req_param)
        client = DbClient()
        whereClause = self._build_movie_where_clause(req_map)
        sql = f"SELECT COUNT(*) AS count FROM MOVIES{whereClause}"
        result = client.SelectSQL(sql)
        return result[0]["count"] if result else 0

    # 신규 영화 등록
    def createMovie(self, req_param):
        req_map = self._to_map(req_param)
        client = DbClient()
        docId = self._to_sql_text(req_map.get("docid")) or self._make_unique_docid(client)
        
        title = self._to_sql_text(req_map.get("title"))
        if not title: raise ValueError("title은 필수입니다.")

        relDate = self._to_sql_text(self._normalize_release_date(req_map.get("releaseDate") or req_map.get("repRlsDate")))
        dirNm = self._to_sql_text(req_map.get("directorNm"))
        actNm = self._to_sql_text(req_map.get("actorNm"))
        genre = self._to_sql_text(req_map.get("genre") or req_map.get("genreNm"))
        poster = self._to_sql_text(req_map.get("posterUrl"))

        insertSql = (
            "INSERT INTO MOVIES (docid, title, directorNm, actorNm, genre, posterUrl, releaseDate, repRlsDate) "
            f"VALUES ('{docId}', '{title}', '{dirNm}', '{actNm}', '{genre}', '{poster}', '{relDate}', '{relDate}')"
        )
        client.ExecuteSQL(insertSql)
        created = client.SelectSQL(f"SELECT * FROM MOVIES WHERE docid = '{docId}' LIMIT 1")
        return created[0] if created else {}

    # 영화 삭제 (연관 리뷰도 함께 삭제)
    def deleteMovie(self, req_param):
        req_map = self._to_map(req_param)
        movieId = QS.Obj2Int(req_map.get("movieId"))
        if movieId <= 0: raise ValueError("movieId는 필수입니다.")
        client = DbClient()
        client.ExecuteSQL(f"DELETE FROM REVIEWS WHERE movieId = {movieId}")
        countMap = {}
        client.ExecuteSQLEx(f"DELETE FROM MOVIES WHERE movieId = {movieId}", countMap)
        return int(countMap.get("executeCount", 0)) > 0

    # 영화 정보 업데이트
    def updateMovie(self, req_param):
        req_map = self._to_map(req_param)
        movieId = QS.Obj2Int(req_map.get("movieId"))
        if movieId <= 0: raise ValueError("movieId는 필수입니다.")
        client = DbClient()
        currentRow = self._get_movie_by_id(client, movieId)

        title = self._to_sql_text(req_map.get("title"))
        if not title: raise ValueError("title은 필수입니다.")

        relDate = self._to_sql_text(self._normalize_release_date(req_map.get("releaseDate") or req_map.get("repRlsDate") or currentRow.get("releaseDate")))
        dirNm = self._to_sql_text(req_map.get("directorNm"))
        actNm = self._to_sql_text(req_map.get("actorNm"))
        genre = self._to_sql_text(req_map.get("genre"))
        poster = self._to_sql_text(req_map.get("posterUrl"))

        updateSql = (
            "UPDATE MOVIES SET "
            f"title='{title}', directorNm='{dirNm}', actorNm='{actNm}', genre='{genre}', "
            f"posterUrl='{poster}', releaseDate='{relDate}', repRlsDate='{relDate}' WHERE movieId={movieId}"
        )
        countMap = {}
        client.ExecuteSQLEx(updateSql, countMap)
        return self._get_movie_by_id(client, movieId)

    # 신규 리뷰 등록 및 자동 감성 분석
    def createReview(self, req_param):
        req_map = self._to_map(req_param)
        movieId = QS.Obj2Int(req_map.get("movieId"))
        author = self._to_sql_text(req_map.get("authorName"))
        content = self._to_sql_text(req_map.get("content"))
        if not author or not content: raise ValueError("작성자와 내용은 필수입니다.")

        client = DbClient()
        self._get_movie_by_id(client, movieId) # 영화 존재 확인
        label, score = self._analyze_review_with_model(str(req_map.get("content")).strip())
        
        insertSql = (
            "INSERT INTO REVIEWS (movieId, authorName, content, sentimentLabel, sentimentScore, createdAt) "
            f"VALUES ({movieId}, '{author}', '{content}', '{label}', {score}, datetime('now', 'localtime'))"
        )
        client.ExecuteSQL(insertSql)
        created = client.SelectSQL(f"SELECT * FROM REVIEWS WHERE movieId={movieId} ORDER BY reviewId DESC LIMIT 1")
        return created[0] if created else {}

    # 특정 영화의 리뷰 목록 조회
    def getReviews(self, req_param):
        req_map = self._to_map(req_param)
        movieId = QS.Obj2Int(req_map.get("movieId"))
        client = DbClient()
        sql = f"SELECT *, CAST(sentimentScore AS INTEGER) AS sentimentScore FROM REVIEWS WHERE movieId={movieId} ORDER BY reviewId DESC"
        return client.SelectSQL(sql)

    # 전체 리뷰 조회를 위한 WHERE 절 생성
    def _build_review_where_clause(self, req_map: dict[str, Any]) -> str:
        mTitle = self._to_sql_text(req_map.get("MOVIE_TITLE") or req_map.get("movieTitle"))
        author = self._to_sql_text(req_map.get("AUTHOR_NAME") or req_map.get("authorName"))
        content = self._to_sql_text(req_map.get("CONTENT") or req_map.get("content"))
        label = self._to_sql_text(req_map.get("SENTIMENT_LABEL") or req_map.get("sentimentLabel"))
        score = self._to_sql_text(req_map.get("SENTIMENT_SCORE") or req_map.get("sentimentScore"))
        startD = self._to_sql_text(req_map.get("CREATED_START") or req_map.get("createdStart"))
        endD = self._to_sql_text(req_map.get("CREATED_END") or req_map.get("createdEnd"))

        whereList = []
        if mTitle: whereList.append(f"m.title LIKE '%{mTitle}%'")
        if author: whereList.append(f"r.authorName LIKE '%{author}%'")
        if content: whereList.append(f"r.content LIKE '%{content}%'")
        if label and label.lower() != "all": whereList.append(f"r.sentimentLabel = '{label}'")
        if score and score.lower() != "all": whereList.append(f"CAST(r.sentimentScore AS INTEGER) = {score}")
        if startD: whereList.append(f"r.createdAt >= '{startD} 00:00:00'")
        if endD: whereList.append(f"r.createdAt <= '{endD} 23:59:59'")

        return " WHERE " + " AND ".join(whereList) if whereList else ""

    # 모든 영화의 리뷰 통합 조회 (페이징)
    def getAllReviews(self, req_param):
        req_map = self._to_map(req_param)
        nstart = QS.Obj2Int(req_map.get("START"))
        ncount = QS.Obj2Int(req_map.get("COUNT")) or 10
        whereClause = self._build_review_where_clause(req_map)
        client = DbClient()
        sql = (
            "SELECT r.*, m.title AS movieTitle FROM REVIEWS r LEFT JOIN MOVIES m ON r.movieId = m.movieId "
            f"{whereClause} ORDER BY r.reviewId DESC LIMIT {ncount} OFFSET {nstart}"
        )
        return client.SelectSQL(sql)

    # 전체 리뷰 총 건수 조회
    def getAllReviewsCount(self, req_param):
        req_map = self._to_map(req_param)
        whereClause = self._build_review_where_clause(req_map)
        client = DbClient()
        sql = f"SELECT COUNT(*) AS count FROM REVIEWS r LEFT JOIN MOVIES m ON r.movieId = m.movieId{whereClause}"
        result = client.SelectSQL(sql)
        return result[0]["count"] if result else 0

    # 리뷰 단건 삭제
    def deleteReview(self, req_param):
        req_map = self._to_map(req_param)
        reviewId = QS.Obj2Int(req_map.get("reviewId"))
        client = DbClient()
        countMap = {}
        client.ExecuteSQLEx(f"DELETE FROM REVIEWS WHERE reviewId = {reviewId}", countMap)
        return int(countMap.get("executeCount", 0)) > 0