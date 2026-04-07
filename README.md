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

## Decisões de arquitetura (resumo)
1. Separação em camadas (`ingestion`, `services`, `repositories`, `api`) para facilitar evolução.
2. P/VP domina o score com bloco matemático explícito e auditável.
3. Provider abstrato para permitir integração gradual com fontes oficiais sem quebrar API.
4. Pipeline diário transacional com registro em `job_runs`.
