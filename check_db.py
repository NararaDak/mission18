import sqlite3
import os

# Correct path according to common.defines
dbPath = r"d:\project\misstion18\data\db\mission18.db"
if not os.path.exists(dbPath):
    print(f"Database path not found: {dbPath}")
else:
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM REVIEWS;")
    revCount = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM MOVIES;")
    movCount = cursor.fetchone()[0]
    print(f"Reviews: {revCount}, Movies: {movCount}")
    
    # Check if there are multiple movies or something sticking it back to 1 page
    cursor.execute("SELECT * FROM REVIEWS LIMIT 5;")
    rows = cursor.fetchall()
    print("Sample Reviews:", rows)
    
    conn.close()
