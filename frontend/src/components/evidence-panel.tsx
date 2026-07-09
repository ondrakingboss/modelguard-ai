"use client";

import { motion } from "framer-motion";
import { FileText, Brain, Lightbulb, HelpCircle, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface EvidenceSource {
  source: string;
  location: string;
  data_point: string;
}

interface EvidenceTrail {
  supporting: EvidenceSource[];
  reasoning_chain: string[];
  assumptions: string[];
  missing: string[];
  confidence_breakdown: string;
}

export default function EvidencePanel({ evidence }: { evidence: EvidenceTrail }) {
  const [open, setOpen] = useState(false);
  if (!evidence) return null;

  return (
    <div className="mt-3">
      <button onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-xs text-[#71717a] hover:text-[#22c55e] transition-colors">
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        Evidence Trail {open ? "" : "(click to explore)"}
      </button>

      {open && (
        <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
          className="mt-3 space-y-3">

          {/* Supporting Evidence */}
          <div className="glass p-3">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-3 h-3 text-[#22c55e]" />
              <span className="text-xs text-[#22c55e] uppercase tracking-wider font-semibold">Supporting Evidence</span>
            </div>
            <div className="space-y-2">
              {evidence.supporting.map((e, i) => (
                <div key={i} className="text-sm">
                  <span className="text-[#22c55e] font-semibold">{e.data_point}</span>
                  <div className="flex gap-3 text-xs text-[#71717a] mt-0.5">
                    <span>{e.source}</span>
                    <span>·</span>
                    <span className="italic">{e.location}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Reasoning Chain */}
          <div className="glass p-3">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-3 h-3 text-[#3b82f6]" />
              <span className="text-xs text-[#3b82f6] uppercase tracking-wider font-semibold">Reasoning Chain</span>
            </div>
            <ol className="space-y-1 text-sm text-[#a1a1aa] list-decimal list-inside">
              {evidence.reasoning_chain.map((step, i) => (
                <li key={i}>{step}</li>
              ))}
            </ol>
          </div>

          {/* Assumptions */}
          <div className="glass p-3">
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb className="w-3 h-3 text-[#f59e0b]" />
              <span className="text-xs text-[#f59e0b] uppercase tracking-wider font-semibold">Assumptions Made</span>
            </div>
            <ul className="space-y-1 text-sm text-[#a1a1aa] list-disc list-inside">
              {evidence.assumptions.map((a, i) => <li key={i}>{a}</li>)}
            </ul>
          </div>

          {/* Missing Evidence */}
          <div className="glass p-3">
            <div className="flex items-center gap-2 mb-2">
              <HelpCircle className="w-3 h-3 text-[#ef4444]" />
              <span className="text-xs text-[#ef4444] uppercase tracking-wider font-semibold">Missing Evidence</span>
            </div>
            <ul className="space-y-1 text-sm text-[#a1a1aa] list-disc list-inside">
              {evidence.missing.map((m, i) => <li key={i}>{m}</li>)}
            </ul>
          </div>

          {/* Confidence Breakdown */}
          <div className="glass p-3 border border-[#22c55e]/20">
            <p className="text-xs text-[#22c55e] uppercase tracking-wider font-semibold mb-1">Confidence Derivation</p>
            <p className="text-xs text-[#a1a1aa]">{evidence.confidence_breakdown}</p>
          </div>
        </motion.div>
      )}
    </div>
  );
}
