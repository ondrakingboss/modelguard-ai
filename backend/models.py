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


class AuditResult(BaseModel):
    model_score: int = Field(ge=0, le=100)
    summary: str
    issues: list[Issue]
    severity_breakdown: SeverityBreakdown


class HealthCheck(BaseModel):
    status: str
    service: str
