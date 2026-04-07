from datetime import date
from pydantic import BaseModel


class FIISchema(BaseModel):
    ticker: str
    name: str
    sector: str
    subsector: str
    manager: str
    administrator: str
    is_ifix: bool

    class Config:
        from_attributes = True


class ScoringSchema(BaseModel):
    ticker: str
    reference_date: date
    pvp_score: float
    fundamental_score: float
    income_quality_score: float
    risk_liquidity_score: float
    relative_score: float
    total_score: float
    classification: str

    class Config:
        from_attributes = True
