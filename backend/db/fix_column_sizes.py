import os
import sys

# Get the project root
script_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, PROJECT_ROOT)

from dbclient_oracle import OracleDbClient

def fix_sizes():
    db = OracleDbClient()
    # List of all remaining columns to be boosted to at least 1000
    columns = [
        'vodClass', 'runtime', 'rating', 'genre', 'repRatDate', 
        'repRlsDate', 'ratingMain', 'ratingDate', 'ratingNo', 
        'ratingGrade', 'releaseDate', 'statDate', 'regDate', 
        'modDate', 'codeNm', 'codeNo'
    ]
    
    alter_statements = [f"ALTER TABLE movies MODIFY ({col} VARCHAR2(1000))" for col in columns]
    
    print("오라클 잔여 모든 컬럼 일괄 상향 (1000)...")
    for sql in alter_statements:
        try:
            db.ExecuteSQL(sql)
            print(f"성공: {sql}")
        except Exception as e:
            print(f"실패: {sql}\n에러: {e}")
    print("백업 상향 완료.")

if __name__ == "__main__":
    fix_sizes()
