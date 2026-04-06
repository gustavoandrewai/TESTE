"""Engine financeiro para análise de carteira NTN-B / Prefixado."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np
import pandas as pd

TITLE_NTNB = "NTN-B"
TITLE_PREFIXADO = "Tesouro Prefixado"
VALID_TYPES = (TITLE_NTNB, TITLE_PREFIXADO)


@dataclass
class Position:
    name: str
    title_type: str
    invested_amount: float
    nominal_value: float
    buy_rate: float
    current_rate: float
    scenario_rate: float
    years_to_maturity: float
    expected_ipca: float
    coupon_rate: float = 0.0
    frequency: int = 2


@dataclass
class ScenarioConfig:
    optimistic_shift_bp: float = -100.0
    base_shift_bp: float = 0.0
    pessimistic_shift_bp: float = 100.0
    prob_optimistic: float = 0.3
    prob_base: float = 0.4
    prob_pessimistic: float = 0.3


def real_to_nominal_rate(real_rate: float, ipca: float) -> float:
    return (1 + real_rate) * (1 + ipca) - 1


def _annual_nominal_rate(pos: Position, annual_rate: float) -> float:
    return real_to_nominal_rate(annual_rate, pos.expected_ipca) if pos.title_type == TITLE_NTNB else annual_rate


def _cashflows(pos: Position) -> list[tuple[int, float, float]]:
    """Retorna lista de (n_período, t_anos, fluxo_nominal)."""
    periods = max(1, int(round(pos.years_to_maturity * pos.frequency)))
    out: list[tuple[int, float, float]] = []

    for n in range(1, periods + 1):
        t = n / pos.frequency
        principal_t = pos.nominal_value * (1 + pos.expected_ipca) ** t if pos.title_type == TITLE_NTNB else pos.nominal_value
        coupon = principal_t * (pos.coupon_rate / 100) / pos.frequency
        out.append((n, t, coupon + (principal_t if n == periods else 0.0)))

    return out


def price_from_yield(pos: Position, annual_rate: float) -> float:
    r_per = _annual_nominal_rate(pos, annual_rate) / pos.frequency
    return sum(cf / (1 + r_per) ** n for n, _, cf in _cashflows(pos))


def duration_convexity(pos: Position, annual_rate: float) -> tuple[float, float]:
    """Duration modificada + convexidade discreta anualizada."""
    r_per = _annual_nominal_rate(pos, annual_rate) / pos.frequency
    price = price_from_yield(pos, annual_rate)
    if price <= 0:
        return 0.0, 0.0

    macaulay_num = 0.0
    convex_num = 0.0
    for n, t, cf in _cashflows(pos):
        pv = cf / (1 + r_per) ** n
        macaulay_num += t * pv
        convex_num += (n * (n + 1) * pv) / (1 + r_per) ** 2

    macaulay = macaulay_num / price
    modified = macaulay / (1 + r_per)
    convexity = convex_num / (price * pos.frequency**2)
    return modified, convexity


def dv01(pos: Position, annual_rate: float) -> float:
    return price_from_yield(pos, annual_rate + 0.0001) - price_from_yield(pos, annual_rate)


def _apply_shift(rate: float, shift_bp: float) -> float:
    return max(0.0001, rate + shift_bp / 10_000)


def normalize_probabilities(cfg: ScenarioConfig) -> ScenarioConfig:
    probs = np.array([cfg.prob_optimistic, cfg.prob_base, cfg.prob_pessimistic], dtype=float)
    s = probs.sum()
    probs = np.array([1 / 3, 1 / 3, 1 / 3]) if s <= 0 else probs / s
    cfg.prob_optimistic, cfg.prob_base, cfg.prob_pessimistic = probs.tolist()
    return cfg


def analyze_position(pos: Position, cfg: ScenarioConfig) -> dict:
    price_buy = price_from_yield(pos, pos.buy_rate)
    price_current = price_from_yield(pos, pos.current_rate)
    price_custom = price_from_yield(pos, pos.scenario_rate)

    qty = pos.invested_amount / price_buy if price_buy > 0 else 0.0
    current_value = qty * price_current
    scenario_value = qty * price_custom

    shocks = {
        "otimista": cfg.optimistic_shift_bp,
        "base": cfg.base_shift_bp,
        "pessimista": cfg.pessimistic_shift_bp,
    }
    scen_values = {k: qty * price_from_yield(pos, _apply_shift(pos.current_rate, bp)) for k, bp in shocks.items()}
    scen_pnl = {k: v - current_value for k, v in scen_values.items()}

    mod_dur, conv = duration_convexity(pos, pos.current_rate)
    exp_pnl = (
        scen_pnl["otimista"] * cfg.prob_optimistic
        + scen_pnl["base"] * cfg.prob_base
        + scen_pnl["pessimista"] * cfg.prob_pessimistic
    )

    return {
        "nome": pos.name,
        "tipo": pos.title_type,
        "valor_investido": pos.invested_amount,
        "quantidade": qty,
        "preco_compra": price_buy,
        "preco_atual": price_current,
        "preco_cenario": price_custom,
        "valor_atual": current_value,
        "valor_cenario": scenario_value,
        "ganho_perda_cenario": scenario_value - current_value,
        "variacao_cenario_pct": (price_custom / price_current - 1) * 100 if price_current > 0 else 0.0,
        "duration_modificada": mod_dur,
        "convexidade": conv,
        "dv01_r$": dv01(pos, pos.current_rate) * qty,
        "pnl_otimista": scen_pnl["otimista"],
        "pnl_base": scen_pnl["base"],
        "pnl_pessimista": scen_pnl["pessimista"],
        "retorno_esperado_pnl": exp_pnl,
    }


def analyze_portfolio(positions: Iterable[Position], cfg: ScenarioConfig) -> tuple[pd.DataFrame, dict]:
    cfg = normalize_probabilities(cfg)
    df = pd.DataFrame([analyze_position(p, cfg) for p in positions])
    if df.empty:
        return df, {
            "valor_atual_total": 0.0,
            "valor_cenario_total": 0.0,
            "ganho_perda_total": 0.0,
            "dv01_total": 0.0,
            "duration_media": 0.0,
            "convexidade_media": 0.0,
            "retorno_esperado_total": 0.0,
            "pnl_otimista_total": 0.0,
            "pnl_base_total": 0.0,
            "pnl_pessimista_total": 0.0,
        }

    total = float(df["valor_atual"].sum())
    w = (df["valor_atual"] / total) if total > 0 else 0

    summary = {
        "valor_atual_total": total,
        "valor_cenario_total": float(df["valor_cenario"].sum()),
        "ganho_perda_total": float(df["ganho_perda_cenario"].sum()),
        "dv01_total": float(df["dv01_r$"].sum()),
        "duration_media": float((w * df["duration_modificada"]).sum()) if total > 0 else 0.0,
        "convexidade_media": float((w * df["convexidade"]).sum()) if total > 0 else 0.0,
        "retorno_esperado_total": float(df["retorno_esperado_pnl"].sum()),
        "pnl_otimista_total": float(df["pnl_otimista"].sum()),
        "pnl_base_total": float(df["pnl_base"].sum()),
        "pnl_pessimista_total": float(df["pnl_pessimista"].sum()),
    }
    return df, summary


def pnl_curve_for_position(pos: Position, min_rate: float, max_rate: float, points: int = 50) -> pd.DataFrame:
    rates = np.linspace(min_rate, max_rate, points)
    buy = price_from_yield(pos, pos.buy_rate)
    qty = pos.invested_amount / buy if buy > 0 else 0.0
    current_value = qty * price_from_yield(pos, pos.current_rate)
    pnl = [qty * price_from_yield(pos, float(r)) - current_value for r in rates]
    return pd.DataFrame({"taxa (%)": rates * 100, "pnl_r$": pnl})


def sensitivity_by_shift(df_positions: pd.DataFrame, shifts_bp: Iterable[int]) -> pd.DataFrame:
    positions = dataframe_to_positions(df_positions)
    rows = []
    for s in shifts_bp:
        cfg = ScenarioConfig(s, s, s, 0.0, 1.0, 0.0)
        _, summary = analyze_portfolio(positions, cfg)
        rows.append({"choque_bp": s, "pnl_r$": summary["pnl_base_total"]})
    return pd.DataFrame(rows)


def positions_to_dataframe(positions: Iterable[Position]) -> pd.DataFrame:
    return pd.DataFrame([asdict(p) for p in positions])


def dataframe_to_positions(df: pd.DataFrame) -> list[Position]:
    if df.empty:
        return []

    out: list[Position] = []
    for _, r in df.iterrows():
        t = str(r.get("title_type", TITLE_NTNB))
        out.append(
            Position(
                name=str(r.get("name", "Posição")),
                title_type=t if t in VALID_TYPES else TITLE_NTNB,
                invested_amount=float(r.get("invested_amount", 0)),
                nominal_value=float(r.get("nominal_value", 1000)),
                buy_rate=float(r.get("buy_rate", 0.06)),
                current_rate=float(r.get("current_rate", 0.06)),
                scenario_rate=float(r.get("scenario_rate", 0.05)),
                years_to_maturity=float(r.get("years_to_maturity", 5.0)),
                expected_ipca=float(r.get("expected_ipca", 0.045)),
                coupon_rate=float(r.get("coupon_rate", 6.0 if t == TITLE_NTNB else 0.0)),
                frequency=max(1, int(r.get("frequency", 2))),
            )
        )
    return out
