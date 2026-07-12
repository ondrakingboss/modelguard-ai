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
    impact: str = "unknown",
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
        output_impact=impact,
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


# ── Materiality / Output Impact ──

def test_critical_with_unknown_impact_not_zero():
    """Critical with unknown impact should not automatically force 0-9."""
    issues = [
        _make("c1", "critical", "Formula Error", impact="unknown"),
    ]
    score = _score_model(issues, _bd(issues))
    assert score >= 50, f"Unknown-impact critical should score >=50, got {score}"


def test_critical_with_high_impact_can_be_low():
    """Critical with high output impact can score much lower."""
    issues = [
        _make("c1", "critical", "Formula Error", impact="high"),
        _make("cr", "high", "Circular Reference", impact="medium"),
    ]
    score = _score_model(issues, _bd(issues))
    assert score < 60, f"High-impact critical scores below 60, got {score}"


def test_hidden_empty_rows_dont_tank_score():
    """Hidden empty rows with low impact should barely affect score."""
    issues = [
        _make("h1", "low", "Hidden Content", impact="low"),
        _make("h2", "low", "Hidden Content", impact="low"),
        _make("h3", "low", "Hidden Content", impact="low"),
    ]
    score = _score_model(issues, _bd(issues))
    assert score >= 90, f"Hidden empty rows should barely affect score, got {score}"


def test_meddevice_like_profile_severe_not_critical():
    """MedDevice-like: 1c+5h+20m, mixed impact → should be Severe Risk (10-24)."""
    issues = [
        _make("c1", "critical", "Formula Error", sheet="P&L", impact="high"),
    ]
    issues += [
        _make(f"h{i}", "high", "Circular Reference", sheet="Assumptions", impact="medium")
        for i in range(2)
    ]
    issues += [
        _make(f"hh{i}", "high", "Hidden Content", impact="medium")
        for i in range(3)
    ]
    issues += [
        _make(f"m{i}", "medium", impact="low")
        for i in range(20)
    ]
    score = _score_model(issues, _bd(issues))
    assert 10 <= score <= 30, (
        f"MedDevice profile should land 10-30 (Severe Risk), got {score}"
    )


def test_circular_with_unknown_impact_differs_from_key_output():
    """Formula Error with unknown impact scores higher than with high impact."""
    unknown = [
        _make("c1", "high", "Formula Error", impact="unknown"),
    ]
    known = [
        _make("c1", "high", "Formula Error", impact="high"),
    ]
    score_unknown = _score_model(unknown, _bd(unknown))
    score_known = _score_model(known, _bd(known))
    # 1 high × 12 × 0.5(unknown) = 6 → 94 vs 1 high × 12 × 1.0(high) = 12 → 88
    assert score_unknown > score_known, (
        f"Unknown-impact should score higher than high-impact, got {score_unknown} vs {score_known}"
    )


def test_what_is_known_includes_impact_counts():
    """Score explanation includes known/unknown impact counts."""
    issues = [
        _make("c1", "critical", "Formula Error", impact="high", sheet="P&L"),
        _make("m1", "medium", impact="unknown"),
        _make("m2", "medium", impact="low"),
    ]
    bd = _bd(issues)
    exp = _build_score_explanation(50, issues, bd)
    assert exp.what_is_known
    assert exp.what_is_unknown
    assert "could not be classified" in exp.what_is_unknown.lower()


def test_no_critical_language_in_unknown_model():
    """A model with unknown impact should not use fraud-like language."""
    issues = [
        _make("m1", "medium", impact="unknown"),
        _make("m2", "medium", impact="unknown"),
    ]
    bd = _bd(issues)
    score = _score_model(issues, bd)
    exp = _build_score_explanation(score, issues, bd)
    assert "fraud" not in exp.why_not_higher.lower()
    assert "fraud" not in exp.why_not_lower.lower()