"""Comandos de administração.

  python -m app.cli iniciar-bd                         cria as tabelas e regista as fontes
  python -m app.cli criar-chave --email x@y.ao         cria uma chave de API (mostrada uma vez)
  python -m app.cli autorizar --fonte ine --estado autorizada --licenca "texto"
  python -m app.cli sql                                escreve o SQL (PostgreSQL) para colar no Supabase
"""
import argparse

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from .api.auth import criar_chave
from .db import Base, SessionLocal, engine
from .ingest.store import garantir_fontes_e_series
from .models import Fonte


def main():
    ap = argparse.ArgumentParser(prog="app.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("iniciar-bd")
    sub.add_parser("sql")
    c = sub.add_parser("criar-chave")
    c.add_argument("--email", required=True)
    c.add_argument("--limite", type=int, default=60)
    a = sub.add_parser("autorizar")
    a.add_argument("--fonte", required=True)
    a.add_argument("--estado", required=True, choices=["autorizada", "pendente", "negada"])
    a.add_argument("--licenca")
    args = ap.parse_args()

    if args.cmd == "sql":
        dialeto = postgresql.dialect()
        for t in Base.metadata.sorted_tables:
            print(str(CreateTable(t).compile(dialect=dialeto)).strip() + ";\n")
            for i in t.indexes:
                print(str(CreateIndex(i).compile(dialect=dialeto)).strip() + ";\n")
        return

    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        garantir_fontes_e_series(session)
        if args.cmd == "iniciar-bd":
            print("Base de dados pronta.")
        elif args.cmd == "criar-chave":
            print("Guarda esta chave, não volta a ser mostrada:\n" + criar_chave(session, args.email, args.limite))
        elif args.cmd == "autorizar":
            fonte = session.get(Fonte, args.fonte)
            if fonte is None:
                raise SystemExit(f"Fonte '{args.fonte}' não existe.")
            fonte.estado_autorizacao = args.estado
            if args.licenca:
                fonte.licenca = args.licenca
            session.commit()
            print(f"{fonte.id}: {fonte.estado_autorizacao}")


if __name__ == "__main__":
    main()
