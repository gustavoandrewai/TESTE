from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class IngestionBundle:
    fiis: list[dict]
    market: list[dict]
    fundamentals: list[dict]
    benchmarks: list[dict]


class BaseFIIProvider:
    def fetch_daily_bundle(self, ref_date: date) -> IngestionBundle:  # pragma: no cover - interface
        raise NotImplementedError


class MockFIIProvider(BaseFIIProvider):
    """Provider de demonstração.

    Serve como fallback quando fontes reais estiverem indisponíveis, mantendo
    interfaces estáveis para futura troca por provider oficial.
    """

    def fetch_daily_bundle(self, ref_date: date) -> IngestionBundle:
        fiis = [
            {"ticker": "HGLG11", "name": "CSHG Logística", "sector": "logistica", "subsector": "galpoes", "manager": "Credit Suisse", "administrator": "BTG", "is_ifix": True},
            {"ticker": "VISC11", "name": "Vinci Shopping", "sector": "shopping", "subsector": "shoppings", "manager": "Vinci", "administrator": "BRL", "is_ifix": True},
            {"ticker": "MXRF11", "name": "Maxi Renda", "sector": "recebiveis_high_yield", "subsector": "cri", "manager": "XP", "administrator": "BTG", "is_ifix": True},
        ]
        market = [
            {"ticker": "HGLG11", "reference_date": ref_date, "price": 155.0, "vp_per_share": 170.0, "pvp": 0.91, "avg_daily_liquidity": 3_200_000.0, "return_1m": 0.021, "return_6m": 0.043, "return_12m": 0.12, "volatility": 0.14, "drawdown": -0.08},
            {"ticker": "VISC11", "reference_date": ref_date, "price": 110.0, "vp_per_share": 118.0, "pvp": 0.93, "avg_daily_liquidity": 2_100_000.0, "return_1m": 0.009, "return_6m": 0.032, "return_12m": 0.10, "volatility": 0.16, "drawdown": -0.11},
            {"ticker": "MXRF11", "reference_date": ref_date, "price": 9.50, "vp_per_share": 10.60, "pvp": 0.90, "avg_daily_liquidity": 4_500_000.0, "return_1m": -0.01, "return_6m": 0.02, "return_12m": 0.08, "volatility": 0.18, "drawdown": -0.13},
        ]
        fundamentals = [
            {"ticker": "HGLG11", "reference_date": ref_date, "equity": 4_000_000_000.0, "dy_monthly": 0.008, "dy_12m": 0.102, "physical_vacancy": 0.03, "financial_vacancy": 0.04, "asset_concentration": 0.19, "tenant_concentration": 0.15, "avg_contract_term": 5.2, "leverage": 0.08, "delinquency": 0.01, "income_per_share": 1.2, "income_stability": 0.87},
            {"ticker": "VISC11", "reference_date": ref_date, "equity": 3_200_000_000.0, "dy_monthly": 0.007, "dy_12m": 0.095, "physical_vacancy": 0.08, "financial_vacancy": 0.10, "asset_concentration": 0.22, "tenant_concentration": 0.20, "avg_contract_term": 3.8, "leverage": 0.14, "delinquency": 0.015, "income_per_share": 0.85, "income_stability": 0.75},
            {"ticker": "MXRF11", "reference_date": ref_date, "equity": 2_500_000_000.0, "dy_monthly": 0.011, "dy_12m": 0.135, "physical_vacancy": 0.0, "financial_vacancy": 0.0, "asset_concentration": 0.35, "tenant_concentration": 0.31, "avg_contract_term": 2.1, "leverage": 0.18, "delinquency": 0.04, "income_per_share": 0.1, "income_stability": 0.60},
        ]
        benchmarks = [{"reference_date": ref_date, "ifix_return_1m": 0.012, "ifix_return_12m": 0.11, "cdi_annual": 0.105}]
        return IngestionBundle(fiis=fiis, market=market, fundamentals=fundamentals, benchmarks=benchmarks)


class YahooFIIProvider(BaseFIIProvider):
    """Provider real usando Yahoo Finance via yfinance.

    A camada foi mantida compatível com o formato do pipeline para que
    seja fácil alternar entre mock e dados reais.
    """

    def __init__(self, tickers: list[str] | None = None):
        self.tickers = tickers or ["HGLG11.SA", "VISC11.SA", "MXRF11.SA"]

    def fetch_daily_bundle(self, ref_date: date) -> IngestionBundle:
        try:
            import yfinance as yf
        except Exception as exc:  # pragma: no cover - depende de ambiente externo
            raise RuntimeError("yfinance não está instalado no ambiente.") from exc

        quotes = yf.download(
            tickers=self.tickers,
            period="6mo",
            interval="1d",
            auto_adjust=False,
            progress=False,
            group_by="ticker",
            threads=True,
        )
        if quotes.empty:
            raise RuntimeError("Yahoo Finance retornou dataset vazio.")

        fiis = []
        market = []
        fundamentals = []
        for yf_ticker in self.tickers:
            ticker = yf_ticker.replace(".SA", "")
            frame = self._extract_frame(quotes, yf_ticker)
            last = frame.iloc[-1]
            ret_1m = self._safe_return(frame["Adj Close"], 21)
            ret_6m = self._safe_return(frame["Adj Close"], min(126, len(frame) - 1))
            ret_12m = self._safe_return(frame["Adj Close"], min(252, len(frame) - 1))

            fiis.append(
                {
                    "ticker": ticker,
                    "name": ticker,
                    "sector": "outros",
                    "subsector": "geral",
                    "manager": "nao_informado",
                    "administrator": "nao_informado",
                    "is_ifix": False,
                }
            )
            vp_per_share = max(float(last["Close"]), 0.01)  # placeholder até integrar fonte fundamentalista oficial
            market.append(
                {
                    "ticker": ticker,
                    "reference_date": ref_date,
                    "price": float(last["Close"]),
                    "vp_per_share": vp_per_share,
                    "pvp": float(last["Close"]) / vp_per_share,
                    "avg_daily_liquidity": float(frame["Volume"].tail(21).mean()),
                    "return_1m": ret_1m,
                    "return_6m": ret_6m,
                    "return_12m": ret_12m,
                    "volatility": float(frame["Adj Close"].pct_change().dropna().std() * (252**0.5)),
                    "drawdown": float((frame["Adj Close"] / frame["Adj Close"].cummax() - 1).min()),
                }
            )
            fundamentals.append(
                {
                    "ticker": ticker,
                    "reference_date": ref_date,
                    "equity": 1_000_000_000.0,
                    "dy_monthly": 0.008,
                    "dy_12m": 0.10,
                    "physical_vacancy": 0.08,
                    "financial_vacancy": 0.09,
                    "asset_concentration": 0.25,
                    "tenant_concentration": 0.22,
                    "avg_contract_term": 3.5,
                    "leverage": 0.12,
                    "delinquency": 0.02,
                    "income_per_share": 1.0,
                    "income_stability": 0.75,
                }
            )

        benchmarks = [{"reference_date": ref_date, "ifix_return_1m": 0.0, "ifix_return_12m": 0.0, "cdi_annual": 0.105}]
        return IngestionBundle(fiis=fiis, market=market, fundamentals=fundamentals, benchmarks=benchmarks)

    def _extract_frame(self, quotes: pd.DataFrame, yf_ticker: str) -> pd.DataFrame:
        if isinstance(quotes.columns, pd.MultiIndex):
            frame = quotes[yf_ticker].dropna(how="all")
        else:
            frame = quotes.dropna(how="all")
        return frame

    def _safe_return(self, prices: pd.Series, lookback: int) -> float:
        if lookback <= 0 or len(prices) <= lookback:
            return 0.0
        return float(prices.iloc[-1] / prices.iloc[-1 - lookback] - 1)
