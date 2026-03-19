import configparser
import json
from pathlib import Path
from typing import Any
import os
import requests



class CallApi:
    # API 객체 초기화. timeout, backend url 설정
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

    # 데이터 리스트 정규화. dict/str도 리스트로 변환
    @staticmethod
    def _normalizeDataList(rawData: object) -> list[object] | None:
        if isinstance(rawData, list):
            return rawData

        if isinstance(rawData, dict):
            keys = list(rawData.keys())
            if all(str(keyValue).isdigit() for keyValue in keys):
                sortedItems = sorted(rawData.items(), key=lambda item: int(str(item[0])))
                return [value for _, value in sortedItems]
            return list(rawData.values())

        if isinstance(rawData, str):
            try:
                parsed = json.loads(rawData)
                return CallApi._normalizeDataList(parsed)
            except ValueError:
                return None

        return None

    def _getBackendUrl(self) -> str:
        projectRootDir = Path(__file__).resolve().parent.parent
        iniPath = os.path.join(projectRootDir, "common", "m18.ini")

        configData = configparser.ConfigParser()
        configData.read(iniPath, encoding="utf-8")

        backendUrl = ""
        if configData.has_section("aipurl"):
            backendUrl = configData.get("aipurl", "backend", fallback="").strip()
        if not backendUrl and configData.has_section("apiurl"):
            backendUrl = configData.get("apiurl", "backend", fallback="").strip()

        if not backendUrl:
            backendUrl = "http://127.0.0.1:8019"

        return backendUrl.rstrip("/")

    def getMovies(self, countValue: int = 10, startValue: int = 0, filtersData: dict[str, Any] | None = None) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/getmovies"
        filtersData = filtersData or {}
        requestBody = {
            "COUNT": str(countValue),
            "START": str(startValue),
            "TITLE": str(filtersData.get("title", "") or "").strip(),
            "DIRECTOR": str(filtersData.get("director", "") or "").strip(),
            "ACTOR": str(filtersData.get("actor", "") or "").strip(),
            "RELEASE_START": str(filtersData.get("releaseStart", "") or "").strip(),
            "RELEASE_END": str(filtersData.get("releaseEnd", "") or "").strip(),
        }

        try:
            response = requests.post(apiUrl, json=requestBody, timeout=self.__TimeoutSec)
            statusCode = response.status_code
            try:
                responseJson = response.json()
            except ValueError:
                return {
                    "ok": False,
                    "statusCode": statusCode,
                    "error": "JSON 응답이 아닙니다.",
                    "text": response.text,
                }

            dataList = responseJson.get("datalist") if isinstance(responseJson, dict) else None
            rows = self._normalizeDataList(dataList)

            return {
                "ok": True,
                "backendUrl": self.__BackendUrl,
                "apiUrl": apiUrl,
                "statusCode": statusCode,
                "requestBody": requestBody,
                "responseJson": responseJson,
                "rows": rows,
                "dataList": dataList,
            }
        except requests.RequestException as ex:
            return {
                "ok": False,
                "error": f"요청 실패: {ex}",
            }

    def getMoviesCount(self, filtersData: dict[str, Any] | None = None) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/getmoviescount"
        filtersData = filtersData or {}
        requestBody = {
            "TITLE": str(filtersData.get("title", "") or "").strip(),
            "DIRECTOR": str(filtersData.get("director", "") or "").strip(),
            "ACTOR": str(filtersData.get("actor", "") or "").strip(),
            "RELEASE_START": str(filtersData.get("releaseStart", "") or "").strip(),
            "RELEASE_END": str(filtersData.get("releaseEnd", "") or "").strip(),
        }

        try:
            response = requests.post(apiUrl, json=requestBody, timeout=self.__TimeoutSec)
            statusCode = response.status_code
            try:
                responseJson = response.json()
            except ValueError:
                return {
                    "ok": False,
                    "statusCode": statusCode,
                    "error": "JSON 응답이 아닙니다.",
                    "text": response.text,
                }

            totalCount = 0
            if isinstance(responseJson, dict):
                rawCount = responseJson.get("datacount", responseJson.get("datalist", 0))
                try:
                    totalCount = int(rawCount)
                except (ValueError, TypeError):
                    totalCount = 0

            return {
                "ok": True,
                "apiUrl": apiUrl,
                "statusCode": statusCode,
                "totalCount": totalCount,
            }
        except requests.RequestException as ex:
            return {
                "ok": False,
                "error": f"요청 실패: {ex}",
            }

    def createMovie(
        self,
        titleValue: str,
        releaseDateValue: str,
        docIdValue: str = "",
        directorValue: str = "",
        genreValue: str = "",
        posterUrlValue: str = "",
        actorValue: str = "",
    ) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/createmovie"
        requestBody = {
            "docid": docIdValue,
            "title": titleValue,
            "releaseDate": releaseDateValue,
            "directorNm": directorValue,
            "genre": genreValue,
            "posterUrl": posterUrlValue,
            "actorNm": actorValue,
        }

        return self._postData(apiUrl, requestBody, "영화 등록 실패")

    def updateMovie(
        self,
        movieIdValue: int,
        titleValue: str,
        releaseDateValue: str,
        directorValue: str = "",
        actorValue: str = "",
        genreValue: str = "",
        posterUrlValue: str = "",
    ) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/updatemovie"
        requestBody = {
            "movieId": movieIdValue,
            "title": titleValue,
            "releaseDate": releaseDateValue,
            "directorNm": directorValue,
            "actorNm": actorValue,
            "genre": genreValue,
            "posterUrl": posterUrlValue,
        }

        return self._postData(apiUrl, requestBody, "영화 수정 실패")

    def deleteMovie(self, movieIdValue: int) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/deletemovie"
        requestBody = {"movieId": movieIdValue}
        return self._postData(apiUrl, requestBody, "영화 삭제 실패")

    def createReview(self, movieIdValue: int, authorNameValue: str, contentValue: str) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/createreview"
        requestBody = {
            "movieId": movieIdValue,
            "authorName": authorNameValue,
            "content": contentValue,
        }
        return self._postData(apiUrl, requestBody, "리뷰 등록 실패")

    def getReviews(self, movieIdValue: int) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/getreviews"
        requestBody = {"movieId": movieIdValue}
        result = self._postData(apiUrl, requestBody, "리뷰 목록 조회 실패")
        if result.get("ok"):
            dataList = result.get("data")
            result["rows"] = self._normalizeDataList(dataList)
        else:
            result["rows"] = None
        return result

    def getAllReviews(self, countValue: int = 10, startValue: int = 0, filtersData: dict[str, Any] | None = None) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/getallreviews"
        filtersData = filtersData or {}
        requestBody = {
            "COUNT": str(countValue),
            "START": str(startValue),
            "MOVIE_TITLE": str(filtersData.get("movieTitle", "") or "").strip(),
            "AUTHOR_NAME": str(filtersData.get("authorName", "") or "").strip(),
            "CONTENT": str(filtersData.get("content", "") or "").strip(),
            "SENTIMENT_LABEL": str(filtersData.get("sentimentLabel", "") or "").strip(),
            "SENTIMENT_SCORE": str(filtersData.get("sentimentScore", "") or "").strip(),
            "CREATED_START": str(filtersData.get("createdStart", "") or "").strip(),
            "CREATED_END": str(filtersData.get("createdEnd", "") or "").strip(),
        }
        result = self._postData(apiUrl, requestBody, "전체 리뷰 목록 조회 실패")
        if result.get("ok"):
            dataList = result.get("data")
            result["rows"] = self._normalizeDataList(dataList)
        else:
            result["rows"] = None
        return result

    def getAllReviewsCount(self, filtersData: dict[str, Any] | None = None) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/getallreviewscount"
        filtersData = filtersData or {}
        requestBody = {
            "MOVIE_TITLE": str(filtersData.get("movieTitle", "") or "").strip(),
            "AUTHOR_NAME": str(filtersData.get("authorName", "") or "").strip(),
            "CONTENT": str(filtersData.get("content", "") or "").strip(),
            "SENTIMENT_LABEL": str(filtersData.get("sentimentLabel", "") or "").strip(),
            "SENTIMENT_SCORE": str(filtersData.get("sentimentScore", "") or "").strip(),
            "CREATED_START": str(filtersData.get("createdStart", "") or "").strip(),
            "CREATED_END": str(filtersData.get("createdEnd", "") or "").strip(),
        }
        try:
            response = requests.post(apiUrl, json=requestBody, timeout=self.__TimeoutSec)
            statusCode = response.status_code
            try:
                responseJson = response.json()
            except ValueError:
                return {
                    "ok": False,
                    "statusCode": statusCode,
                    "error": "JSON 응답이 아닙니다.",
                    "text": response.text,
                }
            totalCount = 0
            if isinstance(responseJson, dict):
                rawCount = responseJson.get("datacount", responseJson.get("datalist", 0))
                try:
                    totalCount = int(rawCount)
                except (ValueError, TypeError):
                    totalCount = 0
            return {
                "ok": True,
                "apiUrl": apiUrl,
                "statusCode": statusCode,
                "totalCount": totalCount,
            }
        except requests.RequestException as ex:
            return {
                "ok": False,
                "error": f"요청 실패: {ex}",
            }

    def deleteReview(self, reviewIdValue: int) -> dict[str, Any]:
        apiUrl = f"{self.__BackendUrl}/accessdata/deletereview"
        requestBody = {"reviewId": reviewIdValue}
        return self._postData(apiUrl, requestBody, "리뷰 삭제 실패")

    def _postData(self, apiUrl: str, requestBody: dict[str, Any], defaultErrorMessage: str) -> dict[str, Any]:
        try:
            response = requests.post(apiUrl, json=requestBody, timeout=self.__TimeoutSec)
            statusCode = response.status_code
            try:
                responseJson = response.json()
            except ValueError:
                return {
                    "ok": False,
                    "statusCode": statusCode,
                    "error": "JSON 응답이 아닙니다.",
                    "text": response.text,
                }

            responseStatusCode = ""
            if isinstance(responseJson, dict):
                responseStatusCode = str(responseJson.get("statusCode", ""))

            isOk = 200 <= statusCode < 300 and responseStatusCode != "100"
            return {
                "ok": isOk,
                "apiUrl": apiUrl,
                "statusCode": statusCode,
                "requestBody": requestBody,
                "responseJson": responseJson,
                "data": responseJson.get("datalist") if isinstance(responseJson, dict) else None,
                "error": None if isOk else (
                    responseJson.get("statusMsg", defaultErrorMessage) if isinstance(responseJson, dict) else defaultErrorMessage
                ),
            }
        except requests.RequestException as ex:
            return {
                "ok": False,
                "error": f"요청 실패: {ex}",
            }
