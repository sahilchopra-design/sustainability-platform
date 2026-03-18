/**
 * SEC Climate Disclosure Page
 *
 * Reg S-K Items 1501-1505, Reg S-X 14-02,
 * attestation requirements, safe harbor, cross-framework mapping.
 * Backend: /api/v1/sec-climate
 */
import React, { useState } from "react";
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, PieChart, Pie, Cell,
} from "recharts";

const TABS = [
  "Filer Assessment",
  "GHG Disclosure",
  "Financial Effects",
  "Materiality",
  "Cross-Framework",
];

const EMERALD = "#059669";
const COLORS = ["#059669", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6"];

/* ── Deterministic seed ────────────────────────────────────────────────── */
function seed(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
  return () => { h = (h * 16807 + 0) % 2147483647; return (h & 0x7fffffff) / 2147483647; };
}

const rng = seed("sec-climate-2026");

const FILER_CATEGORIES = [
  { category: "LAF", label: "Large Accelerated Filer", threshold: "$700M+ float", phase: "FY 2026" },
  { category: "AF", label: "Accelerated Filer", threshold: "$75M-$700M float", phase: "FY 2027" },
  { category: "NAF", label: "Non-Accelerated Filer", threshold: "<$75M float", phase: "FY 2028" },
  { category: "SRC", label: "Smaller Reporting Co.", threshold: "<$250M revenue", phase: "FY 2028" },
  { category: "EGC", label: "Emerging Growth Co.", threshold: "IPO <5 years", phase: "Exempt" },
];

const REG_SK_ITEMS = [
  { item: "1501", title: "Governance", score: +(rng() * 40 + 60).toFixed(0) },
  { item: "1502", title: "Strategy", score: +(rng() * 40 + 50).toFixed(0) },
  { item: "1503", title: "Risk Management", score: +(rng() * 40 + 55).toFixed(0) },
  { item: "1504", title: "Targets & Goals", score: +(rng() * 40 + 45).toFixed(0) },
  { item: "1505", title: "GHG Emissions", score: +(rng() * 40 + 40).toFixed(0) },
];

const RADAR_DATA = REG_SK_ITEMS.map((r) => ({ subject: r.title, score: Number(r.score), fullMark: 100 }));

const DISCLOSURES = [
  { req: "Board oversight of climate risks", item: "1501", status: "Compliant" },
  { req: "Management role in climate risk", item: "1501", status: "Compliant" },
  { req: "Climate-related risks & opportunities", item: "1502", status: "Partial" },
  { req: "Impact on strategy & business model", item: "1502", status: "Partial" },
  { req: "Risk identification & assessment", item: "1503", status: "Compliant" },
  { req: "Integration into overall risk mgmt", item: "1503", status: "Gap" },
  { req: "GHG reduction targets", item: "1504", status: "Partial" },
  { req: "Transition plan disclosure", item: "1504", status: "Gap" },
  { req: "Scope 1 emissions", item: "1505", status: "Compliant" },
  { req: "Scope 2 emissions", item: "1505", status: "Compliant" },
  { req: "Scope 3 emissions (if material)", item: "1505", status: "Gap" },
  { req: "GHG attestation (limited)", item: "1505", status: "Partial" },
];

const STATUS_COLORS = { Compliant: "text-emerald-600 bg-emerald-50", Partial: "text-amber-600 bg-amber-50", Gap: "text-red-600 bg-red-50" };

const FINANCIAL_EFFECTS = [
  { category: "Severe Weather Events", amount: 12.4, pctRevenue: 1.8, material: true },
  { category: "Transition Activities", amount: 8.7, pctRevenue: 1.3, material: true },
  { category: "Carbon Pricing Impact", amount: 3.2, pctRevenue: 0.5, material: false },
  { category: "Physical Risk Provisions", amount: 5.1, pctRevenue: 0.7, material: false },
  { category: "Estimates & Assumptions", amount: 2.9, pctRevenue: 0.4, material: false },
];

const CROSS_FRAMEWORK = [
  { secItem: "1501 Governance", tcfd: "Governance a/b", issb: "IFRS S2 6-7", csrd: "ESRS 2 GOV-1" },
  { secItem: "1502 Strategy", tcfd: "Strategy a/b/c", issb: "IFRS S2 8-14", csrd: "ESRS E1-1" },
  { secItem: "1503 Risk Mgmt", tcfd: "Risk Mgmt a/b/c", issb: "IFRS S2 15-16", csrd: "ESRS 2 IRO-1" },
  { secItem: "1504 Targets", tcfd: "Metrics c", issb: "IFRS S2 23-24", csrd: "ESRS E1-4" },
  { secItem: "1505 GHG", tcfd: "Metrics a/b", issb: "IFRS S2 17-22", csrd: "ESRS E1-6" },
];

function KpiCard({ label, value }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="text-xs text-gray-500 font-medium">{label}</div>
      <div className="text-2xl font-bold text-gray-900 mt-1">{value}</div>
    </div>
  );
}

/* ── Tab: Filer Assessment ─────────────────────────────────────────────── */
function FilerAssessmentTab() {
  const overall = +(REG_SK_ITEMS.reduce((s, r) => s + Number(r.score), 0) / REG_SK_ITEMS.length).toFixed(0);
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Compliance Radar &mdash; Reg S-K Items</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart data={RADAR_DATA}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
            <Radar name="Score" dataKey="score" stroke={EMERALD} fill={EMERALD} fillOpacity={0.3} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Disclosure Requirements</h3>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Requirement", "Reg S-K Item", "Status"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {DISCLOSURES.map((d, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2">{d.req}</td>
                <td className="px-3 py-2">{d.item}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[d.status]}`}>{d.status}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: GHG Disclosure ───────────────────────────────────────────────── */
function GHGDisclosureTab() {
  const ghgData = [
    { scope: "Scope 1", value: 42500 },
    { scope: "Scope 2 (Location)", value: 28300 },
    { scope: "Scope 2 (Market)", value: 24100 },
    { scope: "Scope 3 (Material)", value: 185000 },
  ];
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">GHG Emissions Summary (tCO2e)</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={ghgData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="scope" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => v.toLocaleString() + " tCO2e"} />
            <Bar dataKey="value" name="Emissions" fill={EMERALD}>
              {ghgData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Attestation Readiness</h3>
        <div className="space-y-2 text-xs text-gray-600">
          <p><span className="font-medium">Limited Assurance (AT-C 210):</span> Required for LAF from FY 2026</p>
          <p><span className="font-medium">Reasonable Assurance (AT-C 205):</span> Required for LAF from FY 2028</p>
          <p><span className="font-medium">Current Status:</span> <span className="text-amber-600 font-medium">In Progress</span> &mdash; Limited assurance provider engaged</p>
        </div>
      </div>
    </div>
  );
}

/* ── Tab: Financial Effects ────────────────────────────────────────────── */
function FinancialEffectsTab() {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Reg S-X 14-02 Financial Effects ($M)</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={FINANCIAL_EFFECTS}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="category" tick={{ fontSize: 10 }} angle={-15} textAnchor="end" height={60} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="amount" name="Amount ($M)" fill={EMERALD} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Category", "Amount ($M)", "% Revenue", "Material (>1%)"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {FINANCIAL_EFFECTS.map((f, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{f.category}</td>
                <td className="px-3 py-2">{f.amount}</td>
                <td className="px-3 py-2">{f.pctRevenue}%</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${f.material ? "text-red-600 bg-red-50" : "text-gray-500 bg-gray-100"}`}>
                    {f.material ? "Yes" : "No"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: Materiality ──────────────────────────────────────────────────── */
function MaterialityTab() {
  const materialityData = [
    { topic: "Physical Risk (Acute)", likelihood: "High", impact: "High", material: true },
    { topic: "Physical Risk (Chronic)", likelihood: "Medium", impact: "High", material: true },
    { topic: "Transition Risk (Policy)", likelihood: "High", impact: "Medium", material: true },
    { topic: "Transition Risk (Market)", likelihood: "Medium", impact: "Medium", material: false },
    { topic: "Transition Risk (Technology)", likelihood: "Low", impact: "High", material: false },
    { topic: "Transition Risk (Reputation)", likelihood: "Medium", impact: "Low", material: false },
  ];
  const pieData = [
    { name: "Material", value: materialityData.filter((m) => m.material).length },
    { name: "Non-Material", value: materialityData.filter((m) => !m.material).length },
  ];
  return (
    <div>
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Materiality Split</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                {pieData.map((_, i) => <Cell key={i} fill={i === 0 ? EMERALD : "#e5e7eb"} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Materiality Threshold</h3>
          <p className="text-xs text-gray-600 mb-2">Per Reg S-X 14-02, financial effects are material if they exceed 1% of total revenue or the relevant line item.</p>
          <p className="text-xs text-gray-600">Items 1502-1503 require disclosure of material climate risks and their integration into strategy and risk management processes.</p>
        </div>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Topic", "Likelihood", "Impact", "Material"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {materialityData.map((m, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{m.topic}</td>
                <td className="px-3 py-2">{m.likelihood}</td>
                <td className="px-3 py-2">{m.impact}</td>
                <td className="px-3 py-2">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${m.material ? "text-emerald-600 bg-emerald-50" : "text-gray-500 bg-gray-100"}`}>
                    {m.material ? "Yes" : "No"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: Cross-Framework ──────────────────────────────────────────────── */
function CrossFrameworkTab() {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">SEC &harr; TCFD / ISSB S2 / CSRD Mapping</h3>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["SEC Reg S-K", "TCFD", "ISSB S2", "CSRD ESRS"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CROSS_FRAMEWORK.map((c, i) => (
              <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{c.secItem}</td>
                <td className="px-3 py-2">{c.tcfd}</td>
                <td className="px-3 py-2">{c.issb}</td>
                <td className="px-3 py-2">{c.csrd}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Filer Categories &amp; Phase-In</h3>
        <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto mt-2">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                {["Code", "Category", "Threshold", "Effective"].map((h) => (
                  <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {FILER_CATEGORIES.map((f, i) => (
                <tr key={f.category} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                  <td className="px-3 py-2 font-medium">{f.category}</td>
                  <td className="px-3 py-2">{f.label}</td>
                  <td className="px-3 py-2">{f.threshold}</td>
                  <td className="px-3 py-2">{f.phase}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ── Main Component ────────────────────────────────────────────────────── */
export default function SECClimatePage() {
  const [activeTab, setActiveTab] = useState(0);

  const overallScore = +(REG_SK_ITEMS.reduce((s, r) => s + Number(r.score), 0) / REG_SK_ITEMS.length).toFixed(0);
  const gaps = DISCLOSURES.filter((d) => d.status === "Gap").length;

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">SEC Climate Disclosure</h1>
        <p className="text-sm text-gray-500 mb-6">
          Reg S-K Items 1501-1505, Reg S-X 14-02 financial effects, attestation readiness &amp; cross-framework mapping
        </p>

        <div className="grid grid-cols-4 gap-4 mb-6">
          <KpiCard label="Filer Category" value="LAF" />
          <KpiCard label="Compliance Score" value={`${overallScore}%`} />
          <KpiCard label="GHG Readiness" value="72%" />
          <KpiCard label="Disclosure Gaps" value={gaps} />
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

        {activeTab === 0 && <FilerAssessmentTab />}
        {activeTab === 1 && <GHGDisclosureTab />}
        {activeTab === 2 && <FinancialEffectsTab />}
        {activeTab === 3 && <MaterialityTab />}
        {activeTab === 4 && <CrossFrameworkTab />}
      </div>
    </div>
  );
}
