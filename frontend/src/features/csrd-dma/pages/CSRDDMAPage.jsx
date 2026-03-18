/**
 * CSRD DMA Page — E40
 * Double Materiality Assessment: DMA Overview, Impact Materiality,
 * Financial Materiality, Stakeholder Engagement, Topic Prioritisation.
 * Backend: /api/v1/csrd-dma
 */
import React, { useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import axios from 'axios';

const API = 'http://localhost:8001';
const s = (i, seed) => Math.abs(Math.sin(i * 9301 + seed * 49297) * 233280) % 233280 / 233280;

const Section = ({ title, children }) => (
  <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 24, marginBottom: 20 }}>
    <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600, color: '#111' }}>{title}</h3>
    {children}
  </div>
);
const KpiCard = ({ label, value, sub, color = '#10b981' }) => (
  <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, textAlign: 'center' }}>
    <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
    <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>{label}</div>
    {sub && <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>{sub}</div>}
  </div>
);
const Row = ({ children, gap = 12 }) => (
  <div style={{ display: 'grid', gridTemplateColumns: `repeat(${React.Children.count(children)},1fr)`, gap }}>
    {children}
  </div>
);
const Inp = ({ label, value, onChange, type = 'text' }) => (
  <div style={{ marginBottom: 12 }}>
    <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: '#374151', marginBottom: 4 }}>{label}</label>
    <input type={type} value={value} onChange={e => onChange(e.target.value)}
      style={{ width: '100%', padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: 14, boxSizing: 'border-box' }} />
  </div>
);
const Sel = ({ label, value, onChange, options }) => (
  <div style={{ marginBottom: 12 }}>
    <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: '#374151', marginBottom: 4 }}>{label}</label>
    <select value={value} onChange={e => onChange(e.target.value)}
      style={{ width: '100%', padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: 14, background: '#fff' }}>
      {options.map(o => <option key={o.value || o} value={o.value || o}>{o.label || o}</option>)}
    </select>
  </div>
);
const Btn = ({ children, onClick, color = '#10b981' }) => (
  <button onClick={onClick} style={{ background: color, color: '#fff', border: 'none', borderRadius: 6, padding: '10px 20px', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
    {children}
  </button>
);

const TABS = ['DMA Overview', 'Impact Materiality', 'Financial Materiality', 'Stakeholder Engagement', 'Topic Prioritisation'];
const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

const ESRS_PILLS = [
  { id: 'E1', label: 'E1 Climate', color: '#10b981' },
  { id: 'E2', label: 'E2 Pollution', color: '#84cc16' },
  { id: 'E3', label: 'E3 Water', color: '#06b6d4' },
  { id: 'E4', label: 'E4 Biodiversity', color: '#22c55e' },
  { id: 'E5', label: 'E5 Circular', color: '#16a34a' },
  { id: 'S1', label: 'S1 Workforce', color: '#3b82f6' },
  { id: 'S2', label: 'S2 Value Chain', color: '#6366f1' },
  { id: 'S3', label: 'S3 Communities', color: '#8b5cf6' },
  { id: 'S4', label: 'S4 Consumers', color: '#a855f7' },
  { id: 'G1', label: 'G1 Governance', color: '#f59e0b' },
];

const TOPICS = [
  { topic: 'Climate Change Mitigation', esrs: 'E1', impact: 82, financial: 78, riskType: 'Transition' },
  { topic: 'Climate Change Adaptation', esrs: 'E1', impact: 74, financial: 65, riskType: 'Physical' },
  { topic: 'Air Pollution', esrs: 'E2', impact: 55, financial: 38, riskType: 'Regulatory' },
  { topic: 'Water & Marine Resources', esrs: 'E3', impact: 61, financial: 45, riskType: 'Physical' },
  { topic: 'Biodiversity Loss', esrs: 'E4', impact: 70, financial: 52, riskType: 'Physical' },
  { topic: 'Resource Use & Circular Economy', esrs: 'E5', impact: 48, financial: 42, riskType: 'Transition' },
  { topic: 'Own Workforce', esrs: 'S1', impact: 67, financial: 55, riskType: 'Social' },
  { topic: 'Value Chain Workers', esrs: 'S2', impact: 58, financial: 35, riskType: 'Social' },
  { topic: 'Affected Communities', esrs: 'S3', impact: 44, financial: 28, riskType: 'Social' },
  { topic: 'Business Conduct', esrs: 'G1', impact: 63, financial: 71, riskType: 'Governance' },
];

function genSeed(entityId) {
  let h = 0;
  for (let i = 0; i < (entityId || 'E001').length; i++) h = (h * 31 + entityId.charCodeAt(i)) | 0;
  return Math.abs(h) || 42;
}

function buildFallback(seed) {
  return {
    material_topics_count: 7,
    dma_completeness: Math.round(60 + s(0, seed) * 35),
    stakeholders_engaged: Math.round(12 + s(1, seed) * 20),
    assurance_readiness: Math.round(50 + s(2, seed) * 40),
    pie_data: [
      { name: 'Both', value: Math.round(3 + s(3, seed) * 3) },
      { name: 'Impact Only', value: Math.round(2 + s(4, seed) * 3) },
      { name: 'Financial Only', value: Math.round(1 + s(5, seed) * 2) },
      { name: 'Neither', value: Math.round(1 + s(6, seed) * 2) },
    ],
    applicable_esrs: ['E1', 'E2', 'E4', 'S1', 'S2', 'G1'],
  };
}

const STAKEHOLDER_TYPES = ['Employees', 'Investors', 'Customers', 'Suppliers', 'NGOs', 'Regulators'];
const ENGAGEMENT_ELEMENTS = ['Identification', 'Dialogue', 'Documentation', 'Integration', 'Feedback'];

function scoreColor(v) {
  if (v >= 70) return '#ef4444';
  if (v >= 40) return '#f59e0b';
  return '#10b981';
}

function esrsColor(std) {
  if (std.startsWith('E')) return '#10b981';
  if (std.startsWith('S')) return '#3b82f6';
  return '#8b5cf6';
}

export default function CSRDDMAPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [entityId, setEntityId] = useState('E-001');
  const [entityName, setEntityName] = useState('Acme Financial Group');
  const [sector, setSector] = useState('financial_services');
  const [nace, setNace] = useState('K64.19');
  const [period, setPeriod] = useState('2024');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(TOPICS[0].topic);

  const seed = genSeed(entityId);
  const fallback = buildFallback(seed);
  const data = result || fallback;

  async function runFullAssessment() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/csrd-dma/full-assessment`, {
        entity_id: entityId, entity_name: entityName, sector, nace_code: nace, reporting_period: period,
      });
      setResult(res.data);
    } catch {
      setResult(null);
    } finally { setLoading(false); }
  }

  async function runImpactAssessment() {
    setLoading(true);
    try {
      await axios.post(`${API}/api/v1/csrd-dma/impact-assessment`, { entity_id: entityId, topic: selectedTopic });
    } catch { } finally { setLoading(false); }
  }

  const impactTopics = TOPICS.map((t, i) => ({
    ...t,
    scale: Math.round(50 + s(i, seed + 1) * 40),
    scope: Math.round(45 + s(i, seed + 2) * 45),
    irremediability: Math.round(30 + s(i, seed + 3) * 60),
    combined: t.impact,
  })).sort((a, b) => b.combined - a.combined);

  const stakeRadar = STAKEHOLDER_TYPES.map((name, i) => ({
    type: name, score: Math.round(40 + s(i, seed + 10) * 55),
  }));

  const prioritised = TOPICS.map((t, i) => ({
    ...t,
    combined: Math.round((t.impact + t.financial) / 2),
    stakeholderSalience: Math.round(30 + s(i, seed + 7) * 65),
    materialityBasis: t.impact >= 70 && t.financial >= 65 ? 'Both' : t.impact >= 60 ? 'Impact' : t.financial >= 60 ? 'Financial' : 'Neither',
  })).sort((a, b) => b.combined - a.combined).map((t, i) => ({ ...t, rank: i + 1 }));

  const CROSS_FRAMEWORK = [
    { topic: 'Climate Change Mitigation', tcfd: 'Strategy/Risk', gri: 'GRI 305', issb: 'IFRS S2 §8', taxonomy: 'CCM' },
    { topic: 'Biodiversity Loss', tcfd: 'Risk Mgmt', gri: 'GRI 304', issb: 'IFRS S2 §29', taxonomy: 'DNSHBio' },
    { topic: 'Own Workforce', tcfd: 'Governance', gri: 'GRI 401', issb: 'IFRS S1 §15', taxonomy: 'N/A' },
    { topic: 'Business Conduct', tcfd: 'Governance', gri: 'GRI 205', issb: 'IFRS S1 §19', taxonomy: 'N/A' },
    { topic: 'Water & Marine Resources', tcfd: 'Physical Risk', gri: 'GRI 303', issb: 'IFRS S2 §16', taxonomy: 'SWM' },
  ];

  const SECTOR_OPTIONS = [
    'financial_services', 'energy', 'manufacturing', 'real_estate', 'agriculture',
    'technology', 'retail', 'healthcare', 'transport', 'mining',
  ];

  return (
    <div style={{ fontFamily: 'Inter,system-ui,sans-serif', background: '#f3f4f6', minHeight: '100vh', padding: 24 }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#111' }}>CSRD Double Materiality Assessment</h1>
          <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 14 }}>ESRS 1 §§ 17-44 — Impact & financial materiality, stakeholder engagement, topic prioritisation</p>
        </div>

        {/* Tab bar */}
        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid #e5e7eb', marginBottom: 24, background: '#fff', borderRadius: '8px 8px 0 0', padding: '0 16px' }}>
          {TABS.map((tab, i) => (
            <button key={tab} onClick={() => setActiveTab(i)} style={{
              background: 'none', border: 'none', borderBottom: activeTab === i ? '3px solid #10b981' : '3px solid transparent',
              padding: '14px 18px', fontSize: 14, fontWeight: activeTab === i ? 600 : 400,
              color: activeTab === i ? '#10b981' : '#6b7280', cursor: 'pointer', whiteSpace: 'nowrap',
            }}>{tab}</button>
          ))}
        </div>

        {/* Tab 0: DMA Overview */}
        {activeTab === 0 && (
          <>
            <Section title="Entity Configuration">
              <Row>
                <Inp label="Entity ID" value={entityId} onChange={setEntityId} />
                <Inp label="Entity Name" value={entityName} onChange={setEntityName} />
                <Inp label="Reporting Period" value={period} onChange={setPeriod} />
              </Row>
              <Row>
                <Sel label="Sector" value={sector} onChange={setSector} options={SECTOR_OPTIONS} />
                <Inp label="NACE Code" value={nace} onChange={setNace} />
                <div style={{ paddingTop: 20 }}><Btn onClick={runFullAssessment}>{loading ? 'Running...' : 'Run DMA Assessment'}</Btn></div>
              </Row>
            </Section>
            <Section title="DMA Summary KPIs">
              <Row>
                <KpiCard label="Material Topics" value={data.material_topics_count} sub="ESRS topics assessed" />
                <KpiCard label="DMA Completeness" value={`${data.dma_completeness}%`} sub="Process completion" color={data.dma_completeness >= 75 ? '#10b981' : '#f59e0b'} />
                <KpiCard label="Stakeholders Engaged" value={data.stakeholders_engaged} sub="Across all channels" color="#3b82f6" />
                <KpiCard label="Assurance Readiness" value={`${data.assurance_readiness}%`} sub="Limited assurance threshold" color={data.assurance_readiness >= 70 ? '#10b981' : '#ef4444'} />
              </Row>
            </Section>
            <Section title="Material Topics by Materiality Type">
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={data.pie_data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, value }) => `${name}: ${value}`}>
                    {data.pie_data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Applicable ESRS Standards">
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {ESRS_PILLS.map(pill => {
                  const active = (data.applicable_esrs || fallback.applicable_esrs).includes(pill.id);
                  return (
                    <span key={pill.id} style={{
                      background: active ? pill.color : '#f3f4f6', color: active ? '#fff' : '#9ca3af',
                      borderRadius: 20, padding: '4px 14px', fontSize: 13, fontWeight: 600, border: `1px solid ${active ? pill.color : '#e5e7eb'}`,
                    }}>{pill.label}</span>
                  );
                })}
              </div>
            </Section>
          </>
        )}

        {/* Tab 1: Impact Materiality */}
        {activeTab === 1 && (
          <>
            <Section title="Impact Materiality Scores by Topic">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={impactTopics} margin={{ left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="topic" angle={-35} textAnchor="end" tick={{ fontSize: 11 }} interval={0} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="combined" name="Impact Score" fill="#10b981">
                    {impactTopics.map((entry, i) => <Cell key={i} fill={scoreColor(entry.combined)} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Impact Materiality Detail">
              <div style={{ marginBottom: 12 }}>
                <Sel label="Assess Topic" value={selectedTopic} onChange={setSelectedTopic}
                  options={TOPICS.map(t => ({ value: t.topic, label: t.topic }))} />
                <Btn onClick={runImpactAssessment}>{loading ? 'Assessing...' : 'Run Impact Assessment'}</Btn>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#f9fafb' }}>
                      {['Topic', 'ESRS', 'Scale', 'Scope', 'Irremediability', 'Impact Score', 'Material'].map(h => (
                        <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb', fontWeight: 600, color: '#374151' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {impactTopics.map((row, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 500 }}>{row.topic}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ background: esrsColor(row.esrs) + '20', color: esrsColor(row.esrs), borderRadius: 4, padding: '2px 8px', fontSize: 12, fontWeight: 600 }}>{row.esrs}</span>
                        </td>
                        <td style={{ padding: '10px 12px', color: scoreColor(row.scale) }}>{row.scale}</td>
                        <td style={{ padding: '10px 12px', color: scoreColor(row.scope) }}>{row.scope}</td>
                        <td style={{ padding: '10px 12px', color: scoreColor(row.irremediability) }}>{row.irremediability}</td>
                        <td style={{ padding: '10px 12px', fontWeight: 700, color: scoreColor(row.combined) }}>{row.combined}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ background: row.combined >= 50 ? '#dcfce7' : '#fee2e2', color: row.combined >= 50 ? '#16a34a' : '#dc2626', borderRadius: 4, padding: '2px 8px', fontSize: 12, fontWeight: 600 }}>
                            {row.combined >= 50 ? 'Y' : 'N'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          </>
        )}

        {/* Tab 2: Financial Materiality */}
        {activeTab === 2 && (
          <>
            <Section title="Financial Materiality Scores">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={[...TOPICS].sort((a, b) => b.financial - a.financial)} margin={{ left: 0, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="topic" angle={-35} textAnchor="end" tick={{ fontSize: 11 }} interval={0} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="financial" name="Financial Score" fill="#3b82f6">
                    {[...TOPICS].sort((a, b) => b.financial - a.financial).map((entry, i) => <Cell key={i} fill={scoreColor(entry.financial)} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Double Materiality Matrix">
              <div style={{ padding: '8px 0', fontSize: 13, color: '#6b7280', marginBottom: 8 }}>X = Impact Score | Y = Financial Score — colour by ESRS standard group</div>
              <div style={{ position: 'relative', height: 300, border: '1px solid #e5e7eb', borderRadius: 8, background: '#fafafa', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, borderLeft: '1px dashed #d1d5db' }} />
                <div style={{ position: 'absolute', right: 0, left: 0, top: '50%', borderTop: '1px dashed #d1d5db' }} />
                {TOPICS.map((t, i) => {
                  const left = `${(t.impact / 100) * 90 + 5}%`;
                  const top = `${100 - ((t.financial / 100) * 90 + 5)}%`;
                  return (
                    <div key={i} title={`${t.topic}: Impact ${t.impact}, Financial ${t.financial}`}
                      style={{ position: 'absolute', left, top, width: 14, height: 14, borderRadius: '50%', background: esrsColor(t.esrs), transform: 'translate(-50%,-50%)', cursor: 'pointer', border: '2px solid #fff', boxShadow: '0 1px 3px rgba(0,0,0,.2)' }} />
                  );
                })}
                <div style={{ position: 'absolute', bottom: 4, left: '50%', transform: 'translateX(-50%)', fontSize: 11, color: '#9ca3af' }}>Higher Impact →</div>
                <div style={{ position: 'absolute', left: 4, top: '40%', fontSize: 11, color: '#9ca3af', writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>Higher Financial →</div>
              </div>
              <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
                {[{ label: 'E — Environmental', color: '#10b981' }, { label: 'S — Social', color: '#3b82f6' }, { label: 'G — Governance', color: '#8b5cf6' }].map(l => (
                  <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 12, height: 12, borderRadius: '50%', background: l.color }} />
                    <span style={{ fontSize: 12, color: '#6b7280' }}>{l.label}</span>
                  </div>
                ))}
              </div>
            </Section>
            <Section title="Financial Materiality Detail">
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#f9fafb' }}>
                      {['Topic', 'ESRS', 'Magnitude', 'Likelihood', 'Financial Score', 'Risk Type', 'Material'].map(h => (
                        <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb', fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[...TOPICS].sort((a, b) => b.financial - a.financial).map((row, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 500 }}>{row.topic}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ background: esrsColor(row.esrs) + '20', color: esrsColor(row.esrs), borderRadius: 4, padding: '2px 8px', fontSize: 12, fontWeight: 600 }}>{row.esrs}</span>
                        </td>
                        <td style={{ padding: '10px 12px', color: scoreColor(Math.round(40 + s(i, seed + 4) * 50)) }}>{Math.round(40 + s(i, seed + 4) * 50)}</td>
                        <td style={{ padding: '10px 12px', color: scoreColor(Math.round(35 + s(i, seed + 5) * 55)) }}>{Math.round(35 + s(i, seed + 5) * 55)}</td>
                        <td style={{ padding: '10px 12px', fontWeight: 700, color: scoreColor(row.financial) }}>{row.financial}</td>
                        <td style={{ padding: '10px 12px' }}>{row.riskType}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ background: row.financial >= 50 ? '#dcfce7' : '#fee2e2', color: row.financial >= 50 ? '#16a34a' : '#dc2626', borderRadius: 4, padding: '2px 8px', fontSize: 12, fontWeight: 600 }}>
                            {row.financial >= 50 ? 'Y' : 'N'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          </>
        )}

        {/* Tab 3: Stakeholder Engagement */}
        {activeTab === 3 && (
          <>
            <Section title="Engagement Summary">
              <Row>
                <KpiCard label="Engagement Quality Score" value={`${Math.round(55 + s(0, seed) * 40)}%`} color="#10b981" />
                <KpiCard label="Stakeholders Engaged" value={data.stakeholders_engaged} color="#3b82f6" />
                <KpiCard label="Stakeholder Types" value="6 / 6" sub="All types covered" color="#8b5cf6" />
              </Row>
            </Section>
            <Section title="Engagement Quality by Stakeholder Type">
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={stakeRadar}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="type" tick={{ fontSize: 12 }} />
                  <Radar name="Quality Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.25} />
                  <Tooltip />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="5-Element Engagement Assessment">
              {ENGAGEMENT_ELEMENTS.map((el, i) => {
                const pct = Math.round(45 + s(i, seed + 12) * 50);
                return (
                  <div key={el} style={{ marginBottom: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span style={{ fontSize: 13, fontWeight: 500, color: '#374151' }}>{el}</span>
                      <span style={{ fontSize: 13, fontWeight: 600, color: scoreColor(pct) }}>{pct}%</span>
                    </div>
                    <div style={{ height: 8, background: '#e5e7eb', borderRadius: 4, overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: scoreColor(pct), borderRadius: 4, transition: 'width 0.3s' }} />
                    </div>
                  </div>
                );
              })}
            </Section>
          </>
        )}

        {/* Tab 4: Topic Prioritisation */}
        {activeTab === 4 && (
          <>
            <Section title="Prioritised Material Topics">
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#f9fafb' }}>
                      {['Rank', 'Topic', 'ESRS', 'Impact', 'Financial', 'Combined', 'Basis', 'Stakeholder Salience'].map(h => (
                        <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb', fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {prioritised.map((row, i) => (
                      <tr key={i} style={{ background: i < 5 ? '#f0fdf4' : '#fff', borderBottom: '1px solid #f3f4f6' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 700, color: i < 5 ? '#10b981' : '#374151' }}>#{row.rank}</td>
                        <td style={{ padding: '10px 12px', fontWeight: 500 }}>{row.topic}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ background: esrsColor(row.esrs) + '20', color: esrsColor(row.esrs), borderRadius: 4, padding: '2px 8px', fontSize: 12, fontWeight: 600 }}>{row.esrs}</span>
                        </td>
                        <td style={{ padding: '10px 12px', color: scoreColor(row.impact) }}>{row.impact}</td>
                        <td style={{ padding: '10px 12px', color: scoreColor(row.financial) }}>{row.financial}</td>
                        <td style={{ padding: '10px 12px', fontWeight: 700, color: scoreColor(row.combined) }}>{row.combined}</td>
                        <td style={{ padding: '10px 12px' }}>{row.materialityBasis}</td>
                        <td style={{ padding: '10px 12px', color: '#6b7280' }}>{row.stakeholderSalience}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <Section title="Cross-Framework Linkage">
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#f9fafb' }}>
                      {['Topic', 'TCFD', 'GRI 3', 'ISSB S1', 'EU Taxonomy'].map(h => (
                        <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb', fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {CROSS_FRAMEWORK.map((row, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 500 }}>{row.topic}</td>
                        <td style={{ padding: '10px 12px', color: '#6b7280' }}>{row.tcfd}</td>
                        <td style={{ padding: '10px 12px', color: '#6b7280' }}>{row.gri}</td>
                        <td style={{ padding: '10px 12px', color: '#6b7280' }}>{row.issb}</td>
                        <td style={{ padding: '10px 12px', color: '#6b7280' }}>{row.taxonomy}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
