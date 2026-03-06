/**
 * Blended Finance Structure Modeller
 * Aligned with: OECD Blended Finance Principles 2018, MDB/DFI Cascade Approach,
 *               IFC EDGE/MAS/FMO concessional finance guidelines,
 *               IDFC Principles on Climate Mainstreaming
 *
 * Computes optimal capital stack (grant, concessional debt, commercial debt, equity)
 * for emerging market RE / climate projects to achieve market-rate IRR.
 */
import React, { useState, useCallback } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, PieChart, Pie
} from "recharts";
import { DollarSign, Layers, TrendingUp, RefreshCw, Info, Target, CheckCircle } from "lucide-react";

const API_BASE = process.env.REACT_APP_BACKEND_URL || "http://localhost:8001";

const fmtM = (v, d = 1) => v == null ? "—" : `$${Number(v).toFixed(d)}M`;
const fmtPct = (v, d = 1) => v == null ? "—" : `${Number(v).toFixed(d)}%`;

// ── Pure client-side blended finance computation ─────────────────────────────
// (no dedicated backend route needed — all math is straightforward)

function computeBlendedFinance(p) {
  const totalCapex = p.total_capex_usd_m;
  const grantPct = p.grant_pct / 100;
  const concDebtPct = p.concessional_debt_pct / 100;
  const commDebtPct = p.commercial_debt_pct / 100;
  const equityPct = 1 - grantPct - concDebtPct - commDebtPct;

  const grantAmt = totalCapex * grantPct;
  const concDebtAmt = totalCapex * concDebtPct;
  const commDebtAmt = totalCapex * commDebtPct;
  const equityAmt = totalCapex * equityPct;

  // Annual debt service
  const annualConcDS = concDebtAmt * (p.conc_rate_pct / 100) / (1 - Math.pow(1 + p.conc_rate_pct / 100, -p.tenor_years));
  const annualCommDS = commDebtAmt * (p.comm_rate_pct / 100) / (1 - Math.pow(1 + p.comm_rate_pct / 100, -p.tenor_years));
  const annualTotalDS = annualConcDS + annualCommDS;

  // DSCR
  const annualNOI = p.annual_revenue_usd_m - p.annual_opex_usd_m;
  const dscr = annualTotalDS > 0 ? annualNOI / annualTotalDS : null;

  // IRR approximation (simplified)
  const cashFlowAfterDS = annualNOI - annualTotalDS;
  const irr_approx = equityAmt > 0 ? (cashFlowAfterDS / equityAmt) * 100 : 0;

  // Blending ratio (public : private)
  const publicFinance = grantAmt + concDebtAmt;
  const privateFinance = commDebtAmt + equityAmt;
  const blendingRatio = privateFinance > 0 ? (privateFinance / publicFinance).toFixed(2) : "—";

  // Concessional subsidy value (NPV of interest savings)
  const interestSavingPA = concDebtAmt * (p.market_rate_pct - p.conc_rate_pct) / 100;
  const concSubsidyNPV = interestSavingPA * (1 - Math.pow(1 + p.market_rate_pct / 100, -p.tenor_years)) / (p.market_rate_pct / 100);

  // MDB cascade check
  const needsConcessional = irr_approx < p.target_irr_pct;
  const additionalGrantNeeded = needsConcessional
    ? Math.max(0, (p.target_irr_pct - irr_approx) / 100 * equityAmt)
    : 0;

  // Capital stack for chart
  const stack = [
    { name: "Grant", value: +grantAmt.toFixed(1), fill: "#10b981" },
    { name: "Conc. Debt", value: +concDebtAmt.toFixed(1), fill: "#6366f1" },
    { name: "Comm. Debt", value: +commDebtAmt.toFixed(1), fill: "#3b82f6" },
    { name: "Equity", value: +equityAmt.toFixed(1), fill: "#f59e0b" },
  ];

  return {
    grantAmt, concDebtAmt, commDebtAmt, equityAmt, equityPct,
    annualTotalDS, annualNOI, dscr, irr_approx,
    blendingRatio, concSubsidyNPV, needsConcessional, additionalGrantNeeded,
    stack,
  };
}

const DEFAULT_PARAMS = {
  project_name: "Solar + Storage, Kenya",
  project_type: "solar_storage",
  country_income_group: "LMC",
  total_capex_usd_m: 120,
  annual_revenue_usd_m: 18,
  annual_opex_usd_m: 4,
  grant_pct: 15,
  concessional_debt_pct: 35,
  commercial_debt_pct: 30,
  conc_rate_pct: 2.5,
  comm_rate_pct: 9.0,
  market_rate_pct: 11.0,
  tenor_years: 18,
  target_irr_pct: 12,
  co2_reduction_mt_pa: 0.065,
};

const PROJECT_TYPES = [
  "solar_storage", "onshore_wind", "offshore_wind", "hydro",
  "green_hydrogen", "energy_efficiency", "grid_modernisation", "climate_adaptation",
];

export function BlendedFinancePanel() {
  const [params, setParams] = useState({ ...DEFAULT_PARAMS });
  const [result, setResult] = useState(null);

  const compute = useCallback(() => {
    setResult(computeBlendedFinance(params));
  }, [params]);

  // Auto-compute on mount
  React.useEffect(() => { compute(); }, []);

  const set = (k, v) => {
    setParams(f => {
      const next = { ...f, [k]: v };
      setResult(computeBlendedFinance(next));
      return next;
    });
  };

  const DSCR_COLOR = result?.dscr >= 1.3 ? "text-emerald-400" : result?.dscr >= 1.1 ? "text-amber-400" : "text-red-400";
  const IRR_COLOR = result?.irr_approx >= params.target_irr_pct ? "text-emerald-400" : "text-amber-400";

  return (
    <div className="space-y-6">
      {/* Methodology note */}
      <div className="p-3 bg-indigo-500/5 border border-indigo-500/20 rounded-lg text-xs text-indigo-300 flex items-start gap-2">
        <Info className="h-4 w-4 mt-0.5 shrink-0" />
        <span>OECD Blended Finance Principles 2018 · MDB Cascade Approach · IFC EDGE concessional finance. The cascade approach tests if a project is commercially viable before adding public subsidy — only the minimum necessary concessional support is provided.</span>
      </div>

      {/* Input + Live Results side-by-side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Inputs */}
        <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
          <h3 className="text-sm font-semibold text-white/80 mb-4">Project Parameters</h3>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-white/40 block mb-1">Project Name</label>
              <input className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                value={params.project_name} onChange={e => set("project_name", e.target.value)} />
            </div>
            <div>
              <label className="text-xs text-white/40 block mb-1">Project Type</label>
              <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                value={params.project_type} onChange={e => set("project_type", e.target.value)}>
                {PROJECT_TYPES.map(v => <option key={v} value={v}>{v.replace(/_/g, " ")}</option>)}
              </select>
            </div>
            {[
              ["total_capex_usd_m", "Total Capex (M USD)"],
              ["annual_revenue_usd_m", "Annual Revenue (M USD)"],
              ["annual_opex_usd_m", "Annual Opex (M USD)"],
              ["tenor_years", "Loan Tenor (years)"],
              ["target_irr_pct", "Target Equity IRR (%)"],
            ].map(([k, label]) => (
              <div key={k}>
                <label className="text-xs text-white/40 block mb-1">{label}</label>
                <input type="number" step="0.5" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                  value={params[k]} onChange={e => set(k, +e.target.value)} />
              </div>
            ))}
          </div>

          <h4 className="text-xs font-semibold text-white/50 mt-4 mb-2">Capital Stack (%)</h4>
          <div className="space-y-2">
            {[
              ["grant_pct", "Grant / ODA (%)", "#10b981"],
              ["concessional_debt_pct", "Concessional Debt (%)", "#6366f1"],
              ["commercial_debt_pct", "Commercial Debt (%)", "#3b82f6"],
            ].map(([k, label, color]) => (
              <div key={k}>
                <div className="flex justify-between mb-1">
                  <label className="text-xs text-white/40">{label}</label>
                  <span className="text-xs font-medium" style={{ color }}>{params[k]}%</span>
                </div>
                <input type="range" min="0" max="60" step="5" value={params[k]}
                  onChange={e => set(k, +e.target.value)}
                  className="w-full accent-indigo-500 h-1.5" />
              </div>
            ))}
            <div className="text-xs text-white/30">
              Equity = {Math.max(0, 100 - params.grant_pct - params.concessional_debt_pct - params.commercial_debt_pct).toFixed(0)}%
            </div>
          </div>

          <h4 className="text-xs font-semibold text-white/50 mt-4 mb-2">Interest Rates (%)</h4>
          {[
            ["conc_rate_pct", "Concessional Rate", "0.5"],
            ["comm_rate_pct", "Commercial Rate", "0.5"],
            ["market_rate_pct", "Market Reference Rate", "0.5"],
          ].map(([k, label, step]) => (
            <div key={k} className="mb-2">
              <label className="text-xs text-white/40 block mb-1">{label}</label>
              <input type="number" step={step} className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                value={params[k]} onChange={e => set(k, +e.target.value)} />
            </div>
          ))}
        </div>

        {/* Live Results */}
        {result && (
          <div className="space-y-4">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "DSCR", val: result.dscr?.toFixed(2) + "x", cls: DSCR_COLOR, sub: "≥1.30x bankable" },
                { label: "Equity IRR (est.)", val: fmtPct(result.irr_approx), cls: IRR_COLOR, sub: `Target: ${params.target_irr_pct}%` },
                { label: "Blending Ratio", val: result.blendingRatio + "x", cls: "text-indigo-400", sub: "Private : Public $$" },
                { label: "Conc. Subsidy NPV", val: fmtM(result.concSubsidyNPV), cls: "text-purple-400", sub: "Interest savings" },
              ].map(({ label, val, cls, sub }) => (
                <div key={label} className="bg-[#0d1424] border border-white/[0.06] rounded-lg p-3">
                  <div className={`text-2xl font-bold ${cls}`}>{val}</div>
                  <div className="text-xs text-white/40 mt-1">{label}</div>
                  <div className="text-xs text-white/20">{sub}</div>
                </div>
              ))}
            </div>

            {/* MDB Cascade Flag */}
            {result.needsConcessional ? (
              <div className="p-3 bg-amber-500/5 border border-amber-500/20 rounded text-xs text-amber-300 flex items-start gap-2">
                <Info className="h-4 w-4 shrink-0 mt-0.5" />
                <span>Project IRR ({fmtPct(result.irr_approx)}) below target ({params.target_irr_pct}%). MDB Cascade: additional concessional support of ~{fmtM(result.additionalGrantNeeded)} grant equivalent recommended.</span>
              </div>
            ) : (
              <div className="p-3 bg-emerald-500/5 border border-emerald-500/20 rounded text-xs text-emerald-300 flex items-start gap-2">
                <CheckCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>Project is commercially viable at current capital stack. IRR exceeds target — concessional support is appropriate but minimal.</span>
              </div>
            )}

            {/* Capital Stack Chart */}
            <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
              <h3 className="text-sm font-semibold text-white/70 mb-3">Capital Stack — {params.project_name}</h3>
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={[{ name: "Capex" }]} layout="vertical" margin={{ left: 0, right: 20 }}>
                  <XAxis type="number" tick={{ fontSize: 10, fill: "#ffffff40" }} tickFormatter={v => `$${v}M`} />
                  <YAxis type="category" dataKey="name" tick={false} width={0} />
                  <Tooltip contentStyle={{ backgroundColor: "#1a2234", border: "1px solid #ffffff10", fontSize: 11 }}
                    formatter={v => [`$${Number(v).toFixed(1)}M`]} />
                  {result.stack.map(s => (
                    <Bar key={s.name} dataKey={() => s.value} name={s.name} stackId="a" fill={s.fill} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
              <div className="flex gap-3 mt-2 flex-wrap">
                {result.stack.map(s => (
                  <div key={s.name} className="flex items-center gap-1.5 text-xs">
                    <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: s.fill }} />
                    <span className="text-white/50">{s.name}: {fmtM(s.value)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Annual flows */}
            <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4 text-xs">
              <h3 className="text-sm font-semibold text-white/70 mb-3">Annual Cash Flow Summary</h3>
              {[
                ["Revenue", result.annualNOI + params.annual_opex_usd_m, "text-emerald-400"],
                ["Opex", -params.annual_opex_usd_m, "text-red-400"],
                ["NOI", result.annualNOI, "text-white/70"],
                ["Debt Service", -result.annualTotalDS, "text-orange-400"],
                ["Equity Cash Flow", result.annualNOI - result.annualTotalDS, result.annualNOI - result.annualTotalDS > 0 ? "text-emerald-400" : "text-red-400"],
              ].map(([label, val, cls]) => (
                <div key={label} className="flex justify-between py-1 border-b border-white/[0.04]">
                  <span className="text-white/40">{label}</span>
                  <span className={`font-medium ${cls}`}>{fmtM(val)}/yr</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
