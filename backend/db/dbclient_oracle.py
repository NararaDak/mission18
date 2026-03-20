# Oracle 데이터베이스 연결 및 쿼리 실행을 담당하는 클라이언트 클래스
from __future__ import annotations
import oracledb
import os
import re
from pathlib import Path
from typing import Any

# 환경설정은 common/defines.py와 .env에서 가져옴
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from common.defines import PROJECT_ROOT
print(f"dbclient_oracle PROJECT_ROOT: {PROJECT_ROOT}")

def load_env_var(key: str, default: str = "") -> str:
    env_path = os.path.join(PROJECT_ROOT, ".env")
    try:
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() == key:
                        val = v.strip()
                        # 따옴표 제거
                        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                            val = val[1:-1]
                        return val
    except Exception:
        pass
    return os.getenv(key, default)

class OracleDbClient:
    def __init__(self) -> None:
        self.wallet_path = os.path.join(PROJECT_ROOT, ".security", "Wallet_FXEEDB2VI08RPM2S")
        self.wallet_password = load_env_var("ORACLE_WALLET_PASSWORD", "wallet_password")
        self.db_user = load_env_var("ORACLE_DB_USER", "ADMIN")
        self.db_password = load_env_var("ORACLE_ADMIN_PASSWORD", "oracle_password")
        self.dsn = load_env_var("ORACLE_DSN", "fxeedb2vi08rpm2s_high") # "fxeedb2vi08rpm2s_low")
        self._sql_queue: list[str] = []
        # Thin 모드 환경 변수 설정
        os.environ["TNS_ADMIN"] = self.wallet_path

    def _connect(self) -> oracledb.Connection:
        return oracledb.connect(
            user=self.db_user,
            password=self.db_password,
            dsn=self.dsn,
            config_dir=self.wallet_path,
            wallet_location=self.wallet_path,
            wallet_password=self.wallet_password
        )

    import re
    def _translate_sql(self, sql: str) -> str:
        # 1. datetime('now', 'localtime') -> SYSDATE
        sql = sql.replace("datetime('now', 'localtime')", "SYSDATE")
        
        # 2. LIMIT n OFFSET m -> OFFSET m ROWS FETCH NEXT n ROWS ONLY
        # OFFSET 단어가 포함된 경우의 LIMIT 변환
        pattern_limit_offset = re.compile(r'LIMIT\s+(\d+)\s+OFFSET\s+(\d+)', re.IGNORECASE)
        if pattern_limit_offset.search(sql):
            sql = pattern_limit_offset.sub(r'OFFSET \2 ROWS FETCH NEXT \1 ROWS ONLY', sql)
        
        # 3. LIMIT n (without OFFSET) -> FETCH NEXT n ROWS ONLY
        # 이미 위에서 매칭되지 않은 단독 LIMIT 구문
        pattern_limit = re.compile(r'LIMIT\s+(\d+)', re.IGNORECASE)
        if pattern_limit.search(sql):
            sql = pattern_limit.sub(r'FETCH NEXT \1 ROWS ONLY', sql)
            
        return sql

    def _format_columns(self, columns: list[str]) -> list[str]:
        # Oracle_DB returns all-uppercase column names.
        # This maps them back to the exact casing expected by the frontend and API.
        key_map = {
            "MOVIEID": "movieId",
            "PAGENO": "pageNo",
            "NUMOFROWS": "numOfRows",
            "TOTALCOUNT": "totalCount",
            "ROWVALUE": "rowValue",
            "DOCID": "docid",
            "KMDBMOVIEID": "kmdbMovieId",
            "MOVIESEQ": "movieSeq",
            "TITLE": "title",
            "TITLEENG": "titleEng",
            "TITLEORG": "titleOrg",
            "TITLEETC": "titleEtc",
            "PLOT": "plot",
            "DIRECTORNM": "directorNm",
            "DIRECTORENNM": "directorEnNm",
            "DIRECTORID": "directorId",
            "ACTORNM": "actorNm",
            "ACTORENNM": "actorEnNm",
            "ACTORID": "actorId",
            "NATION": "nation",
            "COMPANY": "company",
            "PRODYEAR": "prodYear",
            "RUNTIME": "runtime",
            "RATING": "rating",
            "GENRE": "genre",
            "KMDBURL": "kmdbUrl",
            "MOVIETYPE": "movieType",
            "MOVIEUSE": "movieUse",
            "EPISODES": "episodes",
            "RATEDYN": "ratedYn",
            "REPRATDATE": "repRatDate",
            "REPRLSDATE": "repRlsDate",
            "RATINGMAIN": "ratingMain",
            "RATINGDATE": "ratingDate",
            "RATINGNO": "ratingNo",
            "RATINGGRADE": "ratingGrade",
            "RELEASEDATE": "releaseDate",
            "KEYWORDS": "keywords",
            "POSTERURL": "posterUrl",
            "STILLURL": "stillUrl",
            "STAFFNM": "staffNm",
            "STAFFROLEGROUP": "staffRoleGroup",
            "STAFFROLE": "staffRole",
            "STAFFETC": "staffEtc",
            "STAFFID": "staffId",
            "VODCLASS": "vodClass",
            "VODURL": "vodUrl",
            "OPENTHTR": "openThtr",
            "SCREENAREA": "screenArea",
            "SCREENCNT": "screenCnt",
            "SALESACC": "salesAcc",
            "AUDIACC": "audiAcc",
            "STATSOUCE": "statSouce",
            "STATDATE": "statDate",
            "THEMESONG": "themeSong",
            "SOUNDTRACK": "soundtrack",
            "FLOCATION": "fLocation",
            "AWARDS1": "awards1",
            "AWARDS2": "awards2",
            "REGDATE": "regDate",
            "MODDATE": "modDate",
            "CODENM": "codeNm",
            "CODENO": "codeNo",
            "COMMCODES": "commCodes",
            "CREATEDAT": "createdAt",
            "COUNT": "count",
            "REVIEWID": "reviewId",
            "AUTHORNAME": "authorName",
            "CONTENT": "content",
            "SENTIMENTLABEL": "sentimentLabel",
            "SENTIMENTSCORE": "sentimentScore",
            "TOTALCOUNT": "totalCount",
            "UPDATEDCOUNT": "updatedCount",
            "MOVIETITLE": "movieTitle"
        }
        return [key_map.get(c, c) for c in columns]

    def _normalize_value(self, value: Any) -> Any:
        """Oracle에서 반환된 값을 JSON 직렬화 가능한 Python 기본 타입으로 변환"""
        import datetime
        import decimal
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(value, datetime.date):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, decimal.Decimal):
            return int(value) if value == int(value) else float(value)
        # oracledb LOB 객체 (CLOB, BLOB 등)
        if hasattr(value, 'read'):
            try:
                return value.read()
            except Exception:
                return str(value)
        return value

    def SelectSQL(self, sql: str, params: Any = None) -> list[dict[str, Any]]:
        sql = self._translate_sql(sql)
        with self._connect() as conn:
            cur = conn.cursor()
            if params is not None:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            columns = self._format_columns([col[0] for col in cur.description])
            return [
                {col: self._normalize_value(val) for col, val in zip(columns, row)}
                for row in cur.fetchall()
            ]

    def ExecuteSQL(self, sql: str, params: Any = None) -> bool:
        sql = self._translate_sql(sql)
        with self._connect() as conn:
            cur = conn.cursor()
            if params is not None:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            conn.commit()
        return True

    def ExecuteMany(self, sql: str, data_list: list[Any]) -> int:
        if not data_list:
            return 0
        sql = self._translate_sql(sql)
        with self._connect() as conn:
            cur = conn.cursor()
            cur.executemany(sql, data_list)
            count = cur.rowcount
            conn.commit()
        return count

    def AddSQL(self, sql: str) -> None:
        self._sql_queue.append(self._translate_sql(sql))

    def ExecuteSQLEx(self, sql_or_limit: Any = None, out_map: dict[str, Any] | None = None) -> int | bool:
        if isinstance(sql_or_limit, list):
            count = 0
            with self._connect() as conn:
                cur = conn.cursor()
                for sql in sql_or_limit:
                    cur.execute(self._translate_sql(str(sql)))
                    count += cur.rowcount if cur.rowcount > 0 else 0
                conn.commit()
            return count
        if isinstance(sql_or_limit, str):
            sql = self._translate_sql(sql_or_limit)
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(sql)
                conn.commit()
                if out_map is not None:
                    out_map["executeCount"] = cur.rowcount
            return True
        if isinstance(sql_or_limit, int):
            limit = sql_or_limit
            if limit <= 0:
                limit = len(self._sql_queue)
            use_sql = self._sql_queue[:limit]
            self._sql_queue = self._sql_queue[limit:]
            with self._connect() as conn:
                cur = conn.cursor()
                count = 0
                for sql in use_sql:
                    cur.execute(sql)
                    count += cur.rowcount if cur.rowcount > 0 else 0
                conn.commit()
            return count
        return False

if __name__ == "__main__":
    # 간단한 테스트 실행
    client = OracleDbClient()
    try:
        result = client.SelectSQL("SELECT TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') AS current_time FROM DUAL")
        print(f"현재 DB 시간: {result[0]}")
    except Exception as e:
        print(f"DB 연결 또는 쿼리 실행 중 오류 발생: {e}")