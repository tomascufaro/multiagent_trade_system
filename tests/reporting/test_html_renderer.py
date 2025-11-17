import unittest

from analyst_service.reporting.html_renderer import render_html_report


class RenderHtmlReportTests(unittest.TestCase):
    def test_render_includes_metrics_and_body(self):
        analysis = {
            "portfolio": {"equity": 10000, "cash": 2500, "positions": [{"symbol": "AAPL", "qty": 10, "side": "long", "avg_entry_price": 150, "market_value": 1550}]},
            "summary": "Slightly bullish due to cash buffer.",
            "timestamp": "2024-05-05T12:00:00",
            "universe": ["AAPL", "MSFT"],
        }
        html = render_html_report("Portfolio looks balanced.\nConsider trimming winners.", analysis)

        self.assertIsInstance(html, str)
        self.assertIn("Weekly Portfolio Report", html)
        self.assertIn("2024-05-05", html)
        self.assertIn("$10,000.00", html)
        self.assertIn("$2,500.00", html)
        self.assertIn("Slightly bullish", html)
        self.assertIn("Portfolio looks balanced.", html)


if __name__ == "__main__":
    unittest.main()
