import sys
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

fake_models = types.ModuleType("models")
fake_models.AgentAnalysis = MagicMock()
fake_models.MarketAnalysis = MagicMock()
sys.modules.setdefault("models", fake_models)

from scripts import generate_report


class GenerateReportFlowTests(unittest.TestCase):
    def test_generate_report_flow_renders_and_sends(self):
        fake_analysis = {
            "report": "Text report body",
            "summary": "Debate summary",
            "timestamp": "2024-05-05T12:00:00",
            "portfolio": {"equity": 10000, "cash": 2000, "positions": []},
            "universe": ["AAPL"],
        }
        fake_service = MagicMock()
        fake_service.analyze_portfolio.return_value = fake_analysis

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            with patch.object(generate_report, "render_html_report", return_value="<html>body</html>") as mock_render:
                with patch.object(generate_report, "send_html_email") as mock_send_email:
                    paths = generate_report.generate_and_send_report(fake_service, output_dir)
                    mock_render.assert_called_once_with("Text report body", fake_analysis)
                    mock_send_email.assert_called_once()
                    self.assertTrue(paths["html"].exists())
                    self.assertTrue(paths["text"].exists())


if __name__ == "__main__":
    unittest.main()
