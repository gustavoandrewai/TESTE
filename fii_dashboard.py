"""Dashboard profissional/didático para FIIs com foco em P/VP e fundamentos."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st


API_BASE = "http://localhost:8000"


@st.cache_data(ttl=5)
def fetch_rankings(page_size: int = 2000) -> pd.DataFrame:
    try:
        payload = requests.get(f"{API_BASE}/rankings/daily?page=1&page_size={page_size}", timeout=20).json()
        return pd.DataFrame(payload.get("items", []))
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


def parse_tickers_text(tickers_text: str) -> list[str]:
    raw = tickers_text.replace("\n", ",")
    values = [v.strip().upper() for v in raw.split(",") if v.strip()]
    unique = []
    seen = set()
    for v in values:
        if v not in seen:
            seen.add(v)
            unique.append(v)
    return unique


def run_daily_job_with_tickers(tickers_text: str) -> dict:
    tickers = parse_tickers_text(tickers_text)
    try:
        response = requests.post(f"{API_BASE}/jobs/run-daily", json={"tickers": tickers}, timeout=120)
        payload = response.json()
        st.session_state["last_submitted_tickers"] = tickers
        st.session_state["last_job_payload"] = payload
        fetch_rankings.clear()
        fetch_top_by_sector.clear()
        fetch_job_status.clear()
        return payload
    except Exception as exc:
        return {"status": "error", "message": str(exc), "tickers": tickers}


def render_job_trace(status: dict) -> None:
    st.write("**Rastreabilidade da execução**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Recebidos", status.get("tickers_received_count", 0))
    c2.metric("Válidos", status.get("tickers_valid_count", 0))
    c3.metric("Processados", status.get("processed_count", 0))
    c4.metric("Falharam", status.get("failed_count", 0))

    if status.get("tickers_failed"):
        st.warning("Tickers com falha e motivo:")
        failure_df = pd.DataFrame([{"ticker": k, "motivo": v} for k, v in status["tickers_failed"].items()])
        st.dataframe(failure_df, use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="FII Dashboard", page_icon="🏢", layout="wide")
    st.title("🏢 Dashboard de FIIs - P/VP + Fundamentais")

    tabs = st.tabs(["Visão geral", "Benchmarks por ticker", "Ranking diário da API", "Top 5 por setor"])

    with tabs[0]:
        st.subheader("Visão geral")
        tickers_text = st.text_area(
            "Tickers (vírgula ou quebra de linha)",
            value="HGLG11,XPLG11,XPML11,VISC11,KNCR11,MXRF11,HGRE11",
            height=140,
        )

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

        st.write("**Tickers enviados no último job**")
        st.code(", ".join(st.session_state.get("last_submitted_tickers", parse_tickers_text(tickers_text))) or "(vazio)")

        status = fetch_job_status()
        st.write("**Status do último job**")
        st.json(status if status else st.session_state.get("last_job_payload", {"status": "idle"}))
        render_job_trace(status if status else {})

        df = fetch_rankings()
        k1, k2, k3 = st.columns(3)
        k1.metric("Tickers no ranking", len(df))
        k2.metric("Score total médio", f"{df['score_total'].mean():.1f}" if (not df.empty and 'score_total' in df.columns) else "-")
        k3.metric("P/VP médio", f"{df['pvp'].mean():.2f}" if (not df.empty and 'pvp' in df.columns) else "-")

    with tabs[1]:
        st.subheader("Benchmarks por ticker")
        df = fetch_rankings()
        if df.empty:
            st.info("Sem dados. Rode o job diário primeiro.")
        else:
            cols = [
                "ticker", "setor", "subsetor", "preco", "pvp", "pvp_setor_mediana", "pvp_desconto_setor",
                "dy_12m", "dy_setor_mediana", "dy_spread_setor", "vacancia", "inadimplencia", "alavancagem",
                "estabilidade_rendimentos", "score_pvp", "score_fundamental", "score_renda", "score_risco", "score_total", "classificacao",
            ]
            available = [c for c in cols if c in df.columns]
            selected = st.multiselect("Colunas", available, default=available)
            st.dataframe(df[selected if selected else available], use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("Ranking diário da API")
        df = fetch_rankings()
        if df.empty:
            st.info("Sem ranking disponível.")
        else:
            if "score_total" in df.columns:
                df = df.sort_values("score_total", ascending=False)
            selectable = df.columns.tolist()
            default = [c for c in ["ticker", "setor", "score_pvp", "score_fundamental", "score_renda", "score_risco", "score_momentum", "score_total", "classificacao"] if c in selectable]
            choose = st.multiselect("Selecionar colunas", selectable, default=default)
            st.dataframe(df[choose if choose else selectable], use_container_width=True, hide_index=True)

    with tabs[3]:
        st.subheader("Top 5 por setor")
        ranking = fetch_rankings()
        sectors = sorted(ranking["setor"].dropna().unique().tolist()) if (not ranking.empty and "setor" in ranking.columns) else []
        c1, c2 = st.columns(2)
        sector = c1.selectbox("Filtrar setor", ["todos"] + sectors)
        only_positive = c2.checkbox("Somente assimetria_positiva", value=False)

        top_df = fetch_top_by_sector(only_positive=only_positive, sector=None if sector == "todos" else sector)
        if top_df.empty:
            st.info("Sem dados para Top 5 por setor.")
        else:
            cols = ["ticker", "setor", "pvp", "pvp_desconto_setor", "dy_12m", "vacancia", "inadimplencia", "alavancagem", "score_pvp", "score_fundamental", "score_total", "classificacao"]
            cols = [c for c in cols if c in top_df.columns]
            st.dataframe(top_df[cols], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
