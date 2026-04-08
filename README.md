# FII Asymmetry Analyzer

Projeto didático em Python para analisar FIIs diariamente, com **P/VP como benchmark dominante** para geração de ranking de oportunidades.

## Arquitetura
- **FastAPI** para endpoints.
- **PostgreSQL + SQLAlchemy** para persistência.
- **Alembic** para migrations.
- **Pandas** para cálculos quantitativos.
- **APScheduler** para rotina automática opcional.
- **Providers desacoplados** (`app/ingestion/providers.py`) com `MockFIIProvider` pronto para troca por fonte real.
- **Yahoo Finance opcional** com `YahooFIIProvider` para ingestão de preços quando `DATA_PROVIDER=yahoo`.

## Estrutura
```text
app/
  api/
  core/
  ingestion/
  jobs/
  models/
  repositories/
  schemas/
  scoring/
  services/
alembic/
tests/
```

## Modelo de score (0-100)
Pesos em `app/scoring/model.py`:
- 45% valuation por P/VP
- 20% fundamentos
- 15% estabilidade/renda
- 10% risco e liquidez
- 10% relativo vs benchmark

### Bloco P/VP
Implementa:
- mediana e percentis setoriais;
- desvio percentual vs mediana;
- z-score histórico;
- winsorização (5%-95%);
- normalização 0-100;
- penalização por deterioração fundamentalista.

## Como rodar local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

## Com Docker
```bash
docker compose up --build
```

## Migrations
```bash
alembic upgrade head
```

## Rodar job diário manualmente
```bash
curl -X POST http://localhost:8000/jobs/run-daily
```

## Usando dados do Yahoo Finance no pipeline
1. Defina `DATA_PROVIDER=yahoo` no `.env`.
2. Execute o job diário (`POST /jobs/run-daily`).
3. O pipeline buscará cotações via `yfinance` e recalculará o ranking.

## Endpoints principais
- `GET /health`
- `GET /fiis`
- `GET /fiis/{ticker}`
- `GET /rankings/daily`
- `GET /rankings/by-sector`
- `GET /rankings/value-traps`
- `GET /benchmarks`
- `POST /jobs/run-daily`
- `GET /jobs/status`

### Exemplos
```bash
curl 'http://localhost:8000/fiis?page=1&page_size=10&sector=logistica&only_ifix=true'
curl 'http://localhost:8000/rankings/daily?page=1&page_size=20'
curl 'http://localhost:8000/rankings/value-traps'
```

Resposta exemplo (`/rankings/daily`):
```json
{
  "total": 3,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "ticker": "HGLG11",
      "reference_date": "2026-04-07",
      "pvp_score": 74.2,
      "fundamental_score": 83.5,
      "income_quality_score": 72.0,
      "risk_liquidity_score": 68.9,
      "relative_score": 54.0,
      "total_score": 73.3,
      "classification": "assimetria_positiva"
    }
  ]
}
```

## Configuração
- **Pesos**: `WEIGHTS` em `app/scoring/model.py`.
- **Taxonomia setorial**: `sector_taxonomy` + provider (`app/ingestion/providers.py`).
- **Classificação** (`assimetria_positiva`, `neutro`, `value_trap`): `classify_opportunity`.
- **Fonte de dados**: `DATA_PROVIDER` (`mock` ou `yahoo`) em `.env`.

## Dashboard com atualização manual do Yahoo
O `streamlit_app.py` possui a aba **FIIs Yahoo**, com botão **“🔄 Atualizar dados do Yahoo Finance”** para forçar refresh dos preços conforme o tempo passa.
Além do refresh, a aba traz uma visão mais profissional com:
- KPIs de destaque (top retorno, preço médio, volatilidade média e liquidez média);
- gráfico comparativo de retorno 1m vs 3m;
- tabela formatada para leitura executiva;
- exportação do snapshot para CSV.

## Decisões de arquitetura (resumo)
1. Separação em camadas (`ingestion`, `services`, `repositories`, `api`) para facilitar evolução.
2. P/VP domina o score com bloco matemático explícito e auditável.
3. Provider abstrato para permitir integração gradual com fontes oficiais sem quebrar API.
4. Pipeline diário transacional com registro em `job_runs`.

## Dashboard profissional (Yahoo + API)
Execute:
```bash
streamlit run fii_dashboard.py
```

Recursos:
- botão **🔄 Atualizar Yahoo** para refresh manual imediato dos preços;
- botão **▶️ Rodar job diário** para acionar a API e recalcular o ranking;
- cards explícitos com a distribuição obrigatória dos pesos (**45/20/15/10/10**);
- decomposição visual do score por componente (contribuições ponderadas);
- painel setorial com score médio e líder por setor;
- KPIs e explicação didática para leitura executiva.

## Execução rápida (modo simples solicitado)
```bash
python -m uvicorn routes:app --reload
python -m streamlit run fii_dashboard.py
```

Nesse modo, `POST /jobs/run-daily` gera `ranking.csv` na raiz e `GET /rankings/daily` retorna JSON paginado baseado nesse arquivo.


### Comportamento do job dinâmico por ticker
- O dashboard envia os tickers digitados para `POST /jobs/run-daily?tickers=...`.
- A API executa `daily_pipeline.py` via subprocess e sobrescreve `ranking.csv` em cada execução.
- O endpoint `GET /rankings/daily` sempre lê o arquivo mais recente.
- O status do último job fica em `job_status.json` (`status`, `tickers`, `last_run_utc`, `processed_count`).


## CSVs locais usados no modo simples
- `fundamentals_mock.csv`: taxonomia setorial + fundamentos por ticker (`setor`, `subsetor`, `pvp`, `dy_12m`, `vacancia`, `inadimplencia`, `alavancagem`, `liquidez_media`, `estabilidade_rendimentos`).
- `ranking.csv`: ranking diário completo com benchmarks de mercado + fundamentalistas + scores por bloco.
- `top_by_sector.csv`: Top 5 por setor gerado a cada job.
- `job_status.json`: status da última execução.

Rotas extras no modo simples:
- `GET /`
- `GET /rankings/top-by-sector`
