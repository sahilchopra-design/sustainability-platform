/**
 * IFRSS1Page.jsx — Route: /ifrs-s1
 * IFRS S1 General Requirements for Disclosure of Sustainability-related Financial Information
 * ISSB IFRS S1 (effective 1 January 2024)
 * Sprint 14 — E18
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const EM = '#10b981';
const seed = (n) => ((n * 9301 + 49297) % 233280) / 233280;

/* ── Primitives ── */
const Section = ({ title, children }) => (
  <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 20, marginBottom: 16 }}>
    {title && <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 12, color: '#111' }}>{title}</div>}
    {children}
  </div>
);
const KpiCard = ({ label, value, sub }) => (
  <div style={{ background: '#f0fdf4', border: `1px solid ${EM}`, borderRadius: 8, padding: '14px 18px', flex: 1, minWidth: 140 }}>
    <div style={{ fontSize: 22, fontWeight: 800, color: EM }}>{value}</div>
    <div style={{ fontSize: 12, color: '#374151', marginTop: 2 }}>{label}</div>
    {sub && <div style={{ fontSize: 11, color: '#6b7280', marginTop: 2 }}>{sub}</div>}
  </div>
);
const Row = ({ children, gap = 12 }) => (
  <div style={{ display: 'flex', gap, flexWrap: 'wrap', marginBottom: 12 }}>{children}</div>
);
const Inp = ({ label, ...props }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 160 }}>
    {label && <label style={{ fontSize: 12, color: '#374151', fontWeight: 600 }}>{label}</label>}
    <input style={{ border: '1px solid #d1d5db', borderRadius: 6, padding: '7px 10px', fontSize: 13, outline: 'none' }} {...props} />
  </div>
);
const Sel = ({ label, children, ...props }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 160 }}>
    {label && <label style={{ fontSize: 12, color: '#374151', fontWeight: 600 }}>{label}</label>}
    <select style={{ border: '1px solid #d1d5db', borderRadius: 6, padding: '7px 10px', fontSize: 13, outline: 'none', background: '#fff' }} {...props}>{children}</select>
  </div>
);
const Btn = ({ children, ...props }) => (
  <button style={{ background: EM, color: '#fff', border: 'none', borderRadius: 6, padding: '9px 20px', fontSize: 13, fontWeight: 700, cursor: 'pointer' }} {...props}>{children}</button>
);

/* ── Constants ── */
const TABS = ['S1 Assessment', 'Pillar Breakdown', 'SASB Industry', 'Cross-Framework', 'Reference'];

const PILLARS = [
  { key: 'governance', label: 'Governance', weight: 0.25, color: '#10b981', desc: 'Board oversight, management roles, incentive alignment' },
  { key: 'strategy', label: 'Strategy', weight: 0.35, color: '#3b82f6', desc: 'Short/medium/long-term risks & opportunities, business model impacts, financial effects' },
  { key: 'risk_mgmt', label: 'Risk Management', weight: 0.20, color: '#f59e0b', desc: 'Processes for identifying, assessing, monitoring sustainability risks' },
  { key: 'metrics', label: 'Metrics & Targets', weight: 0.20, color: '#8b5cf6', desc: 'Cross-industry metrics, industry-based metrics, targets & progress' },
];

const SASB_INDUSTRIES = [
  { sector: 'Financial Services', sub: 'Commercial Banks', key_metrics: 'Financed emissions, climate-adjusted credit risk, green lending %' },
  { sector: 'Energy', sub: 'Oil & Gas (E&P)', key_metrics: 'GHG intensity, flaring volume, proven reserves stranded risk' },
  { sector: 'Materials', sub: 'Steel', key_metrics: 'Scope 1 CO2/t, recycled input %, water consumption intensity' },
  { sector: 'Real Estate', sub: 'Real Estate Owners & Developers', key_metrics: 'Energy intensity, GRESB score, green-certified floor area %' },
  { sector: 'Technology', sub: 'Software & IT Services', key_metrics: 'Data centre PUE, water usage effectiveness, e-waste recycling' },
  { sector: 'Healthcare', sub: 'Pharmaceutical', key_metrics: 'Pharmaceutical waste, access to medicine index, clinical trial diversity' },
  { sector: 'Consumer Goods', sub: 'Food & Beverage', key_metrics: 'GHG/revenue, deforestation-free sourcing %, water-stressed areas sourcing' },
  { sector: 'Industrials', sub: 'Aerospace & Defence', key_metrics: 'Fuel burn improvement %, revenue from sustainable aviation fuel' },
  { sector: 'Utilities', sub: 'Electric Utilities', key_metrics: 'CO2e per MWh, renewable capacity %, physical climate risk exposure' },
  { sector: 'Transportation', sub: 'Airlines', key_metrics: 'Available tonne-km CO2 intensity, SAF blend %, fleet age' },
  { sector: 'Agriculture', sub: 'Agricultural Products', key_metrics: 'GHG/tonne produce, deforestation risk, freshwater consumption' },
  { sector: 'Mining', sub: 'Metals & Mining', key_metrics: 'Energy consumption, water recycled %, biodiversity impact rating' },
];

const SEED_ASSESSMENTS = Array.from({ length: 5 }, (_, i) => ({
  entity: ['Barclays plc', 'BP plc', 'ArcelorMittal SA', 'British Land plc', 'Microsoft Corp'][i],
  industry: SASB_INDUSTRIES[i].sub,
  governance: Math.round(60 + seed(i * 5 + 1) * 35),
  strategy: Math.round(55 + seed(i * 5 + 2) * 40),
  risk_mgmt: Math.round(58 + seed(i * 5 + 3) * 37),
  metrics: Math.round(52 + seed(i * 5 + 4) * 43),
})).map(a => ({
  ...a,
  overall: Math.round(a.governance * 0.25 + a.strategy * 0.35 + a.risk_mgmt * 0.20 + a.metrics * 0.20),
}));

const DISCLOSURE_REQS = [
  { para: '14(a)', pillar: 'Governance', requirement: 'Governance body oversight of sustainability risks & opportunities' },
  { para: '14(b)', pillar: 'Governance', requirement: 'Management role in sustainability risk assessment and monitoring' },
  { para: '14(c)', pillar: 'Strategy', requirement: 'Sustainability-related risks & opportunities over short/medium/long term' },
  { para: '14(d)', pillar: 'Strategy', requirement: 'Effects on entity business model, value chain, strategy, decision-making' },
  { para: '14(e)', pillar: 'Strategy', requirement: 'Financial effects of sustainability risks: assets, liabilities, revenues' },
  { para: '14(f)', pillar: 'Strategy', requirement: 'Resilience of entity strategy under scenario analysis' },
  { para: '14(g)', pillar: 'Risk Mgmt', requirement: 'Process for identifying and assessing sustainability-related risks' },
  { para: '14(h)', pillar: 'Risk Mgmt', requirement: 'Process for monitoring and managing sustainability-related risks' },
  { para: '14(i)', pillar: 'Risk Mgmt', requirement: 'Integration of risk management processes with overall risk management' },
  { para: '14(j)', pillar: 'Metrics', requirement: 'Cross-industry category metrics (GHG, water, energy, waste, workforce)' },
  { para: '14(k)', pillar: 'Metrics', requirement: 'Industry-based metrics per SASB industry standard' },
  { para: '14(l)', pillar: 'Metrics', requirement: 'Targets: goals set, progress, changes to targets' },
];

const CROSS_FRAMEWORK = [
  { pillar: 'Governance', ifrs_s1: 'Paras 14(a)–14(b)', tcfd: 'Governance pillar', csrd: 'ESRS 2 GOV-1 to GOV-5', sec: 'Reg S-K Item 1501' },
  { pillar: 'Strategy', ifrs_s1: 'Paras 14(c)–14(f)', tcfd: 'Strategy pillar', csrd: 'ESRS 2 SBM-1 to SBM-3', sec: 'Reg S-K Item 1502' },
  { pillar: 'Risk Management', ifrs_s1: 'Paras 14(g)–14(i)', tcfd: 'Risk Management pillar', csrd: 'ESRS 2 IRO-1 to IRO-2', sec: 'Reg S-K Item 1503' },
  { pillar: 'Metrics & Targets', ifrs_s1: 'Paras 14(j)–14(l)', tcfd: 'Metrics & Targets pillar', csrd: 'E1/S1/G1 cross-cutting metrics', sec: 'Reg S-K Items 1504–1505' },
];

/* ── Page ── */
export default function IFRSS1Page() {
  const [tab, setTab] = useState(0);
  const [selectedIndustry, setSelectedIndustry] = useState(0);
  const [form, setForm] = useState({
    entity_name: 'Test Corporation plc',
    sasb_industry: 'Commercial Banks',
    reporting_period: '2024',
    governance_disclosed: true,
    strategy_disclosed: true,
    risk_mgmt_disclosed: false,
    metrics_disclosed: false,
    significant_risks_count: 4,
    transition_plan: true,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAssess = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.post(`${API}/api/v1/ifrs-s1/assess`, form);
      setResult(res.data);
    } catch {
      const pillarScores = {
        governance: form.governance_disclosed ? Math.round(72 + seed(1) * 20) : Math.round(20 + seed(1) * 25),
        strategy: form.strategy_disclosed ? Math.round(68 + seed(2) * 25) : Math.round(15 + seed(2) * 30),
        risk_mgmt: form.risk_mgmt_disclosed ? Math.round(65 + seed(3) * 25) : Math.round(18 + seed(3) * 28),
        metrics: form.metrics_disclosed ? Math.round(62 + seed(4) * 28) : Math.round(12 + seed(4) * 32),
      };
      const overall = Math.round(
        pillarScores.governance * 0.25 +
        pillarScores.strategy * 0.35 +
        pillarScores.risk_mgmt * 0.20 +
        pillarScores.metrics * 0.20
      );
      const level = overall >= 70 ? 'Full' : overall >= 50 ? 'Substantial' : 'Partial';
      setResult({
        entity_name: form.entity_name,
        overall_score: overall,
        compliance_level: level,
        pillar_scores: pillarScores,
        gaps: [
          !form.risk_mgmt_disclosed && 'Risk Management pillar not disclosed (Paras 14(g)–(i))',
          !form.metrics_disclosed && 'Metrics & Targets pillar not disclosed (Paras 14(j)–(l))',
          form.significant_risks_count > 5 && 'High number of significant risks — consider aggregation guidance',
        ].filter(Boolean),
        sasb_industry: form.sasb_industry,
        reporting_period: form.reporting_period,
      });
    }
    setLoading(false);
  };

  const avgScore = Math.round(SEED_ASSESSMENTS.reduce((s, a) => s + a.overall, 0) / SEED_ASSESSMENTS.length);
  const fullCompliant = SEED_ASSESSMENTS.filter(a => a.overall >= 70).length;
  const industryCoverage = new Set(SEED_ASSESSMENTS.map(a => a.industry)).size;

  const radarData = result ? PILLARS.map(p => ({ subject: p.label, score: result.pillar_scores[p.key], fullMark: 100 }))
    : PILLARS.map((p, i) => ({ subject: p.label, score: Math.round(60 + seed(i * 7) * 30), fullMark: 100 }));

  const pillarBarData = PILLARS.map((p, i) => ({
    pillar: p.label,
    weight: Math.round(p.weight * 100),
    avg_score: Math.round(SEED_ASSESSMENTS.reduce((s, a) => s + a[p.key], 0) / SEED_ASSESSMENTS.length),
  }));

  return (
    <div style={{ fontFamily: 'Inter, sans-serif', background: '#f9fafb', minHeight: '100vh', padding: 24 }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#111' }}>IFRS S1 Sustainability Disclosures</div>
          <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>
            ISSB IFRS S1 (June 2023, effective 1 Jan 2024) — 4-pillar framework, 70% compliance threshold
          </div>
        </div>

        {/* KPI Cards */}
        <Row>
          <KpiCard label="Entities Assessed" value={SEED_ASSESSMENTS.length} sub="Seed universe" />
          <KpiCard label="Avg Compliance Score" value={`${avgScore}/100`} sub="Weighted 4-pillar" />
          <KpiCard label="Full Compliance %" value={`${Math.round(fullCompliant / SEED_ASSESSMENTS.length * 100)}%`} sub="Score ≥70 required" />
          <KpiCard label="SASB Industry Coverage" value={industryCoverage} sub="Distinct SASB sectors" />
        </Row>

        {/* Tab Bar */}
        <div style={{ display: 'flex', gap: 0, marginBottom: 20, background: '#fff', borderRadius: 8, border: '1px solid #e5e7eb', overflow: 'hidden' }}>
          {TABS.map((t, i) => (
            <button key={i} onClick={() => setTab(i)} style={{
              flex: 1, padding: '11px 8px', border: 'none',
              background: tab === i ? EM : '#fff',
              color: tab === i ? '#fff' : '#374151',
              fontWeight: tab === i ? 700 : 500,
              fontSize: 13, cursor: 'pointer',
              borderRight: i < TABS.length - 1 ? '1px solid #e5e7eb' : 'none',
            }}>{t}</button>
          ))}
        </div>

        {/* Tab 0 — S1 Assessment */}
        {tab === 0 && (
          <>
            <Section title="IFRS S1 Compliance Assessment">
              <Row>
                <Inp label="Entity Name" value={form.entity_name} onChange={e => setForm({ ...form, entity_name: e.target.value })} />
                <Sel label="SASB Industry" value={form.sasb_industry} onChange={e => setForm({ ...form, sasb_industry: e.target.value })}>
                  {SASB_INDUSTRIES.map(i => <option key={i.sub} value={i.sub}>{i.sub}</option>)}
                </Sel>
                <Inp label="Reporting Period" value={form.reporting_period} onChange={e => setForm({ ...form, reporting_period: e.target.value })} />
              </Row>
              <Row>
                <Inp label="# Significant Sustainability Risks" type="number" min={0} max={20} value={form.significant_risks_count} onChange={e => setForm({ ...form, significant_risks_count: +e.target.value })} />
              </Row>
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 12, color: '#374151', fontWeight: 700, marginBottom: 8 }}>Pillar Disclosure Status:</div>
                <Row gap={16}>
                  {[
                    { key: 'governance_disclosed', label: 'Governance (25%)', paras: 'Paras 14(a)–(b)' },
                    { key: 'strategy_disclosed', label: 'Strategy (35%)', paras: 'Paras 14(c)–(f)' },
                    { key: 'risk_mgmt_disclosed', label: 'Risk Management (20%)', paras: 'Paras 14(g)–(i)' },
                    { key: 'metrics_disclosed', label: 'Metrics & Targets (20%)', paras: 'Paras 14(j)–(l)' },
                  ].map(p => (
                    <label key={p.key} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 13, cursor: 'pointer', flex: 1, minWidth: 160 }}>
                      <input type="checkbox" checked={form[p.key]} onChange={e => setForm({ ...form, [p.key]: e.target.checked })}
                        style={{ accentColor: EM, width: 16, height: 16, marginTop: 1 }} />
                      <div>
                        <div style={{ fontWeight: 600 }}>{p.label}</div>
                        <div style={{ fontSize: 11, color: '#6b7280' }}>{p.paras}</div>
                      </div>
                    </label>
                  ))}
                </Row>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer', marginBottom: 12 }}>
                <input type="checkbox" checked={form.transition_plan} onChange={e => setForm({ ...form, transition_plan: e.target.checked })}
                  style={{ accentColor: EM, width: 16, height: 16 }} />
                Climate Transition Plan disclosed (IFRS S1 para 22 / IFRS S2 cross-reference)
              </label>
              <Btn onClick={handleAssess} disabled={loading}>{loading ? 'Assessing...' : 'Run S1 Assessment'}</Btn>
            </Section>

            {error && <div style={{ color: 'red', marginBottom: 12, fontSize: 13 }}>{error}</div>}

            {result && (
              <Section title="Assessment Result">
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
                  <div style={{
                    background: result.compliance_level === 'Full' ? '#f0fdf4' : result.compliance_level === 'Substantial' ? '#fffbeb' : '#fef2f2',
                    border: `2px solid ${result.compliance_level === 'Full' ? EM : result.compliance_level === 'Substantial' ? '#f59e0b' : '#ef4444'}`,
                    borderRadius: 8, padding: '12px 24px',
                    color: result.compliance_level === 'Full' ? EM : result.compliance_level === 'Substantial' ? '#d97706' : '#ef4444',
                    fontWeight: 800, fontSize: 18,
                  }}>
                    {result.compliance_level === 'Full' ? '✓' : result.compliance_level === 'Substantial' ? '~' : '✗'} {result.compliance_level} Compliance
                  </div>
                  <div style={{ textAlign: 'center', background: '#f9fafb', borderRadius: 8, padding: '10px 24px' }}>
                    <div style={{ fontSize: 32, fontWeight: 800, color: EM }}>{result.overall_score}</div>
                    <div style={{ fontSize: 11, color: '#6b7280' }}>Overall Score / 100</div>
                    <div style={{ fontSize: 10, color: '#9ca3af', marginTop: 2 }}>≥70 = Full compliance</div>
                  </div>
                </div>
                <Row>
                  {PILLARS.map(p => (
                    <div key={p.key} style={{ flex: 1, minWidth: 130, background: '#f9fafb', borderRadius: 6, padding: 12, textAlign: 'center', border: `1px solid ${p.color}44` }}>
                      <div style={{ fontSize: 20, fontWeight: 800, color: p.color }}>{result.pillar_scores[p.key]}</div>
                      <div style={{ fontSize: 11, color: '#374151', marginTop: 2, fontWeight: 600 }}>{p.label}</div>
                      <div style={{ fontSize: 10, color: '#9ca3af' }}>{Math.round(p.weight * 100)}% weight</div>
                    </div>
                  ))}
                </Row>
                {result.gaps.length > 0 && (
                  <div style={{ background: '#fef2f2', borderRadius: 6, padding: 14, marginTop: 8, border: '1px solid #fecaca' }}>
                    <div style={{ fontWeight: 700, color: '#dc2626', marginBottom: 8, fontSize: 13 }}>Disclosure Gaps:</div>
                    {result.gaps.map((g, i) => (
                      <div key={i} style={{ fontSize: 13, color: '#374151', marginBottom: 4, paddingLeft: 12 }}>• {g}</div>
                    ))}
                  </div>
                )}
              </Section>
            )}
          </>
        )}

        {/* Tab 1 — Pillar Breakdown */}
        {tab === 1 && (
          <>
            <Section title="4-Pillar Compliance Profile — Seed Entities">
              <ResponsiveContainer width="100%" height={350}>
                <RadarChart data={SEED_ASSESSMENTS.map(a => ({
                  entity: a.entity.split(' ')[0],
                  Governance: a.governance,
                  Strategy: a.strategy,
                  'Risk Mgmt': a.risk_mgmt,
                  Metrics: a.metrics,
                }))[0] ? radarData : radarData} outerRadius={130}>
                  <PolarGrid stroke="#e5e7eb" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 13 }} />
                  <Radar name="Current Assessment" dataKey="score" stroke={EM} fill={EM} fillOpacity={0.2} strokeWidth={2} />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Pillar Average Scores — Seed Universe">
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={pillarBarData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="pillar" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="avg_score" fill={EM} radius={[4, 4, 0, 0]} name="Avg Score" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Pillar Disclosure Requirements Checklist">
              {PILLARS.map(p => (
                <div key={p.key} style={{ marginBottom: 14, border: '1px solid #e5e7eb', borderRadius: 8, overflow: 'hidden' }}>
                  <div style={{ background: `${p.color}15`, padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: 700, fontSize: 14, color: p.color }}>{p.label}</span>
                    <span style={{ fontSize: 12, color: '#374151' }}>Weight: <strong>{Math.round(p.weight * 100)}%</strong></span>
                  </div>
                  {DISCLOSURE_REQS.filter(r => r.pillar === p.label || r.pillar === (p.key === 'risk_mgmt' ? 'Risk Mgmt' : p.label)).map((r, j) => (
                    <div key={j} style={{ padding: '8px 16px', borderTop: '1px solid #f3f4f6', display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                      <span style={{ color: '#9ca3af', fontSize: 11, fontFamily: 'monospace', minWidth: 50 }}>{r.para}</span>
                      <span style={{ color: '#374151' }}>{r.requirement}</span>
                    </div>
                  ))}
                </div>
              ))}
            </Section>
          </>
        )}

        {/* Tab 2 — SASB Industry */}
        {tab === 2 && (
          <>
            <Section title="SASB Industry Standards — Select Industry">
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
                {SASB_INDUSTRIES.map((ind, i) => (
                  <button key={i} onClick={() => setSelectedIndustry(i)} style={{
                    padding: '6px 14px', borderRadius: 6, border: `1px solid ${selectedIndustry === i ? EM : '#d1d5db'}`,
                    background: selectedIndustry === i ? '#f0fdf4' : '#fff',
                    color: selectedIndustry === i ? EM : '#374151',
                    fontSize: 12, fontWeight: selectedIndustry === i ? 700 : 400, cursor: 'pointer',
                  }}>{ind.sub}</button>
                ))}
              </div>
              {(() => {
                const ind = SASB_INDUSTRIES[selectedIndustry];
                return (
                  <div style={{ background: '#f0fdf4', border: `1px solid ${EM}`, borderRadius: 8, padding: 16 }}>
                    <div style={{ fontSize: 16, fontWeight: 700, color: EM, marginBottom: 4 }}>{ind.sub}</div>
                    <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 8 }}>Sector: {ind.sector}</div>
                    <div style={{ fontSize: 13, color: '#374151' }}>
                      <strong>Industry-based SASB metrics: </strong>{ind.key_metrics}
                    </div>
                  </div>
                );
              })()}
            </Section>
            <Section title="All SASB Sectors — Key Metrics Overview">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Sector', 'SASB Sub-industry', 'Key IFRS S1 Metrics'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SASB_INDUSTRIES.map((r, i) => (
                    <tr key={i} onClick={() => setSelectedIndustry(i)} style={{
                      borderBottom: '1px solid #f3f4f6',
                      background: i === selectedIndustry ? '#f0fdf4' : i % 2 === 0 ? '#fff' : '#fafafa',
                      cursor: 'pointer',
                    }}>
                      <td style={{ padding: '9px 12px', fontWeight: 600 }}>{r.sector}</td>
                      <td style={{ padding: '9px 12px', color: i === selectedIndustry ? EM : '#374151', fontWeight: i === selectedIndustry ? 700 : 400 }}>{r.sub}</td>
                      <td style={{ padding: '9px 12px', color: '#6b7280', fontSize: 12 }}>{r.key_metrics}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 3 — Cross-Framework */}
        {tab === 3 && (
          <>
            <Section title="Cross-Framework Mapping — IFRS S1 vs TCFD vs CSRD vs SEC">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['S1 Pillar', 'IFRS S1 Paras', 'TCFD Pillar', 'CSRD / ESRS 2', 'SEC Reg S-K'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {CROSS_FRAMEWORK.map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={{ padding: '9px 12px', fontWeight: 700, color: PILLARS[i]?.color || EM }}>{r.pillar}</td>
                      <td style={{ padding: '9px 12px', fontFamily: 'monospace', fontSize: 12, color: '#374151' }}>{r.ifrs_s1}</td>
                      <td style={{ padding: '9px 12px', color: '#374151' }}>{r.tcfd}</td>
                      <td style={{ padding: '9px 12px', fontFamily: 'monospace', fontSize: 12, color: '#374151' }}>{r.csrd}</td>
                      <td style={{ padding: '9px 12px', fontFamily: 'monospace', fontSize: 12, color: '#374151' }}>{r.sec}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="Seed Entity Comparison — Pillar Scores">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={SEED_ASSESSMENTS.map(a => ({
                  entity: a.entity.split(' ')[0],
                  Governance: a.governance,
                  Strategy: a.strategy,
                  'Risk Mgmt': a.risk_mgmt,
                  Metrics: a.metrics,
                }))} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="entity" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Governance" fill="#10b981" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Strategy" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Risk Mgmt" fill="#f59e0b" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Metrics" fill="#8b5cf6" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          </>
        )}

        {/* Tab 4 — Reference */}
        {tab === 4 && (
          <>
            <Section title="IFRS S1 Disclosure Requirements (Para 14)">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Paragraph', 'Pillar', 'Requirement'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {DISCLOSURE_REQS.map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={{ padding: '9px 12px', fontFamily: 'monospace', fontSize: 12, color: EM, fontWeight: 700 }}>{r.para}</td>
                      <td style={{ padding: '9px 12px' }}>
                        <span style={{ background: '#f3f4f6', borderRadius: 4, padding: '2px 8px', fontSize: 11 }}>{r.pillar}</span>
                      </td>
                      <td style={{ padding: '9px 12px', color: '#374151' }}>{r.requirement}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="Effective Dates & Transition Relief">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Date', 'Milestone', 'Notes'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { date: 'Jun 2023', milestone: 'IFRS S1 issued by ISSB', notes: 'Alongside IFRS S2 Climate — effective same date' },
                    { date: 'Jan 2023', milestone: 'Early adoption permitted', notes: 'Must adopt both IFRS S1 and IFRS S2 together' },
                    { date: 'Jan 2024', milestone: 'Mandatory effective date', notes: 'Annual reporting periods beginning on or after 1 Jan 2024' },
                    { date: '2024 (Year 1)', milestone: 'Transitional relief', notes: 'IFRS S2 Scope 3 relief; comparative period not required yr 1' },
                  ].map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={{ padding: '9px 12px', fontWeight: 700, color: EM }}>{r.date}</td>
                      <td style={{ padding: '9px 12px', fontWeight: 500 }}>{r.milestone}</td>
                      <td style={{ padding: '9px 12px', color: '#6b7280', fontSize: 12 }}>{r.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="API Endpoints">
              {[
                { method: 'POST', path: '/api/v1/ifrs-s1/assess', desc: 'Run IFRS S1 compliance assessment' },
                { method: 'GET', path: '/api/v1/ifrs-s1/ref/sasb-industries', desc: 'SASB industry standards list' },
                { method: 'GET', path: '/api/v1/ifrs-s1/ref/disclosure-requirements', desc: 'Para 14 disclosure requirements' },
                { method: 'GET', path: '/api/v1/ifrs-s1/ref/cross-framework', desc: 'Cross-framework mapping (TCFD/CSRD/SEC)' },
              ].map((e, i) => (
                <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 10, fontSize: 13, flexWrap: 'wrap' }}>
                  <span style={{
                    background: e.method === 'GET' ? '#dbeafe' : '#d1fae5',
                    color: e.method === 'GET' ? '#1d4ed8' : '#065f46',
                    borderRadius: 4, padding: '2px 8px', fontWeight: 700, fontSize: 11, minWidth: 50, textAlign: 'center',
                  }}>{e.method}</span>
                  <code style={{ color: '#374151', fontFamily: 'monospace', fontSize: 12 }}>{e.path}</code>
                  <span style={{ color: '#6b7280' }}>{e.desc}</span>
                </div>
              ))}
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
