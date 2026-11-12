import hashlib
import secrets
import time
from collections import defaultdict, deque

from fastapi import Depends, Header, HTTPException, Request

from ..config import LIMITE_POR_MINUTO
from ..supa import Supa, get_supa


def hash_chave(chave: str) -> str:
    return hashlib.sha256(chave.encode("utf-8")).hexdigest()


def criar_chave(supa: Supa, email: str, limite: int = LIMITE_POR_MINUTO) -> str:
    """Cria uma chave nova e devolve-a em claro (só aparece esta vez)."""
    chave = "ddb_" + secrets.token_urlsafe(32)
    supa.insert("chaves_api", {
        "chave_hash": hash_chave(chave),
        "email": email,
        "ativa": True,
        "limite_por_minuto": limite,
        "criada_em": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, returning=False)
    return chave


class Limitador:
    """Janela deslizante de 60 s por chave, em memória por processo.

    No serverless (Vercel) cada invocação pode cair numa instância diferente,
    pelo que o limite é só uma defesa aproximada. Para v2, mover para Supabase
    (tabela de pedidos recentes) ou Upstash Redis.
    """

    def __init__(self):
        self.janelas: dict[int | str, deque] = defaultdict(deque)

    def verificar(self, chave_id: int | str, limite: int, agora: float | None = None) -> int | None:
        t = time.monotonic() if agora is None else agora
        janela = self.janelas[chave_id]
        while janela and t - janela[0] >= 60:
            janela.popleft()
        if len(janela) >= limite:
            return max(1, int(60 - (t - janela[0])) + 1)
        janela.append(t)
        return None


def chave_opcional(request: Request, x_api_key: str | None = Header(default=None),
                   supa: Supa = Depends(get_supa)) -> dict | None:
    """Leitura pública: sem chave conta por IP, com chave conta pela chave."""
    if x_api_key:
        return chave_atual(request, x_api_key, supa)
    fwd = request.headers.get("x-forwarded-for", "")
    ip = fwd.split(",")[0].strip() or (request.client.host if request.client else "?")
    espera = request.app.state.limitador.verificar(f"ip:{ip}", LIMITE_POR_MINUTO)
    if espera is not None:
        raise HTTPException(429, "Limite de pedidos excedido.", headers={"Retry-After": str(espera)})
    return None


def chave_atual(request: Request, x_api_key: str | None = Header(default=None),
                supa: Supa = Depends(get_supa)) -> dict:
    if not x_api_key:
        raise HTTPException(401, "Falta o cabeçalho X-API-Key. Gera uma chave gratuita em /api.html.")
    chave = supa.first("chaves_api", columns="id,limite_por_minuto,ativa",
                       filters={"chave_hash": f"eq.{hash_chave(x_api_key)}"})
    if chave is None or not chave.get("ativa"):
        raise HTTPException(401, "Chave inválida ou desativada.")
    espera = request.app.state.limitador.verificar(chave["id"], chave["limite_por_minuto"])
    if espera is not None:
        raise HTTPException(429, "Limite de pedidos excedido.", headers={"Retry-After": str(espera)})
    return chave
