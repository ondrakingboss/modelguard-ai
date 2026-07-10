"""Peer Benchmark — industry comparison data with percentiles."""

from copy import deepcopy

def _metric(name: str, company_value: float, p25: float, p50: float, p75: float, unit: str = "%") -> dict:
    percentile = 50
    if company_value >= p75: percentile = 85
    elif company_value >= p50: percentile = 60
    elif company_value >= p25: percentile = 35
    else: percentile = 15
    
    status = "strong" if percentile >= 75 else "moderate" if percentile >= 40 else "weak"
    return {
        "name": name,
        "company_value": company_value,
        "unit": unit,
        "percentile": percentile,
        "status": status,
        "peer_p25": p25, "peer_p50": p50, "peer_p75": p75,
    }

BENCHMARKS = {
    "saas": {
        "industry": "Cloud / SaaS",
        "peers": ["NimbusForge Software Group", "CloudPeak Inc.", "DataStream Corp.", "AppForge Ltd.", "Pipeline SaaS Holdings"],
        "peer_count": 48,
        "metrics": [
            _metric("Revenue Growth", 24, 15, 22, 35),
            _metric("Gross Margin", 73, 65, 72, 78),
            _metric("EBITDA Margin", 8, 2, 10, 22),
            _metric("Net Margin", -3, -8, 2, 12),
            _metric("Debt/Equity", 0.4, 0.0, 0.3, 0.8, "×"),
            _metric("Current Ratio", 2.8, 1.5, 2.2, 3.5, "×"),
            _metric("Free Cash Flow Margin", 12, 5, 15, 28),
            _metric("ROIC", 14, 8, 18, 28),
        ],
        "strengths": [
            {"metric": "Gross Margin", "observation": "73% gross margin — above industry median of 72% (60th percentile)", "interpretation": "Indicates strong pricing power and efficient infrastructure cost management typical of scaled SaaS platforms."},
            {"metric": "Debt/Equity", "observation": "0.4× leverage — well below industry median of 0.3×", "interpretation": "Conservative capital structure leaves room for strategic debt-funded acquisitions without threatening credit quality."},
        ],
        "weaknesses": [
            {"metric": "Net Margin", "observation": "-3% net margin — below industry median of +2% (35th percentile)", "interpretation": "Profitability drag likely from SBC and amortization of acquired intangibles. Path to GAAP profitability is the key investor question."},
            {"metric": "FCF Margin", "observation": "12% FCF margin — below median of 15%", "interpretation": "CapEx cycle may be elevated. Once infrastructure investment normalizes, FCF conversion should improve."},
        ],
        "unusual": [
            {"metric": "Revenue Growth vs Profitability", "observation": "24% growth with -3% net margin", "interpretation": "Typical for Series B SaaS: strong top-line but GAAP losses. Rule of 40 score = 21 (24 + -3), below the 40 threshold investors target."},
        ],
    },
    "manufacturing": {
        "industry": "Industrial Manufacturing",
        "peers": ["Atlas Components", "SteelBridge Industries", "PrecisionForge Corp.", "Delta Manufacturing Group", "Meridian Industrial"],
        "peer_count": 36,
        "metrics": [
            _metric("Revenue Growth", -0.5, -3, 1, 5),
            _metric("Gross Margin", 27, 22, 26, 30),
            _metric("EBITDA Margin", 14, 10, 15, 20),
            _metric("Net Margin", 5, 2, 6, 10),
            _metric("Debt/Equity", 1.2, 0.8, 1.5, 2.5, "×"),
            _metric("Current Ratio", 1.8, 1.2, 1.6, 2.0, "×"),
            _metric("Free Cash Flow Margin", 8, 4, 9, 14),
            _metric("ROIC", 9, 6, 10, 15),
        ],
        "strengths": [
            {"metric": "Gross Margin", "observation": "27% — above 26% industry median (60th percentile)", "interpretation": "Portfolio rationalization and shift toward higher-margin products is yielding results."},
            {"metric": "Debt/Equity", "observation": "1.2× — well below 1.5× industry median", "interpretation": "Debt reduction via asset sales has strengthened the balance sheet."},
        ],
        "weaknesses": [
            {"metric": "Revenue Growth", "observation": "-0.5% — below 1% industry median", "interpretation": "Restructuring-related portfolio exits are masking underlying demand. Core continuing operations may show modest growth."},
            {"metric": "FCF Margin", "observation": "8% — slightly below 9% median", "interpretation": "Restructuring charges of $1.2B are compressing FCF. Excluding one-time items, normalized FCF conversion appears healthier."},
        ],
        "unusual": [
            {"metric": "Margin Improvement vs Revenue", "observation": "Margin improving (+3pp GM) while revenue flat (-0.5%)", "interpretation": "Quality-over-quantity strategy: shedding low-margin business improves profitability metrics but masks the revenue growth story."},
        ],
    },
    "financial": {
        "industry": "Banking / Financial Services",
        "peers": ["SummitBridge Financial", "First National Bancorp", "Pacific Rim Banking Group", "Metro Financial Corp.", "Heritage Trust & Savings"],
        "peer_count": 42,
        "metrics": [
            _metric("Revenue Growth", 8, 3, 7, 12),
            _metric("Net Interest Margin", 3.42, 2.8, 3.2, 3.6),
            _metric("Efficiency Ratio", 58, 60, 55, 50),
            _metric("ROE", 12.8, 9, 12, 16),
            _metric("CET1 Ratio", 12.8, 10.5, 11.5, 13.0),
            _metric("Loan/Deposit Ratio", 82, 70, 80, 90),
            _metric("NPA Ratio", 0.8, 0.5, 0.9, 1.5),
            _metric("ROIC", 10, 7, 11, 14),
        ],
        "strengths": [
            {"metric": "CET1 Ratio", "observation": "12.8% — above 11.5% industry median (75th percentile)", "interpretation": "Strong capital position exceeds regulatory requirements, providing capacity for organic growth, buybacks, or strategic M&A."},
            {"metric": "Net Interest Margin", "observation": "3.42% — above 3.2% median", "interpretation": "Asset-sensitive balance sheet is benefiting from the elevated rate environment."},
        ],
        "weaknesses": [
            {"metric": "Credit Provisions", "observation": "Provisions increased from $800M to $2.1B", "interpretation": "CECL adoption and CRE exposure are driving higher reserve builds. Credit normalization remains the primary earnings risk."},
        ],
        "unusual": [
            {"metric": "NIM Expansion vs Fee Decline", "observation": "NIM +57bps while fee income -8%", "interpretation": "Rate sensitivity cuts both ways: higher NII from loan book but M&A/wealth management fee compression in deal-making slowdown."},
        ],
    },
}

def get_benchmark(industry: str) -> dict:
    if industry not in BENCHMARKS:
        raise ValueError(f"Unknown industry '{industry}'. Available: {list(BENCHMARKS.keys())}")
    return deepcopy(BENCHMARKS[industry])

def get_available_industries() -> list[str]:
    return list(BENCHMARKS.keys())
