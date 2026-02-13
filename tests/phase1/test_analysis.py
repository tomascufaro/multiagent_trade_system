import sqlite3
import sys
import types

from data_module.data_manager import DataManager

# Stub crewai to avoid importing external dependency during tests.
fake_crewai = types.ModuleType("crewai")

class _FakeCrewAI:
    def __init__(self, *args, **kwargs):
        pass

fake_crewai.Agent = _FakeCrewAI
fake_crewai.Task = _FakeCrewAI
fake_crewai.Crew = _FakeCrewAI
class _FakeProcess:
    sequential = "sequential"

fake_crewai.Process = _FakeProcess
fake_crewai_tools = types.ModuleType("crewai.tools")
fake_crewai_tools.tool = lambda *args, **kwargs: (lambda f: f)
sys.modules.setdefault("crewai", fake_crewai)
sys.modules.setdefault("crewai.tools", fake_crewai_tools)

from analyst_service.analysis import analyst_service as analyst_mod


def test_analysis_persists(tmp_path, monkeypatch):
    db_path = tmp_path / "portfolio.db"
    monkeypatch.setenv("PORTFOLIO_DB_PATH", str(db_path))

    def fake_analyze(self, symbol):
        return {
            "debate": {
                "summary": "Strong buy due to momentum",
                "confidence": 0.9,
                "bull_perspective": "Bull case",
                "bear_perspective": "Bear case",
            },
            "ta_signals": {"rsi": 55},
        }

    monkeypatch.setattr(analyst_mod.AnalystService, "analyze", fake_analyze)

    dm = DataManager()
    monkeypatch.setattr(dm.price_feed, "get_current_price", lambda symbol: 123.45)

    analysis = dm.analyze_stock("AAPL")
    assert analysis["recommendation"] in {"STRONG_BUY", "BUY"}

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM asset_analysis WHERE symbol = ?", ("AAPL",))
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 1
