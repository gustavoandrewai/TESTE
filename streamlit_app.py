"""Renda Fixa Pro - Streamlit."""

from __future__ import annotations

import json
from datetime import UTC, datetime

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


def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v: float) -> str:
    return f"{v:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def default_state() -> tuple[pd.DataFrame, dict]:
    positions = [
        Position("NTN-B 2035", TITLE_NTNB, 50000, 1000, 0.055, 0.06, 0.05, 9, 0.045, 6.0, 2),
        Position("Prefixado 2029", TITLE_PREFIXADO, 35000, 1000, 0.105, 0.115, 0.10, 3, 0.045, 0.0, 2),
    ]
    cfg = {
        "optimistic_shift_bp": -100.0,
        "base_shift_bp": 0.0,
        "pessimistic_shift_bp": 100.0,
        "prob_optimistic": 0.30,
        "prob_base": 0.40,
        "prob_pessimistic": 0.30,
        "cdi_esperado": 0.13,
    }
    return positions_to_dataframe(positions), cfg


def init_state() -> None:
    if "positions_df" not in st.session_state or "scenario_config" not in st.session_state:
        st.session_state.positions_df, st.session_state.scenario_config = default_state()


def get_config() -> ScenarioConfig:
    c = st.session_state.scenario_config
    return ScenarioConfig(c["optimistic_shift_bp"], c["base_shift_bp"], c["pessimistic_shift_bp"], c["prob_optimistic"], c["prob_base"], c["prob_pessimistic"])


def metric_row(items: list[tuple[str, str]]) -> None:
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.metric(label, value)


@st.cache_data(ttl=300)
def fetch_yahoo_fii_snapshot(tickers: list[str]) -> pd.DataFrame:
    """Busca snapshot de FIIs no Yahoo Finance.

    Cache curto para evitar múltiplas chamadas em sequência e botão de refresh
    para invalidar manualmente quando o usuário quiser atualizar.
    """
    import yfinance as yf

    data = []
    for ticker in tickers:
        yf_ticker = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
        history = yf.Ticker(yf_ticker).history(period="3mo", interval="1d")
        if history.empty:
            continue
        close = history["Close"]
        data.append(
            {
                "ticker": yf_ticker.replace(".SA", ""),
                "preco_atual": float(close.iloc[-1]),
                "retorno_1m": float(close.iloc[-1] / close.iloc[max(0, len(close) - 22)] - 1) if len(close) > 22 else 0.0,
                "retorno_3m": float(close.iloc[-1] / close.iloc[0] - 1),
                "volatilidade_3m": float(close.pct_change().dropna().std() * (252**0.5)),
                "liquidez_media_21d": float(history["Volume"].tail(21).mean()),
            }
        )
    return pd.DataFrame(data)




def didatic_manual_panel() -> None:
    """Painel didático para orientar ajustes manuais."""
    with st.expander("Guia rápido de ajustes manuais (didático)", expanded=False):
        st.markdown(
            """
            **1) Taxa atual**: usada na marcação a mercado de hoje.  
            **2) Taxa cenário**: taxa que você quer testar para ver ganho/perda.  
            **3) Prazo (anos)**: sensibilidade cresce com prazo.  
            **4) Duration alvo**: se ativada, o app estima um prazo equivalente para essa duration.
            """
        )

def scenario_controls() -> None:
    cfg = st.session_state.scenario_config

    presets = {
        "Otimista": (-150.0, -50.0, 50.0),
        "Base": (-100.0, 0.0, 100.0),
        "Pessimista": (-50.0, 50.0, 150.0),
    }
    cols = st.columns(3)
    for col, (name, values) in zip(cols, presets.items()):
        if col.button(f"Cenário rápido: {name}", use_container_width=True):
            cfg["optimistic_shift_bp"], cfg["base_shift_bp"], cfg["pessimistic_shift_bp"] = values

    for key, label, step in [
        ("optimistic_shift_bp", "Choque otimista (bps)", 10.0),
        ("base_shift_bp", "Choque base (bps)", 10.0),
        ("pessimistic_shift_bp", "Choque pessimista (bps)", 10.0),
    ]:
        cfg[key] = st.number_input(label, value=float(cfg[key]), step=step)

    pcols = st.columns(3)
    for col, key, label in [
        (pcols[0], "prob_optimistic", "Prob. otimista"),
        (pcols[1], "prob_base", "Prob. base"),
        (pcols[2], "prob_pessimistic", "Prob. pessimista"),
    ]:
        cfg[key] = col.slider(label, 0.0, 1.0, float(cfg[key]), 0.05)


def portfolio_editor() -> pd.DataFrame:
    return st.data_editor(
        st.session_state.positions_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "name": st.column_config.TextColumn("Nome", required=True),
            "title_type": st.column_config.SelectboxColumn("Tipo", options=[TITLE_NTNB, TITLE_PREFIXADO]),
            "invested_amount": st.column_config.NumberColumn("Investido (R$)", min_value=0.0, step=1000.0),
            "nominal_value": st.column_config.NumberColumn("Valor nominal", min_value=100.0, step=100.0),
            "buy_rate": st.column_config.NumberColumn("Taxa compra", format="%.4f"),
            "current_rate": st.column_config.NumberColumn("Taxa atual", format="%.4f"),
            "scenario_rate": st.column_config.NumberColumn("Taxa cenário", format="%.4f"),
            "years_to_maturity": st.column_config.NumberColumn("Prazo", min_value=0.1, step=0.5),
            "expected_ipca": st.column_config.NumberColumn("IPCA", format="%.4f"),
            "coupon_rate": st.column_config.NumberColumn("Cupom (%)", min_value=0.0, step=0.5),
            "frequency": st.column_config.NumberColumn("Freq", min_value=1, max_value=12, step=1),
            "use_duration_target": st.column_config.CheckboxColumn("Usar duration alvo"),
            "duration_target": st.column_config.NumberColumn("Duration alvo", min_value=0.0, step=0.1),
        },
    )


def save_restore_controls() -> None:
    payload = {
        "positions": st.session_state.positions_df.to_dict(orient="records"),
        "scenario_config": st.session_state.scenario_config,
    }
    cols = st.columns(2)
    cols[0].download_button(
        "Salvar simulação (.json)",
        json.dumps(payload, ensure_ascii=False, indent=2),
        "simulacao_carteira_rf.json",
        "application/json",
        use_container_width=True,
    )

    loaded = cols[1].file_uploader("Carregar simulação (.json)", type=["json"])
    if loaded is not None:
        data = json.loads(loaded.read().decode("utf-8"))
        st.session_state.positions_df = pd.DataFrame(data.get("positions", []))
        st.session_state.scenario_config.update(data.get("scenario_config", {}))
        st.success("Simulação carregada.")

    if st.button("Resetar simulador", type="primary", use_container_width=True):
        st.session_state.positions_df, st.session_state.scenario_config = default_state()
        st.success("Reset concluído.")


def main() -> None:
    st.set_page_config(page_title="Renda Fixa Pro", page_icon="📊", layout="wide")
    init_state()
    st.title("📊 Renda Fixa Pro | Carteira NTN-B e Prefixado")
    st.caption("Análise de carteira, cenários, risco, P&L e benchmark CDI.")
    didatic_manual_panel()

    tabs = st.tabs(["Simulação individual", "Carteira", "Cenários", "Risco", "Benchmark", "FIIs Yahoo"])

    with tabs[1]:
        st.subheader("Carteira")
        st.session_state.positions_df = portfolio_editor()
        detail_df, summary = analyze_portfolio(dataframe_to_positions(st.session_state.positions_df), get_config())
        metric_row([
            ("Valor atual", brl(summary["valor_atual_total"])),
            ("Valor cenário", brl(summary["valor_cenario_total"])),
            ("P&L cenário", brl(summary["ganho_perda_total"])),
            ("DV01", brl(summary["dv01_total"])),
            ("Duration média", f"{summary['duration_media']:.2f}"),
        ])
        if not detail_df.empty:
            st.dataframe(detail_df[["nome", "tipo", "preco_atual", "preco_cenario", "ganho_perda_cenario", "duration_modificada", "prazo_utilizado", "dv01_r$"]], use_container_width=True, hide_index=True)

    with tabs[0]:
        st.subheader("Simulação individual")
        if st.session_state.positions_df.empty:
            st.info("Adicione posições na aba Carteira.")
        else:
            name = st.selectbox("Posição", st.session_state.positions_df["name"].tolist())
            idx = st.session_state.positions_df.index[st.session_state.positions_df["name"] == name][0]
            with st.expander("Ajuste manual rápido desta posição", expanded=False):
                st.session_state.positions_df.loc[idx, "current_rate"] = st.slider("Taxa atual", 0.0, 0.30, float(st.session_state.positions_df.loc[idx, "current_rate"]), 0.001)
                st.session_state.positions_df.loc[idx, "scenario_rate"] = st.slider("Taxa cenário", 0.0, 0.30, float(st.session_state.positions_df.loc[idx, "scenario_rate"]), 0.001)
                st.session_state.positions_df.loc[idx, "years_to_maturity"] = st.slider("Prazo (anos)", 0.5, 40.0, float(st.session_state.positions_df.loc[idx, "years_to_maturity"]), 0.5)
                st.session_state.positions_df.loc[idx, "use_duration_target"] = st.checkbox("Usar duration alvo", value=bool(st.session_state.positions_df.loc[idx, "use_duration_target"]))
                st.session_state.positions_df.loc[idx, "duration_target"] = st.number_input("Duration alvo (anos)", min_value=0.0, value=float(st.session_state.positions_df.loc[idx, "duration_target"]), step=0.1)
            pos = dataframe_to_positions(st.session_state.positions_df[st.session_state.positions_df["name"] == name])[0]
            row = analyze_portfolio([pos], get_config())[0].iloc[0]
            metric_row([
                ("Preço atual", brl(row["preco_atual"])),
                ("Preço cenário", brl(row["preco_cenario"])),
                ("P&L (R$)", brl(row["ganho_perda_cenario"])),
                ("DV01", brl(row["dv01_r$"])),
                ("Prazo usado", f"{row['prazo_utilizado']:.2f} anos"),
            ])
            st.caption("DV01 = variação aproximada em R$ para choque de +1 bp na taxa.")
            curve = pnl_curve_for_position(pos, max(0.0001, pos.current_rate - 0.04), pos.current_rate + 0.04, 60)
            st.line_chart(curve.set_index("taxa (%)"), height=340)

    with tabs[2]:
        st.subheader("Cenários")
        scenario_controls()
        detail_df, summary = analyze_portfolio(dataframe_to_positions(st.session_state.positions_df), get_config())
        scen = pd.DataFrame([
            {"Cenário": "Otimista", "P&L (R$)": summary["pnl_otimista_total"]},
            {"Cenário": "Base", "P&L (R$)": summary["pnl_base_total"]},
            {"Cenário": "Pessimista", "P&L (R$)": summary["pnl_pessimista_total"]},
            {"Cenário": "Esperado", "P&L (R$)": summary["retorno_esperado_total"]},
        ])
        st.dataframe(scen, use_container_width=True, hide_index=True)
        st.bar_chart(scen.set_index("Cenário"), height=300)

    with tabs[3]:
        st.subheader("Risco")
        detail_df, summary = analyze_portfolio(dataframe_to_positions(st.session_state.positions_df), get_config())
        metric_row([
            ("DV01 carteira", brl(summary["dv01_total"])),
            ("Duration média", f"{summary['duration_media']:.2f}"),
            ("Convexidade média", f"{summary['convexidade_media']:.4f}"),
        ])
        if not detail_df.empty:
            st.dataframe(detail_df[["nome", "tipo", "duration_modificada", "convexidade", "dv01_r$"]], use_container_width=True, hide_index=True)
            st.line_chart(sensitivity_by_shift(st.session_state.positions_df, [-300, -200, -100, -50, 0, 50, 100, 200, 300]).set_index("choque_bp"), height=320)
            st.bar_chart(detail_df.groupby("tipo")[["pnl_otimista", "pnl_base", "pnl_pessimista"]].sum(), height=300)

    with tabs[4]:
        st.subheader("Benchmark")
        detail_df, summary = analyze_portfolio(dataframe_to_positions(st.session_state.positions_df), get_config())
        st.session_state.scenario_config["cdi_esperado"] = st.number_input("CDI esperado (% a.a.)", 0.0, 100.0, float(st.session_state.scenario_config["cdi_esperado"] * 100), 0.1) / 100
        current = summary["valor_atual_total"]
        ret_pct = summary["retorno_esperado_total"] / current if current > 0 else 0.0
        cdi = st.session_state.scenario_config["cdi_esperado"]
        metric_row([
            ("Retorno esperado", pct(ret_pct * 100)),
            ("CDI", pct(cdi * 100)),
            ("Excesso", pct((ret_pct - cdi) * 100)),
        ])
        st.dataframe(pd.DataFrame({"Métrica": ["Retorno esperado", "CDI", "Excesso"], "Valor (%)": [ret_pct * 100, cdi * 100, (ret_pct - cdi) * 100]}), use_container_width=True, hide_index=True)

    with tabs[5]:
        st.subheader("Atualização de FIIs via Yahoo Finance")
        default_tickers = "HGLG11,VISC11,MXRF11,XPLG11"
        tickers_text = st.text_input("Tickers (separados por vírgula)", value=default_tickers)
        tickers = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]
        last_update_key = "yahoo_last_update_utc"

        if st.button("🔄 Atualizar dados do Yahoo Finance", type="primary", use_container_width=True):
            fetch_yahoo_fii_snapshot.clear()
            st.session_state[last_update_key] = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")

        try:
            df_yahoo = fetch_yahoo_fii_snapshot(tickers)
            if df_yahoo.empty:
                st.warning("Nenhum dado retornado para os tickers informados.")
            else:
                if last_update_key in st.session_state:
                    st.caption(f"Última atualização manual: {st.session_state[last_update_key]}")
                st.dataframe(df_yahoo, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Falha ao buscar dados no Yahoo Finance: {exc}")

    st.divider()
    save_restore_controls()


if __name__ == "__main__":
    main()
