from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["low", "medium", "high", "critical"]


class Issue(BaseModel):
    id: str
    severity: Severity
    sheet: str
    cell: str
    category: str
    title: str
    description: str
    why_it_matters: str
    suggested_fix: str


class SeverityBreakdown(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0


class ScoreExplanation(BaseModel):
    score: int = Field(ge=0, le=100)
    score_band: str
    main_drivers: list[str]
    penalty_breakdown: dict[str, int]
    caps_applied: list[str]
    floor_rules_applied: list[str]
    why_not_lower: str
    why_not_higher: str


class AuditResult(BaseModel):
    model_score: int = Field(ge=0, le=100)
    summary: str
    issues: list[Issue]
    severity_breakdown: SeverityBreakdown
    score_explanation: ScoreExplanation | None = None


class HealthCheck(BaseModel):
    status: str
    service: str