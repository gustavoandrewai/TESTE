"""App Streamlit para simulação de NTN-B (Tesouro IPCA+) e Tesouro Prefixado."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
import streamlit as st


@dataclass
class BondResult:
    """Resultado de precificação para um título."""

    current_price: float
    scenario_price: float
    variation_pct: float
    approx_duration: float


def real_to_nominal_rate(real_rate: float, ipca: float) -> float:
    """Converte taxa real em taxa nominal anual (aproximação de Fisher exata)."""

    return (1.0 + real_rate) * (1.0 + ipca) - 1.0


def ntnb_price(nominal_value: float, years_to_maturity: float, ipca: float, real_rate: float) -> float:
    """Preço simplificado de NTN-B zero cupom com VNA projetado e desconto por taxa real."""

    vna_projected = nominal_value * (1.0 + ipca) ** years_to_maturity
    return vna_projected / (1.0 + real_rate) ** years_to_maturity


def prefixado_price(nominal_value: float, years_to_maturity: float, nominal_rate: float) -> float:
    """Preço de Tesouro Prefixado zero cupom (desconto a taxa nominal)."""

    return nominal_value / (1.0 + nominal_rate) ** years_to_maturity


def approx_modified_duration(years_to_maturity: float, annual_yield: float) -> float:
    """Duration modificada aproximada para título zero cupom."""

    return years_to_maturity / (1.0 + annual_yield)


def simulate_bonds(
    nominal_value: float,
    years_to_maturity: float,
    ipca: float,
    current_real_rate: float,
    scenario_real_rate: float,
) -> dict[str, BondResult]:
    """Calcula métricas de preço para NTN-B e Prefixado no cenário atual e alternativo."""

    # NTN-B
    ntnb_current = ntnb_price(nominal_value, years_to_maturity, ipca, current_real_rate)
    ntnb_scenario = ntnb_price(nominal_value, years_to_maturity, ipca, scenario_real_rate)

    # Prefixado (taxa nominal derivada do IPCA + taxa real)
    nominal_current = real_to_nominal_rate(current_real_rate, ipca)
    nominal_scenario = real_to_nominal_rate(scenario_real_rate, ipca)

    pref_current = prefixado_price(nominal_value, years_to_maturity, nominal_current)
    pref_scenario = prefixado_price(nominal_value, years_to_maturity, nominal_scenario)

    return {
        "NTN-B": BondResult(
            current_price=ntnb_current,
            scenario_price=ntnb_scenario,
            variation_pct=(ntnb_scenario / ntnb_current - 1.0),
            approx_duration=approx_modified_duration(years_to_maturity, current_real_rate),
        ),
        "Tesouro Prefixado": BondResult(
            current_price=pref_current,
            scenario_price=pref_scenario,
            variation_pct=(pref_scenario / pref_current - 1.0),
            approx_duration=approx_modified_duration(years_to_maturity, nominal_current),
        ),
    }


def build_price_curve(
    nominal_value: float,
    years_to_maturity: float,
    ipca: float,
    min_rate: float = 0.02,
    max_rate: float = 0.12,
    points: int = 60,
) -> pd.DataFrame:
    """Monta curva de preço versus taxa real para NTN-B e Prefixado."""

    real_rates = np.linspace(min_rate, max_rate, points)
    nominal_rates = real_to_nominal_rate(real_rates, ipca)

    return pd.DataFrame(
        {
            "Taxa real (%)": real_rates * 100,
            "Preço NTN-B": [ntnb_price(nominal_value, years_to_maturity, ipca, r) for r in real_rates],
            "Preço Prefixado": [prefixado_price(nominal_value, years_to_maturity, n) for n in nominal_rates],
        }
    )


def parse_scenarios(raw: str) -> list[float]:
    """Converte texto de cenários (ex.: '7, 6, 5, 4') para lista de taxas em decimal."""

    values: list[float] = []
    for item in raw.replace(";", ",").split(","):
        item = item.strip().replace("%", "")
        if not item:
            continue
        values.append(float(item) / 100)
    return values


def build_sensitivity_table(
    nominal_value: float,
    years_to_maturity: float,
    ipca: float,
    current_real_rate: float,
    scenarios: Iterable[float],
) -> pd.DataFrame:
    """Cria tabela com sensibilidade de preço para múltiplos cenários de taxa real."""

    base = simulate_bonds(nominal_value, years_to_maturity, ipca, current_real_rate, current_real_rate)
    base_ntnb = base["NTN-B"].current_price
    base_pref = base["Tesouro Prefixado"].current_price

    rows = []
    for scenario in scenarios:
        sim = simulate_bonds(nominal_value, years_to_maturity, ipca, current_real_rate, scenario)
        rows.append(
            {
                "Taxa real cenário (%)": scenario * 100,
                "Preço NTN-B": sim["NTN-B"].scenario_price,
                "Variação NTN-B (%)": (sim["NTN-B"].scenario_price / base_ntnb - 1.0) * 100,
                "Preço Prefixado": sim["Tesouro Prefixado"].scenario_price,
                "Variação Prefixado (%)": (sim["Tesouro Prefixado"].scenario_price / base_pref - 1.0) * 100,
            }
        )

    return pd.DataFrame(rows).sort_values("Taxa real cenário (%)", ascending=False)


def main() -> None:
    """Renderiza dashboard principal."""

    st.set_page_config(page_title="Simulador NTN-B e Prefixado", page_icon="📈", layout="wide")

    st.title("📈 Simulador de NTN-B e Tesouro Prefixado")
    st.caption("Dashboard para simulação de preço, variação e sensibilidade por taxa de juros.")

    with st.container():
        c1, c2, c3, c4, c5 = st.columns(5)
        nominal_value = c1.number_input("Valor nominal (R$)", min_value=1.0, value=1000.0, step=100.0)
        years_to_maturity = c2.number_input("Anos até vencimento", min_value=0.5, value=5.0, step=0.5)
        ipca = c3.number_input("IPCA esperado (% a.a.)", min_value=0.0, value=4.5, step=0.1) / 100
        current_real_rate = c4.number_input("Taxa real atual (% a.a.)", min_value=0.0, value=6.0, step=0.1) / 100
        scenario_real_rate = c5.number_input("Taxa real de cenário (% a.a.)", min_value=0.0, value=5.0, step=0.1) / 100

    results = simulate_bonds(
        nominal_value=nominal_value,
        years_to_maturity=years_to_maturity,
        ipca=ipca,
        current_real_rate=current_real_rate,
        scenario_real_rate=scenario_real_rate,
    )

    titulo = st.radio("Título para destaque dos KPIs", ["NTN-B", "Tesouro Prefixado"], horizontal=True)
    selected = results[titulo]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Preço atual", f"R$ {selected.current_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    k2.metric("Preço no cenário", f"R$ {selected.scenario_price:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    k3.metric("Variação percentual", f"{selected.variation_pct * 100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", "."))
    k4.metric("Duration aproximada", f"{selected.approx_duration:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.divider()

    curve_df = build_price_curve(nominal_value, years_to_maturity, ipca)
    st.subheader("Gráfico: preço vs taxa de juros")
    st.line_chart(curve_df.set_index("Taxa real (%)")[["Preço NTN-B", "Preço Prefixado"]], height=360)

    st.subheader("Sensibilidade por múltiplos cenários de taxa")
    scenarios_raw = st.text_input(
        "Taxas reais de cenário (%), separadas por vírgula",
        value="7, 6, 5, 4",
        help="Exemplo: 8,5; 7; 6,25",
    )

    try:
        scenarios = parse_scenarios(scenarios_raw)
        if not scenarios:
            st.warning("Informe ao menos uma taxa de cenário.")
            return
    except ValueError:
        st.error("Não foi possível interpretar as taxas de cenário. Use números separados por vírgula.")
        return

    sensitivity_df = build_sensitivity_table(
        nominal_value=nominal_value,
        years_to_maturity=years_to_maturity,
        ipca=ipca,
        current_real_rate=current_real_rate,
        scenarios=scenarios,
    )

    st.dataframe(sensitivity_df, use_container_width=True, hide_index=True)
    st.bar_chart(
        sensitivity_df.set_index("Taxa real cenário (%)")[["Variação NTN-B (%)", "Variação Prefixado (%)"]],
        height=320,
    )


if __name__ == "__main__":
    main()
