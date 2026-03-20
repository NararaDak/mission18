import os
import sys

# Get the script folder
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, PROJECT_ROOT)

from dbclient_oracle import OracleDbClient

client = OracleDbClient()

try:
    sql = "SELECT object_name, status FROM all_objects WHERE object_name = 'TRG_MOVIES_ID'"
    result = client.SelectSQL(sql)
    print(f"Trigger TRG_MOVIES_ID Object Status: {result}")
except Exception as e:
    print(f"Error checking trigger object: {e}")
