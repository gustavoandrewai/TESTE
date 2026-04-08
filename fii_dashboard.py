"""Dashboard profissional/didático para FIIs com foco em P/VP e fundamentos."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


API_BASE = "http://localhost:8000"
OVERRIDES_FILE = Path("sector_overrides.csv")
SECTORS = [
    "logistica",
    "shopping",
    "lajes_corporativas",
    "renda_urbana",
    "recebiveis_high_grade",
    "recebiveis_high_yield",
    "fof",
    "hibridos",
    "desenvolvimento",
    "outros",
]
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
    if "subsetor" not in out.columns:
        out["subsetor"] = "na"
    out["setor"] = out["setor"].fillna("outros").astype(str).str.strip().str.lower().replace({"": "outros", "fundo_de_fundos": "fof", "FoF": "fof"})
    out["subsetor"] = out["subsetor"].fillna("na")
    return out


def load_overrides() -> pd.DataFrame:
    if not OVERRIDES_FILE.exists():
        return pd.DataFrame(columns=["ticker", "setor", "subsetor", "updated_at"])
    return pd.read_csv(OVERRIDES_FILE)


def save_override(ticker: str, setor: str, subsetor: str) -> None:
    df = load_overrides()
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_row = pd.DataFrame([{"ticker": ticker, "setor": setor, "subsetor": subsetor or "na", "updated_at": updated_at}])
    df = df[df["ticker"] != ticker]
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(OVERRIDES_FILE, index=False)


def generate_tese(row: pd.Series) -> str:
    frases = []
    if row.get("pvp", 1.0) < row.get("pvp_setor_mediana", 1.0):
        frases.append("negocia com desconto frente à mediana do setor")
    if row.get("pvp_desconto_setor", 0) > 0.15 and ((row.get("vacancia", 0) > 0.12) or (row.get("inadimplencia", 0) > 0.05)):
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


def ensure_top5_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    warnings = []
    out = df.copy()
    if "setor" not in out.columns:
        out["setor"] = "outros"
        warnings.append("Coluna setor ausente no ranking; usando 'outros' como fallback.")
    if "subsetor" not in out.columns:
        out["subsetor"] = "na"
        warnings.append("Coluna subsetor ausente no ranking; usando 'na' como fallback.")
    if "score_total" not in out.columns and "score" in out.columns:
        out["score_total"] = out["score"]
        warnings.append("score_total ausente; usando coluna 'score' como fallback.")
    out = normalize_sector_col(out)
    return out, warnings


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
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Recebidos", status.get("tickers_received_count", 0))
    c2.metric("Válidos", status.get("tickers_valid_count", 0))
    c3.metric("Processados", status.get("processed_count", 0))
    c4.metric("Falharam", status.get("failed_count", 0))


def top5_by_sector(df: pd.DataFrame) -> pd.DataFrame:
    """Top 5 por setor preservando coluna `setor` no resultado final."""
    work = df.copy()
    if "setor" not in work.columns:
        # caso `setor` tenha virado índice em alguma etapa
        if getattr(work.index, "name", None) == "setor":
            work = work.reset_index()
        else:
            work["setor"] = "outros"

    work["setor"] = work["setor"].fillna("outros").astype(str)
    grouped = (
        work.sort_values(["setor", "score_total"], ascending=[True, False])
        .groupby("setor", as_index=False)
        .head(5)
        .reset_index(drop=True)
    )

    # defesa final para não quebrar a UI
    if "setor" not in grouped.columns:
        if getattr(grouped.index, "name", None) == "setor":
            grouped = grouped.reset_index()
        else:
            grouped["setor"] = "outros"
    return grouped


def render_ticker_card(row: pd.Series) -> None:
    with st.container(border=True):
        c1, c2, c3 = st.columns([1.4, 1, 1])
        c1.markdown(f"**{row['ticker']}**")
        c1.caption(row.get("classificacao", "neutro"))
        c2.metric("P/VP", f"{row.get('pvp', 0):.2f}")
        c3.metric("Score", f"{row.get('score_total', 0):.1f}")
        st.markdown(f"**🧠 Tese:** {generate_tese(row)}")


def main() -> None:
    st.set_page_config(page_title="FII Dashboard", page_icon="🏢", layout="wide")
    st.title("🏢 Dashboard de FIIs - P/VP + Fundamentais")

    tabs = st.tabs(["Visão geral", "Benchmarks por ticker", "Ranking diário da API", "Top 5 por setor"])

    with tabs[0]:
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

        status = fetch_job_status()
        st.json(status if status else st.session_state.get("last_job_payload", {"status": "idle"}))
        render_job_trace(status if status else {})

        st.subheader("Correção manual de setor")
        ranking = normalize_sector_col(fetch_rankings())
        if ranking.empty:
            st.info("Sem dados no ranking para editar setor.")
        else:
            ticker = st.selectbox("Ticker", options=sorted(ranking["ticker"].dropna().unique().tolist()))
            current = ranking.loc[ranking["ticker"] == ticker, "setor"].iloc[0] if (ranking["ticker"] == ticker).any() else "outros"
            new_sector = st.selectbox("Novo setor", options=SECTORS, index=SECTORS.index(current) if current in SECTORS else SECTORS.index("outros"))
            new_subsetor = st.text_input("Subsetor (opcional)", value="na")
            if st.button("Salvar override de setor"):
                save_override(ticker, new_sector, new_subsetor)
                st.success("Override salvo em sector_overrides.csv. Rode o job novamente para aplicar.")

            ov = load_overrides()
            if not ov.empty:
                st.caption(f"Overrides manuais ativos: {len(ov)}")
                st.dataframe(ov.sort_values("updated_at", ascending=False), use_container_width=True, hide_index=True)

    with tabs[1]:
        df = normalize_sector_col(fetch_rankings())
        if df.empty:
            st.info("Sem dados. Rode o job diário primeiro.")
        else:
            cols = ["ticker", "setor", "subsetor", "preco", "pvp", "pvp_setor_mediana", "pvp_desconto_setor", "dy_12m", "dy_setor_mediana", "dy_spread_setor", "vacancia", "inadimplencia", "alavancagem", "estabilidade_rendimentos", "score_pvp", "score_fundamental", "score_renda", "score_risco", "score_total", "classificacao"]
            cols = [c for c in cols if c in df.columns]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)

    with tabs[2]:
        df = normalize_sector_col(fetch_rankings())
        if df.empty:
            st.info("Sem ranking disponível.")
        else:
            st.dataframe(df.sort_values("score_total", ascending=False), use_container_width=True, hide_index=True)

    with tabs[3]:
        ranking_raw = fetch_rankings()
        status = fetch_job_status()
        if ranking_raw.empty:
            st.info("Sem ranking disponível para montar Top 5 por setor.")
            return

        ranking, warn_msgs = ensure_top5_columns(ranking_raw)
        for msg in warn_msgs:
            st.warning(msg)

        with st.expander("Debug Top 5 (diagnóstico)", expanded=False):
            st.write("Colunas ranking:", ranking.columns.tolist())
            st.write("Shape ranking:", ranking.shape)

        m1, m2, m3 = st.columns(3)
        m1.metric("Mapeados", int((ranking["setor"] != "outros").sum()))
        m2.metric("Em outros", int((ranking["setor"] == "outros").sum()))
        m3.metric("Overrides manuais", int(status.get("override_count", 0) if isinstance(status, dict) else 0))

        if (ranking["setor"] == "outros").any():
            st.caption("Tickers em 'outros': " + ", ".join(sorted(ranking.loc[ranking["setor"] == "outros", "ticker"].tolist())))

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

        if work.empty:
            st.warning("Nenhum dado após filtros para Top 5 por setor.")
            return

        grouped_top5 = top5_by_sector(work)
        if "setor" not in grouped_top5.columns:
            st.warning("Coluna `setor` ausente no DataFrame agrupado; fallback aplicado.")
            grouped_top5 = grouped_top5.reset_index() if getattr(grouped_top5.index, "name", None) == "setor" else grouped_top5
            if "setor" not in grouped_top5.columns:
                grouped_top5["setor"] = "outros"

        with st.expander("Debug agrupamento (diagnóstico)", expanded=False):
            st.write("Colunas grouped_top5:", grouped_top5.columns.tolist())
            st.write("Shape grouped_top5:", grouped_top5.shape)

        total_by_sector = work.groupby("setor")["ticker"].count().to_dict()

        for setor in sorted(grouped_top5["setor"].unique().tolist()):
            block = grouped_top5[grouped_top5["setor"] == setor].copy()
            title = f"{SECTOR_LABELS.get(setor, setor.title())} (Top {len(block)} de {int(total_by_sector.get(setor, len(block)))})"
            with st.expander(title, expanded=True):
                if mode == "Modo tabela":
                    cols = ["ticker", "setor", "pvp", "pvp_desconto_setor", "dy_12m", "vacancia", "inadimplencia", "alavancagem", "score_pvp", "score_fundamental", "score_total", "classificacao"]
                    cols = [c for c in cols if c in block.columns]
                    st.dataframe(block[cols], use_container_width=True, hide_index=True)
                else:
                    for _, row in block.iterrows():
                        render_ticker_card(row)


if __name__ == "__main__":
    main()
