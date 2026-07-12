"use client";

import { apiUrl } from "@/lib/api";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Loader2, Building2, Factory, Cloud, ShoppingBag, AlertTriangle } from "lucide-react";
import FinancialIntelligence from "@/components/financial-intelligence";

const scenarios = [
  { id: "startup", label: "High-Growth Startup", icon: <Building2 className="w-5 h-5" />, desc: "SaaS, burning cash, Series B" },
  { id: "manufacturing", label: "Manufacturer", icon: <Factory className="w-5 h-5" />, desc: "Mature, stable cash flows" },
  { id: "saas", label: "SaaS Company", icon: <Cloud className="w-5 h-5" />, desc: "Mid-stage, strong margins" },
  { id: "retail", label: "Retail Chain", icon: <ShoppingBag className="w-5 h-5" />, desc: "Thin margins, seasonal" },
  { id: "leveraged", label: "Leveraged Corp", icon: <AlertTriangle className="w-5 h-5" />, desc: "High debt, restructuring risk" },
];

export default function AnalyzePage() {
  const [scenario, setScenario] = useState("startup");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchAnalysis(scenario); }, [scenario]);

  async function fetchAnalysis(id: string) {
    setLoading(true);
    try {
      const res = await fetch(apiUrl(`/api/analyze/${id}`));
      if (res.ok) setData(await res.json());
    } catch {}
    setLoading(false);
  }

  return (
    <main className="min-h-screen max-w-5xl mx-auto px-6 py-8">
      <Link href="/" className="inline-flex items-center gap-2 text-sm text-[#a1a1aa] hover:text-[#fafafa] mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold mb-2">Financial Intelligence</h1>
        <p className="text-[#a1a1aa] mb-6">AI analyst review across 5 business scenarios with differentiated financial reasoning.</p>

        {/* Scenario Selector */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-8">
          {scenarios.map((s) => (
            <button key={s.id} onClick={() => setScenario(s.id)}
              className={`glass p-4 text-left transition-all hover:border-[#22c55e]/30 ${scenario === s.id ? "border-[#22c55e] bg-[#22c55e]/5" : ""}`}>
              <div className="text-[#a1a1aa] mb-2">{s.icon}</div>
              <p className="text-sm font-semibold">{s.label}</p>
              <p className="text-xs text-[#71717a] mt-1">{s.desc}</p>
            </button>
          ))}
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="w-8 h-8 animate-spin text-[#22c55e]" />
              <p className="text-[#a1a1aa]">Analyzing financial assumptions...</p>
            </div>
          </div>
        )}

        {/* Intelligence Dashboard */}
        {!loading && data && <FinancialIntelligence data={data} />}

        {!loading && !data && (
          <div className="flex items-center justify-center py-20">
            <p className="text-[#a1a1aa]">Select a scenario above to begin analysis.</p>
          </div>
        )}
      </motion.div>
    </main>
  );
}
