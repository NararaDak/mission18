# FastAPI 기반 백엔드 서버 메인 파일
from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Body, FastAPI
from backend.api2db import Api2Db
from common.util import error_response, ok_response

# /accessdata 경로를 사용하는 라우터 설정
router = APIRouter(prefix="/accessdata", tags=["accessdata"])
app = FastAPI(title="Mission18 Backend")

# 성공 응답 포맷 생성 함수
def Get_Ok_Response(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return ok_response(extra)

# 에러 응답 포맷 생성 함수
def Get_Error_Response(message: str) -> dict[str, Any]:
    return error_response(message)

# 영화 목록 조회 API
@router.post("/getmovies")
def Get_Movies(req_param: str | dict[str, Any] = Body(...)) -> dict[str, Any]:
    out_map: dict[str, Any] = {}
    try:
        api2db = Api2Db()
        result = api2db.getMovies(req_param)
        out_map["datalist"] = result
        out_map["datacount"] = len(result) if isinstance(result, list) else 0
        out_map.update(Get_Ok_Response())
    except Exception as ex:
        out_map.update(Get_Error_Response(str(ex)))
    return out_map

# 영화 총 건수 조회 API
@router.post("/getmoviescount")
def Get_Movies_Count(req_param: str | dict[str, Any] = Body(...)) -> dict[str, Any]:
    out_map: dict[str, Any] = {}
    try:
        api2db = Api2Db()
        result = api2db.getMoviesCount(req_param)
        out_map["datalist"] = result
        out_map["datacount"] = result
        out_map.update(Get_Ok_Response())
    except Exception as ex:
        out_map.update(Get_Error_Response(str(ex)))
    return out_map

# 신규 영화 등록 API
@router.post("/createmovie")
def Create_Movie(req_param: str | dict[str, Any] = Body(...)) -> dict[str, Any]:
    out_map: dict[str, Any] = {}
    try:
        api2db = Api2Db()
        result = api2db.createMovie(req_param)
        out_map["datalist"] = result
        out_map["datacount"] = 1 if isinstance(result, dict) and len(result) > 0 else 0
        out_map.update(Get_Ok_Response())
    except Exception as ex:
        out_map.update(Get_Error_Response(str(ex)))
    return out_map

# 영화 정보 수정 API
@router.post("/updatemovie")
def Update_Movie(req_param: str | dict[str, Any] = Body(...)) -> dict[str, Any]:
    out_map: dict[str, Any] = {}
    try:
        api2db = Api2Db()
        result = api2db.updateMovie(req_param)
        out_map["datalist"] = result
        out_map["datacount"] = 1 if isinstance(result, dict) and len(result) > 0 else 0
        out_map.update(Get_Ok_Response())
    except Exception as ex:
        out_map.update(Get_Error_Response(str(ex)))
    return out_map

# 영화 삭제 API
@router.post("/deletemovie")
def Delete_Movie(req_param: str | dict[str, Any] = Body(...)) -> dict[str, Any]:
    out_map: dict[str, Any] = {}
    try:
        api2db = Api2Db()
        result = api2db.deleteMovie(req_param)
        out_map["datalist"] = result
        out_map["datacount"] = 1 if result else 0
        out_map.update(Get_Ok_Response())
    except Exception as ex:
        out_map.update(Get_Error_Response(str(ex)))
    return out_map

# 신규 리뷰 등록 API
@router.post("/createreview")
def Create_Review(req_param: str | dict[str, Any] = Body(...)) -> dict[str, Any]:
    out_map: dict[str, Any] = {}
    try:
        api2db = Api2Db()
        result = api2db.createReview(req_param)
        out_map["datalist"] = result
        out_map["datacount"] = 1 if isinstance(result, dict) and len(result) > 0 else 0
        out_map.update(Get_Ok_Response())
    except Exception as ex:
        out_map.update(Get_Error_Response(str(ex)))
    return out_map

# 특정 영화의 리뷰 목록 조회 API
@router.post("/getreviews")
def Get_Reviews(req_param: str | dict[str, Any] = Body(...)) -> dict[str, Any]:
    out_map: dict[str, Any] = {}
    try:
        api2db = Api2Db()
        result = api2db.getReviews(req_param)
        out_map["datalist"] = result
        out_map["datacount"] = len(result) if isinstance(result, list) else 0
        out_map.update(Get_Ok_Response())
    except Exception as ex:
        out_map.update(Get_Error_Response(str(ex)))
    return out_map

# 전체 리뷰 통합 조회 API
@router.post("/getallreviews")
def Get_All_Reviews(req_param: str | dict[str, Any] = Body(...)) -> dict[str, Any]:
    out_map: dict[str, Any] = {}
    try:
        api2db = Api2Db()
        result = api2db.getAllReviews(req_param)
        out_map["datalist"] = result
        out_map["datacount"] = len(result) if isinstance(result, list) else 0
        out_map.update(Get_Ok_Response())
    except Exception as ex:
        out_map.update(Get_Error_Response(str(ex)))
    return out_map

# 전체 리뷰 총 건수 조회 API
@router.post("/getallreviewscount")
def Get_All_Reviews_Count(req_param: str | dict[str, Any] = Body(...)) -> dict[str, Any]:
    out_map: dict[str, Any] = {}
    try:
        api2db = Api2Db()
        result = api2db.getAllReviewsCount(req_param)
        out_map["datalist"] = result
        out_map["datacount"] = result
        out_map.update(Get_Ok_Response())
    except Exception as ex:
        out_map.update(Get_Error_Response(str(ex)))
    return out_map

# 리뷰 삭제 API
@router.post("/deletereview")
def Delete_Review(req_param: str | dict[str, Any] = Body(...)) -> dict[str, Any]:
    out_map: dict[str, Any] = {}
    try:
        api2db = Api2Db()
        result = api2db.deleteReview(req_param)
        out_map["datalist"] = result
        out_map["datacount"] = 1 if result else 0
        out_map.update(Get_Ok_Response())
    except Exception as ex:
        out_map.update(Get_Error_Response(str(ex)))
    return out_map

# 리뷰 내용 수정 및 감성 분석 재처리 API
@router.post("/updatereview")
def Update_Review(req_param: str | dict[str, Any] = Body(...)) -> dict[str, Any]:
    out_map: dict[str, Any] = {}
    try:
        api2db = Api2Db()
        result = api2db.editReview(req_param)
        out_map["datalist"] = result
        out_map["datacount"] = 1 if isinstance(result, dict) and len(result) > 0 else 0
        out_map.update(Get_Ok_Response())
    except Exception as ex:
        out_map.update(Get_Error_Response(str(ex)))
    return out_map

# 라우터 등록 및 서버 실행 설정
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # 로컬 호스트 8009 포트로 서버 구동
    uvicorn.run(app, host="127.0.0.1", port=8009)
