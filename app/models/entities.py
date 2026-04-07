from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SectorTaxonomy(Base):
    __tablename__ = "sector_taxonomy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sector: Mapped[str] = mapped_column(String(80), unique=True)
    subsector: Mapped[str] = mapped_column(String(80), default="geral")
    description: Mapped[str] = mapped_column(String(255), default="")


class FIIMaster(Base):
    __tablename__ = "fii_master"

    ticker: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sector: Mapped[str] = mapped_column(String(80), nullable=False)
    subsector: Mapped[str] = mapped_column(String(80), nullable=False)
    manager: Mapped[str] = mapped_column(String(120), default="")
    administrator: Mapped[str] = mapped_column(String(120), default="")
    is_ifix: Mapped[bool] = mapped_column(Boolean, default=False)


class MarketDaily(Base):
    __tablename__ = "market_daily"
    __table_args__ = (UniqueConstraint("ticker", "reference_date", name="uq_market_ticker_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(ForeignKey("fii_master.ticker"), index=True)
    reference_date: Mapped[date] = mapped_column(Date, index=True)
    price: Mapped[float] = mapped_column(Float)
    vp_per_share: Mapped[float] = mapped_column(Float)
    pvp: Mapped[float] = mapped_column(Float)
    avg_daily_liquidity: Mapped[float] = mapped_column(Float)
    return_1m: Mapped[float] = mapped_column(Float)
    return_6m: Mapped[float] = mapped_column(Float)
    return_12m: Mapped[float] = mapped_column(Float)
    volatility: Mapped[float] = mapped_column(Float)
    drawdown: Mapped[float] = mapped_column(Float)


class FundamentalsMonthly(Base):
    __tablename__ = "fundamentals_monthly"
    __table_args__ = (UniqueConstraint("ticker", "reference_date", name="uq_fund_ticker_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(ForeignKey("fii_master.ticker"), index=True)
    reference_date: Mapped[date] = mapped_column(Date, index=True)
    equity: Mapped[float] = mapped_column(Float)
    dy_monthly: Mapped[float] = mapped_column(Float)
    dy_12m: Mapped[float] = mapped_column(Float)
    physical_vacancy: Mapped[float] = mapped_column(Float)
    financial_vacancy: Mapped[float] = mapped_column(Float)
    asset_concentration: Mapped[float] = mapped_column(Float)
    tenant_concentration: Mapped[float] = mapped_column(Float)
    avg_contract_term: Mapped[float] = mapped_column(Float)
    leverage: Mapped[float] = mapped_column(Float)
    delinquency: Mapped[float] = mapped_column(Float)
    income_per_share: Mapped[float] = mapped_column(Float)
    income_stability: Mapped[float] = mapped_column(Float)


class BenchmarksDaily(Base):
    __tablename__ = "benchmarks_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference_date: Mapped[date] = mapped_column(Date, index=True)
    ifix_return_1m: Mapped[float] = mapped_column(Float)
    ifix_return_12m: Mapped[float] = mapped_column(Float)
    cdi_annual: Mapped[float] = mapped_column(Float)


class ScoringDaily(Base):
    __tablename__ = "scoring_daily"
    __table_args__ = (UniqueConstraint("ticker", "reference_date", name="uq_scoring_ticker_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(ForeignKey("fii_master.ticker"), index=True)
    reference_date: Mapped[date] = mapped_column(Date, index=True)
    pvp_score: Mapped[float] = mapped_column(Float)
    fundamental_score: Mapped[float] = mapped_column(Float)
    income_quality_score: Mapped[float] = mapped_column(Float)
    risk_liquidity_score: Mapped[float] = mapped_column(Float)
    relative_score: Mapped[float] = mapped_column(Float)
    total_score: Mapped[float] = mapped_column(Float)
    classification: Mapped[str] = mapped_column(String(32))


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(12), index=True)
    reference_date: Mapped[date] = mapped_column(Date, index=True)
    alert_type: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(String(255))


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_name: Mapped[str] = mapped_column(String(80), index=True)
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    details: Mapped[str] = mapped_column(String(255), default="")
