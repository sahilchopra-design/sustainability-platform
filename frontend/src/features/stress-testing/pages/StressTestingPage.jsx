/**
 * Stress Testing Page
 *
 * Multi-scenario ECL stress testing, PD backtesting,
 * sensitivity analysis, EBA GL/2017/16 regulatory scenarios.
 * Backend: /api/v1/stress-testing
 */
import React, { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, Cell,
} from "recharts";

const TABS = [
  "ECL Stress Test",
  "PD Backtesting",
  "Sensitivity Analysis",
  "Regulatory Scenarios",
  "Results",
];

const EMERALD = "#059669";
const COLORS = { base: "#059669", adverse: "#f59e0b", severe: "#ef4444" };
const COLORS_ARR = ["#059669", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6"];

/* ── Deterministic data ────────────────────────────────────────────────── */
const SECTORS = [
  "Corporate", "Retail Mortgage", "SME", "Sovereign", "Financial Institutions",
  "Commercial RE", "Infrastructure", "Trade Finance",
];

const ECL_BY_SECTOR = SECTORS.map((s, i) => ({
  sector: s,
  base: +(0.45 + i * 0.12).toFixed(2),
  adverse: +(0.78 + i * 0.18).toFixed(2),
  severe: +(1.25 + i * 0.25).toFixed(2),
}));

const ECL_TOTAL = {
  base: ECL_BY_SECTOR.reduce((s, r) => s + r.base, 0),
  adverse: ECL_BY_SECTOR.reduce((s, r) => s + r.adverse, 0),
  severe: ECL_BY_SECTOR.reduce((s, r) => s + r.severe, 0),
};

const PD_BACKTEST = [
  { year: 2019, predicted: 1.2, actual: 1.1 },
  { year: 2020, predicted: 2.8, actual: 3.5 },
  { year: 2021, predicted: 2.1, actual: 1.9 },
  { year: 2022, predicted: 1.5, actual: 1.4 },
  { year: 2023, predicted: 1.3, actual: 1.5 },
  { year: 2024, predicted: 1.1, actual: 1.2 },
  { year: 2025, predicted: 1.0, actual: 0.9 },
];

const SENSITIVITY_PARAMS = [
  { param: "GDP Growth", baseVal: "+2.1%", shocked: "-3.5%", eclImpact: "+42 bps", direction: "up" },
  { param: "Unemployment Rate", baseVal: "4.2%", shocked: "9.8%", eclImpact: "+38 bps", direction: "up" },
  { param: "Interest Rate", baseVal: "3.5%", shocked: "6.5%", eclImpact: "+25 bps", direction: "up" },
  { param: "Property Prices", baseVal: "+3%", shocked: "-25%", eclImpact: "+31 bps", direction: "up" },
  { param: "Oil Price", baseVal: "$75/bbl", shocked: "$120/bbl", eclImpact: "+18 bps", direction: "up" },
  { param: "Carbon Price", baseVal: "$60/t", shocked: "$150/t", eclImpact: "+22 bps", direction: "up" },
  { param: "FX Rate (EUR/USD)", baseVal: "1.08", shocked: "0.85", eclImpact: "+15 bps", direction: "up" },
];

const SENSITIVITY_CHART = SENSITIVITY_PARAMS.map((p) => ({
  param: p.param,
  impact: parseInt(p.eclImpact),
}));

const REG_SCENARIOS = [
  { framework: "EBA 2025", scenario: "Baseline", gdp: "+1.8%", unemp: "6.5%", property: "+2%", horizon: "3 years" },
  { framework: "EBA 2025", scenario: "Adverse", gdp: "-1.2%", unemp: "9.2%", property: "-12%", horizon: "3 years" },
  { framework: "EBA 2025", scenario: "Severely Adverse", gdp: "-4.5%", unemp: "12.8%", property: "-28%", horizon: "3 years" },
  { framework: "ECB CSST 2024", scenario: "Disorderly Transition", gdp: "-2.1%", unemp: "8.5%", property: "-15%", horizon: "5 years" },
  { framework: "ECB CSST 2024", scenario: "Hot House", gdp: "-3.8%", unemp: "10.2%", property: "-22%", horizon: "30 years" },
  { framework: "BoE ACS", scenario: "Early Action", gdp: "-0.5%", unemp: "5.5%", property: "-5%", horizon: "5 years" },
  { framework: "BoE ACS", scenario: "Late Action", gdp: "-3.2%", unemp: "9.8%", property: "-20%", horizon: "5 years" },
];

function KpiCard({ label, value }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="text-xs text-gray-500 font-medium">{label}</div>
      <div className="text-2xl font-bold text-gray-900 mt-1">{value}</div>
    </div>
  );
}

/* ── Tab: ECL Stress Test ──────────────────────────────────────────────── */
function ECLStressTestTab() {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">ECL by Sector &mdash; Base vs Adverse vs Severe (%)</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={340}>
          <BarChart data={ECL_BY_SECTOR} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="sector" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={60} />
            <YAxis tick={{ fontSize: 11 }} label={{ value: "ECL %", angle: -90, position: "insideLeft", style: { fontSize: 11 } }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="base" name="Base" fill={COLORS.base} />
            <Bar dataKey="adverse" name="Adverse" fill={COLORS.adverse} />
            <Bar dataKey="severe" name="Severe" fill={COLORS.severe} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Sector", "Base ECL (%)", "Adverse ECL (%)", "Severe ECL (%)", "Stress Multiple"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ECL_BY_SECTOR.map((r, i) => (
              <tr key={r.sector} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{r.sector}</td>
                <td className="px-3 py-2 text-emerald-700">{r.base}</td>
                <td className="px-3 py-2 text-amber-600">{r.adverse}</td>
                <td className="px-3 py-2 text-red-600">{r.severe}</td>
                <td className="px-3 py-2 font-semibold">{(r.severe / r.base).toFixed(1)}x</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: PD Backtesting ───────────────────────────────────────────────── */
function PDBacktestingTab() {
  const absErrors = PD_BACKTEST.map((p) => Math.abs(p.predicted - p.actual));
  const mae = (absErrors.reduce((s, e) => s + e, 0) / absErrors.length).toFixed(2);
  const ar = 0.82;
  return (
    <div>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <KpiCard label="Accuracy Ratio (AR)" value={ar} />
        <KpiCard label="Mean Absolute Error" value={`${mae}%`} />
        <KpiCard label="Observations" value={PD_BACKTEST.length} />
      </div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Predicted vs Actual PD (%)</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={PD_BACKTEST}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="year" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="predicted" name="Predicted PD" stroke={EMERALD} strokeWidth={2} dot={{ r: 4 }} />
            <Line type="monotone" dataKey="actual" name="Actual PD" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Backtest Assessment</h3>
        <p className="text-xs text-gray-600">Model passes traffic-light test (green zone). Binomial test p-value = 0.34 (no significant deviation). COVID-19 year 2020 shows largest underestimate, consistent with tail-risk event not captured by through-the-cycle PD.</p>
      </div>
    </div>
  );
}

/* ── Tab: Sensitivity Analysis ─────────────────────────────────────────── */
function SensitivityAnalysisTab() {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Tornado Chart &mdash; ECL Impact by Macro Parameter (bps)</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={SENSITIVITY_CHART} layout="vertical" margin={{ left: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis type="number" tick={{ fontSize: 11 }} label={{ value: "bps", position: "insideRight", style: { fontSize: 10 } }} />
            <YAxis type="category" dataKey="param" tick={{ fontSize: 10 }} width={130} />
            <Tooltip />
            <Bar dataKey="impact" name="ECL Impact (bps)">
              {SENSITIVITY_CHART.map((_, i) => <Cell key={i} fill={COLORS_ARR[i % COLORS_ARR.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Parameter", "Base Value", "Shocked Value", "ECL Impact"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SENSITIVITY_PARAMS.map((p, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{p.param}</td>
                <td className="px-3 py-2">{p.baseVal}</td>
                <td className="px-3 py-2 text-red-600">{p.shocked}</td>
                <td className="px-3 py-2 font-semibold">{p.eclImpact}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: Regulatory Scenarios ─────────────────────────────────────────── */
function RegulatoryScenariosTab() {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Regulatory Stress Test Scenarios</h3>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Framework", "Scenario", "GDP", "Unemployment", "Property", "Horizon"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {REG_SCENARIOS.map((r, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{r.framework}</td>
                <td className="px-3 py-2">{r.scenario}</td>
                <td className="px-3 py-2">{r.gdp}</td>
                <td className="px-3 py-2">{r.unemp}</td>
                <td className="px-3 py-2">{r.property}</td>
                <td className="px-3 py-2">{r.horizon}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Applicable Guidelines</h3>
        <div className="text-xs text-gray-600 space-y-1">
          <p><span className="font-medium">EBA GL/2018/04:</span> Guidelines on stress testing institutions</p>
          <p><span className="font-medium">EBA GL/2017/16:</span> Credit risk stress testing &amp; ECL estimation</p>
          <p><span className="font-medium">ECB CSST:</span> Climate stress test (biennial, next 2026)</p>
          <p><span className="font-medium">BoE ACS:</span> Annual Cyclical Scenario + Climate BES</p>
        </div>
      </div>
    </div>
  );
}

/* ── Tab: Results ──────────────────────────────────────────────────────── */
function ResultsTab() {
  const capitalImpact = [
    { metric: "CET1 Ratio (Pre-Stress)", value: "14.2%", status: "Above minimum" },
    { metric: "CET1 Ratio (Base)", value: "13.8%", status: "Above minimum" },
    { metric: "CET1 Ratio (Adverse)", value: "11.5%", status: "Above buffer" },
    { metric: "CET1 Ratio (Severe)", value: "9.1%", status: "Near minimum" },
    { metric: "Pillar 2R Add-on", value: "2.0%", status: "Prescribed" },
    { metric: "MDA Trigger", value: "9.5%", status: "Severe breaches" },
    { metric: "Leverage Ratio (Severe)", value: "3.8%", status: "Above 3% min" },
  ];
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Aggregate Stress Test Results</h3>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <KpiCard label="Total Base ECL ($M)" value={ECL_TOTAL.base.toFixed(1)} />
        <KpiCard label="Total Adverse ECL ($M)" value={ECL_TOTAL.adverse.toFixed(1)} />
        <KpiCard label="Total Severe ECL ($M)" value={ECL_TOTAL.severe.toFixed(1)} />
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Capital Metric", "Value", "Assessment"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {capitalImpact.map((c, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{c.metric}</td>
                <td className="px-3 py-2 font-semibold">{c.value}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    c.status.includes("Near") || c.status.includes("breaches") ? "text-red-600 bg-red-50" : "text-emerald-600 bg-emerald-50"
                  }`}>{c.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Main Component ────────────────────────────────────────────────────── */
export default function StressTestingPage() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Stress Testing</h1>
        <p className="text-sm text-gray-500 mb-6">
          Multi-scenario ECL stress testing, PD backtesting, sensitivity analysis &amp; EBA/ECB/BoE regulatory scenarios
        </p>

        <div className="grid grid-cols-4 gap-4 mb-6">
          <KpiCard label="Base ECL" value={`$${ECL_TOTAL.base.toFixed(1)}M`} />
          <KpiCard label="Stressed ECL (Severe)" value={`$${ECL_TOTAL.severe.toFixed(1)}M`} />
          <KpiCard label="PD Accuracy Ratio" value="0.82" />
          <KpiCard label="Capital Impact" value="-510 bps" />
        </div>

        <div className="flex gap-1 mb-6 border-b border-gray-200">
          {TABS.map((tab, i) => (
            <button
              key={tab}
              onClick={() => setActiveTab(i)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === i
                  ? "text-emerald-700 border-b-2 border-emerald-600"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === 0 && <ECLStressTestTab />}
        {activeTab === 1 && <PDBacktestingTab />}
        {activeTab === 2 && <SensitivityAnalysisTab />}
        {activeTab === 3 && <RegulatoryScenariosTab />}
        {activeTab === 4 && <ResultsTab />}
      </div>
    </div>
  );
}
