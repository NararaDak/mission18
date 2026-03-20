import os
import sys
import configparser
from pathlib import Path

# Get the project root
script_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, PROJECT_ROOT)

from backend.db.dbclient import DbClient
from backend.db.dbclient_oracle import OracleDbClient

def selectDb():
    """
    m18.ini 설정 파일에서 dbtype을 읽어 
    해당하는 DB 클라이언트(DbClient 또는 OracleDbClient) 인스턴스를 반환합니다.
    """
    ini_path = os.path.join(PROJECT_ROOT, "common", "m18.ini")
    
    config = configparser.ConfigParser()
    if os.path.exists(ini_path):
        config.read(ini_path, encoding='utf-8')
    
    # 기본값은 sqlite. inline 주석(#)이 있을 수 있으므로 분할 후 처리.
    raw_db_type = config.get("selectordb", "dbtype", fallback="sqlite")
    db_type = raw_db_type.split('#')[0].strip().lower()

    if db_type == "oracle":
        # print("DbSelector: OracleDbClient를 선택했습니다.")
        return OracleDbClient()
    else:
        # print("DbSelector: SQLite DbClient를 선택했습니다.")
        return DbClient()

# DbSelector 클래스로도 사용할 수 있도록 래퍼 제공
class DbSelector:
    @staticmethod
    def get_client():
        return selectDb()

if __name__ == "__main__":
    db = selectDb()
    print(f"선택된 DB 클라이언트: {type(db).__name__}")
