import json

import pytest
from sqlalchemy import func, select

from app.ingest import clients
from app.ingest.run import executar
from app.ingest.sources import SERIES
from app.ingest.store import garantir_fontes_e_series, gravar_observacoes
from app.models import ExecucaoRecolha, Fonte, Observacao

WB = json.dumps([{"page": 1}, [{"date": "2024", "value": 3.0}, {"date": "2023", "value": 1.0},
                               {"date": "2022", "value": None}]])
IMF_TPL = '{{"values": {{"{c}": {{"AGO": {{"2023": 1.2, "2024": 2.8, "2025": null}}}}}}}}'
FRANKFURTER = json.dumps([
    {"date": d, "base": "AOA", "quote": q, "rate": r}
    for d, q, r in [
        ("2024-01-01", "USD", 0.00121), ("2024-01-01", "EUR", 0.00111),
        ("2024-01-01", "CNY", 0.00865), ("2024-01-01", "ZAR", 0.02232),
        ("2024-02-01", "USD", 0.00119), ("2024-02-01", "EUR", 0.00109),
        ("2024-02-01", "CNY", 0.00858), ("2024-02-01", "ZAR", 0.02220),
    ]
])

OWID = "Entity,Code,Year,Valor\nAngola,AGO,2023,1.5\nAngola,AGO,2024,2.5\nNamibia,NAM,2024,9.0\n"


def falso_fetch(client, url, params, delay):
    if "worldbank" in url:
        return WB, url
    if "frankfurter" in url:
        return FRANKFURTER, url
    if "ourworldindata" in url:
        return OWID, url
    codigo = url.rstrip("/").split("/")[-2]
    return IMF_TPL.format(c=codigo), url


def test_parse_wb_e_imf():
    assert clients.parse_wb(WB) == [("2023", 1.0), ("2024", 3.0)]
    assert clients.parse_imf(IMF_TPL.format(c="NGDP_RPCH"), "NGDP_RPCH") == [("2023", 1.2), ("2024", 2.8)]


def test_parse_frankfurter_inverte_e_filtra_quote():
    usd = clients.parse_frankfurter(FRANKFURTER, "USD")
    assert usd == [("2024-01", round(1 / 0.00121, 6)), ("2024-02", round(1 / 0.00119, 6))]
    with pytest.raises(ValueError):
        clients.parse_frankfurter(FRANKFURTER, "GBP")


@pytest.mark.parametrize("mau", ["[]", "{}"])
def test_parse_resposta_inesperada(mau):
    with pytest.raises(ValueError):
        clients.parse_wb(mau)
    with pytest.raises(ValueError):
        clients.parse_imf(mau, "X")


def test_revisao_guarda_as_duas_versoes(session):
    garantir_fontes_e_series(session)
    assert gravar_observacoes(session, "wb_pib_crescimento", [("2024", 3.0)]) == (1, 0)
    assert gravar_observacoes(session, "wb_pib_crescimento", [("2024", 3.0)]) == (0, 0)
    assert gravar_observacoes(session, "wb_pib_crescimento", [("2024", 3.4)]) == (0, 1)
    n = session.scalar(select(func.count()).select_from(Observacao))
    assert n == 2


def test_executar_grava_tudo_e_guarda_bruto(session, tmp_path):
    execs = executar(session, None, tmp_path, delay=0, fetch_fn=falso_fetch)
    assert len(execs) == len(SERIES)
    assert all(e.estado == "ok" for e in execs)
    assert len(list(tmp_path.glob("*.json"))) == len(SERIES)


def test_fonte_nao_autorizada_nao_e_recolhida(session, tmp_path):
    garantir_fontes_e_series(session)
    session.get(Fonte, "banco_mundial").estado_autorizacao = "pendente"
    session.commit()
    chamadas = []

    def fetch(*a):
        chamadas.append(a)
        return falso_fetch(*a)

    execs = executar(session, None, tmp_path, delay=0, fetch_fn=fetch)
    wb = [e for e in execs if e.conector.startswith("wb_")]
    assert wb and all(e.estado == "ignorada" for e in wb)
    assert not any("worldbank" in c[1] for c in chamadas)


def test_ine_arranca_pendente(session):
    garantir_fontes_e_series(session)
    for f in ("ine", "bna", "lex_ao", "imprensa_nacional"):
        assert session.get(Fonte, f).estado_autorizacao == "pendente"


def test_garantir_nao_repoe_autorizacao_alterada(session):
    garantir_fontes_e_series(session)
    session.get(Fonte, "ine").estado_autorizacao = "autorizada"
    session.commit()
    garantir_fontes_e_series(session)
    assert session.get(Fonte, "ine").estado_autorizacao == "autorizada"


def test_falha_numa_serie_nao_para_as_outras(session, tmp_path):
    def fetch(client, url, params, delay):
        if "NY.GDP.MKTP.CD" in url:
            raise RuntimeError("ligação caiu")
        return falso_fetch(client, url, params, delay)

    execs = executar(session, None, tmp_path, delay=0, fetch_fn=fetch)
    erros = [e for e in execs if e.estado == "erro"]
    assert [e.conector for e in erros] == ["wb_pib_usd"]
    assert sum(e.estado == "ok" for e in execs) == len(SERIES) - 1
