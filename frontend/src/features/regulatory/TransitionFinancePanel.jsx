/**
 * Transition Finance Eligibility Engine
 * Frameworks: EU Taxonomy (2020/852 + Delegated Acts 2021/2139 & 2023/2486),
 *             ICMA Green Bond Principles 2021 (GBP),
 *             ICMA Sustainability-Linked Bond Principles 2023 (SLBP),
 *             Climate Bonds Initiative Climate Bonds Standard v4 (CBI CBS),
 *             MAS Singapore Green Finance Taxonomy v2.0 (SGT),
 *             ASEAN Green Finance Framework 2021 (ASEAN GFF),
 *             EU Social Taxonomy (draft — KPI set B, C)
 *
 * Pure client-side eligibility rules engine — no backend route required.
 */
import React, { useState, useCallback } from "react";
import { CheckCircle, XCircle, AlertTriangle, Info, Zap, RefreshCw } from "lucide-react";

// ── Activity taxonomy (NACE-mapped) ──────────────────────────────────────────
const ACTIVITIES = {
  "Solar PV Generation": {
    nace: "D35.11", sector: "Energy",
    eu_taxonomy: { obj: "CCM", article: "9", dnsh: true, criteria: ["≥55% LCOE reduction vs EU grid mix", "No hazardous waste from manufacturing"], eligible: true },
    icma_gbp: { eligible: true, category: "Renewable Energy", typical_pct: 100 },
    cbi_cbs: { eligible: true, sector: "Energy", criteria_note: "Ground-mounted solar must not use high carbon land" },
    mas_sgt: { eligible: true, tier: "Green", category: "Renewable Energy" },
    asean_gff: { eligible: true, category: "Renewable Energy" },
    transition: false,
  },
  "Onshore Wind": {
    nace: "D35.11", sector: "Energy",
    eu_taxonomy: { obj: "CCM", article: "9", dnsh: true, criteria: ["<0.05 tCO₂e/MWh lifecycle GHG"], eligible: true },
    icma_gbp: { eligible: true, category: "Renewable Energy", typical_pct: 100 },
    cbi_cbs: { eligible: true, sector: "Energy", criteria_note: "No grid intensity requirement in CBSv4" },
    mas_sgt: { eligible: true, tier: "Green", category: "Renewable Energy" },
    asean_gff: { eligible: true, category: "Renewable Energy" },
    transition: false,
  },
  "Offshore Wind": {
    nace: "D35.11", sector: "Energy",
    eu_taxonomy: { obj: "CCM", article: "9", dnsh: true, criteria: ["<0.05 tCO₂e/MWh lifecycle GHG", "Biodiversity impact assessment"], eligible: true },
    icma_gbp: { eligible: true, category: "Renewable Energy", typical_pct: 100 },
    cbi_cbs: { eligible: true, sector: "Energy", criteria_note: "Marine biodiversity DNSH assessment required" },
    mas_sgt: { eligible: true, tier: "Green", category: "Renewable Energy" },
    asean_gff: { eligible: true, category: "Renewable Energy" },
    transition: false,
  },
  "Green Hydrogen (Electrolysis)": {
    nace: "C20.11", sector: "Industry",
    eu_taxonomy: { obj: "CCM", article: "9", dnsh: true, criteria: ["<3 tCO₂e/tH₂ (delegated act threshold)", "Renewable electricity sourced"], eligible: true },
    icma_gbp: { eligible: true, category: "Clean Transportation / Energy", typical_pct: 100 },
    cbi_cbs: { eligible: true, sector: "Industry", criteria_note: "Must demonstrate renewable electricity input" },
    mas_sgt: { eligible: true, tier: "Green", category: "Low Carbon Technologies" },
    asean_gff: { eligible: true, category: "Low Carbon Technologies" },
    transition: false,
  },
  "Natural Gas Power Plant": {
    nace: "D35.11", sector: "Energy",
    eu_taxonomy: { obj: "CCM", article: "9.5", dnsh: false, criteria: ["<270 gCO₂e/kWh annualised or <550 kgCO₂e/kW over 20 yrs", "Transition activity — time-limited"], eligible: true },
    icma_gbp: { eligible: false, category: "Not eligible for green label", typical_pct: 0 },
    cbi_cbs: { eligible: false, sector: "Energy", criteria_note: "CBI CBS v4 excludes fossil gas from eligible sector" },
    mas_sgt: { eligible: true, tier: "Transition", category: "Transition Activity" },
    asean_gff: { eligible: false, category: "Not eligible" },
    transition: true,
  },
  "Coal Power Plant (Retrofit/Efficiency)": {
    nace: "D35.11", sector: "Energy",
    eu_taxonomy: { obj: null, eligible: false, criteria: ["Coal is explicitly excluded from EU Taxonomy CCM"] },
    icma_gbp: { eligible: false, category: "Excluded", typical_pct: 0 },
    cbi_cbs: { eligible: false, sector: "Energy", criteria_note: "Coal explicitly excluded from CBI CBS" },
    mas_sgt: { eligible: false, tier: null, category: "Excluded" },
    asean_gff: { eligible: false, category: "Excluded" },
    transition: false,
  },
  "Electric Vehicle Manufacturing": {
    nace: "C29.10", sector: "Industry",
    eu_taxonomy: { obj: "CCM", article: "3.40", dnsh: true, criteria: ["Zero direct emission vehicles only", "Battery lifecycle footprint <65 tCO₂e (2026 threshold)"], eligible: true },
    icma_gbp: { eligible: true, category: "Clean Transportation", typical_pct: 100 },
    cbi_cbs: { eligible: true, sector: "Transport", criteria_note: "Battery GHG threshold must be met" },
    mas_sgt: { eligible: true, tier: "Green", category: "Sustainable Transport" },
    asean_gff: { eligible: true, category: "Clean Transport" },
    transition: false,
  },
  "Rail Infrastructure (New/Upgrade)": {
    nace: "F42.12", sector: "Transport",
    eu_taxonomy: { obj: "CCM", article: "6.15", dnsh: true, criteria: ["Dedicated high-speed or urban rail", "Modal shift from road/air"], eligible: true },
    icma_gbp: { eligible: true, category: "Clean Transportation", typical_pct: 100 },
    cbi_cbs: { eligible: true, sector: "Transport", criteria_note: "Climate-resilience assessment for physical risk" },
    mas_sgt: { eligible: true, tier: "Green", category: "Sustainable Transport" },
    asean_gff: { eligible: true, category: "Clean Transport" },
    transition: false,
  },
  "Green Building (New — NZEB)": {
    nace: "F41.10", sector: "Real Estate",
    eu_taxonomy: { obj: "CCM", article: "7.1", dnsh: true, criteria: ["Top 15% local energy performance (NZEB)", "EPC class A or B", "No coal/oil heating"], eligible: true },
    icma_gbp: { eligible: true, category: "Green Buildings", typical_pct: 100 },
    cbi_cbs: { eligible: true, sector: "Buildings", criteria_note: "Top 15% or net zero energy standard required" },
    mas_sgt: { eligible: true, tier: "Green", category: "Green Buildings" },
    asean_gff: { eligible: true, category: "Green Buildings" },
    transition: false,
  },
  "Building Renovation (Energy Efficiency)": {
    nace: "F41.20", sector: "Real Estate",
    eu_taxonomy: { obj: "CCM", article: "7.2", dnsh: true, criteria: ["≥30% primary energy reduction post-renovation", "EPC improvement of ≥2 classes"], eligible: true },
    icma_gbp: { eligible: true, category: "Energy Efficiency", typical_pct: 100 },
    cbi_cbs: { eligible: true, sector: "Buildings", criteria_note: "30% improvement threshold or near-zero threshold" },
    mas_sgt: { eligible: true, tier: "Green", category: "Energy Efficiency" },
    asean_gff: { eligible: true, category: "Energy Efficiency" },
    transition: false,
  },
  "Steel Production (EAF — Green)": {
    nace: "C24.10", sector: "Industry",
    eu_taxonomy: { obj: "CCM", article: "3.4", dnsh: true, criteria: ["<0.5 tCO₂/tSteel (2026 threshold)", "Powered by renewable electricity"], eligible: true },
    icma_gbp: { eligible: true, category: "Eco-efficient / Circular Economy", typical_pct: 80 },
    cbi_cbs: { eligible: true, sector: "Industry", criteria_note: "Must use green steel benchmark <0.5 tCO₂/t" },
    mas_sgt: { eligible: true, tier: "Transition", category: "Industrial Transition" },
    asean_gff: { eligible: false, category: "Not yet covered" },
    transition: true,
  },
  "Steel Production (BF-BOF — Low Abatement)": {
    nace: "C24.10", sector: "Industry",
    eu_taxonomy: { obj: null, eligible: false, criteria: ["BF-BOF exceeds 2026 CCM threshold (>0.5 tCO₂/t)"] },
    icma_gbp: { eligible: false, category: "Not eligible", typical_pct: 0 },
    cbi_cbs: { eligible: false, sector: "Industry", criteria_note: "Conventional BF-BOF not eligible" },
    mas_sgt: { eligible: false, tier: null, category: "Not eligible" },
    asean_gff: { eligible: false, category: "Not eligible" },
    transition: false,
  },
  "Afforestation / Reforestation": {
    nace: "A02.10", sector: "Forestry",
    eu_taxonomy: { obj: "CCA/CCM", article: "1.1", dnsh: true, criteria: ["Additionality demonstrated", "No land-use-change from high-carbon stock", "IPCC Land Use accounting"], eligible: true },
    icma_gbp: { eligible: true, category: "Land Use / Biodiversity", typical_pct: 100 },
    cbi_cbs: { eligible: true, sector: "Land Use", criteria_note: "Must demonstrate permanence and additionality" },
    mas_sgt: { eligible: true, tier: "Green", category: "Nature-Based Solutions" },
    asean_gff: { eligible: true, category: "Nature-Based Solutions" },
    transition: false,
  },
  "Sustainable Agriculture / Food": {
    nace: "A01.11", sector: "Agriculture",
    eu_taxonomy: { obj: "CCM/CCA", article: "1.1 (agriculture)", dnsh: true, criteria: ["GHG reduction vs conventional baseline", "Water stewardship plan", "No high-biodiversity land conversion"], eligible: true },
    icma_gbp: { eligible: true, category: "Sustainable Land Use / Biodiversity", typical_pct: 70 },
    cbi_cbs: { eligible: true, sector: "Land Use", criteria_note: "Soil organic carbon improvements and avoided deforestation" },
    mas_sgt: { eligible: true, tier: "Green", category: "Nature-Based Solutions" },
    asean_gff: { eligible: true, category: "Sustainable Land Use" },
    transition: false,
  },
  "Carbon Capture and Storage (CCS)": {
    nace: "D35.11 / C20.59", sector: "Energy / Industry",
    eu_taxonomy: { obj: "CCM", article: "Annex I (enabling)", dnsh: false, criteria: ["Dedicated CCS for hard-to-abate sectors", "Storage permanence demonstrated", "Leakage monitoring"], eligible: true },
    icma_gbp: { eligible: true, category: "Carbon Capture — Enabling Activity", typical_pct: 60 },
    cbi_cbs: { eligible: false, sector: "Industry", criteria_note: "CBI CBS v4 does not include CCS as standalone" },
    mas_sgt: { eligible: true, tier: "Transition", category: "Transition Activity" },
    asean_gff: { eligible: false, category: "Not covered" },
    transition: true,
  },
};

const INSTRUMENT_TYPES = [
  "Green Bond (ICMA GBP)",
  "Sustainability Bond (ICMA GBP/SBP)",
  "Green Loan (LMA GLP)",
  "Sustainability-Linked Bond (ICMA SLBP)",
  "Sustainability-Linked Loan (LMA SLLP)",
  "Social Bond (ICMA SBP)",
  "Transition Bond (ICMA TBP)",
];

// ── Eligibility check engine ─────────────────────────────────────────────────
function computeEligibility(activity_key, instrument, capex_m) {
  const act = ACTIVITIES[activity_key];
  if (!act) return null;

  // Instrument compatibility
  const instrumentChecks = {
    "Green Bond (ICMA GBP)": act.icma_gbp.eligible,
    "Sustainability Bond (ICMA GBP/SBP)": act.icma_gbp.eligible,
    "Green Loan (LMA GLP)": act.icma_gbp.eligible,
    "Sustainability-Linked Bond (ICMA SLBP)": true, // SLBs don't require specific use of proceeds
    "Sustainability-Linked Loan (LMA SLLP)": true,
    "Social Bond (ICMA SBP)": false, // environmental activity — not social
    "Transition Bond (ICMA TBP)": act.transition || act.eu_taxonomy?.eligible,
  };

  const frameworks = [
    {
      id: "eu_taxonomy",
      name: "EU Taxonomy",
      ref: "Reg 2020/852 + Delegated Acts 2021/2139",
      eligible: act.eu_taxonomy.eligible,
      details: act.eu_taxonomy.eligible
        ? `Objective: ${act.eu_taxonomy.obj || "—"} · Art. ${act.eu_taxonomy.article || "—"} · DNSH: ${act.eu_taxonomy.dnsh ? "Pass" : "Review required"}`
        : "Not eligible under EU Taxonomy Delegated Acts",
      criteria: act.eu_taxonomy.criteria || [],
      badge: act.eu_taxonomy.eligible ? (act.transition ? "amber" : "green") : "red",
    },
    {
      id: "icma_gbp",
      name: "ICMA GBP / GLP",
      ref: "ICMA Green Bond Principles 2021",
      eligible: act.icma_gbp.eligible,
      details: act.icma_gbp.eligible
        ? `Category: ${act.icma_gbp.category} · Eligible proceeds: ~${act.icma_gbp.typical_pct}%`
        : `Category: ${act.icma_gbp.category}`,
      criteria: act.icma_gbp.eligible ? ["Use of Proceeds documented", "Project Evaluation process defined", "Management of Proceeds ring-fenced", "Reporting: annual allocation + impact"] : [],
      badge: act.icma_gbp.eligible ? "green" : "red",
    },
    {
      id: "cbi_cbs",
      name: "CBI Climate Bonds Standard",
      ref: "CBI CBS v4 (2022)",
      eligible: act.cbi_cbs.eligible,
      details: act.cbi_cbs.criteria_note,
      criteria: act.cbi_cbs.eligible ? ["Sector criteria met", "Pre-issuance verification by approved verifier", "Post-issuance certification report"] : [],
      badge: act.cbi_cbs.eligible ? "green" : "red",
    },
    {
      id: "mas_sgt",
      name: "MAS Singapore Green Taxonomy",
      ref: "SGT v2.0 (MAS 2023)",
      eligible: act.mas_sgt.eligible,
      details: act.mas_sgt.eligible
        ? `Tier: ${act.mas_sgt.tier} · Category: ${act.mas_sgt.category}`
        : `Category: ${act.mas_sgt.category}`,
      criteria: act.mas_sgt.eligible ? ["Activity in SGT eligible list", "Substantive contribution test", "DNSH criteria (MAS SGT Annex)", "Minimum social safeguards"] : [],
      badge: act.mas_sgt.eligible ? (act.mas_sgt.tier === "Transition" ? "amber" : "green") : "red",
    },
    {
      id: "asean_gff",
      name: "ASEAN Green Finance Framework",
      ref: "ASEAN Capital Markets Forum 2021",
      eligible: act.asean_gff.eligible,
      details: `Category: ${act.asean_gff.category}`,
      criteria: act.asean_gff.eligible ? ["Activity in ASEAN GFF eligible categories", "Use of Proceeds aligned", "Impact reporting commitment"] : [],
      badge: act.asean_gff.eligible ? "green" : "red",
    },
  ];

  const eligibleCount = frameworks.filter(f => f.eligible).length;
  const allEligible = eligibleCount === frameworks.length;
  const noneEligible = eligibleCount === 0;

  let overall_label;
  if (noneEligible) overall_label = "Not Eligible";
  else if (act.transition && eligibleCount >= 2) overall_label = "Transition Finance";
  else if (allEligible) overall_label = "Fully Eligible (All Frameworks)";
  else if (eligibleCount >= 3) overall_label = "Eligible (Major Frameworks)";
  else overall_label = "Partially Eligible";

  const instrumentCompatible = instrumentChecks[instrument] ?? false;

  return {
    activity: activity_key,
    nace: act.nace,
    sector: act.sector,
    capex_m,
    instrument,
    instrumentCompatible,
    frameworks,
    eligibleCount,
    overall_label,
    transition: act.transition,
  };
}

// ── KPI card ──────────────────────────────────────────────────────────────────
function KpiCard({ label, value, sub, color = "text-white" }) {
  return (
    <div className="bg-[#0d1424] border border-white/[0.06] rounded-lg p-3">
      <div className={`text-xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-white/40 mt-0.5">{label}</div>
      {sub && <div className="text-[11px] text-white/20 mt-0.5">{sub}</div>}
    </div>
  );
}

// ── Badge component ───────────────────────────────────────────────────────────
function EligBadge({ badge }) {
  if (badge === "green") return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
      <CheckCircle className="h-3 w-3" /> Eligible
    </span>
  );
  if (badge === "amber") return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
      <AlertTriangle className="h-3 w-3" /> Transition
    </span>
  );
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-red-500/10 text-red-400 border border-red-500/20">
      <XCircle className="h-3 w-3" /> Not Eligible
    </span>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────────
const DEFAULT_PARAMS = {
  activity: "Solar PV Generation",
  instrument: "Green Bond (ICMA GBP)",
  capex_m: 150,
  project_name: "Renewables SPV — Jurong Island",
  country: "Singapore",
};

export function TransitionFinancePanel() {
  const [params, setParams] = useState({ ...DEFAULT_PARAMS });
  const [result, setResult] = useState(() => computeEligibility(DEFAULT_PARAMS.activity, DEFAULT_PARAMS.instrument, DEFAULT_PARAMS.capex_m));

  const set = (k, v) => {
    const next = { ...params, [k]: v };
    setParams(next);
    setResult(computeEligibility(next.activity, next.instrument, next.capex_m));
  };

  const overallColor = result
    ? result.overall_label === "Not Eligible" ? "text-red-400"
    : result.overall_label === "Transition Finance" ? "text-amber-400"
    : "text-emerald-400"
    : "text-white";

  return (
    <div className="space-y-6">
      {/* Methodology note */}
      <div className="p-3 bg-indigo-500/5 border border-indigo-500/20 rounded-lg text-xs text-indigo-300 flex items-start gap-2">
        <Info className="h-4 w-4 mt-0.5 shrink-0" />
        <span>
          Multi-framework eligibility engine: EU Taxonomy (2020/852 + Delegated Acts), ICMA Green Bond Principles 2021,
          Climate Bonds Initiative CBS v4, MAS Singapore Green Taxonomy v2.0, ASEAN GFF 2021.
          Select an activity to run simultaneous eligibility checks across all frameworks.
        </span>
      </div>

      {/* Inputs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-white/80">Project Parameters</h3>

          <div>
            <label className="text-xs text-white/40 block mb-1">Project Name</label>
            <input className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={params.project_name} onChange={e => set("project_name", e.target.value)} />
          </div>

          <div>
            <label className="text-xs text-white/40 block mb-1">Activity / Asset Type</label>
            <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={params.activity} onChange={e => set("activity", e.target.value)}>
              {Object.keys(ACTIVITIES).map(a => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-white/40 block mb-1">Financial Instrument</label>
            <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={params.instrument} onChange={e => set("instrument", e.target.value)}>
              {INSTRUMENT_TYPES.map(i => (
                <option key={i} value={i}>{i}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-white/40 block mb-1">Capex / Use of Proceeds (M USD)</label>
            <input type="number" step="10" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={params.capex_m} onChange={e => set("capex_m", +e.target.value)} />
          </div>

          <div>
            <label className="text-xs text-white/40 block mb-1">Country / Jurisdiction</label>
            <input className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
              value={params.country} onChange={e => set("country", e.target.value)} />
          </div>

          {result && (
            <div className="mt-2 p-2 bg-[#0d1424] border border-white/[0.06] rounded text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-white/40">NACE Code</span>
                <span className="text-white/70 font-mono">{result.nace}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/40">Sector</span>
                <span className="text-white/70">{result.sector}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/40">Transition Activity</span>
                <span className={result.transition ? "text-amber-400" : "text-emerald-400"}>
                  {result.transition ? "Yes" : "No"}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Overall verdict */}
        {result && (
          <div className="space-y-3">
            {/* Overall KPIs */}
            <div className="grid grid-cols-2 gap-3">
              <KpiCard
                label="Overall Eligibility"
                value={result.overall_label}
                sub={`${result.eligibleCount}/5 frameworks`}
                color={overallColor}
              />
              <KpiCard
                label="Instrument Compatible"
                value={result.instrumentCompatible ? "Yes" : "No"}
                sub={params.instrument.split(" ")[0]}
                color={result.instrumentCompatible ? "text-emerald-400" : "text-red-400"}
              />
              <KpiCard
                label="Use of Proceeds (M USD)"
                value={`$${params.capex_m}M`}
                sub={`${result.eligibleCount > 0 ? "~" + (result.icma_gbp_pct || 100) + "% eligible" : "0% eligible"}`}
                color="text-indigo-400"
              />
              <KpiCard
                label="Frameworks Eligible"
                value={`${result.eligibleCount} / 5`}
                sub="Simultaneous check"
                color={result.eligibleCount >= 4 ? "text-emerald-400" : result.eligibleCount >= 2 ? "text-amber-400" : "text-red-400"}
              />
            </div>

            {/* Instrument warning */}
            {!result.instrumentCompatible && (
              <div className="p-3 bg-red-500/5 border border-red-500/20 rounded text-xs text-red-300 flex items-start gap-2">
                <XCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>
                  The selected instrument type <strong>{params.instrument}</strong> is not compatible with
                  this activity's eligibility profile. Consider a Transition Bond or Sustainability-Linked structure.
                </span>
              </div>
            )}

            {result.transition && (
              <div className="p-3 bg-amber-500/5 border border-amber-500/20 rounded text-xs text-amber-300 flex items-start gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>
                  This activity qualifies as a <strong>Transition Activity</strong> under applicable frameworks.
                  Transition Bond (ICMA TBP 2023) or Sustainability-Linked structures are most appropriate.
                  EU Taxonomy eligibility may be time-limited.
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Framework-by-framework breakdown */}
      {result && (
        <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white/70 mb-4">
            Framework Eligibility — {params.project_name}
          </h3>
          <div className="space-y-3">
            {result.frameworks.map(fw => (
              <div key={fw.id} className="border border-white/[0.06] rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <span className="text-sm font-semibold text-white/80">{fw.name}</span>
                    <span className="ml-2 text-[10px] text-white/30">{fw.ref}</span>
                  </div>
                  <EligBadge badge={fw.badge} />
                </div>
                <p className="text-xs text-white/50 mb-2">{fw.details}</p>
                {fw.criteria.length > 0 && (
                  <div className="space-y-1">
                    {fw.criteria.map((c, i) => (
                      <div key={i} className="flex items-start gap-1.5 text-xs text-white/40">
                        <CheckCircle className="h-3 w-3 text-emerald-500/60 shrink-0 mt-0.5" />
                        {c}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Required documentation checklist */}
      {result && result.eligibleCount > 0 && (
        <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white/70 mb-3">Pre-Issuance Documentation Checklist</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            {[
              ["Green/Sustainability Finance Framework", "Required for all labelled instruments — aligned to relevant GBP/GLP"],
              ["Second Party Opinion (SPO)", "From CICERO, Sustainalytics, ISS ESG, V.E or equivalent"],
              ["Use of Proceeds Register", "Project list, CAPEX amounts, eligible % tracking"],
              ["Project Selection Criteria", "Internal taxonomy aligned to EU Taxonomy / ICMA GBP categories"],
              ["Allocation Reporting", "Annual — unallocated proceeds, reallocations, temporary placements"],
              ["Impact Reporting", "Annual — GHG avoided (tCO₂e), kWh generated, m² certified, etc."],
              ["CBI Pre-Issuance Certification", "Required if CBI Climate Bonds label is targeted"],
              ["EU Taxonomy Alignment Assessment", "DNSH criteria, Minimum Social Safeguards, TSC per activity"],
            ].map(([item, desc]) => (
              <div key={item} className="flex items-start gap-2 p-2 bg-[#0d1424] border border-white/[0.04] rounded">
                <CheckCircle className="h-3.5 w-3.5 text-indigo-400/60 shrink-0 mt-0.5" />
                <div>
                  <div className="text-white/60 font-medium">{item}</div>
                  <div className="text-white/30 mt-0.5">{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
