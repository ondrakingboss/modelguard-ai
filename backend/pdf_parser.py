from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import pdfplumber
except ImportError:  # pragma: no cover - exercised only when dependency is absent
    pdfplumber = None


SECTION_PATTERNS: dict[str, list[str]] = {
    "revenue_segments": [
        "revenue",
        "net sales",
        "segment",
        "subscription",
        "product revenue",
        "service revenue",
    ],
    "geographic_exposure": [
        "geographic",
        "region",
        "international",
        "united states",
        "emea",
        "europe",
        "asia",
        "apac",
        "americas",
    ],
    "debt_structure": [
        "debt",
        "borrowings",
        "credit facility",
        "senior notes",
        "maturit",
        "covenant",
        "interest rate",
    ],
    "profitability": [
        "gross margin",
        "operating margin",
        "net income",
        "operating income",
        "profitability",
        "ebitda",
        "margin",
    ],
    "cash_flow": [
        "cash flow",
        "operating cash",
        "free cash flow",
        "capital expenditures",
        "cash provided by",
        "cash used in",
    ],
}


def extract_text(path: str | Path) -> str:
    pdf_path = Path(path)
    _ensure_pdfplumber()

    pages: list[str] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for index, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append(f"[Page {index}]\n{text.strip()}")
    except Exception as exc:
        raise ValueError(f"Unable to read PDF text from {pdf_path.name}: {exc}") from exc

    return "\n\n".join(pages).strip()


def extract_tables(path: str | Path) -> list[dict[str, Any]]:
    pdf_path = Path(path)
    _ensure_pdfplumber()

    tables: list[dict[str, Any]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                for table in page.extract_tables() or []:
                    cleaned_rows = [[_clean_cell(cell) for cell in row] for row in table]
                    tables.append({"page": page_number, "rows": cleaned_rows})
    except Exception as exc:
        raise ValueError(f"Unable to read PDF tables from {pdf_path.name}: {exc}") from exc

    return tables


def extract_financial_data(path: str | Path) -> dict[str, list[dict[str, str]]]:
    text = extract_text(path)
    page_texts = _split_pages(text)
    return {
        key: _matching_snippets(page_texts, patterns)
        for key, patterns in SECTION_PATTERNS.items()
    }


def _ensure_pdfplumber() -> None:
    if pdfplumber is None:
        raise ValueError(
            "pdfplumber is required for PDF analysis. Install backend dependencies with "
            "`pip install -r backend/requirements.txt`."
        )


def _clean_cell(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _split_pages(text: str) -> list[tuple[int, str]]:
    matches = list(re.finditer(r"\[Page\s+(\d+)\]", text))
    pages: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        pages.append((int(match.group(1)), text[start:end].strip()))
    return pages


def _matching_snippets(
    page_texts: list[tuple[int, str]], patterns: list[str], max_per_section: int = 8
) -> list[dict[str, str]]:
    snippets: list[dict[str, str]] = []
    seen: set[tuple[int, str]] = set()

    for page_number, page_text in page_texts:
        paragraphs = _paragraphs(page_text)
        for paragraph in paragraphs:
            normalized = paragraph.lower()
            if not any(pattern in normalized for pattern in patterns):
                continue

            snippet = _shorten(paragraph)
            key = (page_number, snippet)
            if key in seen:
                continue
            seen.add(key)
            snippets.append({"page_ref": f"Page {page_number}", "text": snippet})
            if len(snippets) >= max_per_section:
                return snippets

    return snippets


def _paragraphs(page_text: str) -> list[str]:
    blocks = re.split(r"\n\s*\n", page_text)
    if len(blocks) <= 1:
        blocks = page_text.splitlines()
    return [re.sub(r"\s+", " ", block).strip() for block in blocks if block.strip()]


def _shorten(text: str, limit: int = 650) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rsplit(" ", 1)[0] + "..."
