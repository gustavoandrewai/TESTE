# Renda Fixa Pro (Streamlit)

Aplicativo web em Python/Streamlit para análise profissional de carteira com **NTN-B** e **Tesouro Prefixado**.

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Funcionalidades principais

- Carteira com múltiplas posições (incluir, editar e remover via tabela dinâmica)
- Marcação a mercado por posição e consolidado
- Ganho/perda em R$ por título e da carteira
- Cenários de juros: otimista, base e pessimista (com probabilidades)
- Retorno esperado ponderado por probabilidade
- DV01 por posição e consolidado
- Duration/convexidade por posição e médias ponderadas da carteira
- Gráficos de P&L versus taxa, sensibilidade e comparação entre tipos de título
- Benchmark CDI e excesso de retorno
- Salvamento local da simulação em JSON + recarga
- Botões de cenário rápido e reset

## Abas do sistema

1. **Simulação individual**
2. **Carteira**
3. **Cenários**
4. **Risco**
5. **Benchmark**

## Modelagem financeira (resumo)

### 1) Precificação por fluxo de caixa

Preço = soma dos fluxos descontados:

`P = Σ [ CF_t / (1 + y_per)^n ]`

- `CF_t`: cupom + principal (na data de vencimento)
- `y_per`: taxa por período (anual/frequência)
- `n`: número de períodos

### 2) NTN-B

- Fluxos corrigidos por IPCA esperado ao longo do tempo
- Taxa real convertida para nominal com Fisher:

`(1 + i_nominal) = (1 + i_real) * (1 + ipca)`

### 3) Duration e convexidade

- Duration modificada estimada a partir dos fluxos descontados
- Convexidade discreta para melhorar leitura de curvatura

### 4) DV01

- `DV01 = P(y + 1bp) - P(y)`
- Mostrado por posição e consolidado em R$

### 5) Cenários e retorno esperado

- Choques paralelos de taxa (bps) para cenários otimista/base/pessimista
- Retorno esperado da carteira:

`E[P&L] = p_otimista * P&L_otimista + p_base * P&L_base + p_pessimista * P&L_pessimista`
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
