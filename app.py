"""App Streamlit para análise profissional de carteira de renda fixa."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from fixed_income import (
    TITLE_NTNB,
    TITLE_PREFIXADO,
    Position,
    ScenarioConfig,
    analyze_portfolio,
    dataframe_to_positions,
    pnl_curve_for_position,
    positions_to_dataframe,
    sensitivity_by_shift,
)


def brl(value: float) -> str:
    """Formata número em BRL."""

    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(value: float) -> str:
    """Formata percentual."""

    return f"{value:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def init_state() -> None:
    """Inicializa estado da aplicação com carteira exemplo e cenários padrão."""

    if "positions_df" not in st.session_state:
        default_positions = [
            Position(
                name="NTN-B 2035",
                title_type=TITLE_NTNB,
                invested_amount=50000.0,
                nominal_value=1000.0,
                buy_rate=0.055,
                current_rate=0.06,
                scenario_rate=0.05,
                years_to_maturity=9.0,
                expected_ipca=0.045,
                coupon_rate=6.0,
                frequency=2,
            ),
            Position(
                name="Prefixado 2029",
                title_type=TITLE_PREFIXADO,
                invested_amount=35000.0,
                nominal_value=1000.0,
                buy_rate=0.105,
                current_rate=0.115,
                scenario_rate=0.10,
                years_to_maturity=3.0,
                expected_ipca=0.045,
                coupon_rate=0.0,
                frequency=2,
            ),
        ]
        st.session_state.positions_df = positions_to_dataframe(default_positions)

    if "scenario_config" not in st.session_state:
        st.session_state.scenario_config = {
            "optimistic_shift_bp": -100.0,
            "base_shift_bp": 0.0,
            "pessimistic_shift_bp": 100.0,
            "prob_optimistic": 0.30,
            "prob_base": 0.40,
            "prob_pessimistic": 0.30,
            "cdi_esperado": 0.13,
        }


def get_config() -> ScenarioConfig:
    """Obtém configuração de cenários do estado."""

    cfg = st.session_state.scenario_config
    return ScenarioConfig(
        optimistic_shift_bp=float(cfg["optimistic_shift_bp"]),
        base_shift_bp=float(cfg["base_shift_bp"]),
        pessimistic_shift_bp=float(cfg["pessimistic_shift_bp"]),
        prob_optimistic=float(cfg["prob_optimistic"]),
        prob_base=float(cfg["prob_base"]),
        prob_pessimistic=float(cfg["prob_pessimistic"]),
    )


def quick_scenario_button(label: str, opt: float, base: float, pess: float) -> None:
    """Aplica configuração rápida de cenário."""

    if st.button(label, use_container_width=True):
        st.session_state.scenario_config["optimistic_shift_bp"] = opt
        st.session_state.scenario_config["base_shift_bp"] = base
        st.session_state.scenario_config["pessimistic_shift_bp"] = pess


def render_top_kpis(summary: dict) -> None:
    """Renderiza KPIs consolidados no topo."""

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Valor atual da carteira", brl(summary["valor_atual_total"]))
    c2.metric("Valor no cenário custom", brl(summary["valor_cenario_total"]))
    c3.metric("Ganho/Perda cenário (R$)", brl(summary["ganho_perda_total"]))
    c4.metric("DV01 consolidado", brl(summary["dv01_total"]))
    c5.metric("Duration média", f"{summary['duration_media']:.2f}")


def render_simulacao_individual(positions_df: pd.DataFrame, config: ScenarioConfig) -> None:
    """Aba de simulação individual por posição."""

    st.subheader("Simulação individual")
    if positions_df.empty:
        st.info("Adicione posições na aba Carteira para visualizar esta análise.")
        return

    nomes = positions_df["name"].tolist()
    escolhido = st.selectbox("Selecione a posição", nomes)
    pos = dataframe_to_positions(positions_df[positions_df["name"] == escolhido])[0]

    df_ind, _ = analyze_portfolio([pos], config)
    row = df_ind.iloc[0]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Preço atual", brl(row["preco_atual"]))
    k2.metric("Preço no cenário", brl(row["preco_cenario"]))
    k3.metric("P&L cenário (R$)", brl(row["ganho_perda_cenario"]))
    k4.metric("DV01 posição", brl(row["dv01_r$"]))

    st.caption("**DV01**: variação aproximada em R$ no valor da posição para um choque de +1 bps na taxa de juros.")

    min_rate = max(0.0001, pos.current_rate - 0.04)
    max_rate = pos.current_rate + 0.04
    curve = pnl_curve_for_position(pos, min_rate=min_rate, max_rate=max_rate, points=60)
    st.line_chart(curve.set_index("taxa (%)"), height=340)


def render_carteira_tab() -> tuple[pd.DataFrame, ScenarioConfig, pd.DataFrame, dict]:
    """Aba de carteira com edição dinâmica e visão consolidada."""

    st.subheader("Carteira de títulos")

    editor_df = st.data_editor(
        st.session_state.positions_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "name": st.column_config.TextColumn("Nome da posição", required=True),
            "title_type": st.column_config.SelectboxColumn("Tipo", options=[TITLE_NTNB, TITLE_PREFIXADO]),
            "invested_amount": st.column_config.NumberColumn("Valor investido (R$)", min_value=0.0, step=1000.0),
            "nominal_value": st.column_config.NumberColumn("Valor nominal", min_value=100.0, step=100.0),
            "buy_rate": st.column_config.NumberColumn("Taxa compra", format="%.4f"),
            "current_rate": st.column_config.NumberColumn("Taxa atual", format="%.4f"),
            "scenario_rate": st.column_config.NumberColumn("Taxa cenário", format="%.4f"),
            "years_to_maturity": st.column_config.NumberColumn("Prazo (anos)", min_value=0.1, step=0.5),
            "expected_ipca": st.column_config.NumberColumn("IPCA esperado", format="%.4f"),
            "coupon_rate": st.column_config.NumberColumn("Cupom anual (%)", min_value=0.0, step=0.5),
            "frequency": st.column_config.NumberColumn("Frequência", min_value=1, max_value=12, step=1),
        },
    )

    st.session_state.positions_df = editor_df

    config = get_config()
    positions = dataframe_to_positions(editor_df)
    detail_df, summary = analyze_portfolio(positions, config)

    st.markdown("### Visão consolidada")
    render_top_kpis(summary)

    if not detail_df.empty:
        view_cols = [
            "nome",
            "tipo",
            "valor_investido",
            "preco_atual",
            "preco_cenario",
            "ganho_perda_cenario",
            "duration_modificada",
            "dv01_r$",
        ]
        st.dataframe(detail_df[view_cols], use_container_width=True, hide_index=True)

    return editor_df, config, detail_df, summary


def render_cenarios_tab(detail_df: pd.DataFrame, summary: dict) -> None:
    """Aba de cenários, estresse e probabilidades."""

    st.subheader("Cenários de juros e probabilidades")

    b1, b2, b3 = st.columns(3)
    with b1:
        quick_scenario_button("Cenário rápido: Otimista", -150.0, -50.0, 50.0)
    with b2:
        quick_scenario_button("Cenário rápido: Base", -100.0, 0.0, 100.0)
    with b3:
        quick_scenario_button("Cenário rápido: Pessimista", -50.0, 50.0, 150.0)

    c1, c2, c3 = st.columns(3)
    st.session_state.scenario_config["optimistic_shift_bp"] = c1.number_input(
        "Choque otimista (bps)", value=float(st.session_state.scenario_config["optimistic_shift_bp"]), step=10.0
    )
    st.session_state.scenario_config["base_shift_bp"] = c2.number_input(
        "Choque base (bps)", value=float(st.session_state.scenario_config["base_shift_bp"]), step=10.0
    )
    st.session_state.scenario_config["pessimistic_shift_bp"] = c3.number_input(
        "Choque pessimista (bps)", value=float(st.session_state.scenario_config["pessimistic_shift_bp"]), step=10.0
    )

    p1, p2, p3 = st.columns(3)
    st.session_state.scenario_config["prob_optimistic"] = p1.slider(
        "Prob. otimista", min_value=0.0, max_value=1.0, value=float(st.session_state.scenario_config["prob_optimistic"]), step=0.05
    )
    st.session_state.scenario_config["prob_base"] = p2.slider(
        "Prob. base", min_value=0.0, max_value=1.0, value=float(st.session_state.scenario_config["prob_base"]), step=0.05
    )
    st.session_state.scenario_config["prob_pessimistic"] = p3.slider(
        "Prob. pessimista", min_value=0.0, max_value=1.0, value=float(st.session_state.scenario_config["prob_pessimistic"]), step=0.05
    )

    st.info(
        "Os três cenários de stress calculam P&L da carteira para choques paralelos de taxa. "
        "Use probabilidades para estimar retorno esperado ponderado."
    )

    if detail_df.empty:
        st.warning("Sem posições para exibir cenários.")
        return

    scenario_table = pd.DataFrame(
        [
            {"Cenário": "Otimista", "P&L carteira (R$)": summary["pnl_otimista_total"]},
            {"Cenário": "Base", "P&L carteira (R$)": summary["pnl_base_total"]},
            {"Cenário": "Pessimista", "P&L carteira (R$)": summary["pnl_pessimista_total"]},
            {"Cenário": "Esperado (ponderado)", "P&L carteira (R$)": summary["retorno_esperado_total"]},
        ]
    )
    st.dataframe(scenario_table, use_container_width=True, hide_index=True)
    st.bar_chart(scenario_table.set_index("Cenário"), height=320)


def render_risco_tab(positions_df: pd.DataFrame, detail_df: pd.DataFrame, summary: dict) -> None:
    """Aba de risco com DV01, duration, convexidade e sensibilidade consolidada."""

    st.subheader("Risco e sensibilidade")

    if detail_df.empty:
        st.warning("Sem posições para análise de risco.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("DV01 carteira", brl(summary["dv01_total"]))
    c2.metric("Duration média ponderada", f"{summary['duration_media']:.2f}")
    c3.metric("Convexidade média", f"{summary['convexidade_media']:.4f}")

    st.caption(
        "DV01 mede quanto a carteira tende a variar em R$ para um choque de +1 bp na curva. "
        "Quanto maior em módulo, maior a sensibilidade a juros."
    )

    risk_table = detail_df[["nome", "tipo", "duration_modificada", "convexidade", "dv01_r$"]].copy()
    st.dataframe(risk_table, use_container_width=True, hide_index=True)

    shifts = [-300, -200, -100, -50, 0, 50, 100, 200, 300]
    sens_df = sensitivity_by_shift(positions_df, shifts)
    st.line_chart(sens_df.set_index("choque_bp"), height=340)

    comp = (
        detail_df.groupby("tipo")[["pnl_otimista", "pnl_base", "pnl_pessimista"]]
        .sum()
        .reset_index()
        .set_index("tipo")
    )
    st.bar_chart(comp, height=320)


def render_benchmark_tab(summary: dict) -> None:
    """Aba de benchmark CDI e excesso de retorno."""

    st.subheader("Benchmark CDI")
    st.session_state.scenario_config["cdi_esperado"] = st.number_input(
        "CDI esperado (% a.a.)",
        value=float(st.session_state.scenario_config["cdi_esperado"]) * 100,
        step=0.1,
    ) / 100

    valor_atual = summary["valor_atual_total"]
    retorno_esperado_pct = summary["retorno_esperado_total"] / valor_atual if valor_atual > 0 else 0.0
    excesso = retorno_esperado_pct - st.session_state.scenario_config["cdi_esperado"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Retorno esperado carteira", pct(retorno_esperado_pct * 100))
    c2.metric("CDI esperado", pct(st.session_state.scenario_config["cdi_esperado"] * 100))
    c3.metric("Excesso sobre CDI", pct(excesso * 100))

    table = pd.DataFrame(
        {
            "Métrica": ["Retorno esperado carteira", "CDI esperado", "Excesso sobre CDI"],
            "Valor (%)": [retorno_esperado_pct * 100, st.session_state.scenario_config["cdi_esperado"] * 100, excesso * 100],
        }
    )
    st.dataframe(table, use_container_width=True, hide_index=True)


def render_save_and_reset() -> None:
    """Controles de persistência local e reset rápido."""

    st.markdown("### Persistência local")
    payload = {
        "positions": st.session_state.positions_df.to_dict(orient="records"),
        "scenario_config": st.session_state.scenario_config,
    }
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2)

    c1, c2 = st.columns(2)
    c1.download_button(
        "Salvar simulação local (.json)",
        data=payload_json,
        file_name="simulacao_carteira_rf.json",
        mime="application/json",
        use_container_width=True,
    )

    uploaded = c2.file_uploader("Carregar simulação (.json)", type=["json"])
    if uploaded is not None:
        data = json.loads(uploaded.read().decode("utf-8"))
        st.session_state.positions_df = pd.DataFrame(data.get("positions", []))
        st.session_state.scenario_config.update(data.get("scenario_config", {}))
        st.success("Simulação carregada com sucesso.")

    if st.button("Resetar simulador", type="primary", use_container_width=True):
        for k in ["positions_df", "scenario_config"]:
            if k in st.session_state:
                del st.session_state[k]
        init_state()
        st.success("Simulador resetado para os valores padrão.")


def main() -> None:
    """Render principal do app."""

    st.set_page_config(page_title="Renda Fixa Pro", page_icon="📊", layout="wide")
    init_state()

    st.title("📊 Renda Fixa Pro | Carteira NTN-B e Prefixado")
    st.caption("Marcação a mercado, cenários de juros, risco (DV01/duration) e comparação com CDI.")

    tabs = st.tabs(["Simulação individual", "Carteira", "Cenários", "Risco", "Benchmark"])

    with tabs[1]:
        positions_df, config, detail_df, summary = render_carteira_tab()

    with tabs[0]:
        render_simulacao_individual(positions_df, config)

    with tabs[2]:
        render_cenarios_tab(detail_df, summary)

    with tabs[3]:
        render_risco_tab(positions_df, detail_df, summary)

    with tabs[4]:
        render_benchmark_tab(summary)

    st.divider()
    render_save_and_reset()


if __name__ == "__main__":
    main()
