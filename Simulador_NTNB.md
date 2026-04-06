# Simulador Web de NTN-B e Tesouro Prefixado (Streamlit)

Aplicativo interativo em Python para simular preço e sensibilidade de **NTN-B (Tesouro IPCA+)** e **Tesouro Prefixado**.

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Inputs no topo do dashboard

- Valor nominal
- Anos até vencimento
- IPCA esperado (% a.a.)
- Taxa real atual (% a.a.)
- Taxa real de cenário (% a.a.)

## Métricas calculadas

Para ambos os títulos:

- Preço atual
- Preço no cenário
- Variação percentual
- Duration aproximada

## Visualizações

- Gráfico de **Preço vs Taxa de Juros** (NTN-B e Prefixado)
- Tabela de sensibilidade com múltiplos cenários
- Gráfico de sensibilidade (% de variação)

## Cenários múltiplos (extra)

No campo de cenários, informe taxas reais separadas por vírgula (exemplo: `7, 6, 5, 4`).

## Fórmulas utilizadas (modelo simplificado)

- Conversão real -> nominal: `taxa_nominal = (1 + taxa_real) * (1 + ipca) - 1`
- Preço NTN-B (zero cupom simplificado):
  `preco = (valor_nominal * (1 + ipca)^anos) / (1 + taxa_real)^anos`
- Preço Prefixado (zero cupom):
  `preco = valor_nominal / (1 + taxa_nominal)^anos`
- Duration aproximada (modificada):
  `duration = anos / (1 + yield)`
