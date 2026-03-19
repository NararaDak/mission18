from __future__ import annotations
from typing import Any
from fastapi import APIRouter, Body, FastAPI
from backend.api2db import Api2Db
from common.util import error_response, ok_response

router = APIRouter(prefix="/accessdata", tags=["accessdata"])
app = FastAPI(title="Mission18 Backend")


def Get_Ok_Response(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return ok_response(extra)


def Get_Error_Response(message: str) -> dict[str, Any]:
    return error_response(message)

## 영화 목록 가져오기 API 
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


app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8019)
