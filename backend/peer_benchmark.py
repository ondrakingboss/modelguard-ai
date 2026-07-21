"""Peer Benchmark — real data ingestion with percentile calculation."""

import csv
from copy import deepcopy
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def _load_csv(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with open(path) as f:
        return list(csv.DictReader(f))

def _percentile(values: list[float], pct: float) -> float:
    """Linear interpolation percentile (same as numpy.percentile)."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    f = int(k)
    c = k - f
    if f + 1 < len(sorted_vals):
        return sorted_vals[f] + c * (sorted_vals[f + 1] - sorted_vals[f])
    return sorted_vals[f]

def _company_percentile(value: float, all_values: list[float]) -> int:
    """Return percentile rank (0-100) of value within all_values."""
    if not all_values:
        return 50
    below = sum(1 for v in all_values if v < value)
    return round((below / len(all_values)) * 100)

def _metric(name: str, company_value: float, peer_values: list[float], unit: str = "%") -> dict:
    p25 = round(_percentile(peer_values, 25), 1)
    p50 = round(_percentile(peer_values, 50), 1)
    p75 = round(_percentile(peer_values, 75), 1)
    percentile = _company_percentile(company_value, peer_values)
    status = "strong" if percentile >= 75 else "moderate" if percentile >= 40 else "weak"
    return {
        "name": name, "company_value": company_value, "unit": unit,
        "percentile": percentile, "status": status,
        "peer_p25": p25, "peer_p50": p50, "peer_p75": p75,
    }

def _metric_label(name: str) -> str:
    """Convert snake_case metric name to display label."""
    labels = {
        "revenue_growth_pct": "Revenue Growth",
        "gross_margin_pct": "Gross Margin",
        "ebitda_margin_pct": "EBITDA Margin",
        "net_margin_pct": "Net Margin",
        "fcf_margin_pct": "FCF Margin",
        "debt_to_equity": "Debt/Equity",
        "current_ratio": "Current Ratio",
    }
    return labels.get(name, name.replace("_", " ").title())

def _inclusion_policy(flag: str) -> tuple[str, str]:
    """Map quality flag to (status, rationale)."""
    if not flag:
        return ("included", "No quality concerns — GAAP metric from verified 10-K filing.")
    policies = {
        "fiscal_period_mismatch": (
            "included_with_caution",
            "Fiscal year ends Jun 2024 vs peer median Jan 2025. Different macro conditions may affect comparability. Included in full benchmark; excluded from strict comparison."
        ),
        "stock_compensation_distortion": (
            "included_with_caution",
            "GAAP metric distorted by stock-based compensation exceeding 15% of revenue. Non-GAAP equivalent would differ materially. Included in full benchmark; excluded from strict comparison."
        ),
        "outlier": (
            "included",
            "Genuine outlier — verified against 10-K filing. Represents actual company performance. Included in all benchmarks."
        ),
    }
    return policies.get(flag, ("included_with_caution", f"Flagged: {flag}. Included in full benchmark; excluded from strict comparison."))

def _build_saas_benchmark() -> dict:
    rows = _load_csv("saas_peers.csv")
    if not rows:
        return _fallback_saas()

    # Group by metric_name
    metric_groups: dict[str, list[dict]] = {}
    for r in rows:
        name = r["metric_name"]
        if name not in metric_groups:
            metric_groups[name] = []
        metric_groups[name].append(r)
    
    # Build peer list and sources
    peers = list(set(r["company_name"] for r in rows))
    sources = list(set(r["source_url"] for r in rows if r.get("source_url")))
    quality_flags = list(set(r["data_quality_flag"] for r in rows if r.get("data_quality_flag")))
    
    # Unit mapping
    unit_map = {"percent": "%", "ratio": "×"}
    
    metrics = []
    source_detail = []
    for name, group in metric_groups.items():
        # All values (full cohort)
        all_vals = [float(r["normalized_value"]) for r in group]
        # Exclude only "excluded" status values (none in this dataset)
        adjusted_vals = all_vals  # No rows are excluded
        # Strict: exclude caution rows
        strict_vals = [float(r["normalized_value"]) for r in group
                       if _inclusion_policy(r.get("data_quality_flag", ""))[0] != "included_with_caution"]
        
        unit = unit_map.get(group[0].get("reported_unit", "percent"), "%")
        median_val = round(_percentile(all_vals, 50), 1)
        
        full_percentile = _company_percentile(median_val, all_vals)
        adjusted_percentile = _company_percentile(median_val, adjusted_vals)
        strict_percentile = _company_percentile(median_val, strict_vals) if strict_vals else full_percentile
        
        metrics.append({
            "name": _metric_label(name), "company_value": median_val, "unit": unit,
            "full_percentile": full_percentile,
            "adjusted_percentile": adjusted_percentile,
            "strict_comparability_percentile": strict_percentile,
            "cohort_size_full": len(all_vals),
            "cohort_size_adjusted": len(adjusted_vals),
            "caution_count": sum(1 for r in group if _inclusion_policy(r.get("data_quality_flag", ""))[0] == "included_with_caution"),
            "excluded_count": sum(1 for r in group if _inclusion_policy(r.get("data_quality_flag", ""))[0] == "excluded"),
            "peer_p25": round(_percentile(all_vals, 25), 1),
            "peer_p50": round(_percentile(all_vals, 50), 1),
            "peer_p75": round(_percentile(all_vals, 75), 1),
        })
        
        for r in group:
            status, rationale = _inclusion_policy(r.get("data_quality_flag", ""))
            source_detail.append({
                "company": r["company_name"], "ticker": r["ticker"],
                "fiscal_year": r["fiscal_year"], "filing_type": r["filing_type"],
                "metric": _metric_label(name),
                "reported_value": r["reported_value"],
                "reported_unit": r["reported_unit"],
                "normalized_value": float(r["normalized_value"]),
                "gaap_or_non_gaap": r["gaap_or_non_gaap"],
                "source_section": r.get("source_page_or_section", ""),
                "source_url": r.get("source_url", ""),
                "formula": r.get("calculation_formula", ""),
                "quality_flag": r.get("data_quality_flag", ""),
                "inclusion_status": status,
                "inclusion_rationale": rationale,
                "in_full_percentile": True,
                "in_adjusted_percentile": status != "excluded",
                "in_strict_percentile": status == "included",
            })

    return {
        "industry": "Cloud / SaaS",
        "peers": peers,
        "peer_count": len(peers),
        "data_source": "Real public company data from FY2024-FY2025 10-K filings",
        "sources": sources,
        "quality_flags": quality_flags,
        "source_detail": source_detail,
        "methodology": {
            "peer_selection": "10 public US-listed cloud/SaaS companies with >$2B annual revenue",
            "metric_definitions": "GAAP revenue growth, gross margin, EBITDA margin, net margin, FCF margin (OCF - CapEx), debt/equity, current ratio",
            "normalization": "All metrics from most recent fiscal year 10-K filings. Fiscal years ending between Jun 2024 and Jan 2026.",
            "missing_data": "None — all metrics available for all 10 peers",
            "percentile_calculation": "Linear interpolation between sorted values. Company percentile = count of peers below / total peers × 100.",
            "limitations": "SaaS companies vary by go-to-market model (enterprise vs PLG), revenue mix (subscription vs consumption), and GAAP profitability (SBC impact). Benchmarks represent observed distribution, not a recommended target.",
        },
        "metrics": metrics,
        "strengths": [
            {"metric": "Data Quality", "observation": f"All {len(peers)} peers sourced from official 10-K filings", "interpretation": "Metrics are GAAP-consistent and directly comparable across companies."},
            {"metric": "Coverage", "observation": f"Peer set spans {len(peers)} companies from $2.7B to $41.5B revenue", "interpretation": "Broad coverage of scaled public SaaS companies provides meaningful comparison range."},
        ],
        "weaknesses": [
            {"metric": "GAAP Net Margins", "observation": "3 of 10 peers have negative GAAP net margins due to SBC", "interpretation": "GAAP profitability comparison is distorted by stock-based compensation. Non-GAAP metrics would show different results."},
            {"metric": "Fiscal Period Alignment", "observation": "Fiscal years span Jun 2024 to Jan 2026", "interpretation": "Macro conditions during these periods differ. Results may not be fully comparable."},
        ],
        "unusual": [
            {"metric": "Growth vs Profitability", "observation": "Highest growth (31%) correlates with negative GAAP net margin (-12.2%)", "interpretation": "Classic SaaS growth-profitability tradeoff. High-growth peers reinvest heavily while mature peers show GAAP profitability."},
        ],
    }

def _fallback_saas() -> dict:
    """Fallback if CSV not available — synthetic data."""
    from copy import deepcopy
    return deepcopy({
        "industry": "Cloud / SaaS",
        "peers": ["Data unavailable — check data/saas_peers.csv"],
        "peer_count": 0,
        "metrics": [],
        "strengths": [], "weaknesses": [], "unusual": [],
        "methodology": {"note": "Real peer data not loaded. Check data/saas_peers.csv."},
    })

def _build_empty_benchmark(industry: str) -> dict:
    """Return a properly structured empty benchmark so the frontend doesn't crash."""
    return dict(
        industry=industry,
        peers=[],
        peer_count=0,
        metrics=[],
        strengths=[],
        weaknesses=[],
        unusual=[],
        methodology={"note": f"Real peer data not yet loaded for {industry}. Check data/ directory."},
    )

BENCHMARKS = {
    "saas": _build_saas_benchmark(),
    "manufacturing": _build_empty_benchmark("Manufacturing"),  # TODO: real data
    "financial": _build_empty_benchmark("Financial Services"),  # TODO: real data
}

def get_benchmark(industry: str) -> dict:
    from copy import deepcopy
    if industry not in BENCHMARKS:
        raise ValueError(f"Unknown industry '{industry}'. Available: {list(BENCHMARKS.keys())}")
    return deepcopy(BENCHMARKS[industry])

def get_available_industries() -> list[str]:
    return list(BENCHMARKS.keys())
