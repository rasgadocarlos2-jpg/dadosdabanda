"""Entrada ASGI do Vercel.

O Vercel reescreve o pedido para `/api/index` e passa o caminho original na
query string `?__path=...`. Este middleware põe esse valor de volta no scope.
"""
from urllib.parse import parse_qs, urlencode

from app.api.main import app as real_app


class ReescreverPath:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            qs = scope.get("query_string", b"").decode("latin-1")
            params = parse_qs(qs, keep_blank_values=True)
            if "__path" in params:
                path = params.pop("__path")[0] or "/"
                scope = {
                    **scope,
                    "path": path,
                    "raw_path": path.encode("latin-1"),
                    "query_string": urlencode(params, doseq=True).encode("latin-1"),
                }
        await self.inner(scope, receive, send)


app = ReescreverPath(real_app)
