# Glossário de Pricing — Documentação para RAG

## Safra

**Definição:** Safra é o mês de concessão do crédito ou de geração do contrato, no formato `YYYY-MM` (ex: `2026-03`).

**Uso:** Permite análise temporal da carteira. A "última safra" é sempre o mês mais recente disponível na base.

**Exemplo:** Safra `2026-03` representa todos os contratos gerados em março de 2026.

**Regra de negócio:** Ao filtrar por "última safra", usar sempre:
```sql
WHERE safra = (SELECT MAX(safra) FROM fact_pricing_snapshot)
```

---

## Margem Líquida

**Definição:** Percentual de lucro gerado após dedução de todos os custos diretos.

**Fórmula:** `margem_liquida = (receita - custo) / receita × 100`

**Unidade:** Percentual (%)

**Referência de benchmark:** Margem acima de 10% é considerada saudável no segmento bancário PME.

**Segmentos típicos:**
- PME: 6% a 12%
- Varejo: 3% a 8%
- Corporativo: 5% a 10%
- Agro: 7% a 15%

---

## ROAE — Return on Average Equity

**Definição:** Retorno sobre o Patrimônio Líquido Médio. Mede a eficiência na geração de lucro a partir do capital próprio.

**Fórmula:** `ROAE = Lucro Líquido / Patrimônio Líquido Médio × 100`

**Unidade:** Percentual (%)

**Interpretação:**
- ROAE > 15%: performance excelente
- ROAE 10-15%: performance adequada
- ROAE 5-10%: performance abaixo do esperado
- ROAE < 5%: performance crítica

---

## Score de Risco

**Definição:** Score de 1 a 10 que representa o risco de inadimplência do cliente.

**Escala:**
- 1-3: Baixo risco
- 4-6: Médio risco
- 7-10: Alto risco

**Regra:** Clientes com `score_risco >= 7` são classificados como **alto risco**.

---

## Spread

**Definição:** Diferença entre a taxa cobrada ao cliente e o custo de captação do banco.

**Relação com margem:** Spread maior tende a gerar margem maior, mas pode elevar o risco de inadimplência.

---

## Inadimplência

**Definição:** Situação em que o cliente deixa de honrar obrigações financeiras no prazo acordado.

**Flag na base:** `inadimplente = TRUE` na tabela `fact_pricing_snapshot`.

**Taxa de inadimplência:** Percentual de contratos inadimplentes no período.
```sql
AVG(CASE WHEN inadimplente THEN 1.0 ELSE 0.0 END) * 100
```
