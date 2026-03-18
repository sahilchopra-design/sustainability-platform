/**
 * PCAF Sovereign Debt Page
 *
 * 5 tabs: Sovereign Assessment | Portfolio View | Attribution Calculator |
 *         NDC Alignment | Reference
 * Backend: /api/v1/pcaf-sovereign
 * Standard: PCAF Global GHG Accounting and Reporting Standard Part D (2022)
 */
import React, { useState, useMemo } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";

const API = process.env.REACT_APP_API_URL || "";
const EMERALD = "#10b981";
const COLORS = ["#10b981", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6", "#64748b", "#06b6d4", "#f97316", "#a855f7", "#ec4899"];

const TABS = ["Sovereign Assessment", "Portfolio View", "Attribution Calculator", "NDC Alignment", "Reference"];

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

/* ── Country profiles ───────────────────────────────────────────────────── */
const COUNTRIES = [
  { code: "DEU", name: "Germany", region: "Europe", gdp: 4072, govDebt: 2750, ghgMt: 675, ndcTarget: -55, ndcTrajectory: -38, rating: "AAA", dqs: 1 },
  { code: "FRA", name: "France", region: "Europe", gdp: 2782, govDebt: 3020, ghgMt: 408, ndcTarget: -55, ndcTrajectory: -42, rating: "AA", dqs: 1 },
  { code: "GBR", name: "United Kingdom", region: "Europe", gdp: 3070, govDebt: 2560, ghgMt: 435, ndcTarget: -68, ndcTrajectory: -47, rating: "AA", dqs: 1 },
  { code: "USA", name: "United States", region: "Americas", gdp: 25460, govDebt: 31400, ghgMt: 5686, ndcTarget: -50, ndcTrajectory: -26, rating: "AA+", dqs: 1 },
  { code: "JPN", name: "Japan", region: "Asia-Pacific", gdp: 4231, govDebt: 9800, ghgMt: 1135, ndcTarget: -46, ndcTrajectory: -22, rating: "A+", dqs: 1 },
  { code: "CHN", name: "China", region: "Asia-Pacific", gdp: 17960, govDebt: 10200, ghgMt: 11470, ndcTarget: -65, ndcTrajectory: -40, rating: "A+", dqs: 2 },
  { code: "IND", name: "India", region: "Asia-Pacific", gdp: 3385, govDebt: 2800, ghgMt: 2960, ndcTarget: -45, ndcTrajectory: -28, rating: "BBB-", dqs: 2 },
  { code: "BRA", name: "Brazil", region: "Americas", gdp: 1920, govDebt: 1580, ghgMt: 2430, ndcTarget: -50, ndcTrajectory: -18, rating: "BB-", dqs: 3 },
  { code: "ZAF", name: "South Africa", region: "Africa", gdp: 399, govDebt: 265, ghgMt: 478, ndcTarget: -42, ndcTrajectory: -10, rating: "BB-", dqs: 3 },
  { code: "IDN", name: "Indonesia", region: "Asia-Pacific", gdp: 1319, govDebt: 570, ghgMt: 1022, ndcTarget: -41, ndcTrajectory: -14, rating: "BBB", dqs: 3 },
  { code: "MEX", name: "Mexico", region: "Americas", gdp: 1293, govDebt: 720, ghgMt: 697, ndcTarget: -22, ndcTrajectory: -8, rating: "BBB-", dqs: 3 },
  { code: "SAU", name: "Saudi Arabia", region: "Middle East", gdp: 1061, govDebt: 290, ghgMt: 723, ndcTarget: -30, ndcTrajectory: -5, rating: "A", dqs: 2 },
  { code: "TUR", name: "Turkey", region: "Europe", gdp: 905, govDebt: 450, ghgMt: 520, ndcTarget: -21, ndcTrajectory: -4, rating: "B+", dqs: 3 },
  { code: "AUS", name: "Australia", region: "Asia-Pacific", gdp: 1693, govDebt: 820, ghgMt: 499, ndcTarget: -43, ndcTrajectory: -30, rating: "AAA", dqs: 1 },
  { code: "CAN", name: "Canada", region: "Americas", gdp: 2140, govDebt: 1480, ghgMt: 670, ndcTarget: -40, ndcTrajectory: -27, rating: "AAA", dqs: 1 },
];

function getCountry(code) { return COUNTRIES.find(c => c.code === code) || COUNTRIES[0]; }

function calcAttribution(outstanding, govDebt) {
  return outstanding / govDebt;
}

function calcFinancedEmissions(attributionFactor, ghgMt) {
  return attributionFactor * ghgMt * 1e6; // MtCO2e → tCO2e
}

function ndcAlignmentStatus(country) {
  const gap = country.ndcTarget - country.ndcTrajectory;
  if (gap <= 8) return { status: "Aligned", cls: "bg-emerald-100 text-emerald-800" };
  if (gap <= 20) return { status: "Partial", cls: "bg-amber-100 text-amber-800" };
  return { status: "Misaligned", cls: "bg-red-100 text-red-800" };
}

const DQS_DESC = [
  { dqs: 1, label: "Primary data", desc: "Country-specific, year-specific national inventory data directly from national GHG registry" },
  { dqs: 2, label: "Proxy primary data", desc: "National inventory data with minor adjustments or 1-year lag" },
  { dqs: 3, label: "Proxy secondary data", desc: "Regional average or interpolated inventory data from third-party sources" },
  { dqs: 4, label: "Modelled data", desc: "Estimated using economic or emissions intensity models; lowest confidence" },
];

/* ── Portfolio seed data ─────────────────────────────────────────────────── */
const PORTFOLIO_COUNTRIES = ["DEU", "FRA", "GBR", "USA", "JPN", "CHN", "IND", "BRA"];
const portfolioData = PORTFOLIO_COUNTRIES.map((code, i) => {
  const c = getCountry(code);
  const r = rng(i * 7 + 11);
  const outstanding = Math.round((r() * 400 + 100) * 10) / 10;
  const af = calcAttribution(outstanding, c.govDebt);
  const fe = Math.round(calcFinancedEmissions(af, c.ghgMt));
  const ndcInfo = ndcAlignmentStatus(c);
  return { ...c, outstanding, af: +af.toFixed(6), fe, ndcStatus: ndcInfo.status, ndcCls: ndcInfo.cls };
});

const regionPie = (() => {
  const map = {};
  portfolioData.forEach(p => { map[p.region] = (map[p.region] || 0) + p.outstanding; });
  return Object.entries(map).map(([name, value]) => ({ name, value: +value.toFixed(1) }));
})();

export default function PCAFSovereignPage() {
  const [tab, setTab] = useState(0);

  // Tab 1
  const [form, setForm] = useState({ entity: "Meridian Capital Group", country: "DEU", outstanding: "250", lulucf: false });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  // Tab 3
  const [attrForm, setAttrForm] = useState({ outstanding: "250", govDebt: "2750", ghgMt: "675", dqs: "1" });

  const country = getCountry(form.country);
  const af = calcAttribution(Number(form.outstanding), country.govDebt);
  const fe = calcFinancedEmissions(af, country.ghgMt);
  const intensity = Number(form.outstanding) > 0 ? fe / Number(form.outstanding) : 0;
  const ndcInfo = ndcAlignmentStatus(country);
  const climateScore = Math.round(
    (country.ndcTarget / 100) * 40 +
    (country.dqs === 1 ? 30 : country.dqs === 2 ? 20 : 10) +
    30 * (1 - Math.abs(country.ndcTarget - country.ndcTrajectory) / 100)
  );

  async function runAssessment() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/pcaf-sovereign/assess`, form);
      setResult(res.data);
    } catch { setResult(null); }
    finally { setLoading(false); }
  }

  // Tab 3 live calc
  const attrAF = Number(attrForm.outstanding) > 0 && Number(attrForm.govDebt) > 0
    ? calcAttribution(Number(attrForm.outstanding), Number(attrForm.govDebt) * 1000) // debt in €bn → €M
    : 0;
  const attrFE = calcFinancedEmissions(attrAF, Number(attrForm.ghgMt));

  const ndcTop10 = COUNTRIES.slice(0, 10).map(c => ({
    name: c.name.split(" ")[0],
    target: Math.abs(c.ndcTarget),
    trajectory: Math.abs(c.ndcTrajectory),
  }));

  return (
    <div className="min-h-screen bg-white text-black p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">PCAF Sovereign Debt Emissions</h1>
          <p className="text-sm text-gray-500 mt-1">PCAF Global GHG Accounting and Reporting Standard — Part D: Sovereign Debt (2022)</p>
        </div>

        <div className="flex border-b border-gray-200 mb-6 gap-1 flex-wrap">
          {TABS.map((t, i) => (
            <button key={t} onClick={() => setTab(i)}
              className={`px-4 py-2 text-sm transition-colors ${tab === i ? "border-b-2 border-emerald-500 text-black font-semibold" : "text-gray-500 hover:text-black"}`}>
              {t}
            </button>
          ))}
        </div>

        {/* Tab 1 — Sovereign Assessment */}
        {tab === 0 && (
          <div>
            <Section title="Assessment Inputs">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Inp label="FI Entity Name" value={form.entity} onChange={e => setForm({ ...form, entity: e.target.value })} />
                <Sel label="Country" value={form.country} onChange={e => setForm({ ...form, country: e.target.value })}>
                  {COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
                </Sel>
                <Inp label="Outstanding Amount (EUR M)" type="number" value={form.outstanding} onChange={e => setForm({ ...form, outstanding: e.target.value })} />
                <div className="mb-3 flex items-end">
                  <label className="flex items-center gap-2 cursor-pointer text-sm text-gray-700">
                    <input type="checkbox" checked={form.lulucf} onChange={e => setForm({ ...form, lulucf: e.target.checked })} className="w-4 h-4 accent-emerald-500" />
                    Apply LULUCF adjustment
                  </label>
                </div>
              </div>
            </Section>
            <div className="mb-6"><Btn onClick={runAssessment} disabled={loading}>{loading ? "Running..." : "Run Sovereign Assessment"}</Btn></div>

            <Row>
              <KpiCard label="Attribution Factor" value={af.toFixed(6)} sub={`Outstanding / Government Debt`} />
              <KpiCard label="Financed Emissions" value={`${(fe / 1000).toFixed(1)}k tCO2e`} sub="PCAF Part D attribution" accent />
              <KpiCard label="Emissions Intensity" value={`${(intensity / 1000).toFixed(1)}k tCO2e/EUR M`} sub="Per EUR M outstanding" />
              <KpiCard label="PCAF DQS" value={`${country.dqs}/4`} sub={DQS_DESC.find(d => d.dqs === country.dqs)?.label} />
            </Row>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              <Section title="NDC Alignment">
                <div className="bg-white border border-gray-200 rounded-lg p-5">
                  <div className="flex items-center gap-3 mb-4">
                    <span className={`px-4 py-1.5 rounded-full font-semibold text-sm ${ndcInfo.cls}`}>{ndcInfo.status}</span>
                    <span className="text-sm text-gray-500">{country.name} NDC Assessment</span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-gray-500">NDC 2030 target</span><span className="font-medium">{country.ndcTarget}% vs 1990</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">Current trajectory</span><span className="font-medium">{country.ndcTrajectory}% vs 1990</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">Gap</span><span className={`font-medium ${Math.abs(country.ndcTarget - country.ndcTrajectory) > 20 ? "text-red-600" : "text-amber-600"}`}>{country.ndcTarget - country.ndcTrajectory}%</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">Credit rating</span><span className="font-bold text-black">{country.rating}</span></div>
                  </div>
                </div>
              </Section>
              <Section title="Country Profile">
                <div className="bg-white border border-gray-200 rounded-lg p-5">
                  <div className="text-lg font-bold mb-1">{country.name}</div>
                  <div className="text-xs text-gray-400 mb-3">{country.region} — {country.code}</div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between"><span className="text-gray-500">GDP (EUR bn)</span><span className="font-medium">{country.gdp.toLocaleString()}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">Government Debt (EUR bn)</span><span className="font-medium">{country.govDebt.toLocaleString()}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">GHG Inventory (MtCO2e)</span><span className="font-medium">{country.ghgMt.toLocaleString()}</span></div>
                    <div className="flex justify-between"><span className="text-gray-500">Debt/GDP</span><span className="font-medium">{(country.govDebt / country.gdp * 100).toFixed(1)}%</span></div>
                  </div>
                  <div className="mt-3">
                    <div className="text-xs text-gray-500 mb-1">Climate Risk Score</div>
                    <div className="h-2 bg-gray-100 rounded-full">
                      <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${Math.min(100, climateScore)}%` }} />
                    </div>
                    <div className="text-xs text-gray-400 mt-1">{Math.min(100, climateScore)}/100</div>
                  </div>
                </div>
              </Section>
            </div>
          </div>
        )}

        {/* Tab 2 — Portfolio View */}
        {tab === 1 && (
          <div>
            <Row>
              <KpiCard label="Total Financed Emissions" value={`${(portfolioData.reduce((a, p) => a + p.fe, 0) / 1e6).toFixed(2)} MtCO2e`} sub="PCAF Part D portfolio total" accent />
              <KpiCard label="Weighted Avg DQS" value={(portfolioData.reduce((a, p) => a + p.dqs * p.outstanding, 0) / portfolioData.reduce((a, p) => a + p.outstanding, 0)).toFixed(2)} sub="Exposure-weighted DQS" />
              <KpiCard label="Total Outstanding" value={`EUR ${portfolioData.reduce((a, p) => a + p.outstanding, 0).toFixed(0)}M`} sub="Sovereign debt portfolio" />
              <KpiCard label="Portfolio Countries" value={portfolioData.length} sub="8 sovereign issuers" />
            </Row>

            <Section title="Portfolio Breakdown by Country">
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-xs text-gray-500">
                      <th className="text-left p-3">Country</th>
                      <th className="text-right p-3">Outstanding (EUR M)</th>
                      <th className="text-right p-3">Attribution Factor</th>
                      <th className="text-right p-3">Financed tCO2e</th>
                      <th className="text-center p-3">DQS</th>
                      <th className="text-center p-3">NDC Alignment</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolioData.map((p, i) => (
                      <tr key={i} className="border-t border-gray-100 hover:bg-gray-50">
                        <td className="p-3 font-medium">{p.name}</td>
                        <td className="p-3 text-right font-mono">{p.outstanding.toFixed(1)}</td>
                        <td className="p-3 text-right font-mono text-xs">{p.af.toFixed(6)}</td>
                        <td className="p-3 text-right font-mono">{(p.fe / 1000).toFixed(0)}k</td>
                        <td className="p-3 text-center"><span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-medium">{p.dqs}/4</span></td>
                        <td className="p-3 text-center"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${p.ndcCls}`}>{p.ndcStatus}</span></td>
                      </tr>
                    ))}
                    <tr className="border-t-2 border-gray-300 bg-gray-50 font-semibold text-sm">
                      <td className="p-3">Total</td>
                      <td className="p-3 text-right font-mono">{portfolioData.reduce((a, p) => a + p.outstanding, 0).toFixed(1)}</td>
                      <td className="p-3 text-right text-gray-400">—</td>
                      <td className="p-3 text-right font-mono text-emerald-700">{(portfolioData.reduce((a, p) => a + p.fe, 0) / 1000).toFixed(0)}k</td>
                      <td colSpan={2} />
                    </tr>
                  </tbody>
                </table>
              </div>
            </Section>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Section title="Financed Emissions by Country (tCO2e)">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={portfolioData.map(p => ({ name: p.code, fe: Math.round(p.fe / 1000) }))} margin={{ top: 4, right: 10, bottom: 20, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${v}k`} />
                    <Tooltip formatter={v => [`${v}k tCO2e`]} />
                    <Bar dataKey="fe" name="Financed (k tCO2e)" fill={EMERALD} radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Section>
              <Section title="Portfolio Allocation by Region">
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={regionPie} cx="50%" cy="50%" outerRadius={90} dataKey="value" label={({ name, value }) => `${name}: ${value}M`} labelLine>
                      {regionPie.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip formatter={v => `EUR ${v}M`} />
                  </PieChart>
                </ResponsiveContainer>
              </Section>
            </div>
          </div>
        )}

        {/* Tab 3 — Attribution Calculator */}
        {tab === 2 && (
          <div>
            <Section title="Attribution Formula (PCAF Part D, Para 4.2)">
              <div className="bg-gray-50 rounded-lg p-5 font-mono text-sm text-center mb-4 border border-gray-200">
                <div className="text-xs text-gray-500 mb-2">Financed Emissions = Attribution Factor x GHG Inventory</div>
                <div className="text-lg font-bold text-black">
                  Attribution Factor = Outstanding Amount / Total Government Debt
                </div>
                <div className="text-xs text-gray-400 mt-2">Where outstanding amount and government debt are expressed in the same currency and year</div>
              </div>
            </Section>

            <Section title="Live Calculation">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Inp label="Outstanding Amount (EUR M)" type="number" value={attrForm.outstanding} onChange={e => setAttrForm({ ...attrForm, outstanding: e.target.value })} />
                  <Inp label="Government Debt (EUR bn)" type="number" value={attrForm.govDebt} onChange={e => setAttrForm({ ...attrForm, govDebt: e.target.value })} />
                  <Inp label="GHG Inventory (MtCO2e/yr)" type="number" value={attrForm.ghgMt} onChange={e => setAttrForm({ ...attrForm, ghgMt: e.target.value })} />
                  <Sel label="Data Quality Score" value={attrForm.dqs} onChange={e => setAttrForm({ ...attrForm, dqs: e.target.value })}>
                    {DQS_DESC.map(d => <option key={d.dqs} value={d.dqs}>DQS {d.dqs} — {d.label}</option>)}
                  </Sel>
                </div>
                <div className="space-y-4">
                  <div className="bg-white border border-emerald-200 rounded-lg p-5">
                    <div className="text-xs text-gray-500 mb-1">Attribution Factor</div>
                    <div className="text-3xl font-bold text-emerald-600">{attrAF.toFixed(6)}</div>
                    <div className="text-xs text-gray-400 mt-1">{attrForm.outstanding}M / {(Number(attrForm.govDebt) * 1000).toLocaleString()}M</div>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-lg p-5">
                    <div className="text-xs text-gray-500 mb-1">Financed Emissions</div>
                    <div className="text-3xl font-bold text-black">{(attrFE / 1000).toFixed(1)}k tCO2e</div>
                    <div className="text-xs text-gray-400 mt-1">{attrAF.toFixed(6)} x {attrForm.ghgMt} MtCO2e</div>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4 text-xs text-gray-600">
                    <div className="font-semibold mb-1">DQS {attrForm.dqs} — {DQS_DESC.find(d => d.dqs === Number(attrForm.dqs))?.label}</div>
                    <div>{DQS_DESC.find(d => d.dqs === Number(attrForm.dqs))?.desc}</div>
                  </div>
                </div>
              </div>
            </Section>
          </div>
        )}

        {/* Tab 4 — NDC Alignment */}
        {tab === 3 && (
          <div>
            <Section title="NDC Target vs Current Trajectory (Top 10 Countries, % reduction vs 1990)">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={ndcTop10} margin={{ top: 4, right: 20, bottom: 40, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-30} textAnchor="end" />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={v => `${v}%`} />
                  <Legend />
                  <Bar dataKey="target" name="NDC 2030 Target %" fill={EMERALD} radius={[3, 3, 0, 0]} />
                  <Bar dataKey="trajectory" name="Current Trajectory %" fill="#f59e0b" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>

            <Section title="Full NDC Alignment Register">
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-xs text-gray-500">
                      <th className="text-left p-3">Country</th>
                      <th className="text-right p-3">NDC 2030 Target</th>
                      <th className="text-right p-3">Current Trajectory</th>
                      <th className="text-right p-3">Gap</th>
                      <th className="text-center p-3">Alignment</th>
                    </tr>
                  </thead>
                  <tbody>
                    {COUNTRIES.map((c, i) => {
                      const info = ndcAlignmentStatus(c);
                      const gap = c.ndcTarget - c.ndcTrajectory;
                      return (
                        <tr key={i} className="border-t border-gray-100 hover:bg-gray-50">
                          <td className="p-3 font-medium">{c.name}</td>
                          <td className="p-3 text-right font-mono">{c.ndcTarget}%</td>
                          <td className="p-3 text-right font-mono">{c.ndcTrajectory}%</td>
                          <td className={`p-3 text-right font-mono font-semibold ${gap > 20 ? "text-red-600" : gap > 8 ? "text-amber-600" : "text-emerald-600"}`}>{gap}%</td>
                          <td className="p-3 text-center"><span className={`px-2 py-0.5 rounded-full text-xs font-medium ${info.cls}`}>{info.status}</span></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Section>
          </div>
        )}

        {/* Tab 5 — Reference */}
        {tab === 4 && (
          <div>
            <Section title="PCAF Part D — Scope and Methodology">
              <div className="bg-gray-50 rounded-lg p-5 text-sm text-gray-700 mb-6">
                <div className="font-semibold mb-2">PCAF Global GHG Accounting and Reporting Standard Part D: Sovereign Debt (2022)</div>
                <ul className="list-disc list-inside space-y-1.5 text-xs">
                  <li>Applies to government bonds and sovereign loans held in financial institution portfolios.</li>
                  <li>Covers all territorial GHG emissions, with optional LULUCF (land use, land-use change and forestry) adjustment.</li>
                  <li>Attribution approach: outstanding amount divided by total government debt stock.</li>
                  <li>National GHG inventories sourced from UNFCCC submissions, IEA, or World Bank (DQS 1-4).</li>
                  <li>Emissions include Scope 1 of the sovereign (production-based accounting); consumption-based optional.</li>
                </ul>
              </div>
            </Section>
            <Section title="Attribution Formula Explanation">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {[
                  { term: "Outstanding Amount", def: "FI's holding of the sovereign's debt instruments (bonds + loans) at fair/book value in EUR or reporting currency" },
                  { term: "Government Debt", def: "Total outstanding government debt (central + general government) at year-end, same currency as outstanding amount" },
                  { term: "GHG Inventory", def: "Total sovereign GHG emissions (tCO2e/year) from national inventory, typically 1-2 year lag vs reporting date" },
                ].map(item => (
                  <div key={item.term} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="font-semibold text-sm text-emerald-700 mb-1">{item.term}</div>
                    <div className="text-xs text-gray-500">{item.def}</div>
                  </div>
                ))}
              </div>
            </Section>
            <Section title="Data Quality Score (DQS) Descriptions">
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead><tr className="bg-gray-50 text-xs text-gray-500"><th className="text-left p-3">DQS</th><th className="text-left p-3">Label</th><th className="text-left p-3">Description</th></tr></thead>
                  <tbody>
                    {DQS_DESC.map((d, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="p-3 font-bold text-emerald-700">{d.dqs}</td>
                        <td className="p-3 font-medium">{d.label}</td>
                        <td className="p-3 text-gray-600">{d.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <Section title="National Circumstances Adjustments">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4 text-sm">
                  <div className="font-semibold mb-2">LULUCF Adjustment</div>
                  <div className="text-xs text-gray-600">Land Use, Land-Use Change and Forestry (LULUCF) emissions/removals may be included or excluded. Exclusion recommended where LULUCF creates large year-on-year volatility. Must be disclosed consistently.</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 text-sm">
                  <div className="font-semibold mb-2">Annex I vs Non-Annex I</div>
                  <div className="text-xs text-gray-600">Annex I countries (developed) submit detailed annual inventories to UNFCCC — DQS 1 typically applicable. Non-Annex I countries submit biennial reports with greater uncertainty — DQS 2-3 more common.</div>
                </div>
              </div>
            </Section>
            <Section title="Reporting Requirements">
              <div className="space-y-2">
                {[
                  "Disclose total financed emissions from sovereign debt portfolio (tCO2e/year)",
                  "Report attribution factor and data sources used for each sovereign",
                  "Disclose DQS for each sovereign holding and aggregate weighted average DQS",
                  "State whether LULUCF is included or excluded, applied consistently",
                  "Disclose alignment with nationally determined contributions (NDC) where assessed",
                  "Report year-on-year comparison with explanation of significant changes",
                ].map((req, i) => (
                  <div key={i} className="flex gap-3 items-start text-sm">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5 flex-shrink-0" />
                    <span className="text-gray-700">{req}</span>
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
