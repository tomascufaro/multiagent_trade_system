# Analyst Service Refactor - Implementation Plan

## Overview

Refactor the analyst service into a simple, **portfolio‑level**, analysis‑only pipeline that:
- Builds a rich DB‑backed **portfolio context** via `data_context.py` and `DataManager`.
- Runs a single bull vs bear **portfolio debate** using CrewAI agents.
- Returns an informative **portfolio report** (no trading actions) suggesting how to adjust holdings and wishlist.

---

## Goals

- Keep the system focused on **portfolio‑level insight**, not order generation.
- Reuse existing components (`DataManager`, `data_context`, bull/bear agents, `TradingCrew`) where they still fit.
- Minimize moving parts in the main flow (one main debate per run).
- Make it easy to call a single entrypoint, e.g. `AnalystService().analyze_portfolio()`.

---

## Target Architecture (v2 Analyst Service)

### New High‑Level Interface

Extend or adapt `AnalystService` in `analyst_service/analysis/analyst_service.py` to support a portfolio‑centric API:

```python
analysis = AnalystService().analyze_portfolio()

# Example return shape
{
  "portfolio": { ... },        # Portfolio summary (equity, cash, positions)
  "universe": { ... },         # Tracked symbols, incl. wishlist
  "context": { ... },          # Structured context used in prompts
  "debate": { ... },           # MarketAnalysis dict from a portfolio‑level debate
  "summary": "...",            # High‑level portfolio summary from the agents
  "timestamp": "...",
}
```

### Components Used in the New Flow

- `data_module.DataManager`:
  - `get_portfolio_summary()` → cash, equity, open positions.
  - `get_all_tracking_symbols()` / universe repo → watchlist and other tracked symbols.
- `analyst_service/data_context.py`:
  - `build_analysis_context(symbol)` remains available for symbol‑level context if needed.
  - Add or reuse helpers to build a **portfolio‑level context dict** (aggregating portfolio, positions, wishlist, and recent news for relevant symbols).
  - `format_context_for_prompt(context)` (or a new portfolio‑oriented formatter) is used to generate a single prompt block for the debate.
- `analyst_service/agents`:
  - Reuse existing bull/bear agents, but with **portfolio‑level tasks** (they read a portfolio context block instead of a single‑symbol context).
  - Extend `DebateManager` or add a simple portfolio debate entry that creates one Crew with a single portfolio‑level debate task.

### Components Removed from the Main Path

- `SentimentAgent` and OpenAI‑heavy sentiment calls are **not** part of the default pipeline.
- Symbol‑level trading recommendation logic (`BUY/SELL/CLOSE_*`) remains deprecated.
- Action‑oriented fields (`action`, `position_context`, etc.) are removed from the main result; instead we keep descriptive portfolio suggestions in natural language.

---

## Phase 1 – Implement Portfolio‑Level AnalystService

**File**: `analyst_service/analysis/analyst_service.py`

1. Extend `AnalystService` with a portfolio‑centric method:
   - `__init__(config_path='analyst_service/config/settings.yaml')` already wires `DataManager` and `DebateManager`.
   - Add `analyze_portfolio(self) -> Dict[str, Any]`:
     - Get portfolio overview via `DataManager.get_portfolio_summary()`.
     - Get tracking symbols / universe via `DataManager.get_all_tracking_symbols()` (or universe repo).
     - Build a **portfolio context dict** that includes:
       - Portfolio snapshot (equity, cash, overall performance if available).
       - List of open positions (symbol, size, unrealized P&L if available).
       - Wishlist / tracked symbols (with a flag indicating no current position).
       - Optional recent news for current positions and wishlisted symbols.
     - Format this into a prompt text block (reuse or extend `format_context_for_prompt` for portfolio use).
     - Call a portfolio‑level debate method (see Phase 2) with this context text.
     - Construct final analysis dict:
       - `portfolio`, `universe`, `context`, `debate`, `summary`, `timestamp`.

2. Keep symbol‑level `analyze(symbol)` as a possible future helper if needed, but the main path becomes `analyze_portfolio()`.

---

## Phase 2 – Portfolio‑Level Debate Orchestration

**File**: `analyst_service/agents/debate_manager.py` (or a small new helper alongside it)

1. Adapt debate management for portfolio context:
   - Extend `DebateManager` with a new method `conduct_portfolio_debate(context_text: str)` that:
     - Uses the existing bull/bear agents.
     - Creates **one task each** where the description includes the full portfolio context text and clear portfolio‑level instructions.
   - The debate topic becomes: “Given this portfolio and wishlist, what adjustments (add/trim/hold/avoid) make sense overall?” (described textually, not as explicit orders).

2. Return a `MarketAnalysis` structure as today, but interpreted at portfolio level:
   - `bull_case` and `bear_case` list arguments and conviction about being more risk‑on vs risk‑off.
   - `market_bias` expresses the tilt toward risk‑taking or de‑risking.
   - `summary` is a concise portfolio‑level explanation.

3. Wire `AnalystService.analyze_portfolio()` to call this portfolio debate and embed its result in the final analysis dict.

---

## Phase 3 – Wire CLI to Portfolio‑Level Analysis

**File**: `analyst_service/main.py`

1. Use `AnalystService.analyze_portfolio()` in `analyst_service/main.py`:
   - `from analyst_service.analysis.analyst_service import AnalystService`.
   - Construct `AnalystService()` and call `analysis = analyst.analyze_portfolio()`.

2. CLI output reflects **portfolio focus**:
   - Print timestamp and basic portfolio metrics (equity, cash, number of positions).
   - Print portfolio‑level debate results:
     - Bull vs bear convictions.
     - Market bias (risk‑on vs risk‑off).
     - Summary explaining suggested portfolio stance.
   - Optionally print a short bullet list of “focus symbols” mentioned in the debate arguments.

3. Do **not** print explicit trade instructions (no `BUY/SELL/CLOSE_*`). The output remains descriptive suggestions.

---

## Phase 4 – Deprecate Legacy MarketAnalyzer & Trading Logic

1. Ensure any legacy trading‑oriented logic (e.g. `MarketAnalyzer`, recommendation generators) is not used in the new portfolio flow.
2. Keep any sentiment‑specific components as optional tools only:
   - No instantiation in `AnalystService` by default.
   - Leave them available for future advanced pipelines or offline sentiment runs.

---

## Phase 5 – Cleanup & Documentation

1. Remove or update trading‑oriented text in:
   - `README.md` section describing the Analyst Service (focus on debate and insights, not trade execution).
   - Any references to `MarketAnalyzer` as the primary entrypoint; replace with `AnalystService`.

2. Update `CHANGELOG.md` to note the shift to portfolio‑level analysis.

---

## Future Enhancements (Backlog)

- Add an optional, pluggable sentiment layer:
  - Use a sentiment helper or agent to compute a real `sentiment_data` structure for the portfolio or key symbols.
  - Feed it into the portfolio‑level debate alongside TA and DB context.
- Add optional per‑symbol deep dives:
  - For a small set of focus symbols, call a symbol‑level debate flow to augment the portfolio report when needed.
