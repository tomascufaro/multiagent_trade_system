#!/usr/bin/env python3
"""Generate and email the weekly portfolio report."""
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "shared"))

from analyst_service.analysis.analyst_service import AnalystService
from analyst_service.reporting import render_html_report, send_html_email
from shared.formatting import setup_logger

logger = setup_logger("generate_report")


load_dotenv()


def _save_report_files(
    output_dir: Path, analysis: Dict, text_report: str, html_report: str
) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_timestamp = analysis.get("timestamp") or datetime.now().isoformat()
    sanitized_timestamp = raw_timestamp.replace(":", "").replace("-", "").split(".")[0]
    base_path = output_dir / f"weekly_report_{sanitized_timestamp}"

    html_path = base_path.with_suffix(".html")
    text_path = base_path.with_suffix(".txt")

    html_path.write_text(html_report, encoding="utf-8")
    text_path.write_text(text_report, encoding="utf-8")

    return {"html": html_path, "text": text_path}


def generate_and_send_report(
    analyst_service: Optional[AnalystService] = None, output_dir: Optional[Path] = None
) -> Dict[str, Path]:
    """Run the portfolio analysis, render HTML, send email, and persist artifacts."""
    analyst = analyst_service or AnalystService()
    report_dir = output_dir or PROJECT_ROOT / "data" / "reports"

    logger.info("Starting weekly portfolio analysis")
    analysis = analyst.analyze_portfolio()

    text_report = analysis.get("report") or ""
    html_report = render_html_report(text_report, analysis)
    subject = f"Weekly Portfolio Report – {datetime.now().strftime('%Y-%m-%d')}"

    logger.info("Sending HTML email")
    send_html_email(subject, html_report)

    logger.info("Saving report artifacts to %s", report_dir)
    saved_paths = _save_report_files(report_dir, analysis, text_report, html_report)

    logger.info("Report generation complete")
    return saved_paths


def main():
    try:
        paths = generate_and_send_report()
        print(f"HTML report saved to: {paths['html']}")
        print(f"Text report saved to: {paths['text']}")
    except Exception as exc:
        logger.error("Report generation failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
