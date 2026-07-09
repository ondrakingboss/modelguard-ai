from __future__ import annotations

from copy import deepcopy
from typing import Any


AVAILABLE_SCENARIOS = ("startup", "manufacturing", "saas", "retail", "leveraged")


def _insight(
    category: str,
    confidence: int,
    severity: str,
    title: str,
    finding: str,
    financial_reasoning: str,
    validation_questions: list[str],
    recommended_actions: list[str],
    benchmark_context: str,
) -> dict[str, Any]:
    return {
        "category": category,
        "confidence": confidence,
        "severity": severity,
        "title": title,
        "finding": finding,
        "financial_reasoning": financial_reasoning,
        "validation_questions": validation_questions,
        "recommended_actions": recommended_actions,
        "benchmark_context": benchmark_context,
    }


SCENARIO_ANALYSES: dict[str, dict[str, Any]] = {
    "startup": {
        "business_health_score": 58,
        "forecast_confidence": 52,
        "assumption_risk_score": 78,
        "cash_flow_risk": 84,
        "profitability_outlook": "Caution",
        "revenue_sustainability": "Moderate",
        "balance_sheet_health": "Weak",
        "executive_summary": (
            "The Series B SaaS case shows strong top-line momentum, but the plan relies on sustained enterprise booking acceleration while burn remains elevated. "
            "Revenue quality is improving, yet negative EBITDA and expanding sales capacity create a material funding dependency. "
            "The forecast is credible only if pipeline conversion, churn, and net revenue retention are validated against signed demand. "
            "Management should prioritize runway, cohort economics, and a clear path from growth investment to operating leverage."
        ),
        "insights": [
            _insight(
                "Revenue Analysis",
                76,
                "medium",
                "Growth plan depends on accelerated enterprise conversion",
                "Forecast ARR growth steps above the recent cohort trend because the model assumes larger enterprise deal sizes and faster sales cycle compression after Series B hiring.",
                "The assumption matters because revenue acceleration is funding the path to scale; if enterprise conversion slips, cash burn continues without the planned ARR base to absorb fixed go-to-market costs.",
                ["Which forecast bookings are already covered by signed contracts or late-stage pipeline?", "How do assumed win rates compare with the last four quarters by segment?"],
                ["Tie forecast revenue to pipeline stage, weighted probability, and sales capacity by cohort.", "Add a downside case where sales cycles remain at historical levels and expansion ARR slows."],
                "High-growth SaaS companies can sustain 40%+ ARR growth, but forecasts above 2x historical growth normally require documented pipeline coverage and capacity ramp evidence.",
            ),
            _insight(
                "Margin Analysis",
                73,
                "high",
                "Negative margins improve before operating proof is visible",
                "EBITDA margin remains negative but improves sharply because gross margin expansion and sales productivity gains are assumed before the company has demonstrated repeatable scale efficiency.",
                "This is a key valuation risk because the model assumes burn per dollar of ARR falls quickly; if onboarding, support, or cloud costs scale with customers, the company may miss both margin and runway targets.",
                ["What operational changes support the forecast gross margin improvement?", "Are cloud hosting, implementation, and support costs modeled per customer or as a flat percentage?"],
                ["Rebuild gross margin from usage, support headcount, and implementation effort instead of a single margin percentage.", "Track EBITDA bridge items separating hiring, hosting, support, and discretionary spend."],
                "Efficient SaaS companies often reach 70% to 85% gross margin, but earlier-stage firms with heavy implementation can sit materially below that until delivery processes mature.",
            ),
            _insight(
                "Cost Structure",
                79,
                "high",
                "Hiring plan may understate expansion cost",
                "The plan assumes rapid customer and revenue growth while payroll growth flattens after the initial Series B hiring wave.",
                "Payroll is the largest controllable cost and the forecast may be understating customer success, implementation, product, and security staffing needs; if staffing is too low, churn and delivery quality could deteriorate.",
                ["Which departments are capacity-constrained at the forecast customer count?", "Does the hiring plan include customer success coverage ratios and enterprise security requirements?"],
                ["Model headcount by function using customers, ARR, tickets, and product roadmap milestones.", "Separate one-time hiring catch-up from recurring capacity required to support expansion."],
                "SaaS payroll commonly remains 55% to 75% of operating expense at this stage, and flat payroll during rapid expansion is unusual without proven automation leverage.",
            ),
            _insight(
                "Cash Flow",
                82,
                "critical",
                "Runway remains vulnerable despite strong ARR growth",
                "Operating cash flow stays negative because upfront hiring and customer acquisition spend precede collections, while the forecast assumes no delay in new-logo bookings.",
                "This matters because ARR growth does not pay payroll unless it converts into cash collections; if bookings slip or annual prepay mix declines, the company may need an earlier bridge or down-round financing.",
                ["What is monthly runway under bookings delayed by one quarter?", "What percentage of forecast ARR is billed annually upfront versus monthly?"],
                ["Add a 13-week cash view tied to billings, collections, payroll, and vendor commitments.", "Set financing triggers based on minimum cash balance and pipeline conversion thresholds."],
                "Venture-backed SaaS companies often tolerate burn, but investors generally expect a visible path to 18 to 24 months of runway after a Series B raise.",
            ),
            _insight(
                "Balance Sheet",
                74,
                "medium",
                "Liquidity depends on equity cash rather than operating resilience",
                "The balance sheet has limited debt, but cash coverage deteriorates as deferred revenue growth does not fully offset operating losses.",
                "The assumption causing the risk is that customer prepayments and new equity fund expansion; if collection timing weakens, the company has few balance sheet buffers besides cutting growth spend.",
                ["How much cash is restricted, committed, or reserved for customer deposits?", "Are receivables aging and deferred revenue balances consistent with the billing model?"],
                ["Monitor current ratio, net burn, and months of cash monthly against board-approved thresholds.", "Negotiate annual prepay incentives and vendor payment terms before cash pressure appears."],
                "Early-stage SaaS balance sheets are often cash-heavy post-raise, but current ratios can deteriorate quickly when burn is high and receivables stretch.",
            ),
            _insight(
                "Forecast Quality",
                68,
                "high",
                "Forecast has hockey-stick characteristics",
                "The plan changes slope materially in the second forecast year because sales productivity, churn, and expansion all improve at the same time.",
                "When multiple assumptions improve together, forecast error compounds; if one driver misses, the projected path to cash break-even can move out several quarters.",
                ["Which two or three drivers explain most of the forecast uplift?", "Has management shown sensitivity cases for churn, win rate, and hiring productivity?"],
                ["Build sensitivity tables for ARR, burn, and runway around churn, win rate, and average contract value.", "Require owner-level evidence for each major assumption change from historical actuals."],
                "Institutional SaaS plans usually include driver-based cohorts and sensitivities; a single hockey-stick revenue curve without driver support is below investor-grade FP&A practice.",
            ),
        ],
    },
    "manufacturing": {
        "business_health_score": 72,
        "forecast_confidence": 76,
        "assumption_risk_score": 46,
        "cash_flow_risk": 38,
        "profitability_outlook": "Moderate",
        "revenue_sustainability": "Moderate",
        "balance_sheet_health": "Strong",
        "executive_summary": (
            "The manufacturer presents a stable operating profile with moderate growth and generally dependable cash conversion. "
            "The main pressure point is margin compression from input costs, freight, and labor inflation that may not be fully recoverable through pricing. "
            "Balance sheet risk appears manageable, but working capital needs should be watched as inventory and receivables rise with volume. "
            "The CFO focus should be price realization, procurement coverage, and capital discipline."
        ),
        "insights": [
            _insight(
                "Revenue Analysis",
                82,
                "low",
                "Moderate growth is credible but price-led",
                "Revenue growth is consistent with the historical trend, but a meaningful portion comes from pricing actions rather than unit volume expansion.",
                "This matters because price-led growth can reverse if customers push back or competitors absorb cost inflation; if volume weakens, fixed plant overhead will pressure margins.",
                ["What portion of growth is volume, mix, and price by product family?", "Are customer contracts indexed to raw material costs or renegotiated manually?"],
                ["Build a price-volume-mix bridge for each forecast year.", "Track order intake and backlog conversion by product line against the pricing plan."],
                "Mature manufacturers commonly grow in the low to mid single digits unless they add capacity or win share; pricing-driven growth should be supported by contract terms.",
            ),
            _insight(
                "Margin Analysis",
                78,
                "medium",
                "Input cost inflation is compressing gross margin",
                "Gross margin declines because steel, resin, freight, and labor costs are rising faster than the model's pass-through assumptions.",
                "Margin compression matters because EBITDA depends on plant absorption and procurement discipline; if input costs remain elevated, operating leverage from volume growth may not materialize.",
                ["What percentage of raw material exposure is covered by purchase contracts or hedges?", "How long is the lag between supplier cost increases and customer price recovery?"],
                ["Add commodity and labor sensitivity cases to gross margin.", "Create a monthly price-cost waterfall showing realized recovery versus inflation."],
                "Stable manufacturers often operate with gross margins in the 20% to 35% range; sustained expansion above that usually requires mix shift, automation, or pricing power.",
            ),
            _insight(
                "Cost Structure",
                75,
                "medium",
                "CapEx supports growth but needs return validation",
                "CapEx rises for equipment maintenance and selective capacity expansion, while depreciation lags the spend profile.",
                "This assumption matters because growth requires reliable plant capacity; if CapEx is delayed or under-scoped, service levels could slip, but if returns are weak, free cash flow will be diluted.",
                ["Which CapEx projects are maintenance, compliance, automation, or growth?", "What payback and utilization assumptions support the expansion projects?"],
                ["Separate maintenance CapEx from growth CapEx in the forecast.", "Require post-investment reviews comparing throughput, scrap, and labor savings to plan."],
                "Manufacturing CapEx commonly runs above depreciation during expansion cycles; mature steady-state businesses should show a clear link between CapEx and capacity or efficiency.",
            ),
            _insight(
                "Cash Flow",
                80,
                "low",
                "Cash generation remains solid but working capital is heavier",
                "Operating cash flow tracks earnings, but inventory and receivables consume more cash as management builds safety stock and extends terms to larger customers.",
                "The risk is timing rather than structural profitability; if inventory builds ahead of demand or DSO increases, free cash flow could undershoot despite stable EBITDA.",
                ["Are safety-stock assumptions tied to confirmed demand or supplier lead-time risk?", "Which customers are driving longer receivable terms and are they creditworthy?"],
                ["Monitor cash conversion cycle by month and product family.", "Set inventory days and DSO limits in the forecast covenant package."],
                "Manufacturers with healthy operations often convert a high share of EBITDA to operating cash flow, but working capital swings can absorb cash in growth or inflationary periods.",
            ),
            _insight(
                "Balance Sheet",
                81,
                "low",
                "Leverage and liquidity are manageable",
                "Debt grows modestly to fund equipment, but current ratio and debt service coverage remain within typical lender comfort ranges.",
                "This matters because the business can absorb moderate forecast variance; however, leverage could rise if margin compression and working capital investment occur together.",
                ["What are the covenant thresholds for fixed charge coverage and leverage?", "Are inventory values current under standard costing and reserve policies?"],
                ["Stress test leverage and current ratio under lower gross margin and slower inventory turns.", "Update inventory reserves for obsolete or slow-moving SKUs before lender reporting."],
                "For mature industrial borrowers, lenders often focus on leverage below roughly 3x EBITDA and current ratios above 1.2x, depending on asset quality.",
            ),
            _insight(
                "Forecast Quality",
                77,
                "medium",
                "Forecast is operationally grounded but light on sensitivities",
                "The forecast uses historical growth and cost trends, but it does not fully sensitize commodity costs, volume shortfalls, and working capital timing.",
                "The assumption risk is manageable, but manufacturing earnings can move materially from small changes in price-cost spread; without sensitivity coverage, management may underprepare for downside cases.",
                ["Which variables explain most EBITDA variance in prior forecast misses?", "Does the plan include downside cases for commodities, labor, and volume?"],
                ["Add a sensitivity matrix for price, volume, raw materials, and labor absorption.", "Reconcile forecast drivers to backlog, production capacity, and procurement commitments."],
                "Board-ready manufacturing forecasts usually include price-volume-mix and commodity sensitivity views because small basis-point margin changes can be material.",
            ),
        ],
    },
    "saas": {
        "business_health_score": 76,
        "forecast_confidence": 67,
        "assumption_risk_score": 61,
        "cash_flow_risk": 42,
        "profitability_outlook": "Strong",
        "revenue_sustainability": "Caution",
        "balance_sheet_health": "Moderate",
        "executive_summary": (
            "The mid-stage SaaS profile shows attractive gross margins, improving EBITDA, and efficient scaling. "
            "The core issue is revenue durability: churn and downgrade risk could offset strong new-logo productivity. "
            "The model is directionally sound, but confidence depends on cohort-level retention evidence and realistic expansion assumptions. "
            "Management should defend net revenue retention before increasing growth spend."
        ),
        "insights": [
            _insight(
                "Revenue Analysis",
                70,
                "high",
                "Growth quality is exposed to churn",
                "The forecast assumes continued new-logo growth and expansion revenue, but customer churn remains elevated in smaller accounts.",
                "This matters because headline ARR growth can hide weak retention; if churn persists, sales capacity is spent replacing lost ARR rather than compounding the revenue base.",
                ["What are gross and net revenue retention by customer segment and cohort?", "Are churn assumptions based on contracted renewals or management targets?"],
                ["Forecast ARR using cohort retention, expansion, contraction, and new-logo layers.", "Segment the go-to-market plan toward customers with stronger retention economics."],
                "Healthy mid-stage SaaS companies often target net revenue retention above 110%; elevated SMB churn can pull the business below efficient-growth benchmarks.",
            ),
            _insight(
                "Margin Analysis",
                82,
                "low",
                "Strong margin profile supports scalability",
                "Gross margin and EBITDA margin improve because infrastructure costs scale efficiently and sales productivity is rising.",
                "The assumption is credible if usage costs remain variable and customer success load does not increase; if churn mitigation requires more support, EBITDA improvement could slow.",
                ["Are cloud costs modeled by usage tier and customer size?", "How much customer success investment is required to reduce churn?"],
                ["Maintain a margin bridge separating hosting, support, sales efficiency, and R&D leverage.", "Track gross margin by cohort to identify unprofitable customer segments."],
                "SaaS gross margins above 75% are strong but common for software-led products; EBITDA margin expansion is credible when retention and support burden are stable.",
            ),
            _insight(
                "Cost Structure",
                77,
                "medium",
                "Efficient scaling depends on disciplined sales spend",
                "Sales and marketing expense declines as a percentage of revenue while the forecast still assumes strong customer acquisition.",
                "This is favorable but sensitive: if CAC payback lengthens or win rates fall, the company may either miss growth or reaccelerate spend and lose operating leverage.",
                ["What CAC payback and pipeline conversion assumptions support lower sales intensity?", "Are sales quotas and ramp times consistent with historical rep productivity?"],
                ["Tie sales expense to rep count, ramp, quota attainment, and pipeline generation.", "Set guardrails for growth spend based on CAC payback and logo retention."],
                "Efficient SaaS companies often show CAC payback below 18 months; declining sales intensity without retention strength can be a warning sign.",
            ),
            _insight(
                "Cash Flow",
                74,
                "medium",
                "Cash flow is improving but renewal timing matters",
                "Free cash flow turns positive as EBITDA improves and annual billings are collected upfront.",
                "The risk is that churn, downgrades, or a shift toward monthly billing would weaken collections; EBITDA could look solid while cash conversion softens.",
                ["What percentage of renewals are annual prepaid versus monthly?", "How much forecast cash depends on renewal cohorts with known churn risk?"],
                ["Add billings and cash collection schedules by renewal month.", "Stress test free cash flow under lower renewal rates and shorter billing terms."],
                "SaaS cash flow often benefits from annual prepayments, but billings quality matters more than GAAP revenue when liquidity is tight.",
            ),
            _insight(
                "Balance Sheet",
                71,
                "medium",
                "Deferred revenue is healthy but receivables need monitoring",
                "The balance sheet shows moderate liquidity and meaningful deferred revenue, while receivables grow as enterprise customers negotiate longer terms.",
                "This matters because deferred revenue is a useful funding source only after cash is collected; if DSO rises, reported ARR may not translate into liquidity.",
                ["Are receivables aging concentrated in enterprise customers or disputed invoices?", "Do deferred revenue balances reconcile to contracted annual billings?"],
                ["Monitor DSO, billings, deferred revenue, and collections as a single revenue-quality dashboard.", "Tighten credit review and collections process for extended-payment enterprise deals."],
                "SaaS companies with enterprise exposure can carry higher receivables, but rising DSO should be explained by billing terms rather than collection weakness.",
            ),
            _insight(
                "Forecast Quality",
                69,
                "high",
                "Retention sensitivity is not prominent enough",
                "The forecast includes growth sensitivities but does not put enough weight on churn, contraction, and renewal timing.",
                "The most important assumption is customer durability; if retention misses, revenue, margin, and cash flow all weaken because replacement acquisition cost rises.",
                ["Does the board package show gross retention, net retention, and logo retention sensitivities?", "Which customer cohorts have the largest renewal exposure in the next two quarters?"],
                ["Add churn and downgrade sensitivities to ARR, EBITDA, and cash flow.", "Create an early-warning renewal dashboard using product usage, support tickets, and sponsor changes."],
                "Investor-grade SaaS forecasting typically starts with cohort retention because it determines whether new ARR compounds or merely replaces churned revenue.",
            ),
        ],
    },
    "retail": {
        "business_health_score": 49,
        "forecast_confidence": 55,
        "assumption_risk_score": 70,
        "cash_flow_risk": 73,
        "profitability_outlook": "Weak",
        "revenue_sustainability": "Caution",
        "balance_sheet_health": "Caution",
        "executive_summary": (
            "The retail chain faces thin margins, seasonal cash pressure, and competitive pricing pressure. "
            "The forecast depends on stable same-store sales and inventory turns despite weaker consumer demand and promotional intensity. "
            "Liquidity could tighten around seasonal inventory builds if markdowns rise or sell-through slows. "
            "Management should focus on store-level contribution, inventory discipline, and vendor terms."
        ),
        "insights": [
            _insight(
                "Revenue Analysis",
                66,
                "high",
                "Same-store sales assumptions may be optimistic",
                "The forecast assumes positive same-store sales and modest traffic recovery despite heavy competitive discounting and mixed recent growth.",
                "This matters because retail revenue is highly sensitive to traffic, conversion, and average ticket; if promotions drive sales without margin, revenue growth will not improve profitability.",
                ["What traffic, conversion, and average ticket assumptions drive same-store sales?", "Are forecast sales gains coming from price, units, promotions, or new stores?"],
                ["Build revenue by store cohort using traffic, conversion, basket size, and markdown rate.", "Separate comp-store performance from new-store openings and acquisition effects."],
                "Retailers with mature store bases often grow low single digits on a comp basis; sustained acceleration requires clear traffic drivers or merchandising advantage.",
            ),
            _insight(
                "Margin Analysis",
                64,
                "high",
                "Thin margins leave little room for markdown error",
                "Gross margin assumes improved merchandise mix and controlled discounts while the competitive environment suggests higher promotional pressure.",
                "The assumption matters because a small miss in gross margin can erase operating profit; if inventory must be marked down, EBITDA and cash flow deteriorate together.",
                ["What markdown rate is embedded by category and season?", "How does current sell-through compare with the margin plan?"],
                ["Add gross margin sensitivity for markdowns, shrink, freight, and product mix.", "Review category-level margin and sell-through weekly during peak season."],
                "Retail operating margins are often low single digit; a 100 to 200 basis point margin miss can be material to covenant compliance and liquidity.",
            ),
            _insight(
                "Cost Structure",
                69,
                "medium",
                "Store expense flexibility is limited",
                "The plan assumes store labor and occupancy expense decline as a percentage of sales, but rent and minimum staffing are largely fixed.",
                "This matters because fixed store costs reduce downside flexibility; if sales soften, expense ratios rise quickly and store contribution can turn negative.",
                ["Which stores are below contribution break-even under current traffic?", "Are labor hours flexed by traffic forecasts or held flat for service levels?"],
                ["Model store-level four-wall profitability and closure thresholds.", "Tie labor scheduling to traffic and conversion by location."],
                "Retail fixed occupancy costs can make deleveraging severe when comps decline; strong operators manage labor tightly but cannot flex rent in the short term.",
            ),
            _insight(
                "Cash Flow",
                62,
                "critical",
                "Seasonal inventory build creates liquidity risk",
                "Cash flow turns negative before peak season because inventory purchases rise ahead of sales, and the forecast assumes normal sell-through and vendor terms.",
                "If demand is weaker or markdowns rise, cash is trapped in inventory and the company may need revolver draws or delayed vendor payments.",
                ["How much liquidity is available at the seasonal inventory peak?", "Are vendor terms tightening or dependent on payment history?"],
                ["Build a weekly seasonal cash forecast covering inventory receipts, sell-through, markdowns, and vendor payments.", "Set purchase order limits tied to sales velocity and liquidity headroom."],
                "Inventory-heavy retailers often experience seasonal borrowing peaks; lenders focus closely on borrowing-base availability and inventory eligibility.",
            ),
            _insight(
                "Balance Sheet",
                61,
                "high",
                "Inventory growth is outpacing revenue visibility",
                "Inventory increases faster than forecast revenue, while current ratio remains only modestly above minimum comfort levels.",
                "The assumption causing the risk is that inventory will sell at planned margin; if not, write-downs reduce equity and lower borrowing availability.",
                ["Which categories account for inventory growth and how aged are they?", "Does inventory build reflect confirmed demand or minimum vendor order quantities?"],
                ["Track inventory turns, aged stock, and markdown reserve adequacy by category.", "Stress test current ratio and borrowing base under slower turns and lower recovery values."],
                "Retail inventory turns vary by category, but inventory growth without comp sales support is a common early warning sign for markdown and liquidity pressure.",
            ),
            _insight(
                "Forecast Quality",
                63,
                "high",
                "Forecast needs stronger seasonal and downside cases",
                "The model includes a base seasonal pattern but limited downside sensitivity for traffic, markdowns, inventory turns, and vendor terms.",
                "Retail forecasts can miss quickly when consumer demand shifts; if the model lacks downside cases, management may buy too much inventory or react too late on promotions.",
                ["Does the forecast include weekly seasonality through peak periods?", "What downside case combines lower traffic, higher markdowns, and slower inventory turns?"],
                ["Add weekly seasonal cash and inventory sensitivities.", "Create trigger points for markdown action, order cuts, and revolver usage."],
                "Retail FP&A best practice uses weekly operating drivers during seasonal peaks because monthly models can hide liquidity inflection points.",
            ),
        ],
    },
    "leveraged": {
        "business_health_score": 31,
        "forecast_confidence": 44,
        "assumption_risk_score": 86,
        "cash_flow_risk": 92,
        "profitability_outlook": "Caution",
        "revenue_sustainability": "Weak",
        "balance_sheet_health": "Weak",
        "executive_summary": (
            "The leveraged case shows a stressed capital structure with limited margin for forecast error. "
            "Debt service consumes cash flow, interest coverage is weak, and the plan relies on EBITDA recovery that has not yet been proven. "
            "Liquidity and covenant risk are the primary concerns, with restructuring risk increasing if operating performance misses. "
            "Management should focus immediately on cash preservation, lender communication, and credible downside planning."
        ),
        "insights": [
            _insight(
                "Revenue Analysis",
                58,
                "high",
                "Revenue recovery assumption is not yet supported",
                "The forecast assumes revenue stabilizes and returns to growth after recent declines, but the model does not show enough customer or pricing evidence.",
                "This matters because even modest revenue weakness can push EBITDA below debt service needs; if the recovery is delayed, liquidity and covenant pressure intensify.",
                ["Which customers or contracts support the forecast revenue recovery?", "Are price increases assumed despite customer churn or competitive pressure?"],
                ["Build revenue from contracted backlog, renewal risk, and customer-level retention.", "Prepare a downside case with flat revenue and lower pricing realization."],
                "Highly leveraged businesses generally need conservative revenue cases because lenders and restructuring advisors focus on downside cash capacity, not upside targets.",
            ),
            _insight(
                "Margin Analysis",
                55,
                "critical",
                "EBITDA improvement may be too aggressive for the leverage profile",
                "The plan assumes EBITDA margin expansion from cost reductions and operating leverage while revenue is only modestly recovering.",
                "This is critical because debt capacity depends on EBITDA; if margin improvement misses, leverage ratios rise and interest coverage can fall below sustainable levels.",
                ["Which cost reductions are already executed versus planned?", "Do margin gains rely on revenue growth, headcount cuts, vendor concessions, or accounting adjustments?"],
                ["Create an EBITDA bridge separating realized savings, run-rate savings, and unexecuted initiatives.", "Remove non-recurring add-backs from lender-facing cash coverage analysis."],
                "Leveraged borrowers are commonly evaluated on adjusted EBITDA, but aggressive add-backs receive scrutiny when cash interest coverage is weak.",
            ),
            _insight(
                "Cost Structure",
                60,
                "high",
                "Cost cuts may impair the operating base",
                "The forecast reduces payroll, overhead, and CapEx while expecting service levels and revenue retention to improve.",
                "The assumption matters because underinvestment can create a second-order revenue decline; if cuts damage sales execution or asset reliability, EBITDA gains reverse.",
                ["Which cost cuts affect customer-facing roles, maintenance, or compliance?", "Is CapEx below the maintenance level required to protect revenue?"],
                ["Classify savings as structural, temporary, or risky to revenue continuity.", "Define minimum maintenance CapEx and customer service staffing needed to avoid value erosion."],
                "In distressed situations, cost takeout can support liquidity, but lenders discount savings that are not executed or that threaten the revenue base.",
            ),
            _insight(
                "Cash Flow",
                57,
                "critical",
                "Debt service exceeds reliable cash generation",
                "Free cash flow remains weak because cash interest and amortization absorb most operating cash flow, leaving little room for working capital or CapEx needs.",
                "This is the central risk: if EBITDA or collections miss, the company may breach covenants, draw remaining liquidity, or need lender relief.",
                ["What is minimum liquidity by week after interest, amortization, and vendor payments?", "Are any debt repayments mandatory, springing, or tied to excess cash flow sweeps?"],
                ["Build a 13-week cash flow with debt service, borrowing availability, and covenant dates.", "Open lender discussions around amendments, waivers, refinancing, or restructuring alternatives."],
                "Distressed lenders focus on near-term liquidity and fixed charge coverage; positive EBITDA is insufficient if cash interest and amortization consume the cash.",
            ),
            _insight(
                "Balance Sheet",
                54,
                "critical",
                "Leverage is above sustainable levels",
                "Debt-to-equity and debt-to-EBITDA are elevated, liquidity is thin, and the current ratio is close to or below 1 in downside periods.",
                "The risk is that the balance sheet cannot absorb operational volatility; if asset values or EBITDA decline, refinancing options narrow and restructuring becomes more likely.",
                ["What are secured debt, unsecured debt, maturities, and covenant levels by facility?", "How much borrowing-base availability remains after reserves and eligibility haircuts?"],
                ["Prepare a maturity wall, covenant forecast, and recovery analysis by creditor class.", "Evaluate asset sales, equity cure rights, refinancing, and restructuring paths."],
                "Debt/equity above 5x or current ratio below 1 is a serious warning sign; distressed credits are judged on liquidity runway and collateral coverage.",
            ),
            _insight(
                "Forecast Quality",
                52,
                "critical",
                "Forecast lacks restructuring-grade downside support",
                "The forecast relies on simultaneous revenue stabilization, margin recovery, working capital improvement, and lender flexibility.",
                "When a leveraged company needs several favorable outcomes at once, forecast confidence should be low; if one driver fails, the liquidity plan can break quickly.",
                ["Does the forecast include downside, severe downside, and liquidation-sensitive cases?", "Are covenant calculations independently reconciled to credit agreement definitions?"],
                ["Develop lender-ready downside cases with weekly liquidity, covenant headroom, and restructuring triggers.", "Reconcile all EBITDA add-backs and debt definitions to the legal credit documents."],
                "Restructuring-grade forecasts require granular cash timing, legal covenant definitions, and downside cases; annual P&L forecasts are not enough for a stressed borrower.",
            ),
        ],
    },
}


def get_available_scenarios() -> list[str]:
    return list(AVAILABLE_SCENARIOS)


def analyze_scenario(scenario_name: str) -> dict[str, Any]:
    normalized = scenario_name.strip().lower()
    if normalized not in SCENARIO_ANALYSES:
        available = ", ".join(AVAILABLE_SCENARIOS)
        raise ValueError(f"Unknown scenario '{scenario_name}'. Available scenarios: {available}.")

    return deepcopy(SCENARIO_ANALYSES[normalized])


if __name__ == "__main__":
    for scenario in ["startup", "manufacturing", "saas", "retail", "leveraged"]:
        result = analyze_scenario(scenario)
        print(f"{scenario}: health={result['business_health_score']}, insights={len(result['insights'])}")
