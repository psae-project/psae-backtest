# psae-backtest

Event-driven backtesting engine for **PSAE** — analogous to Quantopian's **Zipline**.

## Quick start

```bash
pip install psae-backtest

psae-backtest run \
  --start 2017-01-20 \
  --end 2021-01-20 \
  --signals data/signals.csv \
  --output results/v1.pkl
```

## Strategy interface

```python
from psae_backtest.strategy.base import BaseStrategy, SimulationContext
from psae.types.events import SentimentSignal

class MyStrategy(BaseStrategy):
    def initialize(self, context): ...
    def handle_signal(self, context, data, signal: SentimentSignal): ...
    def handle_data(self, context, data): ...
```

## License
Apache 2.0
