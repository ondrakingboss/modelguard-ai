"""
Demo audit results — generated at startup using the current audit engine.
This ensures the demo always reflects the live scoring and explanation logic.
"""

from pathlib import Path
from typing import Any

from audit_engine import audit_workbook
from models import AuditResult
from parser import parse_excel_file

_SAMPLE_PATH = Path(__file__).resolve().parent / ".." / "sample_model.xlsx"
_CACHED: Any = None


def get_demo_audit_result() -> AuditResult:
    """Return a demo audit result from the sample model, with live score explanation."""
    global _CACHED

    if _CACHED is None:
        try:
            path = _SAMPLE_PATH.resolve()
            if path.exists():
                parsed = parse_excel_file(path)
                _CACHED = audit_workbook(parsed)
            else:
                _CACHED = _fallback()
        except Exception:
            _CACHED = _fallback()

    return _CACHED


def _fallback() -> AuditResult:
    """Minimal fallback if sample model is unavailable."""
    from models import Issue, SeverityBreakdown

    return AuditResult(
        model_score=100,
        summary="Demo model unavailable. Upload your own workbook to see an audit.",
        severity_breakdown=SeverityBreakdown(),
        issues=[
            Issue(
                id="demo_fallback",
                severity="low",
                sheet="—",
                cell="—",
                category="Demo",
                title="Demo model not found",
                description="The sample model file could not be loaded. The audit engine is ready for uploads.",
                why_it_matters="This only affects the demo preview — uploaded workbooks are processed normally.",
                suggested_fix="Upload your own .xlsx workbook to see a full audit.",
            )
        ],
    )