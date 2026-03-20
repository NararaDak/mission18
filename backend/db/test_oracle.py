import oracledb
import os

# 1. 경로 설정 (반드시 r을 붙이세요)
wallet_path = r"D:\02.영역\oracle_cloud\database\Wallet_FXEEDB2VI08RPM2S"
db_user = "ADMIN"
db_password = "Abc123456789!"  # DBeaver에서 성공한 그 비번!
dsn_name = "fxeedb2vi08rpm2s_low"

try:
    # 2. Thin 모드에서는 환경 변수로 지갑 위치를 알려주는 것이 가장 확실합니다.
    os.environ["TNS_ADMIN"] = wallet_path

    # 3. 접속 실행 (Thin 모드 전용 파라미터 구성)
    # wallet_location과 config_dir을 동시에 지정합니다.
    connection = oracledb.connect(
        user=db_user,
        password=db_password,
        dsn=dsn_name,
        config_dir=wallet_path,
        wallet_location=wallet_path,
        wallet_password="Nabidream!@123456" 
    )

    print("🎉 [Thin Mode] 드디어 접속에 성공했습니다!")

    # 4. 데이터 조회 테스트
    with connection.cursor() as cursor:
        cursor.execute("SELECT TO_CHAR(SYSDATE, 'YYYY-MM-DD HH24:MI:SS') FROM DUAL")
        row = cursor.fetchone()
        print(f"현재 DB 시간: {row[0]}")

except oracledb.Error as e:
    error_obj, = e.args
    print(f"❌ 접속 실패 코드: {error_obj.code}")
    print(f"❌ 에러 상세 메시지: {error_obj.message}")

finally:
    if 'connection' in locals():
        connection.close()