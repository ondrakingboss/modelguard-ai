"use client";

import { apiUrl } from "@/lib/api";
import { useEffect, useState, type ComponentProps } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Loader2, Cloud, Factory, Zap } from "lucide-react";
import ConfidenceHeatmap from "@/components/confidence-heatmap";

type ConfidenceData = ComponentProps<typeof ConfidenceHeatmap>["data"];

const scenarios = [
  { id: "startup", label: "Startup", icon: <Zap className="w-5 h-5" />, desc: "Series B SaaS" },
  { id: "manufacturing", label: "Manufacturing", icon: <Factory className="w-5 h-5" />, desc: "Mature industrial" },
  { id: "saas", label: "SaaS", icon: <Cloud className="w-5 h-5" />, desc: "Mid-stage cloud" },
];

export default function ConfidencePage() {
  const [scenario, setScenario] = useState("startup");
  const [data, setData] = useState<ConfidenceData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    async function loadConfidence() {
      setLoading(true);
      try {
        const res = await fetch(apiUrl(`/api/confidence/${scenario}`), { signal: controller.signal });
        if (res.ok) {
          const json: { categories: ConfidenceData } = await res.json();
          setData(json.categories);
        }
      } catch (error) {
        if (!(error instanceof DOMException && error.name === "AbortError")) setData(null);
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void loadConfidence();
    return () => controller.abort();
  }, [scenario]);

  return (
    <main className="min-h-screen max-w-3xl mx-auto px-6 py-8">
      <Link href="/" className="inline-flex items-center gap-2 text-sm text-[#a1a1aa] hover:text-[#fafafa] mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold mb-2">Confidence Heatmap</h1>
        <p className="text-[#a1a1aa] mb-6">Evidence-based confidence scores showing what supports — and what&apos;s missing from — every analytical conclusion.</p>

        {/* Scenario Selector */}
        <div className="grid grid-cols-3 gap-3 mb-8">
          {scenarios.map((s) => (
            <button key={s.id} onClick={() => setScenario(s.id)}
              className={`glass p-4 text-left transition-all hover:border-[#22c55e]/30 ${scenario === s.id ? "border-[#22c55e] bg-[#22c55e]/5" : ""}`}>
              <div className="text-[#a1a1aa] mb-2">{s.icon}</div>
              <p className="text-sm font-semibold">{s.label}</p>
              <p className="text-xs text-[#71717a] mt-1">{s.desc}</p>
            </button>
          ))}
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-[#22c55e]" />
          </div>
        )}

        {!loading && data && <ConfidenceHeatmap data={data} />}
      </motion.div>
    </main>
  );
}
