"""Dashboard profissional/didático para FIIs com foco em P/VP e fundamentos."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st


API_BASE = "http://localhost:8000"
SECTOR_LABELS = {
    "logistica": "🚚 Logística",
    "shopping": "🏢 Shopping",
    "lajes_corporativas": "🏬 Lajes Corporativas",
    "renda_urbana": "🏙️ Renda Urbana",
    "recebiveis_high_grade": "💳 Recebíveis High Grade",
    "recebiveis_high_yield": "💳 Recebíveis High Yield",
    "fof": "🧺 FoF",
    "hibridos": "🔀 Híbridos",
    "desenvolvimento": "🏗️ Desenvolvimento",
    "outros": "📦 Outros",
}


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


def normalize_sector_col(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "setor" not in out.columns:
        out["setor"] = "outros"
    out["setor"] = out["setor"].fillna("outros").astype(str).str.strip().str.lower()
    out["setor"] = out["setor"].replace({"": "outros", "fundo_de_fundos": "fof", "FoF": "fof"})
    return out


def generate_tese(row: pd.Series) -> str:
    frases = []

    if row.get("pvp", 1.0) < row.get("pvp_setor_mediana", 1.0):
        frases.append("negocia com desconto frente à mediana do setor")

    fundamentals_bad = (row.get("vacancia", 0) > 0.12) or (row.get("inadimplencia", 0) > 0.05) or (row.get("alavancagem", 0) > 0.25)
    if row.get("pvp_desconto_setor", 0) > 0.15 and fundamentals_bad:
        frases.append("desconto relevante com risco de value trap")

    if row.get("dy_12m", 0) > row.get("dy_setor_mediana", 0) and row.get("vacancia", 1) < 0.08:
        frases.append("boa geração de renda com vacância controlada")

    if row.get("alavancagem", 0) > 0.22:
        frases.append("alavancagem elevada exige monitoramento")

    if row.get("score_total", 0) >= 70:
        frases.append("assimetria positiva para acompanhamento prioritário")
    elif row.get("score_total", 0) >= 55:
        frases.append("assimetria moderada com potencial seletivo")
    else:
        frases.append("caso neutro, depende de gatilho de melhora")

    return "; ".join(frases).capitalize() + "."


def run_daily_job_with_tickers(tickers_text: str) -> dict:
    tickers = parse_tickers_text(tickers_text)
    try:
        response = requests.post(f"{API_BASE}/jobs/run-daily", json={"tickers": tickers}, timeout=120)
        payload = response.json()
        st.session_state["last_submitted_tickers"] = tickers
        st.session_state["last_job_payload"] = payload
        fetch_rankings.clear()
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
        failure_df = pd.DataFrame([{"ticker": k, "motivo": v} for k, v in status["tickers_failed"].items()])
        st.warning("Tickers com falha e motivo:")
        st.dataframe(failure_df, use_container_width=True, hide_index=True)


def top5_by_sector(df: pd.DataFrame) -> pd.DataFrame:
    # Correção obrigatória: Top 5 aplicado dentro de cada setor, nunca global.
    grouped = (
        df.groupby("setor", group_keys=False)
        .apply(lambda x: x.sort_values("score_total", ascending=False).head(5))
        .reset_index(drop=True)
    )
    return grouped


def render_ticker_card(row: pd.Series) -> None:
    with st.container(border=True):
        c1, c2, c3 = st.columns([1.4, 1, 1])
        c1.markdown(f"**{row['ticker']}**")
        c1.caption(row.get("classificacao", "neutro"))
        c2.metric("P/VP", f"{row.get('pvp', 0):.2f}")
        c3.metric("Score", f"{row.get('score_total', 0):.1f}")

        d1, d2, d3 = st.columns(3)
        d1.metric("DY 12m", f"{row.get('dy_12m', 0) * 100:.2f}%")
        d2.metric("Vacância", f"{row.get('vacancia', 0) * 100:.1f}%")
        d3.metric("Alavancagem", f"{row.get('alavancagem', 0) * 100:.1f}%")

        st.markdown(f"**🧠 Tese:** {generate_tese(row)}")


def main() -> None:
    st.set_page_config(page_title="FII Dashboard", page_icon="🏢", layout="wide")
    st.title("🏢 Dashboard de FIIs - P/VP + Fundamentais")

    tabs = st.tabs(["Visão geral", "Benchmarks por ticker", "Ranking diário da API", "Top 5 por setor"])

    with tabs[0]:
        st.subheader("Visão geral")
        tickers_text = st.text_area("Tickers (vírgula ou quebra de linha)", value="HGLG11,XPLG11,XPML11,VISC11,KNCR11,MXRF11,HGRE11", height=140)

        c1, c2 = st.columns([1, 1])
        if c1.button("▶️ Rodar job diário", use_container_width=True):
            payload = run_daily_job_with_tickers(tickers_text)
            if payload.get("status") == "success":
                st.success("Job executado com sucesso.")
            else:
                st.error(f"Falha no job: {payload}")

        if c2.button("🔄 Atualizar painel", use_container_width=True):
            fetch_rankings.clear()
            fetch_job_status.clear()
            st.session_state["last_refresh"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        st.write("**Tickers enviados no último job**")
        st.code(", ".join(st.session_state.get("last_submitted_tickers", parse_tickers_text(tickers_text))) or "(vazio)")

        status = fetch_job_status()
        st.write("**Status do último job**")
        st.json(status if status else st.session_state.get("last_job_payload", {"status": "idle"}))
        render_job_trace(status if status else {})

    with tabs[1]:
        st.subheader("Benchmarks por ticker")
        df = normalize_sector_col(fetch_rankings())
        if df.empty:
            st.info("Sem dados. Rode o job diário primeiro.")
        else:
            cols = [
                "ticker", "setor", "subsetor", "preco", "pvp", "pvp_setor_mediana", "pvp_desconto_setor", "dy_12m", "dy_setor_mediana", "dy_spread_setor", "vacancia", "inadimplencia", "alavancagem", "estabilidade_rendimentos", "score_pvp", "score_fundamental", "score_renda", "score_risco", "score_total", "classificacao",
            ]
            available = [c for c in cols if c in df.columns]
            selected = st.multiselect("Colunas", available, default=available)
            st.dataframe(df[selected if selected else available], use_container_width=True, hide_index=True)

    with tabs[2]:
        st.subheader("Ranking diário da API")
        df = normalize_sector_col(fetch_rankings())
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
        ranking = normalize_sector_col(fetch_rankings())
        status = fetch_job_status()

        if ranking.empty:
            st.info("Sem ranking disponível para montar Top 5 por setor.")
            return

        c1, c2, c3 = st.columns(3)
        sectors = sorted(ranking["setor"].unique().tolist())
        selected_sector = c1.selectbox("Filtro opcional por setor", ["todos"] + sectors)
        only_positive = c2.checkbox("Somente assimetria_positiva", value=False)
        min_score = c3.slider("Score mínimo", min_value=0.0, max_value=100.0, value=0.0, step=1.0)

        mode = st.radio("Visualização", options=["Modo executivo", "Modo tabela"], horizontal=True)

        work = ranking.copy()
        if only_positive and "classificacao" in work.columns:
            work = work[work["classificacao"] == "assimetria_positiva"]
        work = work[work["score_total"] >= min_score]
        if selected_sector != "todos":
            work = work[work["setor"] == selected_sector]

        grouped_top5 = top5_by_sector(work)
        total_by_sector = work.groupby("setor")["ticker"].count().to_dict()

        # Renderiza TODOS setores ao mesmo tempo por padrão.
        for setor in sorted(grouped_top5["setor"].unique().tolist()):
            block = grouped_top5[grouped_top5["setor"] == setor].copy()
            total_setor = int(total_by_sector.get(setor, len(block)))
            title = f"{SECTOR_LABELS.get(setor, setor.title())} (Top {len(block)} de {total_setor})"
            with st.expander(title, expanded=True):
                if mode == "Modo tabela":
                    cols = ["ticker", "setor", "pvp", "pvp_desconto_setor", "dy_12m", "vacancia", "inadimplencia", "alavancagem", "score_pvp", "score_fundamental", "score_total", "classificacao"]
                    cols = [c for c in cols if c in block.columns]
                    st.dataframe(block[cols], use_container_width=True, hide_index=True)
                else:
                    for _, row in block.iterrows():
                        render_ticker_card(row)

        st.divider()
        st.subheader("Diagnóstico de tickers ausentes")
        enviados = status.get("tickers_received", []) if isinstance(status, dict) else []
        processados = status.get("tickers_processed", []) if isinstance(status, dict) else ranking.get("ticker", pd.Series()).tolist()
        failed_map = status.get("tickers_failed", {}) if isinstance(status, dict) else {}

        enviados_set = set(enviados)
        processados_set = set(processados)
        ranking_set = set(ranking["ticker"].tolist()) if "ticker" in ranking.columns else set()
        sem_setor = ranking[ranking["setor"].isna() | (ranking["setor"].astype(str).str.strip() == "")]["ticker"].tolist()
        ausentes = sorted(enviados_set - ranking_set)

        d1, d2, d3, d4, d5 = st.columns(5)
        d1.metric("Enviados", len(enviados_set))
        d2.metric("Processados", len(processados_set))
        d3.metric("Com setor atribuído", int(len(ranking_set) - len(set(sem_setor))))
        d4.metric("Falharam", len(failed_map))
        d5.metric("Sem setor", len(set(sem_setor)))

        if ausentes:
            rows = [{"ticker": tkr, "motivo": failed_map.get(tkr, "nao_encontrado_no_ranking")} for tkr in ausentes]
            st.write("**Tickers ausentes no ranking**")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
