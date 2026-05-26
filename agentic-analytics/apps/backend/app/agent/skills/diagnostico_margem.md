# Skill: Diagnóstico de Margem

## Objetivo
Analisar a margem líquida de um segmento de crédito, identificando tendências, anomalias e ofensores.

## Ferramentas (PTC - Programmatic Tool Calling)
Para executar esta skill, utilize o `sandbox_node` executando as seguintes etapas via código Python:

1. Extrair os dados da margem líquida agregada dos últimos 12 meses por segmento usando SQL na tabela `fact_pricing_snapshot`.
2. Executar código em Python (via Sandbox) que:
   - Usa `pandas` para calcular a média móvel de 3 meses.
   - Identifica os 3 segmentos com maior queda percentual de margem em relação ao último trimestre.
3. Gerar um relatório final em formato Markdown destacando os insights.

## Regras
- Sempre valide que a coluna analisada é `margem_liquida`.
- Nunca apresente dados individuais (nível de cliente).
- Destaque em negrito os segmentos com rentabilidade menor que 1.5%.
