import pytest
from fastapi.testclient import TestClient

from app.api.auth import Limitador, criar_chave
import os
import pytest

if not os.environ.get("SUPABASE_URL"):
    pytest.skip("API agora corre contra Supabase REST; testes necessitam SUPABASE_URL para integração.", allow_module_level=True)

from app.api.main import app  # noqa
from app.db import get_session
from app.ingest.store import garantir_fontes_e_series, gravar_observacoes


@pytest.fixture()
def cliente(session):
    garantir_fontes_e_series(session)
    gravar_observacoes(session, "wb_pib_crescimento", [("2023", 1.0), ("2024", 3.0)])
    gravar_observacoes(session, "imf_pib_crescimento", [("2023", 1.2), ("2024", 2.8)])
    app.dependency_overrides[get_session] = lambda: session
    app.state.limitador = Limitador()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def chave(session, cliente):
    return {"X-API-Key": criar_chave(session, "teste@exemplo.ao", limite=3)}


def test_saude_e_fontes_sao_abertas(cliente):
    assert cliente.get("/saude").json() == {"estado": "ok"}
    fontes = {f["id"]: f for f in cliente.get("/v1/fontes").json()}
    assert fontes["ine"]["estado_autorizacao"] == "pendente"


def test_series_exigem_chave(cliente):
    assert cliente.get("/v1/series").status_code == 401
    assert cliente.get("/v1/series", headers={"X-API-Key": "errada"}).status_code == 401


def test_observacoes_json_com_fonte(cliente, chave):
    r = cliente.get("/v1/series/wb_pib_crescimento/observacoes", headers=chave)
    corpo = r.json()
    assert r.status_code == 200
    assert corpo["fonte"].startswith("Banco Mundial")
    assert [o["periodo"] for o in corpo["observacoes"]] == ["2023", "2024"]


def test_filtro_de_periodo(cliente, chave):
    r = cliente.get("/v1/series/wb_pib_crescimento/observacoes?de=2024", headers=chave)
    assert [o["periodo"] for o in r.json()["observacoes"]] == ["2024"]


def test_observacoes_csv(cliente, chave):
    r = cliente.get("/v1/series/wb_pib_crescimento/observacoes?formato=csv", headers=chave)
    assert r.headers["content-type"].startswith("text/csv")
    linhas = r.text.strip().splitlines()
    assert linhas[0].startswith("periodo,valor,unidade,fonte")
    assert len(linhas) == 3


def test_mostra_o_valor_revisto(session, cliente, chave):
    gravar_observacoes(session, "wb_pib_crescimento", [("2024", 3.4)])
    obs = cliente.get("/v1/series/wb_pib_crescimento/observacoes", headers=chave).json()["observacoes"]
    assert obs[-1]["valor"] == 3.4 and len(obs) == 2


def test_comparar_duas_series(cliente, chave):
    r = cliente.get("/v1/comparar?series=wb_pib_crescimento&series=imf_pib_crescimento", headers=chave)
    corpo = r.json()
    assert r.status_code == 200
    assert corpo["linhas"][0]["diferenca"] == pytest.approx(0.2)
    assert "não indicam" in corpo["aviso"].lower()


def test_serie_inexistente(cliente, chave):
    assert cliente.get("/v1/series/nao_existe", headers=chave).status_code == 404


def test_limite_de_pedidos(cliente, chave):
    codigos = [cliente.get("/v1/series", headers=chave).status_code for _ in range(4)]
    assert codigos == [200, 200, 200, 429]
    assert "retry-after" in cliente.get("/v1/series", headers=chave).headers


def test_limitador_liberta_apos_60s():
    lim = Limitador()
    assert lim.verificar(1, 1, agora=0.0) is None
    assert lim.verificar(1, 1, agora=10.0) is not None
    assert lim.verificar(1, 1, agora=61.0) is None
