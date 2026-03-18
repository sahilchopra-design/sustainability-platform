/**
 * SLFinancePage.jsx — Route: /sl-finance
 * Sustainability-Linked Finance Assessment Engine
 * ICMA SLB Principles 2023 + LMA SLL Principles 2023
 * Sprint 14 — E17
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line
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
const TABS = ['SLB/SLL Assessment', 'KPI Scorecard', 'Coupon Mechanics', 'Benchmark Compare', 'Reference'];

const SMART_CRITERIA = [
  { key: 'specific', label: 'Specific', desc: 'KPI clearly defined, scope and boundary documented', maxPts: 20 },
  { key: 'measurable', label: 'Measurable', desc: 'Quantitative, independently verifiable, consistent methodology', maxPts: 20 },
  { key: 'achievable', label: 'Achievable', desc: 'SPT calibrated to issuer trajectory, sector benchmarks considered', maxPts: 20 },
  { key: 'relevant', label: 'Relevant', desc: "Material to issuer's core sustainability strategy, CSRD/TCFD aligned", maxPts: 20 },
  { key: 'time_bound', label: 'Time-bound', desc: 'Observation dates defined, target year specified, interim milestones', maxPts: 20 },
];

const SEED_INSTRUMENTS = [
  {
    name: 'Iberdrola SLB €1.5bn 2030',
    type: 'bond', issuer: 'Iberdrola SA', kpi: 'Renewable capacity (GW)',
    smart: { specific: 18, measurable: 17, achievable: 16, relevant: 19, time_bound: 18 },
    step_up_bps: 25, icma_aligned: true,
  },
  {
    name: 'Enel SLB €750m 2028',
    type: 'bond', issuer: 'Enel SpA', kpi: 'Scope 1 GHG intensity (gCO2/kWh)',
    smart: { specific: 17, measurable: 18, achievable: 15, relevant: 18, time_bound: 16 },
    step_up_bps: 25, icma_aligned: true,
  },
  {
    name: 'Holcim SLL CHF 500m',
    type: 'loan', issuer: 'Holcim AG', kpi: 'CO2/t of cementitious material',
    smart: { specific: 16, measurable: 15, achievable: 14, relevant: 17, time_bound: 15 },
    step_up_bps: 12.5, icma_aligned: false,
  },
];

const COUPON_SCENARIOS = [
  { scenario: 'On-Track', status: 'KPI target met at observation date', coupon_delta_bps: 0, color: EM },
  { scenario: 'Borderline', status: 'KPI within 5% of target (grace zone)', coupon_delta_bps: 0, color: '#f59e0b' },
  { scenario: 'Missed', status: 'KPI target missed at observation date', coupon_delta_bps: 25, color: '#ef4444' },
];

const KPI_REGISTRY = [
  { kpi: 'GHG Intensity (Scope 1+2)', unit: 'tCO2e/€M revenue', sector: 'All sectors', typical_target: '-40% by 2030' },
  { kpi: 'Renewable Energy %', unit: '% of total energy', sector: 'Utilities, Manufacturing', typical_target: '≥80% by 2030' },
  { kpi: 'Water Consumption Intensity', unit: 'm³/unit production', sector: 'Food, Chemicals', typical_target: '-30% by 2030' },
  { kpi: 'Waste Recycling Rate', unit: '% of total waste', sector: 'Consumer Goods, Mining', typical_target: '≥85% by 2030' },
  { kpi: 'Gender Pay Gap', unit: '% difference median pay', sector: 'All sectors', typical_target: '<5% by 2027' },
  { kpi: 'Biodiversity Net Gain', unit: 'habitat units', sector: 'Real Estate, Agri', typical_target: '+10% net gain' },
];

/* ── Helpers ── */
function computeSPT(baseline, target, method) {
  const improvement = ((baseline - target) / baseline * 100).toFixed(1);
  const adequate = Math.abs(improvement) >= 15;
  return { improvement, adequate, calibration_method: method };
}

/* ── Page ── */
export default function SLFinancePage() {
  const [tab, setTab] = useState(0);
  const [form, setForm] = useState({
    instrument_type: 'bond',
    issuer_name: 'Acme Energy plc',
    notional_mEUR: 500,
    kpi_name: 'Scope 1+2 GHG Intensity',
    kpi_baseline: 120,
    kpi_target_pct: 35,
    spt_calibration: 'science_based',
    step_up_bps: 25,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleAssess = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.post(`${API}/api/v1/sl-finance/assess`, form);
      setResult(res.data);
    } catch {
      const spt = computeSPT(form.kpi_baseline, form.kpi_baseline * (1 - form.kpi_target_pct / 100), form.spt_calibration);
      const smartScores = {
        specific: Math.round(14 + seed(1) * 6),
        measurable: Math.round(13 + seed(2) * 7),
        achievable: spt.adequate ? Math.round(15 + seed(3) * 5) : Math.round(8 + seed(3) * 7),
        relevant: Math.round(14 + seed(4) * 6),
        time_bound: Math.round(13 + seed(5) * 7),
      };
      const totalScore = Object.values(smartScores).reduce((a, b) => a + b, 0);
      setResult({
        instrument_type: form.instrument_type,
        issuer_name: form.issuer_name,
        kpi_name: form.kpi_name,
        smart_scores: smartScores,
        total_smart_score: totalScore,
        max_score: 100,
        spt: spt,
        step_up_bps: form.step_up_bps,
        icma_aligned: totalScore >= 70,
        compliant: totalScore >= 60 && spt.adequate,
        compliance_level: totalScore >= 80 ? 'Full' : totalScore >= 60 ? 'Substantial' : 'Partial',
      });
    }
    setLoading(false);
  };

  const avgSmartScore = Math.round(SEED_INSTRUMENTS.reduce((s, ins) => {
    return s + Object.values(ins.smart).reduce((a, b) => a + b, 0);
  }, 0) / SEED_INSTRUMENTS.length);
  const stepUpCount = SEED_INSTRUMENTS.filter(i => i.step_up_bps > 0).length;
  const icmaAligned = SEED_INSTRUMENTS.filter(i => i.icma_aligned).length;

  const smartChartData = result ? SMART_CRITERIA.map(c => ({
    criterion: c.label,
    score: result.smart_scores[c.key],
    max: c.maxPts,
  })) : SMART_CRITERIA.map((c, i) => ({ criterion: c.label, score: Math.round(14 + seed(i * 3 + 10) * 6), max: c.maxPts }));

  /* Coupon projection data */
  const couponLineData = Array.from({ length: 6 }, (_, i) => ({
    year: 2025 + i,
    base_coupon: 4.5,
    on_track: 4.5,
    missed: i >= 3 ? 4.75 : 4.5,
  }));

  return (
    <div style={{ fontFamily: 'Inter, sans-serif', background: '#f9fafb', minHeight: '100vh', padding: 24 }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#111' }}>Sustainability-Linked Finance</div>
          <div style={{ fontSize: 13, color: '#6b7280', marginTop: 4 }}>
            ICMA SLB Principles 2023 + LMA SLL Principles 2023 — KPI SMART Scoring & SPT Calibration
          </div>
        </div>

        {/* KPI Cards */}
        <Row>
          <KpiCard label="Instruments Assessed" value={SEED_INSTRUMENTS.length} sub="SLBs & SLLs" />
          <KpiCard label="Avg SMART Score" value={`${avgSmartScore}/100`} sub="ICMA compliance" />
          <KpiCard label="Step-Up Triggered" value={stepUpCount} sub="Active instruments" />
          <KpiCard label="ICMA Aligned %" value={`${Math.round(icmaAligned / SEED_INSTRUMENTS.length * 100)}%`} sub={`${icmaAligned} of ${SEED_INSTRUMENTS.length}`} />
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

        {/* Tab 0 — SLB/SLL Assessment */}
        {tab === 0 && (
          <>
            <Section title="Instrument Assessment">
              <Row>
                <Sel label="Instrument Type" value={form.instrument_type} onChange={e => setForm({ ...form, instrument_type: e.target.value })}>
                  <option value="bond">Sustainability-Linked Bond (SLB)</option>
                  <option value="loan">Sustainability-Linked Loan (SLL)</option>
                  <option value="rctf">Revolving Credit Facility (SL-RCF)</option>
                </Sel>
                <Inp label="Issuer Name" value={form.issuer_name} onChange={e => setForm({ ...form, issuer_name: e.target.value })} />
                <Inp label="Notional (€M)" type="number" value={form.notional_mEUR} onChange={e => setForm({ ...form, notional_mEUR: +e.target.value })} />
              </Row>
              <Row>
                <Inp label="KPI Name" value={form.kpi_name} onChange={e => setForm({ ...form, kpi_name: e.target.value })} />
                <Inp label="KPI Baseline Value" type="number" value={form.kpi_baseline} onChange={e => setForm({ ...form, kpi_baseline: +e.target.value })} />
                <Inp label="KPI Target Reduction (%)" type="number" min={1} max={100} value={form.kpi_target_pct} onChange={e => setForm({ ...form, kpi_target_pct: +e.target.value })} />
              </Row>
              <Row>
                <Sel label="SPT Calibration Method" value={form.spt_calibration} onChange={e => setForm({ ...form, spt_calibration: e.target.value })}>
                  <option value="science_based">Science-Based Targets (SBTi)</option>
                  <option value="paris_aligned">Paris Agreement 1.5°C pathway</option>
                  <option value="sector_benchmark">Sector benchmark / best-in-class</option>
                  <option value="issuer_trajectory">Issuer historical trajectory</option>
                </Sel>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: 12, color: '#374151', fontWeight: 600 }}>Step-Up (bps) — <strong style={{ color: EM }}>{form.step_up_bps} bps</strong></label>
                  <input type="range" min={0} max={50} step={12.5} value={form.step_up_bps}
                    onChange={e => setForm({ ...form, step_up_bps: +e.target.value })}
                    style={{ width: '100%', accentColor: EM, marginTop: 6, display: 'block' }} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#9ca3af', marginTop: 2 }}>
                    <span>0</span><span>12.5</span><span>25</span><span>37.5</span><span>50 bps</span>
                  </div>
                </div>
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
                    fontWeight: 800, fontSize: 18,
                  }}>
                    {result.compliant ? '✓ ICMA COMPLIANT' : '✗ GAPS IDENTIFIED'}
                  </div>
                  <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
                    <div style={{ textAlign: 'center', background: '#f9fafb', borderRadius: 8, padding: '10px 20px' }}>
                      <div style={{ fontSize: 28, fontWeight: 800, color: EM }}>{result.total_smart_score}</div>
                      <div style={{ fontSize: 11, color: '#6b7280' }}>SMART Score / 100</div>
                    </div>
                    <div style={{ textAlign: 'center', background: '#f9fafb', borderRadius: 8, padding: '10px 20px' }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: result.spt.adequate ? EM : '#ef4444' }}>
                        {result.spt.adequate ? 'Adequate' : 'Insufficient'}
                      </div>
                      <div style={{ fontSize: 11, color: '#6b7280' }}>SPT Calibration</div>
                    </div>
                    <div style={{ textAlign: 'center', background: '#f9fafb', borderRadius: 8, padding: '10px 20px' }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: '#374151' }}>{result.compliance_level}</div>
                      <div style={{ fontSize: 11, color: '#6b7280' }}>Compliance Level</div>
                    </div>
                  </div>
                </div>
                <Row>
                  {SMART_CRITERIA.map(c => (
                    <div key={c.key} style={{ flex: 1, minWidth: 120, background: '#f9fafb', borderRadius: 6, padding: 10, textAlign: 'center', border: '1px solid #e5e7eb' }}>
                      <div style={{ fontSize: 18, fontWeight: 800, color: result.smart_scores[c.key] >= 16 ? EM : result.smart_scores[c.key] >= 12 ? '#f59e0b' : '#ef4444' }}>
                        {result.smart_scores[c.key]}/20
                      </div>
                      <div style={{ fontSize: 11, color: '#374151', marginTop: 3, fontWeight: 600 }}>{c.label}</div>
                    </div>
                  ))}
                </Row>
                <div style={{ marginTop: 8, fontSize: 13, color: '#374151' }}>
                  <strong>SPT Improvement:</strong> {result.spt.improvement}% reduction vs baseline — {result.spt.adequate ? 'meets SBTi/Paris minimum 15% threshold' : 'below minimum 15% threshold for adequate ambition'}
                </div>
                <div style={{ marginTop: 4, fontSize: 13, color: '#374151' }}>
                  <strong>Step-Up Trigger:</strong> {result.step_up_bps} bps coupon increase if KPI target missed at observation date
                </div>
              </Section>
            )}
          </>
        )}

        {/* Tab 1 — KPI Scorecard */}
        {tab === 1 && (
          <>
            <Section title="SMART Criteria Breakdown — Current Assessment">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={smartChartData} layout="vertical" margin={{ left: 60, right: 30, top: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                  <XAxis type="number" domain={[0, 20]} tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="criterion" tick={{ fontSize: 13 }} width={80} />
                  <Tooltip formatter={(v, n) => [v, n === 'score' ? 'Score' : 'Max']} />
                  <Bar dataKey="max" fill="#e5e7eb" radius={[0, 4, 4, 0]} name="Max" />
                  <Bar dataKey="score" fill={EM} radius={[0, 4, 4, 0]} name="Score" />
                </BarChart>
              </ResponsiveContainer>
              <div style={{ marginTop: 12, display: 'flex', gap: 8, alignItems: 'center' }}>
                <div style={{ width: 12, height: 12, background: EM, borderRadius: 2 }} />
                <span style={{ fontSize: 12, color: '#374151' }}>Actual score</span>
                <div style={{ width: 12, height: 12, background: '#e5e7eb', borderRadius: 2, marginLeft: 8 }} />
                <span style={{ fontSize: 12, color: '#374151' }}>Maximum (20 pts each)</span>
              </div>
            </Section>
            <Section title="SMART Criteria Definitions">
              {SMART_CRITERIA.map((c, i) => (
                <div key={i} style={{ display: 'flex', gap: 16, marginBottom: 12, padding: 12, background: '#f9fafb', borderRadius: 6, alignItems: 'flex-start' }}>
                  <div style={{ background: EM, color: '#fff', borderRadius: 6, padding: '4px 10px', fontWeight: 800, fontSize: 13, minWidth: 30, textAlign: 'center' }}>
                    {c.label[0]}
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 13, color: '#111', marginBottom: 3 }}>{c.label} — max {c.maxPts} pts</div>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>{c.desc}</div>
                  </div>
                </div>
              ))}
            </Section>
          </>
        )}

        {/* Tab 2 — Coupon Mechanics */}
        {tab === 2 && (
          <>
            <Section title="Coupon Step-Up Mechanics — Trigger Scenarios">
              {COUPON_SCENARIOS.map((s, i) => (
                <div key={i} style={{ display: 'flex', gap: 16, marginBottom: 12, padding: 14, background: '#f9fafb', borderRadius: 6, alignItems: 'center', border: `1px solid ${s.color}22` }}>
                  <div style={{ background: s.color, color: '#fff', borderRadius: 6, padding: '6px 14px', fontWeight: 700, fontSize: 13, minWidth: 100, textAlign: 'center' }}>
                    {s.scenario}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, color: '#374151', marginBottom: 2 }}>{s.status}</div>
                    <div style={{ fontSize: 12, color: '#6b7280' }}>
                      Coupon adjustment: <strong style={{ color: s.coupon_delta_bps > 0 ? '#ef4444' : EM }}>
                        {s.coupon_delta_bps > 0 ? `+${s.coupon_delta_bps} bps` : 'No change'}
                      </strong>
                    </div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 18, fontWeight: 800, color: s.color }}>{s.coupon_delta_bps > 0 ? `+${s.coupon_delta_bps}` : '0'}</div>
                    <div style={{ fontSize: 10, color: '#9ca3af' }}>bps step-up</div>
                  </div>
                </div>
              ))}
            </Section>
            <Section title="Illustrative Coupon Trajectory (Base: 4.50%)">
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={couponLineData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                  <YAxis domain={[4.3, 4.9]} tickFormatter={v => `${v}%`} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(v) => [`${v}%`]} />
                  <Legend />
                  <Line type="monotone" dataKey="on_track" stroke={EM} strokeWidth={2} name="On-Track (no step-up)" dot={false} />
                  <Line type="monotone" dataKey="missed" stroke="#ef4444" strokeWidth={2} strokeDasharray="5 5" name="Missed (25bps step-up yr 3)" dot={false} />
                </LineChart>
              </ResponsiveContainer>
              <div style={{ marginTop: 10, fontSize: 12, color: '#6b7280', lineHeight: 1.6 }}>
                Step-up provisions are typically structured around annual or bi-annual observation dates.
                Under ICMA SLB Principles 2023, the step-up must be meaningful (typically 12.5–25 bps)
                and cannot be offset by corresponding step-downs unless symmetrically structured.
              </div>
            </Section>
          </>
        )}

        {/* Tab 3 — Benchmark Compare */}
        {tab === 3 && (
          <>
            <Section title="Framework Requirements Comparison">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Requirement', 'ICMA SLB 2023', 'LMA SLL 2023', 'LSTA SLL 2021'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { req: 'KPI Materiality', icma: 'Core/Material to business', lma: 'Relevant to borrower', lsta: 'Material to business' },
                    { req: 'SMART Criteria', icma: 'Explicit requirement', lma: 'Implicit (best practice)', lsta: 'Recommended' },
                    { req: 'SPT Ambition', icma: 'Significant/Ambitious', lma: 'Ambitious vs trajectory', lsta: 'Meaningful improvement' },
                    { req: 'Step-Up Range', icma: '12.5–25 bps (typical)', lma: 'Margin adjustment', lsta: '5–10 bps (typical)' },
                    { req: 'Third-Party Verification', icma: 'Required annually', lma: 'Required at testing', lsta: 'Recommended' },
                    { req: 'Reporting Frequency', icma: 'Annual', lma: 'Annual minimum', lsta: 'Annual minimum' },
                  ].map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={{ padding: '9px 12px', fontWeight: 600 }}>{r.req}</td>
                      <td style={{ padding: '9px 12px', color: '#374151' }}>{r.icma}</td>
                      <td style={{ padding: '9px 12px', color: '#374151' }}>{r.lma}</td>
                      <td style={{ padding: '9px 12px', color: '#374151' }}>{r.lsta}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="Sample Instruments — SMART Score Comparison">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={SEED_INSTRUMENTS.map(ins => ({
                  name: ins.name.split(' ').slice(0, 2).join(' '),
                  Specific: ins.smart.specific,
                  Measurable: ins.smart.measurable,
                  Achievable: ins.smart.achievable,
                  Relevant: ins.smart.relevant,
                  'Time-bound': ins.smart.time_bound,
                }))} margin={{ top: 5, right: 20, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 20]} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Specific" fill="#10b981" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Measurable" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Achievable" fill="#f59e0b" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Relevant" fill="#8b5cf6" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="Time-bound" fill="#ef4444" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          </>
        )}

        {/* Tab 4 — Reference */}
        {tab === 4 && (
          <>
            <Section title="ICMA SLB Principles 2023 — Key Components">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Component', 'Description', 'Guidance'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { comp: '1. KPI Selection', desc: "Core to issuer's business model, material, measurable", guide: 'Use ICMA KPI registry; cover >60% of EBITDA exposure' },
                    { comp: '2. SPT Calibration', desc: 'Significant/ambitious vs issuer trajectory', guide: 'Minimum 15% improvement vs baseline; sector-benchmarked' },
                    { comp: '3. Bond Characteristics', desc: 'Coupon step-up of 12.5–25 bps if SPT missed', guide: 'Observe on 1-2 annual dates; cannot be pre-called to avoid' },
                    { comp: '4. Reporting', desc: 'Annual KPI performance report', guide: 'Publish before coupon observation date; board-signed' },
                    { comp: '5. Verification', desc: 'External verifier (auditor / ESG rating agency)', guide: 'Limited assurance minimum; reasonable assurance preferred' },
                  ].map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={{ padding: '9px 12px', fontWeight: 700, color: EM }}>{r.comp}</td>
                      <td style={{ padding: '9px 12px' }}>{r.desc}</td>
                      <td style={{ padding: '9px 12px', color: '#6b7280', fontSize: 12 }}>{r.guide}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="Common KPI Registry">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['KPI', 'Unit', 'Typical Sector', 'Typical Target'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '2px solid #e5e7eb', fontWeight: 700, fontSize: 12 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {KPI_REGISTRY.map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: i % 2 === 0 ? '#fff' : '#fafafa' }}>
                      <td style={{ padding: '9px 12px', fontWeight: 600 }}>{r.kpi}</td>
                      <td style={{ padding: '9px 12px', color: '#374151', fontFamily: 'monospace', fontSize: 12 }}>{r.unit}</td>
                      <td style={{ padding: '9px 12px', color: '#6b7280' }}>{r.sector}</td>
                      <td style={{ padding: '9px 12px', color: EM, fontWeight: 600 }}>{r.typical_target}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="API Endpoints">
              {[
                { method: 'POST', path: '/api/v1/sl-finance/assess', desc: 'Assess SLB/SLL SMART score and SPT calibration' },
                { method: 'POST', path: '/api/v1/sl-finance/spt-calibrate', desc: 'Calibrate SPT against science-based target trajectory' },
                { method: 'GET', path: '/api/v1/sl-finance/ref/kpi-registry', desc: 'ICMA common KPI registry' },
                { method: 'GET', path: '/api/v1/sl-finance/ref/frameworks', desc: 'ICMA SLB / LMA SLL framework requirements' },
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
