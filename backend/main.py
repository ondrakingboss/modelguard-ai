from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from audit_engine import audit_workbook
from company_diff import build_company_diff, get_available_diff_pairs, get_demo_diff
from company_intelligence import build_company_profile, get_company_industries, get_demo_profile
from confidence_analyzer import get_confidence_profile, get_available_confidence_scenarios
from evidence_explorer import enrich_insights, get_evidence
from financial_intelligence import analyze_scenario, get_available_scenarios
from mock import get_demo_audit_result
from models import AuditResult, HealthCheck
from parser import parse_excel_file
from pdf_parser import extract_financial_data, extract_tables, extract_text


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATABASE_PATH = BASE_DIR / "audits.db"

UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="ModelGuard AI Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    _init_db()


@app.get("/", response_model=HealthCheck)
def health_check() -> HealthCheck:
    return HealthCheck(status="ok", service="ModelGuard AI")


@app.get("/api/demo", response_model=AuditResult)
def demo() -> AuditResult:
    return get_demo_audit_result()


@app.get("/api/scenarios")
def scenarios() -> dict[str, list[str]]:
    return {"scenarios": get_available_scenarios()}


@app.get("/api/company-industries")
def company_industries() -> list[str]:
    return get_company_industries()


@app.get("/api/company-demo/{industry}")
def company_demo(industry: str) -> dict:
    try:
        return get_demo_profile(industry)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/confidence-scenarios")
def confidence_scenarios() -> dict[str, list[str]]:
    return {"scenarios": get_available_confidence_scenarios()}


@app.get("/api/confidence/{scenario}")
def confidence(scenario: str) -> dict:
    try:
        return {"scenario": scenario, "categories": get_confidence_profile(scenario)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/evidence/{mode}/{scenario}")
def evidence(mode: str, scenario: str) -> dict:
    """Return evidence-enriched insights for any analysis mode."""
    valid_modes = ["fi", "ci", "diff"]
    if mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid mode. Use: {valid_modes}")
    
    if mode == "fi":
        from financial_intelligence import analyze_scenario
        result = analyze_scenario(scenario)
        result["insights"] = enrich_insights("fi", scenario, result["insights"])
        return result
    elif mode == "ci":
        from company_intelligence import get_demo_profile
        result = get_demo_profile(scenario)
        result["insights"] = enrich_insights("ci", scenario, result.get("insights", []))
        return result
    else:
        from company_diff import get_demo_diff
        result = get_demo_diff(scenario)
        result["changes"] = enrich_insights("diff", scenario, result.get("changes", []))
        return result


@app.get("/api/diff-pairs")
def diff_pairs() -> dict[str, list[str]]:
    return {"pairs": get_available_diff_pairs()}


@app.get("/api/demo-diff/{pair}")
def demo_diff(pair: str) -> dict:
    try:
        return get_demo_diff(pair)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/analyze/{scenario}")
def analyze(scenario: str) -> dict:
    try:
        return analyze_scenario(scenario)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/analyze-company")
async def analyze_company(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported.")

    safe_name = Path(file.filename).name
    stored_name = f"{uuid4().hex}_{safe_name}"
    destination = UPLOAD_DIR / stored_name

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        parsed_pdf = {
            "text": extract_text(destination),
            "tables": extract_tables(destination),
            "financial_data": extract_financial_data(destination),
        }
        return build_company_profile(parsed_pdf)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to analyze company PDF: {exc}") from exc
    finally:
        await file.close()


@app.post("/api/company-diff")
async def company_diff(file_a: UploadFile = File(...), file_b: UploadFile = File(...)) -> dict:
    for file in (file_a, file_b):
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only .pdf files are supported.")

    safe_name_a = Path(file_a.filename).name
    safe_name_b = Path(file_b.filename).name
    destination_a = UPLOAD_DIR / f"{uuid4().hex}_{safe_name_a}"
    destination_b = UPLOAD_DIR / f"{uuid4().hex}_{safe_name_b}"

    try:
        with destination_a.open("wb") as buffer:
            shutil.copyfileobj(file_a.file, buffer)
        with destination_b.open("wb") as buffer:
            shutil.copyfileobj(file_b.file, buffer)

        parsed_a = {
            "text": extract_text(destination_a),
            "tables": extract_tables(destination_a),
            "financial_data": extract_financial_data(destination_a),
        }
        parsed_b = {
            "text": extract_text(destination_b),
            "tables": extract_tables(destination_b),
            "financial_data": extract_financial_data(destination_b),
        }
        return build_company_diff(parsed_a, parsed_b)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to compare company PDFs: {exc}") from exc
    finally:
        await file_a.close()
        await file_b.close()


@app.post("/api/upload", response_model=AuditResult)
async def upload(file: UploadFile = File(...)) -> AuditResult:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    safe_name = Path(file.filename).name
    stored_name = f"{uuid4().hex}_{safe_name}"
    destination = UPLOAD_DIR / stored_name

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        parsed = parse_excel_file(destination)
        result = audit_workbook(parsed)
        _record_audit(original_filename=safe_name, stored_filename=stored_name, result=result)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to audit workbook: {exc}") from exc
    finally:
        await file.close()


def _init_db() -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                model_score INTEGER NOT NULL,
                issue_count INTEGER NOT NULL,
                severity_breakdown TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def _record_audit(*, original_filename: str, stored_filename: str, result: AuditResult) -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO audits (
                original_filename,
                stored_filename,
                model_score,
                issue_count,
                severity_breakdown,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                original_filename,
                stored_filename,
                result.model_score,
                len(result.issues),
                json.dumps(result.severity_breakdown.model_dump()),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        connection.commit()
