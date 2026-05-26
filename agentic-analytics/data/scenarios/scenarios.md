# Scenarios — Regras de Negócio para Text-to-SQL Agent
# Padrão: text2sql-framework (cada ## heading = uma regra)
# O agente usa lookup_example(topic) para recuperar a regra relevante.

## alto risco
Clientes com score_risco >= 7 são classificados como alto risco de inadimplência.
Usar sempre: WHERE fp.score_risco >= 7
Nunca usar threshold arbitrário diferente de 7 sem instrução explícita.

Exemplo:
    SELECT segmento, COUNT(*) as clientes_alto_risco, AVG(roae) as roae_medio
    FROM fact_pricing_snapshot fp
    WHERE fp.score_risco >= 7
      AND fp.safra = (SELECT MAX(safra) FROM fact_pricing_snapshot)
    GROUP BY segmento
    ORDER BY clientes_alto_risco DESC
    LIMIT 50

## última safra
"Última safra" = (SELECT MAX(safra) FROM fact_pricing_snapshot)
Sempre usar subquery, nunca hardcode de data.
Formato de safra: YYYY-MM (ex: '2026-03')

Exemplo:
    WHERE safra = (SELECT MAX(safra) FROM fact_pricing_snapshot)

## ROAE
ROAE = Return on Average Equity (Retorno sobre Patrimônio Líquido Médio).
Coluna: roae na tabela fact_pricing_snapshot (já calculada, em %).
Não recalcular. Usar AVG(roae) para médias por grupo.

Exemplo:
    SELECT safra, segmento, AVG(roae) as roae_medio
    FROM fact_pricing_snapshot
    GROUP BY safra, segmento
    ORDER BY safra DESC, roae_medio ASC
    LIMIT 100

## margem líquida
Margem líquida = (receita - custo) / receita * 100 (em %).
Coluna: margem_liquida na tabela fact_pricing_snapshot (já calculada).
Não recalcular. Usar AVG(margem_liquida) para médias.

Exemplo:
    SELECT segmento, AVG(margem_liquida) as margem_media
    FROM fact_pricing_snapshot
    WHERE safra >= '2025-01'
    GROUP BY segmento
    ORDER BY margem_media
    LIMIT 50

## pior desempenho
"Pior" = ORDER BY métrica ASC (menor valor = pior).
Para margem: ORDER BY margem_liquida ASC
Para ROAE: ORDER BY roae ASC
Para inadimplência: ORDER BY inadimplente DESC (mais inadimplentes = pior)

## comparar safras
Para comparar duas ou mais safras, usar filtro com IN ou BETWEEN.
Exemplo:
    SELECT safra, segmento, AVG(margem_liquida) as margem
    FROM fact_pricing_snapshot
    WHERE safra IN ('2025-12', '2026-01', '2026-02', '2026-03')
    GROUP BY safra, segmento
    ORDER BY safra, segmento
    LIMIT 200

## inadimplência por safra
Inadimplência = COUNT(*) FILTER (WHERE inadimplente = TRUE) / COUNT(*) * 100
Ou usar AVG(inadimplente::int) * 100 para taxa percentual.

Exemplo:
    SELECT safra,
           COUNT(*) as total,
           SUM(CASE WHEN inadimplente THEN 1 ELSE 0 END) as inadimplentes,
           ROUND(AVG(CASE WHEN inadimplente THEN 1.0 ELSE 0.0 END) * 100, 2) as taxa_inadimplencia
    FROM fact_pricing_snapshot
    GROUP BY safra
    ORDER BY safra DESC
    LIMIT 24

## produto com pior ROAE
Para encontrar produto com pior ROAE, fazer JOIN com dim_produto para nome legível.

Exemplo:
    SELECT dp.produto, dp.familia, AVG(fp.roae) as roae_medio, COUNT(*) as contratos
    FROM fact_pricing_snapshot fp
    JOIN dim_produto dp ON fp.produto = dp.produto_id
    WHERE fp.safra = (SELECT MAX(safra) FROM fact_pricing_snapshot)
    GROUP BY dp.produto, dp.familia
    ORDER BY roae_medio ASC
    LIMIT 10

## diagnóstico executivo
Para gerar diagnóstico executivo, consolidar: margem média, ROAE médio,
taxa de inadimplência e volume de contratos por segmento ou safra.

Exemplo:
    SELECT safra,
           segmento,
           COUNT(*) as contratos,
           AVG(margem_liquida) as margem_media,
           AVG(roae) as roae_medio,
           ROUND(AVG(CASE WHEN inadimplente THEN 1.0 ELSE 0.0 END) * 100, 2) as taxa_inad
    FROM fact_pricing_snapshot
    WHERE safra >= '2025-10'
    GROUP BY safra, segmento
    ORDER BY safra DESC, segmento
    LIMIT 100
