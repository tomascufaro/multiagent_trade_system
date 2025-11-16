"""Portfolio Report Writer - second-layer agent to turn debate into a narrative report."""
from typing import Dict, Any

from crewai import Agent, Task, Crew, Process


class ReportWriter:
    def __init__(self, model: str = "gpt-4.1-nano"):
        self.agent = Agent(
            role="Portfolio Report Writer",
            goal=(
                "Produce clear, concise portfolio reports that turn bull/bear debates "
                "into practical guidance for an individual investor."
            ),
            backstory=(
                "You are a senior discretionary portfolio manager. You read structured "
                "analysis (bull and bear cases) and portfolio context, then write a "
                "short, focused note explaining what the investor should consider "
                "doing with their positions and watchlist, and why."
            ),
            tools=[],
            verbose=False,
            allow_delegation=False,
            max_iter=3,
            llm=model,
        )

    def write_portfolio_report(self, context_text: str, debate: Dict[str, Any]) -> str:
        """Generate a human-readable portfolio report from context and debate output."""
        bull = debate.get("bull_case") or {}
        bear = debate.get("bear_case") or {}
        market_bias = debate.get("market_bias", 0.0)

        description = f"""You are writing a portfolio report for an individual investor.

You are given:
1) A portfolio context text block with equity, cash, positions, tracked symbols, and recent news.
2) A bull case JSON object (arguments, conviction, recommendation) from a bullish analyst.
3) A bear case JSON object (arguments, conviction, recommendation) from a bearish analyst.
4) A numeric market_bias value (bull conviction minus bear conviction).

Your task:
- Write a concise portfolio report (3–7 short paragraphs).
- Start with the overall stance (e.g. slightly bearish, neutral, slightly bullish) and why.
- For the most important CURRENT positions, clearly say whether to keep, reduce, or add, using those verbs explicitly, and give the 1–3 strongest arguments for that view.
- Treat tracked / wishlist symbols as secondary: mention at most 1–3 of the strongest opportunities or clear avoids from this list, again with reasons.
- Use the arguments from the bull and bear cases and any obvious signals from the portfolio context. Do not invent facts.
- Do NOT mention that there was a bull/bear debate, tools, or internal implementation details. Just present the final reasoning as your own judgment.

Portfolio context:
{context_text}

Bull case JSON:
{bull}

Bear case JSON:
{bear}

Market bias: {market_bias}
"""

        task = Task(
            description=description,
            agent=self.agent,
            expected_output=(
                "A short, human-readable portfolio report in 3–7 paragraphs, "
                "covering overall stance and key position/watchlist guidance."
            ),
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )

        results = crew.kickoff()

        # Best-effort extraction of the text output from the first task
        task_output = results.tasks_output[0]
        text = None
        for attr in ("raw", "output", "value"):
            if hasattr(task_output, attr):
                candidate = getattr(task_output, attr)
                if isinstance(candidate, str):
                    text = candidate
                    break

        if text is None:
            text = str(task_output)

        return text.strip()

