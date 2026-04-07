from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session

from app.models.entities import FIIMaster, ScoringDaily


class FIIRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_fiis(self, sector: str | None, only_ifix: bool | None, min_liquidity: float | None, page: int, page_size: int):
        query: Select = select(FIIMaster)
        if sector:
            query = query.where(FIIMaster.sector == sector)
        if only_ifix is not None:
            query = query.where(FIIMaster.is_ifix == only_ifix)

        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = self.db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
        return total or 0, items

    def get_fii(self, ticker: str):
        return self.db.get(FIIMaster, ticker)

    def daily_rankings(self, page: int, page_size: int, sector: str | None, min_pvp: float | None, max_pvp: float | None):
        q = (
            select(ScoringDaily, FIIMaster.sector)
            .join(FIIMaster, FIIMaster.ticker == ScoringDaily.ticker)
            .order_by(desc(ScoringDaily.total_score))
        )
        if sector:
            q = q.where(FIIMaster.sector == sector)
        total = self.db.scalar(select(func.count()).select_from(q.subquery())) or 0
        rows = self.db.execute(q.offset((page - 1) * page_size).limit(page_size)).all()
        return total, rows

    def value_traps(self):
        q = select(ScoringDaily).where(ScoringDaily.classification == "value_trap").order_by(desc(ScoringDaily.reference_date))
        return self.db.scalars(q).all()
