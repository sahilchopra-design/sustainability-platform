/**
 * ESGRatingsPage.jsx
 * Route: /esg-ratings
 *
 * Engine: E57 — ESG Ratings Reform
 * API prefix: /api/v1/esg-ratings
 *
 * Tab 1 — ESRA Authorisation     POST /api/v1/esg-ratings/esra-authorisation
 * Tab 2 — Divergence Analysis    POST /api/v1/esg-ratings/divergence-analysis
 * Tab 3 — Bias Detection         POST /api/v1/esg-ratings/bias-detection
 * Tab 4 — Composite Rating       POST /api/v1/esg-ratings/composite-rating
 * Tab 5 — Peer Benchmark         POST /api/v1/esg-ratings/peer-benchmark
 */
import axios from 'axios';
import { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, PieChart, Pie, Cell, LineChart, Line, ReferenceLine,
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

const RATING_SCALE = ['CCC', 'B', 'BB', 'BBB', 'A', 'AA', 'AAA'];
const GAUGE_COLORS = ['#ef4444', '#f97316', '#eab308', '#84cc16', '#22c55e', '#10b981', '#059669'];

/* ════════════════════════════════════════════════════════════════════════ */
export default function ESGRatingsPage() {
  const tabs = ['ESRA Authorisation', 'Divergence Analysis', 'Bias Detection', 'Composite Rating', 'Peer Benchmark'];
  const [tab, setTab] = useState(0);

  /* ── Tab 1: ESRA Authorisation ─────────────────────────────────────── */
  const [t1, setT1] = useState({ entity_id: 'ESG-PROVIDER-01', provider_name: 'ClimateScore Ltd', sector: 'finance', country_code: 'DE' });
  const [t1Data, setT1Data] = useState(null);
  const [t1Loading, setT1Loading] = useState(false);

  const runT1 = useCallback(() => {
    setT1Loading(true);
    axios.post(`${API}/api/v1/esg-ratings/esra-authorisation`, { ...t1 })
      .then(r => setT1Data(r.data))
      .catch(() => {
        const seed = mkSeed(t1.entity_id);
        const reqs = ['R01 Independence', 'R02 Transparency', 'R03 Methodology', 'R04 Governance', 'R05 Conflicts', 'R06 Data Quality', 'R07 Disclosure', 'R08 Supervision'];
        setT1Data({
          esra_compliance_score: Math.round(seedVal(1, seed) * 40 + 45),
          authorisation_status: seedVal(2, seed) > 0.55 ? 'Eligible' : 'Non-Eligible',
          gaps_found: Math.round(seedVal(3, seed) * 5 + 1),
          requirements: reqs.map((r, i) => ({
            requirement: r,
            score: Math.round(seedVal(i + 4, seed) * 50 + 30),
            threshold: 70,
          })),
        });
      })
      .finally(() => setT1Loading(false));
  }, [t1]);

  useEffect(() => { runT1(); }, []); // eslint-disable-line

  /* ── Tab 2: Divergence Analysis ────────────────────────────────────── */
  const [t2, setT2] = useState({ entity_id: 'CORP-001', msci_rating: '65', sustainalytics_score: '22', bloomberg_score: '58' });
  const [t2Data, setT2Data] = useState(null);
  const [t2Loading, setT2Loading] = useState(false);

  const runT2 = useCallback(() => {
    setT2Loading(true);
    const payload = {
      ...t2,
      msci_rating: Number(t2.msci_rating),
      sustainalytics_score: Number(t2.sustainalytics_score),
      bloomberg_score: Number(t2.bloomberg_score),
    };
    axios.post(`${API}/api/v1/esg-ratings/divergence-analysis`, payload)
      .then(r => setT2Data(r.data))
      .catch(() => {
        const seed = mkSeed(t2.entity_id);
        // Normalise to 0-100
        const msciN = Number(t2.msci_rating);
        const sustN = (Number(t2.sustainalytics_score) / 50) * 100;
        const bloomN = Number(t2.bloomberg_score);
        setT2Data({
          overall_divergence_pct: Math.round(seedVal(1, seed) * 25 + 10),
          scope_divergence: Math.round(seedVal(2, seed) * 20 + 8),
          weight_divergence: Math.round(seedVal(3, seed) * 10 + 3),
          divergence_sources: [
            { source: 'Scope', pct: 56, fullMark: 100 },
            { source: 'Weight', pct: 23, fullMark: 100 },
            { source: 'Measurement', pct: 21, fullMark: 100 },
          ],
          provider_comparison: [
            { provider: 'MSCI', score: msciN },
            { provider: 'Sustainalytics', score: sustN },
            { provider: 'Bloomberg', score: bloomN },
          ],
        });
      })
      .finally(() => setT2Loading(false));
  }, [t2]);

  /* ── Tab 3: Bias Detection ─────────────────────────────────────────── */
  const [t3, setT3] = useState({ entity_id: 'CORP-001', company_size: 'mid', region: 'western_europe', sector: 'utilities' });
  const [t3Data, setT3Data] = useState(null);
  const [t3Loading, setT3Loading] = useState(false);

  const runT3 = useCallback(() => {
    setT3Loading(true);
    axios.post(`${API}/api/v1/esg-ratings/bias-detection`, { ...t3 })
      .then(r => setT3Data(r.data))
      .catch(() => {
        const seed = mkSeed(t3.entity_id);
        const base = Math.round(seedVal(1, seed) * 30 + 45);
        const sizeBias = (t3.company_size === 'micro' || t3.company_size === 'small') ? -(seedVal(2, seed) * 12 + 3) : (seedVal(2, seed) * 8);
        const geoBias = (t3.region === 'emerging_markets' || t3.region === 'asia_pacific') ? -(seedVal(3, seed) * 10 + 2) : (seedVal(3, seed) * 5);
        const sectorBias = seedVal(4, seed) * 10 - 5;
        setT3Data({
          size_bias_pct: Math.round(sizeBias * 10) / 10,
          geography_bias_pct: Math.round(geoBias * 10) / 10,
          sector_bias_pct: Math.round(sectorBias * 10) / 10,
          detected_score: base,
          expected_score: Math.round(base - sizeBias - geoBias - sectorBias),
          bias_adjustments: [
            { type: 'Size Bias', adjustment: Math.round(sizeBias * 10) / 10 },
            { type: 'Geography Bias', adjustment: Math.round(geoBias * 10) / 10 },
            { type: 'Sector Bias', adjustment: Math.round(sectorBias * 10) / 10 },
            { type: 'Reporting Bias', adjustment: Math.round((seedVal(5, seed) * 6 - 3) * 10) / 10 },
          ],
        });
      })
      .finally(() => setT3Loading(false));
  }, [t3]);

  /* ── Tab 4: Composite Rating ───────────────────────────────────────── */
  const [t4, setT4] = useState({ entity_id: 'CORP-001', sector: 'utilities' });
  const [t4Data, setT4Data] = useState(null);
  const [t4Loading, setT4Loading] = useState(false);

  const runT4 = useCallback(() => {
    setT4Loading(true);
    axios.post(`${API}/api/v1/esg-ratings/composite-rating`, { ...t4 })
      .then(r => setT4Data(r.data))
      .catch(() => {
        const seed = mkSeed(t4.entity_id);
        const score = Math.round(seedVal(1, seed) * 60 + 30);
        const ratingIdx = Math.floor((score / 100) * 6);
        const subpillars = ['E1 Climate', 'E2 Pollution', 'E3 Water', 'E4 Biodiversity', 'E5 Circular'];
        setT4Data({
          composite_rating: RATING_SCALE[Math.min(ratingIdx, 6)],
          composite_score: score,
          e_pillar_divergence: Math.round(seedVal(2, seed) * 20 + 5),
          gauge_data: [
            { name: 'Score', value: score },
            { name: 'Remaining', value: 100 - score },
          ],
          e_subpillars: subpillars.map((s, i) => ({
            subpillar: s,
            divergence: Math.round(seedVal(i + 3, seed) * 25 + 3),
          })),
        });
      })
      .finally(() => setT4Loading(false));
  }, [t4]);

  /* ── Tab 5: Peer Benchmark ─────────────────────────────────────────── */
  const [t5, setT5] = useState({ entity_id: 'CORP-001', sector: 'utilities' });
  const [t5Data, setT5Data] = useState(null);
  const [t5Loading, setT5Loading] = useState(false);

  const runT5 = useCallback(() => {
    setT5Loading(true);
    axios.post(`${API}/api/v1/esg-ratings/peer-benchmark`, { ...t5 })
      .then(r => setT5Data(r.data))
      .catch(() => {
        const seed = mkSeed(t5.entity_id);
        const entityScore = Math.round(seedVal(1, seed) * 50 + 30);
        const peerScores = Array.from({ length: 10 }, (_, i) => Math.round(seedVal(i + 2, seed) * 50 + 25));
        const allScores = [...peerScores, entityScore].sort((a, b) => a - b);
        const rank = allScores.indexOf(entityScore) + 1;
        const percentile = Math.round((rank / allScores.length) * 100);
        const sectorMean = Math.round(peerScores.reduce((a, b) => a + b, 0) / peerScores.length);
        setT5Data({
          peer_percentile: percentile,
          sector_mean: sectorMean,
          above_average: entityScore > sectorMean,
          entity_score: entityScore,
          peer_data: peerScores.map((s, i) => ({ name: `Peer ${String.fromCharCode(65 + i)}`, score: s })).concat([{ name: 'Entity', score: entityScore }]),
        });
      })
      .finally(() => setT5Loading(false));
  }, [t5]);

  const sectorOptions = ['oil_gas', 'finance', 'utilities', 'real_estate', 'mining', 'chemicals', 'other'].map(s => ({ value: s, label: s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) }));

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">ESG Ratings Reform</h1>
          <p className="text-sm text-gray-500 mt-1">E57 — ESRA authorisation, provider divergence, bias detection, composite rating</p>
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

        {/* ── Tab 1: ESRA Authorisation ─── */}
        {tab === 0 && (
          <div>
            <Section title="ESRA Authorisation Requirements">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t1.entity_id} onChange={v => setT1(p => ({ ...p, entity_id: v }))} />
                <Inp label="Provider Name" value={t1.provider_name} onChange={v => setT1(p => ({ ...p, provider_name: v }))} />
                <Sel label="Sector" value={t1.sector} onChange={v => setT1(p => ({ ...p, sector: v }))} options={sectorOptions} />
                <Inp label="Country Code" value={t1.country_code} onChange={v => setT1(p => ({ ...p, country_code: v }))} />
              </div>
              <div className="mb-4"><Btn onClick={runT1}>Assess Authorisation</Btn></div>
            </Section>

            {t1Loading ? <Spinner /> : t1Data && (
              <>
                <Row>
                  <KpiCard label="ESRA Compliance Score" value={t1Data.esra_compliance_score} sub="Reg (EU) 2023/2859 composite" color="emerald" />
                  <KpiCard label="Authorisation Status" value={t1Data.authorisation_status} sub="ESMA eligibility" color={t1Data.authorisation_status === 'Eligible' ? 'emerald' : 'red'} />
                  <KpiCard label="Gaps Found" value={t1Data.gaps_found} sub="Requirements not met" color={t1Data.gaps_found > 3 ? 'red' : 'amber'} />
                  <KpiCard label="Provider" value={t1.provider_name} sub={t1.country_code} />
                </Row>
                <Section title="ESRA Requirements R01–R08 vs Threshold (%)">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={t1Data.requirements} margin={{ top: 10, right: 20, left: 0, bottom: 30 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="requirement" tick={{ fontSize: 9 }} angle={-20} textAnchor="end" />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={TT} />
                      <Legend />
                      <Bar dataKey="score" name="Score" fill="#10b981" radius={[3, 3, 0, 0]} />
                      <Bar dataKey="threshold" name="Threshold" fill="#fbbf24" radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 2: Divergence Analysis ─── */}
        {tab === 1 && (
          <div>
            <Section title="Provider Score Divergence">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t2.entity_id} onChange={v => setT2(p => ({ ...p, entity_id: v }))} />
                <Inp label="MSCI Rating (0-100)" value={t2.msci_rating} onChange={v => setT2(p => ({ ...p, msci_rating: v }))} type="number" />
                <Inp label="Sustainalytics (0-50)" value={t2.sustainalytics_score} onChange={v => setT2(p => ({ ...p, sustainalytics_score: v }))} type="number" />
                <Inp label="Bloomberg (0-100)" value={t2.bloomberg_score} onChange={v => setT2(p => ({ ...p, bloomberg_score: v }))} type="number" />
              </div>
              <div className="mb-4"><Btn onClick={runT2}>Analyse Divergence</Btn></div>
            </Section>

            {t2Loading ? <Spinner /> : t2Data && (
              <>
                <Row>
                  <KpiCard label="Overall Divergence" value={`${t2Data.overall_divergence_pct}%`} sub="Cross-provider spread" color="amber" />
                  <KpiCard label="Scope Divergence" value={`${t2Data.scope_divergence}%`} sub="56% of total divergence" color="red" />
                  <KpiCard label="Weight Divergence" value={`${t2Data.weight_divergence}%`} sub="23% of total divergence" color="amber" />
                  <KpiCard label="Entity" value={t2.entity_id} sub="3 providers analysed" />
                </Row>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Section title="Divergence Sources (%)">
                    <ResponsiveContainer width="100%" height={260}>
                      <RadarChart data={t2Data.divergence_sources}>
                        <PolarGrid stroke="#e5e7eb" />
                        <PolarAngleAxis dataKey="source" tick={{ fontSize: 12 }} />
                        <PolarRadiusAxis angle={30} domain={[0, 60]} tick={{ fontSize: 10 }} />
                        <Radar name="Divergence %" dataKey="pct" stroke="#10b981" fill="#10b981" fillOpacity={0.35} />
                        <Tooltip contentStyle={TT} />
                      </RadarChart>
                    </ResponsiveContainer>
                  </Section>
                  <Section title="Provider Scores Normalised (0-100)">
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={t2Data.provider_comparison} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="provider" tick={{ fontSize: 12 }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={TT} />
                        <Bar dataKey="score" name="Normalised Score" fill="#10b981" radius={[3, 3, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </Section>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── Tab 3: Bias Detection ─── */}
        {tab === 2 && (
          <div>
            <Section title="Rating Bias Detection">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t3.entity_id} onChange={v => setT3(p => ({ ...p, entity_id: v }))} />
                <Sel label="Company Size" value={t3.company_size} onChange={v => setT3(p => ({ ...p, company_size: v }))}
                  options={['large', 'mid', 'small', 'micro'].map(s => ({ value: s, label: s.charAt(0).toUpperCase() + s.slice(1) }))} />
                <Sel label="Region" value={t3.region} onChange={v => setT3(p => ({ ...p, region: v }))}
                  options={['western_europe', 'north_america', 'asia_pacific', 'emerging_markets'].map(s => ({ value: s, label: s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) }))} />
                <Sel label="Sector" value={t3.sector} onChange={v => setT3(p => ({ ...p, sector: v }))} options={sectorOptions} />
              </div>
              <div className="mb-4"><Btn onClick={runT3}>Detect Bias</Btn></div>
            </Section>

            {t3Loading ? <Spinner /> : t3Data && (
              <>
                <Row>
                  <KpiCard label="Size Bias" value={`${t3Data.size_bias_pct > 0 ? '+' : ''}${t3Data.size_bias_pct}%`} sub="Positive = upward bias" color={Math.abs(t3Data.size_bias_pct) > 5 ? 'red' : 'amber'} />
                  <KpiCard label="Geography Bias" value={`${t3Data.geography_bias_pct > 0 ? '+' : ''}${t3Data.geography_bias_pct}%`} sub="vs. Western Europe baseline" color={Math.abs(t3Data.geography_bias_pct) > 5 ? 'red' : 'amber'} />
                  <KpiCard label="Sector Bias" value={`${t3Data.sector_bias_pct > 0 ? '+' : ''}${t3Data.sector_bias_pct}%`} sub="vs. market average" color={Math.abs(t3Data.sector_bias_pct) > 3 ? 'amber' : 'emerald'} />
                  <KpiCard label="Detected vs Expected" value={`${t3Data.detected_score} / ${t3Data.expected_score}`} sub="Score comparison" />
                </Row>
                <Section title="Bias Adjustment by Type (% points)">
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={t3Data.bias_adjustments} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="type" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={TT} />
                      <ReferenceLine y={0} stroke="#374151" strokeDasharray="3 3" />
                      <Bar dataKey="adjustment" name="Bias Adjustment (pp)"
                        fill="#10b981"
                        radius={[3, 3, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── Tab 4: Composite Rating ─── */}
        {tab === 3 && (
          <div>
            <Section title="Composite ESG Rating">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t4.entity_id} onChange={v => setT4(p => ({ ...p, entity_id: v }))} />
                <Sel label="Sector" value={t4.sector} onChange={v => setT4(p => ({ ...p, sector: v }))} options={sectorOptions} />
              </div>
              <div className="mb-4"><Btn onClick={runT4}>Compute Rating</Btn></div>
            </Section>

            {t4Loading ? <Spinner /> : t4Data && (
              <>
                <Row>
                  <KpiCard label="Composite Rating" value={t4Data.composite_rating} sub="AAA–CCC scale" color="emerald" />
                  <KpiCard label="Composite Score" value={t4Data.composite_score} sub="0-100 normalised" color="emerald" />
                  <KpiCard label="E-Pillar Divergence" value={`${t4Data.e_pillar_divergence}%`} sub="Across E1–E5 sub-pillars" color="amber" />
                  <KpiCard label="Sector" value={t4.sector.replace(/_/g, ' ').toUpperCase()} sub="Peer-adjusted" />
                </Row>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Section title="Composite Score Gauge">
                    <ResponsiveContainer width="100%" height={260}>
                      <PieChart>
                        <Pie data={t4Data.gauge_data} cx="50%" cy="70%" startAngle={180} endAngle={0} innerRadius={60} outerRadius={100} dataKey="value">
                          <Cell fill="#10b981" />
                          <Cell fill="#e5e7eb" />
                        </Pie>
                        <text x="50%" y="72%" textAnchor="middle" className="text-2xl" style={{ fontSize: 24, fontWeight: 700, fill: '#059669' }}>{t4Data.composite_rating}</text>
                        <text x="50%" y="82%" textAnchor="middle" style={{ fontSize: 13, fill: '#6b7280' }}>{t4Data.composite_score}/100</text>
                        <Tooltip contentStyle={TT} />
                      </PieChart>
                    </ResponsiveContainer>
                  </Section>
                  <Section title="E-Pillar Sub-pillar Divergence (%)">
                    <ResponsiveContainer width="100%" height={260}>
                      <BarChart data={t4Data.e_subpillars} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                        <XAxis dataKey="subpillar" tick={{ fontSize: 10 }} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip contentStyle={TT} />
                        <Bar dataKey="divergence" name="Divergence %" fill="#f59e0b" radius={[3, 3, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </Section>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── Tab 5: Peer Benchmark ─── */}
        {tab === 4 && (
          <div>
            <Section title="Peer Benchmarking">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <Inp label="Entity ID" value={t5.entity_id} onChange={v => setT5(p => ({ ...p, entity_id: v }))} />
                <Sel label="Sector" value={t5.sector} onChange={v => setT5(p => ({ ...p, sector: v }))} options={sectorOptions} />
              </div>
              <div className="mb-4"><Btn onClick={runT5}>Run Benchmark</Btn></div>
            </Section>

            {t5Loading ? <Spinner /> : t5Data && (
              <>
                <Row>
                  <KpiCard label="Peer Percentile" value={`${t5Data.peer_percentile}th`} sub="vs. 10 sector peers" color="emerald" />
                  <KpiCard label="Sector Mean" value={t5Data.sector_mean} sub="Average peer score" color="amber" />
                  <KpiCard label="Entity vs Average" value={t5Data.above_average ? 'Above Average' : 'Below Average'} sub={`Score: ${t5Data.entity_score}`} color={t5Data.above_average ? 'emerald' : 'red'} />
                  <KpiCard label="Peers Compared" value="10" sub={t5.sector.replace(/_/g, ' ')} />
                </Row>
                <Section title="Entity vs Peer Distribution (ESG Score 0-100)">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={t5Data.peer_data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                      <Tooltip contentStyle={TT} />
                      <ReferenceLine y={t5Data.sector_mean} stroke="#f59e0b" strokeDasharray="4 4"
                        label={{ value: `Mean ${t5Data.sector_mean}`, position: 'right', fontSize: 10 }} />
                      <Bar dataKey="score" name="ESG Score"
                        fill="#10b981"
                        radius={[3, 3, 0, 0]} />
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
