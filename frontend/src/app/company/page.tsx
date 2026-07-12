"use client";

import { apiUrl } from "@/lib/api";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowLeft, Loader2, Cloud, Factory, Landmark, UploadCloud } from "lucide-react";
import CompanyIntelligence from "@/components/company-intelligence";

const industries = [
  { id: "tech", label: "Cloud / SaaS", icon: <Cloud className="w-5 h-5" />, desc: "Multi-segment tech company" },
  { id: "industrial", label: "Industrial", icon: <Factory className="w-5 h-5" />, desc: "Manufacturing conglomerate" },
  { id: "financial", label: "Financial Services", icon: <Landmark className="w-5 h-5" />, desc: "Banking & lending" },
];

export default function CompanyPage() {
  const [industry, setIndustry] = useState("tech");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { fetchDemo(industry); }, [industry]);

  async function fetchDemo(id: string) {
    setLoading(true); setError(null);
    try {
      const res = await fetch(apiUrl(`/api/company-demo/${id}`));
      if (res.ok) setData(await res.json());
      else setError("Failed to load demo profile.");
    } catch { setError("Backend connection failed."); }
    setLoading(false);
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true); setError(null);
    try {
      const fd = new FormData(); fd.append("file", file);
      const res = await fetch(apiUrl("/api/analyze-company"), { method: "POST", body: fd });
      if (!res.ok) throw new Error(await res.text());
      setData(await res.json());
    } catch (e: any) { setError(e.message || "Upload failed"); }
    setUploading(false);
  }

  return (
    <main className="min-h-screen max-w-5xl mx-auto px-6 py-8">
      <Link href="/" className="inline-flex items-center gap-2 text-sm text-[#a1a1aa] hover:text-[#fafafa] mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-bold mb-2">Real Company Intelligence</h1>
        <p className="text-[#a1a1aa] mb-6">Upload an annual report or select a demo profile for AI-powered business analysis.</p>

        {/* Industry Selector + Upload */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-8">
          {industries.map((ind) => (
            <button key={ind.id} onClick={() => setIndustry(ind.id)}
              className={`glass p-4 text-left transition-all hover:border-[#22c55e]/30 ${industry === ind.id ? "border-[#22c55e] bg-[#22c55e]/5" : ""}`}>
              <div className="text-[#a1a1aa] mb-2">{ind.icon}</div>
              <p className="text-sm font-semibold">{ind.label}</p>
              <p className="text-xs text-[#71717a] mt-1">{ind.desc}</p>
            </button>
          ))}

          {/* Upload Zone */}
          <div className={`glass p-4 flex flex-col items-center justify-center gap-2 cursor-pointer transition-all hover:border-[#3b82f6]/30 ${file ? 'border-[#3b82f6]' : ''}`}
            onClick={() => document.getElementById("pdf-input")?.click()}>
            <input id="pdf-input" type="file" accept=".pdf" className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) setFile(f); }} />
            <UploadCloud className="w-5 h-5 text-[#3b82f6]" />
            <p className="text-xs font-semibold text-center">{file ? file.name.slice(0, 20) + "..." : "Upload PDF"}</p>
            {file && (
              <button onClick={(e) => { e.stopPropagation(); handleUpload(); }} disabled={uploading}
                className="text-xs px-3 py-1 rounded-lg bg-[#3b82f6] text-white hover:bg-[#2563eb] disabled:opacity-50 transition-colors">
                {uploading ? "Processing..." : "Analyze"}
              </button>
            )}
          </div>
        </div>

        {/* Loading */}
        {(loading || uploading) && (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="w-8 h-8 animate-spin text-[#22c55e]" />
              <p className="text-[#a1a1aa]">{uploading ? "Extracting financial data..." : "Building company profile..."}</p>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="glass p-4 border border-[#ef4444]/30 mb-6">
            <p className="text-sm text-[#ef4444]">{error}</p>
          </div>
        )}

        {/* Dashboard */}
        {!loading && !uploading && data && <CompanyIntelligence data={data} />}
      </motion.div>
    </main>
  );
}
