from psae_backtest.portfolio.constructor import BetaNeutralConstructor
from psae.types.events import SentimentSignal, AssetSignal
from datetime import datetime, timezone


def test_beta_neutral_construction():
    betas = {"XLI": 1.2, "SLX": 0.9, "SPY": 1.0}
    constructor = BetaNeutralConstructor(universe_betas=betas, max_position=0.10, target_gross=1.0)

    signal = SentimentSignal(
        event_id="test",
        timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc),
        overall_sentiment=-0.7,
        confidence=0.85,
        asset_signals=[
            AssetSignal(ticker="XLI", direction=-1.0, conviction=0.8, reason="trade tariffs"),
            AssetSignal(ticker="SLX", direction=1.0, conviction=0.6, reason="domestic steel"),
        ]
    )
    weights, net_beta = constructor.construct(signal)
    assert "SPY" in weights or abs(net_beta) < 0.15
    assert all(abs(v) <= 0.10 + 1e-6 for k, v in weights.items() if k != "SPY")
