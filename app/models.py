from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def agora() -> datetime:
    return datetime.now(timezone.utc)


class Fonte(Base):
    """Uma fonte de dados. `estado_autorizacao` decide se a ingestão pode correr."""

    __tablename__ = "fontes"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    url: Mapped[str] = mapped_column(String(300))
    # autorizada | pendente | negada
    estado_autorizacao: Mapped[str] = mapped_column(String(20), default="pendente")
    licenca: Mapped[str | None] = mapped_column(Text, nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    series: Mapped[list["Serie"]] = relationship(back_populates="fonte")


class Serie(Base):
    __tablename__ = "series"

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    fonte_id: Mapped[str] = mapped_column(ForeignKey("fontes.id"))
    codigo: Mapped[str] = mapped_column(String(60))
    nome: Mapped[str] = mapped_column(String(200))
    unidade: Mapped[str] = mapped_column(String(40))
    periodicidade: Mapped[str] = mapped_column(String(20), default="anual")
    url_consulta: Mapped[str | None] = mapped_column(String(500), nullable=True)

    fonte: Mapped[Fonte] = relationship(back_populates="series")
    observacoes: Mapped[list["Observacao"]] = relationship(back_populates="serie")


class Observacao(Base):
    """Uma observação por período e por recolha. Valores revistos geram nova linha."""

    __tablename__ = "observacoes"
    __table_args__ = (UniqueConstraint("serie_id", "periodo", "recolhido_em"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    serie_id: Mapped[str] = mapped_column(ForeignKey("series.id"), index=True)
    periodo: Mapped[str] = mapped_column(String(10))  # "2024" ou "2024-03"
    valor: Mapped[float] = mapped_column(Float)
    recolhido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    hash_bruto: Mapped[str | None] = mapped_column(String(64), nullable=True)

    serie: Mapped[Serie] = relationship(back_populates="observacoes")


class ExecucaoRecolha(Base):
    __tablename__ = "execucoes_recolha"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conector: Mapped[str] = mapped_column(String(60))
    iniciada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    terminada_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="a_correr")  # ok | erro | ignorada
    mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)
    novas: Mapped[int] = mapped_column(Integer, default=0)
    revistas: Mapped[int] = mapped_column(Integer, default=0)


class ChaveApi(Base):
    """Só guardamos o hash da chave. A chave em claro é mostrada uma vez, ao criar."""

    __tablename__ = "chaves_api"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chave_hash: Mapped[str] = mapped_column(String(64), unique=True)
    email: Mapped[str] = mapped_column(String(200))
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
    limite_por_minuto: Mapped[int] = mapped_column(Integer, default=60)
