from dataclasses import dataclass
from datetime import date


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
