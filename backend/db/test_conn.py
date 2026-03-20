import os
import sys

# Get the script folder
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the project root (assuming mission18 is the root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, PROJECT_ROOT)

print(f"Script dir: {script_dir}")
print(f"Project root inferred: {PROJECT_ROOT}")

from dbclient_oracle import OracleDbClient

client = OracleDbClient()
print(f"User from client: {client.db_user}")
print(f"Password from client: {client.db_password}")
print(f"Wallet Path from client: {client.wallet_path}")
print(f"DSN from client: {client.dsn}")

try:
    result = client.SelectSQL("SELECT user FROM dual")
    print(f"Login success: {result}")
except Exception as e:
    print(f"Login failed: {e}")
