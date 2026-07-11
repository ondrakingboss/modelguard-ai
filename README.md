# ModelGuard AI

**Audit Your Financial Models with AI** — Like Grammarly for Excel.

ModelGuard catches formula errors, hidden risks, and suspicious patterns in financial models. Built for FP&A, investment banking, audit, and accounting professionals who need confidence in their spreadsheet outputs.

![ModelGuard AI Dashboard](assets/hero_bg.png)

---

## Why ModelGuard Matters

Financial models drive billion-dollar decisions. A single formula error, hidden assumption, or inconsistent cell can cascade into flawed valuations, misallocated capital, or regulatory exposure. Most model audits are manual, time-consuming, and error-prone.

**ModelGuard automates the audit** — scanning every cell, every sheet, every hidden element — and produces a structured, explainable report in seconds.

---

## Features

### 🔍 Formula Audit
- Detects `#REF!`, `#DIV/0!`, `#VALUE!` errors across all sheets
- Flags hardcoded constants inside formula cells
- Identifies inconsistent neighboring formula patterns

### 🛡️ Risk Detection
- Reveals hidden sheets, hidden rows, hidden columns
- Detects external workbook links that can break
- Identifies circular reference patterns

### 📊 Business Logic Checks
- Flags suspicious revenue growth (>100% period-over-period)
- Detects margin jumps (>20% period change)
- Warns on negative cash flow and empty assumption sections

### 🤖 AI Explanations
Every issue includes:
- Plain-English description of what's wrong
- Why it matters for financial modeling
- Suggested fix with context

### 📄 Export & Sharing
- Professional PDF audit reports
- CSV export for issue tracking
- Clean, recruiter-friendly dashboard

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, Framer Motion, Recharts |
| **Backend** | FastAPI, Python 3.11+, openpyxl, pandas |
| **Database** | SQLite (MVP), audit history tracking |
| **AI** | Mock AI layer (pluggable to OpenAI/OpenRouter) |
| **Design** | Dark fintech theme (inspired by Bloomberg Terminal, Linear, Mercury) |

---

## Architecture

```
┌─────────────────────────────────────────┐
│              Next.js Frontend            │
│  Landing → Upload → Audit Dashboard     │
│  (shadcn/ui + Framer Motion)            │
└──────────────┬──────────────────────────┘
               │ /api/upload, /api/demo
┌──────────────▼──────────────────────────┐
│              FastAPI Backend             │
│  Parser (openpyxl) → Audit Engine → DB  │
│  12 detection rules                     │
└─────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Clone
git clone <repo-url> && cd modelguard-ai

# Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` — click **Try Demo** for an instant audit preview.

---

## Demo Flow

1. **Landing Page** — Dark hero with CTA and feature cards
2. **Upload** — Drag-and-drop your .xlsx file
3. **Processing** — Animated audit steps (Reading → Scanning → Detecting → Generating)
4. **Dashboard** — Health score, severity breakdown, issues table, AI summary
5. **Export** — PDF report or CSV issue list

---

## Audit Output Format

```json
{
  "model_score": 48,
  "summary": "Detected 7 issues. Model is high risk...",
  "issues": [
    {
      "severity": "critical",
      "sheet": "Forecast",
      "cell": "H42",
      "category": "Formula Error",
      "description": "#REF! in revenue forecast",
      "why_it_matters": "Broken formulas cascade into valuation outputs",
      "suggested_fix": "Trace precedent cells and restore reference"
    }
  ],
  "severity_breakdown": { "critical": 1, "high": 3, "medium": 3, "low": 0 }
}
```

---

## CV Bullet Points

- **Built ModelGuard AI**, a full-stack financial model auditing platform that detects 12 categories of Excel errors including formula integrity, hidden risks, and business logic anomalies using Python (FastAPI, openpyxl, pandas) and TypeScript (Next.js, Tailwind CSS).

- **Designed a dark fintech dashboard** inspired by Bloomberg Terminal and Linear, featuring animated health scores, severity breakdowns, interactive issue tables with detail modals, and professional PDF/CSV export — deployed as a portfolio-ready demo with mock data.

- **Engineered a 12-rule audit engine** that scans Excel workbooks for `#REF!/#DIV/0!` errors, hidden sheets/rows/columns, circular references, external links, suspicious revenue growth (>100%), margin jumps, and negative cash flow patterns — producing structured JSON output with plain-English explanations.

- **Integrated AI-style explanations** where each detected issue includes context-aware descriptions of why it matters for financial modeling professionals and actionable suggested fixes — designed to plug into OpenAI/OpenRouter for production use.

---

## Future Roadmap

- [ ] OpenAI/OpenRouter integration for real AI explanations
- [ ] User accounts and audit history
- [ ] Multi-file model comparison
- [ ] Excel formula dependency graphing
- [ ] Custom audit rule builder
- [ ] Slack/Teams notification integration

---

## Built With

- **Codex CLI** — Implementation and code review
- **OpenArt** — Visual assets (hero, logo, illustrations)
- **Hermes Agent** — Project orchestration and task delegation

---

## Deployment

### Frontend (Vercel)
```bash
cd frontend
vercel login        # Interactive browser OAuth required
vercel --prod       # Deploys with vercel.json config
```
Set environment variable: `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com`

### Backend (Render / Railway)
```bash
cd backend
# Render: connect GitHub repo → set build command: pip install -r requirements.txt
# Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
```
CORS configured in main.py — update `allow_origins` with production frontend URL.

### Local Development
```bash
# Backend
cd backend && source venv/bin/activate && uvicorn main:app --port 8000
# Frontend (new terminal)
cd frontend && npm run dev
```

## QA Verification (2026-07-09)

| Check | Result |
|---|---|
| 9 API endpoints | All 200 OK |
| Frontend build | 11/11 pages, zero errors |
| accessibility | `rel="noopener noreferrer"` on external links |
| Security audit | No API keys exposed, GAAP-only data, source URLs verified |

### Known Limitations
- Screen capture MCP tool broken — screenshots require manual browser capture
- Backend deploy requires Render/Railway account (browser setup)
- Vercel deploy requires `vercel login` (browser OAuth)
- Real peer data only for SaaS industry (10 companies)
- No authentication — demo-only deployment
- sound MCP broken — no audio feedback on flex

---

*Built as a fintech portfolio project demonstrating full-stack engineering, financial domain knowledge, and UI/UX design.*

## Live Demo

- **Frontend:** https://modelguard-ai.vercel.app
- **Backend API:** https://modelguard-ai.onrender.com
- **Demo Dashboard:** https://modelguard-ai.vercel.app/demo
- **Benchmark:** https://modelguard-ai.vercel.app/benchmark
