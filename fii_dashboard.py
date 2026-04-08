"""Dashboard profissional/didático para FIIs com atualização manual via Yahoo Finance."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st


API_BASE = "http://localhost:8000"
WEIGHTS = {
    "pvp_score": 0.45,
    "fundamental_score": 0.20,
    "income_quality_score": 0.15,
    "risk_liquidity_score": 0.10,
    "relative_score": 0.10,
}


@st.cache_data(ttl=300)
def fetch_yahoo_snapshot(tickers: list[str]) -> pd.DataFrame:
    import yfinance as yf

    rows = []
    for ticker in tickers:
        yf_ticker = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
        history = yf.Ticker(yf_ticker).history(period="6mo", interval="1d")
        if history.empty:
            continue
        close = history["Close"]
        rows.append(
            {
                "ticker": yf_ticker.replace(".SA", ""),
                "preco": float(close.iloc[-1]),
                "retorno_1m": float(close.iloc[-1] / close.iloc[max(0, len(close) - 22)] - 1) if len(close) > 22 else 0.0,
                "retorno_6m": float(close.iloc[-1] / close.iloc[0] - 1),
                "volatilidade": float(close.pct_change().dropna().std() * (252**0.5)),
                "liquidez_media": float(history["Volume"].tail(21).mean()),
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(ttl=120)
def fetch_api_ranking(page_size: int = 200) -> pd.DataFrame:
    """Lê /rankings/daily aceitando respostas em formato paginado ou lista."""
    try:
        payload = requests.get(f"{API_BASE}/rankings/daily?page=1&page_size={page_size}", timeout=10).json()
        if isinstance(payload, dict):
            items = payload.get("items", [])
        elif isinstance(payload, list):
            items = payload
        else:
            items = []
        if not items:
            return pd.DataFrame()
        return pd.DataFrame(items)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=120)
def fetch_by_sector() -> dict:
    try:
        resp = requests.get(f"{API_BASE}/rankings/by-sector", timeout=10)
        if resp.status_code != 200:
            return {}
        return resp.json()
    except Exception:
        return {}


def render_weight_cards() -> None:
    st.subheader("🎯 Distribuição obrigatória de pesos (score final)")
    cols = st.columns(5)
    cards = [
        ("Valuation P/VP", "45%", "Eixo dominante do modelo"),
        ("Fundamentos", "20%", "Vacância, alavancagem, inadimplência etc."),
        ("Rendimentos", "15%", "Qualidade e estabilidade da renda"),
        ("Liquidez & Risco", "10%", "Liquidez média, volatilidade e drawdown"),
        ("Relativo", "10%", "Comparação contra setor / benchmark"),
    ]
    for col, (label, value, note) in zip(cols, cards):
        col.metric(label, value)
        col.caption(note)


def enrich_contributions(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    for component, weight in WEIGHTS.items():
        out_name = component.replace("_score", "_contrib")
        enriched[out_name] = enriched[component] * weight
    contribution_cols = [c for c in enriched.columns if c.endswith("_contrib")]
    enriched["total_rebuild"] = enriched[contribution_cols].sum(axis=1)
    return enriched


def render_score_breakdown(df: pd.DataFrame) -> None:
    st.subheader("📊 Decomposição do score por componente")
    if df.empty:
        st.info("Sem dados de score para decomposição.")
        return

    top_n = st.slider("Quantidade de FIIs no gráfico", min_value=5, max_value=min(30, len(df)), value=min(10, len(df)))
    top = df.sort_values("total_score", ascending=False).head(top_n).copy()
    contrib_cols = [
        "pvp_contrib",
        "fundamental_contrib",
        "income_quality_contrib",
        "risk_liquidity_contrib",
        "relative_contrib",
    ]
    chart = top.set_index("ticker")[contrib_cols]
    st.bar_chart(chart, height=360)

    detail_cols = [
        "ticker",
        "total_score",
        "classification",
        "pvp_score",
        "fundamental_score",
        "income_quality_score",
        "risk_liquidity_score",
        "relative_score",
    ]
    st.dataframe(top[detail_cols], use_container_width=True, hide_index=True)


def render_sector_panel(by_sector: dict) -> None:
    st.subheader("🏭 Ranking por setor")
    if not by_sector:
        st.info("Endpoint por setor vazio ou indisponível.")
        return

    rows = []
    for sector, items in by_sector.items():
        if not items:
            continue
        scores = [i["score"] for i in items]
        rows.append(
            {
                "setor": sector,
                "qtd_fiis": len(items),
                "score_medio": sum(scores) / len(scores),
                "melhor_ticker": items[0]["ticker"],
                "melhor_score": items[0]["score"],
            }
        )
    if not rows:
        st.info("Sem dados setoriais para mostrar.")
        return

    df_sector = pd.DataFrame(rows).sort_values("score_medio", ascending=False)
    st.dataframe(df_sector, use_container_width=True, hide_index=True)
    st.bar_chart(df_sector.set_index("setor")["score_medio"], height=280)


def main() -> None:
    st.set_page_config(page_title="FII Assimetria Dashboard", page_icon="🏢", layout="wide")
    st.title("🏢 Dashboard Profissional de FIIs - Assimetrias por P/VP")
    st.caption("Visão executiva + didática, com peso dominante de P/VP e atualização manual no Yahoo Finance.")

    with st.expander("📘 Leitura didática", expanded=False):
        st.markdown(
            """
            - O score final vai de **0 a 100**.
            - O componente de **P/VP pesa 45%** e domina a priorização.
            - Desconto de P/VP sem fundamento costuma virar **value trap**.
            - Use a decomposição para enxergar *por que* um ticker ficou no topo.
            """
        )

    render_weight_cards()
    st.divider()

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        tickers_text = st.text_input("Tickers Yahoo", value="HGLG11,VISC11,MXRF11,XPLG11,KNCR11")
    with c2:
        run_job = st.button("▶️ Rodar job diário", use_container_width=True)
    with c3:
        refresh = st.button("🔄 Atualizar Yahoo", type="primary", use_container_width=True)

    if run_job:
        try:
            response = requests.post(f"{API_BASE}/jobs/run-daily", timeout=30)
            fetch_api_ranking.clear()
            fetch_by_sector.clear()
            st.success(f"Job acionado: {response.json()}")
        except Exception as exc:
            st.error(f"Não foi possível acionar a API: {exc}")

    if refresh:
        fetch_yahoo_snapshot.clear()
        st.session_state["last_refresh"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if "last_refresh" in st.session_state:
        st.caption(f"Última atualização manual do Yahoo: {st.session_state['last_refresh']}")

    tickers = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]
    df_yahoo = fetch_yahoo_snapshot(tickers)

    st.subheader("💹 Monitor de mercado (Yahoo Finance)")
    if not df_yahoo.empty:
        cols = st.columns(4)
        cols[0].metric("Preço médio", f"R$ {df_yahoo['preco'].mean():.2f}")
        cols[1].metric("Retorno médio 1m", f"{df_yahoo['retorno_1m'].mean() * 100:.2f}%")
        cols[2].metric("Retorno médio 6m", f"{df_yahoo['retorno_6m'].mean() * 100:.2f}%")
        cols[3].metric("Volatilidade média", f"{df_yahoo['volatilidade'].mean() * 100:.2f}%")

        st.bar_chart((df_yahoo.set_index("ticker")[["retorno_1m", "retorno_6m"]] * 100), height=260)
        st.dataframe(df_yahoo.sort_values("retorno_6m", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.warning("Sem dados do Yahoo para os tickers selecionados.")

    st.divider()
    ranking_df = fetch_api_ranking()
    if ranking_df.empty:
        st.info("Sem ranking na API. Execute o job diário para popular o banco.")
        return

    st.subheader("🏆 Ranking diário (API)")

    # Compatível com payload mínimo (ticker/price/ret_1m/ret_6m/vol/score)
    base_cols = ["ticker", "price", "ret_1m", "ret_6m", "vol", "score"]
    available_base = [c for c in base_cols if c in ranking_df.columns]
    if "score" in ranking_df.columns:
        ranking_df = ranking_df.sort_values("score", ascending=False)

    st.dataframe(ranking_df[available_base] if available_base else ranking_df, use_container_width=True, hide_index=True)

    # Se a API avançada estiver disponível, exibe decomposição e painel setorial.
    if set(WEIGHTS.keys()).issubset(set(ranking_df.columns)) and "total_score" in ranking_df.columns:
        enriched = enrich_contributions(ranking_df)
        render_score_breakdown(enriched)
        render_sector_panel(fetch_by_sector())


if __name__ == "__main__":
    main()
