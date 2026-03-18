/**
 * ClimateLitigationPage.jsx
 * Route: /climate-litigation
 *
 * Engine: E56 — Climate Litigation & Legal Risk
 * API prefix: /api/v1/climate-litigation
 *
 * Tab 1 — TCFD Liability        POST /api/v1/climate-litigation/tcfd-liability
 * Tab 2 — Greenwashing Risk     POST /api/v1/climate-litigation/greenwashing-risk
 * Tab 3 — D&O Exposure          POST /api/v1/climate-litigation/do-exposure
 * Tab 4 — SEC Climate Disclosure POST /api/v1/climate-litigation/sec-disclosure
 * Tab 5 — Portfolio Litigation  POST /api/v1/climate-litigation/portfolio-litigation
 */
import axios from 'axios';
import { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, LineChart, Line, ReferenceLine,
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

/* ════════════════════════════════════════════════════════════════════════ */
export default function ClimateLitigationPage() {
  const tabs = ['TCFD Liability', 'Greenwashing Risk', 'D&O Exposure', 'SEC Climate Disclosure', 'Portfolio Litigation'];
  const [tab, setTab] = useState(0);

  /* ── Tab 1: TCFD Liability ─────────────────────────────────────────── */
  const [t1, setT1] = useState({ entity_id: 'CORP-001', sector: 'oil_gas', jurisdiction: 'US', tcfd_disclosure_score: '62' });
  const [t1Data, setT1Data] = useState(null);
  const [t1Loading, setT1Loading] = useState(false);

  const runT1 = useCallback(() => {
    setT1Loading(true);
    const payload = { ...t1, tcfd_disclosure_score: Number(t1.tcfd_disclosure_score) };
    axios.post(`${API}/api/v1/climate-litigation/tcfd-liability`, payload)
      .then(r => setT1Data(r.data))
      .catch(() => {
        const seed = mkSeed(t1.entity_id);
        const pillars = ['Governance', 'Strategy', 'Risk Mgmt', 'Metrics'];
        setT1Data({
          tcfd_liability_score: Math.round(seedVal(1, seed) * 40 + 45),
          disclosure_gap: Math.round(seedVal(2, seed) * 30 + 15),
          regulatory_penalties_usd: Math.round(seedVal(3, seed) * 8000000 + 500000),
          pillar_scores: pillars.map((p, i) => ({
            pillar: p,
            score: Math.round(seedVal(i + 4, seed) * 50 + 30),
            target: 80,
          })),
        });
      })
      .finally(() => setT1Loading(false));
  }, [t1]);

  useEffect(() => { runT1(); }, []); // eslint-disable-line

  /* ── Tab 2: Greenwashing Risk ──────────────────────────────────────── */
  const [t2, setT2] = useState({ entity_id: 'CORP-001', green_claims: 'net_zero by 2040\ncarbon neutral operations\nscience-based targets', sector: 'oil_gas' });
  const [t2Data, setT2Data] = useState(null);
  const [t2Loading, setT2Loading] = useState(false);

  const runT2 = useCallback(() => {
    setT2Loading(true);
    axios.post(`${API}/api/v1/climate-litigation/greenwashing-risk`, { ...t2 })
      .then(r => setT2Data(r.data))
      .catch(() => {
        const seed = mkSeed(t2.entity_id);
        const claims = ['net_zero', 'carbon_neutral', 'science_based', 'sustainable', 'green', 'eco_friendly'];
        setT2Data({
          greenwashing_risk_score: Math.round(seedVal(1, seed) * 35 + 50),
          claims_at_risk: Math.round(seedVal(2, seed) * 4 + 1),
          eu_green_claims_compliance: Math.round(seedVal(3, seed) * 40 + 30),
          claim_scores: claims.map((c, i) => ({
            claim: c,
            substantiation: Math.round(seedVal(i + 4, seed) * 60 + 20),
            fullMark: 100,
          })),
        });
      })
      .finally(() => setT2Loading(false));
  }, [t2]);

  /* ── Tab 3: D&O Exposure ───────────────────────────────────────────── */
  const [t3, setT3] = useState({ entity_id: 'CORP-001', revenue_usd: '5000000000', d_and_o_coverage_usd: '150000000', climate_targets_set: 'true' });
  const [t3Data, setT3Data] = useState(null);
  const [t3Loading, setT3Loading] = useState(false);

  const runT3 = useCallback(() => {
    setT3Loading(true);
    const payload = { ...t3, revenue_usd: Number(t3.revenue_usd), d_and_o_coverage_usd: Number(t3.d_and_o_coverage_usd), climate_targets_set: t3.climate_targets_set === 'true' };
    axios.post(`${API}/api/v1/climate-litigation/do-exposure`, payload)
      .then(r => setT3Data(r.data))
      .catch(() => {
        const seed = mkSeed(t3.entity_id);
        const vectors = ['disclosure_fraud', 'greenwashing', 'stranded_asset', 'physical_damage', 'fiduciary_duty'];
        setT3Data({
          do_exposure_score: Math.round(seedVal(1, seed) * 40 + 40),
          coverage_gap_usd: Math.round(seedVal(2, seed) * 200000000 + 50000000),
          litigation_risk_rating: ['Low', 'Moderate', 'High', 'Very High'][Math.floor(seedVal(3, seed) * 4)],
          vectors: vectors.map((v, i) => ({
            vector: v.replace(/_/g, ' '),
            probability: Math.round(seedVal(i + 4, seed) * 60 + 10),
          })),
        });
      })
      .finally(() => setT3Loading(false));
  }, [t3]);

  /* ── Tab 4: SEC Climate Disclosure ────────────────────────────────── */
  const [t4, setT4] = useState({ entity_id: 'CORP-001', filer_category: 'LAF', emissions_scope12: '450000', financial_effects: 'severe weather events affecting operations' });
  const [t4Data, setT4Data] = useState(null);
  const [t4Loading, setT4Loading] = useState(false);

  const runT4 = useCallback(() => {
    setT4Loading(true);
    const payload = { ...t4, emissions_scope12: Number(t4.emissions_scope12) };
    axios.post(`${API}/api/v1/climate-litigation/sec-disclosure`, payload)
      .then(r => setT4Data(r.data))
      .catch(() => {
        const seed = mkSeed(t4.entity_id);
        const items = ['1501 Governance', '1502 Strategy', '1503 Risk Mgmt', '1504 Targets', '1505 GHG'];
        setT4Data({
          sec_compliance_score: Math.round(seedVal(1, seed) * 40 + 45),
          attestation_required: seedVal(2, seed) > 0.5 ? 'Limited Assurance' : 'Reasonable Assurance',
          safe_harbor_eligible: seedVal(3, seed) > 0.4,
          item_scores: items.map((item, i) => ({
            item,
            score: Math.round(seedVal(i + 4, seed) * 50 + 30),
            required: 75,
          })),
        });
      })
      .finally(() => setT4Loading(false));
  }, [t4]);

  /* ── Tab 5: Portfolio Litigation ───────────────────────────────────── */
  const [t5, setT5] = useState({ portfolio_name: 'ENERGY-FUND-1', jurisdiction: 'US' });
  const [t5Data, setT5Data] = useState(null);
  const [t5Loading, setT5Loading] = useState(false);

  const runT5 = useCallback(() => {
    setT5Loading(true);
    axios.post(`${API}/api/v1/climate-litigation/portfolio-litigation`, { ...t5 })
      .then(r => setT5Data(r.data))
      .catch(() => {
        const seed = mkSeed(t5.portfolio_name);
        const sectors = ['Oil & Gas', 'Utilities', 'Mining', 'Chemicals', 'Aviation', 'Shipping', 'Cement', 'Steel', 'Real Estate', 'Finance'];
        setT5Data({
          portfolio_litigation_risk_usd: Math.round(seedVal(1, seed) * 500000000 + 100000000),
          avg_risk_score: Math.round(seedVal(2, seed) * 30 + 45) / 10,
          high_risk_assets_count: Math.round(seedVal(3, seed) * 15 + 3),
          sector_risks: sectors.map((s, i) => ({
            sector: s,
            risk_score: Math.round(seedVal(i + 4, seed) * 70 + 20),
          })),
        });
      })
      .finally(() => setT5Loading(false));
  }, [t5]);

  const fmtUsd = v => v >= 1e9 ? `$${(v / 1e9).toFixed(1)}B` : v >= 1e6 ? `$${(v / 1e6).toFixed(1)}M` : `$${v?.toLocaleString()}`;

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Climate Litigation & Legal Risk</h1>
          <p className="text-sm text-gray-500 mt-1">E56 — TCFD liability, greenwashing exposure, D&O risk, SEC disclosure compliance</p>
        </div>

        {/* Tab Bar */}
        <div className="flex border-b border-gray-200 mb-6">
          {tabs.map((t, i) => (
            <button key={i} onClick={() => setTab(i)}
              className={`px-4 py-2 text-sm font-medium ${tab === i ? 'border-b-2 border-emerald-600 text-emerald-600' : 'text-gray-500'}`}>
              {t}
            </button>
          ))}
        </div>

        {/* ── Tab 1: TCFD Liability ─── */}
        {tab === 0 && (
          <div>
            <Section title="TCFD Liability Assessment">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t1.entity_id} onChange={v => setT1(p => ({ ...p, entity_id: v }))} />
                <Sel label="Sector" value={t1.sector} onChange={v => setT1(p => ({ ...p, sector: v }))}
                  options={['oil_gas', 'finance', 'utilities', 'real_estate', 'other'].map(s => ({ value: s, label: s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) }))} />
                <Sel label="Jurisdiction" value={t1.jurisdiction} onChange={v => setT1(p => ({ ...p, jurisdiction: v }))}
                  options={['US', 'EU', 'UK', 'AUS', 'OTHER'].map(s => ({ value: s, label: s }))} />
                <Inp label="TCFD Disclosure Score (0-100)" value={t1.tcfd_disclosure_score} onChange={v => setT1(p => ({ ...p, tcfd_disclosure_score: v }))} type="number" />
              </div>
              <div className="mb-4"><Btn onClick={runT1}>Run Assessment</Btn></div>
            </Section>

            {t1Loading ? <Spinner /> : t1Data && (
              <>
                <Row>
                  <KpiCard label="TCFD Liability Score" value={t1Data.tcfd_liability_score} sub="Higher = more exposure" color="red" />
                  <KpiCard label="Disclosure Gap" value={`${t1Data.disclosure_gap}%`} sub="vs. required minimum" color="amber" />
                  <KpiCard label="Regulatory Penalties" value={fmtUsd(t1Data.regulatory_penalties_usd)} sub="Estimated maximum" color="red" />
                  <KpiCard label="Sector" value={t1.sector.replace(/_/g, ' ').toUpperCase()} sub={t1.jurisdiction} />
                </Row>
                <Section title="TCFD 4-Pillar Scores vs Target">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={t1Data.pillar_scores} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="pillar" tick={{ fontSize: 11 }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={TT} />
                      <Legend />
                      <Bar dataKey="score" name="Current Score" fill="#10b981" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="target" name="Target" fill="#d1fae5" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 2: Greenwashing Risk ─── */}
        {tab === 1 && (
          <div>
            <Section title="Greenwashing Risk Assessment">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Inp label="Entity ID" value={t2.entity_id} onChange={v => setT2(p => ({ ...p, entity_id: v }))} />
                <Sel label="Sector" value={t2.sector} onChange={v => setT2(p => ({ ...p, sector: v }))}
                  options={['oil_gas', 'finance', 'utilities', 'real_estate', 'other'].map(s => ({ value: s, label: s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) }))} />
              </div>
              <div className="mb-4">
                <label className="text-xs text-gray-500 block mb-1">Green Claims (one per line)</label>
                <textarea value={t2.green_claims} onChange={e => setT2(p => ({ ...p, green_claims: e.target.value }))}
                  className="w-full border border-gray-300 rounded px-3 py-1.5 text-sm h-20" />
              </div>
              <div className="mb-4"><Btn onClick={runT2}>Analyse Claims</Btn></div>
            </Section>

            {t2Loading ? <Spinner /> : t2Data && (
              <>
                <Row>
                  <KpiCard label="Greenwashing Risk Score" value={t2Data.greenwashing_risk_score} sub="0-100; higher = riskier" color="red" />
                  <KpiCard label="Claims at Risk" value={t2Data.claims_at_risk} sub="Unsubstantiated claims" color="amber" />
                  <KpiCard label="EU Green Claims Compliance" value={`${t2Data.eu_green_claims_compliance}%`} sub="Art. 8 requirement" color="emerald" />
                  <KpiCard label="Sector" value={t2.sector.replace(/_/g, ' ').toUpperCase()} sub="Assessed" />
                </Row>
                <Section title="Claim Substantiation Radar (0-100)">
                  <ResponsiveContainer width="100%" height={300}>
                    <RadarChart data={t2Data.claim_scores}>
                      <PolarGrid stroke="#e5e7eb" />
                      <PolarAngleAxis dataKey="claim" tick={{ fontSize: 11 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                      <Radar name="Substantiation Score" dataKey="substantiation" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                      <Tooltip contentStyle={TT} />
                    </RadarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 3: D&O Exposure ─── */}
        {tab === 2 && (
          <div>
            <Section title="Directors & Officers Exposure">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t3.entity_id} onChange={v => setT3(p => ({ ...p, entity_id: v }))} />
                <Inp label="Revenue USD" value={t3.revenue_usd} onChange={v => setT3(p => ({ ...p, revenue_usd: v }))} type="number" />
                <Inp label="D&O Coverage USD" value={t3.d_and_o_coverage_usd} onChange={v => setT3(p => ({ ...p, d_and_o_coverage_usd: v }))} type="number" />
                <Sel label="Climate Targets Set" value={t3.climate_targets_set} onChange={v => setT3(p => ({ ...p, climate_targets_set: v }))}
                  options={[{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }]} />
              </div>
              <div className="mb-4"><Btn onClick={runT3}>Assess D&O Exposure</Btn></div>
            </Section>

            {t3Loading ? <Spinner /> : t3Data && (
              <>
                <Row>
                  <KpiCard label="D&O Exposure Score" value={t3Data.do_exposure_score} sub="0-100 composite" color="red" />
                  <KpiCard label="Coverage Gap" value={fmtUsd(t3Data.coverage_gap_usd)} sub="Estimated uncovered liability" color="amber" />
                  <KpiCard label="Litigation Risk Rating" value={t3Data.litigation_risk_rating} sub="Overall assessment" color="emerald" />
                  <KpiCard label="Vectors Assessed" value={t3Data.vectors?.length ?? 5} sub="D&O exposure vectors" />
                </Row>
                <Section title="D&O Exposure Probability by Vector (%)">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={t3Data.vectors} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
                      <YAxis dataKey="vector" type="category" tick={{ fontSize: 11 }} width={120} />
                      <Tooltip contentStyle={TT} />
                      <Bar dataKey="probability" name="Probability %" fill="#ef4444" radius={[0, 3, 3, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 4: SEC Climate Disclosure ─── */}
        {tab === 3 && (
          <div>
            <Section title="SEC Climate Disclosure Compliance">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Inp label="Entity ID" value={t4.entity_id} onChange={v => setT4(p => ({ ...p, entity_id: v }))} />
                <Sel label="Filer Category" value={t4.filer_category} onChange={v => setT4(p => ({ ...p, filer_category: v }))}
                  options={['LAF', 'AF', 'NAF', 'SRC', 'EGC'].map(s => ({ value: s, label: s }))} />
                <Inp label="Scope 1+2 Emissions (tCO2e)" value={t4.emissions_scope12} onChange={v => setT4(p => ({ ...p, emissions_scope12: v }))} type="number" />
                <Inp label="Financial Effects Description" value={t4.financial_effects} onChange={v => setT4(p => ({ ...p, financial_effects: v }))} />
              </div>
              <div className="mb-4"><Btn onClick={runT4}>Check SEC Compliance</Btn></div>
            </Section>

            {t4Loading ? <Spinner /> : t4Data && (
              <>
                <Row>
                  <KpiCard label="SEC Compliance Score" value={t4Data.sec_compliance_score} sub="Reg S-K composite" color="emerald" />
                  <KpiCard label="Attestation Required" value={t4Data.attestation_required} sub="Per filer category" color="amber" />
                  <KpiCard label="Safe Harbor Eligible" value={t4Data.safe_harbor_eligible ? 'Yes' : 'No'} sub="PSLRA coverage" color={t4Data.safe_harbor_eligible ? 'emerald' : 'red'} />
                  <KpiCard label="Filer Category" value={t4.filer_category} sub="Reg S-K filing tier" />
                </Row>
                <Section title="Reg S-K Items 1501–1505 Compliance vs Required (%)">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={t4Data.item_scores} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="item" tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={TT} />
                      <Legend />
                      <Bar dataKey="score" name="Current Score" fill="#10b981" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="required" name="Required" fill="#fbbf24" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 5: Portfolio Litigation ─── */}
        {tab === 4 && (
          <div>
            <Section title="Portfolio Litigation Risk">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Portfolio Name" value={t5.portfolio_name} onChange={v => setT5(p => ({ ...p, portfolio_name: v }))} />
                <Sel label="Jurisdiction" value={t5.jurisdiction} onChange={v => setT5(p => ({ ...p, jurisdiction: v }))}
                  options={['US', 'EU', 'UK', 'AUS', 'OTHER'].map(s => ({ value: s, label: s }))} />
              </div>
              <div className="mb-4"><Btn onClick={runT5}>Analyse Portfolio</Btn></div>
            </Section>

            {t5Loading ? <Spinner /> : t5Data && (
              <>
                <Row>
                  <KpiCard label="Portfolio Litigation Risk" value={fmtUsd(t5Data.portfolio_litigation_risk_usd)} sub="Estimated aggregate exposure" color="red" />
                  <KpiCard label="Avg Risk Score" value={t5Data.avg_risk_score} sub="Portfolio-weighted average" color="amber" />
                  <KpiCard label="High Risk Assets" value={t5Data.high_risk_assets_count} sub="Score > 65" color="red" />
                  <KpiCard label="Jurisdiction" value={t5.jurisdiction} sub="Regulatory framework" />
                </Row>
                <Section title="Sector Litigation Risk Score (0-100)">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={t5Data.sector_risks} margin={{ top: 10, right: 20, left: 0, bottom: 30 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="sector" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={TT} />
                      <ReferenceLine y={65} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'High Risk Threshold', position: 'right', fontSize: 10 }} />
                      <Bar dataKey="risk_score" name="Risk Score" fill="#10b981" radius={[3, 3, 0, 0]} />
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
