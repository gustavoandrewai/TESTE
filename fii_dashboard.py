"""Dashboard profissional/didático para FIIs com atualização manual via Yahoo Finance."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st


API_BASE = "http://localhost:8000"


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


def fetch_api_ranking() -> pd.DataFrame:
    try:
        data = requests.get(f"{API_BASE}/rankings/daily?page=1&page_size=50", timeout=10).json()
        return pd.DataFrame(data.get("items", []))
    except Exception:
        return pd.DataFrame()


def main() -> None:
    st.set_page_config(page_title="FII Assimetria Dashboard", page_icon="🏢", layout="wide")
    st.title("🏢 Dashboard de FIIs - Assimetrias por P/VP")
    st.caption("Painel profissional e didático com Yahoo Finance + ranking da API FastAPI.")

    with st.expander("📘 Como ler este dashboard (didático)", expanded=False):
        st.markdown(
            """
            - **P/VP é o benchmark principal**: descontos podem indicar assimetria.
            - **Confirme fundamentos**: desconto com deterioração pode ser *value trap*.
            - **Retorno e volatilidade** ajudam a contextualizar risco x oportunidade.
            """
        )

    c1, c2 = st.columns([3, 1])
    with c1:
        tickers_text = st.text_input("Tickers", value="HGLG11,VISC11,MXRF11,XPLG11,KNCR11")
    with c2:
        run_job = st.button("▶️ Rodar job diário", use_container_width=True)

    if run_job:
        try:
            response = requests.post(f"{API_BASE}/jobs/run-daily", timeout=30)
            st.success(f"Job acionado: {response.json()}")
        except Exception as exc:
            st.error(f"Não foi possível acionar a API: {exc}")

    if st.button("🔄 Atualizar informações do Yahoo", type="primary", use_container_width=True):
        fetch_yahoo_snapshot.clear()
        st.session_state["last_refresh"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    tickers = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]
    df_yahoo = fetch_yahoo_snapshot(tickers)
    if "last_refresh" in st.session_state:
        st.caption(f"Última atualização manual: {st.session_state['last_refresh']}")

    if not df_yahoo.empty:
        cols = st.columns(4)
        cols[0].metric("Preço médio", f"R$ {df_yahoo['preco'].mean():.2f}")
        cols[1].metric("Retorno médio 1m", f"{df_yahoo['retorno_1m'].mean() * 100:.2f}%")
        cols[2].metric("Retorno médio 6m", f"{df_yahoo['retorno_6m'].mean() * 100:.2f}%")
        cols[3].metric("Volatilidade média", f"{df_yahoo['volatilidade'].mean() * 100:.2f}%")

        chart_df = df_yahoo.set_index("ticker")[["retorno_1m", "retorno_6m"]] * 100
        st.bar_chart(chart_df, height=280)
        st.dataframe(df_yahoo, use_container_width=True, hide_index=True)

    st.subheader("Ranking diário da API")
    ranking_df = fetch_api_ranking()
    if ranking_df.empty:
        st.info("Sem ranking disponível. Rode o job diário para preencher a base.")
    else:
        st.dataframe(
            ranking_df.sort_values("total_score", ascending=False),
            use_container_width=True,
            hide_index=True,
        )


if __name__ == "__main__":
    main()
