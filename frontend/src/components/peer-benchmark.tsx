"use client";

import { Card } from "@/components/ui/card";
import { motion } from "framer-motion";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from "recharts";
import { TrendingUp, Target, AlertTriangle, Sparkles } from "lucide-react";

interface Metric {
  name: string; company_value: number; unit: string; percentile: number; status: string;
  peer_p25: number; peer_p50: number; peer_p75: number;
}
interface Finding { metric: string; observation: string; interpretation: string; }

interface Benchmark {
  industry: string; peers: string[]; peer_count: number; metrics: Metric[];
  strengths: Finding[]; weaknesses: Finding[]; unusual: Finding[];
}

function percentileColor(p: number) {
  if (p >= 75) return "#22c55e"; if (p >= 40) return "#3b82f6"; return "#f59e0b";
}

export default function PeerBenchmark({ data }: { data: Benchmark }) {
  if (!data) return null;

  const radarData = data.metrics.map((m) => ({
    metric: m.name, Company: Math.min(100, (m.company_value / (m.peer_p75 || 1)) * 75),
    "P50 Peer": Math.min(100, (m.peer_p50 / (m.peer_p75 || 1)) * 75),
    "P75 Peer": 75,
  }));

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">{data.industry} — Peer Benchmark</h1>
        <p className="text-sm text-[#a1a1aa]">vs {data.peer_count} peer companies: {data.peers.slice(0, 3).join(", ")}...</p>
      </div>

      {/* Radar Chart */}
      <Card className="glass p-6">
        <h3 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wider mb-4">Performance Radar</h3>
        <div className="h-80">
          <ResponsiveContainer>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(39,39,42,0.5)" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: "#a1a1aa", fontSize: 11 }} />
              <PolarRadiusAxis tick={false} axisLine={false} />
              <Tooltip contentStyle={{ background: "#18181b", border: "1px solid #27272a", borderRadius: 8, color: "#fafafa" }} />
              <Radar name="Company" dataKey="Company" stroke="#22c55e" fill="#22c55e" fillOpacity={0.15} strokeWidth={2} />
              <Radar name="P50 Peer" dataKey="P50 Peer" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.08} strokeWidth={1} strokeDasharray="4 4" />
              <Radar name="P75 Peer" dataKey="P75 Peer" stroke="#71717a" fill="transparent" strokeWidth={1} strokeDasharray="2 2" />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <div className="flex justify-center gap-6 mt-2 text-xs text-[#a1a1aa]">
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#22c55e] rounded" /> Company</span>
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#3b82f6] rounded" /> P50 Peer</span>
          <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#71717a] rounded" /> P75 Peer</span>
        </div>
      </Card>

      {/* Metric Percentiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {data.metrics.map((m) => (
          <Card key={m.name} className="glass p-4 text-center">
            <p className="text-xs text-[#71717a] uppercase tracking-wider mb-1">{m.name}</p>
            <p className="text-xl font-bold">{m.company_value}{m.unit}</p>
            <div className="flex items-center justify-center gap-1 mt-2">
              <div className="h-1.5 flex-1 rounded-full bg-[#27272a] overflow-hidden">
                <motion.div className="h-full rounded-full" style={{ background: percentileColor(m.percentile) }}
                  initial={{ width: 0 }} animate={{ width: `${m.percentile}%` }} transition={{ duration: 0.8, delay: 0.1 }} />
              </div>
              <span className="text-xs font-semibold" style={{ color: percentileColor(m.percentile) }}>P{m.percentile}</span>
            </div>
            <p className="text-xs text-[#71717a] mt-1">{m.peer_p25} – {m.peer_p50} – {m.peer_p75} peer range</p>
          </Card>
        ))}
      </div>

      {/* Findings */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Strengths */}
        <Card className="glass p-5 border-l-4 border-[#22c55e]">
          <div className="flex items-center gap-2 mb-4"><Sparkles className="w-4 h-4 text-[#22c55e]" /><h3 className="text-sm font-semibold text-[#22c55e] uppercase">Strengths</h3></div>
          {data.strengths.map((s, i) => (
            <div key={i} className="mb-4 last:mb-0">
              <p className="text-sm font-semibold">{s.metric}</p>
              <p className="text-xs text-[#22c55e]/80 mt-1">{s.observation}</p>
              <div className="mt-2 pl-3 border-l-2 border-[#27272a]">
                <p className="text-xs text-[#71717a] uppercase tracking-wider mb-0.5">Interpretation</p>
                <p className="text-xs text-[#a1a1aa]">{s.interpretation}</p>
              </div>
            </div>
          ))}
        </Card>

        {/* Weaknesses */}
        <Card className="glass p-5 border-l-4 border-[#f59e0b]">
          <div className="flex items-center gap-2 mb-4"><AlertTriangle className="w-4 h-4 text-[#f59e0b]" /><h3 className="text-sm font-semibold text-[#f59e0b] uppercase">Weaknesses</h3></div>
          {data.weaknesses.map((s, i) => (
            <div key={i} className="mb-4 last:mb-0">
              <p className="text-sm font-semibold">{s.metric}</p>
              <p className="text-xs text-[#f59e0b]/80 mt-1">{s.observation}</p>
              <div className="mt-2 pl-3 border-l-2 border-[#27272a]">
                <p className="text-xs text-[#71717a] uppercase tracking-wider mb-0.5">Interpretation</p>
                <p className="text-xs text-[#a1a1aa]">{s.interpretation}</p>
              </div>
            </div>
          ))}
        </Card>

        {/* Unusual */}
        <Card className="glass p-5 border-l-4 border-[#3b82f6]">
          <div className="flex items-center gap-2 mb-4"><Target className="w-4 h-4 text-[#3b82f6]" /><h3 className="text-sm font-semibold text-[#3b82f6] uppercase">Unusual</h3></div>
          {data.unusual.map((s, i) => (
            <div key={i} className="mb-4 last:mb-0">
              <p className="text-sm font-semibold">{s.metric}</p>
              <p className="text-xs text-[#3b82f6]/80 mt-1">{s.observation}</p>
              <div className="mt-2 pl-3 border-l-2 border-[#27272a]">
                <p className="text-xs text-[#71717a] uppercase tracking-wider mb-0.5">Interpretation</p>
                <p className="text-xs text-[#a1a1aa]">{s.interpretation}</p>
              </div>
            </div>
          ))}
        </Card>
      </div>
    </motion.div>
  );
}
