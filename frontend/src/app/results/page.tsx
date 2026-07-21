"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, FileSpreadsheet, Loader2, AlertTriangle } from "lucide-react";
import { AuditScore, SeverityGrid, IssueTable, IssueModal, SummaryCard } from "@/components/audit-dashboard";
import type { AuditResult, Issue } from "@/components/audit-dashboard";
import ExportReport from "@/components/export-report";

export default function ResultsPage() {
  const [data, setData] = useState<AuditResult | null>(null);
  const [filename, setFilename] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);

  useEffect(() => {
    let cancelled = false;

    queueMicrotask(() => {
      if (cancelled) return;

      const cached = sessionStorage.getItem("auditResult");
      const cachedName = sessionStorage.getItem("auditFilename");

      if (cached && cachedName) {
        try {
          const cachedData: AuditResult = JSON.parse(cached);
          setData(cachedData);
          setFilename(cachedName);
        } catch {
          setError("Failed to parse audit result. The response may be malformed.");
        }
      }

      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-[#22c55e]" />
          <p className="text-[#a1a1aa]">Loading audit result...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 max-w-md text-center">
          <AlertTriangle className="w-8 h-8 text-[#ef4444]" />
          <p className="text-[#a1a1aa]">{error}</p>
          <Link href="/upload" className="text-[#22c55e] text-sm hover:underline">
            ← Try uploading again
          </Link>
        </div>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 max-w-md text-center">
          <FileSpreadsheet className="w-8 h-8 text-[#71717a]" />
          <p className="text-[#a1a1aa]">
            No audit result found. For privacy, uploaded results are not stored
            permanently. Please upload the workbook again.
          </p>
          <Link href="/upload" className="text-[#22c55e] text-sm hover:underline">
            ← Go to upload
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen max-w-5xl mx-auto px-6 py-8">
      <Link href="/upload" className="inline-flex items-center gap-2 text-sm text-[#a1a1aa] hover:text-[#fafafa] mb-4 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Upload another file
      </Link>

      {/* Uploaded file badge */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass p-4 mb-6 flex items-center gap-3"
      >
        <FileSpreadsheet className="w-5 h-5 text-[#22c55e]" />
        <div>
          <p className="text-sm font-semibold">{filename}</p>
          <p className="text-xs text-[#71717a]">Uploaded workbook — audit result below</p>
        </div>
      </motion.div>

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
