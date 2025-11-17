"""HTML renderer for portfolio analysis reports."""
from datetime import datetime
from html import escape
from typing import Any, Dict, Iterable, List


def _format_currency(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def _format_timestamp(timestamp: str) -> str:
    try:
        parsed = datetime.fromisoformat(timestamp)
        return parsed.strftime("%Y-%m-%d %H:%M %Z") or timestamp
    except (TypeError, ValueError):
        return datetime.now().strftime("%Y-%m-%d %H:%M")


def _render_positions(positions: Iterable[Dict[str, Any]]) -> str:
    visible_positions: List[Dict[str, Any]] = list(positions)[:5]
    if not visible_positions:
        return "<p>No open positions.</p>"

    rows = []
    for position in visible_positions:
        symbol = escape(str(position.get("symbol", "")))
        side = escape(str(position.get("side", "")).upper())
        qty = position.get("qty") or position.get("quantity") or position.get("qty_available")
        quantity_display = f"{qty}" if qty not in (None, "") else "-"
        avg_entry = _format_currency(position.get("avg_entry_price"))
        market_value = _format_currency(position.get("market_value"))
        rows.append(
            f"<tr><td>{symbol}</td><td>{side}</td><td>{quantity_display}</td>"
            f"<td>{avg_entry}</td><td>{market_value}</td></tr>"
        )

    table_header = (
        "<table class='positions'>"
        "<thead><tr><th>Symbol</th><th>Side</th><th>Qty</th><th>Avg Entry</th><th>Market Value</th></tr></thead>"
        "<tbody>"
    )
    return table_header + "".join(rows) + "</tbody></table>"


def render_html_report(text_report: str, analysis: Dict[str, Any]) -> str:
    """
    Wrap the plain-text portfolio report and metrics into an HTML document.
    """
    portfolio = analysis.get("portfolio") or {}
    positions = portfolio.get("positions") or []
    summary = analysis.get("summary", "")
    timestamp = analysis.get("timestamp") or datetime.now().isoformat()
    generated_at = _format_timestamp(timestamp)

    equity_display = _format_currency(portfolio.get("equity"))
    cash_display = _format_currency(portfolio.get("cash"))
    open_positions = len(positions)
    universe = analysis.get("universe") or []

    summary_block = escape(summary) if summary else "No debate summary provided."
    narrative = escape(text_report) if text_report else "Report content unavailable."
    narrative = narrative.replace("\n", "<br>")

    positions_table = _render_positions(positions)

    html_body = f"""
    <html>
      <head>
        <meta charset='UTF-8'>
        <style>
          body {{ font-family: Arial, sans-serif; background: #f9fafb; color: #0f172a; margin: 0; padding: 24px; }}
          .container {{ background: #ffffff; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08); }}
          h1 {{ margin-top: 0; color: #111827; }}
          h2 {{ margin-bottom: 8px; color: #111827; }}
          .metrics {{ display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 16px; }}
          .metric {{ background: #f3f4f6; border-radius: 10px; padding: 12px 16px; min-width: 160px; }}
          .label {{ font-size: 12px; text-transform: uppercase; color: #6b7280; letter-spacing: 0.05em; }}
          .value {{ font-size: 20px; font-weight: 700; color: #111827; }}
          .section {{ margin-top: 24px; }}
          table.positions {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
          table.positions th, table.positions td {{ border: 1px solid #e5e7eb; padding: 8px; text-align: left; }}
          table.positions th {{ background: #f9fafb; font-size: 12px; color: #374151; text-transform: uppercase; }}
          footer {{ margin-top: 32px; font-size: 12px; color: #6b7280; }}
        </style>
      </head>
      <body>
        <div class='container'>
          <header>
            <h1>Weekly Portfolio Report</h1>
            <p>Generated: {generated_at}</p>
          </header>
          <section class='metrics'>
            <div class='metric'><div class='label'>Equity</div><div class='value'>{equity_display}</div></div>
            <div class='metric'><div class='label'>Cash</div><div class='value'>{cash_display}</div></div>
            <div class='metric'><div class='label'>Open Positions</div><div class='value'>{open_positions}</div></div>
            <div class='metric'><div class='label'>Tracked Symbols</div><div class='value'>{len(universe)}</div></div>
          </section>
          <section class='section'>
            <h2>Debate Summary</h2>
            <p>{summary_block}</p>
          </section>
          <section class='section'>
            <h2>Portfolio Narrative</h2>
            <p>{narrative}</p>
          </section>
          <section class='section'>
            <h2>Positions Snapshot</h2>
            {positions_table}
          </section>
          <footer>
            <p>This report was generated automatically by the Analyst Service.</p>
          </footer>
        </div>
      </body>
    </html>
    """

    return "".join(line.strip() for line in html_body.splitlines())
