# SCENARIOS — Camada Semântica do Text2SQL Agent

Este arquivo define as regras de negócio do domínio de pricing/risco/ROAE
que o agente Text2SQL deve consultar antes de gerar SQL.
É a "inteligência de negócio" que o schema não consegue expressar.

---

## Conceitos Fundamentais

### O que é "safra"?
Safra é o mês de originação do contrato, no formato `YYYY-MM` (ex: `2026-01`).
Na tabela `fact_pricing_snapshot`, a coluna se chama `safra`.
"Última safra" equivale a `MAX(safra)` da tabela.

```sql
-- Última safra disponível:
SELECT MAX(safra) as ultima_safra FROM fact_pricing_snapshot
```

### O que é "alto risco"?
Clientes com `score_risco >= 7` (escala de 0 a 10) são classificados como alto risco.
O segmento de alto risco frequentemente apresenta menor ROAE e maior inadimplência.

```sql
-- Clientes de alto risco na última safra:
SELECT safra, segmento, COUNT(*) as clientes_alto_risco, AVG(roae) as roae_medio
FROM fact_pricing_snapshot
WHERE score_risco >= 7
  AND safra = (SELECT MAX(safra) FROM fact_pricing_snapshot)
GROUP BY safra, segmento
ORDER BY clientes_alto_risco DESC
LIMIT 50
```

### O que é "margem líquida"?
Margem líquida é o percentual de retorno após dedução de custo de funding, risco e despesas.
Coluna: `margem_liquida` (decimal, ex: 0.045 = 4.5%).
Sinal negativo indica operação com prejuízo.

```sql
-- Margem média por safra e segmento:
SELECT safra, segmento, AVG(margem_liquida) as margem_media, COUNT(*) as contratos
FROM fact_pricing_snapshot
GROUP BY safra, segmento
ORDER BY safra DESC, margem_media DESC
LIMIT 100
```

### O que é "ROAE"?
ROAE (Return on Average Equity) mede a rentabilidade sobre o patrimônio médio alocado.
Coluna: `roae` (decimal, ex: 0.12 = 12%).
ROAE abaixo de 10% indica operação pouco rentável para o banco.

```sql
-- ROAE por segmento na última safra:
SELECT segmento, AVG(roae) as roae_medio, COUNT(*) as contratos,
       MIN(roae) as pior_roae, MAX(roae) as melhor_roae
FROM fact_pricing_snapshot
WHERE safra = (SELECT MAX(safra) FROM fact_pricing_snapshot)
GROUP BY segmento
ORDER BY roae_medio DESC
LIMIT 50
```

### O que é "inadimplência"?
Campo booleano `inadimplente` indica se o contrato está em atraso.
Taxa de inadimplência = proporção de contratos `inadimplente = TRUE`.

```sql
-- Taxa de inadimplência por safra:
SELECT safra,
       COUNT(*) as total,
       SUM(CASE WHEN inadimplente THEN 1 ELSE 0 END) as inadimplentes,
       ROUND(AVG(CASE WHEN inadimplente THEN 1.0 ELSE 0.0 END) * 100, 2) as taxa_inad_pct
FROM fact_pricing_snapshot
GROUP BY safra
ORDER BY safra DESC
LIMIT 24
```

---

## Segmentos

| Código | Descrição |
|---|---|
| `Varejo` | Pessoa Física — contratos de crédito pessoal e consignado |
| `PME` | Pequenas e Médias Empresas — capital de giro e financiamento |
| `Corporate` | Grandes empresas — operações estruturadas |
| `Agro` | Agronegócio — crédito rural |

---

## Produtos

| Código | Descrição |
|---|---|
| `CDC` | Crédito Direto ao Consumidor |
| `Consignado` | Empréstimo com desconto em folha |
| `Capital_Giro` | Capital de giro para PME |
| `Financiamento_Rural` | Financiamento rural para Agro |
| `Trade_Finance` | Operações de comércio exterior para Corporate |

---

## Padrões de Query Seguros

### Diagnóstico geral da safra mais recente
```sql
SELECT safra, segmento, COUNT(*) as contratos,
       AVG(margem_liquida) as margem_media,
       AVG(roae) as roae_medio,
       ROUND(AVG(CASE WHEN inadimplente THEN 1.0 ELSE 0.0 END) * 100, 2) as taxa_inad_pct
FROM fact_pricing_snapshot
WHERE safra = (SELECT MAX(safra) FROM fact_pricing_snapshot)
GROUP BY safra, segmento
ORDER BY margem_media DESC
LIMIT 50
```

### Evolução de margem ao longo do tempo
```sql
SELECT safra, AVG(margem_liquida) as margem_media, COUNT(*) as contratos
FROM fact_pricing_snapshot
GROUP BY safra
ORDER BY safra ASC
LIMIT 36
```

### Comparativo pior vs melhor segmento
```sql
SELECT segmento,
       AVG(margem_liquida) as margem_media,
       AVG(roae) as roae_medio,
       AVG(score_risco) as risco_medio,
       COUNT(*) as contratos
FROM fact_pricing_snapshot
WHERE safra >= (
    SELECT DATE_TRUNC('month', MAX(safra)::DATE - INTERVAL '3 months')::TEXT
    FROM fact_pricing_snapshot
)
GROUP BY segmento
ORDER BY margem_media ASC
LIMIT 20
```

---

## Regras de Governança para o Agente

1. **SEMPRE use LIMIT** em queries sobre `fact_pricing_snapshot`.
2. **NUNCA acesse** `cliente_id`, `cpf` ou `nome_cliente` diretamente — esses campos são mascarados automaticamente.
3. **PREFIRA agregações** (`AVG`, `COUNT`, `SUM`) a dados granulares por cliente.
4. **VERIFIQUE a safra** — use subquery `(SELECT MAX(safra) FROM fact_pricing_snapshot)` para "última safra".
5. **CONECTE regra com dado** — se o usuário citar "alto risco", use `score_risco >= 7`.
