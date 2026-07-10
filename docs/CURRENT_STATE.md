# ModelGuard AI — Current State

## Running
- Backend: FastAPI at localhost:8000 (9 engine modules)
- Frontend: Next.js 14 at localhost:3000 (11 pages, 0 build errors)

## Pages
/ /upload /demo /analyze /company /diff /confidence /benchmark

## API Endpoints
/api/demo, /api/upload, /api/analyze/{scenario}, /api/scenarios
/api/company-demo/{industry}, /api/company-industries
/api/demo-diff/{pair}, /api/diff-pairs
/api/confidence/{scenario}, /api/confidence-scenarios
/api/evidence/{mode}/{scenario}
/api/benchmark/{industry}, /api/benchmark-industries

## Backend Modules
main.py, audit_engine.py, financial_intelligence.py, company_intelligence.py,
company_diff.py, confidence_analyzer.py, evidence_explorer.py, peer_benchmark.py,
pdf_parser.py, models.py, parser.py, mock.py

## Git: 13 commits on main

## Known Issues
- screen_capture MCP: broken (StudioMCP binary bug)
- Vercel deploy: needs `vercel login`
- Backend deploy: needs Render/Railway account
