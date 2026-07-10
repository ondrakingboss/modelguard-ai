# API Contracts

## Audit (audit_engine.py)
GET /api/demo → { model_score, summary, issues[], severity_breakdown }
POST /api/upload (multipart .xlsx) → same

## Financial Intelligence (financial_intelligence.py)
GET /api/scenarios → { scenarios: [startup, manufacturing, saas, retail, leveraged] }
GET /api/analyze/{scenario} → { business_health_score, forecast_confidence, assumption_risk_score, cash_flow_risk, profitability_outlook, revenue_sustainability, balance_sheet_health, insights[], executive_summary }

## Company Intelligence (company_intelligence.py)
GET /api/company-industries → [tech, industrial, financial]
GET /api/company-demo/{industry} → { company_name, industry, filing_type, filing_period, business_profile{...}, insights[], executive_summary }
POST /api/analyze-company (multipart .pdf) → same

## Company Diff (company_diff.py)
GET /api/diff-pairs → { pairs: [tech_growth, industrial_restructuring, bank_nim] }
GET /api/demo-diff/{pair} → { company_a, company_b, changes[], summary_stats, executive_summary }
POST /api/company-diff (multipart: file_a, file_b .pdf) → same

## Confidence (confidence_analyzer.py)
GET /api/confidence-scenarios → { scenarios: [startup, manufacturing, saas] }
GET /api/confidence/{scenario} → { scenario, categories[{category, score, supporting_evidence[], missing_evidence[], assessment}] }

## Evidence (evidence_explorer.py)
GET /api/evidence/{mode}/{scenario} → enriched insights with evidence: { supporting[{source, location, data_point}], reasoning_chain[], assumptions[], missing[], confidence_breakdown }

## Peer Benchmark (peer_benchmark.py)
GET /api/benchmark-industries → { industries: [saas, manufacturing, financial] }
GET /api/benchmark/{industry} → { industry, peers[], peer_count, metrics[{name, company_value, percentile, peer_p25, peer_p50, peer_p75}], strengths[], weaknesses[], unusual[] }
