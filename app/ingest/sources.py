"""Registo das fontes e das séries.

IMPORTANTE: só as fontes com API pública e documentada arrancam como "autorizada".
INE, BNA, lex.ao e Imprensa Nacional arrancam como "pendente": o código de ingestão
recusa-se a tocar-lhes até alguém mudar o estado na base de dados, depois de haver
resposta ao pedido de autorização e de a licença estar lida.

Os códigos dos indicadores abaixo vêm da documentação que conheço e NÃO foram testados
a partir daqui. Os marcados com "confirmar" são os mais incertos.
"""

FONTES = [
    {"id": "banco_mundial", "nome": "Banco Mundial (Indicators API)", "url": "https://data.worldbank.org",
     "estado": "autorizada", "licenca": "Confirmar os termos de utilização antes do lançamento público."},
    {"id": "fmi", "nome": "FMI (DataMapper, WEO)", "url": "https://www.imf.org/external/datamapper",
     "estado": "autorizada", "licenca": "Confirmar os termos de utilização antes do lançamento público."},
    {"id": "frankfurter_bna", "nome": "Frankfurter · referência BNA",
     "url": "https://frankfurter.dev/providers/bna/", "estado": "autorizada",
     "licenca": "Dados do BNA republicados pela Frankfurter (projeto open-source). Licença da Frankfurter em https://frankfurter.dev/license/."},
    {"id": "our_world_in_data", "nome": "Our World in Data",
     "url": "https://ourworldindata.org", "estado": "autorizada",
     "licenca": "CC BY 4.0. Cada série identifica a fonte primária (ex: Energy Institute, UN, WHO) e deve ser citada."},
    {"id": "ine", "nome": "INE Angola", "url": "https://www.ine.gov.ao", "estado": "pendente",
     "notas": "Pedido enviado em 2026-10. A aguardar resposta."},
    {"id": "bna", "nome": "Banco Nacional de Angola", "url": "https://www.bna.ao", "estado": "pendente",
     "notas": "Pedido enviado em 2026-10. A aguardar resposta."},
    {"id": "lex_ao", "nome": "lex.ao", "url": "https://lex.ao", "estado": "pendente",
     "notas": "Pedido enviado em 2026-10. A aguardar resposta."},
    {"id": "imprensa_nacional", "nome": "Imprensa Nacional (Diário da República)",
     "url": "https://www.imprensanacional.gov.ao", "estado": "pendente",
     "notas": "Pedido por enviar — único em falta. Site não permite acesso automatizado sem autorização escrita."},
]

WB_URL = "https://api.worldbank.org/v2/country/AGO/indicator/{codigo}"
IMF_URL = "https://www.imf.org/external/datamapper/api/v1/{codigo}/AGO"
# Frankfurter: base=aoa devolve, por mês, 1 AOA = X cada moeda. Invertemos no parser.
FRANKFURTER_URL = "https://api.frankfurter.dev/v2/rates"
OWID_URL = "https://ourworldindata.org/grapher/{codigo}.csv"

SERIES = [
    {"id": "wb_pib_crescimento", "fonte": "banco_mundial", "tipo": "wb", "codigo": "NY.GDP.MKTP.KD.ZG",
     "nome": "Crescimento anual do PIB real", "unidade": "%"},
    {"id": "wb_pib_usd", "fonte": "banco_mundial", "tipo": "wb", "codigo": "NY.GDP.MKTP.CD",
     "nome": "PIB a preços correntes", "unidade": "USD"},
    {"id": "wb_populacao", "fonte": "banco_mundial", "tipo": "wb", "codigo": "SP.POP.TOTL",
     "nome": "População total", "unidade": "pessoas"},
    {"id": "wb_inflacao", "fonte": "banco_mundial", "tipo": "wb", "codigo": "FP.CPI.TOTL.ZG",
     "nome": "Inflação, preços no consumidor (anual)", "unidade": "%"},
    {"id": "wb_cambio", "fonte": "banco_mundial", "tipo": "wb", "codigo": "PA.NUS.FCRF",
     "nome": "Taxa de câmbio oficial (média anual)", "unidade": "AOA por USD"},
    {"id": "imf_pib_crescimento", "fonte": "fmi", "tipo": "imf", "codigo": "NGDP_RPCH",
     "nome": "Crescimento anual do PIB real", "unidade": "%"},
    {"id": "imf_pib_usd", "fonte": "fmi", "tipo": "imf", "codigo": "NGDPD",
     "nome": "PIB a preços correntes", "unidade": "mil milhões USD"},
    {"id": "imf_inflacao", "fonte": "fmi", "tipo": "imf", "codigo": "PCPIPCH",  # confirmar
     "nome": "Inflação, preços no consumidor (média anual)", "unidade": "%"},
    {"id": "imf_divida", "fonte": "fmi", "tipo": "imf", "codigo": "GGXWDG_NGDP",  # confirmar
     "nome": "Dívida pública bruta", "unidade": "% do PIB"},
    {"id": "bna_cambio_usd", "fonte": "frankfurter_bna", "tipo": "frankfurter", "codigo": "USD",
     "nome": "Câmbio de referência USD/AOA (BNA)", "unidade": "AOA por USD", "periodicidade": "mensal"},
    {"id": "bna_cambio_eur", "fonte": "frankfurter_bna", "tipo": "frankfurter", "codigo": "EUR",
     "nome": "Câmbio de referência EUR/AOA (BNA)", "unidade": "AOA por EUR", "periodicidade": "mensal"},
    {"id": "bna_cambio_cny", "fonte": "frankfurter_bna", "tipo": "frankfurter", "codigo": "CNY",
     "nome": "Câmbio de referência CNY/AOA (BNA)", "unidade": "AOA por CNY", "periodicidade": "mensal"},
    {"id": "bna_cambio_zar", "fonte": "frankfurter_bna", "tipo": "frankfurter", "codigo": "ZAR",
     "nome": "Câmbio de referência ZAR/AOA (BNA)", "unidade": "AOA por ZAR", "periodicidade": "mensal"},
    {"id": "owid_esperanca_vida", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "life-expectancy",
     "nome": "Esperança de vida à nascença", "unidade": "anos"},
    {"id": "owid_mortalidade_infantil", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "child-mortality-rate",
     "nome": "Mortalidade de menores de 5 anos", "unidade": "por 100 nados-vivos"},
    {"id": "owid_co2_per_capita", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "co-emissions-per-capita",
     "nome": "Emissões de CO₂ per capita", "unidade": "toneladas por pessoa"},
    {"id": "owid_producao_petroleo", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "oil-production-by-country",
     "nome": "Produção anual de petróleo", "unidade": "TWh"},
    {"id": "owid_populacao_urbana", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "share-of-population-urban",
     "nome": "Percentagem de população urbana", "unidade": "%"},
    {"id": "owid_internet", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "share-of-individuals-using-the-internet",
     "nome": "Percentagem de pessoas que usam Internet", "unidade": "%"},
    # Saúde (via OWID — reemprega WHO/UN com atribuição)
    {"id": "owid_mortalidade_materna", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "maternal-mortality",
     "nome": "Mortalidade materna", "unidade": "por 100 000 nados-vivos"},
    {"id": "owid_vacina_dtp3", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "share-of-children-immunized-dtp3",
     "nome": "Cobertura da vacina DTP3", "unidade": "% de crianças de 1 ano"},
    {"id": "owid_hiv_prevalencia", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "share-of-population-infected-with-hiv-ihme",
     "nome": "Prevalência de HIV", "unidade": "% da população 15-49"},
    {"id": "owid_fertilidade", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "children-per-woman",
     "nome": "Taxa de fertilidade", "unidade": "filhos por mulher"},
    # Nutrição
    {"id": "owid_desnutricao", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "prevalence-of-undernourishment",
     "nome": "Prevalência de desnutrição", "unidade": "% da população"},
    # Energia
    {"id": "owid_eletricidade", "fonte": "our_world_in_data", "tipo": "owid", "codigo": "share-of-the-population-with-access-to-electricity",
     "nome": "Acesso a eletricidade", "unidade": "% da população"},
    # Educação (via Banco Mundial — tem Angola)
    {"id": "wb_alfabetizacao", "fonte": "banco_mundial", "tipo": "wb", "codigo": "SE.ADT.LITR.ZS",
     "nome": "Taxa de alfabetização de adultos", "unidade": "%"},
    {"id": "wb_gasto_educacao", "fonte": "banco_mundial", "tipo": "wb", "codigo": "SE.XPD.TOTL.GD.ZS",
     "nome": "Gasto público em educação", "unidade": "% do PIB"},
    # Comércio & investimento (Banco Mundial)
    {"id": "wb_comercio", "fonte": "banco_mundial", "tipo": "wb", "codigo": "NE.TRD.GNFS.ZS",
     "nome": "Comércio (export + import)", "unidade": "% do PIB"},
    {"id": "wb_ide", "fonte": "banco_mundial", "tipo": "wb", "codigo": "BX.KLT.DINV.CD.WD",
     "nome": "Investimento direto estrangeiro, entradas", "unidade": "USD"},
    {"id": "wb_remessas", "fonte": "banco_mundial", "tipo": "wb", "codigo": "BX.TRF.PWKR.CD.DT",
     "nome": "Remessas pessoais recebidas", "unidade": "USD"},
    # Comunicações
    {"id": "wb_telemovel", "fonte": "banco_mundial", "tipo": "wb", "codigo": "IT.CEL.SETS.P2",
     "nome": "Subscrições móveis", "unidade": "por 100 pessoas"},
]
