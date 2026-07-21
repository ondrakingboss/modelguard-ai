"use client";

import { Card } from "@/components/ui/card";
import { motion } from "framer-motion";
import {
  TrendingUp, DollarSign, BarChart3, AlertTriangle,
  ShieldCheck, PieChart, Activity, Target
} from "lucide-react";
import EvidencePanel from "@/components/evidence-panel";
import type { ComponentProps } from "react";

type EvidenceTrail = ComponentProps<typeof EvidencePanel>["evidence"];

interface Insight {
  category: string;
  confidence: number;
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  finding: string;
  financial_reasoning: string;
  validation_questions: string[];
  recommended_actions: string[];
  benchmark_context: string;
  evidence?: EvidenceTrail;
}

interface FinancialIntelligence {
  business_health_score: number;
  forecast_confidence: number;
  assumption_risk_score: number;
  cash_flow_risk: number;
  profitability_outlook: string;
  revenue_sustainability: string;
  balance_sheet_health: string;
  insights: Insight[];
  executive_summary: string;
}

function ScoreBadge({ label, score, icon }: { label: string; score: number; icon: React.ReactNode }) {
  const color = score >= 70 ? "#22c55e" : score >= 50 ? "#f59e0b" : score >= 30 ? "#f97316" : "#ef4444";
  return (
    <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
      className="glass p-4 flex flex-col items-center gap-2">
      <div className="text-[#a1a1aa]">{icon}</div>
      <span className="text-2xl font-bold" style={{ color }}>{score}</span>
      <span className="text-xs text-[#71717a] uppercase tracking-wider">{label}</span>
    </motion.div>
  );
}

function OutlookBadge({ label, value }: { label: string; value: string }) {
  const color = value === "Strong" ? "#22c55e" : value === "Moderate" ? "#f59e0b" : value === "Weak" ? "#f97316" : "#ef4444";
  return (
    <div className="glass p-3 flex items-center justify-between">
      <span className="text-xs text-[#71717a] uppercase tracking-wider">{label}</span>
      <span className="text-sm font-semibold" style={{ color }}>{value}</span>
    </div>
  );
}

function severityColor(s: string) {
  const m: Record<string, string> = { critical: "text-[#ef4444]", high: "text-[#f97316]", medium: "text-[#f59e0b]", low: "text-[#22c55e]" };
  return m[s] || "text-[#a1a1aa]";
}

function categoryIcon(c: string) {
  if (c.includes("Revenue")) return <TrendingUp className="w-4 h-4" />;
  if (c.includes("Margin")) return <BarChart3 className="w-4 h-4" />;
  if (c.includes("Cost")) return <DollarSign className="w-4 h-4" />;
  if (c.includes("Cash")) return <Activity className="w-4 h-4" />;
  if (c.includes("Balance")) return <PieChart className="w-4 h-4" />;
  return <Target className="w-4 h-4" />;
}

export default function FinancialIntelligence({ data }: { data: FinancialIntelligence }) {
  if (!data) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center gap-3">
        <div className="h-8 w-1 rounded-full bg-[#22c55e]" />
        <div>
          <h2 className="text-xl font-bold">Financial Intelligence</h2>
          <p className="text-sm text-[#a1a1aa]">AI analyst review of business assumptions and financial logic</p>
        </div>
      </div>

      {/* Score Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <ScoreBadge label="Business Health" score={data.business_health_score} icon={<ShieldCheck className="w-5 h-5" />} />
        <ScoreBadge label="Forecast Confidence" score={data.forecast_confidence} icon={<Target className="w-5 h-5" />} />
        <ScoreBadge label="Assumption Risk" score={100 - data.assumption_risk_score} icon={<AlertTriangle className="w-5 h-5" />} />
        <ScoreBadge label="Cash Flow Risk" score={100 - data.cash_flow_risk} icon={<Activity className="w-5 h-5" />} />
      </div>

      {/* Outlook Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <OutlookBadge label="Profitability" value={data.profitability_outlook} />
        <OutlookBadge label="Revenue Sustainability" value={data.revenue_sustainability} />
        <OutlookBadge label="Balance Sheet" value={data.balance_sheet_health} />
      </div>

      {/* Executive Summary */}
      <Card className="glass p-6 border-l-4 border-[#22c55e]">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-lg">📊</span>
          <h3 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wider">Analyst Briefing</h3>
        </div>
        <p className="text-sm leading-relaxed">{data.executive_summary}</p>
      </Card>

      {/* Insights */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wider">Key Findings</h3>
        {data.insights.map((insight, i) => (
          <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass p-5 hover:border-[#22c55e]/20 transition-colors">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                {categoryIcon(insight.category)}
                <span className="text-xs text-[#71717a] uppercase tracking-wider">{insight.category}</span>
                <span className={`text-xs font-bold uppercase ${severityColor(insight.severity)}`}>{insight.severity}</span>
              </div>
              <span className="text-xs text-[#71717a]">{insight.confidence}% confidence</span>
            </div>

            <h4 className="font-semibold mb-2">{insight.title}</h4>
            <p className="text-sm text-[#a1a1aa] mb-3">{insight.finding}</p>

            <div className="glass p-3 mb-3">
              <p className="text-xs text-[#71717a] uppercase tracking-wider mb-1">Financial Reasoning</p>
              <p className="text-sm">{insight.financial_reasoning}</p>
            </div>

            <div className="mb-3">
              <p className="text-xs text-[#f59e0b] uppercase tracking-wider mb-1">Validate</p>
              <ul className="text-sm text-[#a1a1aa] list-disc pl-4 space-y-1">
                {insight.validation_questions.map((q, j) => <li key={j}>{q}</li>)}
              </ul>
            </div>

            <div className="mb-3">
              <p className="text-xs text-[#22c55e] uppercase tracking-wider mb-1">Recommended Actions</p>
              <ul className="text-sm text-[#a1a1aa] list-disc pl-4 space-y-1">
                {insight.recommended_actions.map((a, j) => <li key={j}>{a}</li>)}
              </ul>
            </div>

            <p className="text-xs text-[#71717a] italic">{insight.benchmark_context}</p>
            {insight.evidence && <EvidencePanel evidence={insight.evidence} />}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
