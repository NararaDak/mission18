import requests
import re
from typing import Dict, Any

# 다른 모듈 임포트
from app.storage.m18_sqlite import SQLiteDB

# KMDB API 설정
SERVICE_KEY = "ZC6C9YMX108KA9U95O9X"
BASE_URL = 'http://api.koreafilm.or.kr/openapi-data2/wisenut/search_api/search_json2.jsp'

def Clean_Text(text: str) -> str:
    """
    API 검색 결과 데이터의 특수 태그(!HS, !HE 등)를 제거합니다.
    """
    if not text:
        return ""
    return re.sub(r'!HS |!HE ', '', text).strip()

def normalize_keys(obj: Any) -> Any:
    """
    JSON 데이터의 모든 키를 소문자로 변환하여 대소문자 불일치 문제를 해결합니다.
    KMDB API 응답의 키가 대문자로 오는 경우 등을 처리합니다.
    """
    if isinstance(obj, dict):
        return {k.lower(): normalize_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [normalize_keys(v) for v in obj]
    else:
        return obj

import json


def _to_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _join_values(items: list[dict[str, Any]], key: str, limit: int | None = None) -> str:
    values = [str(item.get(key, "")).strip() for item in items if str(item.get(key, "")).strip()]
    if limit is not None:
        values = values[:limit]
    return ", ".join(values)


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)

def Get_Movie_Data(serviceKey: str, releaseYear: int,  startCount: int = 0, listCount: int = 100) -> Dict[str, Any]:
    """
    KMDB API를 호출하여 영화 데이터를 가져오는 전역 함수입니다.
    """
    strYear = str(releaseYear)
    
    queryParams = {
        'collection': 'kmdb_new2',
        'nation': '대한민국',
        'ServiceKey': serviceKey,
        'listCount': listCount,
        'startCount': startCount,
        'releaseDts': strYear + '0101', # 개봉일 시작
        'releaseDte': strYear + '1231', # 개봉일 끝
      #  'type': '극영화'
    }
    
    try:
        response = requests.get(BASE_URL, params=queryParams)
        if 200 <= response.status_code <= 300:
            # strict=False를 사용하여 제어 문자(줄바꿈 등)가 포함된 비표준 JSON도 허용
            return json.loads(response.text, strict=False)
        print(f"API Error: {response.status_code}")
        return {}
    except Exception as e:
        print(f"Exception during API call: {str(e)}")
        return {}

def Collect_Movie_Data(db: SQLiteDB, year: int) -> None:
    """
    특정 년도의 영화 데이터를 수집하여 DB에 저장합니다. (페이지네이션 처리)
    """
    print(f"Collecting movies for year: {year}...")
    
    startCount = 0
    listCount = 500 # 한 번에 가져올 개수
    totalToCollect = 1 # 초기값 (루프 진입용)
    totalSaved = 0

    while startCount < totalToCollect:
        jsonData = Get_Movie_Data(SERVICE_KEY, year, startCount, listCount)
        
        if not jsonData:
            break

        # 모든 키를 소문자로 정규화
        jsonData = normalize_keys(jsonData)

        if 'data' not in jsonData or not jsonData['data']:
            break
        
        dataBlock = jsonData['data'][0]
        
        # 첫 요청에서 전체 개수 확인
        if startCount == 0:
            totalToCollect = int(dataBlock.get('totalcount', 0))
            if totalToCollect == 0:
                break
            print(f"Total count for {year}: {totalToCollect}")

        results = dataBlock.get('result', [])
        if not results:
            break

        collectionName = str(dataBlock.get('collection', '') or '')
        pageNo = int(dataBlock.get('pageno', 0) or 0)
        numOfRows = int(dataBlock.get('numofrows', 0) or 0)

        count = 0
        for rowIndex, movie in enumerate(results, start=startCount + 1):
            docid = movie.get('docid')
            if not docid: 
                continue

            directors = _to_list(movie.get('directors', {}).get('director', []))
            actors = _to_list(movie.get('actors', {}).get('actor', []))
            staffs = _to_list(movie.get('staffs', {}).get('staff', []))
            vods = _to_list(movie.get('vods', {}).get('vod', []))
            ratings = _to_list(movie.get('ratings', {}).get('rating', []))
            primaryRating = ratings[0] if ratings else {}

            releaseDate = str(movie.get('releasedate', '') or '')
            repRlsDate = str(primaryRating.get('reprlsdate', '') or movie.get('reprlsdate', '') or '')
            posterUrl = str(movie.get('posters', '') or '').split('|')[0] if movie.get('posters') else ''
            stillRaw = str(movie.get('stlls', '') or movie.get('stills', '') or '')
            stillUrl = stillRaw.split('|')[0] if stillRaw else ''
            
            # 데이터 정제 및 매핑
            movieInfo = {
                'collection': collectionName,
                'pageNo': pageNo,
                'numOfRows': numOfRows,
                'totalCount': totalToCollect,
                'rowValue': rowIndex,
                'docid': docid,
                'kmdbMovieId': movie.get('movieid'),
                'movieSeq': movie.get('movieseq'),
                'title': Clean_Text(movie.get('title', 'Unknown')),
                'titleEng': Clean_Text(movie.get('titleeng', '')),
                'titleOrg': Clean_Text(movie.get('titleorg', '')),
                'titleEtc': Clean_Text(movie.get('titleetc', '')),
                'directorNm': _join_values(directors, 'directornm'),
                'directorEnNm': _join_values(directors, 'directorennm'),
                'directorId': _join_values(directors, 'directorid'),
                'actorNm': _join_values(actors, 'actornm', limit=5),
                'actorEnNm': _join_values(actors, 'actorennm', limit=5),
                'actorId': _join_values(actors, 'actorid', limit=5),
                'nation': _to_text(movie.get('nation', '')),
                'company': _to_text(movie.get('company', '')),
                'prodYear': movie.get('prodyear', ''),
                'plot': movie.get('plots', {}).get('plot', [{}])[0].get('plottext', '') if movie.get('plots') else "" ,
                'runtime': movie.get('runtime', ''),
                'rating': movie.get('rating', ''),
                'genre': movie.get('genre', ''),
                'kmdbUrl': movie.get('kmdburl', ''),
                'movieType': movie.get('type', ''),
                'movieUse': movie.get('use', ''),
                'episodes': _to_text(movie.get('episodes', '')),
                'ratedYn': primaryRating.get('ratedyn', '') or movie.get('ratedyn', ''),
                'repRatDate': primaryRating.get('repratdate', '') or movie.get('repratdate', ''),
                'repRlsDate': repRlsDate,
                'ratingMain': primaryRating.get('ratingmain', '') or movie.get('ratingmain', ''),
                'ratingDate': primaryRating.get('ratingdate', '') or movie.get('ratingdate', ''),
                'ratingNo': primaryRating.get('ratingno', '') or movie.get('ratingno', ''),
                'ratingGrade': primaryRating.get('ratinggrade', '') or movie.get('ratinggrade', ''),
                'releaseDate': releaseDate or repRlsDate,
                'keywords': _to_text(movie.get('keywords', '')),
                'posterUrl': posterUrl,
                'stillUrl': stillUrl,
                'staffNm': _join_values(staffs, 'staffnm', limit=5),
                'staffRoleGroup': _join_values(staffs, 'staffrolegroup', limit=5),
                'staffRole': _join_values(staffs, 'staffrole', limit=5),
                'staffEtc': _join_values(staffs, 'staffetc', limit=5),
                'staffId': _join_values(staffs, 'staffid', limit=5),
                'vodClass': str(vods[0].get('vodclass', '')) if vods else '',
                'vodUrl': str(vods[0].get('vodurl', '')) if vods else '',
                'openThtr': _to_text(movie.get('openthtr', '')),
                'screenArea': _to_text(movie.get('screenarea', '')),
                'screenCnt': _to_text(movie.get('screencnt', '')),
                'salesAcc': _to_text(movie.get('salesacc', '')),
                'audiAcc': _to_text(movie.get('audiacc', '')),
                'statSouce': _to_text(movie.get('statsouce', '')),
                'statDate': _to_text(movie.get('statdate', '')),
                'themeSong': _to_text(movie.get('themesong', '')),
                'soundtrack': _to_text(movie.get('soundtrack', '')),
                'fLocation': _to_text(movie.get('flocation', '')),
                'awards1': _to_text(movie.get('awards1', '')),
                'awards2': _to_text(movie.get('awards2', '')),
                'regDate': movie.get('regdate', ''),
                'modDate': movie.get('moddate', ''),
                'codeNm': _to_text(movie.get('codenm', '')),
                'codeNo': _to_text(movie.get('codeno', '')),
                'commCodes': _to_text(movie.get('commcodes', '')),
            }
            
            # SQLiteDB 클래스를 사용하여 저장
            if db.saveMovie(movieInfo):
                count += 1
        
        totalSaved += count
        startCount += listCount # 다음 페이지로 이동
            
    print(f"Total Saved {totalSaved} movies for {year}.")


def Test_Collect():
    appDb = SQLiteDB()
    appDb.deleteAllMovies()
    # 2000년 데이터만 테스트 수집
    Collect_Movie_Data(appDb, 2000)
            
    print("Test Movie collection completed.")

def All_Collect():
    appDb = SQLiteDB()
    # 모든 데이터를 삭제
    appDb.deleteAllMovies()
    
    # 2000년부터 2026년까지 수집
    for year in range(1900, 2027):
        Collect_Movie_Data(appDb, year)
            
    print("Movie collection completed.")

if __name__ == "__main__":
    All_Collect()