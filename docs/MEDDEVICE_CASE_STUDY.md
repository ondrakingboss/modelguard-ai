# MedDevice 5Y Model — Audit Case Study

## Overview

**Test file:** `MedDevice_5Y_Model_TEST.xlsx`  
**Purpose:** A deliberately flawed 5-year financial model with 13 planted faults, designed to stress-test the audit engine's false-positive rate, severity calibration, and noise reduction.

The model represents a medical device distributor with a P&L and Assumptions sheet, containing hidden rows, hidden columns, hidden worksheets, circular references, hardcoded constants, formula errors, and business logic anomalies.

---

## Before: Original Engine (v1.0)

| Metric | Value |
|--------|-------|
| Total findings | **56** |
| Critical | 0 |
| High | 2 |
| Medium | 54 |
| Low | 0 |
| Health score | **0/100** |
| Score band | Critical Risk |

### Problems

- **54 medium findings** — mostly hardcoded constant false positives on trivial literals (`1`, `0`, `100`, `/100`, `*100`)
- **Score collapsed to 0** — 54 medium × 5 penalty = -270, leaving no differentiation
- **Circular references** misclassified as "hardcoded constants" instead of "Circular Reference"
- **No row-level dedup** — every cell in a row pattern produced a separate finding
- **#REF! error** (`=I6+#REF!`) in H8 completely missed — only exact string matches detected
- **No output-impact awareness** — structural issues and material issues penalized equally

---

## After: Improved Engine (v3.0)

| Metric | Value |
|--------|-------|
| Total findings | **26** (-54%) |
| Critical | 1 |
| High | 5 |
| Medium | 20 |
| Low | 0 |
| Health score | **16/100** |
| Score band | Severe Risk |

### What Improved

| Fix | Impact |
|-----|--------|
| **Trivial constant filter** (0, 1, -1, 100) | Eliminated ~30 false positives from modeling patterns |
| **Row-level collapse** | 4 row groups collapsed (23 cells → 4 findings) |
| **Hardcoded+inconsistent consolidation** | Same-cell pairs merged into one finding |
| **Circular Reference category** | B8↔B9 correctly classified as circular (was "hardcoded") |
| **Embedded error detection** | H8 `=I6+#REF!` caught as critical formula error |
| **Business logic thresholds** | Revenue growth >50% or < -30% (was >100%) |
| **Hidden content reclassification** | Now risk-aware: formulas → high, empty → low |
| **Materiality-aware scoring** | Output impact classification with 0.5× multiplier for unknown impact |
| **Score explanation** | What is known / what is unknown / caps applied / what would improve |

### Planted Faults Detected: ~11/13

| # | Fault | Detected As | Severity |
|---|-------|-------------|----------|
| 1 | D6: `=C6*1.35` (hardcoded) | Hardcoded + inconsistent | Medium |
| 2 | E6: `792000` (hardcoded value) | Revenue growth anomaly | **High** |
| 3 | F7: `=-F6*0.19` (hardcoded) | Hardcoded + inconsistent | Medium |
| 4 | G7: `=-G6*0.19` (hardcoded) | Hardcoded + inconsistent | Medium |
| 5 | H8: `=I6+#REF!` (formula error) | Formula error | **Critical** |
| 6-7 | B8↔B9 (circular) | Circular reference pair | **High** ×2 |
| 8 | B16: `=8000+B15` (hardcoded) | Hardcoded constant | Medium |
| 9-10 | Rows 21-22 hidden | Hidden content | Low |
| 11 | Column G hidden | Hidden content | **High** |

---

## Score Explanation (Real Output)

> **16/100 — Severe Risk.** The audit engine detected 26 issues: 1 critical, 5 high, 20 medium. Output impact unknown for 9 findings — penalties reduced by 50% until impact is proven. The engine has not proven that every structural issue materially affects final valuation, cash-flow, or key financial statement outputs.

**Why not higher:** The critical formula error and circular references create structural reliability concerns.

**Why not lower:** Medium findings were capped. Hidden rows and formula integrity patterns carry low individual impact until downstream tracing is implemented.

---

## Why Trust & Explainability Matter

The journey from 56 → 26 findings and 0 → 16 score demonstrates the audit engine's evolution from a **panic alarm** to a **professional reviewer**:

1. **v1.0**: "56 problems. Score 0. Your model is broken." — uninformative, destroys trust.
2. **v3.0**: "26 findings. Score 16 — Severe Risk. Here's what we know, what we don't know, and what would improve the score." — actionable, honest, trustworthy.

The explainability layer (what_is_known / what_is_unknown / score band / caps / why_not profiles) transforms ModelGuard from a checkbox scanner into a tool finance professionals can use to prioritize remediation efforts.

---

## Remaining Limitations

- **~2 planted faults still missed** — likely subtler semantic errors requiring value-based analysis
- **Output impact tracing** is heuristic, not graph-based — cannot definitively prove a formula error affects valuation
- **Cross-sheet circular reference detection** limited to pairwise (A→B, B→A) — longer chains not detected
- **Score floor rules** can cap scores even when the raw penalty is milder

---

*Case study prepared July 2026. Backend v3.0, commit series `fix: hardcoded constant` through `fix: materiality-aware scoring`.*