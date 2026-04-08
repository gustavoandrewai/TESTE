"""Pipeline diário simples para gerar ranking.csv na raiz do projeto."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


RANKING_FILE = Path("ranking.csv")
DEFAULT_TICKERS = ["HGLG11.SA", "VISC11.SA", "MXRF11.SA", "XPLG11.SA", "KNCR11.SA"]


@dataclass
class PipelineResult:
    rows: int
    file_path: str


class DailyPipeline:
    """Gera um ranking simples com colunas úteis para o dashboard.

    Colunas garantidas no CSV:
    - ticker
    - price
    - ret_1m
    - ret_6m
    - vol
    - score
    """

    def __init__(self, tickers: list[str] | None = None):
        self.tickers = tickers or DEFAULT_TICKERS

    def run(self) -> PipelineResult:
        df = self._collect_market_data()
        df = self._compute_score(df)
        output = df[["ticker", "price", "ret_1m", "ret_6m", "vol", "score"]].sort_values("score", ascending=False)
        output.to_csv(RANKING_FILE, index=False)
        return PipelineResult(rows=len(output), file_path=str(RANKING_FILE.resolve()))

    def _collect_market_data(self) -> pd.DataFrame:
        try:
            import yfinance as yf

            rows = []
            for ticker in self.tickers:
                history = yf.Ticker(ticker).history(period="6mo", interval="1d")
                if history.empty:
                    continue
                close = history["Close"]
                ret_1m = float(close.iloc[-1] / close.iloc[max(0, len(close) - 22)] - 1) if len(close) > 22 else 0.0
                ret_6m = float(close.iloc[-1] / close.iloc[0] - 1)
                vol = float(close.pct_change().dropna().std() * (252**0.5))
                rows.append(
                    {
                        "ticker": ticker.replace(".SA", ""),
                        "price": float(close.iloc[-1]),
                        "ret_1m": ret_1m,
                        "ret_6m": ret_6m,
                        "vol": vol,
                    }
                )
            if rows:
                return pd.DataFrame(rows)
        except Exception:
            pass

        # Fallback mock para ambiente sem Yahoo/disponibilidade de rede.
        return pd.DataFrame(
            [
                {"ticker": "HGLG11", "price": 155.0, "ret_1m": 0.02, "ret_6m": 0.08, "vol": 0.14},
                {"ticker": "VISC11", "price": 111.0, "ret_1m": 0.01, "ret_6m": 0.05, "vol": 0.16},
                {"ticker": "MXRF11", "price": 9.8, "ret_1m": 0.00, "ret_6m": 0.03, "vol": 0.18},
            ]
        )

    def _compute_score(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()

        # Score didático (0-100): retorno positivo ajuda, volatilidade alta penaliza.
        ret_1m_score = ((data["ret_1m"].clip(-0.2, 0.2) + 0.2) / 0.4) * 100
        ret_6m_score = ((data["ret_6m"].clip(-0.4, 0.4) + 0.4) / 0.8) * 100
        vol_penalty = ((data["vol"].clip(0.05, 0.5) - 0.05) / 0.45) * 100

        data["score"] = (0.35 * ret_1m_score + 0.45 * ret_6m_score + 0.20 * (100 - vol_penalty)).clip(0, 100)
        return data


if __name__ == "__main__":
    result = DailyPipeline().run()
    print(f"ranking.csv gerado com {result.rows} linhas em: {result.file_path}")
