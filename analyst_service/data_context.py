from typing import Dict, Any, List, Set
from datetime import datetime
import os
import sys

# Ensure project root is on the path when running as a script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_module.data_manager import DataManager


def build_analysis_context(symbol: str, config_path: str = 'analyst_service/config/settings.yaml') -> Dict[str, Any]:
    """
    Build a structured context for LLM agents using DataManager.

    Returns a dict with portfolio summary, current position, performance metrics,
    recent news, and optional placeholders for histories.
    """
    dm = DataManager(config_path)

    portfolio = dm.get_portfolio_summary() or {}
    position = dm.get_position(symbol)
    performance = dm.calculate_performance_metrics('30d') or {}
    recent_news = dm.get_news_for_symbol(symbol, limit=10) or []

    return {
        'symbol': symbol,
        'portfolio': portfolio,
        'position': position,
        'performance': performance,
        'recent_news': recent_news,
        # Optional placeholders for later enhancements
        'position_history': [],
        'trade_history': [],
        'timestamp': datetime.now().isoformat(),
    }


def _fmt_money(value: float) -> str:
    try:
        return f"${value:,.2f}"
    except Exception:
        return str(value)


def _fmt_pct(value: float) -> str:
    try:
        return f"{value*100:.2f}%" if abs(value) <= 1.0 else f"{value:.2f}%"
    except Exception:
        return str(value)


def format_context_for_prompt(context: Dict[str, Any]) -> str:
    """
    Convert the structured context to a readable multiline string for LLM prompts.
    """
    lines: List[str] = []
    symbol = context.get('symbol', 'UNKNOWN')
    portfolio = context.get('portfolio') or {}
    position = context.get('position')
    perf = context.get('performance') or {}
    news = context.get('recent_news') or []
    position_history = context.get('position_history') or []
    trade_history = context.get('trade_history') or []

    # Portfolio overview
    lines.append("=== PORTFOLIO CONTEXT ===")
    lines.append(f"Current Equity: {_fmt_money(portfolio.get('equity', 0))}")
    lines.append(f"Cash: {_fmt_money(portfolio.get('cash', 0))}")

    positions = portfolio.get('positions') or []
    lines.append(f"Open Positions: {len(positions)}")
    if positions:
        lines.append("Top Positions (by market value):")
        sorted_positions = sorted(
            positions,
            key=lambda p: float(p.get('market_value', 0) or 0),
            reverse=True,
        )
        for pos in sorted_positions[:5]:
            symbol_p = pos.get('symbol', 'UNKNOWN')
            qty_p = abs(float(pos.get('qty', 0) or 0))
            side_p = "LONG" if float(pos.get('qty', 0) or 0) > 0 else "SHORT"
            mv_p = _fmt_money(float(pos.get('market_value', 0) or 0))
            lines.append(f"- {symbol_p}: {side_p} {qty_p} shares (value {mv_p})")
    lines.append("")

    # Current symbol position
    lines.append("=== POSITION STATUS ===")
    lines.append(f"Symbol: {symbol}")
    if position:
        side = position.get('side')
        qty = position.get('qty') or position.get('quantity')
        avg_entry = position.get('avg_entry_price') or 0
        mkt_value = position.get('market_value') or 0
        lines.append(f"Position: {side} ({qty} shares)")
        lines.append(f"Entry Price: {_fmt_money(avg_entry)}")
        lines.append(f"Market Value: {_fmt_money(mkt_value)}")
    else:
        lines.append("Position: None")
    lines.append("")

    # Performance metrics
    lines.append("=== PERFORMANCE METRICS (30d) ===")
    if perf:
        lines.append(f"Total Return: {_fmt_pct(perf.get('total_return', 0))}")
        if 'total_return_pct' in perf:
            lines.append(f"Total Return (reported): {perf.get('total_return_pct'):.2f}%")
        if 'sharpe_ratio' in perf:
            lines.append(f"Sharpe Ratio: {perf.get('sharpe_ratio'):.2f}")
        if 'max_drawdown' in perf:
            lines.append(f"Max Drawdown: {_fmt_pct(perf.get('max_drawdown', 0))}")
        if 'volatility' in perf:
            lines.append(f"Volatility: {perf.get('volatility'):.2f}")
    else:
        lines.append("No performance data available.")
    lines.append("")

    # Placeholder sections for future history data
    lines.append("=== POSITION HISTORY (Context) ===")
    if position_history:
        lines.append(f"Entries: {len(position_history)} (showing latest 5)")
        for entry in position_history[:5]:
            ts = entry.get('timestamp') or entry.get('date') or ''
            pnl_pct = entry.get('unrealized_pnl_pct') or entry.get('pnl_pct') or 0
            lines.append(f"- {ts}: PnL {pnl_pct:.2f}%")
    else:
        lines.append("No position history loaded in context.")
    lines.append("")

    lines.append("=== TRADE HISTORY (Context) ===")
    if trade_history:
        lines.append(f"Trades: {len(trade_history)} (showing latest 5)")
        for trade in trade_history[:5]:
            ts = trade.get('timestamp', '')
            action = trade.get('action', '')
            qty = trade.get('quantity', '')
            price = trade.get('price', '')
            reason = trade.get('reason', '')
            lines.append(f"- {ts}: {action} {qty} @ {price} ({reason})")
    else:
        lines.append("No trade history loaded in context.")
    lines.append("")

    # Recent news with headlines and summaries
    lines.append("=== RECENT NEWS ===")
    if news:
        for a in news[:10]:
            headline = a.get('headline', 'Unknown')
            created_at = a.get('created_at', '')
            summary = a.get('summary') or a.get('content') or ''
            if summary and len(summary) > 200:
                summary = summary[:200] + "..."
            lines.append(f"- {headline} ({created_at})")
            if summary:
                lines.append(f"  Summary: {summary}")
    else:
        lines.append("No recent news found.")

    return "\n".join(lines)


def format_portfolio_context_for_prompt(context: Dict[str, Any]) -> str:
    """
    Format a portfolio-level context dict into a readable text block for prompts.

    Expected keys in context:
      - portfolio: dict with equity, cash, positions
      - positions: list of position dicts
      - tracking_symbols: list or set of symbols in the universe/watchlist
      - news_by_symbol: mapping symbol -> list of news articles
    """
    lines: List[str] = []

    portfolio = context.get("portfolio") or {}
    positions: List[Dict[str, Any]] = context.get("positions") or []
    tracking_symbols: Set[str] = set(context.get("tracking_symbols") or [])
    news_by_symbol: Dict[str, List[Dict[str, Any]]] = context.get("news_by_symbol") or {}

    # Portfolio overview
    lines.append("=== PORTFOLIO OVERVIEW ===")
    lines.append(f"Equity: {_fmt_money(float(portfolio.get('equity', 0) or 0))}")
    lines.append(f"Cash: {_fmt_money(float(portfolio.get('cash', 0) or 0))}")
    lines.append(f"Number of Open Positions: {len(positions)}")
    lines.append("")

    # Open positions detail
    lines.append("=== OPEN POSITIONS ===")
    if positions:
        for pos in positions:
            symbol = pos.get("symbol", "UNKNOWN")
            quantity = abs(float(pos.get("qty", 0) or pos.get("quantity", 0) or 0))
            side = "LONG" if float(pos.get("qty", 0) or pos.get("quantity", 0) or 0) > 0 else "SHORT"
            market_value = _fmt_money(float(pos.get("market_value", 0) or 0))
            lines.append(f"- {symbol}: {side} {quantity} (value {market_value})")
    else:
        lines.append("No open positions.")
    lines.append("")

    # Tracking / wishlist symbols
    lines.append("=== WATCHLIST & TRACKED SYMBOLS ===")
    watchlist_only = sorted(sym for sym in tracking_symbols if sym and sym not in {p.get("symbol") for p in positions})
    if watchlist_only:
        lines.append("Tracked symbols without an open position:")
        for sym in watchlist_only:
            lines.append(f"- {sym}")
    else:
        lines.append("No additional tracked symbols without positions.")
    lines.append("")

    # News by symbol (only for symbols we hold or track)
    lines.append("=== RECENT NEWS BY SYMBOL ===")
    if news_by_symbol:
        for symbol, articles in news_by_symbol.items():
            if not articles:
                continue
            lines.append(f"- {symbol}:")
            for article in articles[:3]:
                headline = article.get("headline", "Unknown")
                created_at = article.get("created_at", "")
                summary = article.get("summary") or article.get("content") or ""
                if summary and len(summary) > 160:
                    summary = summary[:160] + "..."
                lines.append(f"  * {headline} ({created_at})")
                if summary:
                    lines.append(f"    Summary: {summary}")
    else:
        lines.append("No recent news available for tracked symbols.")

    return "\n".join(lines)


def main():
    """Simple CLI test for data_context module."""
    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    context = build_analysis_context(symbol)
    formatted = format_context_for_prompt(context)

    print(f"\n=== FORMATTED CONTEXT FOR {symbol} ===")
    print(formatted)


if __name__ == "__main__":
    main()
