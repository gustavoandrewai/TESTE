"""API simples CSV-backed para FIIs."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Query


app = FastAPI(title="FII Simple API", version="1.2.0")
RANKING_FILE = Path("ranking.csv")
JOB_STATUS_FILE = Path("job_status.json")
TOP_BY_SECTOR_FILE = Path("top_by_sector.csv")


@app.get("/")
def root() -> dict:
    return {"service": "fii-simple-api", "status": "online"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/jobs/run-daily")
def run_daily_job(tickers: str = Query("", description="Tickers separados por vírgula")) -> dict:
    cmd = [sys.executable, "daily_pipeline.py"]
    if tickers.strip():
        cmd.extend(["--tickers", tickers])

    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        return {"status": "error", "message": completed.stderr.strip() or "Falha ao executar pipeline"}

    response = {"status": "success", "message": "ranking.csv atualizado", "tickers": tickers}
    if JOB_STATUS_FILE.exists():
        response["job_status"] = json.loads(JOB_STATUS_FILE.read_text(encoding="utf-8"))
    return response


@app.get("/jobs/status")
def jobs_status() -> dict:
    if not JOB_STATUS_FILE.exists():
        return {"status": "idle", "tickers": [], "last_run_utc": None, "processed_count": 0}
    return json.loads(JOB_STATUS_FILE.read_text(encoding="utf-8"))


@app.get("/rankings/daily")
def rankings_daily(page: int = Query(1, ge=1), page_size: int = Query(200, ge=1, le=1000)) -> dict:
    if not RANKING_FILE.exists():
        return {"items": [], "page": page, "page_size": page_size, "total": 0}

    df = pd.read_csv(RANKING_FILE)
    items = df.to_dict(orient="records")
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {"items": items[start:end] if start < total else [], "page": page, "page_size": page_size, "total": total}


@app.get("/rankings/top-by-sector")
def top_by_sector(only_positive: bool = False, sector: str | None = None) -> dict:
    if TOP_BY_SECTOR_FILE.exists():
        df = pd.read_csv(TOP_BY_SECTOR_FILE)
    elif RANKING_FILE.exists():
        df = pd.read_csv(RANKING_FILE).sort_values(["setor", "score_total"], ascending=[True, False]).groupby("setor").head(5)
    else:
        return {"items": [], "total": 0}

    if sector:
        df = df[df["setor"] == sector]
    if only_positive and "classificacao" in df.columns:
        df = df[df["classificacao"] == "assimetria_positiva"]

    return {"items": df.to_dict(orient="records"), "total": int(len(df))}
