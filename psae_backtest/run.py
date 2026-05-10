import click
import pickle
from psae_backtest.strategy.psae_v1 import PSAEv1Strategy
from psae_backtest.engine.runner import BacktestRunner


@click.command()
@click.option("--strategy", default="psae_v1", show_default=True)
@click.option("--start", required=True, help="Start date YYYY-MM-DD")
@click.option("--end", required=True, help="End date YYYY-MM-DD")
@click.option("--signals", default=None, help="Path to signals CSV")
@click.option("--output", default="results/backtest_result.pkl", show_default=True)
@click.option("--cash", default=1_000_000.0, show_default=True)
def run(strategy, start, end, signals, output, cash):
    """Run PSAE backtest."""
    click.echo(f"Running {strategy}: {start} → {end}")
    strat = PSAEv1Strategy()
    runner = BacktestRunner(strategy=strat, start=start, end=end, signals_path=signals, initial_cash=cash)
    results = runner.run()
    import os; os.makedirs("results", exist_ok=True)
    with open(output, "wb") as f:
        pickle.dump(results, f)
    click.echo(f"Sharpe: {results['sharpe']} | Max DD: {results['max_drawdown']:.2%} | Net Beta: {results['avg_net_beta']}")
    click.echo(f"Results: {output}")


if __name__ == "__main__":
    run()
