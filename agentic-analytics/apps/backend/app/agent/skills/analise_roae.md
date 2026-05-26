# Skill: Análise de ROAE

## Objetivo
Avaliar o ROAE (Return on Average Equity) por segmento e produto para identificar oportunidades de otimização de capital.

## Ferramentas (PTC - Programmatic Tool Calling)
1. Recuperar o ROAE e a Margem Líquida agregada via SQL.
2. Utilizar o ambiente Sandbox para:
   - Calcular a variância do ROAE.
   - Gerar uma simulação de ganho se a margem de produtos com ROAE < 10% fosse incrementada em 1%.
3. Produzir um relatório Markdown consolidado.

## Regras
- Sempre limite o escopo da simulação à última safra disponível.
- Sinalize na seção "Riscos e Limitações" que a simulação é matemática e não reflete elasticidade de preço de mercado.
