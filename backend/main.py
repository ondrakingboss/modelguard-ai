from __future__ import annotations

import json
import os
import shutil
import sqlite3
import time
from collections import OrderedDict, deque
from collections.abc import Mapping
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from ipaddress import IPv4Network, IPv6Network, ip_address, ip_network
from math import ceil
from pathlib import Path
from uuid import uuid4
from zipfile import BadZipFile, ZipFile

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from audit_engine import audit_workbook
from company_diff import build_company_diff, get_available_diff_pairs, get_demo_diff
from company_intelligence import build_company_profile, get_company_industries, get_demo_profile
from confidence_analyzer import get_confidence_profile, get_available_confidence_scenarios
from evidence_explorer import enrich_insights, get_evidence
from financial_intelligence import analyze_scenario, get_available_scenarios
from mock import get_demo_audit_result
from models import AuditResult, HealthCheck
from parser import parse_excel_file
from peer_benchmark import get_benchmark, get_available_industries
from pdf_parser import extract_financial_data, extract_tables, extract_text


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DATABASE_PATH = BASE_DIR / "audits.db"

UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(application: FastAPI):
    _init_db()
    yield


app = FastAPI(title="ModelGuard AI Backend", version="1.0.0", lifespan=lifespan)

# ── In-memory rate limiter (resets on restart, single-instance only) ───

IPNetwork = IPv4Network | IPv6Network
_RATE_WINDOW = 60
_UPLOAD_LIMIT = 5
_GET_LIMIT = 60
_MAX_RATE_LIMIT_BUCKETS = 10_000


def _parse_trusted_proxy_networks(value: str) -> tuple[IPNetwork, ...]:
    networks = []
    for item in value.split(","):
        cidr = item.strip()
        if cidr:
            networks.append(ip_network(cidr, strict=False))
    return tuple(networks)


_TRUSTED_PROXY_NETWORKS = _parse_trusted_proxy_networks(
    os.getenv("MODEL_GUARD_TRUSTED_PROXY_CIDRS", "")
)


def _is_trusted_proxy(address: str, networks: tuple[IPNetwork, ...]) -> bool:
    try:
        parsed = ip_address(address)
    except ValueError:
        return False
    return any(parsed in network for network in networks)


def _resolve_client_ip(
    direct_host: str,
    forwarded_for: str | None,
    trusted_proxy_networks: tuple[IPNetwork, ...],
) -> str:
    try:
        normalized_direct = str(ip_address(direct_host))
    except ValueError:
        return direct_host

    if not _is_trusted_proxy(normalized_direct, trusted_proxy_networks):
        return normalized_direct
    if not forwarded_for:
        return normalized_direct

    forwarded_addresses = []
    for value in forwarded_for.split(","):
        try:
            forwarded_addresses.append(ip_address(value.strip()))
        except ValueError:
            return normalized_direct

    for candidate in reversed(forwarded_addresses):
        if not any(candidate in network for network in trusted_proxy_networks):
            return str(candidate)
    return normalized_direct


class InMemoryRateLimiter:
    def __init__(self, window_seconds: int, max_buckets: int) -> None:
        if window_seconds <= 0 or max_buckets <= 0:
            raise ValueError("Rate limiter bounds must be positive.")
        self.window_seconds = window_seconds
        self.max_buckets = max_buckets
        self._requests: OrderedDict[tuple[str, str], deque[float]] = OrderedDict()

    @property
    def tracked_buckets(self) -> int:
        return len(self._requests)

    def check(
        self,
        bucket: tuple[str, str],
        limit: int,
        *,
        now: float | None = None,
    ) -> int | None:
        timestamp = time.monotonic() if now is None else now
        requests = self._requests.pop(bucket, deque())
        cutoff = timestamp - self.window_seconds
        while requests and requests[0] <= cutoff:
            requests.popleft()

        self._requests[bucket] = requests
        if len(requests) >= limit:
            return max(1, ceil(self.window_seconds - (timestamp - requests[0])))

        requests.append(timestamp)
        while len(self._requests) > self.max_buckets:
            self._requests.popitem(last=False)
        return None


_RATE_LIMITER = InMemoryRateLimiter(_RATE_WINDOW, _MAX_RATE_LIMIT_BUCKETS)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    direct_host = request.client.host if request.client else "unknown"
    client_ip = _resolve_client_ip(
        direct_host,
        request.headers.get("x-forwarded-for"),
        _TRUSTED_PROXY_NETWORKS,
    )
    bucket_type = "write" if request.method == "POST" else "read"
    limit = _UPLOAD_LIMIT if bucket_type == "write" else _GET_LIMIT
    retry_after = _RATE_LIMITER.check((bucket_type, client_ip), limit)
    if retry_after is not None:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please wait before retrying."},
            headers={"Retry-After": str(retry_after)},
        )
    return await call_next(request)


# ── Security headers middleware ──────────────────────────────────────────

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ── Max upload size (10 MB) ─────────────────────────────────────────────

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_REQUEST_BODY_SIZE = MAX_UPLOAD_SIZE + 1024 * 1024  # multipart envelope allowance
MAX_DIFF_REQUEST_BODY_SIZE = (2 * MAX_UPLOAD_SIZE) + 1024 * 1024
UPLOAD_BODY_LIMITS = {
    "/api/analyze-company": MAX_REQUEST_BODY_SIZE,
    "/api/company-diff": MAX_DIFF_REQUEST_BODY_SIZE,
    "/api/upload": MAX_REQUEST_BODY_SIZE,
}
XLSX_REQUIRED_MEMBERS = frozenset({"[Content_Types].xml", "xl/workbook.xml"})
# Central-directory-only limits keep archive validation cheap and pre-parser.
MAX_XLSX_ARCHIVE_MEMBERS = 2_000
MAX_XLSX_TOTAL_UNCOMPRESSED_SIZE = 50 * 1024 * 1024
MAX_XLSX_MEMBER_UNCOMPRESSED_SIZE = 25 * 1024 * 1024
MAX_XLSX_COMPRESSION_RATIO = 500


class _RequestTooLarge(Exception):
    pass


class RequestSizeLimitMiddleware:
    def __init__(self, app: ASGIApp, limits_by_path: Mapping[str, int]) -> None:
        self.app = app
        self.limits_by_path = limits_by_path

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        max_bytes = self.limits_by_path.get(scope.get("path", ""))
        if scope["type"] != "http" or scope.get("method") != "POST" or max_bytes is None:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        try:
            content_length = int(headers.get(b"content-length", b""))
        except ValueError:
            content_length = None
        if content_length is not None and content_length > max_bytes:
            await self._reject(scope, receive, send)
            return

        bytes_received = 0

        async def limited_receive() -> Message:
            nonlocal bytes_received
            message = await receive()
            if message["type"] == "http.request":
                bytes_received += len(message.get("body", b""))
                if bytes_received > max_bytes:
                    raise _RequestTooLarge
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _RequestTooLarge:
            await self._reject(scope, receive, send)

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=413,
            content={"detail": "Request body exceeds the upload limit."},
        )
        await response(scope, receive, send)


def _validate_upload(file: UploadFile, suffix: str) -> None:
    if not file.filename or not file.filename.lower().endswith(suffix):
        raise HTTPException(status_code=400, detail=f"Only {suffix} files are supported.")

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file_size / 1024 / 1024:.1f} MB). Maximum size is 10 MB.",
        )
    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail=f"Empty file. Upload a valid {suffix} file.",
        )
    if not _has_valid_file_structure(file, suffix):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {suffix} file contents.",
        )


def _has_valid_file_structure(file: UploadFile, suffix: str) -> bool:
    file.file.seek(0)
    try:
        if suffix == ".pdf":
            return file.file.read(5) == b"%PDF-"
        if suffix == ".xlsx":
            try:
                with ZipFile(file.file) as archive:
                    members = archive.infolist()
                    if len(members) > MAX_XLSX_ARCHIVE_MEMBERS:
                        return False
                    if not XLSX_REQUIRED_MEMBERS.issubset(
                        member.filename for member in members
                    ):
                        return False

                    total_size = 0
                    for member in members:
                        total_size += member.file_size
                        if total_size > MAX_XLSX_TOTAL_UNCOMPRESSED_SIZE:
                            return False
                        if member.file_size > MAX_XLSX_MEMBER_UNCOMPRESSED_SIZE:
                            return False
                        if member.file_size and (
                            member.compress_size == 0
                            or member.file_size
                            > member.compress_size * MAX_XLSX_COMPRESSION_RATIO
                        ):
                            return False
                    return True
            except (BadZipFile, OSError):
                return False
        raise ValueError(f"Unsupported upload suffix: {suffix}")
    finally:
        file.file.seek(0)


app.add_middleware(
    RequestSizeLimitMiddleware,
    limits_by_path=UPLOAD_BODY_LIMITS,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://modelguard-ai.vercel.app",
    ],
    allow_origin_regex=r"^https://modelguard-ai(?:-[a-z0-9-]+)*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/api/benchmark-industries")
def benchmark_industries() -> dict[str, list[str]]:
    return {"industries": get_available_industries()}


@app.get("/api/benchmark/{industry}")
def benchmark(industry: str) -> dict:
    try:
        return get_benchmark(industry)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
    destination: Path | None = None

    try:
        _validate_upload(file, ".pdf")
        safe_name = Path(file.filename).name
        stored_name = f"{uuid4().hex}_{safe_name}"
        destination = UPLOAD_DIR / stored_name
        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        parsed_pdf = {
            "text": extract_text(destination),
            "tables": extract_tables(destination),
            "financial_data": extract_financial_data(destination),
        }
        return build_company_profile(parsed_pdf)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to analyze company PDF: {exc}") from exc
    finally:
        await file.close()
        if destination is not None:
            destination.unlink(missing_ok=True)


@app.post("/api/company-diff")
async def company_diff(file_a: UploadFile = File(...), file_b: UploadFile = File(...)) -> dict:
    destination_a: Path | None = None
    destination_b: Path | None = None

    try:
        _validate_upload(file_a, ".pdf")
        _validate_upload(file_b, ".pdf")
        safe_name_a = Path(file_a.filename).name
        safe_name_b = Path(file_b.filename).name
        destination_a = UPLOAD_DIR / f"{uuid4().hex}_{safe_name_a}"
        destination_b = UPLOAD_DIR / f"{uuid4().hex}_{safe_name_b}"
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
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to compare company PDFs: {exc}") from exc
    finally:
        await file_a.close()
        await file_b.close()
        if destination_a is not None:
            destination_a.unlink(missing_ok=True)
        if destination_b is not None:
            destination_b.unlink(missing_ok=True)


@app.post("/api/upload", response_model=AuditResult)
async def upload(file: UploadFile = File(...)) -> AuditResult:
    destination: Path | None = None

    try:
        _validate_upload(file, ".xlsx")
        safe_name = Path(file.filename).name
        stored_name = f"{uuid4().hex}_{safe_name}"
        destination = UPLOAD_DIR / stored_name
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
        if destination is not None:
            destination.unlink(missing_ok=True)


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
