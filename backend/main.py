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
from company_intelligence import build_company_profile, get_company_industries, get_demo_profile
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
