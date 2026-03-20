import traceback
from backend.api2db import Api2Db

def debug():
    try:
        api = Api2Db()
        print("Backend starting debug query...")
        # Filters from the screenshot: 2025-12-20 ~ 2026-03-20
        res = api.getAllReviews({
            'createdStart': '2025-12-20',
            'createdEnd': '2026-03-20',
            'START': 0,
            'COUNT': 10
        })
        print(f"Success! Result count: {len(res)}")
    except Exception as e:
        print("FAIL!")
        traceback.print_exc()

if __name__ == "__main__":
    debug()
