# KMDB API에서 영화 데이터를 수집하여 DB에 저장하는 스크립트
import requests
import re
import json
from typing import Dict, Any

# DB 처리를 위한 SQLite 인터페이스 임포트
from app.storage.m18_sqlite import SQLiteDB

# KMDB API 설정 (서비스키 및 베이스 URL)
SERVICE_KEY = "ZC6C9YMX108KA9U95O9X"
BASE_URL = 'http://api.koreafilm.or.kr/openapi-data2/wisenut/search_api/search_json2.jsp'

# 텍스트 내 KMDB 특수 태그(!HS, !HE 등) 제거
def Clean_Text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'!HS |!HE ', '', text).strip()

# JSON 데이터의 모든 키를 소문자로 정규화 (일관성 유지)
def normalize_keys(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k.lower(): normalize_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [normalize_keys(v) for v in obj]
    else:
        return obj

# 값을 리스트로 변환 (단일 객체인 경우 리스트로 감쌈)
def _to_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []

# 리스트 내 객체들의 특정 키 값을 콤마로 구분된 문자열로 결합
def _join_values(items: list[dict[str, Any]], key: str, limit: int | None = None) -> str:
    values = [str(item.get(key, "")).strip() for item in items if str(item.get(key, "")).strip()]
    if limit is not None:
        values = values[:limit]
    return ", ".join(values)

# 범용 데이터를 텍스트로 변환 (dict/list는 JSON 문자열로)
def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)

# KMDB API를 호출하여 특정 연도의 영화 데이터 조회
def Get_Movie_Data(serviceKey: str, releaseYear: int,  startCount: int = 0, listCount: int = 100) -> Dict[str, Any]:
    strYear = str(releaseYear)
    queryParams = {
        'collection': 'kmdb_new2',
        'nation': '대한민국',
        'ServiceKey': serviceKey,
        'listCount': listCount,
        'startCount': startCount,
        'releaseDts': strYear + '0101',
        'releaseDte': strYear + '1231',
    }
    
    try:
        response = requests.get(BASE_URL, params=queryParams)
        if 200 <= response.status_code <= 300:
            return json.loads(response.text, strict=False)
        return {}
    except Exception as e:
        print(f"API 호출 에러: {str(e)}")
        return {}

# 특정 연도의 모든 영화 데이터를 페이지네이션하며 수집 및 저장
def Collect_Movie_Data(db: SQLiteDB, year: int) -> None:
    print(f"{year}년도 영화 데이터 수집 시작...")
    startCount = 0
    listCount = 500
    totalToCollect = 1 # 루프 진입용 초기값
    totalSaved = 0

    while startCount < totalToCollect:
        jsonData = Get_Movie_Data(SERVICE_KEY, year, startCount, listCount)
        if not jsonData: break

        # 키값 소문자 정규화
        jsonData = normalize_keys(jsonData)
        if 'data' not in jsonData or not jsonData['data']: break
        
        dataBlock = jsonData['data'][0]
        # 첫 페이지 조회 시 전체 개수 갱신
        if startCount == 0:
            totalToCollect = int(dataBlock.get('totalcount', 0))
            if totalToCollect == 0: break
            print(f"{year}년 총 데이터 건수: {totalToCollect}")

        results = dataBlock.get('result', [])
        if not results: break

        collectionName = str(dataBlock.get('collection', '') or '')
        pageNo = int(dataBlock.get('pageno', 0) or 0)
        numOfRows = int(dataBlock.get('numofrows', 0) or 0)

        count = 0
        for rowIndex, movie in enumerate(results, start=startCount + 1):
            docid = movie.get('docid')
            if not docid: continue

            # 중첩된 데이터 구조(감독, 배우 등) 평탄화 작업
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
            
            # DB 스키마에 맞게 데이터 매핑
            movieInfo = {
                'collection': collectionName, 'pageNo': pageNo, 'numOfRows': numOfRows,
                'totalCount': totalToCollect, 'rowValue': rowIndex, 'docid': docid,
                'kmdbMovieId': movie.get('movieid'), 'movieSeq': movie.get('movieseq'),
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
                'posterUrl': posterUrl, 'stillUrl': stillUrl,
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
                'regDate': movie.get('regdate', ''), 'modDate': movie.get('moddate', ''),
                'codeNm': _to_text(movie.get('codenm', '')),
                'codeNo': _to_text(movie.get('codeno', '')),
                'commCodes': _to_text(movie.get('commcodes', '')),
            }
            
            # 영화 정보 DB 저장 시도
            if db.saveMovie(movieInfo):
                count += 1
        
        totalSaved += count
        startCount += listCount # 다음 페이지 오프셋 갱신
            
    print(f"{year}년도 영화 수집 완료. (총 {totalSaved}건 저장)")

# 테스트 수집 함수 (2000년 데이터만 대상)
def Test_Collect():
    appDb = SQLiteDB()
    appDb.deleteAllMovies()
    Collect_Movie_Data(appDb, 2000)
    print("테스트 수집 완료.")

# 전체 기간(1900~2026) 영화 데이터 수집 함수
def All_Collect():
    appDb = SQLiteDB()
    appDb.deleteAllMovies() # 기존 데이터 초기화
    
    # 1900년부터 2026년까지 루프를 돌며 수집 실행
    for year in range(1900, 2027):
        Collect_Movie_Data(appDb, year)
            
    print("전체 영화 수집 프로세스 종료.")

if __name__ == "__main__":
    # 스크립트 실행 시 전체 수집 시작
    All_Collect()