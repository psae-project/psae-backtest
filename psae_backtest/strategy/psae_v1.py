from __future__ import annotations
from psae_backtest.strategy.base import BaseStrategy, SimulationContext
from psae_backtest.portfolio.constructor import BetaNeutralConstructor
from psae.types.events import SentimentSignal
from psae.utils.time import utc_now
from psae.utils.logging import get_logger

log = get_logger("psae.backtest.strategy.v1")


class PSAEv1Strategy(BaseStrategy):
    """
    Reference PSAE strategy.
    Beta-neutral | 4h default holding | VIX kill switch | signal-based rebalancing.
    """

    def initialize(self, context: SimulationContext):
        context.metadata.update({
            "min_confidence": 0.65,
            "holding_period_hours": 4,
            "vix_threshold": 40.0,
            "open_signals": {},
            "constructor": None,
        })

    def handle_signal(self, context: SimulationContext, data, signal: SentimentSignal):
        if signal.confidence < context.metadata["min_confidence"]:
            return

        vix = data.get("VIX", {}).get("close") if hasattr(data, "get") else None
        if vix and vix > context.metadata["vix_threshold"]:
            log.warning("vix_kill_switch", vix=vix)
            return

        if context.metadata["constructor"] is None:
            betas = {t: 1.0 for t in ["SPY", "QQQ", "XLI", "XLE", "JETS", "FXI", "SLX"]}
            context.metadata["constructor"] = BetaNeutralConstructor(universe_betas=betas)

        weights, net_beta = context.metadata["constructor"].construct(signal)

        for ticker, weight in weights.items():
            self.order_target_percent(context, ticker, weight)

        context.metadata["open_signals"][signal.event_id] = {
            "positions": list(weights.keys()),
            "entered_at": utc_now(),
            "net_beta": net_beta,
        }
        log.info("signal_executed", event_id=signal.event_id,
                 n_positions=len(weights), net_beta=net_beta)

    def handle_data(self, context: SimulationContext, data):
        """Time-based decay: exit stale positions."""
        now = utc_now()
        stale = []
        holding_hours = context.metadata["holding_period_hours"]
        for sig_id, meta in context.metadata["open_signals"].items():
            elapsed = (now - meta["entered_at"]).total_seconds() / 3600
            if elapsed > holding_hours:
                for ticker in meta["positions"]:
                    self.order_target_percent(context, ticker, 0.0)
                stale.append(sig_id)
                log.info("signal_decayed", sig_id=sig_id, elapsed_hours=round(elapsed, 1))
        for s in stale:
            del context.metadata["open_signals"][s]
