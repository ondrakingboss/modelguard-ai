"use client";

import { Download, FileSpreadsheet, FileText } from "lucide-react";

interface Issue {
  id?: string;
  severity: "critical" | "high" | "medium" | "low";
  sheet: string;
  cell: string;
  category: string;
  title: string;
  description: string;
  why_it_matters: string;
  suggested_fix: string;
}

interface AuditResult {
  model_score: number;
  summary: string;
  issues: Issue[];
  severity_breakdown: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

const columns: Array<keyof Issue> = [
  "severity",
  "category",
  "sheet",
  "cell",
  "title",
  "description",
  "why_it_matters",
  "suggested_fix",
];

function csvCell(value: unknown) {
  const text = String(value ?? "");
  return `"${text.replace(/"/g, '""')}"`;
}

function downloadBlob(filename: string, contents: string, type: string) {
  const blob = new Blob([contents], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export default function ExportReport({ result }: { result: AuditResult }) {
  const timestamp = new Date();
  const filenameStamp = timestamp.toISOString().slice(0, 19).replace(/[:T]/g, "-");

  function exportCsv() {
    const header = columns.join(",");
    const rows = result.issues.map((issue) => columns.map((column) => csvCell(issue[column])).join(","));
    downloadBlob(`modelguard-audit-${filenameStamp}.csv`, [header, ...rows].join("\n"), "text/csv;charset=utf-8");
  }

  function exportPdf() {
    const pageWidth = 612;
    const pageHeight = 792;
    const margin = 48;
    const pages: string[][] = [[]];
    let y = pageHeight - 48;
    const criticalRisks = result.issues
      .filter((issue) => issue.severity === "critical")
      .slice(0, 3);

    function escapePdf(text: string) {
      return text
        .replace(/[^\x20-\x7E]/g, " ")
        .replace(/\\/g, "\\\\")
        .replace(/\(/g, "\\(")
        .replace(/\)/g, "\\)");
    }

    function currentPage() {
      return pages[pages.length - 1];
    }

    function addPage() {
      pages.push([]);
      y = pageHeight - 48;
    }

    function text(line: string, x = margin, size = 10, bold = false) {
      currentPage().push(`BT /${bold ? "F2" : "F1"} ${size} Tf ${x} ${y} Td (${escapePdf(line)}) Tj ET`);
      y -= size + 5;
    }

    function rule() {
      currentPage().push(`0.13 0.77 0.37 RG ${margin} ${y} m ${pageWidth - margin} ${y} l S`);
      y -= 18;
    }

    function wrap(value: string, chars = 92) {
      const words = (value || "None provided.").split(/\s+/);
      const lines: string[] = [];
      let line = "";
      words.forEach((word) => {
        const next = line ? `${line} ${word}` : word;
        if (next.length > chars) {
          lines.push(line);
          line = word;
        } else {
          line = next;
        }
      });
      if (line) lines.push(line);
      return lines;
    }

    function paragraph(value: string, chars = 92) {
      wrap(value, chars).forEach((line) => text(line, margin, 10));
      y -= 6;
    }

    function ensure(space = 80) {
      if (y < space) addPage();
    }

    text("ModelGuard AI Audit Report", margin, 22, true);
    text(`Generated ${timestamp.toLocaleString()}`, margin, 9);
    rule();
    text(`Model health score: ${result.model_score}/100`, margin, 18, true);
    text("Finance model risk posture", margin, 10);
    y -= 8;
    text("Executive Summary", margin, 14, true);
    paragraph(result.summary);

    text("Severity Breakdown", margin, 14, true);
    text(`Critical: ${result.severity_breakdown.critical}   High: ${result.severity_breakdown.high}   Medium: ${result.severity_breakdown.medium}   Low: ${result.severity_breakdown.low}`, margin, 11, true);
    y -= 10;

    text("Top 3 Critical Risks", margin, 14, true);
    (criticalRisks.length ? criticalRisks : result.issues.slice(0, 3)).forEach((issue, index) => {
      ensure();
      text(`${index + 1}. ${issue.title}`, margin, 11, true);
      paragraph(`${issue.sheet}!${issue.cell} - ${issue.why_it_matters}`, 88);
    });

    ensure(120);
    text("Full Issue Table", margin, 14, true);
    text("Severity | Category | Sheet | Cell | Issue", margin, 9, true);
    rule();
    result.issues.forEach((issue) => {
      ensure(90);
      text(`${issue.severity.toUpperCase()} | ${issue.category} | ${issue.sheet} | ${issue.cell}`, margin, 9, true);
      wrap(issue.title, 86).forEach((line) => text(line, margin + 12, 9));
      y -= 4;
    });

    const objects: string[] = [];
    const pageIds: number[] = [];
    objects.push("<< /Type /Catalog /Pages 2 0 R >>");
    objects.push("");
    objects.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
    objects.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>");

    pages.forEach((page) => {
      const stream = page.join("\n");
      const contentId = objects.length + 1;
      objects.push(`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
      const pageId = objects.length + 1;
      pageIds.push(pageId);
      objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${pageWidth} ${pageHeight}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents ${contentId} 0 R >>`);
    });

    objects[1] = `<< /Type /Pages /Kids [${pageIds.map((id) => `${id} 0 R`).join(" ")}] /Count ${pageIds.length} >>`;

    let pdf = "%PDF-1.4\n";
    const offsets: number[] = [0];
    objects.forEach((object, index) => {
      offsets.push(pdf.length);
      pdf += `${index + 1} 0 obj\n${object}\nendobj\n`;
    });
    const xref = pdf.length;
    pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
    offsets.slice(1).forEach((offset) => {
      pdf += `${String(offset).padStart(10, "0")} 00000 n \n`;
    });
    pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;

    const blob = new Blob([pdf], { type: "application/pdf" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `modelguard-audit-${filenameStamp}.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="glass p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-sm font-semibold">Export Report</p>
        <p className="text-xs text-[#a1a1aa]">Download a board-ready PDF or raw issue CSV.</p>
      </div>
      <div className="flex gap-2">
        <button
          onClick={exportPdf}
          className="inline-flex items-center gap-2 rounded-lg border border-[#22c55e]/40 bg-[#22c55e]/10 px-4 py-2 text-sm font-semibold text-[#22c55e] hover:bg-[#22c55e]/20 transition-colors"
        >
          <FileText className="h-4 w-4" />
          PDF
          <Download className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={exportCsv}
          className="inline-flex items-center gap-2 rounded-lg border border-[#27272a] bg-[#18181b] px-4 py-2 text-sm font-semibold text-[#fafafa] hover:bg-[#27272a] transition-colors"
        >
          <FileSpreadsheet className="h-4 w-4" />
          CSV
          <Download className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
