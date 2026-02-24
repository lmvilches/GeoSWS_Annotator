from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CacheItem:
    key: str
    value: Any
    created_at: float


class SqliteCache:
    """Very small utility cache for:
    - ontology index chunks
    - SPARQL query results
    - external resources results (suggestions/synonyms)
    """

    def __init__(self, path: str):
        self.path = path
        self._init_db()

    def _init_db(self) -> None:
        con = sqlite3.connect(self.path)
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS kv_cache (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            con.commit()
        finally:
            con.close()

    def get(self, key: str) -> Optional[CacheItem]:
        con = sqlite3.connect(self.path)
        try:
            row = con.execute("SELECT key, value_json, created_at FROM kv_cache WHERE key=?", (key,)).fetchone()
            if not row:
                return None
            return CacheItem(key=row[0], value=json.loads(row[1]), created_at=row[2])
        finally:
            con.close()

    def set(self, key: str, value: Any) -> None:
        con = sqlite3.connect(self.path)
        try:
            con.execute(
                "INSERT OR REPLACE INTO kv_cache(key, value_json, created_at) VALUES (?, ?, ?)",
                (key, json.dumps(value, ensure_ascii=False), time.time()),
            )
            con.commit()
        finally:
            con.close()
