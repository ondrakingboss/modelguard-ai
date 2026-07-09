"use client";

import { Card } from "@/components/ui/card";
import { motion } from "framer-motion";
import { TrendingUp, Activity, PiggyBank, Landmark, Target, Info, AlertTriangle, CheckCircle2, HelpCircle } from "lucide-react";
import { useState } from "react";

interface ConfidenceCategory {
  category: string;
  score: number;
  supporting_evidence: string[];
  missing_evidence: string[];
  assessment: string;
}

function scoreColor(score: number) {
  if (score >= 85) return { bg: "rgba(34,197,94,0.15)", border: "rgba(34,197,94,0.4)", text: "#22c55e", label: "High" };
  if (score >= 65) return { bg: "rgba(59,130,246,0.15)", border: "rgba(59,130,246,0.4)", text: "#3b82f6", label: "Moderate" };
  if (score >= 45) return { bg: "rgba(245,158,11,0.15)", border: "rgba(245,158,11,0.4)", text: "#f59e0b", label: "Low" };
  return { bg: "rgba(239,68,68,0.15)", border: "rgba(239,68,68,0.4)", text: "#ef4444", label: "Very Low" };
}

function categoryIcon(cat: string) {
  const icons: Record<string, React.ReactNode> = {
    Revenue: <TrendingUp className="w-5 h-5" />,
    Margin: <Activity className="w-5 h-5" />,
    "Cash Flow": <PiggyBank className="w-5 h-5" />,
    "Balance Sheet": <Landmark className="w-5 h-5" />,
    Forecast: <Target className="w-5 h-5" />,
  };
  return icons[cat] || <Target className="w-5 h-5" />;
}

function HeatmapCard({ category, expanded, onToggle }: { category: ConfidenceCategory; expanded: boolean; onToggle: () => void }) {
  const colors = scoreColor(category.score);

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="glass cursor-pointer transition-all hover:border-[#22c55e]/20"
      style={{ borderColor: expanded ? colors.border : undefined }}
      onClick={onToggle}
    >
      {/* Header */}
      <div className="p-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg" style={{ background: colors.bg, color: colors.text }}>
            {categoryIcon(category.category)}
          </div>
          <div>
            <h3 className="font-semibold">{category.category}</h3>
            <p className="text-xs text-[#71717a]">{colors.label} Confidence</p>
          </div>
        </div>

        {/* Score ring */}
        <div className="relative w-16 h-16 flex items-center justify-center">
          <svg className="absolute w-full h-full -rotate-90">
            <circle cx="32" cy="32" r="28" fill="none" stroke="rgba(39,39,42,0.5)" strokeWidth="4" />
            <motion.circle cx="32" cy="32" r="28" fill="none" stroke={colors.text} strokeWidth="4"
              strokeDasharray={2 * Math.PI * 28}
              initial={{ strokeDashoffset: 2 * Math.PI * 28 }}
              animate={{ strokeDashoffset: (1 - category.score / 100) * 2 * Math.PI * 28 }}
              transition={{ duration: 1, ease: "easeOut" }}
              strokeLinecap="round" />
          </svg>
          <span className="text-lg font-bold relative z-10" style={{ color: colors.text }}>{category.score}</span>
        </div>
      </div>

      {/* Expanded Detail */}
      {expanded && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
          className="px-5 pb-5 space-y-4">
          {/* Assessment */}
          <div className="glass p-3">
            <div className="flex items-center gap-2 mb-1">
              <Info className="w-3 h-3" style={{ color: colors.text }} />
              <span className="text-xs font-semibold" style={{ color: colors.text }}>Assessment</span>
            </div>
            <p className="text-sm">{category.assessment}</p>
          </div>

          {/* Supporting Evidence */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="w-3 h-3 text-[#22c55e]" />
              <span className="text-xs text-[#22c55e] uppercase tracking-wider font-semibold">Supporting Evidence</span>
            </div>
            <ul className="space-y-1">
              {category.supporting_evidence.map((e, i) => (
                <li key={i} className="text-sm text-[#a1a1aa] flex items-start gap-2">
                  <span className="text-[#22c55e] mt-0.5">+</span> {e}
                </li>
              ))}
            </ul>
          </div>

          {/* Missing Evidence */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <HelpCircle className="w-3 h-3 text-[#f59e0b]" />
              <span className="text-xs text-[#f59e0b] uppercase tracking-wider font-semibold">Missing Evidence</span>
            </div>
            <ul className="space-y-1">
              {category.missing_evidence.map((e, i) => (
                <li key={i} className="text-sm text-[#a1a1aa] flex items-start gap-2">
                  <span className="text-[#ef4444] mt-0.5">−</span> {e}
                </li>
              ))}
            </ul>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}

export default function ConfidenceHeatmap({ data }: { data: ConfidenceCategory[] }) {
  const [expanded, setExpanded] = useState<number | null>(null);
  if (!data) return null;

  const avg = Math.round(data.reduce((s, c) => s + c.score, 0) / data.length);
  const avgColor = scoreColor(avg);

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
      {/* Overall Score */}
      <div className="glass p-6 text-center">
        <p className="text-sm text-[#71717a] uppercase tracking-wider mb-2">Overall Analysis Confidence</p>
        <motion.span className="text-5xl font-bold" style={{ color: avgColor.text }}
          initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", delay: 0.2 }}>
          {avg}%
        </motion.span>
        <p className="text-sm text-[#a1a1aa] mt-2">{avgColor.label} — across {data.length} categories</p>
      </div>

      {/* Heatmap Grid */}
      <div className="space-y-3">
        {data.map((cat, i) => (
          <HeatmapCard key={cat.category} category={cat}
            expanded={expanded === i} onToggle={() => setExpanded(expanded === i ? null : i)} />
        ))}
      </div>
    </motion.div>
  );
}
