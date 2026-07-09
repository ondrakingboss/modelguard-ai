"use client";

import { Card } from "@/components/ui/card";
import { motion } from "framer-motion";
import { ArrowUp, ArrowDown, Minus, Plus, FileText, TrendingUp, Landmark, Activity, PiggyBank, Target, AlertTriangle, BookOpen, MessageSquare } from "lucide-react";

interface Change {
  category: string;
  importance: "critical" | "high" | "medium" | "low";
  confidence: number;
  title: string;
  value_a: string;
  value_b: string;
  change_pct: string;
  change_direction: "up" | "down" | "flat" | "new" | "removed";
  document_ref_a: string;
  document_ref_b: string;
  analyst_note: string;
  financial_implication: string;
  recommended_action: string;
}

interface CompanyDiff {
  company_a: { name: string; period: string };
  company_b: { name: string; period: string };
  executive_summary: string;
  changes: Change[];
  summary_stats: { total_changes: number; critical_changes: number; positive_changes: number; negative_changes: number; neutral_changes: number };
}

function importanceColor(v: string) {
  const m: Record<string, string> = { critical: "#ef4444", high: "#f97316", medium: "#f59e0b", low: "#22c55e" };
  return m[v] || "#a1a1aa";
}

function directionIcon(d: string) {
  switch (d) {
    case "up": return <ArrowUp className="w-3 h-3 text-[#22c55e]" />;
    case "down": return <ArrowDown className="w-3 h-3 text-[#ef4444]" />;
    case "new": return <Plus className="w-3 h-3 text-[#3b82f6]" />;
    case "removed": return <Minus className="w-3 h-3 text-[#71717a]" />;
    default: return <Minus className="w-3 h-3 text-[#71717a]" />;
  }
}

function categoryIcon(c: string) {
  const icons: Record<string, React.ReactNode> = {
    Revenue: <TrendingUp className="w-4 h-4" />,
    Margin: <Activity className="w-4 h-4" />,
    Debt: <Landmark className="w-4 h-4" />,
    "Cash Flow": <PiggyBank className="w-4 h-4" />,
    "Capital Allocation": <Target className="w-4 h-4" />,
    Guidance: <FileText className="w-4 h-4" />,
    "Business Risks": <AlertTriangle className="w-4 h-4" />,
    "Accounting Policy": <BookOpen className="w-4 h-4" />,
    "Management Commentary": <MessageSquare className="w-4 h-4" />,
  };
  return icons[c] || <FileText className="w-4 h-4" />;
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="glass p-4 text-center">
      <span className="text-2xl font-bold" style={{ color }}>{value}</span>
      <p className="text-xs text-[#71717a] mt-1">{label}</p>
    </div>
  );
}

export default function CompanyDiffView({ data }: { data: CompanyDiff }) {
  if (!data) return null;
  const s = data.summary_stats;

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      {/* Header */}
      <div className="glass p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold">{data.company_a.name}</h2>
            <span className="text-[#71717a] text-lg">vs</span>
            <h2 className="text-xl font-bold">{data.company_b.name}</h2>
          </div>
        </div>
        <div className="flex gap-6 text-sm text-[#a1a1aa]">
          <span>Period A: {data.company_a.period}</span>
          <span>Period B: {data.company_b.period}</span>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard label="Total Changes" value={s.total_changes} color="#3b82f6" />
        <StatCard label="Critical" value={s.critical_changes} color="#ef4444" />
        <StatCard label="Positive" value={s.positive_changes} color="#22c55e" />
        <StatCard label="Negative" value={s.negative_changes} color="#ef4444" />
        <StatCard label="Neutral" value={s.neutral_changes} color="#a1a1aa" />
      </div>

      {/* Executive Summary */}
      <Card className="glass p-6 border-l-4 border-[#22c55e]">
        <p className="text-sm leading-relaxed">{data.executive_summary}</p>
      </Card>

      {/* Side-by-Side Changes */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wider">Detailed Comparison</h3>
        {data.changes.map((change, i) => (
          <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08 }}
            className="glass hover:border-[#22c55e]/20 transition-colors overflow-hidden">
            {/* Header Row */}
            <div className="p-4 border-b border-[#27272a]">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {categoryIcon(change.category)}
                  <span className="text-xs text-[#71717a] uppercase tracking-wider">{change.category}</span>
                  <span className="text-xs font-bold uppercase" style={{ color: importanceColor(change.importance) }}>{change.importance}</span>
                  <span className="text-xs text-[#71717a] ml-auto">{change.confidence}%</span>
                </div>
              </div>
              <h4 className="font-semibold">{change.title}</h4>
            </div>

            {/* Side-by-Side Values */}
            <div className="grid grid-cols-3 border-b border-[#27272a]">
              <div className="p-4 border-r border-[#27272a] bg-[#09090b]/30">
                <p className="text-xs text-[#71717a] mb-1">Period A</p>
                <p className="text-lg font-bold">{change.value_a}</p>
                <p className="text-xs text-[#71717a] italic mt-1">{change.document_ref_a}</p>
              </div>
              <div className="p-4 flex flex-col items-center justify-center bg-[#09090b]/10">
                <div className="flex items-center gap-1 text-lg font-bold"
                  style={{ color: change.change_direction === "up" ? "#22c55e" : change.change_direction === "down" ? "#ef4444" : "#a1a1aa" }}>
                  {directionIcon(change.change_direction)}
                  {change.change_pct}
                </div>
              </div>
              <div className="p-4 border-l border-[#27272a] bg-[#09090b]/30">
                <p className="text-xs text-[#71717a] mb-1">Period B</p>
                <p className="text-lg font-bold">{change.value_b}</p>
                <p className="text-xs text-[#71717a] italic mt-1">{change.document_ref_b}</p>
              </div>
            </div>

            {/* Analyst Note */}
            <div className="p-4 space-y-3">
              <div className="glass p-3">
                <p className="text-xs text-[#22c55e] uppercase tracking-wider mb-1">Analyst Note</p>
                <p className="text-sm">{change.analyst_note}</p>
              </div>
              <div className="glass p-3">
                <p className="text-xs text-[#f59e0b] uppercase tracking-wider mb-1">Financial Implication</p>
                <p className="text-sm">{change.financial_implication}</p>
              </div>
              <div className="glass p-3 border border-[#22c55e]/20">
                <p className="text-xs text-[#22c55e] uppercase tracking-wider mb-1">Action</p>
                <p className="text-sm">{change.recommended_action}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
