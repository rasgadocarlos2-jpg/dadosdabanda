import os

# SQLite para desenvolvimento local. Em produção, define DATABASE_URL com o
# endereço PostgreSQL do Supabase (postgresql+psycopg://...).
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dadosdabanda.db")

# Limite de pedidos por minuto para chaves novas (pode ser ajustado por chave).
LIMITE_POR_MINUTO = int(os.getenv("LIMITE_POR_MINUTO", "60"))
