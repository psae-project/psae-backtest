from __future__ import annotations
import pandas as pd
import numpy as np
from psae_backtest.engine.clock import SimulatedClock
from psae_backtest.strategy.base import BaseStrategy, SimulationContext
from psae.types.events import SentimentSignal
from psae.utils.logging import get_logger

log = get_logger("psae.backtest.runner")


class BacktestRunner:
    def __init__(
        self,
        strategy: BaseStrategy,
        start: str,
        end: str,
        signals_path: str | None = None,
        initial_cash: float = 1_000_000.0,
    ):
        self.strategy = strategy
        self.start = start
        self.end = end
        self.initial_cash = initial_cash
        self.signals_df = pd.read_csv(signals_path, parse_dates=["timestamp"]) if signals_path else pd.DataFrame()

    def run(self) -> dict:
        context = SimulationContext(
            today=pd.Timestamp(self.start).to_pydatetime(),
            cash=self.initial_cash,
        )
        self.strategy.initialize(context)
        clock = SimulatedClock(self.start, self.end)
        portfolio_values = []

        for bar in clock:
            context.today = bar.timestamp

            # Deliver any signals that fall in this bar
            if not self.signals_df.empty:
                bar_signals = self.signals_df[
                    self.signals_df["timestamp"].between(
                        bar.timestamp, bar.timestamp + pd.Timedelta(hours=1)
                    )
                ]
                for _, row in bar_signals.iterrows():
                    from psae.types.events import SentimentSignal
                    sig = SentimentSignal(
                        event_id=str(row.get("event_id", "")),
                        timestamp=row["timestamp"],
                        overall_sentiment=float(row["signal_score"]),
                        confidence=float(row.get("confidence", 0.8)),
                    )
                    self.strategy.handle_signal(context, {}, sig)

            self.strategy.handle_data(context, {})
            portfolio_values.append({
                "timestamp": bar.timestamp,
                "portfolio_value": self._compute_value(context),
            })

        pv = pd.DataFrame(portfolio_values).set_index("timestamp")
        pv["return"] = pv["portfolio_value"].pct_change()
        returns = pv["return"].dropna()

        sharpe = returns.mean() / returns.std() * np.sqrt(252 * 6.5) if returns.std() > 0 else 0
        max_dd = ((pv["portfolio_value"] / pv["portfolio_value"].cummax()) - 1).min()
        avg_beta = np.mean([m.get("net_beta", 0) for m in context.metadata.get("open_signals", {}).values()] or [0])

        return {
            "portfolio_returns": returns,
            "portfolio_values": pv,
            "sharpe": round(sharpe, 3),
            "max_drawdown": round(max_dd, 4),
            "avg_net_beta": round(avg_beta, 5),
            "total_return": round((pv["portfolio_value"].iloc[-1] / self.initial_cash) - 1, 4),
        }

    def _compute_value(self, context: SimulationContext) -> float:
        positions_value = sum(p.get("value", 0) for p in context.portfolio.values())
        return context.cash + positions_value
