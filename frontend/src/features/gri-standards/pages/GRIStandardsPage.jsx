/**
 * GRI Standards Disclosure Page
 *
 * 5 tabs: GRI Assessment | Material Topics | GRI 300 Environment |
 *         Content Index | Reference
 * Backend: /api/v1/gri-standards
 */
import React, { useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, AreaChart, Area, PieChart, Pie, Cell,
} from "recharts";

const API = process.env.REACT_APP_API_URL || "";
const EMERALD = "#10b981";
const COLORS = ["#10b981", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6", "#64748b", "#06b6d4"];

const TABS = ["GRI Assessment", "Material Topics", "GRI 300 Environment", "Content Index", "Reference"];

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

/* ── Static data ─────────────────────────────────────────────────────────── */
const r0 = rng(88);

const STANDARD_SCORES = [
  { standard: "GRI 1 Foundation", score: Math.round(r0() * 20 + 78) },
  { standard: "GRI 2 General", score: Math.round(r0() * 25 + 60) },
  { standard: "GRI 3 Material", score: Math.round(r0() * 25 + 55) },
  { standard: "GRI 301 Materials", score: Math.round(r0() * 30 + 45) },
  { standard: "GRI 302 Energy", score: Math.round(r0() * 25 + 60) },
  { standard: "GRI 303 Water", score: Math.round(r0() * 30 + 40) },
  { standard: "GRI 304 Biodiversity", score: Math.round(r0() * 35 + 30) },
  { standard: "GRI 305 Emissions", score: Math.round(r0() * 25 + 55) },
  { standard: "GRI 306 Waste", score: Math.round(r0() * 30 + 45) },
];

const MATERIAL_TOPICS = [
  { topic: "Climate Change", inside: true, outside: true, score: 92 },
  { topic: "Energy Management", inside: true, outside: false, score: 85 },
  { topic: "GHG Emissions", inside: true, outside: true, score: 88 },
  { topic: "Water Stewardship", inside: true, outside: true, score: 71 },
  { topic: "Waste & Circular Economy", inside: true, outside: false, score: 64 },
  { topic: "Biodiversity", inside: false, outside: true, score: 55 },
  { topic: "Employee Health & Safety", inside: true, outside: false, score: 78 },
  { topic: "Labour Practices", inside: true, outside: true, score: 74 },
  { topic: "Anti-Corruption", inside: true, outside: false, score: 81 },
  { topic: "Supply Chain", inside: false, outside: true, score: 67 },
];

const ENERGY_TREND = [2020, 2021, 2022, 2023, 2024].map((y, i) => {
  const r = rng(y);
  return {
    year: String(y),
    consumption: Math.round(1200 - i * 55 + r() * 80),
    renewable: Math.round(180 + i * 62 + r() * 40),
  };
});

const EMISSIONS_TREND = [2020, 2021, 2022, 2023, 2024].map((y, i) => {
  const r = rng(y + 1);
  return {
    year: String(y),
    scope1: Math.round(9800 - i * 420 + r() * 500),
    scope2: Math.round(6200 - i * 280 + r() * 300),
    scope3: Math.round(82000 - i * 2100 + r() * 3000),
  };
});

const WASTE_PIE = [
  { name: "Recycled", value: 38 },
  { name: "Composted", value: 12 },
  { name: "Energy Recovery", value: 18 },
  { name: "Landfill", value: 24 },
  { name: "Hazardous", value: 8 },
];

const CONTENT_INDEX = [
  { standard: "GRI 2", disc: "2-1", title: "Organizational details", location: "Annual Report p.4", omission: "" },
  { standard: "GRI 2", disc: "2-6", title: "Activities, value chain and other business relationships", location: "Annual Report p.12", omission: "" },
  { standard: "GRI 2", disc: "2-22", title: "Statement on sustainable development strategy", location: "Sustainability Report p.2", omission: "" },
  { standard: "GRI 3", disc: "3-1", title: "Process to determine material topics", location: "Sustainability Report p.8", omission: "" },
  { standard: "GRI 3", disc: "3-2", title: "List of material topics", location: "Sustainability Report p.10", omission: "" },
  { standard: "GRI 302", disc: "302-1", title: "Energy consumption within the organization", location: "ESG Appendix p.18", omission: "" },
  { standard: "GRI 302", disc: "302-4", title: "Reduction of energy consumption", location: "ESG Appendix p.19", omission: "" },
  { standard: "GRI 305", disc: "305-1", title: "Direct (Scope 1) GHG emissions", location: "ESG Appendix p.22", omission: "" },
  { standard: "GRI 305", disc: "305-2", title: "Energy indirect (Scope 2) GHG emissions", location: "ESG Appendix p.23", omission: "" },
  { standard: "GRI 305", disc: "305-3", title: "Other indirect (Scope 3) GHG emissions", location: "Not disclosed", omission: "Insufficient data — committed FY2025" },
  { standard: "GRI 303", disc: "303-3", title: "Water withdrawal", location: "ESG Appendix p.25", omission: "" },
  { standard: "GRI 304", disc: "304-1", title: "Operational sites in/near protected areas", location: "Not disclosed", omission: "Not applicable — no manufacturing sites" },
  { standard: "GRI 306", disc: "306-3", title: "Waste generated", location: "ESG Appendix p.28", omission: "" },
];

const SERVICE_LEVELS = [
  { level: "GRI-referenced", req: "Report at least one GRI Standard with reference claim", assurance: "Voluntary", index: "Partial" },
  { level: "In accordance with GRI", req: "Report all material topics per GRI 1, 2, 3", assurance: "Recommended", index: "Full" },
];

export default function GRIStandardsPage() {
  const [tab, setTab] = useState(0);
  const [form, setForm] = useState({
    entity: "Meridian Group plc", period: "2024",
    serviceLevel: "with_reference", assurance: "limited",
  });
  const [matForm, setMatForm] = useState({ sector: "financials", stakeholders: "120" });
  const [indexFilter, setIndexFilter] = useState("All");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function runAssessment() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/gri-standards/assess`, form);
      setResult(res.data);
    } catch {
      setResult({ gri1: 82, gri2: 67, gri3: 60, gri300: 54, overall: 66 });
    } finally { setLoading(false); }
  }

  async function runMateriality() {
    try { await axios.post(`${API}/api/v1/gri-standards/materiality-screen`, matForm); }
    catch { /* use static */ }
  }

  async function generateIndex() {
    try { await axios.post(`${API}/api/v1/gri-standards/generate-content-index`, form); }
    catch { /* use static */ }
  }

  const scores = result
    ? [
        { standard: "GRI 1 Foundation", score: result.gri1 },
        { standard: "GRI 2 General", score: result.gri2 },
        { standard: "GRI 3 Material Topics", score: result.gri3 },
        { standard: "GRI 300 Environment", score: result.gri300 },
      ]
    : [
        { standard: "GRI 1 Foundation", score: 82 },
        { standard: "GRI 2 General", score: 67 },
        { standard: "GRI 3 Material Topics", score: 60 },
        { standard: "GRI 300 Environment", score: 54 },
      ];

  const filteredIndex = indexFilter === "All" ? CONTENT_INDEX
    : CONTENT_INDEX.filter(r => r.standard === indexFilter || r.standard.startsWith(indexFilter));

  const disclosedCount = CONTENT_INDEX.filter(r => !r.omission).length;
  const completenessPct = Math.round(disclosedCount / CONTENT_INDEX.length * 100);

  return (
    <div className="min-h-screen bg-white text-black p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">GRI Standards</h1>
          <p className="text-sm text-gray-500 mt-1">Global Reporting Initiative — Universal and Topic Standards (2021 series)</p>
        </div>

        <div className="flex border-b border-gray-200 mb-6 gap-1 flex-wrap">
          {TABS.map((t, i) => (
            <button key={t} onClick={() => setTab(i)}
              className={`px-4 py-2 text-sm transition-colors ${tab === i ? "border-b-2 border-emerald-500 text-black font-semibold" : "text-gray-500 hover:text-black"}`}>
              {t}
            </button>
          ))}
        </div>

        {/* Tab 1 — GRI Assessment */}
        {tab === 0 && (
          <div>
            <Section title="Entity Details">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Inp label="Entity Name" value={form.entity} onChange={e => setForm({ ...form, entity: e.target.value })} />
                <Inp label="Reporting Period" value={form.period} onChange={e => setForm({ ...form, period: e.target.value })} />
                <Sel label="GRI Service Level" value={form.serviceLevel} onChange={e => setForm({ ...form, serviceLevel: e.target.value })}>
                  <option value="with_reference">GRI-referenced</option>
                  <option value="comprehensive">In accordance with GRI</option>
                </Sel>
                <Sel label="Assurance Level" value={form.assurance} onChange={e => setForm({ ...form, assurance: e.target.value })}>
                  <option value="none">None</option>
                  <option value="limited">Limited</option>
                  <option value="reasonable">Reasonable</option>
                </Sel>
              </div>
            </Section>
            <div className="mb-6"><Btn onClick={runAssessment} disabled={loading}>{loading ? "Running..." : "Run GRI Assessment"}</Btn></div>

            <Row>
              <KpiCard label="GRI 1 — Foundation" value={`${scores[0].score}%`} sub="Reporting principles & requirements" />
              <KpiCard label="GRI 2 — General Disclosures" value={`${scores[1].score}%`} sub="Org. profile, governance, strategy" />
              <KpiCard label="GRI 3 — Material Topics" value={`${scores[2].score}%`} sub="Materiality process & management" />
              <KpiCard label="GRI 300 — Environment" value={`${scores[3].score}%`} sub="301-308 topic standards" />
            </Row>
            <div className="mb-6">
              <KpiCard label="Overall GRI Compliance" value={`${result ? result.overall : 66}%`} sub={`${form.serviceLevel === "comprehensive" ? "In accordance with GRI" : "GRI-referenced"} — ${form.assurance} assurance`} accent />
            </div>

            <Section title="Compliance by Standard">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={STANDARD_SCORES} margin={{ top: 4, right: 20, bottom: 60, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="standard" tick={{ fontSize: 10 }} angle={-35} textAnchor="end" interval={0} />
                  <YAxis domain={[0, 100]} tickFormatter={v => `${v}%`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={v => `${v}%`} />
                  <Bar dataKey="score" name="Compliance %" fill={EMERALD} radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>

            <Section title="Disclosure Gaps">
              <div className="space-y-2">
                {[
                  { gap: "GRI 2-29: Approach to stakeholder engagement", severity: "High" },
                  { gap: "GRI 3-3: Management of material topics (all)", severity: "High" },
                  { gap: "GRI 305-3: Scope 3 GHG emissions", severity: "Medium" },
                  { gap: "GRI 304-2: Significant impacts of activities on biodiversity", severity: "Medium" },
                  { gap: "GRI 302-5: Reductions in energy requirements of products and services", severity: "Low" },
                ].map((g, i) => (
                  <div key={i} className="flex justify-between items-center bg-gray-50 rounded p-3 text-sm">
                    <span>{g.gap}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${g.severity === "High" ? "bg-red-100 text-red-700" : g.severity === "Medium" ? "bg-amber-100 text-amber-700" : "bg-gray-100 text-gray-500"}`}>{g.severity}</span>
                  </div>
                ))}
              </div>
            </Section>
          </div>
        )}

        {/* Tab 2 — Material Topics */}
        {tab === 1 && (
          <div>
            <Section title="Materiality Screen Inputs">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Sel label="Sector" value={matForm.sector} onChange={e => setMatForm({ ...matForm, sector: e.target.value })}>
                  {["financials", "energy", "materials", "utilities", "real_estate"].map(s => (
                    <option key={s} value={s}>{s.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase())}</option>
                  ))}
                </Sel>
                <Inp label="Stakeholder Input Count" type="number" value={matForm.stakeholders} onChange={e => setMatForm({ ...matForm, stakeholders: e.target.value })} />
                <div className="flex items-end mb-3"><Btn onClick={runMateriality}>Screen Topics</Btn></div>
              </div>
            </Section>

            <Section title="GRI 3 — 4-Step Materiality Process">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
                {[
                  { step: "1", title: "Understand context", desc: "Activities, business relationships, stakeholder landscape" },
                  { step: "2", title: "Identify actual & potential impacts", desc: "Positive/negative impacts across value chain" },
                  { step: "3", title: "Assess significance of impacts", desc: "Severity (scale, scope, irremediability) & likelihood" },
                  { step: "4", title: "Prioritise material topics", desc: "Select topics, obtain senior approval, engage stakeholders" },
                ].map(s => (
                  <div key={s.step} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="w-7 h-7 rounded-full bg-emerald-600 text-white text-sm font-bold flex items-center justify-center mb-2">{s.step}</div>
                    <div className="font-semibold text-sm mb-1">{s.title}</div>
                    <div className="text-xs text-gray-500">{s.desc}</div>
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Material Topics — Significance Assessment">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {MATERIAL_TOPICS.map((t, i) => (
                  <div key={i} className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
                    <div className="flex justify-between items-start mb-2">
                      <span className="font-medium text-sm">{t.topic}</span>
                      <span className={`text-xs font-bold ${t.score >= 80 ? "text-emerald-600" : t.score >= 65 ? "text-amber-600" : "text-gray-500"}`}>{t.score}</span>
                    </div>
                    <div className="flex gap-2 text-xs">
                      <span className={`px-1.5 py-0.5 rounded ${t.inside ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-400"}`}>Inside org</span>
                      <span className={`px-1.5 py-0.5 rounded ${t.outside ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-400"}`}>Outside org</span>
                    </div>
                    <div className="mt-2 h-1.5 bg-gray-100 rounded-full">
                      <div className="h-1.5 rounded-full bg-emerald-500" style={{ width: `${t.score}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Boundary Assessment Table">
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead><tr className="bg-gray-50 text-xs text-gray-500"><th className="text-left p-3">Topic</th><th className="text-center p-3">Inside Org</th><th className="text-center p-3">Outside Org</th><th className="text-right p-3">Significance</th></tr></thead>
                  <tbody>
                    {MATERIAL_TOPICS.map((t, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="p-3 font-medium">{t.topic}</td>
                        <td className="p-3 text-center">{t.inside ? <span className="text-emerald-600 font-bold">Yes</span> : <span className="text-gray-300">No</span>}</td>
                        <td className="p-3 text-center">{t.outside ? <span className="text-emerald-600 font-bold">Yes</span> : <span className="text-gray-300">No</span>}</td>
                        <td className="p-3 text-right font-mono">{t.score}/100</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          </div>
        )}

        {/* Tab 3 — GRI 300 Environment */}
        {tab === 2 && (
          <div>
            {[
              { num: "301", name: "Materials", pct: 48, metrics: [{ label: "Materials consumed (t)", val: "142,800" }, { label: "Recycled input %", val: "34%" }], omissions: 2 },
              { num: "302", name: "Energy", pct: 72, metrics: [{ label: "Total energy consumption (MWh)", val: "1,124,000" }, { label: "Renewable %", val: "38%" }], omissions: 1 },
              { num: "303", name: "Water", pct: 55, metrics: [{ label: "Water withdrawal (m3)", val: "284,600" }, { label: "Water recycled %", val: "22%" }], omissions: 2 },
              { num: "304", name: "Biodiversity", pct: 31, metrics: [{ label: "Sites in/near protected areas", val: "0" }, { label: "Sig. impacts reported", val: "N/A" }], omissions: 4 },
              { num: "305", name: "Emissions", pct: 68, metrics: [{ label: "Scope 1 (tCO2e)", val: "9,380" }, { label: "Scope 2 (tCO2e)", val: "5,920" }], omissions: 1 },
              { num: "306", name: "Waste", pct: 58, metrics: [{ label: "Total waste (t)", val: "4,820" }, { label: "Diverted from disposal %", val: "68%" }], omissions: 2 },
            ].map(s => (
              <Section key={s.num} title={`GRI ${s.num} — ${s.name}`}>
                <div className="bg-white border border-gray-200 rounded-lg p-4 mb-3">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium">Completeness</span>
                    <span className="text-sm font-bold text-black">{s.pct}%</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full mb-3">
                    <div className="h-2 rounded-full bg-emerald-500 transition-all" style={{ width: `${s.pct}%` }} />
                  </div>
                  <div className="flex gap-6">
                    {s.metrics.map((m, i) => (
                      <div key={i} className="text-xs">
                        <div className="text-gray-500">{m.label}</div>
                        <div className="font-semibold text-black">{m.val}</div>
                      </div>
                    ))}
                    <div className="text-xs">
                      <div className="text-gray-500">Omissions</div>
                      <div className={`font-semibold ${s.omissions > 2 ? "text-red-600" : s.omissions > 0 ? "text-amber-600" : "text-emerald-600"}`}>{s.omissions}</div>
                    </div>
                  </div>
                </div>
              </Section>
            ))}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-4">
              <Section title="Energy Consumption Trend (GRI 302)">
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={ENERGY_TREND}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Legend />
                    <Area type="monotone" dataKey="consumption" name="Total (MWh)" stroke="#0ea5e9" fill="#dbeafe" strokeWidth={2} />
                    <Area type="monotone" dataKey="renewable" name="Renewable (MWh)" stroke={EMERALD} fill="#d1fae5" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </Section>
              <Section title="Waste Composition (GRI 306)">
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={WASTE_PIE} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, value }) => `${name} ${value}%`} labelLine={false}>
                      {WASTE_PIE.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Section>
            </div>

            <Section title="GHG Emissions Trend (GRI 305)">
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={EMISSIONS_TREND}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="scope1" name="Scope 1" stroke="#ef4444" fill="#fee2e2" strokeWidth={2} />
                  <Area type="monotone" dataKey="scope2" name="Scope 2" stroke="#f59e0b" fill="#fef3c7" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </Section>
          </div>
        )}

        {/* Tab 4 — Content Index */}
        {tab === 3 && (
          <div>
            <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
              <div className="flex gap-2 flex-wrap">
                {["All", "GRI 2", "GRI 3", "GRI 302", "GRI 303", "GRI 304", "GRI 305", "GRI 306"].map(f => (
                  <button key={f} onClick={() => setIndexFilter(f)}
                    className={`px-3 py-1 text-xs rounded-full border transition-colors ${indexFilter === f ? "bg-black text-white border-black" : "border-gray-200 text-gray-600 hover:border-gray-400"}`}>
                    {f}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-3">
                <div className="text-xs text-gray-500">Completeness: <span className="font-bold text-black">{completenessPct}%</span></div>
                <span className="px-3 py-1 text-xs bg-gray-100 text-gray-500 rounded border border-gray-200 cursor-not-allowed">Export Index</span>
              </div>
            </div>
            <div className="h-2 bg-gray-100 rounded-full mb-4">
              <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${completenessPct}%` }} />
            </div>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs text-gray-500">
                    <th className="text-left p-3">Standard</th>
                    <th className="text-left p-3">Disc. No.</th>
                    <th className="text-left p-3">Disclosure Title</th>
                    <th className="text-left p-3">Location</th>
                    <th className="text-left p-3">Omission Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredIndex.map((row, i) => (
                    <tr key={i} className="border-t border-gray-100 hover:bg-gray-50">
                      <td className="p-3 font-medium text-emerald-700">{row.standard}</td>
                      <td className="p-3 font-mono text-xs">{row.disc}</td>
                      <td className="p-3">{row.title}</td>
                      <td className="p-3 text-gray-500">{row.location}</td>
                      <td className="p-3 text-xs text-amber-600">{row.omission || <span className="text-emerald-600">—</span>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 5 — Reference */}
        {tab === 4 && (
          <div>
            <Section title="GRI Universal Standards Structure">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {[
                  { id: "GRI 1", title: "Foundation 2021", type: "Universal", desc: "Requirements and principles for using the GRI Standards. All organisations must comply with GRI 1." },
                  { id: "GRI 2", title: "General Disclosures 2021", type: "Universal", desc: "Information about reporting organization: profile, governance, strategy, stakeholder engagement, reporting practices." },
                  { id: "GRI 3", title: "Material Topics 2021", type: "Universal", desc: "Requirements for determining material topics, managing them, and reporting on them. Foundation of topic standard reporting." },
                ].map(s => (
                  <div key={s.id} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="text-xs text-emerald-600 font-bold mb-1">{s.id} — {s.type}</div>
                    <div className="font-semibold text-sm mb-2">{s.title}</div>
                    <div className="text-xs text-gray-500">{s.desc}</div>
                  </div>
                ))}
              </div>
              <div className="bg-gray-50 rounded-lg p-4 text-xs text-gray-600 mb-6">
                <span className="font-semibold">Topic Standards</span> — GRI 200 (Economic), GRI 300 (Environmental), GRI 400 (Social). Organisations select relevant topic standards based on materiality assessment results. Each topic standard includes management disclosures (3-3) and topic-specific disclosures.
              </div>
            </Section>
            <Section title="GRI Service Levels">
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead><tr className="bg-gray-50 text-xs text-gray-500"><th className="text-left p-3">Service Level</th><th className="text-left p-3">Requirements</th><th className="text-left p-3">Assurance</th><th className="text-left p-3">Content Index</th></tr></thead>
                  <tbody>
                    {SERVICE_LEVELS.map((s, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="p-3 font-medium">{s.level}</td>
                        <td className="p-3 text-gray-600">{s.req}</td>
                        <td className="p-3 text-gray-500">{s.assurance}</td>
                        <td className="p-3">{s.index}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <Section title="GRI 300 Environmental Standards Overview">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {[
                  { std: "GRI 301", name: "Materials", focus: "Materials used, recycled inputs, reclaimed products" },
                  { std: "GRI 302", name: "Energy", focus: "Consumption, intensity, reduction, renewables" },
                  { std: "GRI 303", name: "Water & Effluents", focus: "Withdrawal, discharge, consumption, water-related impacts" },
                  { std: "GRI 304", name: "Biodiversity", focus: "Sites near protected areas, significant impacts, species affected" },
                  { std: "GRI 305", name: "Emissions", focus: "Scope 1/2/3 GHG, intensity, reduction, ODS" },
                  { std: "GRI 306", name: "Waste", focus: "Waste generated, diverted, directed to disposal" },
                  { std: "GRI 308", name: "Supplier Environmental Assessment", focus: "Supplier screening, negative impacts, supplier assessments" },
                ].map(s => (
                  <div key={s.std} className="bg-gray-50 rounded-lg p-3 text-xs">
                    <div className="font-bold text-emerald-700">{s.std} — {s.name}</div>
                    <div className="text-gray-500 mt-1">{s.focus}</div>
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
