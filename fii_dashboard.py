"""Dashboard profissional/didático para FIIs com foco em P/VP e fundamentos."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st


API_BASE = "http://localhost:8000"


@st.cache_data(ttl=5)
def fetch_rankings(page_size: int = 500) -> pd.DataFrame:
    try:
        payload = requests.get(f"{API_BASE}/rankings/daily?page=1&page_size={page_size}", timeout=10).json()
        return pd.DataFrame(payload.get("items", [])) if isinstance(payload, dict) else pd.DataFrame(payload)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=5)
def fetch_job_status() -> dict:
    try:
        return requests.get(f"{API_BASE}/jobs/status", timeout=10).json()
    except Exception:
        return {}


@st.cache_data(ttl=5)
def fetch_top_by_sector(only_positive: bool = False, sector: str | None = None) -> pd.DataFrame:
    params = {"only_positive": only_positive}
    if sector:
        params["sector"] = sector
    try:
        payload = requests.get(f"{API_BASE}/rankings/top-by-sector", params=params, timeout=10).json()
        return pd.DataFrame(payload.get("items", []))
    except Exception:
        return pd.DataFrame()


def run_daily_job_with_tickers(tickers_text: str) -> dict:
    tickers = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]
    try:
        response = requests.post(f"{API_BASE}/jobs/run-daily", params={"tickers": ",".join(tickers)}, timeout=90)
        payload = response.json()
        st.session_state["last_submitted_tickers"] = tickers
        st.session_state["last_job_payload"] = payload
        fetch_rankings.clear()
        fetch_top_by_sector.clear()
        fetch_job_status.clear()
        return payload
    except Exception as exc:
        return {"status": "error", "message": str(exc), "tickers": tickers}


def kpis(df: pd.DataFrame) -> None:
    cols = st.columns(5)
    cols[0].metric("Tickers", int(len(df)))
    cols[1].metric("Score médio", f"{df['score_total'].mean():.1f}" if "score_total" in df.columns and not df.empty else "-")
    cols[2].metric("P/VP médio", f"{df['pvp'].mean():.2f}" if "pvp" in df.columns and not df.empty else "-")
    cols[3].metric("DY 12m médio", f"{df['dy_12m'].mean() * 100:.2f}%" if "dy_12m" in df.columns and not df.empty else "-")
    cols[4].metric("Assimetria positiva", int((df.get("classificacao") == "assimetria_positiva").sum()) if not df.empty else 0)


def main() -> None:
    st.set_page_config(page_title="FII Dashboard", page_icon="🏢", layout="wide")
    st.title("🏢 Dashboard de FIIs - P/VP + Fundamentais")

    tabs = st.tabs(["Visão geral", "Benchmarks por ticker", "Ranking diário da API", "Top 5 por setor"])

    with tabs[0]:
        st.subheader("Visão geral")
        tickers_text = st.text_input("Tickers (separados por vírgula)", value="HGLG11,XPLG11,XPML11,VISC11,KNCR11,MXRF11,HGRE11")

        c1, c2 = st.columns([1, 1])
        if c1.button("▶️ Rodar job diário", use_container_width=True):
            payload = run_daily_job_with_tickers(tickers_text)
            if payload.get("status") == "success":
                st.success("Job executado com sucesso.")
            else:
                st.error(f"Falha no job: {payload}")

        if c2.button("🔄 Atualizar painel", use_container_width=True):
            fetch_rankings.clear()
            fetch_top_by_sector.clear()
            fetch_job_status.clear()
            st.session_state["last_refresh"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        if "last_refresh" in st.session_state:
            st.caption(f"Último refresh manual: {st.session_state['last_refresh']}")

        st.write("**Tickers enviados no último job**")
        st.code(", ".join(st.session_state.get("last_submitted_tickers", [t.strip().upper() for t in tickers_text.split(",") if t.strip()])))

        st.write("**Status do último job**")
        job_status = fetch_job_status()
        st.json(job_status if job_status else st.session_state.get("last_job_payload", {"status": "idle"}))

        df = fetch_rankings()
        kpis(df)

    with tabs[1]:
        st.subheader("Benchmarks por ticker")
        df = fetch_rankings()
        if df.empty:
            st.info("Sem dados. Rode o job diário primeiro.")
        else:
            benchmark_cols = [
                "ticker", "setor", "subsetor", "preco", "pvp", "pvp_setor_mediana", "pvp_desconto_setor", "pvp_zscore_historico",
                "dy_12m", "dy_setor_mediana", "dy_spread_setor", "vacancia", "inadimplencia", "alavancagem", "estabilidade_rendimentos",
                "score_pvp", "score_fundamental", "score_renda", "score_risco", "score_total", "classificacao",
            ]
            available = [c for c in benchmark_cols if c in df.columns]
            default = [c for c in ["ticker", "setor", "subsetor", "pvp", "pvp_desconto_setor", "dy_12m", "vacancia", "inadimplencia", "alavancagem", "score_pvp", "score_fundamental", "score_total", "classificacao"] if c in available]
            selected = st.multiselect("Colunas", available, default=default)
            view_cols = selected if selected else available
            st.dataframe(df[view_cols], use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("Ranking diário da API")
        df = fetch_rankings()
        if df.empty:
            st.info("Sem ranking disponível.")
        else:
            if "score_total" in df.columns:
                df = df.sort_values("score_total", ascending=False)
            selectable = df.columns.tolist()
            prefer = [c for c in ["ticker", "setor", "score_pvp", "score_fundamental", "score_renda", "score_risco", "score_momentum", "score_total", "classificacao"] if c in selectable]
            chosen = st.multiselect("Selecionar colunas do ranking", selectable, default=prefer)
            st.dataframe(df[chosen if chosen else selectable], use_container_width=True, hide_index=True)

    with tabs[3]:
        st.subheader("Top 5 por setor")
        df_all = fetch_rankings()
        sector_options = sorted(df_all["setor"].dropna().unique().tolist()) if not df_all.empty and "setor" in df_all.columns else []

        c1, c2 = st.columns(2)
        selected_sector = c1.selectbox("Filtrar setor", options=["todos"] + sector_options)
        only_pos = c2.checkbox("Mostrar apenas assimetria_positiva", value=False)

        sector_param = None if selected_sector == "todos" else selected_sector
        top_df = fetch_top_by_sector(only_positive=only_pos, sector=sector_param)
        if top_df.empty:
            st.info("Sem dados para Top 5 por setor.")
        else:
            cols = [
                "ticker", "setor", "pvp", "pvp_desconto_setor", "dy_12m", "vacancia", "inadimplencia", "alavancagem",
                "score_pvp", "score_fundamental", "score_total", "classificacao",
            ]
            cols = [c for c in cols if c in top_df.columns]
            st.dataframe(top_df[cols], use_container_width=True, hide_index=True)

            if "classificacao" in top_df.columns:
                st.caption("Destaque visual: assimetria_positiva em verde.")
                styled = top_df[cols].style.apply(
                    lambda row: ["background-color: #d1fae5" if row.get("classificacao") == "assimetria_positiva" else "" for _ in row],
                    axis=1,
                )
                st.dataframe(styled, use_container_width=True)


if __name__ == "__main__":
    main()
