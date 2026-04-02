# Dashboard de Aportes Mensais

Aplicação web em **React + Vite + TypeScript** para importar uma planilha de aportes (`.xlsx`) e gerar:

- KPIs financeiros
- gráficos de evolução
- insights automáticos
- alertas de inconsistência/importação

Interface em **português-BR**, responsiva e pronta para rodar localmente.

---

## Funcionalidades implementadas

### Importação e processamento da planilha

- Leitura de planilha `.xlsx` com biblioteca `xlsx`.
- Tentativa de carregamento automático de `public/planilha de aportes.xlsx`.
- Upload manual de outra planilha via interface.
- Fallback automático para dados de exemplo quando o arquivo padrão não existir.

### Mapeamento de colunas (automático + manual)

A aplicação tenta inferir colunas por similaridade de nomes e permite ajuste manual.

Campos suportados:

- data
- mês/ano
- valor do aporte
- categoria
- ativo/investimento
- saldo/patrimônio
- rendimento

### KPIs no dashboard

- total aportado no mês atual
- total aportado no ano atual
- média mensal de aportes
- maior aporte
- menor aporte
- crescimento mês a mês
- evolução acumulada
- patrimônio total (quando existir)

### Gráficos

- aportes por mês
- evolução acumulada
- divisão por categoria
- comparação entre meses
- tendência de crescimento

### Insights automáticos

- mês com maior aporte
- mês com menor aporte
- variação percentual do último mês vs mês anterior
- alerta de queda acentuada
- concentração por categoria
- consistência/inconsistência de aportes

### Tratamento de erros

- linhas inválidas (sem data/mês válido ou sem valor de aporte) são ignoradas
- alertas exibidos no painel de importação

---

## Inferências adotadas para colunas ambíguas

Quando os nomes de colunas são ambíguos, o sistema aplica inferência textual (normalizada, sem acentos), por exemplo:

- **Data**: `data`, `dt`
- **Mês/Ano**: `mês`, `mes`, `competencia`, `periodo`, `ano`
- **Valor do aporte**: `aporte`, `valor`, `aplicacao`
- **Categoria**: `categoria`
- **Ativo/Investimento**: `ativo`, `invest`, `produto`
- **Patrimônio**: `patrimonio`, `saldo`, `carteira`
- **Rendimento**: `rendimento`, `rentabilidade`, `lucro`

Se a inferência errar, ajuste no bloco **Mapeamento de colunas** na UI.

---

## Estrutura do projeto

```bash
.
├── public/
├── src/
│   ├── components/
│   ├── services/
│   ├── utils/
│   ├── App.tsx
│   ├── main.tsx
│   └── styles.css
├── package.json
└── README.md
```

---

## Como rodar localmente

### 1) Instalar dependências

```bash
npm install
```

### 2) Rodar em desenvolvimento

```bash
npm run dev
```

### 3) Build de produção

```bash
npm run build
npm run preview
```

---

## Como trocar a planilha depois

### Opção A (recomendada para uso recorrente)

1. Coloque o arquivo no caminho:

```bash
public/planilha de aportes.xlsx
```

2. Reinicie o `npm run dev` (se necessário).

### Opção B (rápida pela interface)

- Use o campo **Trocar planilha (.xlsx)** no topo da tela.
- O arquivo será processado no navegador para a sessão atual.

---

## Observações

- Se o arquivo `planilha de aportes.xlsx` não estiver no `public/`, o app inicia com dados de exemplo para não travar o fluxo.
- Valores monetários são formatados para `pt-BR`.
- Datas aceitas: Excel date serial, `yyyy-MM-dd`, `dd/MM/yyyy` e `MM/yyyy`.
