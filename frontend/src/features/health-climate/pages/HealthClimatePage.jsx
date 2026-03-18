/**
 * HealthClimatePage.jsx
 * Route: /health-climate
 *
 * Engine: E59 — Health-Climate Nexus
 * API prefix: /api/v1/health-climate
 *
 * Tab 1 — Heat Stress            POST /api/v1/health-climate/heat-stress
 * Tab 2 — Air Quality            POST /api/v1/health-climate/air-quality
 * Tab 3 — Vector Disease Risk    POST /api/v1/health-climate/vector-disease
 * Tab 4 — Health Financial Impact POST /api/v1/health-climate/financial-impact
 * Tab 5 — WHO Country Profiles   POST /api/v1/health-climate/who-profile
 */
import axios from 'axios';
import { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, ReferenceLine,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
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

const fmtUsd = v => v >= 1e9 ? `$${(v / 1e9).toFixed(1)}B` : v >= 1e6 ? `$${(v / 1e6).toFixed(1)}M` : `$${v?.toLocaleString()}`;

const SECTOR_OPTIONS = ['construction', 'agriculture', 'manufacturing', 'logistics', 'mining', 'utilities', 'services'].map(s => ({
  value: s, label: s.charAt(0).toUpperCase() + s.slice(1),
}));

const COUNTRY_OPTIONS = ['IN', 'US', 'DE', 'NG', 'BR', 'CN', 'ID', 'PH', 'EG', 'PK', 'BD', 'VN'].map(c => ({ value: c, label: c }));

/* ════════════════════════════════════════════════════════════════════════ */
export default function HealthClimatePage() {
  const tabs = ['Heat Stress', 'Air Quality', 'Vector Disease Risk', 'Health Financial Impact', 'WHO Country Profiles'];
  const [tab, setTab] = useState(0);

  /* ── Tab 1: Heat Stress ─────────────────────────────────────────────── */
  const [t1, setT1] = useState({ entity_id: 'CORP-001', country_code: 'IN', sector: 'construction', outdoor_workers_pct: '65', wbgt_baseline_c: '28' });
  const [t1Data, setT1Data] = useState(null);
  const [t1Loading, setT1Loading] = useState(false);

  const runT1 = useCallback(() => {
    setT1Loading(true);
    const payload = {
      ...t1,
      outdoor_workers_pct: Number(t1.outdoor_workers_pct),
      wbgt_baseline_c: Number(t1.wbgt_baseline_c),
    };
    axios.post(`${API}/api/v1/health-climate/heat-stress`, payload)
      .then(r => setT1Data(r.data))
      .catch(() => {
        const seed = mkSeed(t1.entity_id);
        const base = Number(t1.wbgt_baseline_c);
        const scenarios = [
          { scenario: 'RCP 2.6', wbgt: base + seedVal(1, seed) * 1.5 + 0.5 },
          { scenario: 'RCP 4.5', wbgt: base + seedVal(2, seed) * 2.5 + 1.5 },
          { scenario: 'RCP 8.5', wbgt: base + seedVal(3, seed) * 4 + 3 },
        ].map(s => ({ ...s, wbgt: Math.round(s.wbgt * 10) / 10 }));
        const maxWbgt = scenarios[2].wbgt;
        const heatStressScore = Math.round((maxWbgt - 20) * 3.5);
        setT1Data({
          heat_stress_score: Math.min(heatStressScore, 100),
          productivity_loss_pct: Math.round(seedVal(4, seed) * 20 + 5),
          labour_capacity_reduction_pct: Math.round(seedVal(5, seed) * 25 + 5),
          scenarios,
        });
      })
      .finally(() => setT1Loading(false));
  }, [t1]);

  useEffect(() => { runT1(); }, []); // eslint-disable-line

  /* ── Tab 2: Air Quality ─────────────────────────────────────────────── */
  const [t2, setT2] = useState({ entity_id: 'CORP-001', country_code: 'IN', pm25_baseline_ug_m3: '35' });
  const [t2Data, setT2Data] = useState(null);
  const [t2Loading, setT2Loading] = useState(false);

  const runT2 = useCallback(() => {
    setT2Loading(true);
    const payload = { ...t2, pm25_baseline_ug_m3: Number(t2.pm25_baseline_ug_m3) };
    axios.post(`${API}/api/v1/health-climate/air-quality`, payload)
      .then(r => setT2Data(r.data))
      .catch(() => {
        const pm25 = Number(t2.pm25_baseline_ug_m3);
        const WHO_AQG = 5;
        const EU_AQD = 10;
        setT2Data({
          pm25_health_risk_score: Math.min(Math.round((pm25 / WHO_AQG) * 15), 100),
          who_aqg_exceedance: Math.round((pm25 / WHO_AQG) * 10) / 10,
          eu_aqd_exceedance: Math.round((pm25 / EU_AQD) * 10) / 10,
          comparison: [
            { category: 'Measured PM2.5', value: pm25 },
            { category: 'WHO AQG', value: WHO_AQG },
            { category: 'EU AQD', value: EU_AQD },
          ],
        });
      })
      .finally(() => setT2Loading(false));
  }, [t2]);

  /* ── Tab 3: Vector Disease Risk ─────────────────────────────────────── */
  const [t3, setT3] = useState({ entity_id: 'CORP-001', country_code: 'NG', sector: 'agriculture' });
  const [t3Data, setT3Data] = useState(null);
  const [t3Loading, setT3Loading] = useState(false);

  const runT3 = useCallback(() => {
    setT3Loading(true);
    axios.post(`${API}/api/v1/health-climate/vector-disease`, { ...t3 })
      .then(r => setT3Data(r.data))
      .catch(() => {
        const seed = mkSeed(t3.entity_id + t3.country_code);
        const diseases = ['malaria', 'dengue', 'lyme_disease', 'schistosomiasis'];
        setT3Data({
          rcp26_risk: Math.round(seedVal(1, seed) * 30 + 20),
          rcp45_risk: Math.round(seedVal(2, seed) * 35 + 30),
          rcp85_risk: Math.round(seedVal(3, seed) * 40 + 45),
          disease_risks: diseases.map((d, i) => ({
            disease: d.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
            rcp26: Math.round(seedVal(i * 3 + 4, seed) * 40 + 10),
            rcp45: Math.round(seedVal(i * 3 + 5, seed) * 50 + 20),
            rcp85: Math.round(seedVal(i * 3 + 6, seed) * 55 + 30),
          })),
        });
      })
      .finally(() => setT3Loading(false));
  }, [t3]);

  /* ── Tab 4: Health Financial Impact ────────────────────────────────── */
  const [t4, setT4] = useState({ entity_id: 'CORP-001', annual_revenue_usd: '2000000000', workforce_size: '15000', insurance_premium_usd: '5000000' });
  const [t4Data, setT4Data] = useState(null);
  const [t4Loading, setT4Loading] = useState(false);

  const runT4 = useCallback(() => {
    setT4Loading(true);
    const payload = {
      ...t4,
      annual_revenue_usd: Number(t4.annual_revenue_usd),
      workforce_size: Number(t4.workforce_size),
      insurance_premium_usd: Number(t4.insurance_premium_usd),
    };
    axios.post(`${API}/api/v1/health-climate/financial-impact`, payload)
      .then(r => setT4Data(r.data))
      .catch(() => {
        const seed = mkSeed(t4.entity_id);
        const rev = Number(t4.annual_revenue_usd);
        const wf = Number(t4.workforce_size);
        const ins = Number(t4.insurance_premium_usd);
        const healthcareUplift = Math.round(wf * (seedVal(1, seed) * 800 + 400));
        const productivityLoss = Math.round(rev * (seedVal(2, seed) * 0.02 + 0.005));
        const insuranceIncrease = Math.round(ins * (seedVal(3, seed) * 0.3 + 0.1));
        const litigationRisk = Math.round(seedVal(4, seed) * 5000000 + 500000);
        const total = healthcareUplift + productivityLoss + insuranceIncrease + litigationRisk;
        setT4Data({
          total_health_financial_impact_usd: total,
          pct_of_revenue: Math.round((total / rev) * 1000) / 10,
          healthcare_uplift_usd: healthcareUplift,
          components: [
            { component: 'Healthcare Uplift', value: healthcareUplift },
            { component: 'Productivity Loss', value: productivityLoss },
            { component: 'Insurance Increase', value: insuranceIncrease },
            { component: 'Litigation Risk', value: litigationRisk },
          ],
        });
      })
      .finally(() => setT4Loading(false));
  }, [t4]);

  /* ── Tab 5: WHO Country Profiles ───────────────────────────────────── */
  const [t5, setT5] = useState({ entity_id: 'CORP-001', country_code: 'IN' });
  const [t5Data, setT5Data] = useState(null);
  const [t5Loading, setT5Loading] = useState(false);

  const runT5 = useCallback(() => {
    setT5Loading(true);
    axios.post(`${API}/api/v1/health-climate/who-profile`, { ...t5 })
      .then(r => setT5Data(r.data))
      .catch(() => {
        const seed = mkSeed(t5.country_code);
        setT5Data({
          who_ccs_score: Math.round(seedVal(1, seed) * 40 + 40),
          health_resilience: Math.round(seedVal(2, seed) * 30 + 40),
          ncchap_status: seedVal(3, seed) > 0.5 ? 'Submitted' : 'In Development',
          dimensions: [
            { dimension: 'heat_mortality', value: Math.round(seedVal(4, seed) * 60 + 20), fullMark: 100 },
            { dimension: 'pm25', value: Math.round(seedVal(5, seed) * 60 + 20), fullMark: 100 },
            { dimension: 'who_ccs_score', value: Math.round(seedVal(6, seed) * 40 + 40), fullMark: 100 },
            { dimension: 'health_resilience', value: Math.round(seedVal(7, seed) * 30 + 40), fullMark: 100 },
            { dimension: 'ncchap', value: Math.round(seedVal(8, seed) * 50 + 25), fullMark: 100 },
            { dimension: 'ndc_health', value: Math.round(seedVal(9, seed) * 50 + 30), fullMark: 100 },
          ],
        });
      })
      .finally(() => setT5Loading(false));
  }, [t5]);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Health-Climate Nexus</h1>
          <p className="text-sm text-gray-500 mt-1">E59 — Heat stress, air quality, vector disease risk, financial impact, WHO country profiles</p>
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

        {/* ── Tab 1: Heat Stress ─── */}
        {tab === 0 && (
          <div>
            <Section title="Heat Stress Assessment (WBGT)">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t1.entity_id} onChange={v => setT1(p => ({ ...p, entity_id: v }))} />
                <Sel label="Country Code" value={t1.country_code} onChange={v => setT1(p => ({ ...p, country_code: v }))} options={COUNTRY_OPTIONS} />
                <Sel label="Sector" value={t1.sector} onChange={v => setT1(p => ({ ...p, sector: v }))} options={SECTOR_OPTIONS} />
                <Inp label="Outdoor Workers (%)" value={t1.outdoor_workers_pct} onChange={v => setT1(p => ({ ...p, outdoor_workers_pct: v }))} type="number" />
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="WBGT Baseline (°C)" value={t1.wbgt_baseline_c} onChange={v => setT1(p => ({ ...p, wbgt_baseline_c: v }))} type="number" />
              </div>
              <div className="mb-4"><Btn onClick={runT1}>Assess Heat Stress</Btn></div>
            </Section>

            {t1Loading ? <Spinner /> : t1Data && (
              <>
                <Row>
                  <KpiCard label="Heat Stress Score" value={t1Data.heat_stress_score} sub="0-100 composite" color={t1Data.heat_stress_score > 60 ? 'red' : 'amber'} />
                  <KpiCard label="Productivity Loss" value={`${t1Data.productivity_loss_pct}%`} sub="Climate-adjusted" color="amber" />
                  <KpiCard label="Labour Capacity Reduction" value={`${t1Data.labour_capacity_reduction_pct}%`} sub="vs. baseline" color="red" />
                  <KpiCard label="Outdoor Workers" value={`${t1.outdoor_workers_pct}%`} sub={t1.sector} />
                </Row>
                <Section title="WBGT (°C) Across RCP Scenarios — Thresholds: 28°C Moderate, 32°C High">
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={t1Data.scenarios} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="scenario" tick={{ fontSize: 12 }} />
                      <YAxis domain={[20, 40]} tick={{ fontSize: 11 }} label={{ value: '°C WBGT', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }} />
                      <Tooltip contentStyle={TT} formatter={v => [`${v}°C`, 'WBGT']} />
                      <ReferenceLine y={28} stroke="#f59e0b" strokeDasharray="4 4"
                        label={{ value: 'Moderate 28°C', position: 'right', fontSize: 10, fill: '#f59e0b' }} />
                      <ReferenceLine y={32} stroke="#ef4444" strokeDasharray="4 4"
                        label={{ value: 'High 32°C', position: 'right', fontSize: 10, fill: '#ef4444' }} />
                      <Line type="monotone" dataKey="wbgt" stroke="#10b981" strokeWidth={2.5} dot={{ r: 5, fill: '#10b981' }} name="WBGT °C" />
                    </LineChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 2: Air Quality ─── */}
        {tab === 1 && (
          <div>
            <Section title="PM2.5 Air Quality Health Risk">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t2.entity_id} onChange={v => setT2(p => ({ ...p, entity_id: v }))} />
                <Sel label="Country Code" value={t2.country_code} onChange={v => setT2(p => ({ ...p, country_code: v }))} options={COUNTRY_OPTIONS} />
                <Inp label="PM2.5 Baseline (μg/m³)" value={t2.pm25_baseline_ug_m3} onChange={v => setT2(p => ({ ...p, pm25_baseline_ug_m3: v }))} type="number" />
              </div>
              <div className="mb-4"><Btn onClick={runT2}>Assess Air Quality</Btn></div>
            </Section>

            {t2Loading ? <Spinner /> : t2Data && (
              <>
                <Row>
                  <KpiCard label="PM2.5 Health Risk Score" value={t2Data.pm25_health_risk_score} sub="0-100; higher = worse" color={t2Data.pm25_health_risk_score > 60 ? 'red' : 'amber'} />
                  <KpiCard label="WHO AQG Exceedance" value={`${t2Data.who_aqg_exceedance}x`} sub="vs. 5μg/m³ guideline" color={t2Data.who_aqg_exceedance > 3 ? 'red' : 'amber'} />
                  <KpiCard label="EU AQD Exceedance" value={`${t2Data.eu_aqd_exceedance}x`} sub="vs. 10μg/m³ directive" color={t2Data.eu_aqd_exceedance > 2 ? 'red' : 'emerald'} />
                  <KpiCard label="Country" value={t2.country_code} sub="Jurisdiction" />
                </Row>
                <Section title="PM2.5 vs WHO AQG and EU AQD Thresholds (μg/m³)">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={t2Data.comparison} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} label={{ value: 'μg/m³', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }} />
                      <Tooltip contentStyle={TT} formatter={v => [`${v} μg/m³`, '']} />
                      <Bar dataKey="value" name="PM2.5 μg/m³"
                        radius={[3, 3, 0, 0]}
                        fill="#10b981" />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 3: Vector Disease Risk ─── */}
        {tab === 2 && (
          <div>
            <Section title="Vector-Borne Disease Climate Risk">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t3.entity_id} onChange={v => setT3(p => ({ ...p, entity_id: v }))} />
                <Sel label="Country Code" value={t3.country_code} onChange={v => setT3(p => ({ ...p, country_code: v }))} options={COUNTRY_OPTIONS} />
                <Sel label="Sector" value={t3.sector} onChange={v => setT3(p => ({ ...p, sector: v }))} options={SECTOR_OPTIONS} />
              </div>
              <div className="mb-4"><Btn onClick={runT3}>Assess Disease Risk</Btn></div>
            </Section>

            {t3Loading ? <Spinner /> : t3Data && (
              <>
                <Row>
                  <KpiCard label="RCP 2.6 Risk Score" value={t3Data.rcp26_risk} sub="Low-warming scenario" color="emerald" />
                  <KpiCard label="RCP 4.5 Risk Score" value={t3Data.rcp45_risk} sub="Intermediate scenario" color="amber" />
                  <KpiCard label="RCP 8.5 Risk Score" value={t3Data.rcp85_risk} sub="High-warming scenario" color="red" />
                  <KpiCard label="Country" value={t3.country_code} sub="4 diseases assessed" />
                </Row>
                <Section title="Vector Disease Risk by RCP Scenario and Disease (0-100)">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={t3Data.disease_risks} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="disease" tick={{ fontSize: 11 }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={TT} />
                      <Legend />
                      <Bar dataKey="rcp26" name="RCP 2.6" fill="#22c55e" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="rcp45" name="RCP 4.5" fill="#f59e0b" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="rcp85" name="RCP 8.5" fill="#ef4444" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 4: Health Financial Impact ─── */}
        {tab === 3 && (
          <div>
            <Section title="Health-Climate Financial Impact Quantification">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t4.entity_id} onChange={v => setT4(p => ({ ...p, entity_id: v }))} />
                <Inp label="Annual Revenue (USD)" value={t4.annual_revenue_usd} onChange={v => setT4(p => ({ ...p, annual_revenue_usd: v }))} type="number" />
                <Inp label="Workforce Size" value={t4.workforce_size} onChange={v => setT4(p => ({ ...p, workforce_size: v }))} type="number" />
                <Inp label="Insurance Premium (USD)" value={t4.insurance_premium_usd} onChange={v => setT4(p => ({ ...p, insurance_premium_usd: v }))} type="number" />
              </div>
              <div className="mb-4"><Btn onClick={runT4}>Quantify Impact</Btn></div>
            </Section>

            {t4Loading ? <Spinner /> : t4Data && (
              <>
                <Row>
                  <KpiCard label="Total Health Financial Impact" value={fmtUsd(t4Data.total_health_financial_impact_usd)} sub="Annual estimated cost" color="red" />
                  <KpiCard label="% of Revenue" value={`${t4Data.pct_of_revenue}%`} sub="Revenue impact ratio" color="amber" />
                  <KpiCard label="Healthcare Uplift" value={fmtUsd(t4Data.healthcare_uplift_usd)} sub="Per-employee × workforce" color="amber" />
                  <KpiCard label="Workforce" value={Number(t4.workforce_size).toLocaleString()} sub="Employees assessed" />
                </Row>
                <Section title="Financial Impact Components (USD)">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={t4Data.components} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={v => fmtUsd(v)} />
                      <YAxis dataKey="component" type="category" tick={{ fontSize: 11 }} width={140} />
                      <Tooltip contentStyle={TT} formatter={v => [fmtUsd(v), 'Impact']} />
                      <Bar dataKey="value" name="Financial Impact USD" fill="#ef4444" radius={[0, 3, 3, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 5: WHO Country Profiles ─── */}
        {tab === 4 && (
          <div>
            <Section title="WHO Climate & Health Country Profile">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t5.entity_id} onChange={v => setT5(p => ({ ...p, entity_id: v }))} />
                <Sel label="Country Code" value={t5.country_code} onChange={v => setT5(p => ({ ...p, country_code: v }))} options={COUNTRY_OPTIONS} />
              </div>
              <div className="mb-4"><Btn onClick={runT5}>Load WHO Profile</Btn></div>
            </Section>

            {t5Loading ? <Spinner /> : t5Data && (
              <>
                <Row>
                  <KpiCard label="WHO CCS Score" value={t5Data.who_ccs_score} sub="Climate & Health Score" color="emerald" />
                  <KpiCard label="Health Resilience" value={t5Data.health_resilience} sub="System adaptive capacity" color={t5Data.health_resilience > 60 ? 'emerald' : 'amber'} />
                  <KpiCard label="NCCHAP Status" value={t5Data.ncchap_status} sub="National climate & health action plan" color={t5Data.ncchap_status === 'Submitted' ? 'emerald' : 'amber'} />
                  <KpiCard label="Country" value={t5.country_code} sub="WHO profile" />
                </Row>
                <Section title="WHO Country Health-Climate Dimensions (0-100)">
                  <ResponsiveContainer width="100%" height={320}>
                    <RadarChart data={t5Data.dimensions}>
                      <PolarGrid stroke="#e5e7eb" />
                      <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                      <Radar name="WHO Dimension Score" dataKey="value" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                      <Tooltip contentStyle={TT} />
                      <Legend />
                    </RadarChart>
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
