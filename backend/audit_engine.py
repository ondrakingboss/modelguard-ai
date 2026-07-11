from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Any, Iterable

from openpyxl.cell.cell import Cell
from openpyxl.utils import get_column_letter, range_boundaries
from openpyxl.worksheet.worksheet import Worksheet

from models import AuditResult, Issue, SeverityBreakdown
from parser import ParsedWorkbook, cell_value


FORMULA_ERRORS = {"#REF!", "#DIV/0!", "#VALUE!"}
EXTERNAL_LINK_RE = re.compile(r"\[[^\]]+\.(?:xlsx|xlsm|xlsb|xls)\]", re.IGNORECASE)
CELL_REF_RE = re.compile(r"(?<![A-Z0-9_])\$?([A-Z]{1,3})\$?([1-9][0-9]*)(?![A-Z0-9_])", re.IGNORECASE)
NUMBER_RE = re.compile(r"(?<![A-Z])[-+]?\d+(?:\.\d+)?%?")
ONLY_NUMBERS_OPERATORS_RE = re.compile(r"^=\s*[-+*/().,\s\d%]+$")
TRIVIAL_CONSTANTS = {0.0, 1.0, -1.0, 100.0, -100.0}
REVENUE_RE = re.compile(r"revenue|sales|turnover", re.IGNORECASE)
MARGIN_RE = re.compile(r"margin|gross margin|ebitda margin|operating margin", re.IGNORECASE)
CASH_FLOW_RE = re.compile(r"cash flow|cashflow|cash balance|running cash|ending cash", re.IGNORECASE)
ASSUMPTION_LABEL_RE = re.compile(r"growth|rate|margin|cost|price|inflation|wacc|discount|tax|depreciation", re.IGNORECASE)


def audit_workbook(parsed: ParsedWorkbook) -> AuditResult:
    issues: list[Issue] = []
    workbook = parsed.workbook

    for worksheet in workbook.worksheets:
        issues.extend(_detect_hidden_sheet(worksheet))
        issues.extend(_detect_hidden_rows(worksheet))
        issues.extend(_detect_hidden_columns(worksheet))
        issues.extend(_scan_cells(worksheet))
        issues.extend(_detect_inconsistent_neighboring_formulas(worksheet))
        issues.extend(_detect_assumption_gaps(worksheet))
        issues.extend(_detect_business_anomalies(worksheet))

    # Deduplicate before collapsing row noise
    issues = _dedupe_issues(issues)
    # Collapse repeated findings across adjacent cells in the same row
    issues = _collapse_row_noise(issues)

    severity_breakdown = Counter(issue.severity for issue in issues)
    breakdown = SeverityBreakdown(
        critical=severity_breakdown["critical"],
        high=severity_breakdown["high"],
        medium=severity_breakdown["medium"],
        low=severity_breakdown["low"],
    )
    score = _score_model(breakdown)
    summary = _summary_for(score, len(issues), breakdown)

    return AuditResult(
        model_score=score,
        summary=summary,
        issues=issues,
        severity_breakdown=breakdown,
    )


def _detect_hidden_sheet(worksheet: Worksheet) -> list[Issue]:
    if worksheet.sheet_state == "visible":
        return []

    return [
        _issue(
            severity="high",
            sheet=worksheet.title,
            cell="",
            category="Hidden Content",
            title="Hidden worksheet detected",
            description=f"Worksheet '{worksheet.title}' is marked as {worksheet.sheet_state}.",
            why_it_matters="Hidden worksheets can contain assumptions, calculations, or overrides that materially affect model outputs but are easy to miss during review.",
            suggested_fix="Unhide the sheet and document whether it is required, archival, or safe to remove.",
        )
    ]


def _detect_hidden_rows(worksheet: Worksheet) -> list[Issue]:
    issues: list[Issue] = []
    for row_idx, dimension in worksheet.row_dimensions.items():
        if dimension.hidden:
            issues.append(
                _issue(
                    severity="medium",
                    sheet=worksheet.title,
                    cell=str(row_idx),
                    category="Hidden Content",
                    title="Hidden row detected",
                    description=f"Row {row_idx} is hidden.",
                    why_it_matters="Hidden rows may conceal inputs, manual adjustments, or stale calculations.",
                    suggested_fix="Unhide the row and either validate its contents or remove it if obsolete.",
                )
            )
    return issues


def _detect_hidden_columns(worksheet: Worksheet) -> list[Issue]:
    issues: list[Issue] = []
    for col_key, dimension in worksheet.column_dimensions.items():
        if dimension.hidden:
            issues.append(
                _issue(
                    severity="medium",
                    sheet=worksheet.title,
                    cell=str(col_key),
                    category="Hidden Content",
                    title="Hidden column detected",
                    description=f"Column {col_key} is hidden.",
                    why_it_matters="Hidden columns can obscure linked calculations, helper inputs, or manual overrides.",
                    suggested_fix="Unhide the column and confirm whether its values are necessary and accurate.",
                )
            )
    return issues


def _scan_cells(worksheet: Worksheet) -> list[Issue]:
    issues: list[Issue] = []
    merged_cells = _merged_cells(worksheet)

    for row in worksheet.iter_rows():
        for cell in row:
            value = cell.value
            text = cell_value(value)

            if text in FORMULA_ERRORS:
                issues.append(_formula_error_issue(worksheet, cell, text))

            if _is_formula(value):
                formula = str(value)
                if _has_hardcoded_constants(formula):
                    issues.append(_hardcoded_formula_issue(worksheet, cell, formula))

                if EXTERNAL_LINK_RE.search(formula):
                    issues.append(_external_link_issue(worksheet, cell, formula))

                if _has_self_reference(cell, formula):
                    issues.append(_circular_reference_issue(worksheet, cell))

            if cell.coordinate in merged_cells and text in FORMULA_ERRORS:
                issues.append(_formula_error_issue(worksheet, cell, text))

    return issues


def _detect_inconsistent_neighboring_formulas(worksheet: Worksheet) -> list[Issue]:
    issues: list[Issue] = []

    for row in worksheet.iter_rows():
        formula_cells = [cell for cell in row if _is_formula(cell.value)]
        if len(formula_cells) < 3:
            continue

        patterns = [_formula_pattern(str(cell.value), cell.row, cell.column) for cell in formula_cells]
        counts = Counter(patterns)
        common_pattern, common_count = counts.most_common(1)[0]
        if common_count < 2:
            continue

        for cell, pattern in zip(formula_cells, patterns):
            if pattern != common_pattern:
                issues.append(_inconsistent_formula_issue(worksheet, cell, "row"))

    for col in worksheet.iter_cols():
        formula_cells = [cell for cell in col if _is_formula(cell.value)]
        if len(formula_cells) < 3:
            continue

        patterns = [_formula_pattern(str(cell.value), cell.row, cell.column) for cell in formula_cells]
        counts = Counter(patterns)
        common_pattern, common_count = counts.most_common(1)[0]
        if common_count < 2:
            continue

        for cell, pattern in zip(formula_cells, patterns):
            if pattern != common_pattern:
                issues.append(_inconsistent_formula_issue(worksheet, cell, "column"))

    return _dedupe_issues(issues)


def _detect_assumption_gaps(worksheet: Worksheet) -> list[Issue]:
    if "assumption" not in worksheet.title.lower():
        return []

    issues: list[Issue] = []
    max_row = max(worksheet.max_row, 1)
    max_column = max(worksheet.max_column, 1)

    for row in worksheet.iter_rows(min_row=1, max_row=max_row, min_col=1, max_col=max_column):
        label = cell_value(row[0].value) if row else ""
        row_values = [cell_value(cell.value) for cell in row]

        if label and all(value == "" for value in row_values[1:]):
            issues.append(
                _issue(
                    severity="medium",
                    sheet=worksheet.title,
                    cell=row[0].coordinate,
                    category="Assumptions",
                    title="Empty assumption line",
                    description=f"Assumption row '{label}' has no entered values.",
                    why_it_matters="Incomplete assumptions can cause downstream formulas to rely on blanks, defaults, or unintended zero values.",
                    suggested_fix="Populate the missing assumption values or remove the unused row.",
                )
            )

    non_empty = sum(1 for row in worksheet.iter_rows() for cell in row if cell_value(cell.value))
    if non_empty == 0:
        issues.append(
            _issue(
                severity="high",
                sheet=worksheet.title,
                cell="A1",
                category="Assumptions",
                title="Empty assumptions sheet",
                description="The assumptions worksheet is empty.",
                why_it_matters="A model with a blank assumptions section may be missing the documented inputs needed to validate outputs.",
                suggested_fix="Add the key operating, financing, and market assumptions used by the model.",
            )
        )

    return issues


def _detect_business_anomalies(worksheet: Worksheet) -> list[Issue]:
    issues: list[Issue] = []
    for row in worksheet.iter_rows():
        label = " ".join(cell_value(cell.value) for cell in row[:3])
        numeric_cells = [(cell, _to_number(cell.value)) for cell in row]
        numeric_cells = [(cell, value) for cell, value in numeric_cells if value is not None]
        if len(numeric_cells) < 2:
            continue

        if REVENUE_RE.search(label):
            issues.extend(_growth_issues(worksheet, numeric_cells))

        if MARGIN_RE.search(label):
            issues.extend(_margin_jump_issues(worksheet, numeric_cells))

        if CASH_FLOW_RE.search(label):
            issues.extend(_negative_cash_flow_issues(worksheet, numeric_cells))

        if ASSUMPTION_LABEL_RE.search(label):
            issues.extend(_assumption_mismatch_issues(worksheet, numeric_cells, label))

    return issues


def _growth_issues(worksheet: Worksheet, numeric_cells: list[tuple[Cell, float]]) -> list[Issue]:
    issues: list[Issue] = []
    for (previous_cell, previous), (current_cell, current) in zip(numeric_cells, numeric_cells[1:]):
        if previous <= 0:
            continue
        growth = (current - previous) / abs(previous)
        flagged = False
        if growth > 0.50:
            desc = f"Revenue grows by {growth:.0%} from {previous_cell.coordinate} to {current_cell.coordinate}."
            flagged = True
        elif growth < -0.30:
            desc = f"Revenue declines by {growth:.0%} from {previous_cell.coordinate} to {current_cell.coordinate}."
            flagged = True
        else:
            continue

        issues.append(
            _issue(
                severity="high",
                sheet=worksheet.title,
                cell=current_cell.coordinate,
                category="Business Logic",
                title="Suspicious revenue growth",
                description=desc,
                why_it_matters=(
                    "Period-over-period revenue changes exceeding 50% growth or -30% decline "
                    "are rare outside distressed or hyper-growth scenarios. Such jumps often "
                    "indicate a broken link, pasted override, or unsupported forecast assumption."
                ),
                suggested_fix="Trace the revenue driver and document the basis for the step change.",
            )
        )
    return issues


def _margin_jump_issues(worksheet: Worksheet, numeric_cells: list[tuple[Cell, float]]) -> list[Issue]:
    issues: list[Issue] = []
    for (previous_cell, previous), (current_cell, current) in zip(numeric_cells, numeric_cells[1:]):
        previous_margin = _normalize_margin(previous)
        current_margin = _normalize_margin(current)
        if previous_margin is None or current_margin is None:
            continue
        jump = abs(current_margin - previous_margin)
        if jump > 0.20:
            issues.append(
                _issue(
                    severity="medium",
                    sheet=worksheet.title,
                    cell=current_cell.coordinate,
                    category="Business Logic",
                    title="Suspicious margin jump",
                    description=f"Margin changes by {jump:.0%} from {previous_cell.coordinate} to {current_cell.coordinate}.",
                    why_it_matters="Large margin changes can materially distort profitability and valuation outputs.",
                    suggested_fix="Validate the margin formula and add support for the operational change if intentional.",
                )
            )
    return issues


def _negative_cash_flow_issues(worksheet: Worksheet, numeric_cells: list[tuple[Cell, float]]) -> list[Issue]:
    issues: list[Issue] = []
    running_total = 0.0
    for cell, value in numeric_cells:
        running_total += value
        if running_total < 0:
            issues.append(
                _issue(
                    severity="high",
                    sheet=worksheet.title,
                    cell=cell.coordinate,
                    category="Business Logic",
                    title="Negative running cash flow",
                    description=f"Running cash flow turns negative at {cell.coordinate}.",
                    why_it_matters="Negative cash flow may imply a funding gap, liquidity issue, or missing financing assumption.",
                    suggested_fix="Review cash inflows, outflows, and financing assumptions for this period.",
                )
            )
            break
    return issues


def _assumption_mismatch_issues(
    worksheet: Worksheet,
    numeric_cells: list[tuple[Cell, float]],
    label: str,
) -> list[Issue]:
    """Flag assumption rows where period-over-period changes suggest stale or mismatched inputs."""
    issues: list[Issue] = []
    values = [v for _, v in numeric_cells]
    if len(values) < 3 or all(v == values[0] for v in values):
        return issues

    # Check for suspiciously static values across periods
    unique_values = len(set(round(v, 6) for v in values))
    if unique_values == 1:
        return issues

    # Flag if a percentage-labeled row has values that look like they should vary but don't
    for i in range(1, len(values)):
        change = abs(values[i] - values[i - 1])
        if values[i - 1] != 0 and change / abs(values[i - 1]) > 1.0:
            issues.append(
                _issue(
                    severity="medium",
                    sheet=worksheet.title,
                    cell=numeric_cells[i][0].coordinate,
                    category="Business Logic",
                    title="Assumption value jump",
                    description=(
                        f"'{label}' changes abruptly at {numeric_cells[i][0].coordinate}. "
                        f"Previous value: {values[i-1]:.4f}, current: {values[i]:.4f}."
                    ),
                    why_it_matters=(
                        "Assumption values that change dramatically between periods may indicate "
                        "a copy-paste error, broken link, or undocumented change in methodology."
                    ),
                    suggested_fix=(
                        "Verify whether the change is intentional. If so, document the rationale. "
                        "If not, restore the consistent assumption series."
                    ),
                )
            )
            break
    return issues


def _has_hardcoded_constants(formula: str) -> bool:
    """Return True if formula contains non-trivial hardcoded numbers.

    Trivial constants (0, 1, -1, 100, -100) and standard modeling
    patterns (percentage conversion, growth formulas) are ignored.
    """
    if ONLY_NUMBERS_OPERATORS_RE.match(formula):
        numbers = [float(n) for n in NUMBER_RE.findall(formula)]
        return any(n not in TRIVIAL_CONSTANTS for n in numbers)

    without_references = CELL_REF_RE.sub("", formula)
    numbers = NUMBER_RE.findall(without_references)
    if not numbers:
        return False

    for num_str in numbers:
        try:
            num = float(num_str.rstrip("%"))
        except ValueError:
            continue
        if num not in TRIVIAL_CONSTANTS:
            return True
    return False


def _formula_pattern(formula: str, row: int, column: int) -> str:
    def replace_ref(match: re.Match[str]) -> str:
        ref_col = _column_index(match.group(1))
        ref_row = int(match.group(2))
        return f"R[{ref_row - row}]C[{ref_col - column}]"

    normalized = CELL_REF_RE.sub(replace_ref, formula.upper())
    normalized = re.sub(r"\d+(?:\.\d+)?", "N", normalized)
    return normalized


def _has_self_reference(cell: Cell, formula: str) -> bool:
    cell_ref = f"{get_column_letter(cell.column)}{cell.row}".upper()
    for match in CELL_REF_RE.finditer(formula.upper()):
        if f"{match.group(1).upper()}{match.group(2)}" == cell_ref:
            return True
    return False


def _is_formula(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("=")


def _to_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip().replace(",", "")
        if stripped.endswith("%"):
            stripped = stripped[:-1]
            try:
                return float(stripped) / 100
            except ValueError:
                return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _normalize_margin(value: float) -> float | None:
    if -1.0 <= value <= 1.0:
        return value
    if -100.0 <= value <= 100.0:
        return value / 100
    return None


def _column_index(column_letters: str) -> int:
    value = 0
    for char in column_letters.upper().replace("$", ""):
        value = value * 26 + ord(char) - ord("A") + 1
    return value


def _merged_cells(worksheet: Worksheet) -> set[str]:
    coordinates: set[str] = set()
    for merged_range in worksheet.merged_cells.ranges:
        min_col, min_row, max_col, max_row = range_boundaries(str(merged_range))
        for row in range(min_row, max_row + 1):
            for column in range(min_col, max_col + 1):
                coordinates.add(f"{get_column_letter(column)}{row}")
    return coordinates


def _dedupe_issues(issues: Iterable[Issue]) -> list[Issue]:
    seen: set[tuple[str, str, str, str]] = set()
    unique: list[Issue] = []
    for issue in issues:
        key = (issue.sheet, issue.cell, issue.category, issue.title)
        if key in seen:
            continue
        seen.add(key)
        unique.append(issue)
    return unique


def _collapse_row_noise(issues: list[Issue]) -> list[Issue]:
    """Group repeated findings across adjacent cells in the same row.

    If the same rule fires on adjacent cells in the same row for the same
    category and title, collapse into one grouped finding with a cell range.
    Individual cells are preserved in the description.
    """
    if len(issues) < 3:
        return issues

    # Group by (sheet, category, title) — find consecutive cell patterns
    from collections import defaultdict
    import re as _re

    def _normalize_title(t: str) -> str:
        """Strip cell references from titles so patterns group correctly."""
        return _re.sub(r"at [A-Z]+\d+", "at XX", t)

    groups: dict[tuple[str, str, str], list[Issue]] = defaultdict(list)
    for issue in issues:
        if not issue.cell:
            continue
        key = (issue.sheet, issue.category, _normalize_title(issue.title))
        groups[key].append(issue)

    collapsed: dict[str, Issue] = {}
    removed_ids: set[str] = set()

    for key, grouped in groups.items():
        if len(grouped) < 3:
            continue

        # Extract cell rows — group by row
        from collections import defaultdict
        row_groups: dict[int, list[Issue]] = defaultdict(list)
        for issue in grouped:
            row_num = _extract_row(issue.cell)
            if row_num:
                row_groups[row_num].append(issue)

        for row_num, row_issues in row_groups.items():
            if len(row_issues) < 3:
                continue

            # Sort by column
            sorted_issues = sorted(row_issues, key=lambda i: _extract_col(i.cell) or 0)

            # Find runs of consecutive columns
            runs: list[list[Issue]] = []
            current_run: list[Issue] = [sorted_issues[0]]
            for i in range(1, len(sorted_issues)):
                prev_col = _extract_col(sorted_issues[i - 1].cell)
                curr_col = _extract_col(sorted_issues[i].cell)
                if prev_col is not None and curr_col is not None and curr_col == prev_col + 1:
                    current_run.append(sorted_issues[i])
                else:
                    if len(current_run) >= 3:
                        runs.append(current_run)
                    current_run = [sorted_issues[i]]
            if len(current_run) >= 3:
                runs.append(current_run)

            for run in runs:
                first = run[0]
                last = run[-1]
                cells = sorted([i.cell for i in run], key=lambda c: (_extract_col(c) or 0))
                cell_range = f"{first.sheet}!{cells[0]}:{cells[-1]}"
                affected_list = ", ".join(cells[:8])
                if len(cells) > 8:
                    affected_list += f", ... ({len(cells)} cells total)"

                collapsed_id = f"{first.id}_grouped_{cell_range}"
                grouped_issue = Issue(
                    id=collapsed_id,
                    severity=first.severity,
                    sheet=first.sheet,
                    cell=cell_range,
                    category=first.category,
                    title=f"{first.title} (×{len(cells)} cells)",
                    description=(
                        f"{first.description} Pattern repeats across {len(cells)} "
                        f"adjacent cells in row {row_num}: {affected_list}."
                    ),
                    why_it_matters=first.why_it_matters,
                    suggested_fix=first.suggested_fix,
                )
                collapsed[collapsed_id] = grouped_issue
                removed_ids.update(i.id for i in run)

    if not collapsed:
        return issues

    result = [i for i in issues if i.id not in removed_ids]
    result.extend(collapsed.values())
    return result


def _extract_row(cell_ref: str) -> int | None:
    """Extract row number from a cell reference like 'B7' or 'A1'."""
    import re
    m = re.search(r"(\d+)", cell_ref)
    return int(m.group(1)) if m else None


def _extract_col(cell_ref: str) -> int | None:
    """Extract column index from a cell reference like 'B7'."""
    import re
    m = re.match(r"([A-Z]+)", cell_ref)
    if not m:
        return None
    return _column_index(m.group(1))


def _formula_error_issue(worksheet: Worksheet, cell: Cell, error: str) -> Issue:
    return _issue(
        severity="critical",
        sheet=worksheet.title,
        cell=cell.coordinate,
        category="Formula Error",
        title=f"Formula error {error}",
        description=f"Cell {cell.coordinate} contains Excel error value {error}.",
        why_it_matters="Formula errors can cascade through linked schedules and make outputs unreliable.",
        suggested_fix="Trace precedent cells, correct the broken formula, and verify dependent calculations.",
    )


def _hardcoded_formula_issue(worksheet: Worksheet, cell: Cell, formula: str) -> Issue:
    return _issue(
        severity="medium",
        sheet=worksheet.title,
        cell=cell.coordinate,
        category="Formula Integrity",
        title="Hardcoded constant inside formula",
        description=f"Formula '{formula}' contains hardcoded numeric input.",
        why_it_matters="Hardcoded constants make assumptions difficult to audit and can bypass the model's input controls.",
        suggested_fix="Move the constant to a clearly labeled assumption cell and reference that cell in the formula.",
    )


def _external_link_issue(worksheet: Worksheet, cell: Cell, formula: str) -> Issue:
    return _issue(
        severity="high",
        sheet=worksheet.title,
        cell=cell.coordinate,
        category="External Links",
        title="External workbook link",
        description=f"Formula '{formula}' references another workbook.",
        why_it_matters="External workbook links can break, pull stale data, or make the model impossible to reproduce for reviewers.",
        suggested_fix="Import the required source data into the model or document and package the linked workbook.",
    )


def _circular_reference_issue(worksheet: Worksheet, cell: Cell) -> Issue:
    cell_ref = f"{get_column_letter(cell.column)}{cell.row}"
    formula = str(cell.value) if cell.value else ""
    return _issue(
        severity="high",
        sheet=worksheet.title,
        cell=cell.coordinate,
        category="Circular Reference",
        title=f"Circular reference at {cell_ref}",
        description=(
            f"Cell {cell_ref} directly references itself in formula: {formula}. "
            "This creates a dependency loop that Excel resolves through iteration, "
            "producing unstable or iteration-dependent outputs."
        ),
        why_it_matters=(
            "Circular references can produce different results on recalc, mask calculation "
            "errors, and make the model fragile. They are frequently used to hide modeling "
            "issues or bypass proper schedule design."
        ),
        suggested_fix=(
            "Rewrite the formula to remove the self-reference. Move iterative logic "
            "into a controlled schedule with explicit iteration and break conditions."
        ),
    )


def _inconsistent_formula_issue(worksheet: Worksheet, cell: Cell, axis: str) -> Issue:
    return _issue(
        severity="medium",
        sheet=worksheet.title,
        cell=cell.coordinate,
        category="Formula Integrity",
        title="Inconsistent neighboring formula",
        description=f"Formula in {cell.coordinate} differs from nearby formulas in the same {axis}.",
        why_it_matters="Inconsistent formulas often indicate accidental overwrites, copied formulas with broken references, or hidden manual adjustments.",
        suggested_fix="Compare the formula against adjacent periods or line items and restore the intended pattern.",
    )


def _score_model(breakdown: SeverityBreakdown) -> int:
    """Weighted penalty scoring with caps to prevent noise inflation.

    Critical findings carry heavy weight; medium/low findings are capped
    so that formula noise doesn't destroy the score on otherwise clean models.
    """
    # Weighted penalties per severity
    critical_penalty = breakdown.critical * 30
    high_penalty = breakdown.high * 18

    # Cap medium/low — beyond 10 findings, they're likely formula noise
    medium_effective = min(breakdown.medium, 10)
    low_effective = min(breakdown.low, 8)
    medium_penalty = medium_effective * 6
    low_penalty = low_effective * 2

    # Remaining medium/low past caps still carry reduced weight
    medium_overflow = max(0, breakdown.medium - 10)
    low_overflow = max(0, breakdown.low - 8)
    overflow_penalty = medium_overflow * 2 + low_overflow * 1

    total_penalty = critical_penalty + high_penalty + medium_penalty + low_penalty + overflow_penalty
    return max(0, min(100, 100 - total_penalty))


def _summary_for(score: int, issue_count: int, breakdown: SeverityBreakdown) -> str:
    if issue_count == 0:
        return "No audit issues were detected. The workbook appears structurally clean based on the configured checks."
    if score >= 80:
        posture = "mostly sound"
    elif score >= 60:
        posture = "moderate risk"
    elif score >= 40:
        posture = "high risk"
    else:
        posture = "critical risk"

    return (
        f"Detected {issue_count} issue(s). Model risk is {posture}, with "
        f"{breakdown.critical} critical, {breakdown.high} high, "
        f"{breakdown.medium} medium, and {breakdown.low} low severity finding(s)."
    )


def _issue(
    *,
    severity: str,
    sheet: str,
    cell: str,
    category: str,
    title: str,
    description: str,
    why_it_matters: str,
    suggested_fix: str,
) -> Issue:
    digest = hashlib.sha1(
        "|".join([severity, sheet, cell, category, title, description]).encode("utf-8")
    ).hexdigest()[:10]
    return Issue(
        id=f"issue_{digest}",
        severity=severity,  # type: ignore[arg-type]
        sheet=sheet,
        cell=cell,
        category=category,
        title=title,
        description=description,
        why_it_matters=why_it_matters,
        suggested_fix=suggested_fix,
    )
