from analyst_service.analysis.ta_signals import TechnicalAnalysis


def test_sma_in_signals():
    ta = TechnicalAnalysis()
    prices = list(range(1, 260))
    signals = ta.get_signals(prices)
    assert "sma" in signals
    assert signals["sma"]["short_sma"] > 0
    assert signals["sma"]["long_sma"] > 0
