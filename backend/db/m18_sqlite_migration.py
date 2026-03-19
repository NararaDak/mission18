import os
from app.storage.m18_sqlite import SQLiteDB
from app.defines import APP_DIR

def run_migrations() -> None:
    """
    데이터베이스 초기화 및 테이블 생성을 실행합니다.
    """
    db = SQLiteDB()
    # migration SQL 파일 경로 설정
    migrationPath = os.path.join(APP_DIR, "util", "m18_sqlite_migration.sql")
    
    print(f"Starting database initialization using {migrationPath}...")
    db.doInitDatabase(migrationPath)
    print("Database processing completed.")

if __name__ == "__main__":
    run_migrations()
