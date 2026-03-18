/**
 * ESMAFundNamesPage.jsx — Route: /esma-fund-names
 * ESMA Fund Names Guidelines (ESMA/2024/249)
 * 80% threshold for ESG/sustainability fund naming compliance
 * Sprint 14 — E16
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
const TABS = ['Name Assessment', 'Batch Screening', 'Exclusion Tracker', 'Fund Universe', 'Reference'];

const SEED_FUNDS = [
  { name: 'Green Future UCITS Fund', type: 'UCITS', esg_pct: 85, sust_pct: 72, compliant: true },
  { name: 'Sustainable World AIF', type: 'AIF', esg_pct: 78, sust_pct: 65, compliant: false },
  { name: 'Paris Aligned Leaders ETF', type: 'UCITS', esg_pct: 92, sust_pct: 88, compliant: true },
  { name: 'Climate Transition ELTIF', type: 'ELTIF', esg_pct: 81, sust_pct: 70, compliant: true },
  { name: 'ESG Core Portfolio Fund', type: 'UCITS', esg_pct: 76, sust_pct: 58, compliant: false },
  { name: 'Impact Opportunities AIF', type: 'AIF', esg_pct: 88, sust_pct: 82, compliant: true },
  { name: 'Net Zero 2050 UCITS', type: 'UCITS', esg_pct: 91, sust_pct: 84, compliant: true },
  { name: 'Responsible Growth Fund', type: 'AIF', esg_pct: 74, sust_pct: 61, compliant: false },
];

const PAB_EXCLUSIONS = [
  {
    category: 'Fossil Fuels', required: true,
    items: ['Coal extraction (>1% revenue threshold)', 'Unconventional oil & gas exploration', 'Conventional oil & gas (>50% revenue)'],
  },
  {
    category: 'Controversial Weapons', required: true,
    items: ['Cluster munitions', 'Anti-personnel mines', 'Biological/chemical weapons', 'Nuclear weapons (non-NPT)'],
  },
  {
    category: 'High-Carbon Sectors', required: false,
    items: ['Power generation (>100 gCO2e/kWh)', 'Cement production (>0.5 tCO2/t)', 'Steel manufacturing (>1.4 tCO2/t)'],
  },
  {
    category: 'Other Exclusions', required: false,
    items: ['Tobacco production & distribution', 'Gambling operators', 'Adult entertainment content'],
  },
];

const RADAR_FUNDS = [
  { subject: 'ESG Score', A: 92, B: 78, C: 85, D: 70, E: 88 },
  { subject: 'Sustainability', A: 88, B: 65, C: 80, D: 68, E: 82 },
  { subject: 'Transition', A: 75, B: 72, C: 90, D: 55, E: 70 },
  { subject: 'Impact', A: 68, B: 60, C: 72, D: 80, E: 85 },
  { subject: 'Exclusions', A: 95, B: 85, C: 90, D: 75, E: 88 },
];

const TERM_CATEGORIES = [
  { category: 'ESG-related', terms: 'ESG, Environmental, Social, Governance, Responsible', threshold: '≥80% ESG investments' },
  { category: 'Sustainability-related', terms: 'Sustainable, Sustainability, SDG-aligned, Green', threshold: '≥80% sustainable investments (Art 2(17) SFDR)' },
  { category: 'Impact-related', terms: 'Impact, Positive Impact, Net Positive, Thematic', threshold: '≥80% + measurable impact objective' },
  { category: 'Transition-related', terms: 'Transition, Paris-aligned, Net Zero, Climate', threshold: '≥80% + PAB exclusions + decarbonisation trajectory' },
];

const RADAR_COLORS = [EM, '#3b82f6', '#f59e0b', '#8b5cf6', '#ef4444'];
const RADAR_NAMES = ['Paris Leaders ETF', 'Sustainable World AIF', 'Climate Transition ELTIF', 'ESG Core Portfolio', 'Impact Opportunities'];

/* ── Helpers ── */
function inferTermCategory(name) {
  const n = name.toLowerCase();
  if (n.includes('paris') || n.includes('climate') || n.includes('net zero') || n.includes('transition')) return 'transition';
  if (n.includes('impact')) return 'impact';
  if (n.includes('sustain')) return 'sustainability';
  return 'esg';
}

/* ── Page ── */
export default function ESMAFundNamesPage() {
  const [tab, setTab] = useState(0);
  const [form, setForm] = useState({
    fund_name: 'Green Horizon Sustainable Fund',
    fund_type: 'UCITS',
    esg_investment_pct: 82,
    sustainability_investment_pct: 68,
    has_pab_exclusions: true,
    has_ctb_exclusions: false,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAssess = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.post(`${API}/api/v1/esma-fund-names/assess`, form);
      setResult(res.data);
    } catch {
      const termType = inferTermCategory(form.fund_name);
      const needsPAB = termType === 'transition';
      const esgOk = form.esg_investment_pct >= 80;
      const sustOk = form.sustainability_investment_pct >= 80;
      const compliant = esgOk && (!needsPAB || form.has_pab_exclusions);
      setResult({
        fund_name: form.fund_name,
        term_category: termType,
        esg_threshold_met: esgOk,
        sustainability_threshold_met: sustOk,
        pab_required: needsPAB,
        pab_applied: form.has_pab_exclusions,
        compliant,
        effective_date: form.fund_type === 'UCITS' ? '21 Nov 2024 (new funds) / 21 May 2025 (existing)' : '21 May 2025',
        remediation: [
          !esgOk ? `Raise ESG investment allocation to ≥80% (current: ${form.esg_investment_pct}%)` : null,
          needsPAB && !form.has_pab_exclusions ? 'Apply Paris-Aligned Benchmark (PAB) exclusions for transition-related fund name' : null,
        ].filter(Boolean),
      });
    }
    setLoading(false);
  };

  /* KPI derivations */
  const compliantCount = SEED_FUNDS.filter(f => f.compliant).length;
  const avgESG = Math.round(SEED_FUNDS.reduce((s, f) => s + f.esg_pct, 0) / SEED_FUNDS.length);
  const remCount = SEED_FUNDS.filter(f => !f.compliant).length;

  const distData = [
    { range: '< 75%', count: SEED_FUNDS.filter(f => f.esg_pct < 75).length },
    { range: '75–79%', count: SEED_FUNDS.filter(f => f.esg_pct >= 75 && f.esg_pct < 80).length },
    { range: '80–84%', count: SEED_FUNDS.filter(f => f.esg_pct >= 80 && f.esg_pct < 85).length },
    { range: '85–89%', count: SEED_FUNDS.filter(f => f.esg_pct >= 85 && f.esg_pct < 90).length },
    { range: '≥ 90%', count: SEED_FUNDS.filter(f => f.esg_pct >= 90).length },
  ];

  return (
    <div style={{ fontFamily: 'Inter, sans-serif', background: '#f9fafb', minHeight: '100vh', padding: 24 }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#111' }}>ESMA Fund Names Guidelines</div>
          <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>
            ESMA/2024/249 — 80% threshold for ESG/sustainability fund naming compliance
          </div>
        </div>

        {/* KPI Cards */}
        <Row>
          <KpiCard label="Funds Assessed" value={SEED_FUNDS.length} sub="Total in batch universe" />
          <KpiCard label="Compliant %" value={`${Math.round(compliantCount / SEED_FUNDS.length * 100)}%`} sub={`${compliantCount} of ${SEED_FUNDS.length} funds`} />
          <KpiCard label="Avg ESG %" value={`${avgESG}%`} sub="vs 80% threshold" />
          <KpiCard label="Remediation Required" value={remCount} sub="Funds needing action" />
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

        {/* Tab 0 — Name Assessment */}
        {tab === 0 && (
          <>
            <Section title="Fund Name Compliance Assessment">
              <Row>
                <Inp label="Fund Name" value={form.fund_name} onChange={e => setForm({ ...form, fund_name: e.target.value })} />
                <Sel label="Fund Type" value={form.fund_type} onChange={e => setForm({ ...form, fund_type: e.target.value })}>
                  <option>UCITS</option><option>AIF</option><option>ELTIF</option>
                </Sel>
              </Row>
              <Row>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 12, color: '#374151', fontWeight: 600 }}>ESG Investment % — <strong style={{ color: EM }}>{form.esg_investment_pct}%</strong></label>
                  <input type="range" min={0} max={100} value={form.esg_investment_pct}
                    onChange={e => setForm({ ...form, esg_investment_pct: +e.target.value })}
                    style={{ width: '100%', accentColor: EM, marginTop: 6, display: 'block' }} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
                    <span>0%</span><span style={{ color: EM, fontWeight: 600 }}>80% threshold</span><span>100%</span>
                  </div>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 12, color: '#374151', fontWeight: 600 }}>Sustainability Investment % — <strong style={{ color: EM }}>{form.sustainability_investment_pct}%</strong></label>
                  <input type="range" min={0} max={100} value={form.sustainability_investment_pct}
                    onChange={e => setForm({ ...form, sustainability_investment_pct: +e.target.value })}
                    style={{ width: '100%', accentColor: EM, marginTop: 6, display: 'block' }} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
                    <span>0%</span><span style={{ color: EM, fontWeight: 600 }}>80% threshold</span><span>100%</span>
                  </div>
                </div>
              </Row>
              <Row>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer', padding: '6px 0' }}>
                  <input type="checkbox" checked={form.has_pab_exclusions}
                    onChange={e => setForm({ ...form, has_pab_exclusions: e.target.checked })}
                    style={{ accentColor: EM, width: 16, height: 16 }} />
                  Paris-Aligned Benchmark (PAB) Exclusions Applied
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer', padding: '6px 0' }}>
                  <input type="checkbox" checked={form.has_ctb_exclusions}
                    onChange={e => setForm({ ...form, has_ctb_exclusions: e.target.checked })}
                    style={{ accentColor: EM, width: 16, height: 16 }} />
                  Climate Transition Benchmark (CTB) Exclusions Applied
                </label>
              </Row>
              <div style={{ marginTop: 8 }}>
                <Btn onClick={handleAssess} disabled={loading}>{loading ? 'Assessing...' : 'Run Assessment'}</Btn>
              </div>
            </Section>

            {error && <div style={{ color: 'red', marginBottom: 12, fontSize: 13 }}>{error}</div>}

            {result && (
              <Section title="Assessment Result">
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 16, flexWrap: 'wrap' }}>
                  <div style={{
                    background: result.compliant ? '#f0fdf4' : '#fef2f2',
                    border: `2px solid ${result.compliant ? EM : '#ef4444'}`,
                    borderRadius: 8, padding: '12px 24px',
                    color: result.compliant ? EM : '#ef4444',
                    fontWeight: 800, fontSize: 18, letterSpacing: 1,
                  }}>
                    {result.compliant ? '✓ COMPLIANT' : '✗ NON-COMPLIANT'}
                  </div>
                  <div style={{ fontSize: 13, color: '#374151', lineHeight: 2 }}>
                    <div>Term Category: <strong style={{ textTransform: 'capitalize' }}>{result.term_category}-related</strong></div>
                    <div>Effective Date: <strong>{result.effective_date}</strong></div>
                    <div>PAB Required: <strong>{result.pab_required ? 'Yes' : 'No'}</strong></div>
                  </div>
                </div>
                <Row>
                  {[
                    { label: 'ESG Threshold (≥80%)', met: result.esg_threshold_met, val: `${form.esg_investment_pct}%` },
                    { label: 'Sustainability Threshold (≥80%)', met: result.sustainability_threshold_met, val: `${form.sustainability_investment_pct}%` },
                    { label: 'PAB Exclusions', met: !result.pab_required || result.pab_applied, val: result.pab_applied ? 'Applied' : result.pab_required ? 'Missing' : 'Not Required' },
                  ].map((c, i) => (
                    <div key={i} style={{ flex: 1, minWidth: 160, background: c.met ? '#f0fdf4' : '#fef2f2', borderRadius: 6, padding: 12, border: `1px solid ${c.met ? '#bbf7d0' : '#fecaca'}` }}>
                      <div style={{ fontSize: 11, color: '#6b7280' }}>{c.label}</div>
                      <div style={{ fontWeight: 700, color: c.met ? EM : '#ef4444', marginTop: 4, fontSize: 15 }}>{c.val}</div>
                      <div style={{ fontSize: 11, marginTop: 2, color: c.met ? EM : '#ef4444', fontWeight: 600 }}>{c.met ? 'Met' : 'Not Met'}</div>
                    </div>
                  ))}
                </Row>
                {result.remediation.length > 0 && (
                  <div style={{ background: '#fef2f2', borderRadius: 6, padding: 14, marginTop: 8, border: '1px solid #fecaca' }}>
                    <div style={{ fontWeight: 700, color: '#dc2626', marginBottom: 8, fontSize: 13 }}>Remediation Actions Required:</div>
                    {result.remediation.map((r, i) => (
                      <div key={i} style={{ fontSize: 13, color: '#374151', marginBottom: 4, paddingLeft: 12 }}>• {r}</div>
                    ))}
                  </div>
                )}
                {result.compliant && (
                  <div style={{ background: '#f0fdf4', borderRadius: 6, padding: 12, marginTop: 8, border: '1px solid #bbf7d0', fontSize: 13, color: '#065f46' }}>
                    Fund name is compliant with ESMA/2024/249 guidelines. No remediation required.
                  </div>
                )}
              </Section>
            )}
          </>
        )}

        {/* Tab 1 — Batch Screening */}
        {tab === 1 && (
          <>
            <Section title="ESG Investment % Distribution — Batch Universe">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={distData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="range" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(v) => [`${v} funds`, 'Count']} />
                  <Bar dataKey="count" fill={EM} radius={[4, 4, 0, 0]} name="Funds" />
                </BarChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
                <div style={{ fontSize: 12, color: '#374151' }}>
                  <strong style={{ color: EM }}>{SEED_FUNDS.filter(f => f.esg_pct >= 80).length}</strong> funds meet 80% threshold
                </div>
                <div style={{ fontSize: 12, color: '#374151' }}>
                  <strong style={{ color: '#ef4444' }}>{SEED_FUNDS.filter(f => f.esg_pct < 80).length}</strong> funds below threshold
                </div>
              </div>
            </Section>
            <Section title="Fund Screening Results">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Fund Name', 'Type', 'ESG %', 'Sust %', 'Status', 'Remediation Flag'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12, color: '#374151' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SEED_FUNDS.map((f, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={{ padding: '9px 12px', fontWeight: 500 }}>{f.name}</td>
                      <td style={{ padding: '9px 12px' }}>
                        <span style={{ background: '#e5e7eb', borderRadius: 4, padding: '2px 8px', fontSize: 11, fontWeight: 600 }}>{f.type}</span>
                      </td>
                      <td style={{ padding: '9px 12px', color: f.esg_pct >= 80 ? EM : '#ef4444', fontWeight: 700 }}>{f.esg_pct}%</td>
                      <td style={{ padding: '9px 12px', color: f.sust_pct >= 80 ? EM : '#f59e0b', fontWeight: 700 }}>{f.sust_pct}%</td>
                      <td style={{ padding: '9px 12px' }}>
                        <span style={{
                          background: f.compliant ? '#f0fdf4' : '#fef2f2',
                          color: f.compliant ? EM : '#ef4444',
                          borderRadius: 4, padding: '2px 10px', fontWeight: 700, fontSize: 11,
                          border: `1px solid ${f.compliant ? '#bbf7d0' : '#fecaca'}`,
                        }}>
                          {f.compliant ? 'Compliant' : 'Non-Compliant'}
                        </span>
                      </td>
                      <td style={{ padding: '9px 12px', fontSize: 12, color: '#6b7280' }}>
                        {f.compliant ? '—' : f.esg_pct < 80 ? 'Raise ESG % to ≥80' : 'Apply PAB exclusions'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 2 — Exclusion Tracker */}
        {tab === 2 && (
          <>
            <Section title="PAB / CTB Exclusion Requirements">
              <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 16, lineHeight: 1.6 }}>
                Paris-Aligned Benchmark (PAB) exclusions are <strong>mandatory</strong> for fund names using transition,
                Paris-aligned, net-zero, or climate-related terms per ESMA/2024/249. CTB exclusions are required for
                climate transition benchmark fund names.
              </div>
              {PAB_EXCLUSIONS.map((cat, i) => (
                <div key={i} style={{ marginBottom: 16, border: '1px solid #e5e7eb', borderRadius: 8, overflow: 'hidden' }}>
                  <div style={{
                    background: cat.required ? '#f0fdf4' : '#f9fafb',
                    padding: '10px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  }}>
                    <span style={{ fontWeight: 700, fontSize: 14, color: '#111' }}>{cat.category}</span>
                    {cat.required
                      ? <span style={{ background: EM, color: '#fff', borderRadius: 4, padding: '2px 10px', fontSize: 11, fontWeight: 700 }}>PAB MANDATORY</span>
                      : <span style={{ background: '#f3f4f6', color: '#6b7280', borderRadius: 4, padding: '2px 10px', fontSize: 11, fontWeight: 600 }}>Best Practice</span>
                    }
                  </div>
                  {cat.items.map((item, j) => (
                    <div key={j} style={{ padding: '9px 16px', borderTop: '1px solid #f3f4f6', display: 'flex', alignItems: 'center', gap: 12, fontSize: 13 }}>
                      <div style={{
                        width: 18, height: 18, borderRadius: '50%',
                        background: cat.required ? EM : '#d1d5db',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                      }}>
                        <span style={{ color: '#fff', fontSize: 10, fontWeight: 700 }}>✓</span>
                      </div>
                      <span style={{ color: '#374151' }}>{item}</span>
                    </div>
                  ))}
                </div>
              ))}
            </Section>
            <Section title="NACE Sectors Excluded Under PAB">
              <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 10 }}>Sectors where revenue exposure triggers PAB exclusion thresholds:</div>
              <Row>
                {['B05 Coal mining', 'B06 Crude oil extraction', 'B09 Oil/gas support', 'C19 Petroleum refining', 'D35 High-carbon power gen', 'C30 Transport equipment (weapons)', 'C11 Tobacco manufacturing'].map((s, i) => (
                  <div key={i} style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6, padding: '6px 12px', fontSize: 12, color: '#374151' }}>{s}</div>
                ))}
              </Row>
            </Section>
          </>
        )}

        {/* Tab 3 — Fund Universe Radar */}
        {tab === 3 && (
          <Section title="Fund Universe — ESG Naming Compliance Profile (5 Sample Funds)">
            <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 16 }}>
              Radar chart scores 5 funds across ESG, Sustainability, Transition, Impact, and Exclusion dimensions (0–100).
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={RADAR_FUNDS} outerRadius={150}>
                <PolarGrid stroke="#e5e7eb" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 13, fill: '#374151' }} />
                {['A', 'B', 'C', 'D', 'E'].map((key, i) => (
                  <Radar key={key} name={RADAR_NAMES[i]} dataKey={key}
                    stroke={RADAR_COLORS[i]} fill={RADAR_COLORS[i]} fillOpacity={0.12} strokeWidth={2} />
                ))}
                <Legend />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
            <div style={{ marginTop: 16 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Fund', 'ESG', 'Sustainability', 'Transition', 'Impact', 'Exclusions', 'Avg'].map(h => (
                      <th key={h} style={{ padding: '8px 10px', textAlign: 'left', borderBottom: '1px solid #e5e7eb', fontSize: 12, fontWeight: 700 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {RADAR_NAMES.map((name, i) => {
                    const k = ['A', 'B', 'C', 'D', 'E'][i];
                    const vals = RADAR_FUNDS.map(r => r[k]);
                    const avg = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
                    return (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                        <td style={{ padding: '7px 10px', fontWeight: 500, color: RADAR_COLORS[i] }}>{name}</td>
                        {vals.map((v, j) => <td key={j} style={{ padding: '7px 10px', color: v >= 80 ? EM : '#374151', fontWeight: v >= 80 ? 600 : 400 }}>{v}</td>)}
                        <td style={{ padding: '7px 10px', fontWeight: 700, color: avg >= 80 ? EM : '#374151' }}>{avg}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Section>
        )}

        {/* Tab 4 — Reference */}
        {tab === 4 && (
          <>
            <Section title="ESMA/2024/249 — Guidelines Timeline">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Date', 'Milestone', 'Scope'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { date: 'Nov 2022', milestone: 'ESMA Consultation Paper published', scope: 'Initial guidelines on ESG/sustainability fund names' },
                    { date: 'Dec 2023', milestone: 'ESMA Final Report', scope: 'Final Guidelines incorporating responses from 150+ stakeholders' },
                    { date: 'May 2024', milestone: 'ESMA/2024/249 published', scope: 'Official guidelines publication with legal references' },
                    { date: '21 Nov 2024', milestone: 'Effective for new funds', scope: 'UCITS, AIF, ELTIF launched after this date must comply' },
                    { date: '21 May 2025', milestone: 'Effective for existing funds', scope: '6-month transition period for funds already using ESG/sustainability terms' },
                  ].map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={{ padding: '9px 12px', fontWeight: 700, color: EM, whiteSpace: 'nowrap' }}>{r.date}</td>
                      <td style={{ padding: '9px 12px', fontWeight: 500 }}>{r.milestone}</td>
                      <td style={{ padding: '9px 12px', color: '#6b7280' }}>{r.scope}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="Fund Name Term Categories">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Category', 'Example Terms', 'Threshold Requirement'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {TERM_CATEGORIES.map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={{ padding: '9px 12px', fontWeight: 700, color: '#111' }}>{r.category}</td>
                      <td style={{ padding: '9px 12px', color: '#374151' }}>{r.terms}</td>
                      <td style={{ padding: '9px 12px', color: EM, fontWeight: 600 }}>{r.threshold}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="API Endpoints">
              {[
                { method: 'POST', path: '/api/v1/esma-fund-names/assess', desc: 'Assess single fund name compliance' },
                { method: 'POST', path: '/api/v1/esma-fund-names/batch', desc: 'Batch screen multiple funds' },
                { method: 'GET', path: '/api/v1/esma-fund-names/ref/exclusions', desc: 'PAB/CTB exclusion reference data' },
                { method: 'GET', path: '/api/v1/esma-fund-names/ref/term-categories', desc: 'Fund name term category definitions' },
                { method: 'GET', path: '/api/v1/esma-fund-names/ref/nace-sectors', desc: 'NACE sector PAB exclusion mappings' },
              ].map((e, i) => (
                <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 10, fontSize: 13, flexWrap: 'wrap' }}>
                  <span style={{
                    background: e.method === 'GET' ? '#dbeafe' : '#d1fae5',
                    color: e.method === 'GET' ? '#1d4ed8' : '#065f46',
                    borderRadius: 4, padding: '2px 8px', fontWeight: 700, minWidth: 50, textAlign: 'center', fontSize: 11,
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
