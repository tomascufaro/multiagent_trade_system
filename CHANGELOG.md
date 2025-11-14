# Changelog

## Unreleased

- Added `analyst_service/data_context.py` with `build_analysis_context()` and `format_context_for_prompt()` to assemble database-backed context for agents.
- Updated `analyst_service/agents/bull_agent.py` to accept a `db_context` parameter in `create_analysis_task()`, include formatted database context in the task description, and use shared `AgentAnalysis` models and `TechnicalAnalysis` from `analyst_service/analysis/ta_signals.py`.
- Updated `analyst_service/agents/bear_agent.py` to mirror the bull agent changes: new `db_context` parameter, injected database context in prompts, and corrected imports.
- Updated `analyst_service/agents/trading_crew.py` to initialize `DataManager`, build analysis context via `build_analysis_context(symbol)`, and change `conduct_analysis()` signature to `conduct_analysis(symbol, prices, sentiment_data)` while passing `db_context` to both agents.
- Updated `analyst_service/agents/debate_manager.py` so it takes a `config_path`, constructs `TradingCrew(config_path)`, and changes `conduct_debate()` to `conduct_debate(symbol, prices, sentiment_data)`.
- Updated `analyst_service/analysis/market_analyzer.py` to pass `symbol` into `conduct_debate(symbol, prices, sentiment_data)` for the CrewAI debate step.

### Breaking changes

- `BullAgent.create_analysis_task()` and `BearAgent.create_analysis_task()` now require an additional `db_context` argument.
- `TradingCrew.conduct_analysis()` requires `symbol` as the first argument.
- `DebateManager.conduct_debate()` requires `symbol` as the first argument.

