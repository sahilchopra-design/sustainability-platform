/**
 * Geothermal Page
 *
 * LCOE analysis, project viability, seismicity risk,
 * financial returns (NPV/IRR), site comparison.
 * Backend: /api/v1/geothermal
 */
import React, { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, Cell, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar,
} from "recharts";

const TABS = [
  "Project Viability",
  "LCOE Analysis",
  "Seismicity Risk",
  "Financial Returns",
  "Site Comparison",
];

const EMERALD = "#059669";
const COLORS = ["#059669", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6"];

/* ── Deterministic data ────────────────────────────────────────────────── */
const SITES = [
  { site: "Iceland Reykjanes", depth: 2500, temp: 290, lcoe: 38, npv: 142, irr: 18.5, seismic: 2.1, capacity: 120, type: "Flash" },
  { site: "Kenya Olkaria V", depth: 2800, temp: 310, lcoe: 42, npv: 118, irr: 16.2, seismic: 1.8, capacity: 180, type: "Flash" },
  { site: "Indonesia Muara Laboh", depth: 2200, temp: 260, lcoe: 45, npv: 95, irr: 14.8, seismic: 3.5, capacity: 85, type: "Binary" },
  { site: "New Zealand Ngatamariki", depth: 2600, temp: 285, lcoe: 40, npv: 130, irr: 17.1, seismic: 2.4, capacity: 100, type: "Flash" },
  { site: "Turkey Efeler", depth: 1800, temp: 230, lcoe: 48, npv: 78, irr: 13.2, seismic: 4.2, capacity: 60, type: "Binary" },
  { site: "Philippines Tiwi", depth: 3000, temp: 320, lcoe: 35, npv: 165, irr: 19.8, seismic: 3.8, capacity: 200, type: "Flash" },
  { site: "USA Coso Basin", depth: 2400, temp: 270, lcoe: 52, npv: 88, irr: 12.5, seismic: 2.8, capacity: 75, type: "Binary" },
  { site: "Japan Yanaizu-Nishiyama", depth: 2100, temp: 250, lcoe: 55, npv: 72, irr: 11.8, seismic: 5.1, capacity: 65, type: "Flash" },
];

const LCOE_COMPARE = [
  { source: "Geothermal", lcoe: 44 },
  { source: "Onshore Wind", lcoe: 38 },
  { source: "Solar PV", lcoe: 32 },
  { source: "Offshore Wind", lcoe: 72 },
  { source: "Nuclear", lcoe: 85 },
  { source: "Gas CCGT", lcoe: 58 },
];

const VIABILITY_FACTORS = [
  { factor: "Resource Temperature", score: 85, fullMark: 100 },
  { factor: "Reservoir Permeability", score: 72, fullMark: 100 },
  { factor: "Grid Connection", score: 90, fullMark: 100 },
  { factor: "Environmental Permits", score: 65, fullMark: 100 },
  { factor: "Social License", score: 78, fullMark: 100 },
  { factor: "Geological Certainty", score: 68, fullMark: 100 },
];

const SEISMIC_HISTORY = [
  { year: 2018, events: 12, maxMag: 1.8 },
  { year: 2019, events: 18, maxMag: 2.1 },
  { year: 2020, events: 8, maxMag: 1.5 },
  { year: 2021, events: 25, maxMag: 2.8 },
  { year: 2022, events: 15, maxMag: 2.0 },
  { year: 2023, events: 22, maxMag: 2.4 },
  { year: 2024, events: 10, maxMag: 1.7 },
  { year: 2025, events: 14, maxMag: 1.9 },
];

const RISK_COLORS = (score) => {
  if (score <= 2) return "text-emerald-600 bg-emerald-50";
  if (score <= 3.5) return "text-amber-600 bg-amber-50";
  return "text-red-600 bg-red-50";
};

function KpiCard({ label, value }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="text-xs text-gray-500 font-medium">{label}</div>
      <div className="text-2xl font-bold text-gray-900 mt-1">{value}</div>
    </div>
  );
}

/* ── Tab: Project Viability ────────────────────────────────────────────── */
function ProjectViabilityTab() {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Viability Assessment Radar</h3>
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={VIABILITY_FACTORS}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="factor" tick={{ fontSize: 10 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Radar name="Score" dataKey="score" stroke={EMERALD} fill={EMERALD} fillOpacity={0.3} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
          <h3 className="text-sm font-semibold text-gray-700">Viability Factors</h3>
          {VIABILITY_FACTORS.map((f) => (
            <div key={f.factor} className="flex items-center justify-between text-xs">
              <span className="text-gray-600">{f.factor}</span>
              <div className="flex items-center gap-2">
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${f.score}%` }} />
                </div>
                <span className="font-medium text-gray-900 w-8 text-right">{f.score}</span>
              </div>
            </div>
          ))}
          <div className="pt-2 border-t border-gray-100">
            <p className="text-xs text-gray-500">Overall Viability: <span className="font-semibold text-emerald-700">
              {(VIABILITY_FACTORS.reduce((s, f) => s + f.score, 0) / VIABILITY_FACTORS.length).toFixed(0)}%
            </span></p>
          </div>
        </div>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Key Risk Factors</h3>
        <div className="grid grid-cols-3 gap-4 text-xs text-gray-600">
          <div><span className="font-medium">Exploration Risk:</span> 20-40% failure rate at exploration drilling stage</div>
          <div><span className="font-medium">Resource Decline:</span> 2-5% annual decline rate without reinjection</div>
          <div><span className="font-medium">Induced Seismicity:</span> Managed via traffic-light protocol (TLP)</div>
        </div>
      </div>
    </div>
  );
}

/* ── Tab: LCOE Analysis ────────────────────────────────────────────────── */
function LCOEAnalysisTab() {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">LCOE Comparison: Geothermal vs Other Sources ($/MWh)</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={LCOE_COMPARE}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="source" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} label={{ value: "$/MWh", angle: -90, position: "insideLeft", style: { fontSize: 11 } }} />
            <Tooltip />
            <Bar dataKey="lcoe" name="LCOE ($/MWh)">
              {LCOE_COMPARE.map((_, i) => <Cell key={i} fill={i === 0 ? EMERALD : COLORS[i % COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Site", "Type", "LCOE ($/MWh)", "Capacity (MW)", "Capacity Factor"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SITES.map((s, i) => (
              <tr key={s.site} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{s.site}</td>
                <td className="px-3 py-2">{s.type}</td>
                <td className="px-3 py-2 font-semibold text-emerald-700">${s.lcoe}</td>
                <td className="px-3 py-2">{s.capacity}</td>
                <td className="px-3 py-2">90%+</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: Seismicity Risk ──────────────────────────────────────────────── */
function SeismicityRiskTab() {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Induced Seismicity Events (All Sites)</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={SEISMIC_HISTORY}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="year" tick={{ fontSize: 11 }} />
            <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} domain={[0, 4]} />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="events" name="Events" fill={EMERALD} />
            <Line yAxisId="right" type="monotone" dataKey="maxMag" name="Max Magnitude" stroke="#ef4444" strokeWidth={2} dot={{ r: 4 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Site Seismic Risk Scores</h3>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Site", "Depth (m)", "Seismic Score", "Risk Level", "TLP Status"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SITES.map((s, i) => (
              <tr key={s.site} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{s.site}</td>
                <td className="px-3 py-2">{s.depth.toLocaleString()}</td>
                <td className="px-3 py-2">{s.seismic}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${RISK_COLORS(s.seismic)}`}>
                    {s.seismic <= 2 ? "Low" : s.seismic <= 3.5 ? "Medium" : "High"}
                  </span>
                </td>
                <td className="px-3 py-2">{s.seismic <= 2 ? "Green" : s.seismic <= 3.5 ? "Amber" : "Red"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: Financial Returns ────────────────────────────────────────────── */
function FinancialReturnsTab() {
  const sorted = [...SITES].sort((a, b) => b.irr - a.irr);
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">IRR by Project (%)</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={sorted}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="site" tick={{ fontSize: 9 }} angle={-20} textAnchor="end" height={60} />
            <YAxis tick={{ fontSize: 11 }} label={{ value: "IRR %", angle: -90, position: "insideLeft", style: { fontSize: 11 } }} />
            <Tooltip />
            <Bar dataKey="irr" name="IRR (%)">
              {sorted.map((s, i) => <Cell key={i} fill={s.irr >= 15 ? EMERALD : s.irr >= 12 ? "#f59e0b" : "#ef4444"} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Site", "NPV ($M)", "IRR (%)", "LCOE ($/MWh)", "Payback (yrs)"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((s, i) => (
              <tr key={s.site} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{s.site}</td>
                <td className="px-3 py-2">${s.npv}M</td>
                <td className="px-3 py-2 font-semibold text-emerald-700">{s.irr}%</td>
                <td className="px-3 py-2">${s.lcoe}</td>
                <td className="px-3 py-2">{(25 / s.irr).toFixed(1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: Site Comparison ──────────────────────────────────────────────── */
function SiteComparisonTab() {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Full Site Assessment Matrix</h3>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Site", "Depth (m)", "Temp (\u00B0C)", "LCOE ($/MWh)", "NPV ($M)", "IRR (%)", "Seismic Risk"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SITES.map((s, i) => (
              <tr key={s.site} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{s.site}</td>
                <td className="px-3 py-2">{s.depth.toLocaleString()}</td>
                <td className="px-3 py-2">{s.temp}</td>
                <td className="px-3 py-2">${s.lcoe}</td>
                <td className="px-3 py-2">${s.npv}M</td>
                <td className="px-3 py-2">{s.irr}%</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${RISK_COLORS(s.seismic)}`}>
                    {s.seismic} ({s.seismic <= 2 ? "Low" : s.seismic <= 3.5 ? "Med" : "High"})
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 grid grid-cols-4 gap-4">
        <KpiCard label="Best LCOE" value={`$${Math.min(...SITES.map((s) => s.lcoe))}/MWh`} />
        <KpiCard label="Best IRR" value={`${Math.max(...SITES.map((s) => s.irr))}%`} />
        <KpiCard label="Total Capacity" value={`${SITES.reduce((s, x) => s + x.capacity, 0)} MW`} />
        <KpiCard label="Avg Seismic Risk" value={(SITES.reduce((s, x) => s + x.seismic, 0) / SITES.length).toFixed(1)} />
      </div>
    </div>
  );
}

/* ── Main Component ────────────────────────────────────────────────────── */
export default function GeothermalPage() {
  const [activeTab, setActiveTab] = useState(0);

  const avgLCOE = (SITES.reduce((s, x) => s + x.lcoe, 0) / SITES.length).toFixed(0);
  const avgIRR = (SITES.reduce((s, x) => s + x.irr, 0) / SITES.length).toFixed(1);
  const avgSeismic = (SITES.reduce((s, x) => s + x.seismic, 0) / SITES.length).toFixed(1);
  const totalCap = SITES.reduce((s, x) => s + x.capacity, 0);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Geothermal Energy</h1>
        <p className="text-sm text-gray-500 mb-6">
          LCOE analysis, project viability, induced seismicity risk, financial returns &amp; site comparison
        </p>

        <div className="grid grid-cols-4 gap-4 mb-6">
          <KpiCard label="Avg LCOE ($/MWh)" value={`$${avgLCOE}`} />
          <KpiCard label="Project IRR" value={`${avgIRR}%`} />
          <KpiCard label="Seismic Risk Score" value={avgSeismic} />
          <KpiCard label="Total Capacity (MW)" value={totalCap} />
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

        {activeTab === 0 && <ProjectViabilityTab />}
        {activeTab === 1 && <LCOEAnalysisTab />}
        {activeTab === 2 && <SeismicityRiskTab />}
        {activeTab === 3 && <FinancialReturnsTab />}
        {activeTab === 4 && <SiteComparisonTab />}
      </div>
    </div>
  );
}
