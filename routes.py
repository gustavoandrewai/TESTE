"""API simples para job diário e leitura paginada de ranking.csv."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Query


app = FastAPI(title="FII Simple API", version="1.1.0")
RANKING_FILE = Path("ranking.csv")
JOB_STATUS_FILE = Path("job_status.json")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/jobs/run-daily")
def run_daily_job(tickers: str = Query("", description="Tickers separados por vírgula")) -> dict:
    """Executa pipeline via subprocess e sobrescreve ranking.csv no diretório raiz."""
    cmd = [sys.executable, "daily_pipeline.py"]
    if tickers.strip():
        cmd.extend(["--tickers", tickers])

    completed = subprocess.run(cmd, capture_output=True, text=True)

    if completed.returncode != 0:
        return {
            "status": "error",
            "message": completed.stderr.strip() or "Falha ao executar o pipeline",
            "tickers": tickers,
        }

    payload = {
        "status": "success",
        "message": "Pipeline executado e ranking.csv atualizado.",
        "tickers": tickers,
    }

    if JOB_STATUS_FILE.exists():
        try:
            payload["job_status"] = json.loads(JOB_STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            payload["job_status"] = {"status": "unknown"}

    return payload


@app.get("/jobs/status")
def jobs_status() -> dict:
    if not JOB_STATUS_FILE.exists():
        return {"status": "idle", "tickers": [], "last_run_utc": None, "processed_count": 0}
    return json.loads(JOB_STATUS_FILE.read_text(encoding="utf-8"))


@app.get("/rankings/daily")
def rankings_daily(
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=1000),
) -> dict:
    """Retorna ranking paginado lendo `ranking.csv`."""
    if not RANKING_FILE.exists():
        return {"items": [], "page": page, "page_size": page_size, "total": 0}

    df = pd.read_csv(RANKING_FILE)
    items = df.to_dict(orient="records")
    total = len(items)

    start = (page - 1) * page_size
    end = start + page_size
    paged_items = items[start:end] if start < total else []

    return {"items": paged_items, "page": page, "page_size": page_size, "total": total}
