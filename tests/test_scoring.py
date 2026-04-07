import pandas as pd

from app.ingestion.providers import YahooFIIProvider
from app.scoring.model import classify_opportunity, compute_pvp_score


def test_compute_pvp_score_discounted_has_higher_score():
    sector = pd.Series([0.85, 0.90, 0.95, 1.00, 1.05])
    hist = pd.Series([0.95, 1.00, 1.02, 1.04, 1.01])
    s_discounted = compute_pvp_score(0.88, sector, hist, fundamental_deterioration=0.1)
    s_expensive = compute_pvp_score(1.08, sector, hist, fundamental_deterioration=0.1)
    assert s_discounted > s_expensive


def test_classify_value_trap():
    assert classify_opportunity(58, 70, 30, 0.8) == "value_trap"


def test_classify_positive_asymmetry():
    assert classify_opportunity(75, 78, 70, 0.2) == "assimetria_positiva"


def test_yahoo_provider_safe_return():
    provider = YahooFIIProvider()
    series = pd.Series([10.0, 11.0, 12.0, 13.0])
    assert round(provider._safe_return(series, 3), 4) == 0.3
