"""Evidence Explorer — enriches analytical insights with evidence trails."""

from copy import deepcopy

EVIDENCE_REGISTRY = {
    # === FINANCIAL INTELLIGENCE EVIDENCE ===
    "fi_startup_revenue": {
        "supporting": [
            {"source": "Income Statement — FY2023-FY2025", "location": "Page 42, Lines 12-24", "data_point": "Revenue CAGR of 18% over 3 years"},
            {"source": "Segment Reporting", "location": "Page 24, Revenue Breakdown", "data_point": "Cloud = 62% of total, growing 31% YoY"},
        ],
        "reasoning_chain": [
            "1. Historical CAGR extracted from income statements (18%)",
            "2. Forecast assumes 38% CAGR — 2.1× acceleration",
            "3. Comparable SaaS companies typically decelerate at this scale",
            "4. No new product category or market entry explains the jump",
        ],
        "assumptions": [
            "Enterprise sales cycle remains at current 9-month average",
            "No competitive pricing pressure in cloud segment",
            "Customer acquisition cost holds at $12K per enterprise logo",
        ],
        "missing": [
            "Bottom-up revenue build not provided",
            "Customer cohort expansion plans not detailed",
            "Pricing strategy for FY2026 undisclosed",
        ],
        "confidence_breakdown": "Base confidence 87% — reduced by 12% due to missing bottom-up build and pricing assumptions",
    },
    "fi_startup_margin": {
        "supporting": [
            {"source": "Income Statement — FY2023-FY2025", "location": "Page 42", "data_point": "Gross margin trend: 68% → 71% → 73%"},
            {"source": "Proxy Statement", "location": "Page 88, SBC Table", "data_point": "SBC: $420M annual, 8% of revenue"},
        ],
        "reasoning_chain": [
            "1. Gross margin improving — infrastructure efficiency gains",
            "2. Operating margin flat due to SBC growth outpacing revenue leverage",
            "3. Industry benchmark: 75% gross margin for scaled SaaS",
            "4. Gap to benchmark closing but SBC remains a drag",
        ],
        "assumptions": [
            "Cloud infrastructure costs continue declining as % of revenue",
            "No significant hiring acceleration in R&D",
        ],
        "missing": [
            "Unit economics (CAC/LTV) not disclosed",
            "No segment-level margin detail",
        ],
        "confidence_breakdown": "Base confidence 80% — reduced by 8% due to missing unit economics",
    },

    # === COMPANY INTELLIGENCE EVIDENCE (tech profile) ===
    "ci_tech_revenue_concentration": {
        "supporting": [
            {"source": "Segment Revenue Breakdown", "location": "Page 24, Revenue Table", "data_point": "Cloud: $5.8B (38%), Workflow SaaS: $3.1B (20%)"},
            {"source": "Management Discussion", "location": "Page 16, Growth Drivers", "data_point": "Cloud revenue grew 24% YoY; fastest growing segment"},
        ],
        "reasoning_chain": [
            "1. Cloud revenue = 38% of total, highest growth at 24%",
            "2. Workflow SaaS decelerating: +18% vs prior year +22%",
            "3. If Cloud growth slows to 15%, total company growth drops from 22% to ~16%",
            "4. No other segment can absorb the Cloud growth gap at current scale",
        ],
        "assumptions": [
            "Cloud TAM continues expanding at 20%+ CAGR",
            "No major competitive entrant in next 12 months",
        ],
        "missing": [
            "Cloud customer count by tier not provided",
            "No cloud retention/churn data disclosed",
        ],
        "confidence_breakdown": "Base confidence 88% — well-supported by segment data",
    },

    # === COMPANY DIFF EVIDENCE (tech_growth pair) ===
    "diff_tech_revenue": {
        "supporting": [
            {"source": "FY2024 Annual Report", "location": "Page 42, Income Statement", "data_point": "FY2024 Revenue: $12.4B"},
            {"source": "FY2025 Annual Report", "location": "Page 42, Income Statement", "data_point": "FY2025 Revenue: $15.4B (+24%)"},
            {"source": "Segment Note", "location": "Page 24 (FY2024), Page 26 (FY2025)", "data_point": "Cloud segment: $4.2B → $5.8B (+38%)"},
        ],
        "reasoning_chain": [
            "1. Total revenue growth of 24% driven primarily by Cloud (+38%)",
            "2. Workflow SaaS decelerated from +22% to +18%",
            "3. Mix shift toward Cloud improves blended gross margin",
            "4. Q4 exit rate suggests 26% growth — above full-year average",
        ],
        "assumptions": [
            "FY2025 growth trajectory sustainable through FY2026",
            "No material FX impact on international revenue",
        ],
        "missing": [
            "Revenue by geography not trended year-over-year",
            "No disclosure of large deal impact on quarterly growth",
        ],
        "confidence_breakdown": "Base confidence 92% — strong financial data support; -8% for missing geo detail",
    },
    "diff_tech_margin": {
        "supporting": [
            {"source": "FY2024 10-K", "location": "Page 44, Gross Profit", "data_point": "GM FY2024: 71%"},
            {"source": "FY2025 10-K", "location": "Page 44, Gross Profit", "data_point": "GM FY2025: 73%"},
        ],
        "reasoning_chain": [
            "1. Gross margin improvement driven by Cloud infrastructure scale",
            "2. Operating margin flat — SBC growth offset COGS leverage",
            "3. SBC increased from $380M to $420M (+10.5%)",
        ],
        "assumptions": ["Infrastructure efficiency gains continue", "No cloud provider price increases"],
        "missing": ["No segment-level gross margin disclosure"],
        "confidence_breakdown": "Base confidence 85% — clear trend but missing segment detail",
    },
}

# Default evidence for unmatched insights
DEFAULT_EVIDENCE = {
    "supporting": [
        {"source": "Financial model review", "location": "Automated scan", "data_point": "Pattern detected from workbook analysis"},
    ],
    "reasoning_chain": ["1. Automated detection identified this pattern", "2. Cross-referenced with industry benchmarks"],
    "assumptions": ["Standard financial analysis assumptions applied"],
    "missing": ["Detailed verification requires manual analyst review"],
    "confidence_breakdown": "Automated confidence — human review recommended for high-severity items",
}

def get_evidence(key: str) -> dict:
    """Return evidence trail for a given insight key, or default if unmatched."""
    return deepcopy(EVIDENCE_REGISTRY.get(key, DEFAULT_EVIDENCE))

def enrich_insights(mode: str, scenario: str, insights: list[dict]) -> list[dict]:
    """Add evidence trails to a list of insights."""
    enriched = []
    for i, insight in enumerate(insights):
        key = f"{mode}_{scenario}_{insight.get('category', '').lower().replace(' ', '_')}"
        # Try specific key first, then indexed fallback
        evidence = EVIDENCE_REGISTRY.get(key)
        if not evidence:
            evidence = EVIDENCE_REGISTRY.get(f"{mode}_{scenario}_{i}", DEFAULT_EVIDENCE)
        
        enriched_insight = deepcopy(insight)
        enriched_insight["evidence"] = deepcopy(evidence) if evidence else deepcopy(DEFAULT_EVIDENCE)
        enriched.append(enriched_insight)
    return enriched
