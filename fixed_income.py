"""Motor financeiro para simulação de NTN-B e Tesouro Prefixado.

As funções deste módulo centralizam a modelagem de preço, duration, convexidade,
DV01 e consolidação de carteira para uso no app Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

import numpy as np
import pandas as pd


TITLE_NTNB = "NTN-B"
TITLE_PREFIXADO = "Tesouro Prefixado"
VALID_TYPES = {TITLE_NTNB, TITLE_PREFIXADO}


@dataclass
class Position:
    """Representa uma posição de renda fixa para análise de carteira."""

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
    """Configuração dos cenários de estresse e probabilidades."""

    optimistic_shift_bp: float = -100.0
    base_shift_bp: float = 0.0
    pessimistic_shift_bp: float = 100.0
    prob_optimistic: float = 0.3
    prob_base: float = 0.4
    prob_pessimistic: float = 0.3


def real_to_nominal_rate(real_rate: float, ipca: float) -> float:
    """Converte taxa real para taxa nominal anual pela identidade de Fisher."""

    return (1.0 + real_rate) * (1.0 + ipca) - 1.0


def _periodic_rate(position: Position, annual_rate: float) -> float:
    """Retorna taxa por período consistente com tipo de título e frequência."""

    annual_nominal = (
        real_to_nominal_rate(annual_rate, position.expected_ipca)
        if position.title_type == TITLE_NTNB
        else annual_rate
    )
    return annual_nominal / position.frequency


def _cashflows(position: Position) -> list[tuple[float, float]]:
    """Gera fluxo de caixa nominal por período.

    - NTN-B: principal corrigido por IPCA esperado ao longo do tempo + cupom real.
    - Prefixado: principal fixo + cupom nominal (se houver; LTN costuma ser 0%).
    """

    periods = max(1, int(round(position.years_to_maturity * position.frequency)))
    flows: list[tuple[float, float]] = []

    for i in range(1, periods + 1):
        t = i / position.frequency

        if position.title_type == TITLE_NTNB:
            principal_t = position.nominal_value * (1.0 + position.expected_ipca) ** t
            coupon = principal_t * (position.coupon_rate / 100.0) / position.frequency
        else:
            principal_t = position.nominal_value
            coupon = principal_t * (position.coupon_rate / 100.0) / position.frequency

        redemption = principal_t if i == periods else 0.0
        flows.append((t, coupon + redemption))

    return flows


def price_from_yield(position: Position, annual_rate: float) -> float:
    """Precifica o título pelo desconto dos fluxos de caixa."""

    periodic_rate = _periodic_rate(position, annual_rate)
    price = 0.0

    for t, cf in _cashflows(position):
        n = int(round(t * position.frequency))
        price += cf / (1.0 + periodic_rate) ** n

    return price


def duration_convexity(position: Position, annual_rate: float) -> tuple[float, float]:
    """Calcula duration modificada e convexidade aproximada."""

    periodic_rate = _periodic_rate(position, annual_rate)
    flows = _cashflows(position)
    price = price_from_yield(position, annual_rate)
    if price <= 0:
        return 0.0, 0.0

    macaulay = 0.0
    convexity = 0.0

    for t, cf in flows:
        n = int(round(t * position.frequency))
        pv = cf / (1.0 + periodic_rate) ** n
        macaulay += t * pv

        # Convexidade discreta para taxa por período, convertida para base anual.
        convexity += (n * (n + 1) * pv) / ((1.0 + periodic_rate) ** 2)

    macaulay /= price
    modified = macaulay / (1.0 + periodic_rate)
    convexity = convexity / (price * (position.frequency**2))

    return modified, convexity


def dv01(position: Position, annual_rate: float) -> float:
    """DV01 por unidade de valor nominal: variação de preço para +1bp na taxa."""

    p0 = price_from_yield(position, annual_rate)
    p1 = price_from_yield(position, annual_rate + 0.0001)
    return p1 - p0


def normalize_probabilities(config: ScenarioConfig) -> ScenarioConfig:
    """Normaliza probabilidades para somarem 1.0."""

    total = config.prob_optimistic + config.prob_base + config.prob_pessimistic
    if total <= 0:
        config.prob_optimistic, config.prob_base, config.prob_pessimistic = 1 / 3, 1 / 3, 1 / 3
        return config

    config.prob_optimistic /= total
    config.prob_base /= total
    config.prob_pessimistic /= total
    return config


def _scenario_rate(base_rate: float, shift_bp: float) -> float:
    """Aplica choque (em bps) sobre uma taxa anual."""

    return max(0.0001, base_rate + shift_bp / 10000.0)


def analyze_position(position: Position, config: ScenarioConfig) -> dict:
    """Consolida métricas de uma posição para cenários e risco."""

    price_buy = price_from_yield(position, position.buy_rate)
    price_current = price_from_yield(position, position.current_rate)
    price_custom = price_from_yield(position, position.scenario_rate)

    quantity = position.invested_amount / price_buy if price_buy > 0 else 0.0
    current_value = quantity * price_current
    custom_value = quantity * price_custom
    pnl_custom = custom_value - current_value

    opt_rate = _scenario_rate(position.current_rate, config.optimistic_shift_bp)
    base_rate = _scenario_rate(position.current_rate, config.base_shift_bp)
    pess_rate = _scenario_rate(position.current_rate, config.pessimistic_shift_bp)

    value_optimistic = quantity * price_from_yield(position, opt_rate)
    value_base = quantity * price_from_yield(position, base_rate)
    value_pessimistic = quantity * price_from_yield(position, pess_rate)

    pnl_opt = value_optimistic - current_value
    pnl_base = value_base - current_value
    pnl_pess = value_pessimistic - current_value

    modified_duration, convexity = duration_convexity(position, position.current_rate)
    dv01_position = dv01(position, position.current_rate) * quantity

    expected_pnl = (
        pnl_opt * config.prob_optimistic + pnl_base * config.prob_base + pnl_pess * config.prob_pessimistic
    )

    return {
        "nome": position.name,
        "tipo": position.title_type,
        "valor_investido": position.invested_amount,
        "quantidade": quantity,
        "preco_compra": price_buy,
        "preco_atual": price_current,
        "preco_cenario": price_custom,
        "valor_atual": current_value,
        "valor_cenario": custom_value,
        "ganho_perda_cenario": pnl_custom,
        "variacao_cenario_pct": (price_custom / price_current - 1.0) * 100 if price_current > 0 else 0.0,
        "taxa_compra_pct": position.buy_rate * 100,
        "taxa_atual_pct": position.current_rate * 100,
        "taxa_cenario_pct": position.scenario_rate * 100,
        "duration_modificada": modified_duration,
        "convexidade": convexity,
        "dv01_r$": dv01_position,
        "pnl_otimista": pnl_opt,
        "pnl_base": pnl_base,
        "pnl_pessimista": pnl_pess,
        "retorno_esperado_pnl": expected_pnl,
        "value_optimistic": value_optimistic,
        "value_base": value_base,
        "value_pessimistic": value_pessimistic,
    }


def analyze_portfolio(positions: Iterable[Position], config: ScenarioConfig) -> tuple[pd.DataFrame, dict]:
    """Gera visão consolidada da carteira e agregados de risco."""

    config = normalize_probabilities(config)
    rows = [analyze_position(p, config) for p in positions]

    if not rows:
        empty = pd.DataFrame()
        return empty, {
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

    df = pd.DataFrame(rows)
    total_value = float(df["valor_atual"].sum())

    if total_value > 0:
        weights = df["valor_atual"] / total_value
        duration_media = float((weights * df["duration_modificada"]).sum())
        convexidade_media = float((weights * df["convexidade"]).sum())
    else:
        duration_media = 0.0
        convexidade_media = 0.0

    summary = {
        "valor_atual_total": total_value,
        "valor_cenario_total": float(df["valor_cenario"].sum()),
        "ganho_perda_total": float(df["ganho_perda_cenario"].sum()),
        "dv01_total": float(df["dv01_r$"].sum()),
        "duration_media": duration_media,
        "convexidade_media": convexidade_media,
        "retorno_esperado_total": float(df["retorno_esperado_pnl"].sum()),
        "pnl_otimista_total": float(df["pnl_otimista"].sum()),
        "pnl_base_total": float(df["pnl_base"].sum()),
        "pnl_pessimista_total": float(df["pnl_pessimista"].sum()),
    }

    return df, summary


def pnl_curve_for_position(position: Position, min_rate: float, max_rate: float, points: int = 50) -> pd.DataFrame:
    """Curva de P&L da posição em função da taxa de juros."""

    rates = np.linspace(min_rate, max_rate, points)
    price_buy = price_from_yield(position, position.buy_rate)
    quantity = position.invested_amount / price_buy if price_buy > 0 else 0.0
    price_current = price_from_yield(position, position.current_rate)
    current_value = quantity * price_current

    rows = []
    for r in rates:
        value_r = quantity * price_from_yield(position, float(r))
        rows.append({"taxa (%)": r * 100, "pnl_r$": value_r - current_value})

    return pd.DataFrame(rows)


def sensitivity_by_shift(df_positions: pd.DataFrame, shifts_bp: Iterable[int]) -> pd.DataFrame:
    """Sensibilidade consolidada de carteira para choques paralelos de taxa."""

    rows = []
    for shock in shifts_bp:
        config = ScenarioConfig(
            optimistic_shift_bp=float(shock),
            base_shift_bp=float(shock),
            pessimistic_shift_bp=float(shock),
            prob_optimistic=0.0,
            prob_base=1.0,
            prob_pessimistic=0.0,
        )
        positions = dataframe_to_positions(df_positions)
        _, summary = analyze_portfolio(positions, config)
        rows.append({"choque_bp": shock, "pnl_r$": summary["pnl_base_total"]})

    return pd.DataFrame(rows)


def positions_to_dataframe(positions: Iterable[Position]) -> pd.DataFrame:
    """Converte lista de posições para DataFrame (persistência/UI)."""

    return pd.DataFrame([asdict(p) for p in positions])


def dataframe_to_positions(df: pd.DataFrame) -> list[Position]:
    """Converte DataFrame da UI para lista de objetos Position."""

    if df.empty:
        return []

    positions: list[Position] = []
    for _, row in df.iterrows():
        title_type = str(row.get("title_type", TITLE_NTNB))
        if title_type not in VALID_TYPES:
            title_type = TITLE_NTNB

        positions.append(
            Position(
                name=str(row.get("name", "Posição")),
                title_type=title_type,
                invested_amount=float(row.get("invested_amount", 0.0)),
                nominal_value=float(row.get("nominal_value", 1000.0)),
                buy_rate=float(row.get("buy_rate", 0.06)),
                current_rate=float(row.get("current_rate", 0.06)),
                scenario_rate=float(row.get("scenario_rate", 0.05)),
                years_to_maturity=float(row.get("years_to_maturity", 5.0)),
                expected_ipca=float(row.get("expected_ipca", 0.045)),
                coupon_rate=float(row.get("coupon_rate", 6.0 if title_type == TITLE_NTNB else 0.0)),
                frequency=int(row.get("frequency", 2)),
            )
        )

    return positions
