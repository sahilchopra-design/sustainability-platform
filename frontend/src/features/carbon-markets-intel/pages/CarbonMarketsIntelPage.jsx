/**
 * CarbonMarketsIntelPage.jsx
 * Route: /carbon-markets-intel
 * Concept: Carbon Markets Intelligence — VCMI Claims · ICVCM CCP · CORSIA · Article 6
 */
import React, { useState, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const Section = ({ title, children }) => (
  <div className="mb-6">
    <h2 className="text-lg font-semibold text-black mb-3 border-b border-emerald-200 pb-1">{title}</h2>
    {children}
  </div>
);
const KpiCard = ({ label, value, sub, color = 'emerald' }) => (
  <div className={`bg-${color}-50 border border-${color}-200 rounded-lg p-4`}>
    <div className="text-xs text-gray-500 mb-1">{label}</div>
    <div className={`text-2xl font-bold text-${color}-700`}>{value}</div>
    {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
  </div>
);
const Row = ({ children }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">{children}</div>
);
const Inp = ({ label, ...p }) => (
  <div className="flex flex-col gap-1">
    <label className="text-xs font-medium text-gray-600">{label}</label>
    <input className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p} />
  </div>
);
const Sel = ({ label, children, ...p }) => (
  <div className="flex flex-col gap-1">
    <label className="text-xs font-medium text-gray-600">{label}</label>
    <select className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}>{children}</select>
  </div>
);
const Btn = ({ children, ...p }) => (
  <button className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors" {...p}>{children}</button>
);

function seeded(i, seed) {
  return Math.abs(Math.sin(i * 9301 + seed * 49297) * 233280) % 233280 / 233280;
}

const TABS = ['VCMI Claims Code', 'ICVCM CCPs', 'CORSIA & Article 6', 'Portfolio Quality', 'Credit Pricing'];
const COLORS = ['#059669', '#10b981', '#34d399', '#6ee7b7', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6'];
const seed = 55;

const CCP_ITEMS = [
  { ccp: 'CCP-01', label: 'Governance', category: 'governance' },
  { ccp: 'CCP-02', label: 'Tracking', category: 'governance' },
  { ccp: 'CCP-03', label: 'Transparency', category: 'governance' },
  { ccp: 'CCP-04', label: 'Validation & Verification', category: 'governance' },
  { ccp: 'CCP-05', label: 'Additionality', category: 'emissions_impact' },
  { ccp: 'CCP-06', label: 'Permanence', category: 'emissions_impact' },
  { ccp: 'CCP-07', label: 'Quantification', category: 'emissions_impact' },
  { ccp: 'CCP-08', label: 'No Double Counting', category: 'emissions_impact' },
  { ccp: 'CCP-09', label: 'SDG Co-benefits', category: 'sustainable_dev' },
  { ccp: 'CCP-10', label: 'Safeguards', category: 'sustainable_dev' },
];

const ARTICLE6_COUNTRIES = [
  { country_a: 'Switzerland', country_b: 'Ghana', status: 'active', volume: 420000, type: '6.2' },
  { country_a: 'Japan', country_b: 'Senegal', status: 'active', volume: 850000, type: '6.2' },
  { country_a: 'Sweden', country_b: 'Viet Nam', status: 'pending', volume: 0, type: '6.4' },
  { country_a: 'Germany', country_b: 'Kenya', status: 'signed', volume: 120000, type: '6.2' },
  { country_a: 'USA', country_b: 'Brazil', status: 'pending', volume: 0, type: '6.4' },
  { country_a: 'UK', country_b: 'Rwanda', status: 'active', volume: 310000, type: '6.2' },
  { country_a: 'Canada', country_b: 'Morocco', status: 'signed', volume: 75000, type: '6.4' },
  { country_a: 'Norway', country_b: 'Ethiopia', status: 'active', volume: 680000, type: '6.2' },
  { country_a: 'Singapore', country_b: 'Papua PNG', status: 'pending', volume: 0, type: '6.4' },
  { country_a: 'Australia', country_b: 'Indonesia', status: 'signed', volume: 290000, type: '6.2' },
  { country_a: 'Netherlands', country_b: 'Colombia', status: 'active', volume: 195000, type: '6.4' },
  { country_a: 'France', country_b: 'Côte d\'Ivoire', status: 'pending', volume: 0, type: '6.2' },
  { country_a: 'Denmark', country_b: 'Nepal', status: 'signed', volume: 55000, type: '6.4' },
  { country_a: 'Finland', country_b: 'Tanzania', status: 'active', volume: 230000, type: '6.2' },
  { country_a: 'Austria', country_b: 'Thailand', status: 'pending', volume: 0, type: '6.4' },
  { country_a: 'Belgium', country_b: 'Peru', status: 'signed', volume: 88000, type: '6.2' },
  { country_a: 'Spain', country_b: 'Chile', status: 'active', volume: 410000, type: '6.4' },
  { country_a: 'Italy', country_b: 'Jordan', status: 'pending', volume: 0, type: '6.2' },
  { country_a: 'Portugal', country_b: 'Mozambique', status: 'signed', volume: 140000, type: '6.4' },
  { country_a: 'South Korea', country_b: 'Mongolia', status: 'active', volume: 560000, type: '6.2' },
];

export default function CarbonMarketsIntelPage() {
  const [tab, setTab] = useState(0);
  const [claimLevel, setClaimLevel] = useState('Silver');
  const [projectType, setProjectType] = useState('redd_plus');
  const [vintageYear, setVintageYear] = useState(2022);
  const [icvcmPass, setIcvcmPass] = useState(true);
  const [cobenefits, setCobenefits] = useState(['biodiversity', 'community']);

  const ccpData = useMemo(() => CCP_ITEMS.map((c, i) => ({
    ...c,
    score: +(seeded(i, seed) * 0.5 + 0.5).toFixed(2),
    pass: seeded(i + 50, seed) > 0.3,
  })), []);

  const ccpRadar = useMemo(() => ccpData.map(c => ({ subject: c.ccp, pass_rate: c.pass ? 1 : 0 })), [ccpData]);

  const passRate = useMemo(() => Math.round(ccpData.filter(c => c.pass).length / ccpData.length * 100), [ccpData]);

  const categoryScores = useMemo(() => {
    const cats = {};
    ccpData.forEach(c => {
      if (!cats[c.category]) cats[c.category] = { total: 0, count: 0 };
      cats[c.category].total += c.score;
      cats[c.category].count++;
    });
    return Object.entries(cats).map(([cat, v]) => ({ category: cat.replace('_', ' '), score: +(v.total / v.count).toFixed(2) }));
  }, [ccpData]);

  const corsiaSchemes = useMemo(() => [
    { name: 'Verra VCS', share: 38 }, { name: 'Gold Standard', share: 22 },
    { name: 'ACR', share: 15 }, { name: 'CAR', share: 12 }, { name: 'Other', share: 13 },
  ], []);

  const article6Bar = useMemo(() => [
    { type: 'Art 6.2 Bilateral', volume: 3920000, ca_adjusted: 3450000 },
    { type: 'Art 6.4 Mechanism', volume: 1840000, ca_adjusted: 1620000 },
  ], []);

  const portfolioByType = useMemo(() => [
    { type: 'REDD+', credits: 4500000 }, { type: 'Cookstoves', credits: 2800000 },
    { type: 'Solar', credits: 1900000 }, { type: 'Afforestation', credits: 3200000 },
    { type: 'Blue Carbon', credits: 850000 }, { type: 'Methane', credits: 1200000 },
  ], []);

  const vintageDist = useMemo(() => [2018, 2019, 2020, 2021, 2022, 2023, 2024].map((yr, i) => ({
    year: yr, credits: Math.round(seeded(i + 80, seed) * 3000000 + 500000),
  })), []);

  const pricingBreakdown = useMemo(() => {
    const base = projectType === 'redd_plus' ? 8 : projectType === 'blue_carbon' ? 18 : projectType === 'cookstoves' ? 12 : 6;
    const vintage_discount = vintageYear < 2020 ? -2.5 : vintageYear < 2022 ? -1.0 : 0;
    const additionality = icvcmPass ? 4.5 : 1.5;
    const cobenefit = cobenefits.length * 1.2;
    return { base, vintage_discount, additionality, cobenefit, total: +(base + vintage_discount + additionality + cobenefit).toFixed(2) };
  }, [projectType, vintageYear, icvcmPass, cobenefits]);

  const pricingComparison = useMemo(() => [
    { type: 'REDD+', price: 9.2 }, { type: 'Cookstoves', price: 14.1 },
    { type: 'Solar', price: 6.8 }, { type: 'Afforestation', price: 11.4 },
    { type: 'Blue Carbon', price: 22.5 }, { type: 'Methane', price: 7.3 },
    { type: 'Direct Air Capture', price: 280 },
  ], []);

  const priceTrend = useMemo(() => [2020, 2021, 2022, 2023, 2024, 2025].map((yr, i) => ({
    year: yr, vcs: +(seeded(i + 30, seed) * 5 + 5 + i * 1.5).toFixed(2),
    gold_standard: +(seeded(i + 40, seed) * 6 + 8 + i * 1.8).toFixed(2),
  })), []);

  const vcmiCriteria = [
    { criterion: 'GHG Emissions Abatement ≥50% vs base year', met: true },
    { criterion: 'SBTi-validated near-term target', met: true },
    { criterion: 'All Scope 1 & 2 emissions covered', met: claimLevel !== 'Bronze' },
    { criterion: 'Material Scope 3 categories covered', met: claimLevel === 'Gold' },
    { criterion: 'VCMI Mitigation Contribution Statement filed', met: true },
    { criterion: 'Third-party verification of claims', met: claimLevel !== 'Bronze' },
  ];

  const credibilityScore = useMemo(() => Math.round(vcmiCriteria.filter(c => c.met).length / vcmiCriteria.length * 100), [claimLevel]);

  function statusBadge(status) {
    const map = { active: 'bg-emerald-100 text-emerald-700', pending: 'bg-amber-100 text-amber-700', signed: 'bg-blue-100 text-blue-700' };
    return <span className={`text-xs px-2 py-0.5 rounded font-medium ${map[status] || 'bg-gray-100 text-gray-500'}`}>{status}</span>;
  }

  function claimBadge(level) {
    const map = { Gold: 'bg-yellow-100 text-yellow-700 border-yellow-300', Silver: 'bg-gray-100 text-gray-600 border-gray-300', Bronze: 'bg-amber-100 text-amber-800 border-amber-300' };
    return <span className={`text-xs px-3 py-1 rounded-full font-bold border ${map[level]}`}>{level}</span>;
  }

  function toggleCobenefit(cb) {
    setCobenefits(prev => prev.includes(cb) ? prev.filter(c => c !== cb) : [...prev, cb]);
  }

  return (
    <div className="p-6 bg-white min-h-screen text-black">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-black">Carbon Markets Intelligence</h1>
        <p className="text-sm text-gray-500 mt-1">VCMI Claims Code · ICVCM CCPs · CORSIA · Paris Agreement Article 6</p>
      </div>

      <div className="flex gap-2 mb-6 border-b border-gray-200 overflow-x-auto">
        {TABS.map((t, i) => (
          <button key={t} onClick={() => setTab(i)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${tab === i ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-gray-500 hover:text-black'}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === 0 && (
        <div>
          <Section title="VCMI Claims Code Assessment">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <Sel label="Claim Level" value={claimLevel} onChange={e => setClaimLevel(e.target.value)}>
                <option value="Gold">Gold</option>
                <option value="Silver">Silver</option>
                <option value="Bronze">Bronze</option>
              </Sel>
              <div className="flex flex-col justify-end pb-1">
                <div className="text-xs text-gray-600 mb-1">Current Claim</div>
                <div>{claimBadge(claimLevel)}</div>
              </div>
              <KpiCard label="Credibility Score" value={`${credibilityScore}%`} sub="Criteria met" color={credibilityScore >= 80 ? 'emerald' : credibilityScore >= 60 ? 'amber' : 'red'} />
              <KpiCard label="Criteria Met" value={`${vcmiCriteria.filter(c => c.met).length} / ${vcmiCriteria.length}`} sub="VCMI v2 requirements" color="blue" />
            </div>
            <Btn onClick={() => alert('VCMI claim submitted')}>Submit Claim</Btn>
          </Section>

          <Section title="Criteria Checklist">
            {vcmiCriteria.map((c, i) => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-lg mb-2 bg-gray-50">
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${c.met ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{c.met ? '✓' : '✗'}</span>
                <span className="text-sm text-black">{c.criterion}</span>
                <span className={`ml-auto text-xs px-2 py-0.5 rounded ${c.met ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>{c.met ? 'Met' : 'Gap'}</span>
              </div>
            ))}
          </Section>
        </div>
      )}

      {tab === 1 && (
        <div>
          <Section title="ICVCM CCP Scoring Overview">
            <Row>
              <KpiCard label="Overall Pass Rate" value={`${passRate}%`} sub="CCPs passed" color={passRate >= 80 ? 'emerald' : passRate >= 60 ? 'amber' : 'red'} />
              {categoryScores.map(c => (
                <KpiCard key={c.category} label={c.category} value={`${(c.score * 100).toFixed(0)}%`} sub="Category avg score" color="blue" />
              ))}
            </Row>
          </Section>

          <Section title="CCP Pass/Fail by Criterion">
            <div className="overflow-x-auto mb-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs text-gray-500 uppercase">
                    <th className="px-3 py-2 text-left">CCP</th>
                    <th className="px-3 py-2 text-left">Label</th>
                    <th className="px-3 py-2 text-left">Category</th>
                    <th className="px-3 py-2 text-right">Score</th>
                    <th className="px-3 py-2 text-left">Result</th>
                  </tr>
                </thead>
                <tbody>
                  {ccpData.map((c, i) => (
                    <tr key={c.ccp} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-3 py-2 font-mono text-xs font-bold text-emerald-700">{c.ccp}</td>
                      <td className="px-3 py-2 font-medium">{c.label}</td>
                      <td className="px-3 py-2 text-gray-500">{c.category.replace('_', ' ')}</td>
                      <td className="px-3 py-2 text-right">{(c.score * 100).toFixed(0)}%</td>
                      <td className="px-3 py-2">
                        <span className={`text-xs px-2 py-0.5 rounded font-medium ${c.pass ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>{c.pass ? 'Pass' : 'Fail'}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title="CCP Radar (Pass Rate by Criterion)">
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={ccpRadar}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10 }} />
                <PolarRadiusAxis domain={[0, 1]} tick={{ fontSize: 9 }} />
                <Radar name="Pass Rate" dataKey="pass_rate" stroke="#059669" fill="#059669" fillOpacity={0.4} />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </Section>

          <Section title="Category Sub-Scores">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={categoryScores}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                <YAxis domain={[0, 1]} tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
                <Tooltip formatter={v => `${(v * 100).toFixed(0)}%`} />
                <Bar dataKey="score" fill="#059669" radius={[4, 4, 0, 0]} name="Avg Score" />
              </BarChart>
            </ResponsiveContainer>
          </Section>
        </div>
      )}

      {tab === 2 && (
        <div>
          <Section title="CORSIA Eligibility">
            <Row>
              <KpiCard label="CORSIA Eligibility" value="74%" sub="% of portfolio eligible" color="emerald" />
              <KpiCard label="ITMO Volume" value="5.76 MtCO2e" sub="Art 6.2 + Art 6.4" color="blue" />
              <KpiCard label="Corresponding Adjustment" value="89%" sub="% with CA applied" color="emerald" />
              <KpiCard label="Art 6.2 Bilateral" value="3.92 MtCO2e" sub="Authorized ITMOs" color="emerald" />
            </Row>
          </Section>

          <Section title="CORSIA Approved Schemes">
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={corsiaSchemes} dataKey="share" nameKey="name" cx="50%" cy="50%" outerRadius={90}
                  label={({ name, share }) => `${name}: ${share}%`}>
                  {corsiaSchemes.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Section>

          <Section title="Article 6.2 vs 6.4 Volume (tCO2e)">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={article6Bar}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" />
                <YAxis tickFormatter={v => `${(v / 1e6).toFixed(1)}M`} />
                <Tooltip formatter={v => `${(v / 1e6).toFixed(2)}M tCO2e`} />
                <Legend />
                <Bar dataKey="volume" fill="#059669" name="Total Volume" radius={[4, 4, 0, 0]} />
                <Bar dataKey="ca_adjusted" fill="#34d399" name="CA Adjusted" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Section>

          <Section title="Bilateral Agreement Status (20 Country Pairs)">
            <div className="overflow-y-auto max-h-64">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-gray-50 text-gray-500 uppercase sticky top-0">
                    <th className="px-3 py-2 text-left">Country A</th>
                    <th className="px-3 py-2 text-left">Country B</th>
                    <th className="px-3 py-2 text-left">Type</th>
                    <th className="px-3 py-2 text-right">Volume (tCO2e)</th>
                    <th className="px-3 py-2 text-left">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {ARTICLE6_COUNTRIES.map((r, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-3 py-2">{r.country_a}</td>
                      <td className="px-3 py-2">{r.country_b}</td>
                      <td className="px-3 py-2 font-mono font-semibold text-emerald-700">{r.type}</td>
                      <td className="px-3 py-2 text-right">{r.volume > 0 ? r.volume.toLocaleString() : '—'}</td>
                      <td className="px-3 py-2">{statusBadge(r.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>
        </div>
      )}

      {tab === 3 && (
        <div>
          <Section title="Portfolio Overview">
            <Row>
              <KpiCard label="Total Credits" value="14.45M tCO2e" sub="Gross portfolio" color="emerald" />
              <KpiCard label="Total Spend" value="USD 128M" sub="Acquisition cost" color="blue" />
              <KpiCard label="Weighted Avg Price" value="USD 8.86/t" sub="Volume weighted" color="emerald" />
              <KpiCard label="High Integrity Share" value="38%" sub="ICVCM-CCP labelled" color={38 >= 50 ? 'emerald' : 'amber'} />
            </Row>
            <Row>
              <KpiCard label="Weighted Vintage" value="2021.4" sub="Volume-weighted avg year" color="blue" />
              <KpiCard label="Registries" value="5" sub="Verra, GS, ACR, CAR, BVC" color="emerald" />
              <KpiCard label="Project Types" value="6" sub="Across methodology mix" color="emerald" />
              <KpiCard label="Retiring Entity" value="87%" sub="% with stated end use" color="emerald" />
            </Row>
          </Section>

          <Section title="Credits by Project Type">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={portfolioByType}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={v => `${(v / 1e6).toFixed(1)}M`} />
                <Tooltip formatter={v => `${(v / 1e6).toFixed(2)}M tCO2e`} />
                <Bar dataKey="credits" fill="#059669" radius={[4, 4, 0, 0]} name="Credits (tCO2e)" />
              </BarChart>
            </ResponsiveContainer>
          </Section>

          <Section title="Vintage Year Distribution">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={vintageDist}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis tickFormatter={v => `${(v / 1e6).toFixed(1)}M`} />
                <Tooltip formatter={v => `${(v / 1e6).toFixed(2)}M tCO2e`} />
                <Line type="monotone" dataKey="credits" stroke="#059669" dot={{ r: 4 }} strokeWidth={2} name="Credits" />
              </LineChart>
            </ResponsiveContainer>
          </Section>
        </div>
      )}

      {tab === 4 && (
        <div>
          <Section title="Pricing Model Inputs">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <Sel label="Project Type" value={projectType} onChange={e => setProjectType(e.target.value)}>
                <option value="redd_plus">REDD+</option>
                <option value="blue_carbon">Blue Carbon</option>
                <option value="cookstoves">Cookstoves</option>
                <option value="solar">Solar</option>
                <option value="afforestation">Afforestation</option>
              </Sel>
              <Inp label="Vintage Year" type="number" min="2015" max="2025" value={vintageYear} onChange={e => setVintageYear(parseInt(e.target.value))} />
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-600">ICVCM CCP Labelled</label>
                <label className="flex items-center gap-2 mt-2 cursor-pointer">
                  <input type="checkbox" checked={icvcmPass} onChange={e => setIcvcmPass(e.target.checked)} className="accent-emerald-600" />
                  <span className="text-sm">{icvcmPass ? 'Yes' : 'No'}</span>
                </label>
              </div>
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-600">Co-Benefits</label>
                <div className="flex flex-wrap gap-1 mt-1">
                  {['biodiversity', 'community', 'water', 'gender'].map(cb => (
                    <label key={cb} className="flex items-center gap-1 text-xs cursor-pointer">
                      <input type="checkbox" checked={cobenefits.includes(cb)} onChange={() => toggleCobenefit(cb)} className="accent-emerald-600" />
                      {cb}
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </Section>

          <Section title="Fair Value Estimate">
            <Row>
              <KpiCard label="Fair Value" value={`USD ${pricingBreakdown.total}/t`} sub="Model estimated price" color="emerald" />
              <KpiCard label="Base Price" value={`USD ${pricingBreakdown.base}/t`} sub="Project type base" color="blue" />
              <KpiCard label="Additionality Premium" value={`+USD ${pricingBreakdown.additionality}/t`} sub={icvcmPass ? 'CCP labelled' : 'Standard'} color="emerald" />
              <KpiCard label="Co-Benefit Premium" value={`+USD ${pricingBreakdown.cobenefit}/t`} sub={`${cobenefits.length} co-benefits`} color="emerald" />
            </Row>
          </Section>

          <Section title="Price Comparison by Project Type (USD/t)">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={pricingComparison.filter(p => p.price < 30)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="type" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip formatter={v => `USD ${v}/t`} />
                <Bar dataKey="price" fill="#059669" radius={[4, 4, 0, 0]} name="Price (USD/t)" />
              </BarChart>
            </ResponsiveContainer>
          </Section>

          <Section title="VCM Price Trend (USD/t)">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={priceTrend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="vcs" stroke="#059669" dot={{ r: 4 }} strokeWidth={2} name="Verra VCS" />
                <Line type="monotone" dataKey="gold_standard" stroke="#f59e0b" dot={{ r: 4 }} strokeWidth={2} name="Gold Standard" />
              </LineChart>
            </ResponsiveContainer>
          </Section>
        </div>
      )}
    </div>
  );
}
