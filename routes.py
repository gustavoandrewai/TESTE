"""API simples para job diário e leitura paginada de ranking.csv."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Query

from daily_pipeline import DailyPipeline


app = FastAPI(title="FII Simple API", version="1.0.0")
RANKING_FILE = Path("ranking.csv")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/jobs/run-daily")
def run_daily_job() -> dict:
    result = DailyPipeline().run()
    return {"status": "success", "rows": result.rows, "file": "ranking.csv"}


@app.get("/rankings/daily")
def rankings_daily(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=1000),
) -> dict:
    """Retorna ranking paginado lendo `ranking.csv`.

    Se o arquivo não existir, retorna items vazios com metadados coerentes.
    """
    if not RANKING_FILE.exists():
        return {"items": [], "page": page, "page_size": page_size, "total": 0}

    df = pd.read_csv(RANKING_FILE)
    items = df.to_dict(orient="records")
    total = len(items)

    start = (page - 1) * page_size
    end = start + page_size
    paged_items = items[start:end] if start < total else []

    return {
        "items": paged_items,
        "page": page,
        "page_size": page_size,
        "total": total,
    }
