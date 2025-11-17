"""Reporting utilities for portfolio analysis outputs."""

from .html_renderer import render_html_report
from .email_sender import send_html_email

__all__ = ["render_html_report", "send_html_email"]
