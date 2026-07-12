"""Tests for scoring calibration and finding consolidation."""

import pytest
from audit_engine import (
    _build_score_explanation,
    _consolidate_related,
    _score_model,
    _worse_severity,
    _collapse_row_noise,
)
from models import Issue, SeverityBreakdown


def _make(
    id: str,
    severity: str = "medium",
    category: str = "Formula Integrity",
    title: str = "Test issue",
    sheet: str = "Sheet1",
    cell: str = "A1",
) -> Issue:
    return Issue(
        id=id,
        severity=severity,
        sheet=sheet,
        cell=cell,
        category=category,
        title=title,
        description="Test",
        why_it_matters="Test",
        suggested_fix="Test",
    )


def _bd(issues: list[Issue]) -> SeverityBreakdown:
    crit = sum(1 for i in issues if i.severity == "critical")
    high = sum(1 for i in issues if i.severity == "high")
    med = sum(1 for i in issues if i.severity == "medium")
    low = sum(1 for i in issues if i.severity == "low")
    return SeverityBreakdown(critical=crit, high=high, medium=med, low=low)


# ── Scoring ──

def test_20_medium_does_not_force_zero():
    issues = [_make(f"m{i}") for i in range(20)]
    score = _score_model(issues, _bd(issues))
    assert score > 0, f"Got {score}"


def test_critical_high_medium_nonzero():
    issues = [_make("c1", "critical", "Formula Error", "Formula error #REF!")]
    issues += [_make(f"h{i}", "high", "Circular Reference", f"Circular ref {i}") for i in range(4)]
    issues += [_make(f"m{i}", "medium") for i in range(22)]
    score = _score_model(issues, _bd(issues))
    assert score > 0


def test_medium_capped():
    issues = [_make(f"m{i}") for i in range(100)]
    score = _score_model(issues, _bd(issues))
    assert score >= 60, f"Expected >=60, got {score}"


def test_circular_caps_score():
    issues = [_make("cr", "high", "Circular Reference", "Circular reference pair")]
    score = _score_model(issues, _bd(issues))
    assert score <= 60


def test_empty_scores_100():
    score = _score_model([], SeverityBreakdown())
    assert score == 100


def test_explanation_has_caps_and_drivers():
    issues = [
        _make("c1", "critical", "Formula Error", "Formula error"),
        _make("cr", "high", "Circular Reference", "Circular reference pair"),
    ]
    bd = _bd(issues)
    exp = _build_score_explanation(50, issues, bd)
    assert exp.score_band
    assert len(exp.main_drivers) > 0
    assert len(exp.floor_rules_applied) > 0
    assert exp.why_not_lower
    assert exp.why_not_higher


# ── Consolidation ──

def test_merge_hardcoded_inconsistent_same_cell():
    issues = [
        _make("hc", "medium", title="Hardcoded constant inside formula", cell="D6"),
        _make("inc", "medium", title="Inconsistent neighboring formula", cell="D6"),
        _make("other", "medium", cell="E6"),
    ]
    result = _consolidate_related(issues)
    assert len(result) == 2
    assert any("embedded" in i.title.lower() for i in result)


def test_hardcoded_only_passes_through():
    issues = [_make("hc", title="Hardcoded constant inside formula", cell="D6")]
    result = _consolidate_related(issues)
    assert len(result) == 1
    assert "Hardcoded" in result[0].title


def test_unrelated_not_merged():
    issues = [
        _make("hc", title="Hardcoded constant", cell="D6"),
        _make("inc", title="Inconsistent formula", cell="E6"),
    ]
    result = _consolidate_related(issues)
    assert len(result) == 2


# ── Row Collapse ──

def test_collapse_three_adjacent():
    issues = [
        _make("a", title="Hardcoded constant inside formula", cell="B7"),
        _make("b", title="Hardcoded constant inside formula", cell="C7"),
        _make("c", title="Hardcoded constant inside formula", cell="D7"),
    ]
    result = _collapse_row_noise(issues)
    assert len(result) == 1
    assert "×" in result[0].title


def test_no_collapse_two_cells():
    issues = [
        _make("a", title="Hardcoded constant", cell="B7"),
        _make("b", title="Hardcoded constant", cell="C7"),
    ]
    result = _collapse_row_noise(issues)
    assert len(result) == 2


# ── Severity ──

def test_worse_severity():
    assert _worse_severity("low", "medium") == "medium"
    assert _worse_severity("critical", "low") == "critical"