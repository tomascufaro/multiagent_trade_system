# Next Implementation Plan – Weekly Report + Email

## 1. Reporting & Email Modules (analyst_service)

- Add `analyst_service/reporting/html_renderer.py`:
  - Implement `render_html_report(text_report, analysis)` to wrap the plain-text portfolio report and key portfolio metrics into a simple HTML string with inline styles (header, sections, footer).
- Add `analyst_service/reporting/email_sender.py`:
  - Implement `send_html_email(subject, html_body)` using SMTP, configured via env vars (`SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `REPORT_FROM`, `REPORT_TO`).
- Tests (unit-level):
  - Unit test for `render_html_report` using dummy text + analysis to assert an HTML string is returned and key fields (e.g. date, equity, cash) appear in the body.
  - Unit test for `send_html_email` that mocks `smtplib.SMTP` and asserts the expected SMTP calls are made without sending real email.

## 2. Report Generation Script

- Create `scripts/generate_report.py`:
  - Call `AnalystService().analyze_portfolio()` to get structured analysis, including the `report` text.
  - Pass `analysis["report"]` and the full analysis dict into `render_html_report` to produce the HTML body.
  - Send the email via `send_html_email`, using a subject like `Weekly Portfolio Report – <date>`.
  - Optionally save the HTML (and/or text report) under `data/reports/` for historical reference.
- Test (integration-lite, local):
  - Add a small test or helper that runs the generate-report flow with a mocked `AnalystService` and mocked `send_html_email`, asserting the HTML is generated and `send_html_email` is called once, without hitting real APIs or SMTP.

## 3. Weekly GitHub Actions Workflow

- Add `.github/workflows/portfolio-report.yml`:
  - Triggers:
    - `schedule`: `0 22 * * 5` (weekly Friday report after market close snapshots).
    - `workflow_dispatch` for manual runs.
  - Steps:
    - Checkout, set up Python 3.12, install Poetry and main deps.
    - Run `scripts/generate_report.py` with API keys + email settings provided via GitHub secrets.
- Manual check:
  - Trigger the workflow once via `workflow_dispatch` in GitHub, verify the job succeeds and logs show the report was generated and the email send was attempted.

## 4. Documentation & Changelog

- Update `README.md`:
  - Describe the portfolio-level analyst service, the weekly HTML email report, and how to configure the required env vars and GitHub secrets.
- Update `CHANGELOG.md`:
  - Add an entry summarizing:
    - The new weekly portfolio report workflow.
    - HTML email report + SMTP integration.
    - Any new env variables/secrets required.
- Manual check:
  - After the first successful weekly run, confirm README instructions match actual behavior and that the CHANGELOG entry accurately reflects the new workflow and configuration.

