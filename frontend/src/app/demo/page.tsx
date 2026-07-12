"use client";

import { apiUrl } from "@/lib/api";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { AuditScore, SeverityGrid, IssueTable, IssueModal, SummaryCard } from "@/components/audit-dashboard";
import type { AuditResult, Issue } from "@/components/audit-dashboard";
import ExportReport from "@/components/export-report";

export default function DemoPage() {
  const [data, setData] = useState<AuditResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);

  useEffect(() => {
    // Check for uploaded result first
    const cached = sessionStorage.getItem("auditResult");
    if (cached) {
      try {
        setData(JSON.parse(cached));
        setLoading(false);
        sessionStorage.removeItem("auditResult");
        return;
      } catch {}
    }

    fetch(apiUrl("/api/demo"))
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-[#22c55e]" />
          <p className="text-[#a1a1aa]">Running model audit...</p>
        </div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <p className="text-[#a1a1aa]">Failed to load audit data.</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen max-w-5xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-[#a1a1aa] hover:text-[#fafafa] transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back
        </Link>
        <span className="text-xs text-[#71717a] bg-[#ffffff06] border border-[#27272a] rounded-full px-3 py-1">
          Demo Mode — Sample Data
        </span>
      </div>

      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8">
        <AuditScore result={data} />
        <SeverityGrid breakdown={data.severity_breakdown} />
        <SummaryCard summary={data.summary} />
        <IssueTable issues={data.issues} onSelect={setSelectedIssue} />
        <ExportReport result={data} />
      </motion.div>

      <IssueModal issue={selectedIssue} open={!!selectedIssue} onClose={() => setSelectedIssue(null)} />
    </main>
  );
}
