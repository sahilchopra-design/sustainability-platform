/**
 * EUTaxonomyGARPage.jsx — Route: /eu-taxonomy-gar
 * EU Taxonomy Green Asset Ratio (GAR) & BTAR Reporter
 * Regulation (EU) 2020/852 — Delegated Act 2021/4987 (Article 8)
 * Sprint 14 — E19
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell
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
const TABS = ['GAR Calculator', 'Asset Class Breakdown', 'Objective Heatmap', 'Peer Benchmark', 'Reference'];

const ENV_OBJECTIVES = [
  { code: 'CCM', label: 'Climate Change Mitigation', color: '#10b981', delegated_act: 'Reg (EU) 2021/2139' },
  { code: 'CCA', label: 'Climate Change Adaptation', color: '#3b82f6', delegated_act: 'Reg (EU) 2021/2139' },
  { code: 'WTR', label: 'Water & Marine Resources', color: '#06b6d4', delegated_act: 'Reg (EU) 2023/2486' },
  { code: 'CE', label: 'Circular Economy', color: '#8b5cf6', delegated_act: 'Reg (EU) 2023/2486' },
  { code: 'PPC', label: 'Pollution Prevention & Control', color: '#f59e0b', delegated_act: 'Reg (EU) 2023/2486' },
  { code: 'BIO', label: 'Biodiversity & Ecosystems', color: '#ef4444', delegated_act: 'Reg (EU) 2023/2486' },
];

const ASSET_CLASSES = [
  { class: 'Corporate Loans', eligible_pct: 45, aligned_pct: 18, off_bs: false },
  { class: 'Retail Mortgages', eligible_pct: 62, aligned_pct: 28, off_bs: false },
  { class: 'SME Loans', eligible_pct: 38, aligned_pct: 12, off_bs: false },
  { class: 'Equity Investments', eligible_pct: 55, aligned_pct: 22, off_bs: false },
  { class: 'Debt Securities', eligible_pct: 48, aligned_pct: 19, off_bs: false },
  { class: 'Off-Balance Sheet', eligible_pct: 30, aligned_pct: 8, off_bs: true },
];

const PEER_BANKS = [
  { name: 'BNP Paribas', country: 'FR', gar_pct: 18.4, btar_pct: 12.1 },
  { name: 'Deutsche Bank', country: 'DE', gar_pct: 14.7, btar_pct: 9.3 },
  { name: 'Santander', country: 'ES', gar_pct: 16.2, btar_pct: 10.8 },
  { name: 'ING Group', country: 'NL', gar_pct: 21.3, btar_pct: 14.6 },
  { name: 'UniCredit', country: 'IT', gar_pct: 12.9, btar_pct: 8.7 },
];

/* ── Heatmap helper ── */
function heatCell(eligible, aligned, dnsh) {
  if (dnsh === 'pass' && aligned >= 15) return { bg: '#f0fdf4', color: EM, text: 'Aligned' };
  if (eligible >= 30) return { bg: '#fffbeb', color: '#d97706', text: 'Eligible' };
  return { bg: '#fef2f2', color: '#ef4444', text: 'Not Eligible' };
}

/* ── Page ── */
export default function EUTaxonomyGARPage() {
  const [tab, setTab] = useState(0);
  const [form, setForm] = useState({
    entity_name: 'European Commercial Bank AG',
    total_assets_mEUR: 250000,
    eligible_assets_mEUR: 62500,
    aligned_assets_mEUR: 31250,
    reporting_period: '2024',
    ccm_eligible: 65, ccm_aligned: 28,
    cca_eligible: 40, cca_aligned: 15,
    wtr_eligible: 25, wtr_aligned: 8,
    ce_eligible: 20, ce_aligned: 6,
    ppc_eligible: 18, ppc_aligned: 5,
    bio_eligible: 12, bio_aligned: 3,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [highlightPeer, setHighlightPeer] = useState(null);

  const handleCalculate = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.post(`${API}/api/v1/eu-taxonomy-gar/calculate`, form);
      setResult(res.data);
    } catch {
      const gar_pct = ((form.aligned_assets_mEUR / form.total_assets_mEUR) * 100).toFixed(2);
      const eligibility_ratio = ((form.eligible_assets_mEUR / form.total_assets_mEUR) * 100).toFixed(2);
      // BTAR uses banking book only (approx 85% of total)
      const btar_pct = ((form.aligned_assets_mEUR / (form.total_assets_mEUR * 0.85)) * 100).toFixed(2);
      const compliant = parseFloat(gar_pct) >= 10;
      setResult({
        entity_name: form.entity_name,
        gar_pct: parseFloat(gar_pct),
        btar_pct: parseFloat(btar_pct),
        eligibility_ratio: parseFloat(eligibility_ratio),
        aligned_assets_mEUR: form.aligned_assets_mEUR,
        total_assets_mEUR: form.total_assets_mEUR,
        compliant,
        disclosure_level: compliant ? 'Full Article 8 Disclosure' : 'Partial — improvement required',
        objective_breakdown: ENV_OBJECTIVES.map(obj => ({
          code: obj.code,
          eligible_pct: form[`${obj.code.toLowerCase()}_eligible`],
          aligned_pct: form[`${obj.code.toLowerCase()}_aligned`],
        })),
      });
    }
    setLoading(false);
  };

  /* Seed KPI values */
  const seedGAR = 15.8;
  const seedBTAR = 10.4;
  const sectorMedianGAR = (PEER_BANKS.reduce((s, b) => s + b.gar_pct, 0) / PEER_BANKS.length).toFixed(1);

  const assetBarData = ASSET_CLASSES.map(ac => ({
    class: ac.class.replace(' ', '\n'),
    'Eligible %': ac.eligible_pct,
    'Aligned %': ac.aligned_pct,
    'Not Eligible %': 100 - ac.eligible_pct,
  }));

  const peerBarData = [...PEER_BANKS, { name: 'Entity (You)', country: '—', gar_pct: result ? result.gar_pct : seedGAR, btar_pct: result ? result.btar_pct : seedBTAR, isSelf: true }]
    .sort((a, b) => b.gar_pct - a.gar_pct);

  /* Heatmap data */
  const heatRows = ENV_OBJECTIVES.map(obj => ({
    obj: obj.code,
    label: obj.label,
    cells: ASSET_CLASSES.slice(0, 3).map((ac, j) => {
      const elig = Math.round(form[`${obj.code.toLowerCase()}_eligible`] * (0.7 + seed(j * 5 + obj.code.charCodeAt(0)) * 0.6));
      const algn = Math.round(form[`${obj.code.toLowerCase()}_aligned`] * (0.6 + seed(j * 7 + obj.code.charCodeAt(0)) * 0.8));
      const dnsh = algn >= 10 ? 'pass' : 'conditional';
      return { ac: ac.class.split(' ')[0], elig, algn, dnsh, cell: heatCell(elig, algn, dnsh) };
    }),
  }));

  return (
    <div style={{ fontFamily: 'Inter, sans-serif', background: '#f9fafb', minHeight: '100vh', padding: 24 }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#111' }}>EU Taxonomy GAR / BTAR Reporter</div>
          <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>
            Regulation (EU) 2020/852 — Article 8 Delegated Act 2021/4987 — Green Asset Ratio & BTAR Calculation
          </div>
        </div>

        {/* KPI Cards */}
        <Row>
          <KpiCard label="GAR %" value={result ? `${result.gar_pct}%` : `${seedGAR}%`} sub="Aligned / Total covered assets" />
          <KpiCard label="BTAR %" value={result ? `${result.btar_pct}%` : `${seedBTAR}%`} sub="Banking book ratio" />
          <KpiCard label="Eligible Asset Ratio" value={result ? `${result.eligibility_ratio}%` : '25.0%'} sub="Eligible / Total covered" />
          <KpiCard label="Taxonomy Aligned €M" value={result ? `€${result.aligned_assets_mEUR.toLocaleString()}M` : `€${form.aligned_assets_mEUR.toLocaleString()}M`} sub="Aligned assets" />
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

        {/* Tab 0 — GAR Calculator */}
        {tab === 0 && (
          <>
            <Section title="GAR / BTAR Calculator — Article 8 Inputs">
              <Row>
                <Inp label="Entity Name" value={form.entity_name} onChange={e => setForm({ ...form, entity_name: e.target.value })} />
                <Inp label="Reporting Period" value={form.reporting_period} onChange={e => setForm({ ...form, reporting_period: e.target.value })} />
              </Row>
              <Row>
                <Inp label="Total Covered Assets (€M)" type="number" value={form.total_assets_mEUR} onChange={e => setForm({ ...form, total_assets_mEUR: +e.target.value })} />
                <Inp label="Taxonomy-Eligible Assets (€M)" type="number" value={form.eligible_assets_mEUR} onChange={e => setForm({ ...form, eligible_assets_mEUR: +e.target.value })} />
                <Inp label="Taxonomy-Aligned Assets (€M)" type="number" value={form.aligned_assets_mEUR} onChange={e => setForm({ ...form, aligned_assets_mEUR: +e.target.value })} />
              </Row>
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 12, color: '#374151', fontWeight: 700, marginBottom: 10 }}>Environmental Objective Breakdown (% of eligible assets):</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
                  {ENV_OBJECTIVES.map(obj => (
                    <div key={obj.code} style={{ border: '1px solid #e5e7eb', borderRadius: 6, padding: 10 }}>
                      <div style={{ fontSize: 12, fontWeight: 700, color: obj.color, marginBottom: 6 }}>{obj.code} — {obj.label}</div>
                      <div style={{ display: 'flex', gap: 8 }}>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: 10, color: '#9ca3af' }}>Eligible %</div>
                          <input type="range" min={0} max={100} value={form[`${obj.code.toLowerCase()}_eligible`]}
                            onChange={e => setForm({ ...form, [`${obj.code.toLowerCase()}_eligible`]: +e.target.value })}
                            style={{ width: '100%', accentColor: obj.color }} />
                          <div style={{ fontSize: 11, fontWeight: 600, color: obj.color, textAlign: 'center' }}>{form[`${obj.code.toLowerCase()}_eligible`]}%</div>
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: 10, color: '#9ca3af' }}>Aligned %</div>
                          <input type="range" min={0} max={100} value={form[`${obj.code.toLowerCase()}_aligned`]}
                            onChange={e => setForm({ ...form, [`${obj.code.toLowerCase()}_aligned`]: +e.target.value })}
                            style={{ width: '100%', accentColor: obj.color }} />
                          <div style={{ fontSize: 11, fontWeight: 600, color: obj.color, textAlign: 'center' }}>{form[`${obj.code.toLowerCase()}_aligned`]}%</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <Btn onClick={handleCalculate} disabled={loading}>{loading ? 'Calculating...' : 'Calculate GAR / BTAR'}</Btn>
            </Section>

            {error && <div style={{ color: 'red', marginBottom: 12, fontSize: 13 }}>{error}</div>}

            {result && (
              <Section title="Calculation Result">
                <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 16 }}>
                  {[
                    { label: 'GAR %', value: `${result.gar_pct}%`, formula: 'Aligned / Total Covered', threshold: '≥10% target (ECB guidance)', ok: result.gar_pct >= 10 },
                    { label: 'BTAR %', value: `${result.btar_pct}%`, formula: 'Aligned / Banking Book', threshold: 'Banking book only (Art. 8(2a))', ok: result.btar_pct >= 8 },
                    { label: 'Eligibility Ratio', value: `${result.eligibility_ratio}%`, formula: 'Eligible / Total Covered', threshold: 'Disclosure required', ok: true },
                  ].map((m, i) => (
                    <div key={i} style={{ flex: 1, minWidth: 160, background: m.ok ? '#f0fdf4' : '#fef2f2', border: `1px solid ${m.ok ? '#bbf7d0' : '#fecaca'}`, borderRadius: 8, padding: 14, textAlign: 'center' }}>
                      <div style={{ fontSize: 28, fontWeight: 800, color: m.ok ? EM : '#ef4444' }}>{m.value}</div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: '#111', marginTop: 4 }}>{m.label}</div>
                      <div style={{ fontSize: 11, color: '#6b7280', marginTop: 3 }}>{m.formula}</div>
                      <div style={{ fontSize: 10, color: m.ok ? EM : '#6b7280', marginTop: 2 }}>{m.threshold}</div>
                    </div>
                  ))}
                </div>
                <div style={{ background: result.compliant ? '#f0fdf4' : '#fffbeb', border: `1px solid ${result.compliant ? '#bbf7d0' : '#fde68a'}`, borderRadius: 6, padding: 12, fontSize: 13 }}>
                  <strong>Disclosure Level:</strong> {result.disclosure_level}
                  {!result.compliant && (
                    <div style={{ marginTop: 4, color: '#92400e' }}>
                      Consider increasing aligned lending through green mortgage products, green corporate loans, and EU Green Bond investments.
                    </div>
                  )}
                </div>
                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: '#374151', marginBottom: 8 }}>Objective Breakdown:</div>
                  <Row>
                    {result.objective_breakdown.map((ob, i) => (
                      <div key={i} style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 6, padding: '8px 12px', textAlign: 'center', flex: 1, minWidth: 80 }}>
                        <div style={{ fontSize: 14, fontWeight: 800, color: ENV_OBJECTIVES[i].color }}>{ob.aligned_pct}%</div>
                        <div style={{ fontSize: 10, color: '#6b7280', marginTop: 2 }}>{ob.code} aligned</div>
                        <div style={{ fontSize: 10, color: '#9ca3af' }}>{ob.eligible_pct}% eligible</div>
                      </div>
                    ))}
                  </Row>
                </div>
              </Section>
            )}
          </>
        )}

        {/* Tab 1 — Asset Class Breakdown */}
        {tab === 1 && (
          <>
            <Section title="Eligible vs Aligned by Asset Class (%)">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={ASSET_CLASSES.map(ac => ({
                  class: ac.class,
                  'Eligible %': ac.eligible_pct,
                  'Aligned %': ac.aligned_pct,
                }))} margin={{ top: 5, right: 20, left: 0, bottom: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="class" tick={{ fontSize: 11 }} angle={-15} textAnchor="end" interval={0} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={v => `${v}%`} />
                  <Legend />
                  <Bar dataKey="Eligible %" fill="#93c5fd" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="Aligned %" fill={EM} radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Asset Class Detail">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Asset Class', 'Off-BS', 'Eligible %', 'Aligned %', 'Gap (Elig–Algn)', 'Status'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ASSET_CLASSES.map((ac, i) => {
                    const gap = ac.eligible_pct - ac.aligned_pct;
                    const status = ac.aligned_pct >= 20 ? 'Strong' : ac.aligned_pct >= 12 ? 'Moderate' : 'Low';
                    const statusColor = status === 'Strong' ? EM : status === 'Moderate' ? '#f59e0b' : '#ef4444';
                    return (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                        <td style={{ padding: '9px 12px', fontWeight: 500 }}>{ac.class}</td>
                        <td style={{ padding: '9px 12px', color: '#9ca3af', fontSize: 12 }}>{ac.off_bs ? 'Yes' : 'No'}</td>
                        <td style={{ padding: '9px 12px', color: '#3b82f6', fontWeight: 600 }}>{ac.eligible_pct}%</td>
                        <td style={{ padding: '9px 12px', color: EM, fontWeight: 600 }}>{ac.aligned_pct}%</td>
                        <td style={{ padding: '9px 12px', color: '#374151' }}>{gap}pp</td>
                        <td style={{ padding: '9px 12px' }}>
                          <span style={{ background: `${statusColor}22`, color: statusColor, borderRadius: 4, padding: '2px 8px', fontWeight: 700, fontSize: 11 }}>{status}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 2 — Objective Heatmap */}
        {tab === 2 && (
          <Section title="6×3 Environmental Objective Heatmap — Eligible / Aligned / DNSH Status">
            <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 12 }}>
              Showing eligibility and alignment status per Environmental Objective × Asset Class. DNSH = Do No Significant Harm.
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    <th style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, minWidth: 200 }}>Environmental Objective</th>
                    {ASSET_CLASSES.slice(0, 3).map(ac => (
                      <th key={ac.class} style={{ padding: '10px 12px', textAlign: 'center', borderBottom: '2px solid #e5e7eb', fontWeight: 700 }}>{ac.class}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {heatRows.map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ padding: '10px 12px', fontWeight: 700, color: ENV_OBJECTIVES[i].color }}>
                        <span style={{ fontFamily: 'monospace', fontSize: 11, marginRight: 6, background: `${ENV_OBJECTIVES[i].color}22`, padding: '2px 6px', borderRadius: 3 }}>{row.obj}</span>
                        {row.label}
                      </td>
                      {row.cells.map((cell, j) => (
                        <td key={j} style={{ padding: '8px 12px', textAlign: 'center' }}>
                          <div style={{ background: cell.cell.bg, border: `1px solid ${cell.cell.color}44`, borderRadius: 6, padding: '8px 6px' }}>
                            <div style={{ fontWeight: 700, color: cell.cell.color, fontSize: 13 }}>{cell.cell.text}</div>
                            <div style={{ fontSize: 10, color: '#6b7280', marginTop: 2 }}>
                              Elig: {cell.elig}% / Algn: {cell.algn}%
                            </div>
                            <div style={{ fontSize: 10, color: cell.dnsh === 'pass' ? EM : '#f59e0b', marginTop: 1 }}>
                              DNSH: {cell.dnsh === 'pass' ? 'Pass' : 'Conditional'}
                            </div>
                          </div>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Row style={{ marginTop: 12 }}>
              {[
                { color: EM, bg: '#f0fdf4', label: 'Aligned — DNSH pass, ≥15% aligned' },
                { color: '#d97706', bg: '#fffbeb', label: 'Eligible — ≥30% eligible, not yet fully aligned' },
                { color: '#ef4444', bg: '#fef2f2', label: 'Not Eligible — below eligibility thresholds' },
              ].map((l, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                  <div style={{ width: 14, height: 14, background: l.bg, border: `2px solid ${l.color}`, borderRadius: 3 }} />
                  <span style={{ color: '#374151' }}>{l.label}</span>
                </div>
              ))}
            </Row>
          </Section>
        )}

        {/* Tab 3 — Peer Benchmark */}
        {tab === 3 && (
          <>
            <Section title="EU Bank GAR % — Peer Benchmark">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={peerBarData} layout="vertical" margin={{ left: 100, right: 40, top: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                  <XAxis type="number" domain={[0, 30]} tickFormatter={v => `${v}%`} tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={100} />
                  <Tooltip formatter={v => `${v}%`} />
                  <Bar dataKey="gar_pct" name="GAR %" radius={[0, 4, 4, 0]}>
                    {peerBarData.map((entry, i) => (
                      <Cell key={i} fill={entry.isSelf ? '#111' : entry.gar_pct >= parseFloat(sectorMedianGAR) ? EM : '#93c5fd'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', gap: 20, marginTop: 10, flexWrap: 'wrap' }}>
                <div style={{ fontSize: 12, color: '#374151' }}>
                  Sector median GAR: <strong style={{ color: EM }}>{sectorMedianGAR}%</strong>
                </div>
                <div style={{ fontSize: 12, color: '#374151' }}>
                  Best-in-class: <strong style={{ color: EM }}>{Math.max(...PEER_BANKS.map(b => b.gar_pct))}% (ING Group)</strong>
                </div>
                <div style={{ fontSize: 12, color: '#374151' }}>
                  ECB supervisory expectation: <strong>≥10% by 2025</strong>
                </div>
              </div>
            </Section>
            <Section title="Peer Comparison Table">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Bank', 'Country', 'GAR %', 'BTAR %', 'vs Median', 'Rating'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {PEER_BANKS.map((b, i) => {
                    const vsMedian = (b.gar_pct - parseFloat(sectorMedianGAR)).toFixed(1);
                    const rating = b.gar_pct >= 18 ? 'Leader' : b.gar_pct >= 14 ? 'Average' : 'Laggard';
                    const ratingColor = rating === 'Leader' ? EM : rating === 'Average' ? '#f59e0b' : '#ef4444';
                    return (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                        <td style={{ padding: '9px 12px', fontWeight: 600 }}>{b.name}</td>
                        <td style={{ padding: '9px 12px', color: '#6b7280' }}>{b.country}</td>
                        <td style={{ padding: '9px 12px', fontWeight: 700, color: EM }}>{b.gar_pct}%</td>
                        <td style={{ padding: '9px 12px', color: '#374151' }}>{b.btar_pct}%</td>
                        <td style={{ padding: '9px 12px', color: parseFloat(vsMedian) >= 0 ? EM : '#ef4444', fontWeight: 600 }}>
                          {parseFloat(vsMedian) >= 0 ? '+' : ''}{vsMedian}pp
                        </td>
                        <td style={{ padding: '9px 12px' }}>
                          <span style={{ background: `${ratingColor}22`, color: ratingColor, borderRadius: 4, padding: '2px 8px', fontWeight: 700, fontSize: 11 }}>{rating}</span>
                        </td>
                      </tr>
                    );
                  })}
                  {/* Current entity row */}
                  <tr style={{ borderBottom: '1px solid #f3f4f6', background: '#f0fdf4', fontWeight: 700 }}>
                    <td style={{ padding: '9px 12px', color: EM }}>Entity (You)</td>
                    <td style={{ padding: '9px 12px', color: '#9ca3af' }}>—</td>
                    <td style={{ padding: '9px 12px', color: EM }}>{result ? result.gar_pct : seedGAR}%</td>
                    <td style={{ padding: '9px 12px' }}>{result ? result.btar_pct : seedBTAR}%</td>
                    <td style={{ padding: '9px 12px', color: EM }}>+{((result ? result.gar_pct : seedGAR) - parseFloat(sectorMedianGAR)).toFixed(1)}pp</td>
                    <td style={{ padding: '9px 12px' }}>
                      <span style={{ background: '#f0fdf4', color: EM, borderRadius: 4, padding: '2px 8px', fontWeight: 700, fontSize: 11 }}>Current</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 4 — Reference */}
        {tab === 4 && (
          <>
            <Section title="6 Environmental Objectives — EU Taxonomy Regulation">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Code', 'Objective', 'Delegated Act', 'Status'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ENV_OBJECTIVES.map((obj, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={{ padding: '9px 12px', fontFamily: 'monospace', fontWeight: 700, color: obj.color }}>{obj.code}</td>
                      <td style={{ padding: '9px 12px', fontWeight: 600 }}>{obj.label}</td>
                      <td style={{ padding: '9px 12px', fontFamily: 'monospace', fontSize: 12, color: '#6b7280' }}>{obj.delegated_act}</td>
                      <td style={{ padding: '9px 12px' }}>
                        <span style={{ background: i < 2 ? '#f0fdf4' : '#fffbeb', color: i < 2 ? EM : '#d97706', borderRadius: 4, padding: '2px 8px', fontWeight: 700, fontSize: 11 }}>
                          {i < 2 ? 'In force since 2022' : 'In force since 2024'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="GAR Formula & Definition">
              <div style={{ background: '#f9fafb', borderRadius: 8, padding: 16, fontFamily: 'monospace', fontSize: 14, color: '#111', marginBottom: 12 }}>
                <div style={{ marginBottom: 6 }}>GAR = Taxonomy-Aligned Assets / Total Covered Assets × 100</div>
                <div style={{ color: '#6b7280', fontSize: 12, fontFamily: 'Inter, sans-serif' }}>
                  Total Covered Assets = Loans & advances (excl. central banks & public sector) + Debt securities + Equity instruments
                </div>
              </div>
              <div style={{ background: '#f9fafb', borderRadius: 8, padding: 16, fontFamily: 'monospace', fontSize: 14, color: '#111' }}>
                <div style={{ marginBottom: 6 }}>BTAR = Taxonomy-Aligned Banking Book Assets / Total Banking Book Assets × 100</div>
                <div style={{ color: '#6b7280', fontSize: 12, fontFamily: 'Inter, sans-serif' }}>
                  BTAR reported separately under CRR Art. 449a; focuses on banking book trading/non-trading book split
                </div>
              </div>
            </Section>
            <Section title="Article 8 Disclosure Timeline">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Year', 'Disclosure Requirements', 'Objectives Covered'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { year: '2022 (FY2021)', req: 'Eligibility KPIs only (% eligible)', obj: 'CCM + CCA' },
                    { year: '2023 (FY2022)', req: 'Full GAR: eligible + aligned + DNSH', obj: 'CCM + CCA' },
                    { year: '2024 (FY2023)', req: 'GAR + BTAR + OpEx + CapEx KPIs', obj: 'All 6 objectives (phased)' },
                    { year: '2025+ (FY2024)', req: 'Full disclosure all 6 objectives + BTAR', obj: 'CCM + CCA + WTR + CE + PPC + BIO' },
                  ].map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={{ padding: '9px 12px', fontWeight: 700, color: EM }}>{r.year}</td>
                      <td style={{ padding: '9px 12px' }}>{r.req}</td>
                      <td style={{ padding: '9px 12px', color: '#6b7280', fontSize: 12 }}>{r.obj}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="API Endpoints">
              {[
                { method: 'POST', path: '/api/v1/eu-taxonomy-gar/calculate', desc: 'Calculate GAR / BTAR from asset inputs' },
                { method: 'POST', path: '/api/v1/eu-taxonomy-gar/asset-breakdown', desc: 'Asset class eligibility & alignment breakdown' },
                { method: 'GET', path: '/api/v1/eu-taxonomy-gar/ref/objectives', desc: '6 environmental objectives reference data' },
                { method: 'GET', path: '/api/v1/eu-taxonomy-gar/ref/formula', desc: 'GAR/BTAR formula definitions and methodology' },
                { method: 'GET', path: '/api/v1/eu-taxonomy-gar/ref/peer-benchmarks', desc: 'EU bank peer GAR benchmark data' },
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
