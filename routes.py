"""API simples CSV-backed para FIIs com suporte a listas grandes de tickers."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Query
from pydantic import BaseModel


app = FastAPI(title="FII Simple API", version="1.3.0")
RANKING_FILE = Path("ranking.csv")
JOB_STATUS_FILE = Path("job_status.json")
TOP_BY_SECTOR_FILE = Path("top_by_sector.csv")


class RunDailyBody(BaseModel):
    tickers: list[str] = []


@app.get("/")
def root() -> dict:
    return {"service": "fii-simple-api", "status": "online"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/jobs/run-daily")
def run_daily_job(body: RunDailyBody | None = None, tickers: str = Query("", description="Fallback query string")) -> dict:
    # Prioridade para BODY JSON (listas grandes). Query string permanece como fallback.
    tickers_list: list[str] = []
    if body and body.tickers:
        tickers_list = body.tickers
    elif tickers.strip():
        tickers_list = [t.strip() for t in tickers.split(",") if t.strip()]

    cmd = [sys.executable, "daily_pipeline.py", "--tickers-json", json.dumps(tickers_list, ensure_ascii=False)]
    completed = subprocess.run(cmd, capture_output=True, text=True)

    if completed.returncode != 0:
        return {
            "status": "error",
            "message": completed.stderr.strip() or "Falha ao executar pipeline",
            "tickers_enviados": tickers_list,
        }

    response = {
        "status": "success",
        "message": "ranking.csv atualizado",
        "tickers_enviados": tickers_list,
    }
    if JOB_STATUS_FILE.exists():
        response["job_status"] = json.loads(JOB_STATUS_FILE.read_text(encoding="utf-8"))
    return response


@app.get("/jobs/status")
def jobs_status() -> dict:
    if not JOB_STATUS_FILE.exists():
        return {
            "status": "idle",
            "tickers_received_count": 0,
            "tickers_valid_count": 0,
            "processed_count": 0,
            "failed_count": 0,
            "tickers_received": [],
            "tickers_valid": [],
            "tickers_processed": [],
            "tickers_failed": {},
            "last_run_utc": None,
        }
    return json.loads(JOB_STATUS_FILE.read_text(encoding="utf-8"))


@app.get("/rankings/daily")
def rankings_daily(page: int = Query(1, ge=1), page_size: int = Query(200, ge=1, le=5000)) -> dict:
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
    if RANKING_FILE.exists():
        df = pd.read_csv(RANKING_FILE)
    elif TOP_BY_SECTOR_FILE.exists():
        df = pd.read_csv(TOP_BY_SECTOR_FILE)
    else:
        return {"items": [], "total": 0}

    if "setor" not in df.columns:
        df["setor"] = "outros"
    df["setor"] = df["setor"].fillna("outros").astype(str).str.strip().str.lower().replace({"": "outros", "fof": "fof", "FoF": "fof"})

    if only_positive and "classificacao" in df.columns:
        df = df[df["classificacao"] == "assimetria_positiva"]

    if sector:
        df = df[df["setor"] == sector.lower()]

    top = df.sort_values(["setor", "score_total"], ascending=[True, False]).groupby("setor", as_index=False).head(5)
    return {"items": top.to_dict(orient="records"), "total": int(len(top))}
