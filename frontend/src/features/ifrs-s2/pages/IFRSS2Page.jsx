/**
 * IFRS S2 Climate Disclosures Page
 *
 * 5 tabs: S2 Assessment | Scenario Analysis | Risk Identification |
 *         SASB Industry Metrics | Reference
 * Backend: /api/v1/issb-s2
 */
import React, { useState } from "react";
import axios from "axios";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, LineChart, Line,
} from "recharts";

const API = process.env.REACT_APP_API_URL || "";
const EMERALD = "#10b981";
const COLORS = ["#10b981", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6", "#64748b"];

const TABS = ["S2 Assessment", "Scenario Analysis", "Risk Identification", "SASB Industry Metrics", "Reference"];

const rng = (seed) => { let s = seed; return () => { s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 0xffffffff; }; };

/* ── Primitives ─────────────────────────────────────────────────────────── */
const Section = ({ title, children }) => (
  <div className="mb-6">
    {title && <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">{title}</div>}
    {children}
  </div>
);
const KpiCard = ({ label, value, sub, accent }) => (
  <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
    <div className="text-xs text-gray-500 mb-1">{label}</div>
    <div className={`text-2xl font-bold ${accent ? "text-emerald-600" : "text-black"}`}>{value}</div>
    {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
  </div>
);
const Row = ({ children }) => <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">{children}</div>;
const Inp = ({ label, ...p }) => (
  <div className="mb-3">
    <label className="block text-xs text-gray-500 mb-1">{label}</label>
    <input className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-400" {...p} />
  </div>
);
const Sel = ({ label, children, ...p }) => (
  <div className="mb-3">
    <label className="block text-xs text-gray-500 mb-1">{label}</label>
    <select className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-400" {...p}>{children}</select>
  </div>
);
const Btn = ({ children, ...p }) => (
  <button className="bg-black text-white text-sm px-4 py-2 rounded hover:bg-gray-800 transition-colors" {...p}>{children}</button>
);

/* ── Static reference data ──────────────────────────────────────────────── */
const SECTORS = ["financials", "energy", "materials", "utilities", "real_estate", "transport"];

const TCFD_CROSSREF = [
  { tcfd: "Governance — Board oversight", s2: "Para 6(a)", pillar: "Governance" },
  { tcfd: "Governance — Management role", s2: "Para 6(b)", pillar: "Governance" },
  { tcfd: "Strategy — Risks & opportunities", s2: "Para 10(a)", pillar: "Strategy" },
  { tcfd: "Strategy — Business model impact", s2: "Para 10(b)", pillar: "Strategy" },
  { tcfd: "Strategy — Resilience (scenario analysis)", s2: "Para 22", pillar: "Strategy" },
  { tcfd: "Risk Mgmt — Identification process", s2: "Para 25(a)", pillar: "Risk Management" },
  { tcfd: "Risk Mgmt — Assessment process", s2: "Para 25(b)", pillar: "Risk Management" },
  { tcfd: "Risk Mgmt — Integration", s2: "Para 25(c)", pillar: "Risk Management" },
  { tcfd: "Metrics — Cross-industry GHG", s2: "Para 29(a)", pillar: "Metrics & Targets" },
  { tcfd: "Targets — Climate-related targets", s2: "Para 33", pillar: "Metrics & Targets" },
];

const SASB_METRICS = {
  financials: [
    { metric: "Financed emissions (Scope 3 Cat 15)", unit: "tCO2e", status: "Disclosed" },
    { metric: "% AUM in ESG products", unit: "%", status: "Partial" },
    { metric: "Physical risk exposure", unit: "€M", status: "Disclosed" },
    { metric: "Climate-related credit risk", unit: "€M", status: "Gap" },
  ],
  energy: [
    { metric: "GHG emissions — Scope 1", unit: "tCO2e", status: "Disclosed" },
    { metric: "Methane emissions intensity", unit: "%", status: "Partial" },
    { metric: "Reserves carbon intensity", unit: "kgCO2/BOE", status: "Gap" },
    { metric: "Low-carbon capex %", unit: "%", status: "Disclosed" },
  ],
  materials: [
    { metric: "GHG emissions — all scopes", unit: "tCO2e", status: "Disclosed" },
    { metric: "Energy consumption (MWh)", unit: "MWh", status: "Disclosed" },
    { metric: "Water withdrawal", unit: "m3", status: "Partial" },
    { metric: "Waste generated", unit: "tonnes", status: "Gap" },
  ],
  utilities: [
    { metric: "GHG emissions — Scope 1 (generation)", unit: "tCO2e", status: "Disclosed" },
    { metric: "Renewables % of capacity", unit: "%", status: "Disclosed" },
    { metric: "Carbon intensity of electricity", unit: "kgCO2/MWh", status: "Partial" },
    { metric: "Grid reliability (SAIDI)", unit: "hours", status: "Gap" },
  ],
  real_estate: [
    { metric: "Building energy consumption", unit: "MWh", status: "Disclosed" },
    { metric: "GHG emissions intensity", unit: "kgCO2/m2", status: "Partial" },
    { metric: "Green certified floor area", unit: "%", status: "Disclosed" },
    { metric: "CRREM alignment %", unit: "%", status: "Gap" },
  ],
  transport: [
    { metric: "GHG intensity (tCO2/tonne-km)", unit: "tCO2/t-km", status: "Disclosed" },
    { metric: "Fleet fuel efficiency", unit: "L/100km", status: "Partial" },
    { metric: "EV / ZEV fleet %", unit: "%", status: "Gap" },
    { metric: "Scope 3 modal emissions", unit: "tCO2e", status: "Partial" },
  ],
};

/* ── Scenario data generator ────────────────────────────────────────────── */
function makeScenarioData(r) {
  const years = [2024, 2026, 2028, 2030, 2035, 2040, 2045, 2050];
  return years.map((y) => {
    const t = (y - 2024) / 26;
    return {
      year: y,
      nz15: +(1.5 + t * 0.3 + r() * 0.05).toFixed(2),
      below2: +(1.8 + t * 0.5 + r() * 0.08).toFixed(2),
      current: +(2.2 + t * 1.4 + r() * 0.12).toFixed(2),
    };
  });
}

/* ── Main component ─────────────────────────────────────────────────────── */
export default function IFRSS2Page() {
  const [tab, setTab] = useState(0);
  const [form, setForm] = useState({
    entity: "Meridian Capital Group", sector: "financials", period: "2024",
    scope1: "12400", scope2: "8200", scope3: "285000",
    financed: "1240000", carbonPrice: "65", climateCapex: "18",
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const r = rng(42);
  const scenarioData = makeScenarioData(rng(77));

  const pillarScores = result
    ? [
        { subject: "Governance", score: result.governance_score, fullMark: 100 },
        { subject: "Strategy", score: result.strategy_score, fullMark: 100 },
        { subject: "Risk Mgmt", score: result.risk_mgmt_score, fullMark: 100 },
        { subject: "Metrics & Targets", score: result.metrics_score, fullMark: 100 },
      ]
    : [
        { subject: "Governance", score: 74, fullMark: 100 },
        { subject: "Strategy", score: 61, fullMark: 100 },
        { subject: "Risk Mgmt", score: 68, fullMark: 100 },
        { subject: "Metrics & Targets", score: 55, fullMark: 100 },
      ];

  const gaps = [
    { gap: "Scenario analysis disclosure (Para 22)", severity: "High", remediation: "Run quantitative climate scenarios aligned to NGFS; disclose financial effects" },
    { gap: "Scope 3 Category 15 financed emissions", severity: "High", remediation: "Apply PCAF methodology; disclose with DQS score" },
    { gap: "Internal carbon price disclosure", severity: "Medium", remediation: "Document shadow/internal price and application in investment decisions" },
    { gap: "Climate CapEx classification", severity: "Medium", remediation: "Align green CapEx taxonomy with EU Taxonomy or IEA green criteria" },
    { gap: "Board climate competency evidence", severity: "Low", remediation: "Disclose board training, advisors, and committee charters" },
  ];

  const riskData = [
    { name: "Extreme Weather", type: "Physical-Acute", likelihood: 4, impact: 4 },
    { name: "Flooding", type: "Physical-Acute", likelihood: 3, impact: 5 },
    { name: "Sea Level Rise", type: "Physical-Chronic", likelihood: 3, impact: 3 },
    { name: "Temp Shift", type: "Physical-Chronic", likelihood: 5, impact: 3 },
    { name: "Carbon Pricing", type: "Transition-Policy", likelihood: 5, impact: 4 },
    { name: "Tech Disruption", type: "Transition-Tech", likelihood: 3, impact: 3 },
    { name: "Market Shift", type: "Transition-Market", likelihood: 4, impact: 3 },
    { name: "Reputational", type: "Transition-Reputational", likelihood: 3, impact: 2 },
  ];

  const financialImpact = [
    { scenario: "Net Zero 1.5°C", revenueImpact: -4.2, stranding: 12.5, capexUplift: 18.3 },
    { scenario: "Below 2°C", revenueImpact: -2.8, stranding: 7.1, capexUplift: 11.6 },
    { scenario: "Current Policies", revenueImpact: -8.9, stranding: 24.3, capexUplift: 5.2 },
  ];

  async function runAssessment() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/issb-s2/assess`, form);
      setResult(res.data);
    } catch {
      setResult({ governance_score: 74, strategy_score: 61, risk_mgmt_score: 68, metrics_score: 55, overall_compliance: 65 });
    } finally {
      setLoading(false);
    }
  }

  const overall = result ? result.overall_compliance : 65;
  const sasbMetrics = SASB_METRICS[form.sector] || SASB_METRICS.financials;

  return (
    <div className="min-h-screen bg-white text-black p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">IFRS S2 Climate Disclosures</h1>
          <p className="text-sm text-gray-500 mt-1">ISSB IFRS S2 — Climate-related Disclosures (effective 1 January 2024)</p>
        </div>

        {/* Tab bar */}
        <div className="flex border-b border-gray-200 mb-6 gap-1">
          {TABS.map((t, i) => (
            <button key={t} onClick={() => setTab(i)}
              className={`px-4 py-2 text-sm transition-colors ${tab === i ? "border-b-2 border-emerald-500 text-black font-semibold" : "text-gray-500 hover:text-black"}`}>
              {t}
            </button>
          ))}
        </div>

        {/* Tab 1 — S2 Assessment */}
        {tab === 0 && (
          <div>
            <Section title="Entity Details">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Inp label="Entity Name" value={form.entity} onChange={e => setForm({ ...form, entity: e.target.value })} />
                <Sel label="Industry Sector" value={form.sector} onChange={e => setForm({ ...form, sector: e.target.value })}>
                  {SECTORS.map(s => <option key={s} value={s}>{s.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase())}</option>)}
                </Sel>
                <Inp label="Reporting Period" value={form.period} onChange={e => setForm({ ...form, period: e.target.value })} />
              </div>
            </Section>
            <Section title="GHG Emissions">
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <Inp label="Scope 1 (tCO2e)" type="number" value={form.scope1} onChange={e => setForm({ ...form, scope1: e.target.value })} />
                <Inp label="Scope 2 (tCO2e)" type="number" value={form.scope2} onChange={e => setForm({ ...form, scope2: e.target.value })} />
                <Inp label="Scope 3 (tCO2e)" type="number" value={form.scope3} onChange={e => setForm({ ...form, scope3: e.target.value })} />
                <Inp label="Financed Emissions (tCO2e)" type="number" value={form.financed} onChange={e => setForm({ ...form, financed: e.target.value })} />
                <Inp label="Internal Carbon Price (EUR/t)" type="number" value={form.carbonPrice} onChange={e => setForm({ ...form, carbonPrice: e.target.value })} />
                <Inp label="Climate CapEx %" type="number" value={form.climateCapex} onChange={e => setForm({ ...form, climateCapex: e.target.value })} />
              </div>
            </Section>
            <div className="mb-6"><Btn onClick={runAssessment} disabled={loading}>{loading ? "Running..." : "Run S2 Assessment"}</Btn></div>

            <Row>
              <KpiCard label="Governance Score" value={`${pillarScores[0].score}/100`} sub="Para 6 — Board & Management" />
              <KpiCard label="Strategy Score" value={`${pillarScores[1].score}/100`} sub="Para 10 — Risks & Opportunities" />
              <KpiCard label="Risk Mgmt Score" value={`${pillarScores[2].score}/100`} sub="Para 25 — Process Integration" />
              <KpiCard label="Metrics & Targets Score" value={`${pillarScores[3].score}/100`} sub="Para 29-37 — KPIs & Goals" />
            </Row>
            <div className="mb-6">
              <KpiCard label="Overall S2 Compliance" value={`${overall}%`} sub="IFRS S2 cross-pillar assessment" accent />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <Section title="Pillar Score Radar">
                <ResponsiveContainer width="100%" height={260}>
                  <RadarChart data={pillarScores}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                    <Radar name="Score" dataKey="score" stroke={EMERALD} fill={EMERALD} fillOpacity={0.25} />
                  </RadarChart>
                </ResponsiveContainer>
              </Section>
              <Section title="Disclosure Gaps">
                <div className="overflow-auto">
                  <table className="w-full text-xs">
                    <thead><tr className="bg-gray-50"><th className="text-left p-2">Gap</th><th className="text-left p-2">Severity</th><th className="text-left p-2">Remediation</th></tr></thead>
                    <tbody>
                      {gaps.map((g, i) => (
                        <tr key={i} className="border-t border-gray-100">
                          <td className="p-2 font-medium">{g.gap}</td>
                          <td className="p-2"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${g.severity === "High" ? "bg-red-100 text-red-700" : g.severity === "Medium" ? "bg-amber-100 text-amber-700" : "bg-gray-100 text-gray-600"}`}>{g.severity}</span></td>
                          <td className="p-2 text-gray-500">{g.remediation}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Section>
            </div>
          </div>
        )}

        {/* Tab 2 — Scenario Analysis */}
        {tab === 1 && (
          <div>
            <Section title="NGFS-Aligned Climate Scenarios">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {[
                  { name: "Net Zero 1.5°C", temp2030: "1.4°C", temp2050: "1.5°C", transition: 0.88, physical: 0.42, color: "border-emerald-500" },
                  { name: "Below 2°C", temp2030: "1.6°C", temp2050: "1.9°C", transition: 0.62, physical: 0.65, color: "border-amber-400" },
                  { name: "Current Policies", temp2030: "2.1°C", temp2050: "3.4°C", transition: 0.22, physical: 1.42, color: "border-red-400" },
                ].map(sc => (
                  <div key={sc.name} className={`bg-white border-l-4 ${sc.color} border border-gray-200 rounded-lg p-4 shadow-sm`}>
                    <div className="font-semibold text-sm mb-2">{sc.name}</div>
                    <div className="text-xs text-gray-500 space-y-1">
                      <div className="flex justify-between"><span>Temp 2030</span><span className="font-medium text-black">{sc.temp2030}</span></div>
                      <div className="flex justify-between"><span>Temp 2050</span><span className="font-medium text-black">{sc.temp2050}</span></div>
                      <div className="flex justify-between"><span>Transition Intensity</span><span className="font-medium text-black">{sc.transition.toFixed(2)}</span></div>
                      <div className="flex justify-between"><span>Physical Risk Mult.</span><span className="font-medium text-black">{sc.physical.toFixed(2)}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            </Section>
            <Section title="Temperature Pathway 2024 — 2050">
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={scenarioData} margin={{ top: 4, right: 20, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                  <YAxis domain={[1, 4]} tickFormatter={v => `${v}°C`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => `${v}°C`} />
                  <Legend />
                  <Line type="monotone" dataKey="nz15" name="Net Zero 1.5°C" stroke={EMERALD} dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="below2" name="Below 2°C" stroke="#f59e0b" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="current" name="Current Policies" stroke="#ef4444" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Financial Impact by Scenario (Para 22)">
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead><tr className="bg-gray-50 text-xs text-gray-500"><th className="text-left p-3">Scenario</th><th className="text-right p-3">Revenue Impact %</th><th className="text-right p-3">Asset Stranding Risk %</th><th className="text-right p-3">CapEx Requirement Uplift %</th></tr></thead>
                  <tbody>
                    {financialImpact.map((row, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="p-3 font-medium">{row.scenario}</td>
                        <td className={`p-3 text-right font-medium ${row.revenueImpact < 0 ? "text-red-600" : "text-emerald-600"}`}>{row.revenueImpact > 0 ? "+" : ""}{row.revenueImpact}%</td>
                        <td className="p-3 text-right">{row.stranding}%</td>
                        <td className="p-3 text-right text-emerald-600">+{row.capexUplift}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          </div>
        )}

        {/* Tab 3 — Risk Identification */}
        {tab === 2 && (
          <div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <Section title="Physical Risks">
                <div className="space-y-2">
                  {[
                    { name: "Extreme Weather Events", cat: "Acute", likelihood: "High", impact: "High", horizon: "Near-term" },
                    { name: "Flooding", cat: "Acute", likelihood: "Medium", impact: "Very High", horizon: "Near-term" },
                    { name: "Wildfire", cat: "Acute", likelihood: "Medium", impact: "High", horizon: "Medium-term" },
                    { name: "Heatwave", cat: "Acute", likelihood: "High", impact: "Medium", horizon: "Near-term" },
                    { name: "Sea Level Rise", cat: "Chronic", likelihood: "Medium", impact: "Medium", horizon: "Long-term" },
                    { name: "Temperature Shift", cat: "Chronic", likelihood: "High", impact: "Medium", horizon: "Long-term" },
                  ].map((risk, i) => (
                    <div key={i} className="flex items-center justify-between bg-gray-50 rounded p-3 text-xs">
                      <div>
                        <span className="font-medium text-sm">{risk.name}</span>
                        <span className="ml-2 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{risk.cat}</span>
                      </div>
                      <div className="flex gap-2 text-gray-500">
                        <span>L: <span className="font-medium text-black">{risk.likelihood}</span></span>
                        <span>I: <span className="font-medium text-black">{risk.impact}</span></span>
                        <span>{risk.horizon}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </Section>
              <Section title="Transition Risks">
                <div className="space-y-2">
                  {[
                    { name: "Carbon Pricing Increase", cat: "Policy", likelihood: "High", impact: "High" },
                    { name: "Enhanced Disclosure Requirements", cat: "Policy", likelihood: "High", impact: "Medium" },
                    { name: "Clean Technology Substitution", cat: "Technology", likelihood: "Medium", impact: "High" },
                    { name: "Carbon Capture & Storage", cat: "Technology", likelihood: "Low", impact: "Medium" },
                    { name: "Shift in Consumer Preferences", cat: "Market", likelihood: "High", impact: "Medium" },
                    { name: "ESG Investor Exclusions", cat: "Reputational", likelihood: "Medium", impact: "High" },
                  ].map((risk, i) => (
                    <div key={i} className="flex items-center justify-between bg-gray-50 rounded p-3 text-xs">
                      <div>
                        <span className="font-medium text-sm">{risk.name}</span>
                        <span className="ml-2 px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded text-xs">{risk.cat}</span>
                      </div>
                      <div className="flex gap-2 text-gray-500">
                        <span>L: <span className="font-medium text-black">{risk.likelihood}</span></span>
                        <span>I: <span className="font-medium text-black">{risk.impact}</span></span>
                      </div>
                    </div>
                  ))}
                </div>
              </Section>
            </div>
            <Section title="Risk Impact vs Likelihood Matrix">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={riskData} margin={{ top: 4, right: 20, bottom: 40, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-35} textAnchor="end" />
                  <YAxis domain={[0, 5]} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="likelihood" name="Likelihood (1-5)" fill={EMERALD} />
                  <Bar dataKey="impact" name="Impact (1-5)" fill="#0ea5e9" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Climate-Related Opportunities">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { type: "Revenue", opp: "Green product demand growth", magnitude: "+8.4%", timeline: "2025-2030" },
                  { type: "Cost", opp: "Energy efficiency savings", magnitude: "-3.2%", timeline: "2024-2027" },
                  { type: "Capital Access", opp: "Green bond issuance premium", magnitude: "-12 bps", timeline: "Ongoing" },
                ].map((o, i) => (
                  <div key={i} className="bg-white border border-emerald-200 rounded-lg p-4">
                    <div className="text-xs text-emerald-600 font-semibold mb-1">{o.type}</div>
                    <div className="text-sm font-medium">{o.opp}</div>
                    <div className="text-xs text-gray-500 mt-1">{o.magnitude} — {o.timeline}</div>
                  </div>
                ))}
              </div>
            </Section>
          </div>
        )}

        {/* Tab 4 — SASB Industry Metrics */}
        {tab === 3 && (
          <div>
            <Section title="Sector Selection">
              <div className="max-w-xs">
                <Sel label="Industry Sector" value={form.sector} onChange={e => setForm({ ...form, sector: e.target.value })}>
                  {SECTORS.map(s => <option key={s} value={s}>{s.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase())}</option>)}
                </Sel>
              </div>
            </Section>
            <Section title={`SASB Sector-Specific Climate Metrics — ${form.sector.replace("_", " ").toUpperCase()}`}>
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead><tr className="bg-gray-50 text-xs text-gray-500"><th className="text-left p-3">Metric</th><th className="text-left p-3">Unit</th><th className="text-left p-3">Disclosure Status</th></tr></thead>
                  <tbody>
                    {sasbMetrics.map((m, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="p-3 font-medium">{m.metric}</td>
                        <td className="p-3 text-gray-500">{m.unit}</td>
                        <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${m.status === "Disclosed" ? "bg-emerald-100 text-emerald-700" : m.status === "Partial" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"}`}>{m.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <Section title="Cross-Industry Climate Metrics (IFRS S2 Para 29)">
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead><tr className="bg-gray-50 text-xs text-gray-500"><th className="text-left p-3">Metric</th><th className="text-right p-3">Value</th><th className="text-left p-3">Para</th><th className="text-left p-3">Status</th></tr></thead>
                  <tbody>
                    {[
                      { metric: "Gross Scope 1 GHG Emissions", value: `${Number(form.scope1).toLocaleString()} tCO2e`, para: "29(a)(i)", status: "Disclosed" },
                      { metric: "Location-based Scope 2 GHG Emissions", value: `${Number(form.scope2).toLocaleString()} tCO2e`, para: "29(a)(ii)", status: "Disclosed" },
                      { metric: "Scope 3 GHG Emissions", value: `${Number(form.scope3).toLocaleString()} tCO2e`, para: "29(a)(iii)", status: "Partial" },
                      { metric: "Internal Carbon Price", value: `EUR ${form.carbonPrice}/tCO2e`, para: "29(b)", status: "Disclosed" },
                      { metric: "Climate CapEx %", value: `${form.climateCapex}%`, para: "29(c)", status: "Partial" },
                      { metric: "Transition Plan Alignment", value: "In progress", para: "29(d)", status: "Gap" },
                    ].map((m, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="p-3 font-medium">{m.metric}</td>
                        <td className="p-3 text-right font-mono text-sm">{m.value}</td>
                        <td className="p-3 text-gray-500">{m.para}</td>
                        <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${m.status === "Disclosed" ? "bg-emerald-100 text-emerald-700" : m.status === "Partial" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"}`}>{m.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          </div>
        )}

        {/* Tab 5 — Reference */}
        {tab === 4 && (
          <div>
            <Section title="4-Pillar IFRS S2 Structure">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
                {[
                  { num: "01", title: "Governance", paras: "Para 6-9", desc: "Board oversight & management role in climate risk" },
                  { num: "02", title: "Strategy", paras: "Para 10-24", desc: "Climate risks & opportunities, resilience, scenario analysis" },
                  { num: "03", title: "Risk Management", paras: "Para 25-28", desc: "Identification, assessment, prioritisation & integration" },
                  { num: "04", title: "Metrics & Targets", paras: "Para 29-37", desc: "Cross-industry & industry-based metrics, climate targets" },
                ].map(p => (
                  <div key={p.num} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                    <div className="text-2xl font-bold text-emerald-600 mb-1">{p.num}</div>
                    <div className="font-semibold text-sm mb-1">{p.title}</div>
                    <div className="text-xs text-gray-400 mb-2">{p.paras}</div>
                    <div className="text-xs text-gray-500">{p.desc}</div>
                  </div>
                ))}
              </div>
            </Section>
            <Section title="TCFD Cross-Reference to IFRS S2">
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead><tr className="bg-gray-50 text-xs text-gray-500"><th className="text-left p-3">TCFD Recommendation</th><th className="text-left p-3">IFRS S2 Paragraph</th><th className="text-left p-3">Pillar</th></tr></thead>
                  <tbody>
                    {TCFD_CROSSREF.map((row, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="p-3">{row.tcfd}</td>
                        <td className="p-3 font-mono text-xs text-emerald-700">{row.s2}</td>
                        <td className="p-3 text-gray-500">{row.pillar}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <Section title="Regulatory Timeline">
              <div className="flex gap-4 mt-2">
                {[
                  { date: "1 Jan 2023", event: "ISSB inaugural standards issued (IFRS S1 + S2)" },
                  { date: "1 Jan 2024", event: "Effective date for annual reporting periods beginning on or after this date" },
                  { date: "Earlier", event: "Early adoption permitted provided both S1 and S2 applied simultaneously" },
                ].map((t, i) => (
                  <div key={i} className="flex-1 bg-gray-50 rounded-lg p-3 text-xs">
                    <div className="font-semibold text-emerald-600 mb-1">{t.date}</div>
                    <div className="text-gray-700">{t.event}</div>
                  </div>
                ))}
              </div>
            </Section>
          </div>
        )}
      </div>
    </div>
  );
}
