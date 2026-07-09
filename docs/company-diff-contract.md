# Company Diff API Contract

## Endpoints

### GET /api/diff-pairs
Returns available demo comparison pairs.

**Response:**
```json
{
  "pairs": ["tech_growth", "industrial_restructuring", "bank_nim"]
}
```

### GET /api/demo-diff/{pair}
Returns a full comparison for a demo pair.

**Path params:** `pair` ∈ {tech_growth, industrial_restructuring, bank_nim}

**Response (200):**
```json
{
  "company_a": { "name": "string", "period": "string" },
  "company_b": { "name": "string", "period": "string" },
  "executive_summary": "string (3-4 sentences)",
  "changes": [
    {
      "category": "Revenue|Margin|Debt|Cash Flow|Capital Allocation|Guidance|Business Risks|Accounting Policy|Management Commentary",
      "importance": "critical|high|medium|low",
      "confidence": 0-100,
      "title": "string",
      "value_a": "string",
      "value_b": "string",
      "change_pct": "string (e.g. +28%)",
      "change_direction": "up|down|flat|new|removed",
      "document_ref_a": "string",
      "document_ref_b": "string",
      "analyst_note": "string",
      "financial_implication": "string",
      "recommended_action": "string"
    }
  ],
  "summary_stats": {
    "total_changes": "int",
    "critical_changes": "int",
    "positive_changes": "int",
    "negative_changes": "int",
    "neutral_changes": "int"
  }
}
```

**Error (404):** `{ "detail": "Unknown pair 'xyz'. Available pairs: ..." }`

### POST /api/company-diff
Upload two PDFs for comparison.

**Request:** multipart/form-data with `file_a` and `file_b` (.pdf)

**Response (200):** Same shape as demo-diff above

**Error (400):** `{ "detail": "Only .pdf files are supported." }`
**Error (500):** `{ "detail": "Failed to compare company PDFs: ..." }`

## Frontend Requirements

1. Page at `/diff` with 3 demo pair selector buttons
2. Component `CompanyDiffView` receives the response JSON
3. Displays: company names + periods header, summary stats grid (5 cards), executive summary card, list of change cards in side-by-side layout
4. Each change card shows: category icon + label, importance badge, title, 3-column layout (value_a | Δ% | value_b), document references, analyst note, financial implication, recommended action
5. Loading state (spinner + text)
6. Error state (red alert card)
7. Dark fintech theme consistent with existing dashboard
