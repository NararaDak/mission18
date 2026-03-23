import traceback
from backend.api2db import Api2Db
from backend.db.dbclient_oracle import OracleDbClient

def debug():
    try:
        api = Api2Db()
        client = OracleDbClient()
        
        # filters from the screenshot
        filters = {
            'movieTitle': '',
            'authorName': '',
            'content': '',
            'sentimentLabel': 'all',
            'sentimentScore': 'all',
            'createdStart': '2025-12-20',
            'createdEnd': '2026-03-20'
        }
        
        # Construct raw SQL as done in api2db.py
        where = api._build_review_where_clause(filters)
        sql_raw = f"SELECT r.*, m.title AS movieTitle FROM REVIEWS r LEFT JOIN MOVIES m ON r.movieId = m.movieId {where} ORDER BY r.reviewId DESC LIMIT 10 OFFSET 0"
        
        print("-" * 50)
        print(f"RAW SQL: {sql_raw}")
        
        # Test translation
        sql_trans = client._translate_sql(sql_raw)
        print("-" * 50)
        print(f"TRANSLATED SQL: {sql_trans}")
        print("-" * 50)
        
        # Execute count
        print("Executing COUNT on Oracle...")
        count_res = api.getAllReviewsCount(filters)
        print(f"Success! Total count: {count_res}")
        
        # Execute
        print("Executing SELECT on Oracle...")
        res = client.SelectSQL(sql_raw)
        print(f"Success! Result count: {len(res)}")
        if res:
            print(f"Sample row keys: {list(res[0].keys())}")
            
    except Exception as e:
        print("FAIL!")
        traceback.print_exc()

if __name__ == "__main__":
    debug()
