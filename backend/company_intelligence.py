from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


INDUSTRIES = ("tech", "industrial", "financial")


def get_company_industries() -> list[str]:
    return list(INDUSTRIES)


def get_demo_profile(industry: str) -> dict[str, Any]:
    try:
        return deepcopy(DEMO_PROFILES[industry])
    except KeyError as exc:
        raise ValueError(f"Unknown industry '{industry}'. Expected one of: {', '.join(INDUSTRIES)}") from exc


def build_company_profile(parsed_pdf: dict[str, Any]) -> dict[str, Any]:
    text = parsed_pdf.get("text", "") or ""
    tables = parsed_pdf.get("tables", []) or []
    financial_data = parsed_pdf.get("financial_data", {}) or {}

    company_name = _extract_company_name(text)
    filing_type = _extract_filing_type(text)
    filing_period = _extract_filing_period(text)
    industry = _infer_industry(text)

    revenue_segments = _extract_revenue_segments(financial_data, tables)
    geographic_exposure = _extract_geographic_exposure(financial_data, tables)
    risks = _extract_risks(text)
    debt_structure = _extract_debt_structure(financial_data)
    capital_allocation = _extract_capital_allocation(text)
    profitability = _extract_profitability(financial_data)
    cash_generation = _extract_cash_generation(financial_data)

    missing_information = _missing_information(
        {
            "company_name": company_name,
            "revenue_segments": revenue_segments,
            "geographic_exposure": geographic_exposure,
            "major_risks": risks,
            "debt_structure": debt_structure,
            "capital_allocation": capital_allocation,
            "profitability_trends": profitability,
            "cash_generation": cash_generation,
        }
    )

    business_profile = {
        "revenue_segments": revenue_segments,
        "geographic_exposure": geographic_exposure,
        "major_risks": risks,
        "debt_structure": debt_structure,
        "capital_allocation": capital_allocation,
        "profitability_trends": profitability,
        "cash_generation": cash_generation,
        "missing_information": missing_information,
    }

    insights = _generate_insights(business_profile, filing_type)

    return {
        "company_name": company_name or "Not found in document",
        "industry": industry,
        "filing_type": filing_type,
        "filing_period": filing_period,
        "business_profile": business_profile,
        "insights": insights,
        "executive_summary": _executive_summary(company_name, filing_type, filing_period, business_profile, insights),
    }


def _extract_company_name(text: str) -> str:
    for pattern in (
        r"\n\s*([A-Z][A-Z0-9&.,' -]{3,80})\s*\n\s*(?:Annual Report|Form 10-K|10-K)",
        r"(?:Registrant|Company Name)\s*[:\-]\s*([A-Z][A-Za-z0-9&.,' -]{3,80})",
    ):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return _title(match.group(1))
    first_lines = [line.strip() for line in text.splitlines()[:30] if line.strip()]
    for line in first_lines:
        if 3 <= len(line) <= 80 and not line.startswith("[Page") and not re.search(r"\d{4}", line):
            return _title(line)
    return ""


def _extract_filing_type(text: str) -> str:
    lowered = text.lower()
    if "quarterly report" in lowered or "form 10-q" in lowered or "10-q" in lowered:
        return "Quarterly Report"
    if "investor presentation" in lowered or "investor day" in lowered:
        return "Investor Presentation"
    return "Annual Report"


def _extract_filing_period(text: str) -> str:
    patterns = (
        r"(?:fiscal year|year|quarter|period)\s+ended\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        r"(?:for the year ended|for the quarter ended)\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        r"\b(20\d{2})\s+(?:annual report|form 10-k|form 10-q)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return "Not found in document"


def _infer_industry(text: str) -> str:
    lowered = text.lower()
    scores = {
        "technology / software": ["cloud", "software", "subscription", "saas", "platform", "data center"],
        "industrial / manufacturing": ["manufacturing", "plant", "raw material", "supply chain", "inventory", "factory"],
        "financial services": ["loan", "deposit", "net interest", "credit loss", "capital ratio", "bank"],
    }
    best = max(scores, key=lambda key: sum(term in lowered for term in scores[key]))
    return best if any(term in lowered for term in scores[best]) else "Not found in document"


def _extract_revenue_segments(financial_data: dict[str, Any], tables: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = _candidate_table_rows(tables, ("revenue", "sales", "segment"))
    segments: list[dict[str, str]] = []
    for page, row in rows:
        joined = " | ".join(row)
        name = next((cell for cell in row if re.search(r"[A-Za-z]", cell) and not _looks_like_header(cell)), "")
        amount = _first_amount(joined)
        growth = _first_percent(joined)
        if name and amount:
            segments.append({"name": name, "revenue": amount, "growth": growth or "Not found", "page_ref": f"Page {page}"})
        if len(segments) >= 8:
            return segments

    for item in financial_data.get("revenue_segments", [])[:5]:
        segments.append(
            {
                "name": "Revenue detail",
                "revenue": _first_amount(item["text"]) or "See referenced text",
                "growth": _first_percent(item["text"]) or "Not found",
                "page_ref": item["page_ref"],
            }
        )
    return segments


def _extract_geographic_exposure(financial_data: dict[str, Any], tables: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows = _candidate_table_rows(tables, ("geographic", "region", "international", "americas", "emea", "apac"))
    regions: list[dict[str, str]] = []
    for page, row in rows:
        joined = " | ".join(row)
        region = next((cell for cell in row if re.search(r"[A-Za-z]", cell) and not _looks_like_header(cell)), "")
        pct = _first_percent(joined)
        if region:
            regions.append({"region": region, "revenue_pct": pct or "Not found", "page_ref": f"Page {page}"})
        if len(regions) >= 5:
            return regions

    for item in financial_data.get("geographic_exposure", [])[:5]:
        regions.append({"region": "Geographic exposure detail", "revenue_pct": _first_percent(item["text"]) or "Not found", "page_ref": item["page_ref"]})
    return regions


def _extract_risks(text: str) -> list[dict[str, str]]:
    page_blocks = _page_blocks(text)
    risks: list[dict[str, str]] = []
    for page, block in page_blocks:
        if "risk" not in block.lower():
            continue
        for sentence in _sentences(block):
            lowered = sentence.lower()
            if "risk" not in lowered and "could adversely" not in lowered and "may adversely" not in lowered:
                continue
            risks.append({"risk": _shorten(sentence, 240), "category": _risk_category(sentence), "page_ref": f"Page {page}"})
            if len(risks) >= 6:
                return risks
    return risks


def _extract_debt_structure(financial_data: dict[str, Any]) -> dict[str, str]:
    snippets = financial_data.get("debt_structure", [])
    text = " ".join(item["text"] for item in snippets)
    page_ref = _first_page(snippets)
    return {
        "total_debt": _first_amount(text) or "Not found",
        "maturity_profile": _snippet_with(text, ("matur", "due", "senior notes")) or "Not found",
        "covenants": _snippet_with(text, ("covenant", "leverage ratio", "credit facility")) or "Not found",
        "page_ref": page_ref,
    }


def _extract_capital_allocation(text: str) -> dict[str, str]:
    snippets = _snippets_for_terms(text, ("capital expenditure", "capex", "repurchase", "buyback", "dividend", "acquisition"))
    joined = " ".join(item["text"] for item in snippets)
    return {
        "capex": _snippet_with(joined, ("capital expenditure", "capex")) or "Not found",
        "buybacks": _snippet_with(joined, ("repurchase", "buyback")) or "Not found",
        "dividends": _snippet_with(joined, ("dividend",)) or "Not found",
        "m_and_a": _snippet_with(joined, ("acquisition", "merger")) or "Not found",
        "page_ref": _first_page(snippets),
    }


def _extract_profitability(financial_data: dict[str, Any]) -> dict[str, str]:
    snippets = financial_data.get("profitability", [])
    text = " ".join(item["text"] for item in snippets)
    return {
        "gross_margin": _snippet_with(text, ("gross margin", "gross profit")) or "Not found",
        "operating_margin": _snippet_with(text, ("operating margin", "operating income")) or "Not found",
        "net_margin": _snippet_with(text, ("net margin", "net income")) or "Not found",
        "page_ref": _first_page(snippets),
    }


def _extract_cash_generation(financial_data: dict[str, Any]) -> dict[str, str]:
    snippets = financial_data.get("cash_flow", [])
    text = " ".join(item["text"] for item in snippets)
    return {
        "operating_cf": _snippet_with(text, ("operating cash", "cash provided by operating")) or "Not found",
        "free_cf": _snippet_with(text, ("free cash flow", "capital expenditures")) or "Not found",
        "fcf_conversion": _snippet_with(text, ("conversion", "free cash flow")) or "Not found",
        "page_ref": _first_page(snippets),
    }


def _generate_insights(business_profile: dict[str, Any], filing_type: str) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    if business_profile["revenue_segments"]:
        first = business_profile["revenue_segments"][0]
        insights.append(_insight("Revenue Mix", "Documented revenue segmentation requires concentration review", f"The filing identifies {first['name']} with revenue detail of {first['revenue']}.", first["page_ref"], "Segment mix can materially affect growth durability, margin profile, and valuation multiple.", "Build a segment bridge for the next quarterly review and compare growth by segment against total company growth.", 78))
    if business_profile["geographic_exposure"]:
        first = business_profile["geographic_exposure"][0]
        insights.append(_insight("Geographic Exposure", "International footprint may add currency and demand sensitivity", f"The document references {first['region']} with exposure detail of {first['revenue_pct']}.", first["page_ref"], "Regional concentration can create FX, macro, and regulatory volatility in reported revenue.", "Track revenue growth on a constant-currency basis and isolate country-level demand changes where disclosed.", 74))
    if business_profile["major_risks"]:
        risk = business_profile["major_risks"][0]
        insights.append(_insight("Risk Factors", "Primary disclosed risk requires operating owner", risk["risk"], risk["page_ref"], "A material disclosed risk can affect forecast reliability and cost of capital if not tied to mitigation metrics.", "Assign an owner and KPI for this risk; test the downside case in the operating plan.", 82))
    if business_profile["debt_structure"]["total_debt"] != "Not found":
        debt = business_profile["debt_structure"]
        insights.append(_insight("Capital Structure", "Debt disclosure should be reconciled to liquidity plan", f"Debt disclosure indicates total debt or borrowings of {debt['total_debt']}.", debt["page_ref"], "Debt maturities and covenant limits can constrain capital allocation during weaker operating periods.", "Create a maturity schedule and covenant cushion view for base, downside, and stress cases.", 80))
    if business_profile["cash_generation"]["operating_cf"] != "Not found":
        cash = business_profile["cash_generation"]
        insights.append(_insight("Cash Flow", "Operating cash flow disclosure supports cash conversion analysis", cash["operating_cf"], cash["page_ref"], "Cash conversion determines whether reported earnings can fund growth, debt service, and shareholder returns.", "Reconcile operating cash flow to EBITDA and identify working-capital drivers.", 79))
    if not insights:
        insights.append(_insight("Document Coverage", "Insufficient financial evidence extracted", f"The uploaded {filing_type.lower()} did not expose enough structured financial text for reliable analysis.", "Section: Extracted PDF text", "The absence of usable disclosures prevents defensible conclusions about revenue mix, margins, leverage, or cash generation.", "Upload a searchable annual report, quarterly filing, or investor presentation with financial statement pages.", 45))
    return insights


def _insight(category: str, title: str, finding: str, page_reference: str, financial_implication: str, recommended_action: str, confidence: int) -> dict[str, Any]:
    return {
        "category": category,
        "title": title,
        "finding": finding,
        "page_reference": page_reference,
        "financial_implication": financial_implication,
        "recommended_action": recommended_action,
        "confidence": confidence,
    }


def _executive_summary(company_name: str, filing_type: str, filing_period: str, business_profile: dict[str, Any], insights: list[dict[str, Any]]) -> str:
    name = company_name or "The company"
    missing_count = len(business_profile["missing_information"])
    insight_line = insights[0]["finding"] if insights else "The document provides limited analyzable detail."
    return (
        f"{name} was analyzed from a {filing_type.lower()} for {filing_period}. "
        f"The strongest extracted evidence is: {insight_line} "
        "The profile only uses information found in the uploaded PDF and marks unsupported fields as not found. "
        f"{missing_count} information gaps remain and should be resolved before using this analysis for investment or credit decisions."
    )


def _missing_information(profile: dict[str, Any]) -> list[str]:
    checks = [
        ("company_name", "Company name was not clearly identified."),
        ("revenue_segments", "Revenue segment detail was not found."),
        ("geographic_exposure", "Geographic revenue exposure was not found."),
        ("major_risks", "Major risk factor disclosure was not found."),
    ]
    missing = [message for key, message in checks if not profile[key]]
    for key, label in (
        ("debt_structure", "Debt structure"),
        ("capital_allocation", "Capital allocation"),
        ("profitability_trends", "Profitability trends"),
        ("cash_generation", "Cash generation"),
    ):
        values = profile[key]
        if all(value == "Not found" for field, value in values.items() if field != "page_ref"):
            missing.append(f"{label} detail was not found.")
    return missing


def _candidate_table_rows(tables: list[dict[str, Any]], terms: tuple[str, ...]) -> list[tuple[int, list[str]]]:
    matches: list[tuple[int, list[str]]] = []
    for table in tables:
        page = table.get("page", 0)
        for row in table.get("rows", []):
            cells = [str(cell).strip() for cell in row if str(cell).strip()]
            if not cells:
                continue
            joined = " ".join(cells).lower()
            if any(term in joined for term in terms) or matches:
                matches.append((page, cells))
            if len(matches) >= 12:
                return matches
    return matches


def _page_blocks(text: str) -> list[tuple[int, str]]:
    matches = list(re.finditer(r"\[Page\s+(\d+)\]", text))
    blocks: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((int(match.group(1)), text[match.end() : end]))
    return blocks


def _snippets_for_terms(text: str, terms: tuple[str, ...]) -> list[dict[str, str]]:
    snippets: list[dict[str, str]] = []
    for page, block in _page_blocks(text):
        for sentence in _sentences(block):
            if any(term in sentence.lower() for term in terms):
                snippets.append({"page_ref": f"Page {page}", "text": _shorten(sentence, 350)})
    return snippets[:8]


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text)) if part.strip()]


def _snippet_with(text: str, terms: tuple[str, ...]) -> str:
    for sentence in _sentences(text):
        if any(term in sentence.lower() for term in terms):
            return _shorten(sentence, 350)
    return ""


def _first_amount(text: str) -> str:
    match = re.search(r"[$€£]?\s?\(?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?\s?(?:million|billion|m|bn)?", text, re.IGNORECASE)
    return match.group(0).strip() if match else ""


def _first_percent(text: str) -> str:
    match = re.search(r"\(?-?\d+(?:\.\d+)?%\)?", text)
    return match.group(0) if match else ""


def _first_page(snippets: list[dict[str, str]]) -> str:
    return snippets[0]["page_ref"] if snippets else "Not found"


def _risk_category(sentence: str) -> str:
    lowered = sentence.lower()
    if any(term in lowered for term in ("regulation", "compliance", "legal")):
        return "regulatory"
    if any(term in lowered for term in ("competition", "demand", "market", "price")):
        return "market"
    if any(term in lowered for term in ("debt", "liquidity", "interest", "credit")):
        return "financial"
    if any(term in lowered for term in ("strategy", "acquisition", "integration")):
        return "strategic"
    return "operational"


def _looks_like_header(cell: str) -> bool:
    return cell.lower() in {"revenue", "sales", "segment", "total", "region", "geographic area"}


def _shorten(text: str, limit: int = 300) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 3].rsplit(" ", 1)[0] + "..."


def _title(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" -")
    return value if not value.isupper() else value.title()


DEMO_PROFILES: dict[str, dict[str, Any]] = {
    "tech": {
        "company_name": "NimbusForge Software Group",
        "industry": "Cloud / SaaS",
        "filing_type": "Annual Report",
        "filing_period": "Fiscal year ended December 31, 2025",
        "business_profile": {
            "revenue_segments": [
                {"name": "Cloud Infrastructure", "revenue": "$5.8B", "growth": "24%", "page_ref": "Page 24"},
                {"name": "Workflow SaaS", "revenue": "$3.1B", "growth": "18%", "page_ref": "Page 24"},
                {"name": "Data Analytics", "revenue": "$2.0B", "growth": "31%", "page_ref": "Page 25"},
                {"name": "Cybersecurity", "revenue": "$1.4B", "growth": "27%", "page_ref": "Page 25"},
                {"name": "Professional Services", "revenue": "$840M", "growth": "6%", "page_ref": "Page 26"},
                {"name": "Marketplace and Integrations", "revenue": "$620M", "growth": "22%", "page_ref": "Page 26"},
            ],
            "geographic_exposure": [
                {"region": "North America", "revenue_pct": "58%", "page_ref": "Page 31"},
                {"region": "EMEA", "revenue_pct": "25%", "page_ref": "Page 31"},
                {"region": "Asia Pacific", "revenue_pct": "12%", "page_ref": "Page 32"},
                {"region": "Latin America", "revenue_pct": "5%", "page_ref": "Page 32"},
            ],
            "major_risks": [
                {"risk": "Enterprise cloud demand could slow as customers optimize usage.", "category": "market", "page_ref": "Page 49"},
                {"risk": "Security incidents could increase churn and remediation expense.", "category": "operational", "page_ref": "Page 52"},
                {"risk": "AI and data privacy regulation may limit product deployment in regulated markets.", "category": "regulatory", "page_ref": "Page 55"},
                {"risk": "Acquisition integration failures could dilute margins.", "category": "strategic", "page_ref": "Page 58"},
                {"risk": "Stock-based compensation may create dilution pressure.", "category": "financial", "page_ref": "Page 73"},
            ],
            "debt_structure": {
                "total_debt": "$2.2B",
                "maturity_profile": "$750M 3.10% notes due 2028, $650M 3.85% notes due 2031, $800M 4.20% notes due 2035",
                "covenants": "Revolving credit facility requires minimum liquidity of $750M and debt-to-EBITDA below 3.5x.",
                "page_ref": "Page 91",
            },
            "capital_allocation": {
                "capex": "$1.1B for data center capacity and internal systems",
                "buybacks": "$2.4B share repurchase authorization used to offset dilution",
                "dividends": "No regular dividend declared",
                "m_and_a": "$1.7B deployed across three security and analytics acquisitions",
                "page_ref": "Page 84",
            },
            "profitability_trends": {"gross_margin": "78.4%, up 120 bps", "operating_margin": "23.6%, up 260 bps", "net_margin": "19.8%, up 190 bps", "page_ref": "Page 39"},
            "cash_generation": {"operating_cf": "$4.3B", "free_cf": "$3.2B", "fcf_conversion": "29% of revenue", "page_ref": "Page 67"},
            "missing_information": ["Customer count by contract size is not disclosed.", "Remaining performance obligation by geography is not disclosed."],
        },
        "insights": [
            _insight("Revenue Concentration", "Cloud division drives majority of incremental growth", "Cloud Infrastructure represents the largest segment at $5.8B and is growing 24%.", "Page 24", "A cloud slowdown would disproportionately reduce consolidated growth and operating leverage.", "Monitor cloud usage growth, renewal pricing, and committed spend every quarter.", 90),
            _insight("Margin Quality", "Strong SaaS margins support valuation premium", "Gross margin expanded to 78.4% while operating margin reached 23.6%.", "Page 39", "Sustained margin expansion can offset higher R&D and acquisition amortization.", "Separate organic margin expansion from acquisition mix and hosting optimization.", 86),
            _insight("Capital Allocation", "Buybacks mostly offset dilution", "$2.4B of buybacks were used while stock-based compensation remains material.", "Page 84", "Repurchases may protect per-share metrics but consume cash that could fund acquisitions or resilience.", "Track net share count reduction, not gross repurchase dollars.", 82),
            _insight("M&A Strategy", "Acquisitions are central to product expansion", "$1.7B was deployed across security and analytics acquisitions.", "Page 84", "Integration risk could affect retention, product roadmap timing, and acquired gross margins.", "Review acquired ARR retention and integration cost milestones.", 80),
            _insight("Liquidity", "Debt maturity ladder appears manageable", "$2.2B debt is spread across 2028, 2031, and 2035 maturities.", "Page 91", "Large cash reserves and staggered maturities lower refinancing pressure.", "Maintain a covenant cushion report under a lower-growth scenario.", 84),
            _insight("Regulatory", "AI privacy rules may constrain regulated-sector adoption", "The filing highlights privacy regulation risk for AI-enabled products.", "Page 55", "Compliance delays could lengthen sales cycles and increase product cost.", "Map AI product releases to jurisdiction-specific approval requirements.", 78),
        ],
        "executive_summary": "NimbusForge is a high-margin cloud software company with broad but cloud-led revenue growth. The profile shows strong cash generation, sizable R&D investment, and an acquisition-led expansion strategy. The main analytical issues are cloud concentration, stock-based compensation dilution, and AI privacy regulation. Liquidity appears sound given cash reserves and staggered debt maturities, but management should prove acquisition integration and organic margin quality.",
    },
    "industrial": {
        "company_name": "HarborWorks Industrial Holdings",
        "industry": "Industrial Manufacturing / Conglomerate",
        "filing_type": "Annual Report",
        "filing_period": "Fiscal year ended December 31, 2025",
        "business_profile": {
            "revenue_segments": [
                {"name": "Motion Systems", "revenue": "$4.4B", "growth": "5%", "page_ref": "Page 22"},
                {"name": "Industrial Automation", "revenue": "$3.6B", "growth": "8%", "page_ref": "Page 22"},
                {"name": "Power Components", "revenue": "$2.9B", "growth": "2%", "page_ref": "Page 23"},
                {"name": "Aerospace Components", "revenue": "$2.1B", "growth": "11%", "page_ref": "Page 23"},
                {"name": "Aftermarket Services", "revenue": "$1.8B", "growth": "7%", "page_ref": "Page 24"},
                {"name": "Specialty Materials", "revenue": "$1.2B", "growth": "-1%", "page_ref": "Page 24"},
            ],
            "geographic_exposure": [
                {"region": "United States", "revenue_pct": "46%", "page_ref": "Page 30"},
                {"region": "Europe", "revenue_pct": "27%", "page_ref": "Page 30"},
                {"region": "China", "revenue_pct": "11%", "page_ref": "Page 31"},
                {"region": "Rest of Asia", "revenue_pct": "9%", "page_ref": "Page 31"},
                {"region": "Other Americas", "revenue_pct": "7%", "page_ref": "Page 31"},
            ],
            "major_risks": [
                {"risk": "Supply chain disruption could limit production and raise freight costs.", "category": "operational", "page_ref": "Page 44"},
                {"risk": "Commodity price increases may not be fully recoverable through customer pricing.", "category": "market", "page_ref": "Page 46"},
                {"risk": "Pension asset returns and discount rates can affect funded status.", "category": "financial", "page_ref": "Page 63"},
                {"risk": "Export controls and industrial safety rules add compliance burden.", "category": "regulatory", "page_ref": "Page 48"},
                {"risk": "Restructuring programs may fail to deliver planned savings.", "category": "strategic", "page_ref": "Page 57"},
            ],
            "debt_structure": {
                "total_debt": "$5.6B",
                "maturity_profile": "$900M due 2027, $1.2B due 2029, $1.5B due 2032, remainder 2036-2045",
                "covenants": "Bank facilities require leverage below 3.75x and interest coverage above 3.0x.",
                "page_ref": "Page 88",
            },
            "capital_allocation": {
                "capex": "$1.35B, including $620M maintenance and $730M growth/automation projects",
                "buybacks": "$650M opportunistic repurchases",
                "dividends": "$780M common dividends, 41% payout ratio",
                "m_and_a": "$420M bolt-on acquisitions; $310M divestiture proceeds",
                "page_ref": "Page 76",
            },
            "profitability_trends": {"gross_margin": "31.2%, down 80 bps", "operating_margin": "13.7%, up 40 bps after restructuring", "net_margin": "8.9%, flat", "page_ref": "Page 36"},
            "cash_generation": {"operating_cf": "$2.4B", "free_cf": "$1.1B", "fcf_conversion": "74% of adjusted net income", "page_ref": "Page 69"},
            "missing_information": ["Backlog by business unit is not disclosed.", "Commodity hedge coverage by material is not disclosed.", "Plant-level capacity utilization is not disclosed."],
        },
        "insights": [
            _insight("Cyclicality", "Automation and motion demand remain economically sensitive", "Motion Systems and Industrial Automation together represent $8.0B of revenue.", "Page 22", "A downturn in industrial production would pressure volume, absorption, and distributor inventory.", "Stress test EBITDA under lower order intake and slower backlog conversion.", 87),
            _insight("Commodity Exposure", "Price-cost spread is the key margin risk", "Gross margin declined 80 bps while commodity sensitivity is disclosed as a risk.", "Pages 36 and 46", "Input cost inflation can erase restructuring savings if price realization lags.", "Build a monthly price-cost waterfall by business unit.", 84),
            _insight("CapEx Intensity", "Automation plan requires return discipline", "$1.35B of CapEx includes $730M for growth and automation.", "Page 76", "Free cash flow could disappoint if projects miss throughput or labor-saving targets.", "Require post-completion ROI reviews for each major CapEx program.", 81),
            _insight("Pension", "Pension assumptions add balance sheet volatility", "The filing identifies pension discount rate and asset return sensitivity.", "Page 63", "Lower discount rates or weak asset returns could increase contributions and reduce free cash flow.", "Review funded status sensitivity and required contributions under downside rates.", 79),
            _insight("Debt", "Leverage covenants need recession cushion", "$5.6B of debt is subject to leverage and coverage covenants.", "Page 88", "A cyclical EBITDA decline could reduce covenant headroom.", "Track leverage under a 15% EBITDA downside and working-capital build.", 83),
            _insight("Restructuring", "Savings must be separated from recurring performance", "Operating margin improved after restructuring programs.", "Page 36", "One-time cost actions can mask weak underlying volume or mix.", "Bridge margin improvement between restructuring savings, price, volume, mix, and productivity.", 80),
        ],
        "executive_summary": "HarborWorks is a diversified industrial manufacturer with balanced business units but meaningful cyclical and commodity exposure. Revenue growth is moderate, while margin quality depends on price-cost execution and restructuring savings. The balance sheet is serviceable but requires covenant monitoring if industrial demand weakens. CapEx and pension obligations are central to free cash flow analysis.",
    },
    "financial": {
        "company_name": "SummitBridge Financial Corp.",
        "industry": "Banking / Financial Services",
        "filing_type": "Annual Report",
        "filing_period": "Fiscal year ended December 31, 2025",
        "business_profile": {
            "revenue_segments": [
                {"name": "Commercial Banking Net Interest Income", "revenue": "$3.9B", "growth": "7%", "page_ref": "Page 28"},
                {"name": "Consumer Banking Net Interest Income", "revenue": "$2.8B", "growth": "4%", "page_ref": "Page 28"},
                {"name": "Wealth Management Fees", "revenue": "$1.4B", "growth": "9%", "page_ref": "Page 29"},
                {"name": "Card and Payment Fees", "revenue": "$1.1B", "growth": "6%", "page_ref": "Page 29"},
                {"name": "Mortgage Banking", "revenue": "$740M", "growth": "-3%", "page_ref": "Page 30"},
                {"name": "Capital Markets and Advisory", "revenue": "$690M", "growth": "12%", "page_ref": "Page 30"},
            ],
            "geographic_exposure": [
                {"region": "Northeast U.S.", "revenue_pct": "34%", "page_ref": "Page 34"},
                {"region": "Southeast U.S.", "revenue_pct": "24%", "page_ref": "Page 34"},
                {"region": "Midwest U.S.", "revenue_pct": "18%", "page_ref": "Page 35"},
                {"region": "Western U.S.", "revenue_pct": "16%", "page_ref": "Page 35"},
                {"region": "International", "revenue_pct": "8%", "page_ref": "Page 35"},
            ],
            "major_risks": [
                {"risk": "Credit losses may increase if commercial real estate values decline.", "category": "financial", "page_ref": "Page 50"},
                {"risk": "Deposit competition could raise funding costs and pressure net interest margin.", "category": "market", "page_ref": "Page 53"},
                {"risk": "Capital and liquidity rules may require higher retained capital.", "category": "regulatory", "page_ref": "Page 57"},
                {"risk": "Cybersecurity or payment outages could disrupt customer activity.", "category": "operational", "page_ref": "Page 61"},
                {"risk": "Expansion into wealth management depends on advisor retention.", "category": "strategic", "page_ref": "Page 64"},
            ],
            "debt_structure": {
                "total_debt": "$7.8B",
                "maturity_profile": "$1.1B senior bank notes due 2027, $2.0B holding company notes due 2029-2031, $4.7B FHLB advances under one year",
                "covenants": "Regulatory capital requirements include CET1 ratio above well-capitalized thresholds; holding company maintains double leverage limits.",
                "page_ref": "Page 96",
            },
            "capital_allocation": {
                "capex": "$290M technology, branch modernization, and risk systems spend",
                "buybacks": "$900M share repurchases subject to stress capital buffer",
                "dividends": "$1.1B common dividends, 36% payout ratio",
                "m_and_a": "$250M wealth advisory acquisition; no bank acquisitions closed",
                "page_ref": "Page 83",
            },
            "profitability_trends": {"gross_margin": "Not applicable for bank", "operating_margin": "Pre-provision net revenue margin 34.5%", "net_margin": "Return on average assets 1.18%; return on tangible common equity 15.2%", "page_ref": "Page 41"},
            "cash_generation": {"operating_cf": "$3.6B", "free_cf": "Not disclosed as a bank metric", "fcf_conversion": "Not disclosed", "page_ref": "Page 72"},
            "missing_information": ["Loan-to-value distribution for commercial real estate is not disclosed.", "Uninsured deposit concentration by customer segment is not disclosed."],
        },
        "insights": [
            _insight("Net Interest Income", "Balance sheet spread remains core earnings driver", "Commercial and consumer banking net interest income totals $6.7B.", "Page 28", "Deposit repricing or loan yield pressure would directly affect earnings power.", "Track net interest margin sensitivity to rate cuts and deposit beta changes.", 88),
            _insight("Credit Quality", "CRE credit exposure is the highest disclosed risk", "The filing flags potential credit losses from commercial real estate value declines.", "Page 50", "Higher provisions would reduce net income and regulatory capital generation.", "Review criticized loans, office exposure, reserves, and borrower debt-service coverage.", 86),
            _insight("Funding", "Deposit competition can pressure margin", "Management identifies deposit competition and higher funding costs as a risk.", "Page 53", "Rising deposit costs can offset loan yield benefits and weaken NIM.", "Monitor noninterest-bearing deposits, deposit beta, and customer concentration monthly.", 84),
            _insight("Capital", "Capital return depends on regulatory buffer", "$900M of buybacks are subject to stress capital buffer constraints.", "Page 83", "Buybacks could be reduced if provisions rise or risk-weighted assets grow.", "Model CET1 under adverse credit and rate scenarios before approving repurchases.", 82),
            _insight("Fee Income", "Wealth and payments diversify spread revenue", "Wealth fees and card/payment fees total $2.5B.", "Page 29", "Fee diversification can stabilize earnings when rate spreads compress.", "Measure fee income growth net of advisor payout and payment loss costs.", 80),
            _insight("Liquidity", "Short-term FHLB advances require active funding plan", "$4.7B of FHLB advances mature within one year.", "Page 96", "Short maturity funding increases refinancing and margin risk if wholesale rates remain elevated.", "Prepare replacement funding scenarios using deposits, securities runoff, and term debt.", 85),
        ],
        "executive_summary": "SummitBridge is a regional financial services company whose earnings remain anchored in net interest income, with growing wealth and payment fees. Credit quality, deposit funding cost, and regulatory capital are the most important drivers to monitor. The company returns capital through dividends and buybacks, but repurchases depend on stress capital capacity. Short-term wholesale funding and CRE exposure require closer liquidity and credit surveillance.",
    },
}
