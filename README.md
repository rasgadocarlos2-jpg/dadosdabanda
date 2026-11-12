# Dados da Banda

Projecto independente de dados abertos sobre Angola: indicadores macroeconómicos, Orçamento Geral do Estado (2010–2026) com execução, dados provinciais e um catálogo pesquisável dos documentos do MINFIN. Cada série identifica a fonte original e guarda a data de recolha.

## Arquitectura

| Peça | Tecnologia | Onde |
|---|---|---|
| Site estático | HTML, CSS e JavaScript sem build | `public/` |
| API pública | FastAPI em função serverless no Vercel | `api/index.py` → `app/api/` |
| Base de dados | Supabase (PostgreSQL via PostgREST) | `schema.sql`, `app/supa.py` |
| Recolha automática | Cron semanal do Vercel (`/cron/atualizar`) | `app/api/main.py` |
| Extracção do OGE | Scripts locais com pdfplumber | `scripts/oge/` |
| Símbolos e cores da marca | SVG e tokens em Python | `marca/` |

As observações são só de acréscimo: uma revisão grava uma nova linha e a versão mais recente (por `recolhido_em`) é a que vale. As anteriores ficam visíveis no histórico de cada série.

## Estrutura

```
api/             ponto de entrada do Vercel (reescreve o caminho para a app FastAPI)
app/api/         rotas da API, autenticação por chave, ficha HTML de cada série
app/ingest/      clientes das fontes (Banco Mundial, FMI, OWID, Frankfurter) e gravação
app/supa.py      cliente mínimo do PostgREST
public/          páginas do site e ficheiros estáticos
scripts/oge/     descarga e extracção dos PDF do MINFIN (não vai para produção)
marca/           símbolos SVG e tokens de cor (o manual completo é interno)
tests/           testes com pytest
schema.sql       esquema da base de dados
vercel.json      rotas, cabeçalhos de segurança e cron
```

## Desenvolvimento local

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; em Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # preenche com os teus valores
uvicorn app.api.main:app --reload
```

Testes:

```bash
pytest -q
```

## Deploy

O Vercel publica a partir deste repositório. As variáveis `SUPABASE_URL`, `SUPABASE_KEY` e `CRON_SECRET` são definidas no painel do Vercel, nunca no código. O ficheiro `.vercelignore` exclui `scripts/`, `marca/`, `tests/` e dados locais do pacote publicado.

## Fontes e licença dos dados

Os dados pertencem às fontes originais (Banco Mundial, FMI, MINFIN, BNA, INE, Our World in Data, entre outras), identificadas em cada série e na página de metodologia. A redistribuição segue os termos de cada fonte.

## Segurança

Ver [SECURITY.md](SECURITY.md).
