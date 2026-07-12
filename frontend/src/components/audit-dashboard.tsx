"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, AlertTriangle, CheckCircle2, ChevronDown, ChevronUp, Flame, Info, Shield } from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export interface Issue {
  id: string;
  severity: "critical" | "high" | "medium" | "low";
  sheet: string;
  cell: string;
  category: string;
  title: string;
  description: string;
  why_it_matters: string;
  suggested_fix: string;
  output_impact?: string;
}

export interface ScoreExplanation {
  score: number;
  score_band: string;
  main_drivers: string[];
  penalty_breakdown: Record<string, number>;
  caps_applied: string[];
  floor_rules_applied: string[];
  what_is_known: string;
  what_is_unknown: string;
  why_not_lower: string;
  why_not_higher: string;
}

export interface AuditResult {
  model_score: number;
  summary: string;
  issues: Issue[];
  severity_breakdown: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  score_explanation?: ScoreExplanation | null;
}

function scoreColor(score: number) {
  if (score >= 80) return "#22c55e";
  if (score >= 60) return "#f59e0b";
  if (score >= 40) return "#f97316";
  return "#ef4444";
}

export default function AuditScore({ result }: { result: AuditResult }) {
  const [displayScore, setDisplayScore] = useState(0);
  const [showExplanation, setShowExplanation] = useState(false);
  const color = scoreColor(result.model_score);
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (displayScore / 100) * circumference;
  const explanation = result.score_explanation;

  useEffect(() => {
    const duration = 950;
    const start = performance.now();
    let frame = 0;

    function tick(now: number) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayScore(Math.round(result.model_score * eased));
      if (progress < 1) frame = requestAnimationFrame(tick);
    }

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [result.model_score]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center gap-3 py-8"
    >
      <div className="relative w-48 h-48">
        <svg className="score-ring w-full h-full -rotate-90" viewBox="0 0 180 180">
          <circle cx="90" cy="90" r={radius} fill="none" stroke="rgba(39,39,42,0.5)" strokeWidth="8" />
          <circle cx="90" cy="90" r={radius} fill="none" stroke={color} strokeWidth="8"
            strokeDasharray={circumference} strokeDashoffset={offset}
            strokeLinecap="round" style={{ transition: "stroke-dashoffset 1s ease" }} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold tabular-nums" style={{ color }}>{displayScore}</span>
          <span className="text-sm text-[#a1a1aa]">/ 100</span>
        </div>
      </div>

      {/* Score band badge */}
      {explanation && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          className="px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider"
          style={{
            background: `${color}18`,
            color,
            border: `1px solid ${color}40`,
          }}
        >
          {explanation.score_band}
        </motion.div>
      )}

      <p className="text-[#a1a1aa] text-sm max-w-md text-center">{result.summary}</p>

      {/* Expandable "Why This Score?" */}
      {explanation && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="w-full max-w-xl"
        >
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="w-full glass p-4 text-left flex items-center justify-between gap-3 hover:border-[#3f3f46] transition-colors"
          >
            <div className="flex items-center gap-2">
              <Info className="w-4 h-4 text-[#a1a1aa]" />
              <span className="text-sm font-medium">Why This Score?</span>
            </div>
            {showExplanation ? (
              <ChevronUp className="w-4 h-4 text-[#71717a]" />
            ) : (
              <ChevronDown className="w-4 h-4 text-[#71717a]" />
            )}
          </button>

          <AnimatePresence>
            {showExplanation && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden"
              >
                <div className="glass border-t-0 rounded-t-none p-5 space-y-5">
                  {/* What is known */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Shield className="w-3.5 h-3.5 text-green-400" />
                      <h4 className="text-xs font-semibold text-green-400 uppercase tracking-wider">What Is Known</h4>
                    </div>
                    <p className="text-xs text-[#a1a1aa] leading-relaxed">{explanation.what_is_known}</p>
                  </div>

                  {/* What is unknown */}
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Info className="w-3.5 h-3.5 text-yellow-400" />
                      <h4 className="text-xs font-semibold text-yellow-400 uppercase tracking-wider">What Is Unknown</h4>
                    </div>
                    <p className="text-xs text-[#a1a1aa] leading-relaxed">{explanation.what_is_unknown}</p>
                  </div>

                  {/* Key drivers */}
                  {explanation.main_drivers.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-[#fafafa] mb-2">Key Score Drivers</h4>
                      <ul className="space-y-1.5">
                        {explanation.main_drivers.map((d, i) => (
                          <li key={i} className="flex items-start gap-2 text-xs text-[#a1a1aa]">
                            <span className="text-[#71717a] mt-0.5">▸</span>
                            {d}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Caps and floors */}
                  {(explanation.caps_applied.length > 0 || explanation.floor_rules_applied.length > 0) && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {explanation.caps_applied.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-[#fafafa] mb-2">Caps Applied</h4>
                          <ul className="space-y-1">
                            {explanation.caps_applied.map((c, i) => (
                              <li key={i} className="text-xs text-[#a1a1aa]">{c}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {explanation.floor_rules_applied.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-[#fafafa] mb-2">Floor Rules</h4>
                          <ul className="space-y-1">
                            {explanation.floor_rules_applied.map((f, i) => (
                              <li key={i} className="text-xs text-[#a1a1aa]">{f}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* What would improve / make worse */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-[#27272a]">
                    <div>
                      <h4 className="text-xs font-semibold text-green-400 mb-1.5">What Would Improve</h4>
                      <p className="text-xs text-[#a1a1aa] leading-relaxed">
                        Resolve critical formula errors, break circular references, unhide content feeding calculations,
                        and restore consistent formula patterns. Each resolved finding directly raises the score.
                      </p>
                    </div>
                    <div>
                      <h4 className="text-xs font-semibold text-red-400 mb-1.5">What Would Make It Worse</h4>
                      <p className="text-xs text-[#a1a1aa] leading-relaxed">
                        If hidden content is found to materially feed key outputs, or if circular references
                        are proven to affect revenue/EBITDA/valuation, the score floor drops to 25.
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </motion.div>
  );
}

function SeverityCard({ label, count, color, icon }: { label: string; count: number; color: string; icon: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="glass p-4 flex items-center gap-3 border" style={{ borderColor: `${color}55` }}>
        <span className="text-xl rounded-lg px-2 py-1" style={{ background: `${color}22`, color }}>{icon}</span>
        <div>
          <p className="text-xs text-[#a1a1aa] uppercase tracking-wider">{label}</p>
          <p className="text-2xl font-bold" style={{ color }}>{count}</p>
        </div>
      </Card>
    </motion.div>
  );
}

export function SeverityGrid({ breakdown }: { breakdown: AuditResult["severity_breakdown"] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <SeverityCard label="Critical" count={breakdown.critical} color="#ef4444" icon="🔴" />
      <SeverityCard label="High" count={breakdown.high} color="#f97316" icon="🟠" />
      <SeverityCard label="Medium" count={breakdown.medium} color="#f59e0b" icon="🟡" />
      <SeverityCard label="Low" count={breakdown.low} color="#22c55e" icon="🟢" />
    </div>
  );
}

function severityBadge(s: Issue["severity"]) {
  const map: Record<Issue["severity"], { className: string; icon: ReactNode }> = {
    critical: { className: "badge-critical", icon: <Flame className="h-3.5 w-3.5" /> },
    high: { className: "badge-high", icon: <AlertTriangle className="h-3.5 w-3.5" /> },
    medium: { className: "badge-medium", icon: <AlertCircle className="h-3.5 w-3.5" /> },
    low: { className: "badge-low", icon: <CheckCircle2 className="h-3.5 w-3.5" /> },
  };
  const config = map[s] || map.low;
  return <Badge className={cn(config.className, "capitalize gap-1.5 px-2.5 py-1 text-xs font-bold shadow-lg")}>{config.icon}{s}</Badge>;
}

export function IssueRow({ issue, onClick }: { issue: Issue; onClick: () => void }) {
  return (
    <tr className="border-b border-[#27272a] hover:bg-[#18181b] cursor-pointer transition-colors" onClick={onClick}>
      <td className="p-3">{severityBadge(issue.severity)}</td>
      <td className="p-3 text-sm text-[#a1a1aa]">{issue.category}</td>
      <td className="p-3 text-sm">{issue.sheet}</td>
      <td className="p-3 text-sm font-mono text-[#22c55e]">{issue.cell}</td>
      <td className="p-3 text-sm max-w-md truncate">{issue.title}</td>
    </tr>
  );
}

function unique(values: string[]) {
  return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b));
}

export function SheetRiskMap({ issues }: { issues: Issue[] }) {
  const data = useMemo(() => {
    const counts = new Map<string, number>();
    issues.forEach((issue) => counts.set(issue.sheet || "Unknown", (counts.get(issue.sheet || "Unknown") || 0) + 1));
    return Array.from(counts, ([sheet, count]) => ({ sheet, count })).sort((a, b) => b.count - a.count);
  }, [issues]);

  if (!data.length) return null;

  return (
    <Card className="glass p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-[#fafafa]">Sheet-Level Risk Map</h3>
          <p className="text-xs text-[#a1a1aa]">Issues grouped by workbook sheet.</p>
        </div>
        <span className="text-xs text-[#71717a]">{data.length} sheets</span>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 20, bottom: 4, left: 12 }}>
            <CartesianGrid stroke="rgba(63,63,70,0.45)" horizontal={false} />
            <XAxis type="number" allowDecimals={false} stroke="#71717a" tick={{ fill: "#a1a1aa", fontSize: 12 }} />
            <YAxis dataKey="sheet" type="category" width={120} stroke="#71717a" tick={{ fill: "#a1a1aa", fontSize: 12 }} />
            <Tooltip
              cursor={{ fill: "rgba(34,197,94,0.08)" }}
              contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 10, color: "#fafafa" }}
            />
            <Bar dataKey="count" fill="#22c55e" radius={[0, 8, 8, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

export function IssueTable({ issues, onSelect }: { issues: Issue[]; onSelect: (i: Issue) => void }) {
  const [severity, setSeverity] = useState("all");
  const [category, setCategory] = useState("all");
  const [sheet, setSheet] = useState("all");

  const categories = useMemo(() => unique(issues.map((issue) => issue.category).filter(Boolean)), [issues]);
  const sheets = useMemo(() => unique(issues.map((issue) => issue.sheet).filter(Boolean)), [issues]);
  const filteredIssues = useMemo(() => {
    return issues.filter((issue) => {
      return (
        (severity === "all" || issue.severity === severity) &&
        (category === "all" || issue.category === category) &&
        (sheet === "all" || issue.sheet === sheet)
      );
    });
  }, [category, issues, severity, sheet]);

  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
      <SheetRiskMap issues={filteredIssues} />
      <Card className="glass overflow-hidden">
        <div className="flex flex-col gap-3 border-b border-[#27272a] p-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h3 className="text-sm font-semibold">Issue Register</h3>
            <p className="text-xs text-[#a1a1aa]">{filteredIssues.length} of {issues.length} issues shown</p>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            <select value={severity} onChange={(e) => setSeverity(e.target.value)} className="rounded-lg border border-[#27272a] bg-[#09090b] px-3 py-2 text-sm text-[#fafafa]">
              <option value="all">All severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select value={category} onChange={(e) => setCategory(e.target.value)} className="rounded-lg border border-[#27272a] bg-[#09090b] px-3 py-2 text-sm text-[#fafafa]">
              <option value="all">All categories</option>
              {categories.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <select value={sheet} onChange={(e) => setSheet(e.target.value)} className="rounded-lg border border-[#27272a] bg-[#09090b] px-3 py-2 text-sm text-[#fafafa]">
              <option value="all">All sheets</option>
              {sheets.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#27272a] text-left">
                <th className="p-3 text-xs text-[#71717a] uppercase tracking-wider">Severity</th>
                <th className="p-3 text-xs text-[#71717a] uppercase tracking-wider">Category</th>
                <th className="p-3 text-xs text-[#71717a] uppercase tracking-wider">Sheet</th>
                <th className="p-3 text-xs text-[#71717a] uppercase tracking-wider">Cell</th>
                <th className="p-3 text-xs text-[#71717a] uppercase tracking-wider">Issue</th>
              </tr>
            </thead>
            <tbody>
              {filteredIssues.map((issue) => (
                <IssueRow key={issue.id} issue={issue} onClick={() => onSelect(issue)} />
              ))}
              {!filteredIssues.length && (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-sm text-[#a1a1aa]">No issues match the selected filters.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </motion.div>
  );
}

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export function IssueModal({ issue, open, onClose }: { issue: Issue | null; open: boolean; onClose: () => void }) {
  if (!issue) return null;
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="glass !bg-[#18181b] border-[#27272a] text-[#fafafa] max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-2">
            {severityBadge(issue.severity)}
            <span className="text-xs text-[#71717a]">{issue.category}</span>
          </div>
          <DialogTitle className="text-lg">{issue.title}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 mt-4">
          <div className="flex gap-4 text-sm">
            <span className="text-[#71717a]">Sheet:</span>
            <span>{issue.sheet}</span>
            <span className="text-[#71717a]">Cell:</span>
            <span className="font-mono text-[#22c55e]">{issue.cell}</span>
          </div>
          <div>
            <p className="text-sm text-[#a1a1aa]">{issue.description}</p>
          </div>
          <div className="glass p-4">
            <p className="text-xs text-[#71717a] uppercase tracking-wider mb-1">Why It Matters</p>
            <p className="text-sm">{issue.why_it_matters}</p>
          </div>
          <div className="glass p-4 border border-[#22c55e]/20">
            <p className="text-xs text-[#22c55e] uppercase tracking-wider mb-1">Suggested Fix</p>
            <p className="text-sm">{issue.suggested_fix}</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function SummaryCard({ summary }: { summary: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="glass p-6">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">🤖</span>
          <h3 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wider">AI Executive Summary</h3>
        </div>
        <p className="text-sm leading-relaxed">{summary}</p>
      </Card>
    </motion.div>
  );
}

export { AuditScore };