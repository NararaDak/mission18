# KMDB API에서 영화 데이터를 수집하여 Oracle DB에 저장하는 스크립트
import requests
import re
import json
from typing import Dict, Any
import os
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from common.defines import PROJECT_ROOT
from dbclient_oracle import OracleDbClient
from dbclient import DbClient as SQLiteClient

SERVICE_KEY = os.getenv("KMDB_SERVICE_KEY")
BASE_URL = 'http://api.koreafilm.or.kr/openapi-data2/wisenut/search_api/search_json2.jsp'

# 텍스트 내 KMDB 특수 태그(!HS, !HE 등) 제거
def Clean_Text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'!HS |!HE ', '', text).strip()

def normalize_keys(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k.lower(): normalize_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [normalize_keys(v) for v in obj]
    else:
        return obj

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

def saveMovieOracle(db: OracleDbClient, movieInfo: dict) -> bool:
    # movieId 컬럼 제거 (트리거 자동 할당)
    movieInfo = {k: v for k, v in movieInfo.items() if k != 'movieId'}
    keys = list(movieInfo.keys())
    values = [movieInfo[k] for k in keys]
    placeholders = ', '.join([':' + str(i+1) for i in range(len(keys))])
    sql = f"INSERT INTO movies ({', '.join(keys)}) VALUES ({placeholders})"
    try:
        with db._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql, values)
            conn.commit()
        return True
    except Exception as e:
        print(f"Oracle 저장 실패: {e}")
        return False

def Collect_Movie_Data(db: OracleDbClient, year: int) -> None:
    print(f"{year}년도 영화 데이터 수집 시작...")
    startCount = 0
    listCount = 500
    totalToCollect = 1
    totalSaved = 0
    while startCount < totalToCollect:
        jsonData = Get_Movie_Data(SERVICE_KEY, year, startCount, listCount)
        if not jsonData: break
        jsonData = normalize_keys(jsonData)
        if 'data' not in jsonData or not jsonData['data']: break
        dataBlock = jsonData['data'][0]
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
            if saveMovieOracle(db, movieInfo):
                count += 1
        totalSaved += count
        startCount += listCount
    print(f"{year}년도 영화 수집 완료. (총 {totalSaved}건 저장)")

def Test_Collect():
    appDb = OracleDbClient()
    # 전체 삭제는 직접 쿼리로 수행
    appDb.ExecuteSQL("DELETE FROM reviews")
    appDb.ExecuteSQL("DELETE FROM movies")
    Collect_Movie_Data(appDb, 2000)
    print("테스트 수집 완료.")

def sync_sequence(db: OracleDbClient):
    # Oracle movieId 및 reviewId 시퀀스 값을 데이터와 동기화
    for table, seq, col in [('movies', 'seq_movies_id', 'movieId'), ('reviews', 'seq_reviews_id', 'reviewId')]:
        try:
            res = db.SelectSQL(f"SELECT MAX({col}) as maxid FROM {table}")
            max_id = res[0]['MAXID'] or 0
            
            # 현재 시퀀스 값 조회
            res_seq = db.SelectSQL(f"SELECT {seq}.NEXTVAL as nextid FROM dual")
            curr_val = res_seq[0]['NEXTID']
            
            diff = max_id - curr_val
            if diff > 0:
                # 시퀀스를 max_id까지 한 번에 점프
                db.ExecuteSQL(f"ALTER SEQUENCE {seq} INCREMENT BY {diff}")
                db.SelectSQL(f"SELECT {seq}.NEXTVAL FROM dual")
                db.ExecuteSQL(f"ALTER SEQUENCE {seq} INCREMENT BY 1")
                print(f"{seq} 시퀀스 동기화 완료 (MAX: {max_id})")
        except Exception as e:
            print(f"{seq} 시퀀스 동기화 실패: {e}")

def All_Collect():
    appDb = OracleDbClient()
    appDb.ExecuteSQL("DELETE FROM reviews")
    appDb.ExecuteSQL("DELETE FROM movies")
    for year in range(1900, 2027):
        Collect_Movie_Data(appDb, year)
    print("전체 영화 수집 프로세스 종료.")

# SQLite에서 Oracle로 모든 데이터 수집 (고성능 배치 마이그레이션)
def All_Collect_fromSQlite():
    sqlite_db = SQLiteClient()
    oracle_db = OracleDbClient()
    
    # 1. 데이터 초기화
    oracle_db.ExecuteSQL("DELETE FROM reviews")
    oracle_db.ExecuteSQL("DELETE FROM movies")
    print("Oracle 데이터 초기화 완료 (movies, reviews)")

    # 2. 모든 영화 데이터 일괄 이관
    # movieId를 포함하여 이관함으로써 reviews 정합성을 유지합니다. (Oracle 트리거가 movieId가 있을 땐 NEXTVAL을 건너뜀)
    print("SQLite에서 영화 데이터를 불러오는 중...")
    all_movies = sqlite_db.SelectSQL("SELECT * FROM movies")
    total_movies = len(all_movies)
    
    if total_movies > 0:
        # 데이터 정제 및 4000자 초과 방지 (최종 안전장치)
        for m in all_movies:
            m.pop('createdAt', None)
            for key, val in m.items():
                # plot은 CLOB이므로 건너뛰고, 나머지는 VARCHAR2(4000) 내로 제한
                if key != 'plot' and isinstance(val, str) and len(val) > 4000:
                    m[key] = val[:4000]
            
        keys = list(all_movies[0].keys())
        placeholders = ', '.join([':' + str(j+1) for j in range(len(keys))])
        sql = f"INSERT INTO movies ({', '.join(keys)}) VALUES ({placeholders})"
        
        batch_size = 500
        for i in range(0, total_movies, batch_size):
            batch = all_movies[i:i+batch_size]
            data = [[m[k] for k in keys] for m in batch]
            oracle_db.ExecuteMany(sql, data)
            print(f"영화 이관 중... ({min(i+batch_size, total_movies)}/{total_movies})")

    # 3. 모든 리뷰 데이터 일괄 이관
    print("SQLite에서 리뷰 데이터를 불러오는 중...")
    all_reviews = sqlite_db.SelectSQL("SELECT * FROM reviews")
    total_reviews = len(all_reviews)
    
    if total_reviews > 0:
        for r in all_reviews:
            r.pop('reviewId', None) # reviewId는 Oracle에서 새로 할당
            r.pop('createdAt', None)
            
        r_keys = list(all_reviews[0].keys())
        r_placeholders = ', '.join([':' + str(j+1) for j in range(len(r_keys))])
        r_sql = f"INSERT INTO reviews ({', '.join(r_keys)}) VALUES ({r_placeholders})"
        
        # 리뷰는 대량이어도 한 번에 처리 가능 (데이터가 크지 않음)
        oracle_db.ExecuteMany(r_sql, [[r[k] for k in r_keys] for r in all_reviews])
        print(f"리뷰 이관 완료: {total_reviews}건")

    # 4. 시퀀스 값 동기화 (ID 보존 이관 후 필수 단계)
    sync_sequence(oracle_db)
    print("SQLite -> Oracle 마이그레이션이 성공적으로 완료되었습니다.")

if __name__ == "__main__":
    All_Collect_fromSQlite()
