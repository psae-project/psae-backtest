from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from psae.types.events import SentimentSignal


@dataclass
class SimulationContext:
    today: datetime
    portfolio: dict = field(default_factory=dict)
    cash: float = 1_000_000.0
    signals: list[SentimentSignal] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class BaseStrategy(ABC):
    @abstractmethod
    def initialize(self, context: SimulationContext): ...

    def before_trading_start(self, context: SimulationContext, data): ...

    @abstractmethod
    def handle_signal(self, context: SimulationContext, data, signal: SentimentSignal): ...

    def handle_data(self, context: SimulationContext, data): ...

    def on_market_close(self, context: SimulationContext, data): ...

    def order_target_percent(self, context: SimulationContext, ticker: str, weight: float):
        target_value = context.cash * weight
        context.portfolio[ticker] = {"weight": weight, "value": target_value}
