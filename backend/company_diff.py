from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


DEMO_PAIRS = ("tech_growth", "industrial_restructuring", "bank_nim")
DEMO_PERIOD_ALIASES = {
    ("tech_2024", "tech_2025"): "tech_growth",
    ("industrial_q3", "industrial_q4"): "industrial_restructuring",
    ("bank_rate_before", "bank_rate_after"): "bank_nim",
}


def get_available_diff_pairs() -> list[str]:
    return list(DEMO_PAIRS)


def get_demo_diff(pair: str) -> dict[str, Any]:
    try:
        return deepcopy(DEMO_DIFFS[pair])
    except KeyError as exc:
        raise ValueError(f"Unknown diff pair '{pair}'. Expected one of: {', '.join(DEMO_PAIRS)}") from exc


def compare_company_periods(company_a: str, company_b: str) -> dict[str, Any]:
    pair = DEMO_PERIOD_ALIASES.get((company_a, company_b))
    if not pair:
        expected = ", ".join(f"{left}/{right}" for left, right in DEMO_PERIOD_ALIASES)
        raise ValueError(f"Unknown comparison '{company_a}' to '{company_b}'. Expected one of: {expected}")
    return get_demo_diff(pair)


def build_company_diff(
    parsed_pdf_a: dict[str, Any],
    parsed_pdf_b: dict[str, Any],
    *,
    name_a: str | None = None,
    name_b: str | None = None,
    period_a: str | None = None,
    period_b: str | None = None,
) -> dict[str, Any]:
    profile_a = _document_profile(parsed_pdf_a, fallback_name=name_a, fallback_period=period_a)
    profile_b = _document_profile(parsed_pdf_b, fallback_name=name_b, fallback_period=period_b)
    changes = _compare_profiles(profile_a, profile_b)

    if not changes:
        changes.append(
            _change(
                "Management Commentary",
                "medium",
                46,
                "Limited comparable disclosures found across uploaded documents",
                "Insufficient comparable evidence",
                "Insufficient comparable evidence",
                "n/a",
                "flat",
                profile_a["default_ref"],
                profile_b["default_ref"],
                "The uploaded PDFs did not expose enough matched financial disclosures for a reliable period-over-period bridge.",
                "ModelGuard should treat this as a document coverage issue before drawing investment or credit conclusions.",
                "Upload searchable annual reports, quarterly filings, or investor presentations with revenue, margin, debt, cash flow, guidance, risk, and accounting sections.",
            )
        )

    return {
        "company_a": {"name": profile_a["name"], "period": profile_a["period"]},
        "company_b": {"name": profile_b["name"], "period": profile_b["period"]},
        "executive_summary": _executive_summary(profile_a, profile_b, changes),
        "changes": changes,
        "summary_stats": _summary_stats(changes),
    }


def _document_profile(parsed_pdf: dict[str, Any], *, fallback_name: str | None, fallback_period: str | None) -> dict[str, Any]:
    text = parsed_pdf.get("text", "") or ""
    financial_data = parsed_pdf.get("financial_data", {}) or {}

    snippets = _section_snippets(financial_data)
    return {
        "name": fallback_name or _extract_company_name(text) or "Not found in document",
        "period": fallback_period or _extract_period(text) or "Not found in document",
        "default_ref": _first_ref(snippets) or "Section: Extracted PDF text",
        "revenue": _extract_section_metric("Revenue", snippets, ("revenue", "net sales", "interest income", "fee income")),
        "margin": _extract_section_metric("Margin", snippets, ("gross margin", "operating margin", "nim", "net interest margin")),
        "debt": _extract_section_metric("Debt", snippets, ("debt", "notes", "borrowings", "preferred shares", "tier 1")),
        "cash_flow": _extract_section_metric("Cash Flow", snippets, ("cash flow", "free cash flow", "operating cash", "securities", "loan book")),
        "capital": _extract_section_metric("Capital Allocation", snippets, ("buyback", "repurchase", "dividend", "cet1", "capital ratio")),
        "guidance": _extract_section_metric("Guidance", snippets, ("guidance", "outlook", "provision", "forecast")),
        "risks": _extract_risk_terms(text),
        "accounting": _extract_section_metric("Accounting Policy", snippets, ("accounting", "asc 606", "cecl", "revenue recognition", "credit losses")),
        "commentary": _extract_commentary(text),
    }


def _compare_profiles(profile_a: dict[str, Any], profile_b: dict[str, Any]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    section_map = [
        ("Revenue", "revenue", "Revenue mix and growth profile changed"),
        ("Margin", "margin", "Margin disclosure changed"),
        ("Debt", "debt", "Capital structure disclosure changed"),
        ("Cash Flow", "cash_flow", "Cash generation and balance sheet liquidity changed"),
        ("Capital Allocation", "capital", "Capital allocation priorities changed"),
        ("Guidance", "guidance", "Forward outlook changed"),
        ("Accounting Policy", "accounting", "Accounting policy disclosure changed"),
        ("Management Commentary", "commentary", "Management tone and emphasis changed"),
    ]

    for category, key, fallback_title in section_map:
        item_a = profile_a[key]
        item_b = profile_b[key]
        if not item_a["value"] and not item_b["value"]:
            continue
        if item_a["normalized"] == item_b["normalized"]:
            continue

        direction, change_pct = _direction_and_pct(item_a["number"], item_b["number"])
        changes.append(
            _change(
                category,
                _importance(category, direction),
                _confidence(item_a, item_b),
                _title(category, item_a["value"], item_b["value"], fallback_title),
                item_a["value"] or "Not found in document",
                item_b["value"] or "Not found in document",
                change_pct,
                direction,
                item_a["ref"] or profile_a["default_ref"],
                item_b["ref"] or profile_b["default_ref"],
                _analyst_note(category, direction),
                _financial_implication(category, direction),
                _recommended_action(category),
            )
        )

    risk_change = _compare_risks(profile_a, profile_b)
    if risk_change:
        changes.append(risk_change)

    return sorted(changes, key=lambda item: {"critical": 0, "high": 1, "medium": 2, "low": 3}[item["importance"]])


def _section_snippets(financial_data: dict[str, Any]) -> list[dict[str, str]]:
    snippets: list[dict[str, str]] = []
    for section, items in financial_data.items():
        for item in items or []:
            snippets.append({"section": section, "text": item.get("text", ""), "page_ref": item.get("page_ref", "")})
    return snippets


def _extract_section_metric(label: str, snippets: list[dict[str, str]], terms: tuple[str, ...]) -> dict[str, Any]:
    best: dict[str, str] | None = None
    for item in snippets:
        lowered = item["text"].lower()
        if any(term in lowered for term in terms):
            best = item
            break

    if not best:
        return {"label": label, "value": "", "normalized": "", "number": None, "ref": ""}

    value = _metric_value(best["text"]) or _shorten(best["text"], 120)
    return {
        "label": label,
        "value": value,
        "normalized": _normalize(value),
        "number": _first_number(value),
        "ref": _document_ref(best),
    }


def _extract_risk_terms(text: str) -> dict[str, Any]:
    risk_sentences = [sentence for sentence in _sentences(text) if "risk" in sentence.lower()][:8]
    terms: set[str] = set()
    for sentence in risk_sentences:
        lowered = sentence.lower()
        for label, keywords in RISK_TERMS.items():
            if any(keyword in lowered for keyword in keywords):
                terms.add(label)
    value = ", ".join(sorted(terms)) if terms else _shorten(risk_sentences[0], 120) if risk_sentences else ""
    ref = _page_ref_for_text(text, risk_sentences[0]) if risk_sentences else ""
    return {"terms": terms, "value": value, "ref": ref}


def _extract_commentary(text: str) -> dict[str, Any]:
    sentences = _sentences(text)
    candidates = [
        sentence
        for sentence in sentences
        if any(term in sentence.lower() for term in ("ceo", "management", "letter", "discipline", "confident", "optimistic", "strategy"))
    ]
    if not candidates:
        return {"value": "", "normalized": "", "number": None, "ref": ""}
    value = _shorten(candidates[0], 140)
    return {"value": value, "normalized": _normalize(value), "number": None, "ref": _page_ref_for_text(text, candidates[0])}


def _compare_risks(profile_a: dict[str, Any], profile_b: dict[str, Any]) -> dict[str, Any] | None:
    risks_a = profile_a["risks"]["terms"]
    risks_b = profile_b["risks"]["terms"]
    added = sorted(risks_b - risks_a)
    removed = sorted(risks_a - risks_b)
    if not added and not removed:
        return None

    title_parts = []
    if added:
        title_parts.append(f"New risk disclosures added: {', '.join(added)}")
    if removed:
        title_parts.append(f"Removed risk disclosures: {', '.join(removed)}")

    direction = "new" if added else "removed"
    return _change(
        "Business Risks",
        "high" if added else "medium",
        78,
        "; ".join(title_parts),
        profile_a["risks"]["value"] or "No matched risk term found",
        profile_b["risks"]["value"] or "No matched risk term found",
        "n/a",
        direction,
        profile_a["risks"]["ref"] or profile_a["default_ref"],
        profile_b["risks"]["ref"] or profile_b["default_ref"],
        "Risk-factor movement is often more important than the wording count because it shows where management and counsel see emerging exposure.",
        "New risks can raise forecast discount rates or require explicit downside cases; removed risks may indicate an operating constraint has eased.",
        "Map each changed risk to a measurable KPI, owner, mitigation plan, and forecast sensitivity.",
    )


def _change(
    category: str,
    importance: str,
    confidence: int,
    title: str,
    value_a: str,
    value_b: str,
    change_pct: str,
    change_direction: str,
    document_ref_a: str,
    document_ref_b: str,
    analyst_note: str,
    financial_implication: str,
    recommended_action: str,
) -> dict[str, Any]:
    return {
        "category": category,
        "importance": importance,
        "confidence": max(0, min(100, confidence)),
        "title": title,
        "value_a": value_a,
        "value_b": value_b,
        "change_pct": change_pct,
        "change_direction": change_direction,
        "document_ref_a": document_ref_a,
        "document_ref_b": document_ref_b,
        "analyst_note": analyst_note,
        "financial_implication": financial_implication,
        "recommended_action": recommended_action,
    }


def _executive_summary(profile_a: dict[str, Any], profile_b: dict[str, Any], changes: list[dict[str, Any]]) -> str:
    critical_or_high = [item for item in changes if item["importance"] in {"critical", "high"}]
    top = critical_or_high[0] if critical_or_high else changes[0]
    second = changes[1] if len(changes) > 1 else top
    return (
        f"The comparison of {profile_a['name']} ({profile_a['period']}) against {profile_b['name']} ({profile_b['period']}) shows {len(changes)} section-backed changes. "
        f"The most important movement is {top['title'].lower()}, which affects the business through {top['financial_implication'].lower()} "
        f"A second watch item is {second['category'].lower()}, where the document evidence points to {second['analyst_note'].lower()} "
        "The output prioritizes interpretation over extraction and should be reconciled to the original filing sections before being used in an investment memo."
    )


def _summary_stats(changes: list[dict[str, Any]]) -> dict[str, int]:
    positive = sum(1 for item in changes if _sentiment(item) == "positive")
    negative = sum(1 for item in changes if _sentiment(item) == "negative")
    neutral = len(changes) - positive - negative
    return {
        "total_changes": len(changes),
        "critical_changes": sum(1 for item in changes if item["importance"] == "critical"),
        "positive_changes": positive,
        "negative_changes": negative,
        "neutral_changes": neutral,
    }


def _sentiment(change: dict[str, Any]) -> str:
    text = f"{change['title']} {change['analyst_note']} {change['financial_implication']}".lower()
    if any(term in text for term in ("improved", "accelerated", "raised", "expanded", "reduced debt", "stronger", "positive")):
        return "positive"
    if any(term in text for term in ("declined", "risk", "withdrew", "higher provisions", "pressure", "negative", "dilution")):
        return "negative"
    return "neutral"


def _title(category: str, value_a: str, value_b: str, fallback: str) -> str:
    if value_a and value_b:
        return f"{category} moved from {value_a} to {value_b}"
    if value_b:
        return f"New {category.lower()} disclosure identified"
    if value_a:
        return f"{category} disclosure removed"
    return fallback


def _direction_and_pct(number_a: float | None, number_b: float | None) -> tuple[str, str]:
    if number_a is None and number_b is None:
        return "flat", "n/a"
    if number_a is None:
        return "new", "n/a"
    if number_b is None:
        return "removed", "n/a"
    if number_a == 0:
        return ("up" if number_b > 0 else "flat", "n/a")
    change = (number_b - number_a) / abs(number_a)
    if abs(change) < 0.01:
        return "flat", "0%"
    return ("up" if change > 0 else "down", f"{change * 100:+.0f}%")


def _importance(category: str, direction: str) -> str:
    if category in {"Debt", "Cash Flow", "Guidance", "Business Risks"} and direction in {"down", "new"}:
        return "high"
    if category in {"Revenue", "Margin"}:
        return "high"
    if category == "Accounting Policy":
        return "medium"
    return "medium"


def _confidence(item_a: dict[str, Any], item_b: dict[str, Any]) -> int:
    score = 62
    if item_a["ref"]:
        score += 12
    if item_b["ref"]:
        score += 12
    if item_a["number"] is not None and item_b["number"] is not None:
        score += 10
    return score


def _analyst_note(category: str, direction: str) -> str:
    notes = {
        "Revenue": "Revenue movement should be read with mix and durability, not only headline growth.",
        "Margin": "Margin movement indicates whether growth is translating into operating leverage or being consumed by cost structure.",
        "Debt": "Debt changes alter refinancing risk, interest burden, and flexibility for acquisitions or shareholder returns.",
        "Cash Flow": "Cash-flow movement is the clearest signal of whether earnings quality improved or deteriorated.",
        "Capital Allocation": "Capital allocation changes show management's current tradeoff between growth, leverage, and shareholder returns.",
        "Guidance": "Guidance movement can reset investor expectations before the income statement fully reflects the change.",
        "Accounting Policy": "Accounting policy changes require comparability checks before using period-over-period metrics.",
        "Management Commentary": "Tone changes can reveal whether management is defending the plan or leaning into stronger execution confidence.",
    }
    suffix = " The direction is favorable but should be tested against supporting KPIs." if direction == "up" else " The direction increases diligence needs around forecast assumptions."
    return notes.get(category, "The change needs direct reconciliation to source disclosures.") + suffix


def _financial_implication(category: str, direction: str) -> str:
    implications = {
        "Revenue": "valuation multiples, revenue quality, and forecast credibility may change.",
        "Margin": "earnings power and cash conversion assumptions may need to be revised.",
        "Debt": "interest expense, covenant cushion, and refinancing risk may change.",
        "Cash Flow": "liquidity, self-funding capacity, and balance sheet resilience may change.",
        "Capital Allocation": "future cash uses and shareholder return assumptions may need to be updated.",
        "Guidance": "the forecast base case and scenario ranges should be reset.",
        "Accounting Policy": "reported growth or credit metrics may not be directly comparable without normalization.",
        "Management Commentary": "the qualitative risk premium in the investment narrative may change.",
    }
    return implications.get(category, "the financial model should be reviewed.")


def _recommended_action(category: str) -> str:
    actions = {
        "Revenue": "Build a bridge by segment and separate price, volume, mix, and retention where disclosed.",
        "Margin": "Reconcile gross and operating margin drivers to cost, mix, pricing, and compensation changes.",
        "Debt": "Update the maturity schedule, interest-rate assumptions, covenant cushion, and refinancing scenarios.",
        "Cash Flow": "Rebuild free cash flow from operating cash flow, CapEx, working capital, and one-time items.",
        "Capital Allocation": "Refresh the capital allocation waterfall before accepting buyback, dividend, or deleveraging assumptions.",
        "Guidance": "Tie guidance changes to explicit model drivers and create upside and downside cases.",
        "Accounting Policy": "Normalize historical metrics for the policy change before comparing growth or margins.",
        "Management Commentary": "Compare the tone shift with KPI evidence from the operating sections.",
    }
    return actions.get(category, "Reconcile this change to source documents and model assumptions.")


def _extract_company_name(text: str) -> str:
    for pattern in (
        r"\n\s*([A-Z][A-Z0-9&.,' -]{3,80})\s*\n\s*(?:Annual Report|Form 10-K|10-K|Quarterly Report|Form 10-Q)",
        r"(?:Registrant|Company Name)\s*[:\-]\s*([A-Z][A-Za-z0-9&.,' -]{3,80})",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return _title_case(match.group(1))
    for line in [line.strip() for line in text.splitlines()[:30] if line.strip()]:
        if 3 <= len(line) <= 80 and not line.startswith("[Page") and not re.search(r"\d{4}", line):
            return _title_case(line)
    return ""


def _extract_period(text: str) -> str:
    for pattern in (
        r"(?:fiscal year|year|quarter|period)\s+ended\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        r"(?:for the year ended|for the quarter ended)\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        r"\b(FY\s?20\d{2}|Q[1-4]\s?20\d{2}|20\d{2})\b",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _metric_value(text: str) -> str:
    percent = re.search(r"[-+]?\d+(?:\.\d+)?\s*%", text)
    money = re.search(r"\$?\d+(?:\.\d+)?\s*(?:billion|million|bn|mm|m|b)\b", text, re.IGNORECASE)
    rate = re.search(r"\d+(?:\.\d+)?\s*(?:bps|basis points)", text, re.IGNORECASE)
    return (money or percent or rate).group(0) if (money or percent or rate) else ""


def _first_number(text: str) -> float | None:
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text.replace(",", ""))
    return float(match.group(0)) if match else None


def _document_ref(item: dict[str, str]) -> str:
    section = item.get("section", "extracted disclosure").replace("_", " ").title()
    page = item.get("page_ref") or "Page not identified"
    return f"{page}, Section {section}"


def _first_ref(snippets: list[dict[str, str]]) -> str:
    return _document_ref(snippets[0]) if snippets else ""


def _page_ref_for_text(full_text: str, target: str) -> str:
    if not target:
        return "Section: Extracted PDF text"
    pages = list(re.finditer(r"\[Page\s+(\d+)\]", full_text))
    position = full_text.find(target[:40])
    if position < 0 or not pages:
        return "Section: Extracted PDF text"
    current_page = pages[0].group(1)
    for page in pages:
        if page.start() <= position:
            current_page = page.group(1)
        else:
            break
    return f"Page {current_page}, Section Narrative Disclosure"


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text)
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", cleaned) if len(sentence.strip()) > 30]


def _shorten(text: str, limit: int = 180) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rsplit(" ", 1)[0] + "..."


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _title_case(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().title()


RISK_TERMS = {
    "AI regulatory risk": ("ai regulation", "artificial intelligence regulation", "ai regulatory"),
    "supply chain risk": ("supply chain", "supplier disruption", "component shortage"),
    "pension underfunding risk": ("pension", "underfund"),
    "commodity risk": ("commodity", "raw material", "steel", "resin"),
    "CRE exposure risk": ("commercial real estate", "cre exposure", "office real estate"),
    "digital banking disruption": ("digital banking", "fintech", "digital disruption"),
}


DEMO_DIFFS: dict[str, dict[str, Any]] = {
    "tech_growth": {
        "company_a": {"name": "Nimbus Systems", "period": "FY2024"},
        "company_b": {"name": "Nimbus Systems", "period": "FY2025"},
        "executive_summary": (
            "Nimbus Systems moved from strong growth to a more confident AI-led expansion profile, with revenue up 24% and cloud acceleration offsetting slower Workflow SaaS growth. "
            "Gross margin improved from 71% to 73%, but operating margin stayed flat because stock-based compensation absorbed much of the operating leverage. "
            "The balance sheet became more flexible after the prior note matured, although the new $2.0B bond adds a higher coupon and extends leverage duration. "
            "Management raised next-year guidance and removed supply-chain risk, but the new AI regulatory risk deserves explicit scenario work."
        ),
        "changes": [
            _change("Revenue", "high", 94, "Cloud revenue accelerated while Workflow SaaS decelerated", "$18.2B revenue; Cloud +27%, Workflow SaaS +19%", "$22.6B revenue; Cloud +31%, Workflow SaaS +14%", "+24%", "up", "Page 42, Section Revenue by Product", "Page 45, Section Revenue by Product", "The growth mix improved because the higher-multiple cloud platform is becoming a larger share of total revenue, even as Workflow SaaS shows maturity.", "Revenue quality improves if cloud retention and attach rates hold; slower Workflow SaaS should reduce the blended growth multiple unless cloud scale offsets it.", "Model separate Cloud and Workflow SaaS growth curves rather than applying one company-wide growth rate."),
            _change("Margin", "high", 91, "Gross margin expanded but operating margin stayed flat due to SBC", "Gross margin 71%; operating margin 22%", "Gross margin 73%; operating margin 22%", "+3%", "up", "Page 58, Section Consolidated Margin Bridge", "Page 61, Section Consolidated Margin Bridge", "Infrastructure efficiency is visible in gross margin, but stock-based compensation is preventing that improvement from reaching operating income.", "EBIT quality is weaker than gross-margin trend implies; normalized operating margin could be higher if SBC growth moderates.", "Track GAAP and ex-SBC operating margin and require management to disclose SBC as a percentage of revenue."),
            _change("Debt", "medium", 89, "New $2.0B bond issued after $1.5B note matured", "$1.5B senior note at 3.75% due FY2025", "$2.0B senior bond at 4.25% due FY2032", "+33%", "up", "Page 76, Section Debt Maturities", "Page 79, Section Long-Term Debt", "The company extended maturity risk but accepted a higher coupon and larger principal balance.", "Annual interest burden rises, but refinancing risk is pushed out and liquidity planning becomes more predictable.", "Update the debt schedule, interest expense forecast, and weighted-average coupon in the valuation model."),
            _change("Cash Flow", "high", 92, "Free cash flow improved as CapEx cycle moderated", "$4.2B FCF; elevated AI data center buildout", "$5.1B FCF; CapEx intensity declined", "+21%", "up", "Page 68, Section Cash Flow and Capital Expenditures", "Page 71, Section Cash Flow and Capital Expenditures", "Cash conversion improved because the prior data-center investment cycle moved past peak intensity.", "Higher FCF supports both AI infrastructure reinvestment and shareholder returns without increasing leverage materially.", "Use a maintenance-versus-growth CapEx bridge before assuming the lower CapEx rate is permanent."),
            _change("Capital Allocation", "medium", 88, "Buyback authorization increased", "$5.0B repurchase authorization", "$8.0B repurchase authorization", "+60%", "up", "Page 82, Section Share Repurchase Program", "Page 85, Section Capital Return Program", "Management is signaling stronger confidence in cash generation by expanding repurchase capacity.", "Buybacks can support EPS, but may compete with AI infrastructure investment if growth CapEx reaccelerates.", "Stress test buybacks after funding cloud CapEx, debt service, and minimum cash balance."),
            _change("Guidance", "high", 93, "Next-year revenue guide raised from +18% to +22%", "+18% revenue growth outlook", "+22% revenue growth outlook", "+22%", "up", "Page 14, Section FY2025 Outlook", "Page 16, Section FY2026 Outlook", "The raised guide confirms management expects cloud acceleration to more than offset SaaS deceleration.", "Consensus revenue and operating expense assumptions should move higher, but margin expansion is still capped by SBC unless compensation intensity improves.", "Revise the base case to +22% revenue growth and add a downside case where Workflow SaaS deceleration continues."),
            _change("Business Risks", "high", 90, "AI regulatory risk added while supply-chain risk was removed", "Supply chain risk disclosed as material", "AI regulatory risk disclosed; supply chain risk removed", "n/a", "new", "Page 104, Section Risk Factors", "Page 109, Section Risk Factors", "The risk profile shifted from physical component availability to regulatory scrutiny over AI products and data use.", "Regulatory constraints could affect product release timing, compliance cost, and enterprise adoption in sensitive industries.", "Add AI compliance cost and launch-delay sensitivities to the forecast."),
            _change("Accounting Policy", "medium", 87, "ASC 606 amendment adopted for revenue recognition", "Prior revenue recognition policy under existing ASC 606 elections", "Adopted ASC 606 amendment for multi-year cloud contracts", "n/a", "new", "Page 91, Section Significant Accounting Policies", "Page 94, Section Revenue Recognition", "The accounting change may affect timing between bookings, deferred revenue, and recognized revenue.", "Reported growth may not be perfectly comparable without normalizing contract timing effects.", "Reconcile revenue growth to billings, RPO, and deferred revenue before changing the forecast."),
            _change("Management Commentary", "medium", 86, "CEO tone shifted from cautiously optimistic to confident", "CEO described demand as cautiously optimistic", "CEO described AI platform demand as confident and broadening", "n/a", "up", "Page 3, Section CEO Letter", "Page 3, Section CEO Letter", "The tone shift aligns with stronger cloud growth and raised guidance, but it still needs KPI confirmation.", "A stronger narrative may support the multiple if backed by retention, pipeline, and margin evidence.", "Compare CEO language against customer additions, backlog, and net retention."),
        ],
        "summary_stats": {"total_changes": 9, "critical_changes": 0, "positive_changes": 6, "negative_changes": 2, "neutral_changes": 1},
    },
    "industrial_restructuring": {
        "company_a": {"name": "Atlas Components", "period": "Q3 FY2025"},
        "company_b": {"name": "Atlas Components", "period": "Q4 FY2025"},
        "executive_summary": (
            "Atlas Components delivered almost flat revenue after restructuring, but the portfolio mix improved as low-margin product lines were exited. "
            "Gross margin rose from 24% to 27%, validating the portfolio rationalization, while free cash flow declined because $1.2B of restructuring charges pulled cash out of the period. "
            "Debt reduction from $3.2B to $2.5B is strategically important, but dividend suspension changes the shareholder return profile. "
            "The new CEO's focus on operational discipline is credible, though withdrawn long-term guidance raises forecast uncertainty."
        ),
        "changes": [
            _change("Revenue", "medium", 90, "Revenue was flat but mix shifted toward higher-margin products", "$10.4B revenue; legacy products 42% of sales", "$10.35B revenue; engineered systems 49% of sales", "-0.5%", "down", "Page 33, Section Segment Revenue", "Page 35, Section Segment Revenue", "The headline revenue decline is minor; the more important change is mix quality after exiting low-margin products.", "Lower-quality sales were removed, so EBITDA can improve even without revenue growth.", "Build a price-volume-mix bridge and separate discontinued product lines from ongoing operations."),
            _change("Margin", "high", 93, "Gross margin improved from 24% to 27%", "24% gross margin", "27% gross margin", "+13%", "up", "Page 49, Section Gross Margin Analysis", "Page 51, Section Gross Margin Analysis", "Portfolio rationalization is flowing through to gross margin faster than revenue growth.", "The business can support higher EBITDA on a flat sales base if the mix shift is durable.", "Validate margin by product family and isolate temporary restructuring benefits from recurring improvement."),
            _change("Debt", "high", 94, "Debt reduced through asset sales", "$3.2B total debt", "$2.5B total debt", "-22%", "down", "Page 72, Section Debt and Liquidity", "Page 74, Section Debt and Liquidity", "Asset-sale proceeds were used to delever, improving the balance sheet during a volatile operating period.", "Lower debt reduces interest expense and covenant risk, partially offsetting restructuring cash drag.", "Update leverage, interest expense, and covenant cushion using post-sale EBITDA."),
            _change("Cash Flow", "high", 91, "Free cash flow declined due to $1.2B restructuring charges", "$620M free cash flow", "$180M free cash flow after $1.2B restructuring charges", "-71%", "down", "Page 64, Section Cash Flow", "Page 67, Section Cash Flow", "The cash decline is driven by restructuring rather than a collapse in the core operating model.", "Near-term liquidity pressure rises, but cash generation should recover if charges are genuinely one-time.", "Separate recurring FCF from restructuring cash costs and monitor the remaining cash charge schedule."),
            _change("Capital Allocation", "high", 89, "Dividend suspended and cash redirected to debt reduction", "$0.48 quarterly dividend maintained", "Dividend suspended; proceeds directed to debt reduction", "n/a", "removed", "Page 82, Section Dividends", "Page 84, Section Capital Allocation", "Management prioritized balance sheet repair over immediate shareholder distributions.", "Income-investor support may weaken, but deleveraging improves credit profile and strategic flexibility.", "Revise shareholder return assumptions and model dividend reinstatement only after leverage targets are met."),
            _change("Guidance", "high", 88, "Long-term guidance withdrawn", "Three-year revenue and EBITDA margin targets provided", "Long-term guidance withdrawn; next-quarter outlook only", "n/a", "removed", "Page 13, Section Long-Term Targets", "Page 15, Section Outlook", "Management is reducing forecast precision while restructuring execution remains uncertain.", "Forecast confidence drops and valuation should rely more on scenarios than a single base case.", "Use next-quarter guidance as the anchor and create probability-weighted restructuring cases."),
            _change("Business Risks", "high", 87, "Pension risk elevated while commodity risk decreased", "Commodity cost inflation disclosed as primary risk", "Pension underfunding elevated; commodity exposure reduced by product exits", "n/a", "new", "Page 96, Section Risk Factors", "Page 101, Section Risk Factors", "The risk profile shifted from input-cost volatility to legacy balance sheet obligations.", "Pension contributions could compete with debt reduction and operating reinvestment.", "Add pension funding requirements to the liquidity forecast and update commodity sensitivities for the new mix."),
            _change("Management Commentary", "medium", 86, "New CEO emphasizes operational discipline", "Prior CEO emphasized market recovery and growth investments", "New CEO emphasizes operational discipline, SKU exits, and cash accountability", "n/a", "new", "Page 4, Section CEO Letter", "Page 4, Section CEO Letter", "The new language supports a restructuring-first operating cadence rather than a growth-first story.", "Execution quality becomes the main valuation driver until growth guidance is restored.", "Track plant utilization, SKU exits, working capital, and restructuring milestones each quarter."),
        ],
        "summary_stats": {"total_changes": 8, "critical_changes": 0, "positive_changes": 3, "negative_changes": 4, "neutral_changes": 1},
    },
    "bank_nim": {
        "company_a": {"name": "Harbor National Bank", "period": "FY2024"},
        "company_b": {"name": "Harbor National Bank", "period": "FY2025"},
        "executive_summary": (
            "Harbor National Bank benefited from the rate-cycle shift, with net interest income up 12% and NIM expanding from 2.85% to 3.42%. "
            "That benefit was partly offset by an 8% decline in fee income as M&A activity slowed. "
            "Capital and liquidity positioning improved through preferred issuance, securities runoff, and a higher CET1 ratio, but credit risk became more prominent. "
            "The main diligence issue is whether higher credit loss provisions and elevated CRE exposure erode the earnings benefit from rates."
        ),
        "changes": [
            _change("Revenue", "high", 93, "Net interest income rose while fee income declined", "$8.4B net interest income; $2.6B fee income", "$9.4B net interest income; $2.4B fee income", "+12% NII; -8% fees", "up", "Page 40, Section Net Interest Income", "Page 43, Section Net Interest Income", "The bank is more asset-sensitive after the rate shift, but capital markets weakness is reducing non-interest revenue diversification.", "Earnings quality is more exposed to rate path and deposit beta than to advisory cycle recovery.", "Model NII and fee income separately with deposit cost and M&A volume sensitivities."),
            _change("Margin", "high", 95, "NIM expanded from 2.85% to 3.42%", "2.85% net interest margin", "3.42% net interest margin", "+20%", "up", "Page 44, Section Net Interest Margin", "Page 47, Section Net Interest Margin", "The rate-cycle benefit is flowing directly into spread income.", "Higher NIM improves pre-provision earnings, but the benefit can reverse if deposit costs catch up or rates fall.", "Stress NIM under higher deposit beta and lower reinvestment yields."),
            _change("Debt", "medium", 88, "Preferred shares issued to bolster Tier 1 capital", "No preferred issuance disclosed", "$1.0B preferred shares issued", "n/a", "new", "Page 81, Section Capital Resources", "Page 83, Section Capital Resources", "Preferred issuance strengthens regulatory capital but adds a recurring dividend burden.", "Tier 1 capital improves, while common equity returns may be modestly diluted by preferred dividends.", "Update capital stack, preferred dividend expense, and regulatory capital ratios."),
            _change("Cash Flow", "medium", 87, "Securities portfolio reduced and loan book expanded", "$42B securities portfolio; $88B loans", "$36B securities portfolio; $94B loans", "Securities -$6B; loans +$6B", "up", "Page 55, Section Balance Sheet Composition", "Page 58, Section Balance Sheet Composition", "The bank rotated balance sheet capacity from lower-yield securities into loans.", "NII can improve, but credit exposure and liquidity flexibility may become more sensitive to loan quality.", "Track loan growth by category, liquidity coverage, and unrealized securities losses."),
            _change("Capital Allocation", "high", 92, "CET1 ratio improved from 11.2% to 12.8%", "11.2% CET1 ratio", "12.8% CET1 ratio", "+14%", "up", "Page 86, Section Regulatory Capital", "Page 88, Section Regulatory Capital", "Capital accretion gives the bank more capacity to absorb credit normalization.", "The stronger CET1 ratio offsets some CRE and provision risk, supporting dividend and lending flexibility.", "Reconcile CET1 movement to retained earnings, preferred issuance, RWA growth, and loan mix."),
            _change("Guidance", "high", 90, "Credit loss provisions increased from $650M to $1.1B", "$650M credit loss provision outlook", "$1.1B credit loss provision outlook", "+69%", "up", "Page 18, Section Credit Outlook", "Page 20, Section Credit Outlook", "Management is explicitly reserving for a weaker credit backdrop despite stronger spread income.", "Higher provisions can absorb much of the NIM benefit and pressure return on equity.", "Add downside credit cases for CRE, office, and leveraged commercial borrowers."),
            _change("Business Risks", "high", 88, "CRE exposure and digital banking disruption risks elevated", "CRE risk monitored; digital banking risk not highlighted", "CRE exposure elevated; digital banking disruption added", "n/a", "new", "Page 101, Section Risk Factors", "Page 106, Section Risk Factors", "The risk profile is shifting from pure rate sensitivity to credit concentration and competitive disruption.", "CRE deterioration could raise provisions, while digital competition may pressure deposit retention and funding costs.", "Create CRE loss scenarios and monitor deposit churn by digital channel and customer cohort."),
            _change("Accounting Policy", "medium", 86, "CECL methodology adopted for credit losses", "Incurred-loss methodology disclosed", "CECL methodology adopted for credit losses", "n/a", "new", "Page 91, Section Accounting Policies", "Page 94, Section Allowance for Credit Losses", "The accounting basis for credit loss recognition changed, affecting comparability of provision expense and allowance coverage.", "Provision trends require normalization before concluding that credit quality changed by the full reported amount.", "Bridge allowance coverage and provision expense between incurred-loss and CECL bases."),
        ],
        "summary_stats": {"total_changes": 8, "critical_changes": 0, "positive_changes": 4, "negative_changes": 3, "neutral_changes": 1},
    },
}
