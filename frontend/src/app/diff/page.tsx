"use client";

import { apiUrl } from "@/lib/api";
import { useEffect, useState, type ComponentProps } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Loader2, GitCompare, Cloud, Factory, Landmark } from "lucide-react";
import CompanyDiffView from "@/components/company-diff";

type CompanyDiffData = ComponentProps<typeof CompanyDiffView>["data"];

const pairs = [
  { id: "tech_growth", label: "Tech — Growth Trajectory", icon: <Cloud className="w-5 h-5" />, desc: "SaaS company across two fiscal years" },
  { id: "industrial_restructuring", label: "Industrial — Restructuring", icon: <Factory className="w-5 h-5" />, desc: "Manufacturer before/after transformation" },
  { id: "bank_nim", label: "Bank — Rate Cycle Shift", icon: <Landmark className="w-5 h-5" />, desc: "Bank navigating interest rate changes" },
];

export default function DiffPage() {
  const [pair, setPair] = useState("tech_growth");
  const [data, setData] = useState<CompanyDiffData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    async function loadDiff() {
      setLoading(true);
      try {
        const res = await fetch(apiUrl(`/api/demo-diff/${pair}`), { signal: controller.signal });
        if (res.ok) {
          const nextData: CompanyDiffData = await res.json();
          setData(nextData);
        }
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError")) setData(null);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void loadDiff();
    return () => controller.abort();
  }, [pair]);

  return (
    <main className="min-h-screen max-w-5xl mx-auto px-6 py-8">
      <Link href="/" className="inline-flex items-center gap-2 text-sm text-[#a1a1aa] hover:text-[#fafafa] mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="flex items-center gap-3 mb-2">
          <GitCompare className="w-6 h-6 text-[#22c55e]" />
          <h1 className="text-3xl font-bold">Company Diff</h1>
        </div>
        <p className="text-[#a1a1aa] mb-6">Compare two reporting periods — revenue, margins, debt, cash flow, guidance, risks, and more.</p>

        {/* Pair Selector */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-8">
          {pairs.map((p) => (
            <button key={p.id} onClick={() => setPair(p.id)}
              className={`glass p-4 text-left transition-all hover:border-[#22c55e]/30 ${pair === p.id ? "border-[#22c55e] bg-[#22c55e]/5" : ""}`}>
              <div className="text-[#a1a1aa] mb-2">{p.icon}</div>
              <p className="text-sm font-semibold">{p.label}</p>
              <p className="text-xs text-[#71717a] mt-1">{p.desc}</p>
            </button>
          ))}
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="w-8 h-8 animate-spin text-[#22c55e]" />
              <p className="text-[#a1a1aa]">Running comparison analysis...</p>
            </div>
          </div>
        )}

        {/* Diff Dashboard */}
        {!loading && data && <CompanyDiffView data={data} />}
      </motion.div>
    </main>
  );
}
