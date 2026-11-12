"""Cliente mínimo para a REST API do Supabase (PostgREST).

Dispensa SQLAlchemy e psycopg no serverless. Usa a anon key — basta ter RLS
desativado nas tabelas (que é o nosso caso: a BD só é lida via este backend).
"""
import os
from typing import Any, Iterable

import httpx


class Supa:
    def __init__(self, url: str | None = None, key: str | None = None):
        self.url = (url or os.environ["SUPABASE_URL"]).rstrip("/")
        key = key or os.environ["SUPABASE_KEY"]
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.Client(timeout=10.0)

    def _endpoint(self, table: str) -> str:
        return f"{self.url}/rest/v1/{table}"

    def select(self, table: str, *, columns: str = "*", order: str | None = None,
               limit: int | None = None, filters: dict[str, str] | None = None) -> list[dict]:
        params: dict[str, Any] = {"select": columns}
        if order:
            params["order"] = order
        if limit:
            params["limit"] = str(limit)
        if filters:
            params.update(filters)
        r = self.client.get(self._endpoint(table), headers=self.headers, params=params)
        r.raise_for_status()
        return r.json()

    def first(self, table: str, **kwargs) -> dict | None:
        kwargs["limit"] = 1
        rows = self.select(table, **kwargs)
        return rows[0] if rows else None

    def insert(self, table: str, data: dict | list[dict], *, returning: bool = True) -> dict | list[dict]:
        headers = {**self.headers, "Prefer": "return=representation" if returning else "return=minimal"}
        r = self.client.post(self._endpoint(table), headers=headers, json=data)
        r.raise_for_status()
        if not returning:
            return {}
        res = r.json()
        if isinstance(data, dict) and isinstance(res, list):
            return res[0]
        return res


# Instância singleton pedida pelos endpoints via FastAPI Depends()
_singleton: Supa | None = None


def get_supa() -> Supa:
    global _singleton
    if _singleton is None:
        _singleton = Supa()
    return _singleton
