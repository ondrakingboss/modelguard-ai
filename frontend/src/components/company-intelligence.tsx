"use client";

import { Card } from "@/components/ui/card";
import { motion } from "framer-motion";
import {
  Building2, Globe, AlertTriangle, Landmark, TrendingUp,
  PiggyBank, FileText, MapPin, Shield, Activity
} from "lucide-react";

interface RevenueSegment { name: string; revenue: string; growth: string; page_ref: string; }
interface GeoExposure { region: string; revenue_pct: string; page_ref: string; }
interface MajorRisk { risk: string; category: string; page_ref: string; }
interface DebtStructure { total_debt: string; maturity_profile: string; covenants: string; page_ref: string; }
interface CapitalAllocation { capex: string; buybacks: string; dividends: string; m_and_a: string; page_ref: string; }
interface ProfitabilityTrends { gross_margin: string; operating_margin: string; net_margin: string; page_ref: string; }
interface CashGeneration { operating_cf: string; free_cf: string; fcf_conversion: string; page_ref: string; }

interface BusinessProfile {
  revenue_segments: RevenueSegment[];
  geographic_exposure: GeoExposure[];
  major_risks: MajorRisk[];
  debt_structure: DebtStructure;
  capital_allocation: CapitalAllocation;
  profitability_trends: ProfitabilityTrends;
  cash_generation: CashGeneration;
  missing_information: string[];
}

interface Insight {
  category: string;
  title: string;
  finding: string;
  page_reference: string;
  financial_implication: string;
  recommended_action: string;
  confidence: number;
}

interface CompanyIntelligence {
  company_name: string;
  industry: string;
  filing_type: string;
  filing_period: string;
  business_profile: BusinessProfile;
  insights: Insight[];
  executive_summary: string;
}

function SectionHeader({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <div className="text-[#22c55e]">{icon}</div>
      <h3 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wider">{title}</h3>
    </div>
  );
}

function PageRef({ pageRef }: { pageRef: string }) {
  return <span className="text-xs text-[#71717a] italic ml-2">({pageRef})</span>;
}

export function BusinessProfileDashboard({ profile }: { profile: BusinessProfile }) {
  return (
    <div className="space-y-6">
      {/* Revenue Segments */}
      <Card className="glass p-5">
        <SectionHeader icon={<Building2 className="w-4 h-4" />} title="Revenue Segments" />
        <div className="space-y-2">
          {profile.revenue_segments.map((seg, i) => (
            <div key={i} className="flex items-center justify-between py-2 border-b border-[#27272a] last:border-0">
              <span className="text-sm">{seg.name}<PageRef pageRef={seg.page_ref} /></span>
              <div className="text-right">
                <span className="text-sm font-semibold">{seg.revenue}</span>
                {seg.growth && <span className={`text-xs ml-2 ${seg.growth.startsWith('-') ? 'text-[#ef4444]' : 'text-[#22c55e]'}`}>{seg.growth}</span>}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Geographic Exposure */}
      <Card className="glass p-5">
        <SectionHeader icon={<Globe className="w-4 h-4" />} title="Geographic Exposure" />
        <div className="grid grid-cols-2 gap-2">
          {profile.geographic_exposure.map((geo, i) => (
            <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-[#09090b]/50">
              <div className="flex items-center gap-2">
                <MapPin className="w-3 h-3 text-[#a1a1aa]" />
                <span className="text-sm">{geo.region}</span>
              </div>
              <span className="text-sm font-semibold">{geo.revenue_pct}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* Major Risks */}
      <Card className="glass p-5">
        <SectionHeader icon={<AlertTriangle className="w-4 h-4" />} title="Major Risks" />
        <div className="space-y-2">
          {profile.major_risks.map((risk, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-[#09090b]/50">
              <Shield className="w-4 h-4 mt-0.5 text-[#f59e0b]" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold">{risk.risk}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-[#f59e0b]/10 text-[#f59e0b]">{risk.category}</span>
                </div>
                <PageRef pageRef={risk.page_ref} />
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Financial Structure Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="glass p-5">
          <SectionHeader icon={<Landmark className="w-4 h-4" />} title="Debt Structure" />
          <div className="space-y-2 text-sm">
            <p><span className="text-[#71717a]">Total Debt:</span> {profile.debt_structure.total_debt}</p>
            <p><span className="text-[#71717a]">Maturity:</span> {profile.debt_structure.maturity_profile}</p>
            <p><span className="text-[#71717a]">Covenants:</span> {profile.debt_structure.covenants}</p>
            <PageRef pageRef={profile.debt_structure.page_ref} />
          </div>
        </Card>

        <Card className="glass p-5">
          <SectionHeader icon={<PiggyBank className="w-4 h-4" />} title="Capital Allocation" />
          <div className="space-y-2 text-sm">
            <p><span className="text-[#71717a]">CapEx:</span> {profile.capital_allocation.capex}</p>
            <p><span className="text-[#71717a]">Buybacks:</span> {profile.capital_allocation.buybacks}</p>
            <p><span className="text-[#71717a]">Dividends:</span> {profile.capital_allocation.dividends}</p>
            <p><span className="text-[#71717a]">M&A:</span> {profile.capital_allocation.m_and_a}</p>
            <PageRef pageRef={profile.capital_allocation.page_ref} />
          </div>
        </Card>

        <Card className="glass p-5">
          <SectionHeader icon={<TrendingUp className="w-4 h-4" />} title="Profitability" />
          <div className="space-y-2 text-sm">
            <p><span className="text-[#71717a]">Gross Margin:</span> {profile.profitability_trends.gross_margin}</p>
            <p><span className="text-[#71717a]">Op Margin:</span> {profile.profitability_trends.operating_margin}</p>
            <p><span className="text-[#71717a]">Net Margin:</span> {profile.profitability_trends.net_margin}</p>
            <PageRef pageRef={profile.profitability_trends.page_ref} />
          </div>
        </Card>

        <Card className="glass p-5">
          <SectionHeader icon={<Activity className="w-4 h-4" />} title="Cash Generation" />
          <div className="space-y-2 text-sm">
            <p><span className="text-[#71717a]">Operating CF:</span> {profile.cash_generation.operating_cf}</p>
            <p><span className="text-[#71717a]">Free CF:</span> {profile.cash_generation.free_cf}</p>
            <p><span className="text-[#71717a]">FCF Conversion:</span> {profile.cash_generation.fcf_conversion}</p>
            <PageRef pageRef={profile.cash_generation.page_ref} />
          </div>
        </Card>
      </div>

      {/* Missing Information */}
      {profile.missing_information.length > 0 && (
        <Card className="glass p-5 border border-[#f59e0b]/30">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-4 h-4 text-[#f59e0b]" />
            <h3 className="text-sm font-semibold text-[#f59e0b] uppercase tracking-wider">Not Found in Document</h3>
          </div>
          <ul className="space-y-1">
            {profile.missing_information.map((item, i) => (
              <li key={i} className="text-sm text-[#a1a1aa] flex items-center gap-2">
                <span className="text-[#f59e0b]">—</span> {item}
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}

export function InsightCards({ insights }: { insights: Insight[] }) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wider">Analyst Insights</h3>
      {insights.map((insight, i) => (
        <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.1 }}
          className="glass p-5 hover:border-[#22c55e]/20 transition-colors">
          <div className="flex items-start justify-between mb-3">
            <div>
              <span className="text-xs text-[#22c55e] uppercase tracking-wider">{insight.category}</span>
              <h4 className="font-semibold mt-1">{insight.title}</h4>
            </div>
            <span className="text-xs text-[#71717a] bg-[#27272a] px-2 py-1 rounded">{insight.confidence}% confidence</span>
          </div>
          <p className="text-sm text-[#a1a1aa] mb-3">{insight.finding}</p>
          <p className="text-xs text-[#71717a] italic mb-2">{insight.page_reference}</p>

          <div className="glass p-3 mb-2">
            <p className="text-xs text-[#71717a] uppercase tracking-wider mb-1">Financial Implication</p>
            <p className="text-sm">{insight.financial_implication}</p>
          </div>
          <div className="glass p-3 border border-[#22c55e]/20">
            <p className="text-xs text-[#22c55e] uppercase tracking-wider mb-1">Recommended Action</p>
            <p className="text-sm">{insight.recommended_action}</p>
          </div>
        </motion.div>
      ))}
    </div>
  );
}

export default function CompanyIntelligence({ data }: { data: CompanyIntelligence }) {
  if (!data) return null;

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="h-10 w-1 rounded-full bg-[#22c55e]" />
        <div>
          <h1 className="text-2xl font-bold">{data.company_name}</h1>
          <div className="flex items-center gap-3 text-sm text-[#a1a1aa]">
            <span>{data.industry}</span>
            <span>·</span>
            <span>{data.filing_type}</span>
            <span>·</span>
            <span>{data.filing_period}</span>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      <Card className="glass p-6 border-l-4 border-[#22c55e]">
        <div className="flex items-center gap-2 mb-3">
          <FileText className="w-4 h-4 text-[#22c55e]" />
          <h3 className="text-sm font-semibold text-[#a1a1aa] uppercase tracking-wider">Executive Summary</h3>
        </div>
        <p className="text-sm leading-relaxed">{data.executive_summary}</p>
      </Card>

      {/* Business Profile */}
      <BusinessProfileDashboard profile={data.business_profile} />

      {/* Insights */}
      <InsightCards insights={data.insights} />
    </motion.div>
  );
}
