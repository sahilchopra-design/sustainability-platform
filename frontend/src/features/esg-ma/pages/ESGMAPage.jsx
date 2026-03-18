import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const Section = ({title,children})=>(<div className="mb-6"><h2 className="text-lg font-semibold text-black mb-3 border-b border-emerald-200 pb-1">{title}</h2>{children}</div>);
const KpiCard = ({label,value,sub})=>(<div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"><div className="text-xs text-gray-500 mb-1">{label}</div><div className="text-2xl font-bold text-black">{value}</div>{sub&&<div className="text-xs text-emerald-600 mt-1">{sub}</div>}</div>);
const Row = ({children})=>(<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">{children}</div>);
const Inp = ({label,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><input className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}/></div>);
const Sel = ({label,children,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><select className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}>{children}</select></div>);
const Btn = ({children,...p})=>(<button className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors" {...p}>{children}</button>);

const seed = 79;
const rng = (i, s = seed) => Math.abs(Math.sin(i * 9301 + s * 49297) * 233280) % 233280 / 233280;

const TABS = ['ESG Due Diligence', 'UNGP Alignment', 'ESG Valuation Impact', 'Post-Merger Integration', 'DD Report'];

const SECTORS = ['Technology','Healthcare','Energy','Financial Services','Consumer Goods','Industrials','Real Estate','Materials','Utilities','Agriculture','Mining','Transport'];
const COUNTRIES = ['Germany','France','UK','US','Netherlands','Sweden','Switzerland','Spain','Italy','Brazil','India','China','Australia','Canada','Japan'];
const SEVERITY_OPTIONS = ['Low','Medium','High','Critical'];

const DD_CATEGORIES_15 = [
  'Climate Change (E1)','Pollution (E2)','Water & Marine (E3)','Biodiversity (E4)','Circular Economy (E5)',
  'Workers — Own (S1)','Workers — Value Chain (S2)','Affected Communities (S3)','Consumers & End-users (S4)',
  'Business Conduct (G1)','Supply Chain Transparency','Human Rights Policy','Anti-Corruption',
  'Environmental Liability','Regulatory Compliance',
];

const UNGP_PILLARS = [
  { pillar: 'Pillar I State Duty', principles: [1,2,3,4,5,10], description: 'State duty to protect human rights' },
  { pillar: 'Pillar II Business Responsibility', principles: [11,12,13,14,15,16,17,18,19,20,21,22,23,24], description: 'Business responsibility to respect' },
  { pillar: 'Pillar III Access to Remedy', principles: [25,26,27,28,29,30,31], description: 'Access to effective remedy' },
];

// ── Tab 1: ESG Due Diligence ───────────────────────────────────────────────────
function Tab1() {
  const [dealName, setDealName] = useState('Project Alpine — Renewables Platform Acquisition');
  const [targetSector, setTargetSector] = useState('Energy');
  const [country, setCountry] = useState('Germany');
  const [dealValue, setDealValue] = useState('450');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const overallScore = result?.score || Math.round(rng(0, seed + 1) * 30 + 55);
  const redFlagCount = result?.red_flags || Math.round(rng(1, seed + 1) * 5 + 1);

  const radarData = DD_CATEGORIES_15.slice(0, 12).map((cat, i) => ({
    category: cat.split(' ')[0],
    score: Math.round(rng(i, seed + 2) * 50 + 40),
  }));

  const csdddBadge = parseInt(dealValue) > 200 ? 'In Scope — Group 1 (>€450M)' : parseInt(dealValue) > 50 ? 'In Scope — Group 2 (>€150M)' : 'Out of Scope';

  const handleDD = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/esg-ma/due-diligence', { deal_name: dealName, target_sector: targetSector, country, deal_value: parseFloat(dealValue) });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [dealName, targetSector, country, dealValue]);

  return (
    <div>
      <Section title="Deal Details">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <Inp label="Deal Name" value={dealName} onChange={e => setDealName(e.target.value)} />
          <Sel label="Target Sector" value={targetSector} onChange={e => setTargetSector(e.target.value)}>
            {SECTORS.map(s => <option key={s}>{s}</option>)}
          </Sel>
          <Sel label="Country" value={country} onChange={e => setCountry(e.target.value)}>
            {COUNTRIES.map(c => <option key={c}>{c}</option>)}
          </Sel>
          <Inp label="Deal Value (€M)" value={dealValue} onChange={e => setDealValue(e.target.value)} type="number" />
        </div>
        <Btn onClick={handleDD} disabled={loading}>{loading ? 'Running DD…' : 'Run ESG Due Diligence'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Overall ESG Score" value={`${overallScore}/100`} sub="15-category assessment" />
        <KpiCard label="Red Flags" value={redFlagCount} sub="Material ESG findings" />
        <KpiCard label="CSDDD Art. 3 Scope" value={parseInt(dealValue) > 200 ? 'In Scope' : 'Out of Scope'} sub={csdddBadge} />
        <KpiCard label="W&I ESG Coverage" value={overallScore > 70 ? 'Insurable' : 'Elevated Risk'} sub="Warranty & indemnity ESG reps" />
      </Row>
      <Section title="15-Category DD Radar">
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="category" tick={{ fontSize: 10 }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 9 }} />
            <Radar name="ESG Score" dataKey="score" stroke="#059669" fill="#059669" fillOpacity={0.3} />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 2: UNGP Alignment ──────────────────────────────────────────────────────
function Tab2() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const pillarScores = UNGP_PILLARS.map((p, i) => ({
    pillar: p.pillar.replace('Pillar ', 'P').split(' ')[0] + ' ' + p.pillar.split(' — ')[0].split(' ')[1],
    score: Math.round(rng(i, seed + 10) * 35 + 50),
    full: p.pillar,
  }));

  const principleScoring = Array.from({ length: 31 }, (_, i) => {
    const num = i + 1;
    const pillar = num <= 10 ? 'I' : num <= 24 ? 'II' : 'III';
    return { principle: `P${num}`, pillar, score: Math.round(rng(i, seed + 11) * 50 + 40) };
  });

  const salientIssues = [
    'Forced / child labour in tier 2–3 supply chain (West Africa)',
    'Workplace safety incidents at manufacturing sub-contractors',
    'Community land rights disputes at raw material sourcing sites',
    'Discriminatory recruitment practices — two supplier audits flagged',
    'Inadequate grievance mechanism access for migrant workers',
  ];

  const oeuvreRbcScore = Math.round(rng(5, seed + 10) * 25 + 55);
  const hriaRequired = pillarScores[1].score < 65;

  const handleAlign = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/esg-ma/ungp-alignment', {});
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, []);

  return (
    <div>
      <Section title="UNGP Assessment">
        <Btn onClick={handleAlign} disabled={loading}>{loading ? 'Assessing…' : 'Assess UNGP Alignment'}</Btn>
      </Section>
      <Row>
        {pillarScores.map(p => <KpiCard key={p.full} label={p.full} value={`${p.score}/100`} sub="UNGP pillar score" />)}
        <KpiCard label="OECD RBC Score" value={`${oeuvreRbcScore}/100`} sub="OECD Due Diligence Guidance" />
      </Row>
      <Section title="3-Pillar UNGP Scores">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={pillarScores}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="full" tick={{ fontSize: 10 }} angle={-10} textAnchor="end" height={60} />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Bar dataKey="score" fill="#059669" name="Score" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="31-Principle Scoring (by Pillar)">
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={principleScoring}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="principle" tick={{ fontSize: 8 }} />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Bar dataKey="score" fill="#7c3aed" name="Score" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Salient Human Rights Issues">
        {hriaRequired && <div className="mb-3 px-3 py-2 bg-orange-50 border border-orange-200 rounded text-sm text-orange-800 font-medium">Human Rights Impact Assessment (HRIA) required — Pillar II score below threshold</div>}
        <ul className="space-y-2">
          {salientIssues.map((issue, i) => (
            <li key={i} className="flex items-start gap-2 text-sm p-2 bg-red-50 border border-red-100 rounded">
              <span className="w-2 h-2 mt-1 rounded-full bg-red-500 flex-shrink-0" />
              {issue}
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}

// ── Tab 3: ESG Valuation Impact ────────────────────────────────────────────────
function Tab3() {
  const [baseVal, setBaseVal] = useState('450');
  const [eSeverity, setESeverity] = useState('Medium');
  const [sSeverity, setSSeverity] = useState('High');
  const [gSeverity, setGSeverity] = useState('Low');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const severityAdj = { Low: -0.02, Medium: -0.05, High: -0.10, Critical: -0.18 };
  const base = parseFloat(baseVal) || 450;
  const eAdj = base * severityAdj[eSeverity];
  const sAdj = (base + eAdj) * severityAdj[sSeverity];
  const gAdj = (base + eAdj + sAdj) * severityAdj[gSeverity];
  const climateLib = -(Math.round(rng(0, seed + 20) * base * 0.04 + base * 0.01));
  const integCost = -(Math.round(rng(1, seed + 20) * base * 0.02 + base * 0.01));
  const adjusted = base + eAdj + sAdj + gAdj + climateLib + integCost;
  const ppaPct = ((adjusted - base) / base * 100).toFixed(1);

  const waterfallData = [
    { step: 'Base Valuation', value: base, fill: '#6b7280' },
    { step: 'E Adjustment', value: Math.round(eAdj), fill: '#059669' },
    { step: 'S Adjustment', value: Math.round(sAdj), fill: '#0284c7' },
    { step: 'G Adjustment', value: Math.round(gAdj), fill: '#7c3aed' },
    { step: 'Climate Liability', value: climateLib, fill: '#ef4444' },
    { step: 'Integration Cost', value: integCost, fill: '#f97316' },
    { step: 'Adjusted Value', value: Math.round(adjusted), fill: '#059669' },
  ];

  const comparableDeals = [
    { deal: 'Project Nordvik', sector: 'Energy', adjPct: -8.2, year: 2023 },
    { deal: 'Project Cedar', sector: 'Materials', adjPct: -12.5, year: 2022 },
    { deal: 'Project Linden', sector: 'Consumer', adjPct: -3.8, year: 2024 },
    { deal: 'Project Astra', sector: 'Healthcare', adjPct: -5.1, year: 2023 },
  ].map((d, i) => ({ ...d, adjPct: +(rng(i, seed + 21) * -15 - 2).toFixed(1) }));

  const handleValuate = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/esg-ma/valuation-impact', { base_valuation: base, e_severity: eSeverity, s_severity: sSeverity, g_severity: gSeverity });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [base, eSeverity, sSeverity, gSeverity]);

  return (
    <div>
      <Section title="Valuation Parameters">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <Inp label="Base Valuation (€M)" value={baseVal} onChange={e => setBaseVal(e.target.value)} type="number" />
          <Sel label="E Findings Severity" value={eSeverity} onChange={e => setESeverity(e.target.value)}>
            {SEVERITY_OPTIONS.map(s => <option key={s}>{s}</option>)}
          </Sel>
          <Sel label="S Findings Severity" value={sSeverity} onChange={e => setSSeverity(e.target.value)}>
            {SEVERITY_OPTIONS.map(s => <option key={s}>{s}</option>)}
          </Sel>
          <Sel label="G Findings Severity" value={gSeverity} onChange={e => setGSeverity(e.target.value)}>
            {SEVERITY_OPTIONS.map(s => <option key={s}>{s}</option>)}
          </Sel>
        </div>
        <Btn onClick={handleValuate} disabled={loading}>{loading ? 'Calculating…' : 'Calculate Valuation Impact'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Base Valuation" value={`€${base}M`} sub="Pre-ESG adjustment" />
        <KpiCard label="Adjusted Valuation" value={`€${Math.round(adjusted)}M`} sub="Post-ESG adjustment" />
        <KpiCard label="Purchase Price Adj." value={`${ppaPct}%`} sub="Total ESG price discount" />
        <KpiCard label="W&I Coverage Est." value={`€${Math.round(Math.abs(eAdj + sAdj + gAdj) * 0.7)}M`} sub="Estimated W&I policy limit" />
      </Row>
      <Section title="ESG Valuation Waterfall (€M)">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={waterfallData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="step" tick={{ fontSize: 10 }} angle={-15} textAnchor="end" height={50} />
            <YAxis />
            <Tooltip formatter={v => `€${v}M`} />
            <Bar dataKey="value" name="Value (€M)">
              {waterfallData.map((entry, i) => (
                <rect key={i} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Comparable Deals — ESG Adjustment">
        <table className="min-w-full text-sm border border-gray-200 rounded">
          <thead className="bg-gray-50">
            <tr>{['Deal','Sector','ESG Adj. %','Year'].map(h => <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-600">{h}</th>)}</tr>
          </thead>
          <tbody>
            {comparableDeals.map((row, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="px-3 py-2 font-medium">{row.deal}</td>
                <td className="px-3 py-2 text-gray-600">{row.sector}</td>
                <td className={`px-3 py-2 font-mono font-bold ${row.adjPct < 0 ? 'text-red-600' : 'text-emerald-600'}`}>{row.adjPct}%</td>
                <td className="px-3 py-2 text-gray-500">{row.year}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

// ── Tab 4: Post-Merger Integration ─────────────────────────────────────────────
function Tab4() {
  const [closeDate, setCloseDate] = useState('2025-06-30');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const gapData = [
    'ESG Governance','Climate Targets','Emissions Reporting','Social Policy','Supply Chain DD',
    'Biodiversity Assessment','Human Rights','Data Quality',
  ].map((dim, i) => ({
    dimension: dim,
    acquirer: Math.round(rng(i, seed + 30) * 40 + 55),
    target: Math.round(rng(i, seed + 31) * 40 + 35),
  }));

  const milestones = [
    { phase: 'Weeks 1–4', milestone: 'ESG governance integration — form Joint ESG Steering Committee', status: 'Critical' },
    { phase: 'Weeks 1–4', milestone: 'Material ESG topics inventory — align to ESRS / CSRD reporting scope', status: 'High' },
    { phase: 'Weeks 5–8', milestone: 'Unified emissions data collection — Scope 1/2/3 baseline alignment', status: 'High' },
    { phase: 'Weeks 5–8', milestone: 'Supply chain due diligence — CSDDD Art. 6 adverse impact mapping', status: 'Medium' },
    { phase: 'Weeks 9–12', milestone: "SBTi target revision — assess combined entity's science-based targets", status: 'High' },
    { phase: 'Weeks 9–12', milestone: 'ESRS harmonisation — single disclosure entity registration', status: 'Medium' },
    { phase: 'Weeks 13+', milestone: 'First joint sustainability report under combined CSRD reporting', status: 'Medium' },
    { phase: 'Weeks 13+', milestone: 'Post-integration ESG KPI dashboard — automated data pipeline', status: 'Low' },
  ];

  const sbtiRevision = gapData.reduce((s, d) => s + Math.abs(d.acquirer - d.target), 0) > 200;

  const handlePlan = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/esg-ma/integration-plan', { close_date: closeDate });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [closeDate]);

  const statusColor = s => s === 'Critical' ? 'bg-red-100 text-red-700' : s === 'High' ? 'bg-orange-100 text-orange-700' : s === 'Medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700';

  return (
    <div>
      <Section title="Integration Parameters">
        <div className="flex gap-4 mb-4">
          <Inp label="Deal Close Date" value={closeDate} onChange={e => setCloseDate(e.target.value)} type="date" />
        </div>
        <Btn onClick={handlePlan} disabled={loading}>{loading ? 'Planning…' : 'Generate Integration Plan'}</Btn>
      </Section>
      <Row>
        <KpiCard label="SBTi Revision Required" value={sbtiRevision ? 'Yes' : 'No'} sub="Combined entity target reassessment" />
        <KpiCard label="ESRS Harmonisation" value="Required" sub="CSRD combined entity scope" />
        <KpiCard label="100-Day Milestones" value={milestones.length} sub="Integration action items" />
        <KpiCard label="Critical Items" value={milestones.filter(m => m.status === 'Critical').length} sub="Immediate priority" />
      </Row>
      <Section title="Acquirer vs Target ESG Gap (8 Dimensions)">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={gapData} layout="vertical" margin={{ left: 150 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 100]} />
            <YAxis type="category" dataKey="dimension" tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="acquirer" fill="#059669" name="Acquirer" />
            <Bar dataKey="target" fill="#94a3b8" name="Target" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="100-Day Integration Plan">
        <table className="min-w-full text-sm border border-gray-200 rounded">
          <thead className="bg-gray-50">
            <tr>{['Phase','Milestone','Priority'].map(h => <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-600">{h}</th>)}</tr>
          </thead>
          <tbody>
            {milestones.map((row, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="px-3 py-2 font-mono text-xs text-gray-600 whitespace-nowrap">{row.phase}</td>
                <td className="px-3 py-2">{row.milestone}</td>
                <td className="px-3 py-2"><span className={`px-2 py-0.5 rounded text-xs font-medium ${statusColor(row.status)}`}>{row.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

// ── Tab 5: DD Report ───────────────────────────────────────────────────────────
function Tab5() {
  const [dealName, setDealName] = useState('Project Alpine — Renewables Platform Acquisition');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const RAG_CATEGORIES = [
    'Climate Risk', 'GHG Emissions', 'Water Use', 'Biodiversity', 'Waste & Circular',
    'Labour Standards', 'Supply Chain', 'Community Impact', 'Governance', 'Anti-Corruption', 'Data Privacy', 'ESG Reporting',
  ];
  const ragStatuses = RAG_CATEGORIES.map((cat, i) => {
    const v = rng(i, seed + 40);
    return { cat, status: v > 0.65 ? 'Green' : v > 0.35 ? 'Amber' : 'Red' };
  });

  const materialFindings = [
    { category: 'Climate Risk', finding: 'Physical risk exposure underreported — 3 facilities in high flood zones', severity: 'High' },
    { category: 'Supply Chain', finding: 'Tier 2 supplier audit gap — 12 sites without ESG assessment', severity: 'Medium' },
    { category: 'Labour Standards', finding: 'Living wage gap of 18% vs Anker benchmark in 2 geographies', severity: 'Medium' },
    { category: 'Governance', finding: 'No board-level climate expertise — ESG committee formed <6 months', severity: 'Low' },
  ];

  const valueCreationData = [
    { opportunity: 'Renewable energy tariff savings', value: Math.round(rng(0, seed + 41) * 15 + 5) },
    { opportunity: 'Carbon credit revenue (VCMI)', value: Math.round(rng(1, seed + 41) * 10 + 3) },
    { opportunity: 'Green premium — sustainable products', value: Math.round(rng(2, seed + 41) * 20 + 8) },
    { opportunity: 'EU Taxonomy GAR improvement', value: Math.round(rng(3, seed + 41) * 12 + 4) },
  ];

  const dealBreakers = [
    { criteria: 'Systemic EUDR non-compliance — high deforestation commodity exposure', met: rng(4, seed + 41) > 0.7 },
    { criteria: 'CSDDD Art. 5 — no human rights policy or HRIA conducted', met: rng(5, seed + 41) > 0.8 },
    { criteria: 'Material environmental liability > 20% of enterprise value', met: rng(6, seed + 41) > 0.85 },
    { criteria: 'Regulatory enforcement action — active investigation by national CA', met: rng(7, seed + 41) > 0.9 },
  ];

  const regFlags = ['CSRD ESRS E1 reporting gap — 3 years of missing GHG data', 'SFDR PAI disclosure incomplete — 2 mandatory indicators missing', 'EU Taxonomy eligibility assessment not conducted'];

  const handleReport = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/esg-ma/dd-report', { deal_name: dealName });
      setResult(res.data);
    } catch { setResult(null); }
    setLoading(false);
  }, [dealName]);

  const ragColor = s => s === 'Green' ? 'bg-green-100 text-green-800 border-green-200' : s === 'Amber' ? 'bg-yellow-100 text-yellow-800 border-yellow-200' : 'bg-red-100 text-red-800 border-red-200';
  const sevColor = s => s === 'High' ? 'bg-orange-100 text-orange-700' : s === 'Medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600';

  return (
    <div>
      <Section title="Report Parameters">
        <div className="flex gap-4 mb-4">
          <Inp label="Deal Name" value={dealName} onChange={e => setDealName(e.target.value)} />
        </div>
        <Btn onClick={handleReport} disabled={loading}>{loading ? 'Generating…' : 'Generate DD Report'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Green" value={ragStatuses.filter(r => r.status === 'Green').length} sub="Categories — no material issues" />
        <KpiCard label="Amber" value={ragStatuses.filter(r => r.status === 'Amber').length} sub="Categories — monitoring required" />
        <KpiCard label="Red" value={ragStatuses.filter(r => r.status === 'Red').length} sub="Categories — remediation required" />
        <KpiCard label="Deal Breakers" value={dealBreakers.filter(d => !d.met).length} sub="Criteria not met" />
      </Row>
      <Section title="RAG Status Dashboard (12 Categories)">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
          {ragStatuses.map((r, i) => (
            <div key={i} className={`px-3 py-2 rounded border text-sm font-medium ${ragColor(r.status)}`}>
              <div className="font-semibold text-xs mb-0.5">{r.status}</div>
              {r.cat}
            </div>
          ))}
        </div>
      </Section>
      <Section title="Material Findings Summary">
        <table className="min-w-full text-sm border border-gray-200 rounded">
          <thead className="bg-gray-50">
            <tr>{['Category','Material Finding','Severity'].map(h => <th key={h} className="px-3 py-2 text-left text-xs font-medium text-gray-600">{h}</th>)}</tr>
          </thead>
          <tbody>
            {materialFindings.map((row, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="px-3 py-2 font-medium text-xs">{row.category}</td>
                <td className="px-3 py-2">{row.finding}</td>
                <td className="px-3 py-2"><span className={`px-2 py-0.5 rounded text-xs font-medium ${sevColor(row.severity)}`}>{row.severity}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
      <Section title="Value Creation Opportunities (€M NPV)">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={valueCreationData} layout="vertical" margin={{ left: 210 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis type="category" dataKey="opportunity" tick={{ fontSize: 10 }} />
            <Tooltip formatter={v => `€${v}M`} />
            <Bar dataKey="value" fill="#059669" name="NPV (€M)" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Regulatory Risk Flags">
        <ul className="space-y-2 mb-4">
          {regFlags.map((f, i) => (
            <li key={i} className="flex items-start gap-2 text-sm p-2 bg-orange-50 border border-orange-100 rounded">
              <span className="w-2 h-2 mt-1 rounded-full bg-orange-500 flex-shrink-0" />
              {f}
            </li>
          ))}
        </ul>
        <div className="text-sm font-medium text-gray-700 mb-2">Deal-Breaker Criteria Checklist</div>
        <ul className="space-y-2">
          {dealBreakers.map((d, i) => (
            <li key={i} className={`flex items-start gap-2 text-sm p-2 rounded border ${d.met ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
              <span className={`mt-0.5 w-4 h-4 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold ${d.met ? 'bg-green-500 text-white' : 'bg-red-500 text-white'}`}>{d.met ? '✓' : '✗'}</span>
              {d.criteria}
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function ESGMAPage() {
  const [activeTab, setActiveTab] = useState(0);
  const tabComponents = [Tab1, Tab2, Tab3, Tab4, Tab5];
  const ActiveComp = tabComponents[activeTab];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">ESG M&A Due Diligence</h1>
          <p className="text-sm text-gray-500 mt-1">UNGP 31 Guiding Principles · EU CSDDD Art 3 · ESG Valuation Adjustment · Post-Merger ESG Integration · OECD RBC · W&I ESG Reps · E79</p>
        </div>
        <div className="flex flex-wrap gap-2 mb-6 border-b border-gray-200 pb-2">
          {TABS.map((tab, i) => (
            <button key={i} onClick={() => setActiveTab(i)} className={`px-4 py-2 rounded-t text-sm font-medium transition-colors ${activeTab === i ? 'bg-emerald-600 text-white' : 'bg-white text-gray-600 hover:bg-emerald-50 border border-gray-200'}`}>{tab}</button>
          ))}
        </div>
        <ActiveComp />
      </div>
    </div>
  );
}
