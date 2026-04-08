from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd


WEIGHTS = {
    "pvp": 0.45,
    "fundamentals": 0.20,
    "income_quality": 0.15,
    "risk_liquidity": 0.10,
    "relative": 0.10,
}


@dataclass
class ScoreResult:
    pvp_score: float
    fundamental_score: float
    income_quality_score: float
    risk_liquidity_score: float
    relative_score: float
    total_score: float
    classification: str


def _clip01(v: float) -> float:
    return float(np.clip(v, 0.0, 1.0))


def normalize_0_100(value: float, low: float, high: float) -> float:
    if high == low:
        return 50.0
    norm = (value - low) / (high - low)
    return _clip01(norm) * 100


def compute_pvp_score(current_pvp: float, sector_values: pd.Series, historical_values: pd.Series, fundamental_deterioration: float) -> float:
    """Bloco dominante de valuation por P/VP.

    Fórmula combina desconto vs mediana setorial, posição em percentis e z-score histórico.
    Usa winsorização para reduzir impacto de outliers.
    """
    sector_raw = sector_values.dropna()
    hist_raw = historical_values.dropna()

    if sector_raw.empty:
        sector_raw = pd.Series([current_pvp])
    if hist_raw.empty:
        hist_raw = pd.Series([current_pvp])

    sector_clean = sector_raw.clip(lower=sector_raw.quantile(0.05), upper=sector_raw.quantile(0.95))
    hist_clean = hist_raw.clip(lower=hist_raw.quantile(0.05), upper=hist_raw.quantile(0.95))

    sector_median = float(sector_clean.median())
    p25 = float(sector_clean.quantile(0.25))
    p75 = float(sector_clean.quantile(0.75))
    pct_dev_vs_median = (sector_median - current_pvp) / max(sector_median, 1e-6)

    hist_mean = float(hist_clean.mean())
    hist_std = float(hist_clean.std(ddof=0) or 0.01)
    z_score = (current_pvp - hist_mean) / hist_std

    component_discount = normalize_0_100(pct_dev_vs_median, -0.25, 0.35)
    component_percentile = normalize_0_100(p75 - current_pvp, -0.2, max(p75 - p25, 0.05))
    component_history = normalize_0_100(-z_score, -2.0, 2.0)

    base_score = 0.45 * component_discount + 0.30 * component_percentile + 0.25 * component_history
    penalty = normalize_0_100(fundamental_deterioration, 0, 1) * 0.35
    return float(np.clip(base_score * (1 - penalty / 100), 0, 100))


def compute_fundamental_score(row: pd.Series) -> float:
    score = (
        (1 - row["physical_vacancy"]) * 0.25
        + (1 - row["financial_vacancy"]) * 0.25
        + (1 - row["leverage"]) * 0.20
        + (1 - row["delinquency"]) * 0.20
        + (1 - row["asset_concentration"]) * 0.10
    )
    return float(np.clip(score * 100, 0, 100))


def compute_income_quality_score(row: pd.Series) -> float:
    return float(np.clip((row["income_stability"] * 0.7 + row["dy_12m"] * 2.0 * 0.3) * 100, 0, 100))


def compute_risk_liquidity_score(row: pd.Series) -> float:
    liquidity_score = normalize_0_100(np.log1p(row["avg_daily_liquidity"]), 10, 16)
    risk_score = normalize_0_100(-(row["volatility"] + abs(row["drawdown"])), -0.5, -0.05)
    return 0.6 * liquidity_score + 0.4 * risk_score


def compute_relative_performance_score(row: pd.Series, ifix_return_12m: float) -> float:
    excess = row["return_12m"] - ifix_return_12m
    return normalize_0_100(excess, -0.25, 0.25)


def compute_total_score(pvp_score: float, fundamental_score: float, income_quality_score: float, risk_liquidity_score: float, relative_score: float) -> float:
    total = (
        pvp_score * WEIGHTS["pvp"]
        + fundamental_score * WEIGHTS["fundamentals"]
        + income_quality_score * WEIGHTS["income_quality"]
        + risk_liquidity_score * WEIGHTS["risk_liquidity"]
        + relative_score * WEIGHTS["relative"]
    )
    return float(np.clip(total, 0, 100))


def classify_opportunity(total_score: float, pvp_score: float, fundamental_score: float, deterioration: float) -> str:
    if pvp_score >= 65 and deterioration >= 0.6 and fundamental_score < 45:
        return "value_trap"
    if pvp_score >= 65 and fundamental_score >= 55 and total_score >= 60:
        return "assimetria_positiva"
    return "neutro"
