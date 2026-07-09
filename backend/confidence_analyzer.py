"""Confidence Analyzer — evidence-based confidence scores for financial analysis categories."""

from copy import deepcopy

def _conf(category: str, score: int, supporting: list[str], missing: list[str]) -> dict:
    return {
        "category": category,
        "score": score,
        "supporting_evidence": supporting,
        "missing_evidence": missing,
        "assessment": _assessment(score),
    }

def _assessment(score: int) -> str:
    if score >= 85: return "High — Analysis is well-supported by documented data."
    if score >= 65: return "Moderate — Key data points present but some gaps remain."
    if score >= 45: return "Low — Significant assumptions required; verify with primary sources."
    return "Very Low — Insufficient data; treat conclusions as directional only."

CONFIDENCE_PROFILES = {
    "startup": [
        _conf("Revenue", 58, [
            "Income statement data from FY2023–FY2025 filings",
            "Segment-level revenue breakdown available for all periods",
            "10-K management discussion references growth drivers",
        ], [
            "No customer cohort retention data in filings",
            "Pricing strategy not disclosed in detail",
            "Competitive market share estimates not provided",
        ]),
        _conf("Margin", 72, [
            "Gross margin trend clearly visible: 68% → 71% → 73%",
            "SBC breakdown provided in proxy statement",
            "Cost structure analysis available from income statement",
        ], [
            "Unit economics (CAC, LTV) not disclosed",
            "Cloud infrastructure cost allocation methodology unclear",
            "No margin guidance beyond current fiscal year",
        ]),
        _conf("Cash Flow", 45, [
            "Operating cash flow positive since Q3 2024",
            "CapEx cycle documented in MD&A",
            "FCF conversion improving: 62% → 74%",
        ], [
            "Working capital detail limited — AR/AP aging not provided",
            "No cash flow sensitivity analysis published",
            "Deferred revenue waterfall not fully disclosed",
        ]),
        _conf("Balance Sheet", 63, [
            "Debt schedule available: $1.5B note maturing 2027, new $2B 2030",
            "Cash reserves: $4.8B at year-end (from balance sheet)",
            "Goodwill breakdown by acquisition provided",
        ], [
            "Off-balance-sheet commitments not detailed",
            "Lease obligations summary absent",
            "No currency exposure breakdown",
        ]),
        _conf("Forecast", 49, [
            "Management guidance: FY2026 revenue +22% (from Q4 earnings call)",
            "Analyst consensus estimates available for comparison",
            "Historical CAGR of 18% over 3 years supports growth trajectory",
        ], [
            "No bottom-up revenue model provided",
            "Assumptions behind +22% guidance not disclosed",
            "No sensitivity analysis on key drivers (churn, pricing, CAC)",
            "Macro scenario planning absent from filings",
        ]),
    ],
    "manufacturing": [
        _conf("Revenue", 76, [
            "Segment revenue data: 6 business units, 3 years of history",
            "Volume/price mix analysis available in 10-K",
            "Customer concentration disclosed: top 10 = 34% of revenue",
        ], [
            "Booking/backlog data not provided quarterly",
            "Geographic revenue split at country level not provided",
        ]),
        _conf("Margin", 68, [
            "Gross margin by segment available (24% → 27% improvement)",
            "Input cost trends documented (steel, energy, labor)",
            "Restructuring charges broken out: $1.2B total",
        ], [
            "Fixed/variable cost split not provided",
            "No segment-level EBIT margins for all units",
        ]),
        _conf("Cash Flow", 81, [
            "FCF bridge from EBITDA documented in earnings release",
            "CapEx guide: $2.8B (from $3.1B prior year)",
            "Working capital trends available quarterly",
        ], [
            "Pension funding schedule incomplete",
            "No deferred tax asset/liability reconciliation",
        ]),
        _conf("Balance Sheet", 71, [
            "Total debt reduced: $8.2B → $6.5B via asset sales",
            "Pension obligation: $4.3B (from footnotes)",
            "Inventory turns: 4.2× → 4.8× improvement",
        ], [
            "Asset sale proceeds detail pending",
            "No environmental liability estimate provided",
        ]),
        _conf("Forecast", 55, [
            "Long-term guidance withdrawn; quarterly outlook only",
            "Input cost assumptions: steel -5%, energy flat",
            "Restructuring benefits estimate: $400M annual run-rate",
        ], [
            "No multi-year financial model from management",
            "Commodity price sensitivity analysis absent",
            "Volume growth assumptions not stated",
        ]),
    ],
    "saas": [
        _conf("Revenue", 82, [
            "ARR and GAAP revenue reconciliation available",
            "Customer count disclosed: enterprise 1,200, SMB 8,400",
            "NDR (net dollar retention): 118% reported",
            "Revenue by product: 3 product lines with growth rates",
        ], [
            "No usage-based vs. subscription revenue split",
            "International revenue not broken out by country",
        ]),
        _conf("Margin", 85, [
            "Gross margin: 78% (subscription) + 58% (services) detailed",
            "Customer support cost per account trended quarterly",
            "Infrastructure cost as % of revenue declining: 22% → 18%",
        ], [
            "No R&D capitalization policy detail",
        ]),
        _conf("Cash Flow", 73, [
            "FCF generation: $180M annual, 22% margin",
            "Capex light: $12M (primarily capitalized software)",
            "DSO: 42 days, improving from 48 days",
        ], [
            "No deferred commission amortization schedule",
            "Stock-based comp cash impact not isolated",
        ]),
        _conf("Balance Sheet", 69, [
            "Cash: $1.2B, no debt — from balance sheet",
            "Deferred revenue: $340M (up 28% YoY)",
            "RPO (remaining performance obligation): $890M disclosed",
        ], [
            "No acquisition goodwill impairment analysis",
            "Convertible note terms not detailed in summary",
        ]),
        _conf("Forecast", 77, [
            "FY2026 guidance: ARR $1.1B-1.15B (from Q4 call)",
            "Churn assumption: 5.2% (improving from 6.1%)",
            "Hiring plan: 200 net new heads (from investor day)",
        ], [
            "No pricing increase assumption disclosed",
            "Competitive win/loss data not provided",
            "Macro sensitivity on enterprise sales cycles absent",
        ]),
    ],
}

def get_confidence_profile(scenario: str) -> list[dict]:
    if scenario not in CONFIDENCE_PROFILES:
        raise ValueError(f"Unknown scenario '{scenario}'. Available: {list(CONFIDENCE_PROFILES.keys())}")
    return deepcopy(CONFIDENCE_PROFILES[scenario])

def get_available_confidence_scenarios() -> list[str]:
    return list(CONFIDENCE_PROFILES.keys())
