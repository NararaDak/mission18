import os
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, PROJECT_ROOT)
from dbclient_oracle import OracleDbClient
client = OracleDbClient()
try:
    sql = "SELECT column_name FROM all_tab_columns WHERE table_name = 'MOVIES' AND column_name = 'DIRECTORNM'"
    result = client.SelectSQL(sql)
    print(f"DirectorNm column existence: {result}")
except Exception as e:
    print(f"Error: {e}")
