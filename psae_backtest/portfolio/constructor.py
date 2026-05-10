from __future__ import annotations
import numpy as np
from psae.types.events import SentimentSignal
from psae.config.settings import settings


class BetaNeutralConstructor:
    """Constructs a beta-neutral portfolio from a SentimentSignal."""

    def __init__(
        self,
        universe_betas: dict[str, float],
        max_position: float | None = None,
        target_gross: float | None = None,
        hedge_ticker: str = "SPY",
    ):
        self.betas = universe_betas
        self.max_position = max_position or settings.max_single_position
        self.target_gross = target_gross or settings.max_gross_exposure
        self.hedge_ticker = hedge_ticker

    def construct(self, signal: SentimentSignal) -> tuple[dict[str, float], float]:
        """Returns (weights_dict, net_beta)."""
        if not signal.asset_signals:
            return {}, 0.0

        total_conv = sum(s.conviction for s in signal.asset_signals) or 1.0
        weights: dict[str, float] = {}
        for s in signal.asset_signals:
            raw = (s.conviction / total_conv) * s.direction * self.target_gross
            weights[s.ticker] = float(np.clip(raw, -self.max_position, self.max_position))

        # Compute portfolio beta
        portfolio_beta = sum(weights.get(t, 0) * self.betas.get(t, 1.0) for t in weights)

        # Hedge
        if abs(portfolio_beta) > 0.01:
            weights[self.hedge_ticker] = weights.get(self.hedge_ticker, 0.0) - portfolio_beta

        # Normalise to target gross
        gross = sum(abs(v) for v in weights.values())
        if gross > self.target_gross:
            scale = self.target_gross / gross
            weights = {k: v * scale for k, v in weights.items()}

        net_beta = sum(weights.get(t, 0) * self.betas.get(t, 1.0) for t in weights)
        return weights, round(net_beta, 5)
