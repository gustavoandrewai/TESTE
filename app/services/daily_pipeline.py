from datetime import date, datetime, timezone

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.ingestion.providers import BaseFIIProvider, MockFIIProvider, YahooFIIProvider
from app.models.entities import BenchmarksDaily, FIIMaster, FundamentalsMonthly, JobRun, MarketDaily, ScoringDaily
from app.scoring.model import (
    classify_opportunity,
    compute_fundamental_score,
    compute_income_quality_score,
    compute_pvp_score,
    compute_relative_performance_score,
    compute_risk_liquidity_score,
    compute_total_score,
)


class DailyPipelineService:
    def __init__(self, db: Session, provider: BaseFIIProvider | None = None):
        self.db = db
        self.provider = provider or self._build_default_provider()

    def _build_default_provider(self) -> BaseFIIProvider:
        if settings.data_provider.lower() == "yahoo":
            return YahooFIIProvider()
        return MockFIIProvider()

    def run(self, ref_date: date | None = None) -> JobRun:
        ref_date = ref_date or date.today()
        job = JobRun(job_name="daily_pipeline", status="running", started_at=datetime.now(timezone.utc), details="start")
        self.db.add(job)
        self.db.commit()

        bundle = self.provider.fetch_daily_bundle(ref_date)
        self._upsert_master(bundle.fiis)
        self._replace_daily(MarketDaily, bundle.market, ref_date)
        self._replace_daily(FundamentalsMonthly, bundle.fundamentals, ref_date)
        self._replace_daily(BenchmarksDaily, bundle.benchmarks, ref_date)
        self._recompute_scoring(ref_date)

        job.status = "success"
        job.finished_at = datetime.now(timezone.utc)
        job.details = "pipeline executed"
        self.db.commit()
        return job

    def _upsert_master(self, records: list[dict]) -> None:
        for record in records:
            entity = self.db.get(FIIMaster, record["ticker"])
            if entity:
                for key, value in record.items():
                    setattr(entity, key, value)
            else:
                self.db.add(FIIMaster(**record))
        self.db.commit()

    def _replace_daily(self, model, records: list[dict], ref_date: date) -> None:
        self.db.execute(delete(model).where(model.reference_date == ref_date))
        for record in records:
            self.db.add(model(**record))
        self.db.commit()

    def _recompute_scoring(self, ref_date: date) -> None:
        self.db.execute(delete(ScoringDaily).where(ScoringDaily.reference_date == ref_date))
        market_rows = (
            self.db.execute(
                select(MarketDaily, FundamentalsMonthly, FIIMaster)
                .join(
                    FundamentalsMonthly,
                    (MarketDaily.ticker == FundamentalsMonthly.ticker)
                    & (MarketDaily.reference_date == FundamentalsMonthly.reference_date),
                )
                .join(FIIMaster, FIIMaster.ticker == MarketDaily.ticker)
                .where(MarketDaily.reference_date == ref_date)
            )
            .all()
        )
        benchmark = self.db.scalar(select(BenchmarksDaily).where(BenchmarksDaily.reference_date == ref_date))
        if not benchmark:
            return

        market_df = pd.DataFrame([{**market.__dict__, "sector": fii.sector} for market, _, fii in market_rows])

        all_history_rows = self.db.execute(select(MarketDaily.ticker, MarketDaily.pvp)).all()
        history_df = pd.DataFrame(all_history_rows, columns=["ticker", "pvp"]) if all_history_rows else pd.DataFrame(columns=["ticker", "pvp"])

        for market, fund, fii in market_rows:
            sector_series = market_df.loc[market_df["sector"] == fii.sector, "pvp"]
            hist_series = history_df.loc[history_df["ticker"] == market.ticker, "pvp"]
            deterioration = min(1.0, fund.delinquency + fund.financial_vacancy + fund.leverage)
            pvp_score = compute_pvp_score(market.pvp, sector_series, hist_series, deterioration)
            fundamental_score = compute_fundamental_score(pd.Series(fund.__dict__))
            income_score = compute_income_quality_score(pd.Series(fund.__dict__))
            risk_score = compute_risk_liquidity_score(pd.Series(market.__dict__))
            rel_score = compute_relative_performance_score(pd.Series(market.__dict__), benchmark.ifix_return_12m)
            total = compute_total_score(pvp_score, fundamental_score, income_score, risk_score, rel_score)
            classification = classify_opportunity(total, pvp_score, fundamental_score, deterioration)
            self.db.add(
                ScoringDaily(
                    ticker=market.ticker,
                    reference_date=ref_date,
                    pvp_score=pvp_score,
                    fundamental_score=fundamental_score,
                    income_quality_score=income_score,
                    risk_liquidity_score=risk_score,
                    relative_score=rel_score,
                    total_score=total,
                    classification=classification,
                )
            )
        self.db.commit()
