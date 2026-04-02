# Simulador NTN-B (CSV)

Foi criada a planilha `Simulador_NTNB.csv` (separada por `;`) para simular a variação de preço de NTN-B com diferentes taxas reais de juros.

## Campos editáveis
- `B4`: Valor nominal (R$)
- `B5`: Anos até o vencimento
- `B6`: IPCA anual esperado (%)
- `B7`: Taxa de cupom real anual (%)
- `B8`: Frequência de cupom (pagamentos por ano)
- `B9`: Taxa real base para comparação (%)

## Tabela de simulação
- As taxas reais de mercado ficam em `A11:A25`.
- O preço teórico hoje é calculado em `B11:B25`.
- O valor projetado no vencimento é calculado em `C11:C25`.
- A variação percentual contra a taxa base é calculada em `D11:D25`.

## Fórmulas usadas
- Preço teórico (coluna B):
  `=($B$4*$B$7/100/$B$8)*(1-(1+taxa/$B$8)^(-$B$5*$B$8))/(taxa/$B$8)+$B$4*(1+taxa/$B$8)^(-$B$5*$B$8)`
  onde `taxa = A(linha)/100`.
- Valor projetado no vencimento (coluna C):
  `=B(linha)*(1+$B$6/100)^$B$5`
- Variação vs base (coluna D):
  `=B(linha)/$B$28-1`
- Preço na taxa base (`B28`):
  mesma fórmula de preço teórico usando `B9` como taxa.
