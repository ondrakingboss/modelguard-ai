"use client";

import { Card } from "@/components/ui/card";
import { motion } from "framer-motion";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from "recharts";
import { Target, AlertTriangle, Sparkles, CheckCircle2, ShieldAlert, Ban, Filter, ExternalLink, Info } from "lucide-react";
import { useState, useMemo } from "react";

interface SourceRow {
  company: string; ticker: string; fiscal_year: string; filing_type: string;
  metric: string; reported_value: string; reported_unit: string; normalized_value: number;
  gaap_or_non_gaap: string; source_section: string; source_url: string; formula: string;
  quality_flag: string; inclusion_status: string; inclusion_rationale: string;
  in_full_percentile: boolean; in_adjusted_percentile: boolean; in_strict_percentile: boolean;
}

interface Metric {
  name: string; company_value: number; unit: string;
  full_percentile: number; adjusted_percentile: number; strict_comparability_percentile: number;
  cohort_size_full: number; cohort_size_adjusted: number; caution_count: number; excluded_count: number;
  peer_p25: number; peer_p50: number; peer_p75: number;
}

interface Finding { metric: string; observation: string; interpretation: string; }

interface Benchmark {
  industry: string; peers: string[]; peer_count: number; metrics: Metric[];
  strengths: Finding[]; weaknesses: Finding[]; unusual: Finding[];
  source_detail?: SourceRow[]; quality_flags?: string[];
}

function statusBadge(status: string) {
  const styles: Record<string, { bg: string; text: string; icon: React.ReactNode; label: string }> = {
    included: { bg: "rgba(34,197,94,0.12)", text: "#22c55e", icon: <CheckCircle2 className="w-3 h-3" />, label: "Included" },
    included_with_caution: { bg: "rgba(245,158,11,0.12)", text: "#f59e0b", icon: <ShieldAlert className="w-3 h-3" />, label: "Caution" },
    excluded: { bg: "rgba(239,68,68,0.12)", text: "#ef4444", icon: <Ban className="w-3 h-3" />, label: "Excluded" },
  };
  const s = styles[status] || styles.included;
  return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold" style={{ background: s.bg, color: s.text }}>{s.icon}{s.label}</span>;
}

function PercentileCard({ label, percentile, cohort, caution, excluded, tip }: { label: string; percentile: number; cohort: number; caution: number; excluded: number; tip: string }) {
  return (
    <Card className="glass p-4 text-center relative group">
      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <Info className="w-3 h-3 text-[#71717a]" />
      </div>
      <p className="text-xs text-[#71717a] uppercase tracking-wider mb-1">{label}</p>
      <p className="text-2xl font-bold text-[#22c55e]">P{percentile}</p>
      <p className="text-xs text-[#71717a] mt-1">{cohort} peers</p>
      {(caution > 0 || excluded > 0) && (
        <p className="text-xs text-[#71717a]">{caution > 0 ? `${caution} caution` : ""}{caution > 0 && excluded > 0 ? ", " : ""}{excluded > 0 ? `${excluded} excluded` : ""}</p>
      )}
    </Card>
  );
}

export default function PeerBenchmark({ data }: { data: Benchmark }) {
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");

  if (!data) return (
    <Card className="glass p-8 text-center"><p className="text-[#71717a]">Backend unavailable. Check that the API server is running.</p></Card>
  );

  const radarData = data.metrics.map((m) => ({
    metric: m.name, Company: Math.min(100, (m.company_value / (m.peer_p75 || 1)) * 75),
    "P50 Peer": Math.min(100, (m.peer_p50 / (m.peer_p75 || 1)) * 75), "P75 Peer": 75,
  }));

  const sourceDetail: SourceRow[] = data.source_detail || [];
  const metricNames = [...new Set(sourceDetail.map(r => r.metric))];

  const filteredRows = useMemo(() => {
    let rows = sourceDetail;
    if (selectedMetric) rows = rows.filter(r => r.metric === selectedMetric);
    if (filter === "included") rows = rows.filter(r => r.inclusion_status === "included");
    if (filter === "included_with_caution") rows = rows.filter(r => r.inclusion_status === "included_with_caution");
    if (filter === "excluded") rows = rows.filter(r => r.inclusion_status === "excluded");
    if (filter === "flagged") rows = rows.filter(r => !!r.quality_flag);
    return rows;
  }, [sourceDetail, selectedMetric, filter]);

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">{data.industry} — Peer Benchmark</h1>
        <p className="text-sm text-[#a1a1aa]">vs {data.peer_count} peer companies: {data.peers.slice(0, 3).join(", ")}...</p>
      </div>

      {/* Percentile Comparison */}
      {data.metrics.length > 0 && (
        <Card className="glass p-5">
          <h3 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wider mb-3">Percentile Cohorts — {data.metrics[0].name}</h3>
          <div className="grid grid-cols-3 gap-3 mb-3">
            <PercentileCard label="Full Cohort" percentile={data.metrics[0].full_percentile} cohort={data.metrics[0].cohort_size_full} caution={0} excluded={0}
              tip="All peers included. Caution rows and outliers participate." />
            <PercentileCard label="Adjusted" percentile={data.metrics[0].adjusted_percentile} cohort={data.metrics[0].cohort_size_adjusted} caution={data.metrics[0].caution_count} excluded={data.metrics[0].excluded_count}
              tip="Excludes only excluded rows. Caution rows and outliers remain." />
            <PercentileCard label="Strict" percentile={data.metrics[0].strict_comparability_percentile} cohort={data.metrics[0].cohort_size_full - data.metrics[0].caution_count} caution={0} excluded={data.metrics[0].caution_count}
              tip="Excludes caution rows. Only clean data. Most conservative." />
          </div>
          <p className="text-xs text-[#71717a] italic">
            Quality flags do not automatically mean data is invalid. Full benchmarks include valid caution rows and genuine outliers. Strict-comparability benchmarks exclude caution rows.
          </p>
        </Card>
      )}

      {/* Radar + Metric Cards (condensed) */}
      <Card className="glass p-6"><h3 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wider mb-4">Performance Radar</h3>
        <div className="h-80"><ResponsiveContainer><RadarChart data={radarData}>
          <PolarGrid stroke="rgba(39,39,42,0.5)" /><PolarAngleAxis dataKey="metric" tick={{ fill: "#a1a1aa", fontSize: 11 }} /><PolarRadiusAxis tick={false} axisLine={false} />
          <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, color: "#fafafa" }} />
          <Radar name="Company" dataKey="Company" stroke="#22c55e" fill="#22c55e" fillOpacity={0.15} strokeWidth={2} />
          <Radar name="P50 Peer" dataKey="P50 Peer" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.08} strokeWidth={1} strokeDasharray="4 4" />
        </RadarChart></ResponsiveContainer></div>
      </Card>

      {/* Metric Selector */}
      <div className="flex flex-wrap gap-2">
        <button onClick={() => setSelectedMetric(null)} className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${!selectedMetric ? "bg-[#22c55e]/20 text-[#22c55e]" : "glass text-[#a1a1aa]"}`}>All metrics</button>
        {metricNames.map(m => (
          <button key={m} onClick={() => setSelectedMetric(selectedMetric === m ? null : m)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${selectedMetric === m ? "bg-[#22c55e]/20 text-[#22c55e]" : "glass text-[#a1a1aa]"}`}>{m}</button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <Filter className="w-3 h-3 text-[#71717a]" />
        {["all", "included", "included_with_caution", "excluded", "flagged"].map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-2 py-1 rounded text-xs transition-colors ${filter === f ? "bg-[#27272a] text-[#fafafa]" : "text-[#71717a] hover:text-[#fafafa]"}`}>
            {f.replace(/_/g, " ")}{f === "included_with_caution" ? " (caution)" : ""}
          </button>
        ))}
        <span className="text-xs text-[#71717a] ml-auto">{filteredRows.length} rows</span>
      </div>

      {/* Audit Trail Table */}
      {filteredRows.length > 0 ? (
        <Card className="glass overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-[#27272a] text-left text-[#71717a]">
                <th className="p-2">Company</th><th className="p-2">Ticker</th><th className="p-2">FY</th>
                <th className="p-2">Reported</th><th className="p-2">Normalized</th><th className="p-2">GAAP</th>
                <th className="p-2">Status</th><th className="p-2">Flag</th><th className="p-2">Source</th>
              </tr></thead>
              <tbody>
                {filteredRows.map((r, i) => (
                  <tr key={i} className="border-b border-[#27272a] hover:bg-[#18181b]">
                    <td className="p-2 font-semibold">{r.company}</td>
                    <td className="p-2 text-[#71717a]">{r.ticker}</td>
                    <td className="p-2 text-[#71717a]">{r.fiscal_year}</td>
                    <td className="p-2">{r.reported_value}</td>
                    <td className="p-2 font-mono text-[#22c55e]">{r.normalized_value}</td>
                    <td className="p-2"><span className="px-1.5 py-0.5 rounded bg-[#22c55e]/10 text-[#22c55e]">{r.gaap_or_non_gaap}</span></td>
                    <td className="p-2">{statusBadge(r.inclusion_status)}</td>
                    <td className="p-2">{r.quality_flag ? <span className="text-[#f59e0b]">{r.quality_flag.replace(/_/g, " ")}</span> : <span className="text-[#71717a]">—</span>}</td>
                    <td className="p-2">
                      {r.source_url ? <a href={r.source_url} target="_blank" rel="noopener noreferrer" className="text-[#3b82f6] hover:underline inline-flex items-center gap-1"><ExternalLink className="w-3 h-3" />{r.source_section || "SEC Filing"}</a> : <span className="text-[#71717a]">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : (
        <Card className="glass p-6 text-center"><p className="text-[#71717a] text-sm">No rows match the selected filters.</p></Card>
      )}

      {/* Rationale Tooltip Panel */}
      {filteredRows.length > 0 && filteredRows.some(r => r.inclusion_rationale) && (
        <details className="glass p-4 rounded-xl">
          <summary className="text-xs text-[#71717a] cursor-pointer hover:text-[#fafafa]">View inclusion rationales</summary>
          <div className="mt-2 space-y-2">
            {filteredRows.filter(r => r.inclusion_rationale).map((r, i) => (
              <div key={i} className="text-xs"><span className="font-semibold">{r.company} {r.metric}:</span> <span className="text-[#a1a1aa]">{r.inclusion_rationale}</span></div>
            ))}
          </div>
        </details>
      )}

      {/* Findings */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass p-5 border-l-4 border-[#22c55e]"><div className="flex items-center gap-2 mb-4"><Sparkles className="w-4 h-4 text-[#22c55e]" /><h3 className="text-sm font-semibold text-[#22c55e] uppercase">Strengths</h3></div>
          {data.strengths.map((s, i) => <div key={i} className="mb-4 last:mb-0"><p className="text-sm font-semibold">{s.metric}</p><p className="text-xs text-[#22c55e]/80 mt-1">{s.observation}</p><div className="mt-2 pl-3 border-l-2 border-[#27272a]"><p className="text-xs text-[#71717a] uppercase tracking-wider mb-0.5">Interpretation</p><p className="text-xs text-[#a1a1aa]">{s.interpretation}</p></div></div>)}
        </Card>
        <Card className="glass p-5 border-l-4 border-[#f59e0b]"><div className="flex items-center gap-2 mb-4"><AlertTriangle className="w-4 h-4 text-[#f59e0b]" /><h3 className="text-sm font-semibold text-[#f59e0b] uppercase">Weaknesses</h3></div>
          {data.weaknesses.map((s, i) => <div key={i} className="mb-4 last:mb-0"><p className="text-sm font-semibold">{s.metric}</p><p className="text-xs text-[#f59e0b]/80 mt-1">{s.observation}</p><div className="mt-2 pl-3 border-l-2 border-[#27272a]"><p className="text-xs text-[#71717a] uppercase tracking-wider mb-0.5">Interpretation</p><p className="text-xs text-[#a1a1aa]">{s.interpretation}</p></div></div>)}
        </Card>
        <Card className="glass p-5 border-l-4 border-[#3b82f6]"><div className="flex items-center gap-2 mb-4"><Target className="w-4 h-4 text-[#3b82f6]" /><h3 className="text-sm font-semibold text-[#3b82f6] uppercase">Unusual</h3></div>
          {data.unusual.map((s, i) => <div key={i} className="mb-4 last:mb-0"><p className="text-sm font-semibold">{s.metric}</p><p className="text-xs text-[#3b82f6]/80 mt-1">{s.observation}</p><div className="mt-2 pl-3 border-l-2 border-[#27272a]"><p className="text-xs text-[#71717a] uppercase tracking-wider mb-0.5">Interpretation</p><p className="text-xs text-[#a1a1aa]">{s.interpretation}</p></div></div>)}
        </Card>
      </div>
    </motion.div>
  );
}
