# Oracle 데이터베이스 마이그레이션 및 초기화를 수행하는 스크립트
import os
from dbclient_oracle import OracleDbClient
from common.defines import APP_DIR

# 초기 DB 테이블 생성 및 마이그레이션 실행
def run_migrations() -> None:
    db = OracleDbClient()
    migrationPath = os.path.join(os.path.dirname(__file__), "m18_oracle_migration.sql")
    print(f"스키마 파일({migrationPath})을 이용해 Oracle DB 초기화 시작...")
    with open(migrationPath, encoding="utf-8") as f:
        sql_script = f.read()
    import re
    # 1. '/'로 먼저 구분 (PL/SQL 블록 구분용)
    blocks = [b.strip() for b in sql_script.split('/') if b.strip()]
    statements = []
    
    for block in blocks:
        # 블록 내에서 트리거 생성 시작 위치 찾기 (정확한 매칭을 위해 re.IGNORECASE 사용)
        match = re.search(r'CREATE\s+(OR\s+REPLACE\s+)?TRIGGER', block, re.IGNORECASE)
        if match:
            start_idx = match.start()
            # 트리거 이전 부분은 일반 SQL 문들의 집합일 수 있음
            pre_trigger = block[:start_idx].strip()
            if pre_trigger:
                parts = [s.strip() for s in pre_trigger.split(';') if s.strip()]
                statements.extend(parts)
            # 트리거 본문 자체
            statements.append(block[start_idx:].strip())
        else:
            # 트리거가 없는 블록은 전체를 ';'로 분리
            parts = [s.strip() for s in block.split(';') if s.strip()]
            statements.extend(parts)

    for stmt in statements:
        # 불필요한 공백 제거 및 주석만 있는 문장 무시
        if not stmt.strip() or not re.sub(r'--.*', '', stmt).strip():
            continue
        
        # Oracle은 실행 시 문장 끝에 ';'가 있으면 안 됨 (PL/SQL 블록 제외)
        exec_stmt = stmt.strip()
        if not (exec_stmt.upper().startswith("BEGIN") or "TRIGGER" in exec_stmt.upper()):
            if exec_stmt.endswith(";"):
                exec_stmt = exec_stmt[:-1].strip()

        try:
            db.ExecuteSQL(exec_stmt)
        except Exception as e:
            # DROP 명령어 실패시는 무시 (이미 존재하지 않는 경우 등)
            if "DROP" in stmt.upper():
                continue
            # 이미 존재하는 인덱스/테이블 에러 무시
            if "ORA-00955" in str(e) or "ORA-01408" in str(e):
                continue
            print(f"실패한 쿼리: {stmt[:150]}...\n에러: {e}")
    print("Oracle DB 마이그레이션 완료.")

if __name__ == "__main__":
    run_migrations()
