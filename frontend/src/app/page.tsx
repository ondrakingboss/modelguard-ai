"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Shield, Search, Lightbulb, BarChart3 } from "lucide-react";

const features = [
  { icon: Search, title: "Formula Audit", desc: "Detects #REF!, #DIV/0!, inconsistent formulas, and hardcoded constants across every sheet." },
  { icon: Shield, title: "Risk Detection", desc: "Identifies hidden sheets, hidden rows/columns, external links, and circular references." },
  { icon: BarChart3, title: "Business Logic Checks", desc: "Flags suspicious revenue growth, margin jumps, negative cash flow, and broken assumptions." },
  { icon: Lightbulb, title: "AI Explanations", desc: "Every issue comes with a plain-English explanation of why it matters and how to fix it." },
];

export default function LandingPage() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="hero-grid relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#09090b]/80 to-[#09090b]" />
        <div className="relative max-w-5xl mx-auto px-6 pt-32 pb-24 text-center">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass border-[#22c55e]/20 mb-8">
              <span className="w-2 h-2 rounded-full bg-[#22c55e] animate-pulse" />
              <span className="text-sm text-[#a1a1aa]">AI-Powered Excel Auditing</span>
            </div>
            <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
              Audit Your<br />
              <span className="text-[#22c55e]">Financial Models</span>
              {" "}with AI
            </h1>
            <p className="text-lg text-[#a1a1aa] max-w-2xl mx-auto mb-10 leading-relaxed">
              ModelGuard catches formula errors, hidden risks, and suspicious patterns in your Excel models.
              Like Grammarly for financial models — built for FP&A, investment banking, and audit professionals.
            </p>
            <div className="flex gap-4 justify-center">
              <Link href="/upload">
                <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                  className="px-8 py-3 bg-[#22c55e] text-[#022c22] font-semibold rounded-xl flex items-center gap-2 hover:bg-[#16a34a] transition-colors">
                  Upload Your Model <ArrowRight className="w-4 h-4" />
                </motion.button>
              </Link>
              <Link href="/demo">
                <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                  className="px-8 py-3 glass font-semibold rounded-xl hover:bg-[#27272a]/50 transition-colors">
                  Try Demo
                </motion.button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-6 pb-24">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="grid grid-cols-1 md:grid-cols-2 gap-4"
        >
          {features.map((f, i) => (
            <motion.div key={f.title} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + i * 0.1 }}
              className="glass p-6 hover:border-[#22c55e]/20 transition-colors"
            >
              <f.icon className="w-8 h-8 text-[#22c55e] mb-3" />
              <h3 className="font-semibold mb-2">{f.title}</h3>
              <p className="text-sm text-[#a1a1aa] leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#27272a] py-8 text-center text-sm text-[#71717a]">
        ModelGuard AI — Built for finance professionals who care about model integrity.
      </footer>
    </main>
  );
}
