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


class Api2Db:
    def __init__(self):
        self._sentimentModelCache: dict[str, Any] = {}


    # 리뷰 수정 처리
    def editReview(self, req_param: dict[str, Any]) -> dict[str, Any]:
        req_map = self._to_map(req_param)
        reviewId = int(req_map.get("reviewId") or req_map.get("id") or 0)
        authorName = str(req_map.get("authorName") or req_map.get("author") or "").strip()
        content = str(req_map.get("content") or "").strip()
        # 입력값 검증
        if reviewId <= 0:
            return self._err("리뷰 ID가 올바르지 않습니다.")
        if not authorName:
            return self._err("작성자 이름이 필요합니다.")
        if not content:
            return self._err("리뷰 내용이 필요합니다.")

        client = DbClient()
        # 감성 분석 재실행
        sentimentLabel, sentimentScore = self._analyze_review_with_model(content)
        # 리뷰 DB 업데이트
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
    def _ok(self,extra: dict[str, Any] | None = None) -> dict[str, Any]:
        return ok_response(extra)


    def _err(self, message: str) -> dict[str, Any]:
        return error_response(message)


    def _to_map(self, req_param: str | dict[str, Any]) -> dict[str, Any]:
        return to_map(req_param)

    @staticmethod
    def _to_sql_text(valueData: Any) -> str:
        if valueData is None:
            return ""
        return str(valueData).strip().replace("'", "''")

    @staticmethod
    def _normalize_release_date(valueData: Any) -> str:
        textValue = "" if valueData is None else str(valueData).strip()
        digitOnly = "".join(ch for ch in textValue if ch.isdigit())
        if len(digitOnly) >= 8:
            return digitOnly[:8]
        return digitOnly

    @staticmethod
    def _make_docid_candidate() -> str:
        return f"AUTO_{secrets.token_hex(8)}"

    def _make_unique_docid(self, client: DbClient) -> str:
        for _ in range(30):
            candidateDocId = self._make_docid_candidate()
            checkSql = f"SELECT 1 FROM MOVIES WHERE docid = '{candidateDocId}' LIMIT 1"
            existRows = client.SelectSQL(checkSql)
            if not existRows:
                return candidateDocId
        raise ValueError("docid 생성에 실패했습니다.")

    @staticmethod
    def _rating_to_label(ratingValue: int) -> str:
        if ratingValue <= 2:
            return "negative"
        if ratingValue == SENTIMENT_NEUTRAL_RATING:
            return "neutral"
        return "positive"

    @staticmethod
    def _score_to_rating(scoreValue: float) -> int:
        normalizedScore = max(0.0, min(1.0, scoreValue))
        return max(SENTIMENT_MIN_RATING, min(SENTIMENT_MAX_RATING, int(normalizedScore * 5) + 1))

    @staticmethod
    def _normalize_rating(valueData: Any) -> int:
        try:
            numericValue = float(valueData)
        except (TypeError, ValueError):
            return SENTIMENT_NEUTRAL_RATING

        return max(SENTIMENT_MIN_RATING, min(SENTIMENT_MAX_RATING, int(round(numericValue))))

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

    def _get_sentiment_model(self):
        configMap = self._read_sentiment_config()
        provider = str(configMap.get("provider", "huggingface")).strip().lower()

        if provider == "ollama":
            cacheKey = "|".join(
                [
                    provider,
                    str(configMap.get("ollama_model", DEFAULT_OLLAMA_MODEL)),
                    str(configMap.get("ollama_base_url", DEFAULT_OLLAMA_BASE_URL)),
                    str(configMap.get("ollama_timeout_sec", DEFAULT_OLLAMA_TIMEOUT_SEC)),
                ]
            )
            if cacheKey not in self._sentimentModelCache:
                self._sentimentModelCache = {
                    cacheKey: OllamaSentimentModel(
                        str(configMap.get("ollama_model", DEFAULT_OLLAMA_MODEL)),
                        str(configMap.get("ollama_base_url", DEFAULT_OLLAMA_BASE_URL)),
                        int(configMap.get("ollama_timeout_sec", DEFAULT_OLLAMA_TIMEOUT_SEC)),
                    )
                }
            return self._sentimentModelCache[cacheKey]

        cacheKey = "|".join(
            [
                "huggingface",
                str(configMap.get("huggingface_model", DEFAULT_HUGGINGFACE_MODEL)),
            ]
        )
        if cacheKey not in self._sentimentModelCache:
            self._sentimentModelCache = {
                cacheKey: HuggingFaceSentimentModel(str(configMap.get("huggingface_model", DEFAULT_HUGGINGFACE_MODEL)))
            }
        return self._sentimentModelCache[cacheKey]

    def _analyze_review_with_model(self, contentText: str) -> tuple[str, int]:
        try:
            model = self._get_sentiment_model()
            resultMap = model.doAnalyzeReview(contentText)
            ratingValue = self._normalize_rating(resultMap.get("sentimentScore", SENTIMENT_NEUTRAL_RATING))
            labelValue = str(resultMap.get("sentimentLabel", self._rating_to_label(ratingValue))).strip().lower()

            if labelValue not in ["positive", "neutral", "negative"]:
                labelValue = self._rating_to_label(ratingValue)
            print(f"Analyzed review with model: label={labelValue}, score={ratingValue}")
            return self._rating_to_label(ratingValue), ratingValue
        except Exception:
            print("Failed to analyze review with model, falling back to keyword analysis.")
            return self._analyze_review(contentText)

    def recalculate_all_review_sentiments(self) -> dict[str, int]:
        client = DbClient()
        reviewRows = client.SelectSQL("SELECT reviewId, content FROM REVIEWS ORDER BY reviewId")
        if not reviewRows:
            return {"totalCount": 0, "updatedCount": 0}

        updateSqlList: list[str] = []
        for reviewRow in reviewRows:
            reviewIdValue = QS.Obj2Int(reviewRow.get("reviewId"))
            if reviewIdValue <= 0:
                continue

            contentText = str(reviewRow.get("content", "")).strip()
            sentimentLabel, sentimentScore = self._analyze_review_with_model(contentText)
            updateSqlList.append(
                "UPDATE REVIEWS SET "
                f"sentimentLabel = '{self._to_sql_text(sentimentLabel)}', "
                f"sentimentScore = {sentimentScore} "
                f"WHERE reviewId = {reviewIdValue}"
            )

        updatedCount = client.ExecuteSQLEx(updateSqlList) if updateSqlList else 0
        return {"totalCount": len(reviewRows), "updatedCount": int(updatedCount)}

    def _get_movie_by_id(self, client: DbClient, movieIdValue: int) -> dict[str, Any]:
        selectSql = f"SELECT * FROM MOVIES WHERE movieId = {movieIdValue} LIMIT 1"
        rows = client.SelectSQL(selectSql)
        if not rows:
            raise ValueError("영화를 찾을 수 없습니다.")
        return rows[0]

    def _build_movie_where_clause(self, req_map: dict[str, Any]) -> str:
        titleValue = self._to_sql_text(req_map.get("TITLE") or req_map.get("title"))
        directorValue = self._to_sql_text(req_map.get("DIRECTOR") or req_map.get("director") or req_map.get("directorNm"))
        actorValue = self._to_sql_text(req_map.get("ACTOR") or req_map.get("actor") or req_map.get("actorNm"))

        releaseStartRaw = req_map.get("RELEASE_START") or req_map.get("releaseStart")
        releaseEndRaw = req_map.get("RELEASE_END") or req_map.get("releaseEnd")
        releaseStartValue = self._to_sql_text(self._normalize_release_date(releaseStartRaw))
        releaseEndValue = self._to_sql_text(self._normalize_release_date(releaseEndRaw))

        whereList: list[str] = []
        if titleValue:
            whereList.append(f"title LIKE '%{titleValue}%'")
        if directorValue:
            whereList.append(f"directorNm LIKE '%{directorValue}%'")
        if actorValue:
            whereList.append(f"actorNm LIKE '%{actorValue}%'")
        if releaseStartValue:
            whereList.append(f"repRlsDate >= '{releaseStartValue}'")
        if releaseEndValue:
            whereList.append(f"repRlsDate <= '{releaseEndValue}'")

        if not whereList:
            return ""
        return " WHERE " + " AND ".join(whereList)

    def getMovies(self, req_param):
        req_map = self._to_map(req_param)
        nstart = QS.Obj2Int(req_map.get("START"))
        ncount = QS.Obj2Int(req_map.get("COUNT"))
        
        if ncount <= 0:
            ncount = 10

        client = DbClient()
        whereClause = self._build_movie_where_clause(req_map)
        ## 개봉일 순으로 정렬하여 최신 영화부터 가져오기
        sql = f"SELECT * FROM MOVIES{whereClause} ORDER BY repRlsDate DESC LIMIT {ncount} OFFSET {nstart}"
        return  client.SelectSQL(sql)
        
    def getMoviesCount(self, req_param):
        req_map = self._to_map(req_param)
        client = DbClient()
        whereClause = self._build_movie_where_clause(req_map)
        ## 개봉일 순으로 정렬하여 최신 영화부터 가져오기
        sql = f"SELECT COUNT(*) AS count FROM MOVIES{whereClause}"
        result = client.SelectSQL(sql)
        return result[0]["count"] if result else 0

    def createMovie(self, req_param):
        req_map = self._to_map(req_param)

        client = DbClient()

        docIdValue = self._to_sql_text(req_map.get("docid"))
        if not docIdValue:
            docIdValue = self._make_unique_docid(client)

        existDocSql = f"SELECT 1 FROM MOVIES WHERE docid = '{docIdValue}' LIMIT 1"
        existDocRows = client.SelectSQL(existDocSql)
        if existDocRows:
            raise ValueError("이미 존재하는 docid 입니다.")

        titleValue = self._to_sql_text(req_map.get("title"))
        releaseDateRaw = req_map.get("releaseDate") or req_map.get("repRlsDate")
        repRlsDateRaw = req_map.get("repRlsDate") or releaseDateRaw
        releaseDateValue = self._to_sql_text(self._normalize_release_date(releaseDateRaw))
        repRlsDateValue = self._to_sql_text(self._normalize_release_date(repRlsDateRaw))
        directorValue = self._to_sql_text(req_map.get("directorNm"))
        actorValue = self._to_sql_text(req_map.get("actorNm"))
        genreValue = self._to_sql_text(req_map.get("genre") or req_map.get("genreNm"))
        posterUrlValue = self._to_sql_text(req_map.get("posterUrl"))

        if not titleValue:
            raise ValueError("title은 필수입니다.")

        insertSql = (
            "INSERT INTO MOVIES "
            "(docid, title, directorNm, actorNm, genre, posterUrl, releaseDate, repRlsDate) "
            f"VALUES ('{docIdValue}', '{titleValue}', '{directorValue}', '{actorValue}', "
            f"'{genreValue}', '{posterUrlValue}', '{releaseDateValue}', '{repRlsDateValue}')"
        )
        client.ExecuteSQL(insertSql)

        selectSql = f"SELECT * FROM MOVIES WHERE docid = '{docIdValue}' ORDER BY movieId DESC LIMIT 1"

        createdRows = client.SelectSQL(selectSql)
        return createdRows[0] if createdRows else {}

    def deleteMovie(self, req_param):
        req_map = self._to_map(req_param)
        movieIdValue = QS.Obj2Int(req_map.get("movieId"))
        if movieIdValue <= 0:
            raise ValueError("movieId는 필수입니다.")

        client = DbClient()
        self._get_movie_by_id(client, movieIdValue)

        countMap: dict[str, Any] = {}
        deleteReviewSql = f"DELETE FROM REVIEWS WHERE movieId = {movieIdValue}"
        client.ExecuteSQLEx(deleteReviewSql, {})
        deleteMovieSql = f"DELETE FROM MOVIES WHERE movieId = {movieIdValue}"
        client.ExecuteSQLEx(deleteMovieSql, countMap)
        return int(countMap.get("executeCount", 0)) > 0

    def updateMovie(self, req_param):
        req_map = self._to_map(req_param)
        movieIdValue = QS.Obj2Int(req_map.get("movieId"))
        if movieIdValue <= 0:
            raise ValueError("movieId는 필수입니다.")

        client = DbClient()
        currentRow = self._get_movie_by_id(client, movieIdValue)

        titleValue = self._to_sql_text(req_map.get("title"))
        if not titleValue:
            raise ValueError("title은 필수입니다.")

        releaseDateRaw = req_map.get("releaseDate") or req_map.get("repRlsDate") or currentRow.get("releaseDate")
        repRlsDateRaw = req_map.get("repRlsDate") or releaseDateRaw or currentRow.get("repRlsDate")
        releaseDateValue = self._to_sql_text(self._normalize_release_date(releaseDateRaw))
        repRlsDateValue = self._to_sql_text(self._normalize_release_date(repRlsDateRaw))
        directorValue = self._to_sql_text(req_map.get("directorNm"))
        actorValue = self._to_sql_text(req_map.get("actorNm"))
        genreValue = self._to_sql_text(req_map.get("genre") or req_map.get("genreNm"))
        posterUrlValue = self._to_sql_text(req_map.get("posterUrl"))

        updateSql = (
            "UPDATE MOVIES SET "
            f"title = '{titleValue}', "
            f"directorNm = '{directorValue}', "
            f"actorNm = '{actorValue}', "
            f"genre = '{genreValue}', "
            f"posterUrl = '{posterUrlValue}', "
            f"releaseDate = '{releaseDateValue}', "
            f"repRlsDate = '{repRlsDateValue}' "
            f"WHERE movieId = {movieIdValue}"
        )
        countMap: dict[str, Any] = {}
        client.ExecuteSQLEx(updateSql, countMap)
        if int(countMap.get("executeCount", 0)) <= 0:
            raise ValueError("영화 수정에 실패했습니다.")

        return self._get_movie_by_id(client, movieIdValue)

    def createReview(self, req_param):
        req_map = self._to_map(req_param)
        movieIdValue = QS.Obj2Int(req_map.get("movieId"))
        if movieIdValue <= 0:
            raise ValueError("movieId는 필수입니다.")

        authorNameRaw = req_map.get("authorName")
        contentRaw = req_map.get("content")
        authorNameValue = self._to_sql_text(authorNameRaw)
        contentValue = self._to_sql_text(contentRaw)
        if not authorNameValue:
            raise ValueError("authorName은 필수입니다.")
        if not contentValue:
            raise ValueError("content는 필수입니다.")

        client = DbClient()
        self._get_movie_by_id(client, movieIdValue)

        sentimentLabel, sentimentScore = self._analyze_review_with_model(str(contentRaw or "").strip())
        insertSql = (
            "INSERT INTO REVIEWS "
            "(movieId, authorName, content, sentimentLabel, sentimentScore, createdAt) "
            f"VALUES ({movieIdValue}, '{authorNameValue}', '{contentValue}', '{sentimentLabel}', {sentimentScore}, datetime('now', 'localtime'))"
        )
        client.ExecuteSQL(insertSql)

        selectSql = (
            "SELECT reviewId, movieId, authorName, content, sentimentLabel, CAST(sentimentScore AS INTEGER) AS sentimentScore, "
            "COALESCE(createdAt, '') AS createdAt "
            f"FROM REVIEWS WHERE movieId = {movieIdValue} ORDER BY reviewId DESC LIMIT 1"
        )
        reviewRows = client.SelectSQL(selectSql)
        return reviewRows[0] if reviewRows else {}

    def getReviews(self, req_param):
        req_map = self._to_map(req_param)
        movieIdValue = QS.Obj2Int(req_map.get("movieId"))
        if movieIdValue <= 0:
            raise ValueError("movieId는 필수입니다.")

        client = DbClient()
        self._get_movie_by_id(client, movieIdValue)
        selectSql = (
            "SELECT reviewId, movieId, authorName, content, sentimentLabel, CAST(sentimentScore AS INTEGER) AS sentimentScore, "
            "COALESCE(createdAt, '') AS createdAt "
            f"FROM REVIEWS WHERE movieId = {movieIdValue} ORDER BY reviewId DESC"
        )
        return client.SelectSQL(selectSql)

    def _build_review_where_clause(self, req_map: dict[str, Any]) -> str:
        movieTitleValue = self._to_sql_text(req_map.get("MOVIE_TITLE") or req_map.get("movieTitle") or req_map.get("title"))
        authorNameValue = self._to_sql_text(req_map.get("AUTHOR_NAME") or req_map.get("authorName") or req_map.get("author"))
        contentValue = self._to_sql_text(req_map.get("CONTENT") or req_map.get("content"))
        sentimentLabelValue = self._to_sql_text(req_map.get("SENTIMENT_LABEL") or req_map.get("sentimentLabel"))
        sentimentScoreValue = self._to_sql_text(req_map.get("SENTIMENT_SCORE") or req_map.get("sentimentScore"))
        createdStartValue = self._to_sql_text(req_map.get("CREATED_START") or req_map.get("createdStart"))
        createdEndValue = self._to_sql_text(req_map.get("CREATED_END") or req_map.get("createdEnd"))

        whereList: list[str] = []
        if movieTitleValue:
            whereList.append(f"m.title LIKE '%{movieTitleValue}%'")
        if authorNameValue:
            whereList.append(f"r.authorName LIKE '%{authorNameValue}%'")
        if contentValue:
            whereList.append(f"r.content LIKE '%{contentValue}%'")
        if sentimentLabelValue and sentimentLabelValue.lower() != "all":
            whereList.append(f"r.sentimentLabel = '{sentimentLabelValue}'")
        if sentimentScoreValue and sentimentScoreValue.lower() != "all":
            whereList.append(f"CAST(r.sentimentScore AS INTEGER) = CAST('{sentimentScoreValue}' AS INTEGER)")
        if createdStartValue:
            whereList.append(f"r.createdAt >= '{createdStartValue} 00:00:00'")
        if createdEndValue:
            whereList.append(f"r.createdAt <= '{createdEndValue} 23:59:59'")

        if not whereList:
            return ""
        return " WHERE " + " AND ".join(whereList)

    def getAllReviews(self, req_param):
        req_map = self._to_map(req_param)
        nstart = QS.Obj2Int(req_map.get("START"))
        ncount = QS.Obj2Int(req_map.get("COUNT"))
        if ncount <= 0:
            ncount = 10

        whereClause = self._build_review_where_clause(req_map)
        client = DbClient()
        selectSql = (
            "SELECT r.reviewId, r.movieId, m.title AS movieTitle, "
            "r.authorName, r.content, r.sentimentLabel, CAST(r.sentimentScore AS INTEGER) AS sentimentScore, "
            "COALESCE(r.createdAt, '') AS createdAt "
            "FROM REVIEWS r "
            "LEFT JOIN MOVIES m ON r.movieId = m.movieId "
            f"{whereClause} "
            f"ORDER BY r.reviewId DESC LIMIT {ncount} OFFSET {nstart}"
        )
        return client.SelectSQL(selectSql)

    def getAllReviewsCount(self, req_param):
        req_map = self._to_map(req_param)
        whereClause = self._build_review_where_clause(req_map)
        client = DbClient()
        selectSql = f"SELECT COUNT(*) AS count FROM REVIEWS r LEFT JOIN MOVIES m ON r.movieId = m.movieId{whereClause}"
        result = client.SelectSQL(selectSql)
        return result[0]["count"] if result else 0

    def deleteReview(self, req_param):
        req_map = self._to_map(req_param)
        reviewIdValue = QS.Obj2Int(req_map.get("reviewId"))
        if reviewIdValue <= 0:
            raise ValueError("reviewId는 필수입니다.")

        client = DbClient()
        countMap: dict[str, Any] = {}
        deleteSql = f"DELETE FROM REVIEWS WHERE reviewId = {reviewIdValue}"
        client.ExecuteSQLEx(deleteSql, countMap)
        return int(countMap.get("executeCount", 0)) > 0

    def save_request(self, request_data):
        # Save the request data to the database
        self.db.save(request_data)

    def get_requests(self, filter_criteria=None):
        # Retrieve requests from the database based on filter criteria
        return self.db.get(filter_criteria)