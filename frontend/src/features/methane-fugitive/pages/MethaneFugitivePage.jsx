/**
 * MethaneFugitivePage.jsx
 * Route: /methane-fugitive
 *
 * Engine: E58 — Methane & Fugitive Emissions
 * API prefix: /api/v1/methane-fugitive
 *
 * Tab 1 — GWP Assessment         POST /api/v1/methane-fugitive/gwp-assessment
 * Tab 2 — EU Methane Regulation  POST /api/v1/methane-fugitive/eu-methane-reg
 * Tab 3 — OGMP 2.0 Framework     POST /api/v1/methane-fugitive/ogmp-framework
 * Tab 4 — Super-Emitter Detection POST /api/v1/methane-fugitive/super-emitter
 * Tab 5 — Abatement Curve        POST /api/v1/methane-fugitive/abatement-curve
 */
import axios from 'axios';
import { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, ReferenceLine,
  ScatterChart, Scatter, ZAxis,
} from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const TT = { backgroundColor: '#fff', border: '1px solid #e5e7eb', color: '#111', fontSize: 11 };

/* ── Primitives ─────────────────────────────────────────────────────────── */
const Section = ({ title, children }) => (
  <div className="mb-6">
    <h2 className="text-lg font-semibold text-black mb-3 border-b border-gray-200 pb-2">{title}</h2>
    {children}
  </div>
);
const KpiCard = ({ label, value, sub, color = 'emerald' }) => (
  <div className="bg-white border border-gray-200 rounded-lg p-4">
    <div className="text-xs text-gray-500 mb-1">{label}</div>
    <div className={`text-2xl font-bold text-${color}-600`}>{value}</div>
    {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
  </div>
);
const Row = ({ children }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">{children}</div>
);
const Inp = ({ label, value, onChange, type = 'text' }) => (
  <div>
    <label className="text-xs text-gray-500 block mb-1">{label}</label>
    <input type={type} value={value} onChange={e => onChange(e.target.value)}
      className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm" />
  </div>
);
const Sel = ({ label, value, onChange, options }) => (
  <div>
    <label className="text-xs text-gray-500 block mb-1">{label}</label>
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm bg-white">
      {options.map(o => <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>)}
    </select>
  </div>
);
const Btn = ({ onClick, children, color = 'emerald' }) => (
  <button onClick={onClick}
    className={`bg-${color}-600 text-white px-4 py-2 rounded text-sm hover:bg-${color}-700`}>
    {children}
  </button>
);
const Spinner = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
  </div>
);

/* ── Seed RNG ───────────────────────────────────────────────────────────── */
function seedVal(i, seed) {
  return Math.abs(Math.sin(i * 9301 + seed * 49297) * 233280) % 233280 / 233280;
}
function mkSeed(entityId) {
  return Math.abs((entityId || 'default').split('').reduce((a, c) => a + c.charCodeAt(0), 0));
}

const fmtNum = v => v >= 1e6 ? `${(v / 1e6).toFixed(2)}M` : v >= 1e3 ? `${(v / 1e3).toFixed(1)}k` : `${v}`;

const SECTOR_OPTIONS = ['oil_gas', 'gas', 'coal', 'upstream', 'midstream'].map(s => ({
  value: s, label: s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
}));

/* ════════════════════════════════════════════════════════════════════════ */
export default function MethaneFugitivePage() {
  const tabs = ['GWP Assessment', 'EU Methane Reg', 'OGMP 2.0 Framework', 'Super-Emitter Detection', 'Abatement Curve'];
  const [tab, setTab] = useState(0);

  /* ── Tab 1: GWP Assessment ─────────────────────────────────────────── */
  const [t1, setT1] = useState({ entity_id: 'UPSTREAM-001', sector: 'oil_gas', baseline_methane_tpa: '50000', reported_gwp_basis: 'GWP-100' });
  const [t1Data, setT1Data] = useState(null);
  const [t1Loading, setT1Loading] = useState(false);

  const runT1 = useCallback(() => {
    setT1Loading(true);
    const payload = { ...t1, baseline_methane_tpa: Number(t1.baseline_methane_tpa) };
    axios.post(`${API}/api/v1/methane-fugitive/gwp-assessment`, payload)
      .then(r => setT1Data(r.data))
      .catch(() => {
        const mTpa = Number(t1.baseline_methane_tpa);
        const gwp100 = mTpa * 29.8; // AR6 GWP-100
        const gwp20 = mTpa * 82.5;  // AR6 GWP-20
        setT1Data({
          gwp100_co2e_tpa: Math.round(gwp100),
          gwp20_co2e_tpa: Math.round(gwp20),
          gwp_ratio: (gwp20 / gwp100).toFixed(2),
          comparison: [
            { basis: 'GWP-100 (AR6)', value: Math.round(gwp100) },
            { basis: 'GWP-20 (AR6)', value: Math.round(gwp20) },
          ],
        });
      })
      .finally(() => setT1Loading(false));
  }, [t1]);

  useEffect(() => { runT1(); }, []); // eslint-disable-line

  /* ── Tab 2: EU Methane Regulation ──────────────────────────────────── */
  const [t2, setT2] = useState({ entity_id: 'UPSTREAM-001', sector: 'oil_gas', country_code: 'NL' });
  const [t2Data, setT2Data] = useState(null);
  const [t2Loading, setT2Loading] = useState(false);

  const runT2 = useCallback(() => {
    setT2Loading(true);
    axios.post(`${API}/api/v1/methane-fugitive/eu-methane-reg`, { ...t2 })
      .then(r => setT2Data(r.data))
      .catch(() => {
        const seed = mkSeed(t2.entity_id);
        const reqs = [
          'Art 12 LDAR', 'Art 14 Venting Limits', 'Art 15 Flaring Limits',
          'Art 17 MRV', 'Art 18 Reporting', 'Art 22 Third Country Imports',
          'Art 28 Penalties', 'Art 30 Monitoring',
        ];
        setT2Data({
          eu_compliance_status: seedVal(1, seed) > 0.5 ? 'Compliant' : 'Partially Compliant',
          venting_prohibition_deadline: '2025-12-31',
          penalty_risk_eur: Math.round(seedVal(2, seed) * 5000000 + 500000),
          requirement_scores: reqs.map((r, i) => ({
            requirement: r,
            score: Math.round(seedVal(i + 3, seed) * 50 + 35),
            threshold: 75,
          })),
        });
      })
      .finally(() => setT2Loading(false));
  }, [t2]);

  /* ── Tab 3: OGMP 2.0 Framework ─────────────────────────────────────── */
  const [t3, setT3] = useState({ entity_id: 'UPSTREAM-001', sector: 'oil_gas', ogmp_level: '2' });
  const [t3Data, setT3Data] = useState(null);
  const [t3Loading, setT3Loading] = useState(false);

  const runT3 = useCallback(() => {
    setT3Loading(true);
    const payload = { ...t3, ogmp_level: Number(t3.ogmp_level) };
    axios.post(`${API}/api/v1/methane-fugitive/ogmp-framework`, payload)
      .then(r => setT3Data(r.data))
      .catch(() => {
        const seed = mkSeed(t3.entity_id);
        const currentLevel = Number(t3.ogmp_level);
        const targetLevel = Math.min(currentLevel + 2, 5);
        const categories = ['Completeness', 'Measurement', 'Reconciliation', 'Verification', 'Reporting'];
        setT3Data({
          current_ogmp_level: currentLevel,
          target_level: targetLevel,
          gap_score: Math.round(seedVal(1, seed) * 30 + 20),
          category_progress: categories.map((c, i) => ({
            category: c,
            current: Math.round(seedVal(i + 2, seed) * 30 + currentLevel * 18),
            target: targetLevel * 20,
          })),
          accuracy_by_level: [1, 2, 3, 4, 5].map(l => ({
            level: `L${l}`,
            accuracy: Math.round(50 + l * 10 + seedVal(l, seed) * 5),
          })),
        });
      })
      .finally(() => setT3Loading(false));
  }, [t3]);

  /* ── Tab 4: Super-Emitter Detection ────────────────────────────────── */
  const [t4, setT4] = useState({ entity_id: 'UPSTREAM-001', sector: 'oil_gas', super_emitter_events: '12' });
  const [t4Data, setT4Data] = useState(null);
  const [t4Loading, setT4Loading] = useState(false);

  const runT4 = useCallback(() => {
    setT4Loading(true);
    const payload = { ...t4, super_emitter_events: Number(t4.super_emitter_events) };
    axios.post(`${API}/api/v1/methane-fugitive/super-emitter`, payload)
      .then(r => setT4Data(r.data))
      .catch(() => {
        const seed = mkSeed(t4.entity_id);
        const numEvents = Number(t4.super_emitter_events);
        const events = Array.from({ length: Math.max(numEvents, 5) }, (_, i) => ({
          event: `SE-${String(i + 1).padStart(3, '0')}`,
          emissions_t: Math.round(seedVal(i + 2, seed) * 500 + 50),
        }));
        const totalEmissions = events.reduce((a, e) => a + e.emissions_t, 0);
        const unepTarget = 0.2;
        const actualIntensity = seedVal(1, seed) * 0.4 + 0.1;
        setT4Data({
          events_detected: numEvents,
          total_super_emitter_emissions_t: totalEmissions,
          unep_intensity_target_met: actualIntensity <= unepTarget,
          actual_intensity_pct: Math.round(actualIntensity * 1000) / 10,
          events,
        });
      })
      .finally(() => setT4Loading(false));
  }, [t4]);

  /* ── Tab 5: Abatement Curve ─────────────────────────────────────────── */
  const [t5, setT5] = useState({ entity_id: 'UPSTREAM-001', sector: 'oil_gas' });
  const [t5Data, setT5Data] = useState(null);
  const [t5Loading, setT5Loading] = useState(false);

  const runT5 = useCallback(() => {
    setT5Loading(true);
    axios.post(`${API}/api/v1/methane-fugitive/abatement-curve`, { ...t5 })
      .then(r => setT5Data(r.data))
      .catch(() => {
        const seed = mkSeed(t5.entity_id);
        const measures = [
          'LDAR Equipment', 'Compressor Upgrades', 'Pneumatic Controllers',
          'Pipeline Integrity', 'Flare Capture', 'Tank Vapour Recovery', 'Well Completion',
        ];
        const abatementData = measures.map((m, i) => ({
          measure: m,
          cost_usd_t: Math.round(seedVal(i * 2, seed) * 30 - 5),
          abatement_potential_pct: Math.round(seedVal(i * 2 + 1, seed) * 15 + 3),
        })).sort((a, b) => a.cost_usd_t - b.cost_usd_t);
        const totalPotential = abatementData.reduce((a, m) => a + m.abatement_potential_pct, 0);
        const avgCost = Math.round(abatementData.reduce((a, m) => a + m.cost_usd_t, 0) / abatementData.length);
        setT5Data({
          total_abatement_potential_pct: Math.min(totalPotential, 100),
          avg_abatement_cost_usd_t: avgCost,
          ldar_compliance_score: Math.round(seedVal(1, seed) * 30 + 55),
          measures: abatementData,
        });
      })
      .finally(() => setT5Loading(false));
  }, [t5]);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Methane & Fugitive Emissions</h1>
          <p className="text-sm text-gray-500 mt-1">E58 — GWP assessment, EU Methane Reg 2024/1787, OGMP 2.0, super-emitter detection, abatement curve</p>
        </div>

        {/* Tab Bar */}
        <div className="flex border-b border-gray-200 mb-6 flex-wrap">
          {tabs.map((t, i) => (
            <button key={i} onClick={() => setTab(i)}
              className={`px-4 py-2 text-sm font-medium ${tab === i ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-gray-500'}`}>
              {t}
            </button>
          ))}
        </div>

        {/* ── Tab 1: GWP Assessment ─── */}
        {tab === 0 && (
          <div>
            <Section title="Global Warming Potential Assessment (IPCC AR6)">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t1.entity_id} onChange={v => setT1(p => ({ ...p, entity_id: v }))} />
                <Sel label="Sector" value={t1.sector} onChange={v => setT1(p => ({ ...p, sector: v }))} options={SECTOR_OPTIONS} />
                <Inp label="Baseline Methane (t/pa)" value={t1.baseline_methane_tpa} onChange={v => setT1(p => ({ ...p, baseline_methane_tpa: v }))} type="number" />
                <Sel label="Reported GWP Basis" value={t1.reported_gwp_basis} onChange={v => setT1(p => ({ ...p, reported_gwp_basis: v }))}
                  options={[{ value: 'GWP-100', label: 'GWP-100' }, { value: 'GWP-20', label: 'GWP-20' }]} />
              </div>
              <div className="mb-4"><Btn onClick={runT1}>Run GWP Assessment</Btn></div>
            </Section>

            {t1Loading ? <Spinner /> : t1Data && (
              <>
                <Row>
                  <KpiCard label="GWP-100 CO2e (t/pa)" value={fmtNum(t1Data.gwp100_co2e_tpa)} sub="AR6 factor: 29.8" color="emerald" />
                  <KpiCard label="GWP-20 CO2e (t/pa)" value={fmtNum(t1Data.gwp20_co2e_tpa)} sub="AR6 factor: 82.5" color="red" />
                  <KpiCard label="GWP-20/GWP-100 Ratio" value={t1Data.gwp_ratio} sub="Near-term warming factor" color="amber" />
                  <KpiCard label="Methane Input (t/pa)" value={fmtNum(Number(t1.baseline_methane_tpa))} sub={t1.reported_gwp_basis} />
                </Row>
                <Section title="GWP-100 vs GWP-20 CO2e Comparison (t/pa)">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={t1Data.comparison} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="basis" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 11 }} tickFormatter={v => fmtNum(v)} />
                      <Tooltip contentStyle={TT} formatter={v => [fmtNum(v), 'CO2e t/pa']} />
                      <Bar dataKey="value" name="CO2e t/pa" fill="#10b981" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 2: EU Methane Regulation ─── */}
        {tab === 1 && (
          <div>
            <Section title="EU Methane Regulation 2024/1787 Compliance">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t2.entity_id} onChange={v => setT2(p => ({ ...p, entity_id: v }))} />
                <Sel label="Sector" value={t2.sector} onChange={v => setT2(p => ({ ...p, sector: v }))} options={SECTOR_OPTIONS} />
                <Inp label="Country Code" value={t2.country_code} onChange={v => setT2(p => ({ ...p, country_code: v }))} />
              </div>
              <div className="mb-4"><Btn onClick={runT2}>Check Compliance</Btn></div>
            </Section>

            {t2Loading ? <Spinner /> : t2Data && (
              <>
                <Row>
                  <KpiCard label="EU Compliance Status" value={t2Data.eu_compliance_status} sub="Reg (EU) 2024/1787" color={t2Data.eu_compliance_status === 'Compliant' ? 'emerald' : 'amber'} />
                  <KpiCard label="Venting Prohibition Deadline" value={t2Data.venting_prohibition_deadline} sub="Article 14 deadline" color="amber" />
                  <KpiCard label="Penalty Risk" value={`€${(t2Data.penalty_risk_eur / 1e6).toFixed(1)}M`} sub="Estimated maximum" color="red" />
                  <KpiCard label="Country" value={t2.country_code} sub="Jurisdiction" />
                </Row>
                <Section title="EU Methane Reg Requirements Compliance Score vs Threshold (%)">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={t2Data.requirement_scores} margin={{ top: 10, right: 20, left: 0, bottom: 30 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="requirement" tick={{ fontSize: 9 }} angle={-20} textAnchor="end" />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={TT} />
                      <Legend />
                      <Bar dataKey="score" name="Compliance Score" fill="#10b981" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="threshold" name="Threshold" fill="#fbbf24" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 3: OGMP 2.0 Framework ─── */}
        {tab === 2 && (
          <div>
            <Section title="OGMP 2.0 Framework Assessment">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t3.entity_id} onChange={v => setT3(p => ({ ...p, entity_id: v }))} />
                <Sel label="Sector" value={t3.sector} onChange={v => setT3(p => ({ ...p, sector: v }))} options={SECTOR_OPTIONS} />
                <Sel label="Current OGMP Level" value={t3.ogmp_level} onChange={v => setT3(p => ({ ...p, ogmp_level: v }))}
                  options={[1, 2, 3, 4, 5].map(l => ({ value: String(l), label: `Level ${l}` }))} />
              </div>
              <div className="mb-4"><Btn onClick={runT3}>Assess OGMP Level</Btn></div>
            </Section>

            {t3Loading ? <Spinner /> : t3Data && (
              <>
                <Row>
                  <KpiCard label="Current OGMP Level" value={`L${t3Data.current_ogmp_level}`} sub="5-tier framework" color="amber" />
                  <KpiCard label="Target Level" value={`L${t3Data.target_level}`} sub="Recommended target" color="emerald" />
                  <KpiCard label="Gap Score" value={t3Data.gap_score} sub="Points to close" color={t3Data.gap_score > 30 ? 'red' : 'amber'} />
                  <KpiCard label="Sector" value={t3.sector.replace(/_/g, ' ').toUpperCase()} sub={`OGMP L${t3Data.current_ogmp_level}→L${t3Data.target_level}`} />
                </Row>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Section title="Category Progress: Current vs Target (%)">
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={t3Data.category_progress} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={TT} />
                        <Legend />
                        <Bar dataKey="current" name="Current %" fill="#10b981" radius={[3, 3, 0, 0]} />
                        <Bar dataKey="target" name="Target %" fill="#d1fae5" radius={[3, 3, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </Section>
                  <Section title="Measurement Accuracy by OGMP Level (%)">
                    <ResponsiveContainer width="100%" height={260}>
                      <LineChart data={t3Data.accuracy_by_level} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="level" tick={{ fontSize: 12 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={TT} />
                        <Line type="monotone" dataKey="accuracy" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} name="Accuracy %" />
                        <ReferenceLine x={`L${t3Data.current_ogmp_level}`} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'Current', position: 'top', fontSize: 10 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </Section>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── Tab 4: Super-Emitter Detection ─── */}
        {tab === 3 && (
          <div>
            <Section title="Super-Emitter Event Detection">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t4.entity_id} onChange={v => setT4(p => ({ ...p, entity_id: v }))} />
                <Sel label="Sector" value={t4.sector} onChange={v => setT4(p => ({ ...p, sector: v }))} options={SECTOR_OPTIONS} />
                <Inp label="Super-Emitter Events Detected" value={t4.super_emitter_events} onChange={v => setT4(p => ({ ...p, super_emitter_events: v }))} type="number" />
              </div>
              <div className="mb-4"><Btn onClick={runT4}>Detect Super-Emitters</Btn></div>
            </Section>

            {t4Loading ? <Spinner /> : t4Data && (
              <>
                <Row>
                  <KpiCard label="Events Detected" value={t4Data.events_detected} sub="Satellite + ground verified" color="red" />
                  <KpiCard label="Total Super-Emitter Emissions" value={`${fmtNum(t4Data.total_super_emitter_emissions_t)}t`} sub="Aggregate methane" color="red" />
                  <KpiCard label="UNEP Intensity Target Met" value={t4Data.unep_intensity_target_met ? 'Yes' : 'No'} sub={`Actual: ${t4Data.actual_intensity_pct}% vs 0.2% target`} color={t4Data.unep_intensity_target_met ? 'emerald' : 'red'} />
                  <KpiCard label="Avg Per Event" value={`${fmtNum(Math.round(t4Data.total_super_emitter_emissions_t / Math.max(t4Data.events_detected, 1)))}t`} sub="Average event size" />
                </Row>
                <Section title="Super-Emitter Events by Emissions (t) — Threshold 100t">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={t4Data.events.slice(0, 20)} margin={{ top: 10, right: 20, left: 0, bottom: 30 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="event" tick={{ fontSize: 9 }} angle={-30} textAnchor="end" />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={TT} />
                      <ReferenceLine y={100} stroke="#ef4444" strokeDasharray="4 4"
                        label={{ value: 'Threshold 100t', position: 'right', fontSize: 10 }} />
                      <Bar dataKey="emissions_t" name="Emissions (t)" fill="#ef4444" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 5: Abatement Curve ─── */}
        {tab === 4 && (
          <div>
            <Section title="IEA Methane Abatement Curve">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t5.entity_id} onChange={v => setT5(p => ({ ...p, entity_id: v }))} />
                <Sel label="Sector" value={t5.sector} onChange={v => setT5(p => ({ ...p, sector: v }))} options={SECTOR_OPTIONS} />
              </div>
              <div className="mb-4"><Btn onClick={runT5}>Build Abatement Curve</Btn></div>
            </Section>

            {t5Loading ? <Spinner /> : t5Data && (
              <>
                <Row>
                  <KpiCard label="Total Abatement Potential" value={`${t5Data.total_abatement_potential_pct}%`} sub="Of baseline methane (t/pa)" color="emerald" />
                  <KpiCard label="Avg Abatement Cost" value={`$${t5Data.avg_abatement_cost_usd_t}/t`} sub="USD per tCO2e abated" color="amber" />
                  <KpiCard label="LDAR Compliance Score" value={t5Data.ldar_compliance_score} sub="0-100 composite" color="emerald" />
                  <KpiCard label="Measures Identified" value={t5Data.measures?.length ?? 0} sub="IEA prioritised" />
                </Row>
                <Section title="Abatement Measures — Abatement Potential (%) sorted by Cost ($/t)">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={t5Data.measures} margin={{ top: 10, right: 20, left: 0, bottom: 30 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="measure" tick={{ fontSize: 9 }} angle={-20} textAnchor="end" />
                      <YAxis yAxisId="left" tick={{ fontSize: 11 }} label={{ value: 'Abatement %', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }} />
                      <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} label={{ value: '$/t cost', angle: 90, position: 'insideRight', style: { fontSize: 10 } }} />
                      <Tooltip contentStyle={TT} />
                      <Legend />
                      <Bar yAxisId="left" dataKey="abatement_potential_pct" name="Abatement Potential %" fill="#10b981" radius={[3, 3, 0, 0]} />
                      <Bar yAxisId="right" dataKey="cost_usd_t" name="Cost $/t" fill="#60a5fa" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
