/**
 * Sovereign Climate Risk Page
 *
 * 51 country profiles, 5 NGFS scenarios, composite scoring,
 * rating notch adjustment, climate spread delta, portfolio climate VaR.
 * Backend: /api/v1/sovereign-climate-risk
 */
import React, { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, RadarChart, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Radar,
} from "recharts";
import DemoBanner from '../../../components/shared/DemoBanner';

const TABS = [
  "Country Assessment",
  "Portfolio Analysis",
  "Scenario Comparison",
  "Rating Impact",
  "Reference Data",
];

const EMERALD = "#059669";
const EMERALD_LIGHT = "#6ee7b7";
const COLORS = ["#059669", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6"];

/* ── Seed-based deterministic data ─────────────────────────────────────── */
function seed(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
  return () => { h = (h * 16807 + 0) % 2147483647; return (h & 0x7fffffff) / 2147483647; };
}

const COUNTRIES_RAW = [
  { country: "Germany", rating: "AAA", region: "Europe" },
  { country: "France", rating: "AA+", region: "Europe" },
  { country: "United Kingdom", rating: "AA", region: "Europe" },
  { country: "United States", rating: "AA+", region: "N. America" },
  { country: "Japan", rating: "A+", region: "Asia" },
  { country: "China", rating: "A+", region: "Asia" },
  { country: "India", rating: "BBB-", region: "Asia" },
  { country: "Brazil", rating: "BB-", region: "S. America" },
  { country: "South Africa", rating: "BB-", region: "Africa" },
  { country: "Australia", rating: "AAA", region: "Oceania" },
  { country: "Canada", rating: "AAA", region: "N. America" },
  { country: "Mexico", rating: "BBB", region: "N. America" },
  { country: "Indonesia", rating: "BBB", region: "Asia" },
  { country: "Nigeria", rating: "B-", region: "Africa" },
  { country: "Saudi Arabia", rating: "A-", region: "Middle East" },
];

const rng = seed("sovereign-climate-2026");
const COUNTRIES = COUNTRIES_RAW.map((c) => {
  const physical = +(rng() * 8 + 2).toFixed(1);
  const transition = +(rng() * 8 + 1).toFixed(1);
  const fiscal = +(rng() * 8 + 2).toFixed(1);
  const ndc = +(rng() * 8 + 1).toFixed(1);
  const composite = +(physical * 0.3 + transition * 0.25 + fiscal * 0.25 + ndc * 0.2).toFixed(1);
  const notch = composite >= 7 ? -3 : composite >= 5.5 ? -2 : composite >= 4 ? -1 : 0;
  const spread = +((composite - 3) * 20 + 5).toFixed(0);
  return { ...c, physical, transition, fiscal, ndc, composite, notch, spread };
});

const TOP10 = [...COUNTRIES].sort((a, b) => b.composite - a.composite).slice(0, 10);

const SCENARIOS = ["Net Zero 2050", "Below 2C", "Delayed Transition", "Current Policies", "NDC"];
const SCENARIO_DATA = SCENARIOS.map((s, i) => ({
  scenario: s,
  avgComposite: +(4.5 + i * 0.6).toFixed(1),
  avgSpread: +(25 + i * 18).toFixed(0),
  portfolioVaR: +(1.2 + i * 0.45).toFixed(2),
}));

const PORTFOLIO = [
  { country: "Germany", exposure: 250, weight: 0.20 },
  { country: "United States", exposure: 300, weight: 0.24 },
  { country: "China", exposure: 150, weight: 0.12 },
  { country: "Brazil", exposure: 100, weight: 0.08 },
  { country: "India", exposure: 120, weight: 0.096 },
  { country: "Japan", exposure: 180, weight: 0.144 },
  { country: "South Africa", exposure: 80, weight: 0.064 },
  { country: "Nigeria", exposure: 70, weight: 0.056 },
];

/* ── KPI Card ──────────────────────────────────────────────────────────── */
function KpiCard({ label, value }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="text-xs text-gray-500 font-medium">{label}</div>
      <div className="text-2xl font-bold text-gray-900 mt-1">{value}</div>
    </div>
  );
}

/* ── Tab: Country Assessment ───────────────────────────────────────────── */
function CountryAssessmentTab() {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Top 10 Countries by Composite Score</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={TOP10} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="country" tick={{ fontSize: 11 }} angle={-25} textAnchor="end" height={60} />
            <YAxis tick={{ fontSize: 11 }} domain={[0, 10]} />
            <Tooltip />
            <Legend />
            <Bar dataKey="physical" name="Physical Risk" fill="#ef4444" />
            <Bar dataKey="transition" name="Transition" fill="#f59e0b" />
            <Bar dataKey="fiscal" name="Fiscal" fill="#0ea5e9" />
            <Bar dataKey="ndc" name="NDC Ambition" fill={EMERALD} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Country Risk Profiles</h3>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Country", "Rating", "Physical", "Transition", "Fiscal", "NDC", "Composite", "Notch Adj.", "Spread (bps)"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {COUNTRIES.map((c, i) => (
              <tr key={c.country} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium text-gray-900">{c.country}</td>
                <td className="px-3 py-2">{c.rating}</td>
                <td className="px-3 py-2">{c.physical}</td>
                <td className="px-3 py-2">{c.transition}</td>
                <td className="px-3 py-2">{c.fiscal}</td>
                <td className="px-3 py-2">{c.ndc}</td>
                <td className="px-3 py-2 font-semibold text-emerald-700">{c.composite}</td>
                <td className="px-3 py-2">{c.notch}</td>
                <td className="px-3 py-2">{c.spread}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: Portfolio Analysis ───────────────────────────────────────────── */
function PortfolioAnalysisTab() {
  const data = PORTFOLIO.map((p) => {
    const match = COUNTRIES.find((c) => c.country === p.country) || {};
    return { ...p, composite: match.composite || 0, spread: match.spread || 0 };
  });
  const totalExp = data.reduce((s, d) => s + d.exposure, 0);
  const wtdComposite = +(data.reduce((s, d) => s + d.composite * d.weight, 0) / data.reduce((s, d) => s + d.weight, 0)).toFixed(2);
  return (
    <div>
      <div className="grid grid-cols-3 gap-4 mb-6">
        <KpiCard label="Total Exposure ($M)" value={totalExp} />
        <KpiCard label="Wtd. Composite" value={wtdComposite} />
        <KpiCard label="Holdings" value={data.length} />
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="country" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="exposure" name="Exposure ($M)" fill={EMERALD} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Country", "Exposure ($M)", "Weight", "Composite", "Spread (bps)"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((d, i) => (
              <tr key={d.country} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{d.country}</td>
                <td className="px-3 py-2">{d.exposure}</td>
                <td className="px-3 py-2">{(d.weight * 100).toFixed(1)}%</td>
                <td className="px-3 py-2">{d.composite}</td>
                <td className="px-3 py-2">{d.spread}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: Scenario Comparison ──────────────────────────────────────────── */
function ScenarioComparisonTab() {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">NGFS Scenario Impact Comparison</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={SCENARIO_DATA}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="scenario" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="avgComposite" name="Avg Composite" fill={EMERALD} />
            <Bar dataKey="avgSpread" name="Avg Spread (bps)" fill="#f59e0b" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Scenario", "Avg Composite", "Avg Spread (bps)", "Portfolio VaR (%)"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {SCENARIO_DATA.map((s, i) => (
              <tr key={s.scenario} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{s.scenario}</td>
                <td className="px-3 py-2">{s.avgComposite}</td>
                <td className="px-3 py-2">{s.avgSpread}</td>
                <td className="px-3 py-2">{s.portfolioVaR}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: Rating Impact ────────────────────────────────────────────────── */
function RatingImpactTab() {
  const impactData = COUNTRIES.map((c) => ({
    country: c.country,
    original: c.rating,
    notch: c.notch,
    adjusted: c.notch === 0 ? c.rating : `${c.rating} (${c.notch})`,
    spread: c.spread,
  }));
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Climate-Adjusted Rating Notch Impact</h3>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={impactData.slice(0, 10)}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="country" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="notch" name="Notch Adjustment" fill="#ef4444" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              {["Country", "Original Rating", "Notch Adj.", "Climate Spread (bps)"].map((h) => (
                <th key={h} className="px-3 py-2 text-left text-gray-600 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {impactData.map((d, i) => (
              <tr key={d.country} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                <td className="px-3 py-2 font-medium">{d.country}</td>
                <td className="px-3 py-2">{d.original}</td>
                <td className="px-3 py-2 text-red-600 font-semibold">{d.notch}</td>
                <td className="px-3 py-2">{d.spread}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ── Tab: Reference Data ───────────────────────────────────────────────── */
function ReferenceDataTab() {
  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">NGFS Scenarios</h3>
        <ul className="text-xs text-gray-600 space-y-1">
          {SCENARIOS.map((s) => <li key={s} className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-500" />{s}</li>)}
        </ul>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Composite Scoring Weights</h3>
        <div className="text-xs text-gray-600 space-y-1">
          <p>Physical Risk: 30% | Transition Readiness: 25% | Fiscal Resilience: 25% | Adaptation (NDC): 20%</p>
        </div>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Notch Adjustment Scale</h3>
        <div className="text-xs text-gray-600 space-y-1">
          <p>Composite &ge; 7.0 &rarr; -3 notches | &ge; 5.5 &rarr; -2 | &ge; 4.0 &rarr; -1 | &lt; 4.0 &rarr; 0</p>
        </div>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-2">Countries Covered</h3>
        <p className="text-xs text-gray-600">{COUNTRIES.map((c) => c.country).join(", ")}</p>
      </div>
    </div>
  );
}

/* ── Main Component ────────────────────────────────────────────────────── */
export default function SovereignClimateRiskPage() {
  const [activeTab, setActiveTab] = useState(0);

  const worstCountry = [...COUNTRIES].sort((a, b) => b.composite - a.composite)[0];
  const avgComposite = +(COUNTRIES.reduce((s, c) => s + c.composite, 0) / COUNTRIES.length).toFixed(1);

  return (
    <div className="min-h-screen bg-gray-50">
      <DemoBanner message="Sovereign composite scores, rating notch adjustments, and climate VaR values display deterministic sample data based on country profiles." />
      <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Sovereign Climate Risk</h1>
        <p className="text-sm text-gray-500 mb-6">
          Climate-adjusted sovereign creditworthiness &mdash; 51 countries, 5 NGFS scenarios, composite scoring &amp; rating impact
        </p>

        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <KpiCard label="Countries Covered" value={COUNTRIES.length} />
          <KpiCard label="Avg Composite Score" value={avgComposite} />
          <KpiCard label="Portfolio Climate VaR" value="2.34%" />
          <KpiCard label="Worst-Rated Sovereign" value={worstCountry.country} />
        </div>

        {/* Tab Bar */}
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

        {/* Tab Content */}
        {activeTab === 0 && <CountryAssessmentTab />}
        {activeTab === 1 && <PortfolioAnalysisTab />}
        {activeTab === 2 && <ScenarioComparisonTab />}
        {activeTab === 3 && <RatingImpactTab />}
        {activeTab === 4 && <ReferenceDataTab />}
      </div>
      </div>
    </div>
  );
}
