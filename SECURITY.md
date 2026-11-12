# Política de segurança

## Reportar uma vulnerabilidade

Não abras uma issue pública. Usa o separador **Security → Report a vulnerability** deste repositório (aviso privado do GitHub). Responderemos com a confirmação de recepção e, depois, com o plano de correcção.

## Regras do projecto

- Nenhum segredo entra no repositório. As chaves ficam em variáveis de ambiente (Vercel e `.env` local, que está no `.gitignore`). Usa `.env.example` como modelo.
- As chaves da API pública são guardadas só como hash. O e-mail associado a uma chave não é publicado.
- A criação de chaves tem limite por e-mail e global, contado na base de dados. A leitura sem chave tem limite por IP.
- O endpoint do cron exige `CRON_SECRET`.
- O site envia CSP, HSTS, `X-Frame-Options`, `X-Content-Type-Options` e `Referrer-Policy` (ver `vercel.json`).
- As dependências são vigiadas pelo Dependabot. O CI corre testes e uma pesquisa de segredos em cada push.

## Se um segredo for exposto

1. Revoga-o de imediato na origem (Supabase, Vercel, etc.) e gera um novo.
2. Actualiza a variável no Vercel e volta a publicar.
3. Remover do histórico do git não chega: o segredo deve ser tratado como comprometido.
