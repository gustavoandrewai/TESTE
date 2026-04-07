from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import BenchmarksDaily, JobRun, ScoringDaily
from app.repositories.fii_repository import FIIRepository
from app.schemas.common import PaginatedResponse
from app.schemas.fii import FIISchema, ScoringSchema
from app.services.daily_pipeline import DailyPipelineService

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/fiis", response_model=PaginatedResponse[FIISchema])
def list_fiis(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sector: str | None = None,
    only_ifix: bool | None = None,
    min_liquidity: float | None = None,
    db: Session = Depends(get_db),
):
    repo = FIIRepository(db)
    total, items = repo.list_fiis(sector, only_ifix, min_liquidity, page, page_size)
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/fiis/{ticker}", response_model=FIISchema)
def get_fii(ticker: str, db: Session = Depends(get_db)):
    repo = FIIRepository(db)
    fii = repo.get_fii(ticker)
    if not fii:
        raise HTTPException(status_code=404, detail="Ticker not found")
    return fii


@router.get("/rankings/daily", response_model=PaginatedResponse[ScoringSchema])
def rankings_daily(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sector: str | None = None,
    min_pvp: float | None = None,
    max_pvp: float | None = None,
    db: Session = Depends(get_db),
):
    repo = FIIRepository(db)
    total, rows = repo.daily_rankings(page, page_size, sector, min_pvp, max_pvp)
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=[r[0] for r in rows])


@router.get("/rankings/by-sector")
def rankings_by_sector(db: Session = Depends(get_db)):
    rows = db.execute(select(ScoringDaily).order_by(ScoringDaily.reference_date.desc())).scalars().all()
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row.classification, []).append({"ticker": row.ticker, "score": row.total_score})
    return grouped


@router.get("/rankings/value-traps", response_model=list[ScoringSchema])
def value_traps(db: Session = Depends(get_db)):
    return FIIRepository(db).value_traps()


@router.get("/benchmarks")
def benchmarks(db: Session = Depends(get_db), ref_date: date | None = None):
    q = select(BenchmarksDaily).order_by(desc(BenchmarksDaily.reference_date))
    if ref_date:
        q = q.where(BenchmarksDaily.reference_date == ref_date)
    return db.execute(q).scalars().all()


@router.post("/jobs/run-daily")
def run_daily_job(db: Session = Depends(get_db)):
    job = DailyPipelineService(db).run()
    return {"job_id": job.id, "status": job.status}


@router.get("/jobs/status")
def jobs_status(db: Session = Depends(get_db)):
    rows = db.execute(select(JobRun).order_by(JobRun.started_at.desc()).limit(20)).scalars().all()
    return rows
