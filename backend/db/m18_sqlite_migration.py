# 데이터베이스 마이그레이션 및 초기화를 수행하는 스크립트
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.storage.m18_sqlite import SQLiteDB
from app.defines import APP_DIR

# 초기 DB 테이블 생성 및 마이그레이션 실행
def run_migrations() -> None:
    db = SQLiteDB()
    # SQL 정의 파일 경로 (defines.py의 APP_DIR 기준)
    migrationPath = os.path.join(APP_DIR, "util", "m18_sqlite_migration.sql")
    
    print(f"스키마 파일({migrationPath})을 이용해 DB 초기화 시작...")
    db.doInitDatabase(migrationPath)
    print("DB 마이그레이션 완료.")

if __name__ == "__main__":
    # 스크립트 직접 실행 시 마이그레이션 구동
    run_migrations()
