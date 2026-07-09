import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface Issue {
  id: string;
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

function scoreColor(score: number) {
  if (score >= 80) return "#22c55e";
  if (score >= 60) return "#f59e0b";
  if (score >= 40) return "#f97316";
  return "#ef4444";
}

export default function AuditScore({ result }: { result: AuditResult }) {
  const color = scoreColor(result.model_score);
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (result.model_score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-4 py-8">
      <div className="relative w-48 h-48">
        <svg className="score-ring w-full h-full -rotate-90" viewBox="0 0 180 180">
          <circle cx="90" cy="90" r={radius} fill="none" stroke="rgba(39,39,42,0.5)" strokeWidth="8" />
          <circle cx="90" cy="90" r={radius} fill="none" stroke={color} strokeWidth="8"
            strokeDasharray={circumference} strokeDashoffset={offset}
            strokeLinecap="round" style={{ transition: "stroke-dashoffset 1s ease" }} />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold" style={{ color }}>{result.model_score}</span>
          <span className="text-sm text-[#a1a1aa]">/ 100</span>
        </div>
      </div>
      <p className="text-[#a1a1aa] text-sm max-w-md text-center">{result.summary}</p>
    </div>
  );
}

function SeverityCard({ label, count, color, icon }: { label: string; count: number; color: string; icon: string }) {
  return (
    <Card className="glass p-4 flex items-center gap-3">
      <span className="text-xl">{icon}</span>
      <div>
        <p className="text-xs text-[#a1a1aa] uppercase tracking-wider">{label}</p>
        <p className="text-2xl font-bold" style={{ color }}>{count}</p>
      </div>
    </Card>
  );
}

export function SeverityGrid({ breakdown }: { breakdown: AuditResult["severity_breakdown"] }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
      <SeverityCard label="Critical" count={breakdown.critical} color="#ef4444" icon="🔴" />
      <SeverityCard label="High" count={breakdown.high} color="#f97316" icon="🟠" />
      <SeverityCard label="Medium" count={breakdown.medium} color="#f59e0b" icon="🟡" />
      <SeverityCard label="Low" count={breakdown.low} color="#22c55e" icon="🟢" />
    </div>
  );
}

function severityBadge(s: Issue["severity"]) {
  const map: Record<string, string> = {
    critical: "badge-critical",
    high: "badge-high",
    medium: "badge-medium",
    low: "badge-low",
  };
  return <Badge className={cn(map[s] || "badge-low", "capitalize")}>{s}</Badge>;
}

export function IssueRow({ issue, onClick }: { issue: Issue; onClick: () => void }) {
  return (
    <tr className="border-b border-[#27272a] hover:bg-[#18181b] cursor-pointer transition-colors" onClick={onClick}>
      <td className="p-3">{severityBadge(issue.severity)}</td>
      <td className="p-3 text-sm text-[#a1a1aa]">{issue.category}</td>
      <td className="p-3 text-sm">{issue.sheet}</td>
      <td className="p-3 text-sm font-mono text-[#22c55e]">{issue.cell}</td>
      <td className="p-3 text-sm max-w-md truncate">{issue.title}</td>
    </tr>
  );
}

export function IssueTable({ issues, onSelect }: { issues: Issue[]; onSelect: (i: Issue) => void }) {
  return (
    <Card className="glass overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#27272a] text-left">
              <th className="p-3 text-xs text-[#71717a] uppercase tracking-wider">Severity</th>
              <th className="p-3 text-xs text-[#71717a] uppercase tracking-wider">Category</th>
              <th className="p-3 text-xs text-[#71717a] uppercase tracking-wider">Sheet</th>
              <th className="p-3 text-xs text-[#71717a] uppercase tracking-wider">Cell</th>
              <th className="p-3 text-xs text-[#71717a] uppercase tracking-wider">Issue</th>
            </tr>
          </thead>
          <tbody>
            {issues.map((issue) => (
              <IssueRow key={issue.id} issue={issue} onClick={() => onSelect(issue)} />
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export function IssueModal({ issue, open, onClose }: { issue: Issue | null; open: boolean; onClose: () => void }) {
  if (!issue) return null;
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="glass !bg-[#18181b] border-[#27272a] text-[#fafafa] max-w-lg">
        <DialogHeader>
          <div className="flex items-center gap-2 mb-2">
            {severityBadge(issue.severity)}
            <span className="text-xs text-[#71717a]">{issue.category}</span>
          </div>
          <DialogTitle className="text-lg">{issue.title}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 mt-4">
          <div className="flex gap-4 text-sm">
            <span className="text-[#71717a]">Sheet:</span>
            <span>{issue.sheet}</span>
            <span className="text-[#71717a]">Cell:</span>
            <span className="font-mono text-[#22c55e]">{issue.cell}</span>
          </div>
          <div>
            <p className="text-sm text-[#a1a1aa]">{issue.description}</p>
          </div>
          <div className="glass p-4">
            <p className="text-xs text-[#71717a] uppercase tracking-wider mb-1">Why It Matters</p>
            <p className="text-sm">{issue.why_it_matters}</p>
          </div>
          <div className="glass p-4 border border-[#22c55e]/20">
            <p className="text-xs text-[#22c55e] uppercase tracking-wider mb-1">Suggested Fix</p>
            <p className="text-sm">{issue.suggested_fix}</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function SummaryCard({ summary }: { summary: string }) {
  return (
    <Card className="glass p-6">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">🤖</span>
        <h3 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wider">AI Executive Summary</h3>
      </div>
      <p className="text-sm leading-relaxed">{summary}</p>
    </Card>
  );
}

export { AuditScore };
