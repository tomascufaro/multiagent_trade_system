from click.testing import CliRunner

from cli import portfolio_cli
from data_module.repositories.portfolio_repository import PortfolioRepository


def test_cli_flow(tmp_path, monkeypatch):
    db_path = tmp_path / "portfolio.db"
    monkeypatch.setenv("PORTFOLIO_DB_PATH", str(db_path))

    def fake_summary(self):
        return {
            'total_equity': 200.0,
            'positions_value': 200.0,
            'total_pnl': -800.0,
            'total_pnl_pct': -80.0,
            'num_positions': 1,
            'positions': [
                {
                    'symbol': 'AAPL',
                    'quantity': 2.0,
                    'avg_entry_price': 100.0,
                    'current_price': 100.0,
                    'market_value': 200.0,
                    'unrealized_pnl': 0.0,
                    'unrealized_pnl_pct': 0.0,
                }
            ],
            'net_contributed': 1000.0,
            'total_deposits': 1000.0,
            'total_withdrawals': 0.0,
        }

    monkeypatch.setattr(portfolio_cli.DataManager, "get_portfolio_value", fake_summary)
    monkeypatch.setattr(
        PortfolioRepository,
        "get_trade_history",
        lambda self, days=30, symbol=None: [],
    )

    runner = CliRunner()

    result = runner.invoke(portfolio_cli.cli, ["deposit", "1000"])
    assert result.exit_code == 0

    result = runner.invoke(portfolio_cli.cli, ["trade", "BUY", "AAPL", "2", "100"])
    assert result.exit_code == 0

    result = runner.invoke(portfolio_cli.cli, ["trade", "SELL", "AAPL", "1", "120"])
    assert result.exit_code == 0

    result = runner.invoke(portfolio_cli.cli, ["show"])
    assert result.exit_code == 0

    result = runner.invoke(portfolio_cli.cli, ["history"])
    assert result.exit_code == 0
