"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { AlertTriangle, ArrowLeft, CheckCircle2, FileSpreadsheet, Loader2, UploadCloud, X } from "lucide-react";
import Link from "next/link";

const progressSteps = [
  "File selected",
  "Uploading workbook",
  "Parsing sheets and formulas",
  "Running audit engine",
  "Report ready",
];

type UploadError = "wrong-type" | "failed-backend" | "corrupted-file" | "empty-workbook" | "backend-unavailable";

const errorCopy: Record<UploadError, { title: string; detail: string }> = {
  "wrong-type": {
    title: "Wrong file type",
    detail: "Upload a valid .xlsx workbook. Legacy .xls, CSV, and PDF files are not supported for this audit.",
  },
  "failed-backend": {
    title: "Audit service failed",
    detail: "The backend could not complete the audit. Confirm localhost:8000 is running and try again.",
  },
  "corrupted-file": {
    title: "Corrupted workbook",
    detail: "The workbook could not be opened or parsed. Re-save it from Excel and upload the new copy.",
  },
  "empty-workbook": {
    title: "Empty workbook",
    detail: "The uploaded workbook does not appear to contain auditable sheets, cells, or formulas.",
  },
  "backend-unavailable": {
    title: "Backend unavailable",
    detail: "Cannot reach the audit service at localhost:8000. Start the backend and try again.",
  },
};

function classifyError(message: string): UploadError {
  const lower = message.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("network") || lower.includes("econnrefused") || lower.includes("unreachable")) {
    return "backend-unavailable";
  }
  if (lower.includes("corrupt") || lower.includes("invalid") || lower.includes("zip") || lower.includes("parse")) {
    return "corrupted-file";
  }
  if (lower.includes("empty") || lower.includes("no sheet") || lower.includes("no workbook") || lower.includes("no data")) {
    return "empty-workbook";
  }
  return "failed-backend";
}

function isXlsx(file: File) {
  return file.name.toLowerCase().endsWith(".xlsx");
}

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState<UploadError | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!loading) return;
    setActiveStep(0);
    const interval = window.setInterval(() => {
      setActiveStep((step) => Math.min(step + 1, progressSteps.length - 1));
    }, 850);
    return () => window.clearInterval(interval);
  }, [loading]);

  function selectFile(nextFile: File) {
    if (!isXlsx(nextFile)) {
      setFile(null);
      setError("wrong-type");
      return;
    }
    if (nextFile.size === 0) {
      setFile(nextFile);
      setError("empty-workbook");
      return;
    }
    setFile(nextFile);
    setError(null);
  }

  async function handleUpload() {
    if (!file || error === "wrong-type" || error === "empty-workbook") return;
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(body || `Upload failed: ${res.statusText}`);
      }
      const data = await res.json();
      sessionStorage.setItem("auditResult", JSON.stringify(data));
      sessionStorage.setItem("auditFilename", file.name);
      setActiveStep(progressSteps.length - 1);
      router.push("/results");
    } catch (e: unknown) {
      const message = e instanceof Error ? e.message : "Upload failed";
      setError(classifyError(message));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen max-w-3xl mx-auto px-6 py-12">
      <Link href="/" className="inline-flex items-center gap-2 text-sm text-[#a1a1aa] hover:text-[#fafafa] mb-8 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back
      </Link>

      <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.35 }}>
        <h1 className="text-3xl font-bold mb-2">Upload Your Model</h1>
        <p className="text-[#a1a1aa] mb-8">Upload an .xlsx file to audit for errors, risks, and suspicious patterns.</p>

        <motion.div
          role="button"
          tabIndex={0}
          onClick={() => !loading && inputRef.current?.click()}
          onKeyDown={(event) => {
            if ((event.key === "Enter" || event.key === " ") && !loading) inputRef.current?.click();
          }}
          onDragOver={(event) => {
            event.preventDefault();
            if (!loading) setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragOver(false);
            const dropped = event.dataTransfer.files[0];
            if (dropped && !loading) selectFile(dropped);
          }}
          animate={{
            borderColor: dragOver ? "rgba(34,197,94,0.9)" : "rgba(39,39,42,0.55)",
            boxShadow: dragOver ? "0 0 40px rgba(34,197,94,0.16)" : "0 0 0 rgba(34,197,94,0)",
            scale: dragOver ? 1.01 : 1,
          }}
          className="glass relative overflow-hidden border p-10 text-center cursor-pointer transition-colors"
        >
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx"
            className="hidden"
            disabled={loading}
            onChange={(event) => {
              const selected = event.target.files?.[0];
              if (selected) selectFile(selected);
            }}
          />

          <motion.div
            animate={{ y: dragOver ? -6 : 0, rotate: dragOver ? -4 : 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 16 }}
            className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#22c55e]/10 text-[#22c55e]"
          >
            <UploadCloud className="h-8 w-8" />
          </motion.div>

          {file ? (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="mx-auto flex max-w-xl items-center justify-between gap-4 rounded-xl border border-[#27272a] bg-[#09090b]/70 p-4 text-left">
              <div className="flex min-w-0 items-center gap-3">
                <FileSpreadsheet className="h-9 w-9 flex-none text-[#22c55e]" />
                <div className="min-w-0">
                  <p className="truncate font-semibold">{file.name}</p>
                  <p className="text-sm text-[#a1a1aa]">{(file.size / 1024).toFixed(1)} KB selected</p>
                </div>
              </div>
              <button
                type="button"
                disabled={loading}
                onClick={(event) => {
                  event.stopPropagation();
                  setFile(null);
                  setError(null);
                }}
                className="rounded-lg p-2 text-[#71717a] hover:bg-[#27272a] hover:text-[#fafafa] disabled:opacity-40"
              >
                <X className="h-4 w-4" />
              </button>
            </motion.div>
          ) : (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <p className="text-lg font-semibold mb-1">{dragOver ? "Release to inspect workbook" : "Drop your Excel model here"}</p>
              <p className="text-sm text-[#a1a1aa]">or click to browse — .xlsx files only</p>
            </motion.div>
          )}

          {/* Accepted file type badge */}
          {!file && !loading && (
            <div className="mt-3 flex items-center justify-center gap-2">
              <span className="text-[0.65rem] uppercase tracking-wider text-[#71717a] bg-[#ffffff06] border border-[#27272a] rounded px-2 py-0.5">
                .xlsx only
              </span>
              <span className="text-[0.65rem] text-[#71717a]">Max size: 10 MB</span>
            </div>
          )}
        </motion.div>

        {/* Privacy notice */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}
          className="mt-6 rounded-xl border border-[#27272a] bg-[#ffffff03] p-4">
          <p className="text-xs font-semibold text-[#a1a1aa] mb-2">Data Safety</p>
          <ul className="space-y-1.5 text-xs text-[#71717a]">
            <li>• Files are processed only to generate the audit report.</li>
            <li>• Uploaded workbooks are not used for model training.</li>
            <li>• Avoid uploading confidential client files to the public demo.</li>
            <li>• For production use, private deployment and retention controls would be required.</li>
          </ul>
        </motion.div>

        {/* Session storage notice */}
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}
          className="mt-4 text-center">
          <p className="text-xs text-[#71717a]">
            Results are stored temporarily in this browser tab only.
            Refreshing the results page clears the displayed audit.
          </p>
        </motion.div>

        {file && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="mt-6">
            <button
              onClick={handleUpload}
              disabled={loading || !!error}
              className="w-full rounded-xl bg-[#22c55e] px-6 py-3 font-semibold text-[#022c22] transition-colors hover:bg-[#16a34a] disabled:cursor-not-allowed disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {loading ? "Auditing workbook..." : "Run Audit"}
            </button>
          </motion.div>
        )}

        {loading && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="glass mt-6 p-5">
            <div className="space-y-4">
              {progressSteps.map((step, index) => {
                const done = index < activeStep;
                const active = index === activeStep;
                return (
                  <div key={step} className="flex items-center gap-3">
                    <motion.div
                      animate={{ scale: active ? [1, 1.14, 1] : 1 }}
                      transition={{ repeat: active ? Infinity : 0, duration: 1.1 }}
                      className={`flex h-8 w-8 items-center justify-center rounded-full border ${done ? "border-[#22c55e] bg-[#22c55e] text-[#022c22]" : active ? "border-[#22c55e] text-[#22c55e]" : "border-[#27272a] text-[#71717a]"}`}
                    >
                      {done ? <CheckCircle2 className="h-4 w-4" /> : index + 1}
                    </motion.div>
                    <div className="flex-1">
                      <p className={active || done ? "text-sm font-semibold text-[#fafafa]" : "text-sm text-[#71717a]"}>{step}</p>
                      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-[#27272a]">
                        <motion.div
                          initial={false}
                          animate={{ width: done ? "100%" : active ? "72%" : "0%" }}
                          className="h-full rounded-full bg-[#22c55e]"
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </motion.div>
        )}

        {error && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-5 rounded-xl border border-[#ef4444]/35 bg-[#ef4444]/10 p-4">
            <div className="flex gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 flex-none text-[#ef4444]" />
              <div>
                <p className="font-semibold text-[#fecaca]">{errorCopy[error].title}</p>
                <p className="mt-1 text-sm text-[#fca5a5]">{errorCopy[error].detail}</p>
              </div>
            </div>
          </motion.div>
        )}
      </motion.div>
    </main>
  );
}
