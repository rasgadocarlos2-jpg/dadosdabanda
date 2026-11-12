from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Fonte, Observacao, Serie, agora
from .sources import FONTES, SERIES


def garantir_fontes_e_series(session: Session) -> None:
    """Cria o que falta. Nunca altera o estado de autorização de uma fonte já existente."""
    for f in FONTES:
        if session.get(Fonte, f["id"]) is None:
            session.add(Fonte(id=f["id"], nome=f["nome"], url=f["url"], estado_autorizacao=f["estado"],
                              licenca=f.get("licenca"), notas=f.get("notas")))
    session.flush()
    for s in SERIES:
        if session.get(Serie, s["id"]) is None:
            session.add(Serie(id=s["id"], fonte_id=s["fonte"], codigo=s["codigo"], nome=s["nome"],
                              unidade=s["unidade"], periodicidade=s.get("periodicidade", "anual")))
    session.commit()


def gravar_observacoes(session: Session, serie_id: str, obs: list[tuple[str, float]],
                       hash_bruto: str | None = None) -> tuple[int, int]:
    """Só insere valores novos ou revistos. Devolve (novas, revistas)."""
    novas = revistas = 0
    for periodo, valor in obs:
        ultimo = session.scalars(
            select(Observacao.valor)
            .where(Observacao.serie_id == serie_id, Observacao.periodo == periodo)
            .order_by(Observacao.recolhido_em.desc(), Observacao.id.desc())
            .limit(1)
        ).first()
        if ultimo is None or ultimo != valor:
            session.add(Observacao(serie_id=serie_id, periodo=periodo, valor=valor,
                                   recolhido_em=agora(), hash_bruto=hash_bruto))
            if ultimo is None:
                novas += 1
            else:
                revistas += 1
    session.commit()
    return novas, revistas
