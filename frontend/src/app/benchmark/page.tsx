"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Loader2, Cloud, Factory, Landmark } from "lucide-react";
import PeerBenchmark from "@/components/peer-benchmark";

const industries = [
  { id: "saas", label: "Cloud / SaaS", icon: <Cloud className="w-5 h-5" />, desc: "48 peer companies" },
  { id: "manufacturing", label: "Industrial Manufacturing", icon: <Factory className="w-5 h-5" />, desc: "36 peer companies" },
  { id: "financial", label: "Banking / Financial Services", icon: <Landmark className="w-5 h-5" />, desc: "42 peer companies" },
];

export default function BenchmarkPage() {
  const [industry, setIndustry] = useState("saas");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { fetchBenchmark(industry); }, [industry]);

  async function fetchBenchmark(id: string) {
    setLoading(true);
    try {
      const res = await fetch(`/api/benchmark/${id}`);
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
        <h1 className="text-3xl font-bold mb-2">Peer Benchmark</h1>
        <p className="text-[#a1a1aa] mb-6">Compare financial metrics against industry peers with percentile rankings and analyst interpretation.</p>

        {/* Industry Selector */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-8">
          {industries.map((ind) => (
            <button key={ind.id} onClick={() => setIndustry(ind.id)}
              className={`glass p-4 text-left transition-all hover:border-[#22c55e]/30 ${industry === ind.id ? "border-[#22c55e] bg-[#22c55e]/5" : ""}`}>
              <div className="text-[#a1a1aa] mb-2">{ind.icon}</div>
              <p className="text-sm font-semibold">{ind.label}</p>
              <p className="text-xs text-[#71717a] mt-1">{ind.desc}</p>
            </button>
          ))}
        </div>

        {loading && <div className="flex justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-[#22c55e]" /></div>}
        {!loading && data && <PeerBenchmark data={data} />}
      </motion.div>
    </main>
  );
}
