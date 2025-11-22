# Changelog

## Unreleased

- Added `analyst_service/reporting/html_renderer.py` to format portfolio analyses into styled HTML and `email_sender.py` to send reports via SMTP using environment configuration.
- Created `scripts/generate_report.py` to run the portfolio analysis, render the HTML report, send the email, and archive artifacts under `data/reports/`.
- Added GitHub Actions workflow `.github/workflows/portfolio-report.yml` to send the weekly portfolio email each Friday at 22:00 UTC or on demand.
- Documented the weekly email report flow and required SMTP environment variables in `README.md` and ignored generated report artifacts under `data/reports/`.
- Added `analyst_service/data_context.py` with `build_analysis_context()` and `format_context_for_prompt()` to assemble database-backed context for agents.
- Updated `analyst_service/agents/bull_agent.py` to accept a `db_context` parameter in `create_analysis_task()`, include formatted database context in the task description, and use shared `AgentAnalysis` models and `TechnicalAnalysis` from `analyst_service/analysis/ta_signals.py`.
- Updated `analyst_service/agents/bear_agent.py` to mirror the bull agent changes: new `db_context` parameter, injected database context in prompts, and corrected imports.
- Updated `analyst_service/agents/trading_crew.py` to initialize `DataManager`, build analysis context via `build_analysis_context(symbol)`, and change `conduct_analysis()` signature to `conduct_analysis(symbol, prices, sentiment_data)` while passing `db_context` to both agents.
- Updated `analyst_service/agents/debate_manager.py` so it takes a `config_path`, constructs `TradingCrew(config_path)`, and changes `conduct_debate()` to `conduct_debate(symbol, prices, sentiment_data)`.
- Updated `analyst_service/analysis/market_analyzer.py` to pass `symbol` into `conduct_debate(symbol, prices, sentiment_data)` for the CrewAI debate step.
- Added portfolio-level context formatting via `format_portfolio_context_for_prompt()` in `analyst_service/data_context.py` to summarize portfolio, positions, tracked symbols, and news for prompts.
- Introduced `AnalystService.analyze_portfolio()` in `analyst_service/analysis/analyst_service.py` to run a single portfolio-level bull/bear debate and return a portfolio-focused report.
- Extended `BullAgent` and `BearAgent` with `create_portfolio_task()` methods for portfolio-oriented prompts, while keeping symbol-level analysis intact.
- Updated `DebateManager` with `conduct_portfolio_debate()` to orchestrate a portfolio-level CrewAI run using the new portfolio tasks.
- Updated `analyst_service/main.py` to call the portfolio-level flow and print a concise portfolio analyst report (equity, cash, positions count, and debate summary).

### Breaking changes

- `BullAgent.create_analysis_task()` and `BearAgent.create_analysis_task()` now require an additional `db_context` argument.
- `TradingCrew.conduct_analysis()` requires `symbol` as the first argument.
- `DebateManager.conduct_debate()` requires `symbol` as the first argument.

### Conversation summary

We refocused the analyst service from symbol-level trading decisions to a portfolio-level debate between bull and bear agents. The current flow builds a portfolio context (positions, cash/equity, tracked symbols, and recent news), feeds it into a single CrewAI debate via new portfolio-specific tasks, and prints a portfolio report that aggregates bull/bear arguments and summarizes overall risk stance. TA tools remain available for symbol-level analysis, but are explicitly disabled for the portfolio debate to keep this version focused on DB-backed context and news; further refinements can deepen the narrative report or reintroduce TA in a controlled way later.
