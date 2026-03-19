# 백엔드 API와의 통신을 담당하는 클라이언트 클래스
import configparser
import json
from pathlib import Path
from typing import Any
import os
import requests

class CallApi:
    # API 객체 초기화. 타임아웃 및 백엔드 접속 URL 설정
    def __init__(self, timeoutSec: int = 30):
        self.__TimeoutSec = timeoutSec
        self.__BackendUrl = self._getBackendUrl()

    # 리뷰 수정 API 호출
    def editReview(self, reviewId: int, authorName: str, content: str) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/updatereview"
        requestBody = {
            "reviewId": reviewId,
            "authorName": authorName,
            "content": content,
        }
        return self._postData(apiUrl, requestBody, "리뷰 수정 실패")

    # API 응답 데이터를 리스트 형식으로 정규화
    @staticmethod
    def _normalizeDataList(rawData: object) -> list[object] | None:
        if isinstance(rawData, list): return rawData
        if isinstance(rawData, dict):
            keys = list(rawData.keys())
            # 키가 숫자인 경우 정렬하여 리스트화
            if all(str(k).isdigit() for k in keys):
                return [v for _, v in sorted(rawData.items(), key=lambda x: int(str(x[0])))]
            return list(rawData.values())
        if isinstance(rawData, str):
            try: return CallApi._normalizeDataList(json.loads(rawData))
            except ValueError: return None
        return None

    # INI 파일에서 백엔드 서버 URL 정보 조회
    def _getBackendUrl(self) -> str:
        projectRootDir = Path(__file__).resolve().parent.parent
        iniPath = os.path.join(projectRootDir, "common", "m18.ini")
        config = configparser.ConfigParser()
        config.read(iniPath, encoding="utf-8")

        url = ""
        if config.has_section("aipurl"): url = config.get("aipurl", "backend", fallback="").strip()
        if not url and config.has_section("apiurl"): url = config.get("apiurl", "backend", fallback="").strip()
        return (url or "http://127.0.0.1:8019").rstrip("/")

    # 영화 목록 조회 API 호출 및 결과 정문화
    def getMovies(self, count: int = 10, start: int = 0, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/getmovies"
        filters = filters or {}
        body = {
            "COUNT": str(count), "START": str(start),
            "TITLE": str(filters.get("title", "")).strip(),
            "DIRECTOR": str(filters.get("director", "")).strip(),
            "ACTOR": str(filters.get("actor", "")).strip(),
            "RELEASE_START": str(filters.get("releaseStart", "")).strip(),
            "RELEASE_END": str(filters.get("releaseEnd", "")).strip(),
        }

        try:
            resp = requests.post(apiUrl, json=body, timeout=self.__TimeoutSec)
            try: respJson = resp.json()
            except ValueError: return {"ok": False, "statusCode": resp.status_code, "error": "JSON 응답 아님", "text": resp.text}

            data = respJson.get("datalist") if isinstance(respJson, dict) else None
            return {
                "ok": True, "backendUrl": self.__BackendUrl, "apiUrl": apiUrl, "statusCode": resp.status_code,
                "requestBody": body, "responseJson": respJson, "rows": self._normalizeDataList(data), "dataList": data,
            }
        except requests.RequestException as ex: return {"ok": False, "error": f"요청 실패: {ex}"}

    # 전체 영화 건수 조회 API 호출
    def getMoviesCount(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/getmoviescount"
        filters = filters or {}
        body = {
            "TITLE": str(filters.get("title", "")).strip(),
            "DIRECTOR": str(filters.get("director", "")).strip(),
            "ACTOR": str(filters.get("actor", "")).strip(),
            "RELEASE_START": str(filters.get("releaseStart", "")).strip(),
            "RELEASE_END": str(filters.get("releaseEnd", "")).strip(),
        }

        try:
            resp = requests.post(apiUrl, json=body, timeout=self.__TimeoutSec)
            try: respJson = resp.json()
            except ValueError: return {"ok": False, "statusCode": resp.status_code, "error": "JSON 응답 아님"}

            total = 0
            if isinstance(respJson, dict):
                try: total = int(respJson.get("datacount", respJson.get("datalist", 0)))
                except (ValueError, TypeError): total = 0
            return {"ok": True, "apiUrl": apiUrl, "statusCode": resp.status_code, "totalCount": total}
        except requests.RequestException as ex: return {"ok": False, "error": f"요청 실패: {ex}"}

    # 신규 영화 정보 등록 API 호출
    def createMovie(self, title: str, releaseDate: str, docId: str = "", director: str = "", genre: str = "", posterUrl: str = "", actor: str = "") -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/createmovie"
        body = {
            "docid": docId, "title": title, "releaseDate": releaseDate,
            "directorNm": director, "genre": genre, "posterUrl": posterUrl, "actorNm": actor,
        }
        return self._postData(apiUrl, body, "영화 등록 실패")

    # 기존 영화 정보 수정 API 호출
    def updateMovie(self, movieIdx: int, title: str, releaseDate: str, director: str = "", actor: str = "", genre: str = "", posterUrl: str = "") -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/updatemovie"
        body = {
            "movieId": movieIdx, "title": title, "releaseDate": releaseDate,
            "directorNm": director, "actorNm": actor, "genre": genre, "posterUrl": posterUrl,
        }
        return self._postData(apiUrl, body, "영화 수정 실패")

    # 영화 삭제 API 호출
    def deleteMovie(self, movieIdx: int) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/deletemovie"
        return self._postData(apiUrl, {"movieId": movieIdx}, "영화 삭제 실패")

    # 신규 리뷰 및 감성 분석 요청 API 호출
    def createReview(self, movieIdx: int, author: str, content: str) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/createreview"
        body = {"movieId": movieIdx, "authorName": author, "content": content}
        return self._postData(apiUrl, body, "리뷰 등록 실패")

    # 특정 영화에 대한 리뷰 목록 조회 API 호출
    def getReviews(self, movieIdx: int) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/getreviews"
        result = self._postData(apiUrl, {"movieId": movieIdx}, "리뷰 목록 조회 실패")
        if result.get("ok"):
            result["rows"] = self._normalizeDataList(result.get("data"))
        return result

    # 전체 리뷰 통합 조회 API 호출
    def getAllReviews(self, count: int = 10, start: int = 0, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/getallreviews"
        filters = filters or {}
        body = {
            "COUNT": str(count), "START": str(start),
            "MOVIE_TITLE": str(filters.get("movieTitle", "")).strip(),
            "AUTHOR_NAME": str(filters.get("authorName", "")).strip(),
            "CONTENT": str(filters.get("content", "")).strip(),
            "SENTIMENT_LABEL": str(filters.get("sentimentLabel", "")).strip(),
            "SENTIMENT_SCORE": str(filters.get("sentimentScore", "")).strip(),
            "CREATED_START": str(filters.get("createdStart", "")).strip(),
            "CREATED_END": str(filters.get("createdEnd", "")).strip(),
        }
        result = self._postData(apiUrl, body, "전체 리뷰 목록 조회 실패")
        if result.get("ok"):
            result["rows"] = self._normalizeDataList(result.get("data"))
        return result

    # 전체 리뷰 총 건수 조회 API 호출
    def getAllReviewsCount(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/getallreviewscount"
        filters = filters or {}
        body = {
            "MOVIE_TITLE": str(filters.get("movieTitle", "")).strip(),
            "AUTHOR_NAME": str(filters.get("authorName", "")).strip(),
            "CONTENT": str(filters.get("content", "")).strip(),
            "SENTIMENT_LABEL": str(filters.get("sentimentLabel", "")).strip(),
            "SENTIMENT_SCORE": str(filters.get("sentimentScore", "")).strip(),
            "CREATED_START": str(filters.get("createdStart", "")).strip(),
            "CREATED_END": str(filters.get("createdEnd", "")).strip(),
        }
        try:
            resp = requests.post(apiUrl, json=body, timeout=self.__TimeoutSec)
            try: respJson = resp.json()
            except ValueError: return {"ok": False, "statusCode": resp.status_code, "error": "JSON 응답 아님"}

            total = 0
            if isinstance(respJson, dict):
                try: total = int(respJson.get("datacount", respJson.get("datalist", 0)))
                except (ValueError, TypeError): total = 0
            return {"ok": True, "apiUrl": apiUrl, "statusCode": resp.status_code, "totalCount": total}
        except requests.RequestException as ex: return {"ok": False, "error": f"요청 실패: {ex}"}

    # 리뷰 삭제 API 호출
    def deleteReview(self, reviewIdx: int) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/deletereview"
        return self._postData(apiUrl, {"reviewId": reviewIdx}, "리뷰 삭제 실패")

    # POST 방식의 API 요청 처리를 위한 내부 공통 메서드
    def _postData(self, apiUrl: str, body: dict[str, Any], failMsg: str) -> dict[str, Any]:
        try:
            resp = requests.post(apiUrl, json=body, timeout=self.__TimeoutSec)
            try: respJson = resp.json()
            except ValueError: return {"ok": False, "statusCode": resp.status_code, "error": "JSON 응답 아님", "text": resp.text}

            statusStr = str(respJson.get("statusCode", "")) if isinstance(respJson, dict) else ""
            isOk = 200 <= resp.status_code < 300 and statusStr != "100"
            return {
                "ok": isOk, "apiUrl": apiUrl, "statusCode": resp.status_code, "requestBody": body,
                "responseJson": respJson, "data": respJson.get("datalist") if isinstance(respJson, dict) else None,
                "error": None if isOk else (respJson.get("statusMsg", failMsg) if isinstance(respJson, dict) else failMsg),
            }
        except requests.RequestException as ex: return {"ok": False, "error": f"요청 실패: {ex}"}
