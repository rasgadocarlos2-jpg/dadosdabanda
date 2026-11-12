import json
import time

import httpx


def fetch(client: httpx.Client, url: str, params: dict | None, delay: float, tries: int = 3):
    """GET com tentativas e espera crescente. Devolve (texto, url_final)."""
    for n in range(tries):
        try:
            r = client.get(url, params=params)
            if r.status_code in (429, 500, 502, 503, 504):
                raise httpx.HTTPStatusError(f"estado {r.status_code}", request=r.request, response=r)
            r.raise_for_status()
            time.sleep(delay)
            return r.text, str(r.url)
        except httpx.HTTPError:
            if n == tries - 1:
                raise
            time.sleep(delay * 2 ** (n + 1))


def parse_wb(texto: str) -> list[tuple[str, float]]:
    dados = json.loads(texto)
    if not isinstance(dados, list) or len(dados) < 2 or dados[1] is None:
        raise ValueError(f"resposta inesperada do Banco Mundial: {texto[:200]}")
    return sorted((str(r["date"]), float(r["value"])) for r in dados[1] if r.get("value") is not None)


def parse_imf(texto: str, codigo: str) -> list[tuple[str, float]]:
    dados = json.loads(texto)
    try:
        valores = dados["values"][codigo]["AGO"]
    except (KeyError, TypeError):
        raise ValueError(f"resposta inesperada do FMI: {texto[:200]}")
    return sorted((str(a), float(v)) for a, v in valores.items() if v is not None)


def parse_owid(texto: str, codigo: str | None = None) -> list[tuple[str, float]]:
    """CSV da Our World in Data: Entity,Code,Year,<Valor>[,<extras…>]. Filtra AGO.

    Pega na primeira coluna numérica depois de Year (ignora colunas de texto como
    "annotations" ou "region").
    """
    linhas = texto.splitlines()
    if not linhas:
        raise ValueError("resposta vazia da OWID")
    cab = linhas[0].split(",")
    if len(cab) < 4 or cab[0].strip() != "Entity":
        raise ValueError(f"cabeçalho OWID inesperado: {linhas[0][:120]}")
    saida = []
    for linha in linhas[1:]:
        if not linha:
            continue
        partes = linha.split(",")
        if len(partes) < 4 or partes[1].strip() != "AGO":
            continue
        try:
            ano = str(int(partes[2]))
        except ValueError:
            continue
        valor = None
        for p in partes[3:]:
            p = p.strip()
            if not p:
                continue
            try:
                valor = float(p); break
            except ValueError:
                continue
        if valor is None:
            continue
        saida.append((ano, valor))
    if not saida:
        raise ValueError(f"sem dados AGO na série {codigo}: {linhas[0][:120]}")
    return sorted(saida)


def parse_frankfurter(texto: str, codigo: str) -> list[tuple[str, float]]:
    """Filtra pelo quote `codigo` e devolve AOA por unidade (invertido). Período "AAAA-MM"."""
    dados = json.loads(texto)
    if not isinstance(dados, list):
        raise ValueError(f"resposta inesperada da Frankfurter: {texto[:200]}")
    saida = []
    for r in dados:
        if r.get("quote") != codigo or r.get("rate") in (None, 0):
            continue
        periodo = str(r["date"])[:7]  # "AAAA-MM"
        saida.append((periodo, round(1.0 / float(r["rate"]), 6)))
    if not saida:
        raise ValueError(f"nenhuma cotação {codigo} na resposta Frankfurter: {texto[:200]}")
    return sorted(saida)
