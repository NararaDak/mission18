from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from common.defines import DB_FILE_PATH


class DbClient:
    def __init__(self)-> None:
        self.db_path = Path(DB_FILE_PATH)
        self._sql_queue: list[str] = []

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def SelectSQL(self, sql: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(sql)
            return [dict(row) for row in cur.fetchall()]

    def ExecuteSQL(self, sql: str) -> bool:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(sql)
            conn.commit()
        return True

    def AddSQL(self, sql: str) -> None:
        self._sql_queue.append(sql)


    def ExecuteSQLEx(self, sql_or_limit: Any = None, out_map: dict[str, Any] | None = None) -> int | bool:
        if isinstance(sql_or_limit, list):
            count = 0
            with self._connect() as conn:
                cur = conn.cursor()
                for sql in sql_or_limit:
                    cur.execute(str(sql))
                    count += cur.rowcount if cur.rowcount > 0 else 0
                conn.commit()
            return count

        if isinstance(sql_or_limit, str):
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(sql_or_limit)
                conn.commit()
                if out_map is not None:
                    out_map["executeCount"] = cur.rowcount
            return True

        # Legacy batch mode: ExecuteSQL(100) / ExecuteSQL(0)
        if isinstance(sql_or_limit, int):
            limit = sql_or_limit
            if limit <= 0:
                limit = len(self._sql_queue)
            use_sql = self._sql_queue[:limit]
            self._sql_queue = self._sql_queue[limit:]
            with self._connect() as conn:
                cur = conn.cursor()
                count = 0
                for sql in use_sql:
                    cur.execute(sql)
                    count += cur.rowcount if cur.rowcount > 0 else 0
                conn.commit()
            return count

        return False
