"""
Portfolio CLI - Simple command-line interface for portfolio management
"""
import click
from data_module.data_manager import DataManager
from tabulate import tabulate


@click.group()
def cli():
    """Portfolio Management CLI - Manual Trading System"""
    pass


@cli.command()
@click.argument('action', type=click.Choice(['BUY', 'SELL']))
@click.argument('symbol')
@click.argument('quantity', type=float)
@click.argument('price', type=float)
@click.option('--fees', default=0.0, type=float, help='Trading fees')
@click.option('--notes', help='Trade notes')
def trade(action, symbol, quantity, price, fees, notes):
    """
    Record a trade (BUY or SELL)

    Examples:
        portfolio trade BUY AAPL 10 150.50
        portfolio trade SELL AAPL 5 155.00 --fees 1.50
    """
    dm = DataManager()

    try:
        if action == 'BUY':
            dm.record_buy(symbol, quantity, price, fees, notes)
        else:
            dm.record_sell(symbol, quantity, price, fees, notes)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('amount', type=float)
@click.option('--notes', help='Deposit notes')
def deposit(amount, notes):
    """Record a capital deposit"""
    dm = DataManager()
    try:
        dm.record_deposit(amount, notes)
        click.echo(f"✅ Deposited ${amount:.2f}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('amount', type=float)
@click.option('--notes', help='Withdrawal notes')
def withdraw(amount, notes):
    """Record a capital withdrawal"""
    dm = DataManager()
    try:
        dm.record_withdrawal(amount, notes)
        click.echo(f"✅ Withdrew ${amount:.2f}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
def show():
    """
    Display current portfolio summary and all positions

    Shows:
    - Total equity, P&L, net contributions
    - All open positions with current values
    """
    dm = DataManager()

    try:
        portfolio = dm.get_portfolio_value()

        click.echo("\n" + "=" * 60)
        click.echo("📊 PORTFOLIO SUMMARY")
        click.echo("=" * 60)
        click.echo(f"Total Equity:     ${portfolio['total_equity']:,.2f}")
        click.echo(f"Positions Value:  ${portfolio['positions_value']:,.2f}")
        click.echo(f"Total P&L:        ${portfolio['total_pnl']:,.2f} ({portfolio['total_pnl_pct']:.2f}%)")
        click.echo(f"Net Contributed:  ${portfolio['net_contributed']:,.2f}")
        click.echo(f"Deposits:         ${portfolio['total_deposits']:,.2f}")
        click.echo(f"Withdrawals:      ${portfolio['total_withdrawals']:,.2f}")
        click.echo(f"Open Positions:   {portfolio['num_positions']}")

        if portfolio['positions']:
            click.echo("\n" + "=" * 60)
            click.echo("📈 OPEN POSITIONS")
            click.echo("=" * 60)

            table_data = []
            for pos in portfolio['positions']:
                table_data.append([
                    pos['symbol'],
                    f"{pos['quantity']:.2f}",
                    f"${pos['avg_entry_price']:.2f}",
                    f"${pos['current_price']:.2f}",
                    f"${pos['market_value']:,.2f}",
                    f"${pos['unrealized_pnl']:,.2f}",
                    f"{pos['unrealized_pnl_pct']:.2f}%",
                ])

            headers = ['Symbol', 'Qty', 'Avg Cost', 'Current', 'Value', 'P&L', 'P&L %']
            click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
        else:
            click.echo("\nNo open positions.")

        click.echo("")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('symbol')
def analyze(symbol):
    """
    Analyze a stock and get investment recommendation

    Example:
        portfolio analyze AAPL
    """
    dm = DataManager()

    click.echo(f"\n🔍 Analyzing {symbol.upper()}...")
    click.echo("This may take a minute...\n")

    try:
        analysis = dm.analyze_stock(symbol.upper())

        click.echo("=" * 60)
        click.echo(f"📊 ANALYSIS: {analysis['symbol']}")
        click.echo("=" * 60)
        click.echo(f"Recommendation:   {analysis['recommendation']}")
        click.echo(f"Confidence:       {analysis.get('confidence_score', 0):.2f}")
        click.echo(f"Current Price:    ${analysis.get('current_price', 0):.2f}")
        click.echo(f"Date:             {analysis['analysis_date'][:10]}")

        if analysis.get('bull_case'):
            click.echo(f"\n🐂 Bull Case:\n{analysis['bull_case']}")

        if analysis.get('bear_case'):
            click.echo(f"\n🐻 Bear Case:\n{analysis['bear_case']}")

        if analysis.get('analyst_notes'):
            click.echo(f"\n📝 Summary:\n{analysis['analyst_notes']}")

        click.echo("")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option('--symbol', help='Filter by symbol')
@click.option('--days', default=30, type=int, help='Number of days (default: 30)')
def history(symbol, days):
    """
    Show trade history

    Examples:
        portfolio history
        portfolio history --symbol AAPL
        portfolio history --days 7
    """
    dm = DataManager()

    try:
        trades = dm.portfolio_repo.get_trade_history(days, symbol)

        if not trades:
            click.echo(f"\nNo trades found in the last {days} days.")
            return

        click.echo(f"\n📜 TRADE HISTORY (Last {days} days)")
        if symbol:
            click.echo(f"Filtered by: {symbol}")
        click.echo("=" * 80)

        table_data = []
        for trade in trades:
            table_data.append([
                trade['timestamp'][:10],
                trade['action'],
                trade['symbol'],
                f"{trade['quantity']:.2f}",
                f"${trade['price']:.2f}",
                f"${trade['total_value']:,.2f}",
                f"${trade.get('fees', 0):.2f}",
                trade.get('notes', '')[:30],
            ])

        headers = ['Date', 'Action', 'Symbol', 'Qty', 'Price', 'Total', 'Fees', 'Notes']
        click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
        click.echo(f"\nTotal trades: {len(trades)}\n")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
