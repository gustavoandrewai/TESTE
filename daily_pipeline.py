"""Pipeline diário simples e didático para FIIs (arquivos locais)."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RANKING_FILE = Path("ranking.csv")
JOB_STATUS_FILE = Path("job_status.json")
FUNDAMENTALS_FILE = Path("fundamentals_mock.csv")
TOP_BY_SECTOR_FILE = Path("top_by_sector.csv")

DEFAULT_TICKERS = ["HGLG11", "XPLG11", "XPML11", "VISC11", "KNCR11", "MXRF11", "HGRE11"]


@dataclass
class PipelineResult:
    rows: int
    tickers: list[str]
    ranking_file: str


def load_or_create_fundamentals_mock(path: Path = FUNDAMENTALS_FILE) -> pd.DataFrame:
    """Carrega arquivo fundamentalista local; cria mock profissional se não existir."""
    if path.exists():
        return pd.read_csv(path)

    data = [
        {"ticker": "HGLG11", "setor": "logistica", "subsetor": "galpoes_prime", "pvp": 0.91, "dy_12m": 0.102, "vacancia": 0.03, "inadimplencia": 0.01, "alavancagem": 0.08, "liquidez_media": 3200000, "estabilidade_rendimentos": 0.88},
        {"ticker": "XPLG11", "setor": "logistica", "subsetor": "galpoes_modernos", "pvp": 0.89, "dy_12m": 0.106, "vacancia": 0.05, "inadimplencia": 0.01, "alavancagem": 0.12, "liquidez_media": 2600000, "estabilidade_rendimentos": 0.82},
        {"ticker": "XPML11", "setor": "shopping", "subsetor": "shoppings_dominantes", "pvp": 0.95, "dy_12m": 0.094, "vacancia": 0.07, "inadimplencia": 0.02, "alavancagem": 0.18, "liquidez_media": 2900000, "estabilidade_rendimentos": 0.78},
        {"ticker": "VISC11", "setor": "shopping", "subsetor": "shoppings_hibridos", "pvp": 0.93, "dy_12m": 0.098, "vacancia": 0.08, "inadimplencia": 0.015, "alavancagem": 0.14, "liquidez_media": 2100000, "estabilidade_rendimentos": 0.75},
        {"ticker": "KNCR11", "setor": "recebiveis_high_grade", "subsetor": "cri_high_grade", "pvp": 1.01, "dy_12m": 0.115, "vacancia": 0.00, "inadimplencia": 0.005, "alavancagem": 0.05, "liquidez_media": 3700000, "estabilidade_rendimentos": 0.91},
        {"ticker": "MXRF11", "setor": "recebiveis_high_yield", "subsetor": "cri_high_yield", "pvp": 0.90, "dy_12m": 0.132, "vacancia": 0.00, "inadimplencia": 0.04, "alavancagem": 0.19, "liquidez_media": 4500000, "estabilidade_rendimentos": 0.64},
        {"ticker": "HGRE11", "setor": "lajes_corporativas", "subsetor": "lajes_sp", "pvp": 0.78, "dy_12m": 0.108, "vacancia": 0.19, "inadimplencia": 0.03, "alavancagem": 0.16, "liquidez_media": 1100000, "estabilidade_rendimentos": 0.58},
        {"ticker": "TRXF11", "setor": "renda_urbana", "subsetor": "varejo_urbano", "pvp": 0.97, "dy_12m": 0.111, "vacancia": 0.02, "inadimplencia": 0.01, "alavancagem": 0.21, "liquidez_media": 1900000, "estabilidade_rendimentos": 0.80},
        {"ticker": "BCFF11", "setor": "FoF", "subsetor": "fundo_de_fundos", "pvp": 0.86, "dy_12m": 0.103, "vacancia": 0.00, "inadimplencia": 0.00, "alavancagem": 0.07, "liquidez_media": 1300000, "estabilidade_rendimentos": 0.72},
        {"ticker": "HGRU11", "setor": "hibridos", "subsetor": "educacional_varejo", "pvp": 0.94, "dy_12m": 0.097, "vacancia": 0.04, "inadimplencia": 0.01, "alavancagem": 0.13, "liquidez_media": 1550000, "estabilidade_rendimentos": 0.79},
        {"ticker": "DEVA11", "setor": "desenvolvimento", "subsetor": "cri_estruturado", "pvp": 0.66, "dy_12m": 0.145, "vacancia": 0.00, "inadimplencia": 0.10, "alavancagem": 0.32, "liquidez_media": 800000, "estabilidade_rendimentos": 0.30},
        {"ticker": "ABCP11", "setor": "outros", "subsetor": "diversificado", "pvp": 0.92, "dy_12m": 0.09, "vacancia": 0.06, "inadimplencia": 0.02, "alavancagem": 0.15, "liquidez_media": 600000, "estabilidade_rendimentos": 0.67},
    ]
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    return df


class DailyPipeline:
    def __init__(self, tickers: list[str] | None = None):
        self.tickers = [t.strip().upper() for t in (tickers or DEFAULT_TICKERS) if t.strip()]

    def run(self) -> PipelineResult:
        fundamentals = load_or_create_fundamentals_mock()
        universe = fundamentals[fundamentals["ticker"].isin(self.tickers)].copy()
        if universe.empty:
            universe = fundamentals[fundamentals["ticker"].isin(DEFAULT_TICKERS)].copy()

        market = self.collect_market_data(universe["ticker"].tolist(), universe)
        df = universe.merge(market, on="ticker", how="left")

        df["liquidez_media"] = df["liquidez_media_x"].fillna(df["liquidez_media_y"])
        df = df.drop(columns=[c for c in ["liquidez_media_x", "liquidez_media_y"] if c in df.columns])

        df = self.compute_sector_benchmarks(df)
        df = self.compute_pvp_score(df)
        df = self.compute_fundamental_score(df)
        df = self.compute_income_score(df)
        df = self.compute_risk_score(df)
        df = self.compute_total_score(df)
        df = self.classify_opportunity(df)

        ordered_cols = [
            "ticker", "setor", "subsetor", "preco", "retorno_1m", "retorno_3m", "retorno_6m", "volatilidade", "drawdown", "last_day_return", "liquidez_media",
            "pvp", "pvp_setor_mediana", "pvp_desconto_setor", "pvp_zscore_historico", "dy_12m", "dy_setor_mediana", "dy_spread_setor",
            "vacancia", "inadimplencia", "alavancagem", "estabilidade_rendimentos",
            "score_pvp", "score_fundamental", "score_renda", "score_risco", "score_momentum", "score_total", "classificacao",
        ]
        ranking = df[ordered_cols].sort_values("score_total", ascending=False)
        ranking.to_csv(RANKING_FILE, index=False)

        top = ranking.sort_values(["setor", "score_total"], ascending=[True, False]).groupby("setor").head(5)
        top.to_csv(TOP_BY_SECTOR_FILE, index=False)

        self.write_job_status("success", ranking)
        return PipelineResult(rows=len(ranking), tickers=ranking["ticker"].tolist(), ranking_file=str(RANKING_FILE.resolve()))

    def collect_market_data(self, tickers: list[str], fundamentals: pd.DataFrame) -> pd.DataFrame:
        rows = []
        try:
            import yfinance as yf

            for ticker in tickers:
                yf_ticker = f"{ticker}.SA"
                hist = yf.Ticker(yf_ticker).history(period="1y", interval="1d")
                if hist.empty:
                    continue
                close = hist["Close"].dropna()
                if close.empty:
                    continue
                rows.append(
                    {
                        "ticker": ticker,
                        "preco": float(close.iloc[-1]),
                        "retorno_1m": self.safe_return(close, 21),
                        "retorno_3m": self.safe_return(close, 63),
                        "retorno_6m": self.safe_return(close, 126),
                        "volatilidade": float(close.pct_change().dropna().std() * (252**0.5)),
                        "drawdown": float((close / close.cummax() - 1).iloc[-1]),
                        "last_day_return": float(close.pct_change().iloc[-1]) if len(close) > 1 else 0.0,
                        "liquidez_media": float(hist["Volume"].tail(21).mean()),
                    }
                )
            if rows:
                return pd.DataFrame(rows)
        except Exception:
            pass

        # fallback mock orientado ao fundamentals
        mock = []
        for i, row in fundamentals.reset_index(drop=True).iterrows():
            mock.append(
                {
                    "ticker": row["ticker"],
                    "preco": 80 + 7 * (i + 1),
                    "retorno_1m": -0.01 + 0.007 * (i + 1),
                    "retorno_3m": -0.02 + 0.012 * (i + 1),
                    "retorno_6m": -0.03 + 0.018 * (i + 1),
                    "volatilidade": 0.12 + 0.01 * (i % 6),
                    "drawdown": -0.05 - 0.01 * (i % 5),
                    "last_day_return": -0.002 + 0.001 * (i % 4),
                    "liquidez_media": row["liquidez_media"],
                }
            )
        return pd.DataFrame(mock)

    def compute_sector_benchmarks(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["pvp_setor_mediana"] = out.groupby("setor")["pvp"].transform("median")
        out["dy_setor_mediana"] = out.groupby("setor")["dy_12m"].transform("median")
        out["pvp_desconto_setor"] = (out["pvp_setor_mediana"] - out["pvp"]) / out["pvp_setor_mediana"].replace(0, 1)
        out["dy_spread_setor"] = out["dy_12m"] - out["dy_setor_mediana"]

        # Sem histórico persistente local, usamos zscore cross-section de P/VP como proxy didático.
        pvp_std = out["pvp"].std(ddof=0) or 0.01
        out["pvp_zscore_historico"] = (out["pvp"] - out["pvp"].mean()) / pvp_std
        return out

    def compute_pvp_score(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        discount_score = self.norm(out["pvp_desconto_setor"], -0.30, 0.35)
        zscore_score = self.norm(-out["pvp_zscore_historico"], -2.5, 2.5)
        deterioration = (out["vacancia"] + out["inadimplencia"] + out["alavancagem"]).clip(0, 1)
        penalty = self.norm(deterioration, 0, 1) * 0.30
        out["score_pvp"] = (0.65 * discount_score + 0.35 * zscore_score) * (1 - penalty / 100)
        return out

    def compute_fundamental_score(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["score_fundamental"] = (
            0.35 * (100 - self.norm(out["vacancia"], 0, 0.35))
            + 0.35 * (100 - self.norm(out["inadimplencia"], 0, 0.2))
            + 0.30 * (100 - self.norm(out["alavancagem"], 0, 0.5))
        ).clip(0, 100)
        return out

    def compute_income_score(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        dy_score = self.norm(out["dy_spread_setor"], -0.05, 0.05)
        stability_score = self.norm(out["estabilidade_rendimentos"], 0, 1)
        out["score_renda"] = (0.55 * dy_score + 0.45 * stability_score).clip(0, 100)
        return out

    def compute_risk_score(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        liq = self.norm(out["liquidez_media"], 300000, 5000000)
        vol = 100 - self.norm(out["volatilidade"], 0.05, 0.55)
        dd = 100 - self.norm(out["drawdown"].abs(), 0.02, 0.45)
        out["score_risco"] = (0.40 * liq + 0.35 * vol + 0.25 * dd).clip(0, 100)
        out["score_momentum"] = self.norm(0.2 * out["retorno_1m"] + 0.3 * out["retorno_3m"] + 0.5 * out["retorno_6m"], -0.30, 0.35)
        return out

    def compute_total_score(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["score_total"] = (
            0.45 * out["score_pvp"]
            + 0.25 * out["score_fundamental"]
            + 0.15 * out["score_renda"]
            + 0.10 * out["score_risco"]
            + 0.05 * out["score_momentum"]
        ).clip(0, 100)
        return out

    def classify_opportunity(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        deterioration = out["vacancia"] + out["inadimplencia"] + out["alavancagem"]

        out["classificacao"] = "neutro"
        out.loc[(out["score_pvp"] >= 65) & (deterioration >= 0.55) & (out["score_fundamental"] < 45), "classificacao"] = "value_trap"
        out.loc[(out["score_pvp"] >= 65) & (out["score_fundamental"] >= 55) & (out["score_total"] >= 60), "classificacao"] = "assimetria_positiva"
        return out

    def write_job_status(self, status: str, ranking: pd.DataFrame) -> None:
        payload = {
            "status": status,
            "tickers": ranking["ticker"].tolist(),
            "last_run_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "processed_count": int(len(ranking)),
        }
        JOB_STATUS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def safe_return(self, prices: pd.Series, lookback: int) -> float:
        if len(prices) <= lookback:
            return 0.0
        return float(prices.iloc[-1] / prices.iloc[-1 - lookback] - 1)

    def norm(self, series: pd.Series, low: float, high: float) -> pd.Series:
        if high == low:
            return pd.Series([50.0] * len(series), index=series.index)
        return ((series.clip(low, high) - low) / (high - low) * 100).clip(0, 100)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera ranking.csv de FIIs")
    parser.add_argument("--tickers", type=str, default="", help="Tickers separados por vírgula")
    return parser.parse_args()


def split_tickers(raw: str) -> list[str]:
    if not raw.strip():
        return DEFAULT_TICKERS
    return [t.strip() for t in raw.split(",") if t.strip()]


if __name__ == "__main__":
    args = parse_args()
    tickers = split_tickers(args.tickers)
    result = DailyPipeline(tickers).run()
    print(json.dumps({"status": "success", "rows": result.rows, "tickers": result.tickers, "file": "ranking.csv"}))
