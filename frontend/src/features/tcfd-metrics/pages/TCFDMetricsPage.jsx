/**
 * TCFDMetricsPage.jsx — Route: /tcfd-metrics
 * TCFD Metrics & Targets Assessment
 * 11 Recommendations across 4 Pillars — Governance / Strategy / Risk Management / Metrics & Targets
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function Section({ title, children }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg mb-4">
      <div className="px-4 py-3 border-b border-gray-100">
        <span className="font-medium text-sm text-gray-700">{title}</span>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function KpiCard({ label, value, sub, color = 'text-gray-900' }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-xl font-semibold font-mono tabular-nums ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function Badge({ label, color = 'gray' }) {
  const cls = {
    green:  'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber:  'bg-amber-50  text-amber-700  border-amber-200',
    red:    'bg-red-50    text-red-700    border-red-200',
    blue:   'bg-blue-50   text-blue-700   border-blue-200',
    gray:   'bg-gray-50   text-gray-600   border-gray-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>;
}

function Row({ label, children }) {
  return (
    <div className="flex items-center gap-3 mb-2">
      <span className="text-xs text-gray-500 w-44 shrink-0">{label}</span>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Inp({ value, onChange, type = 'text', placeholder = '' }) {
  return (
    <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
      className="w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500" />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500">
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Chk({ checked, onChange, label }) {
  return (
    <label className="flex items-center gap-2 text-xs text-gray-700 cursor-pointer">
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)}
        className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
      {label}
    </label>
  );
}

function Btn({ onClick, loading, children, disabled }) {
  return (
    <button onClick={onClick} disabled={disabled || loading}
      className="px-4 py-1.5 rounded text-xs font-medium bg-black text-white hover:bg-gray-800 disabled:opacity-50">
      {loading ? 'Running...' : children}
    </button>
  );
}

function ErrBox({ msg }) {
  return <div className="bg-red-50 border border-red-200 rounded p-3 text-xs text-red-700 mb-4">{msg}</div>;
}

// ── TCFD Recommendations Reference Data ─────────────────────────────────────
const RECOMMENDATIONS = [
  { id: 'G1', pillar: 'Governance',       name: 'Board Oversight',           elements: ['Board oversight description', 'Governance structure detail', 'Board escalation processes'] },
  { id: 'G2', pillar: 'Governance',       name: 'Management Role',           elements: ['Management processes', 'Executive responsibility', 'Reporting lines'] },
  { id: 'S1', pillar: 'Strategy',         name: 'Climate Risks & Opportunities', elements: ['Short-term risks', 'Medium-term risks', 'Long-term opportunities', 'Opportunity categories'] },
  { id: 'S2', pillar: 'Strategy',         name: 'Business Impact',           elements: ['Business model impact', 'Strategy impact', 'Financial planning impact'] },
  { id: 'S3', pillar: 'Strategy',         name: 'Scenario Analysis',         elements: ['Scenario description', '2°C scenario', 'Resilience assessment'] },
  { id: 'RM1', pillar: 'Risk Management', name: 'Risk Identification',        elements: ['Process description', 'Physical risk processes', 'Transition risk processes'] },
  { id: 'RM2', pillar: 'Risk Management', name: 'Risk Management',            elements: ['Management processes', 'Priority determination', 'Materiality threshold'] },
  { id: 'RM3', pillar: 'Risk Management', name: 'Integration into ERM',       elements: ['ERM integration description', 'Board-level integration'] },
  { id: 'MT1', pillar: 'Metrics & Targets', name: 'Climate Metrics',          elements: ['Scope 1 GHG', 'Scope 2 GHG', 'Scope 3 GHG', 'Climate risk metrics', 'Water / land / waste metrics'] },
  { id: 'MT2', pillar: 'Metrics & Targets', name: 'Climate Risk Metrics',     elements: ['Transition risk metrics', 'Physical risk metrics', 'Financed emissions'] },
  { id: 'MT3', pillar: 'Metrics & Targets', name: 'Targets',                  elements: ['GHG reduction target', 'Target time horizon', 'Performance against target', 'Net-zero commitment'] },
];

const QUALITY_OPTIONS = [
  { value: 'none',    label: 'Not Disclosed' },
  { value: 'partial', label: 'Partial' },
  { value: 'full',    label: 'Full' },
];

const SECTOR_OPTIONS = [
  { value: 'financial_institutions', label: 'Financial Institutions' },
  { value: 'energy',                 label: 'Energy' },
  { value: 'transport',              label: 'Transport' },
  { value: 'buildings',              label: 'Buildings' },
  { value: 'agriculture',            label: 'Agriculture' },
  { value: 'general',               label: 'General (Other)' },
];

const MATURITY_COLOR = { 1: 'red', 2: 'orange', 3: 'yellow', 4: 'blue', 5: 'green' };

function buildDefaultRecs() {
  return RECOMMENDATIONS.reduce((acc, r) => {
    acc[r.id] = { disclosed: true, quality: 'partial', elements_covered: r.elements.slice(0, 2) };
    return acc;
  }, {});
}

// ── Tab 1: TCFD Assessment ───────────────────────────────────────────────────
function TCFDAssessmentTab({ onResult }) {
  const [entity, setEntity] = useState({
    entity_id: 'ENT-001',
    entity_name: 'Sample Bank PLC',
    sector: 'financial_institutions',
    disclosure_year: 2025,
  });
  const [recs, setRecs] = useState(buildDefaultRecs);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const setE = useCallback((k, v) => setEntity(f => ({ ...f, [k]: v })), []);

  const toggleElement = useCallback((recId, element) => {
    setRecs(prev => {
      const current = prev[recId].elements_covered;
      const next = current.includes(element)
        ? current.filter(e => e !== element)
        : [...current, element];
      return { ...prev, [recId]: { ...prev[recId], elements_covered: next } };
    });
  }, []);

  const run = async () => {
    setLoading(true); setErr(null); setResult(null);
    const recommendations = RECOMMENDATIONS.map(r => ({
      recommendation_id: r.id,
      pillar: r.pillar,
      disclosed: recs[r.id].disclosed,
      disclosure_quality: recs[r.id].quality,
      elements_covered: recs[r.id].elements_covered,
    }));
    try {
      const { data } = await axios.post(`${API}/api/v1/tcfd-metrics/assess`, {
        entity: { ...entity, disclosure_year: parseInt(entity.disclosure_year) },
        recommendations,
      });
      setResult(data);
      if (onResult) onResult(data);
    } catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  };

  const PILLARS = ['Governance', 'Strategy', 'Risk Management', 'Metrics & Targets'];

  return (
    <div>
      <Section title="Entity Configuration">
        <div className="grid grid-cols-2 gap-x-8">
          <div>
            <Row label="Entity ID"><Inp value={entity.entity_id} onChange={v => setE('entity_id', v)} /></Row>
            <Row label="Entity Name"><Inp value={entity.entity_name} onChange={v => setE('entity_name', v)} /></Row>
            <Row label="Sector"><Sel value={entity.sector} onChange={v => setE('sector', v)} options={SECTOR_OPTIONS} /></Row>
            <Row label="Disclosure Year"><Inp type="number" value={entity.disclosure_year} onChange={v => setE('disclosure_year', v)} /></Row>
          </div>
        </div>
      </Section>

      {PILLARS.map(pillar => (
        <Section key={pillar} title={`${pillar} Recommendations`}>
          <div className="space-y-3">
            {RECOMMENDATIONS.filter(r => r.pillar === pillar).map(r => (
              <div key={r.id} className="border border-gray-100 rounded-lg p-3">
                <div className="flex items-center gap-3 mb-2">
                  <Badge label={r.id} color="blue" />
                  <span className="text-xs font-semibold text-gray-700">{r.name}</span>
                  <div className="ml-auto flex items-center gap-2">
                    <Chk checked={recs[r.id].disclosed}
                      onChange={v => setRecs(p => ({ ...p, [r.id]: { ...p[r.id], disclosed: v } }))}
                      label="Disclosed" />
                    <div className="w-32">
                      <Sel value={recs[r.id].quality}
                        onChange={v => setRecs(p => ({ ...p, [r.id]: { ...p[r.id], quality: v } }))}
                        options={QUALITY_OPTIONS} />
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {r.elements.slice(0, 3).map(el => (
                    <label key={el} className="flex items-center gap-1 text-[10px] text-gray-600 cursor-pointer">
                      <input type="checkbox"
                        checked={recs[r.id].elements_covered.includes(el)}
                        onChange={() => toggleElement(r.id, el)}
                        className="text-emerald-600 focus:ring-emerald-500" />
                      {el}
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Section>
      ))}

      <div className="mb-4"><Btn onClick={run} loading={loading}>Run TCFD Assessment</Btn></div>

      {err && <ErrBox msg={err} />}

      {result && (
        <>
          <div className="grid grid-cols-4 gap-3 mb-4">
            <KpiCard label="Overall Score" value={`${(result.overall_score ?? 0).toFixed(1)}/100`}
              color={result.overall_score >= 70 ? 'text-emerald-700' : result.overall_score >= 40 ? 'text-amber-700' : 'text-red-600'} />
            <KpiCard label="Maturity Level" value={`Level ${result.maturity_level ?? 1}`}
              sub={result.maturity_description}
              color={{ 1: 'text-red-600', 2: 'text-orange-600', 3: 'text-yellow-600', 4: 'text-blue-700', 5: 'text-emerald-700' }[result.maturity_level] || 'text-gray-700'} />
            <KpiCard label="Fully Disclosed" value={result.fully_disclosed_count ?? 0}
              sub={`of ${RECOMMENDATIONS.length} recommendations`} color="text-emerald-700" />
            <KpiCard label="Blocking Gaps" value={result.blocking_gaps_count ?? 0}
              color={result.blocking_gaps_count > 0 ? 'text-red-600' : 'text-emerald-700'} />
          </div>

          <div className="flex items-center gap-2 mb-4">
            <Badge label={`Maturity: Level ${result.maturity_level}`}
              color={MATURITY_COLOR[result.maturity_level] || 'gray'} />
            {result.entity_name && <Badge label={result.entity_name} color="blue" />}
            <Badge label={entity.sector.replace(/_/g, ' ')} color="gray" />
          </div>

          {(result.pillar_results || []).length > 0 && (
            <Section title="Pillar Scores">
              <div className="grid grid-cols-4 gap-3">
                {result.pillar_results.map(p => (
                  <div key={p.pillar} className="border border-gray-200 rounded-lg p-3">
                    <p className="text-xs font-semibold text-gray-700 mb-1">{p.pillar}</p>
                    <p className="text-lg font-mono font-semibold text-gray-900 mb-1">{(p.score ?? 0).toFixed(0)}/100</p>
                    <div className="w-full bg-gray-100 rounded-full h-2">
                      <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${p.score ?? 0}%` }} />
                    </div>
                    <p className="text-[10px] text-gray-400 mt-1">{p.recs_count ?? 0} recommendations</p>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

// ── Tab 2: Pillar Breakdown ──────────────────────────────────────────────────
function PillarBreakdownTab() {
  // Deterministic seed-based demo data for radar chart
  const [expanded, setExpanded] = useState(null);

  const radarData = [
    { pillar: 'Governance',        score: 72 },
    { pillar: 'Strategy',          score: 58 },
    { pillar: 'Risk Management',   score: 65 },
    { pillar: 'Metrics & Targets', score: 44 },
  ];

  const pillarDetail = [
    { pillar: 'Governance',        fully: 2, partial: 0, none: 0, blocking: 0 },
    { pillar: 'Strategy',          fully: 1, partial: 2, none: 0, blocking: 1 },
    { pillar: 'Risk Management',   fully: 1, partial: 2, none: 0, blocking: 0 },
    { pillar: 'Metrics & Targets', fully: 0, partial: 2, none: 1, blocking: 2 },
  ];

  return (
    <div>
      <Section title="TCFD Pillar Scores — Radar Chart">
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid />
            <PolarAngleAxis dataKey="pillar" tick={{ fontSize: 11 }} />
            <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
            <Radar name="Score" dataKey="score" stroke="#059669" fill="#059669" fillOpacity={0.25} />
            <Tooltip formatter={(v) => [`${v}/100`, 'Score']} />
          </RadarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Pillar Detail — Expand to View">
        <div className="space-y-2">
          {pillarDetail.map(p => (
            <div key={p.pillar} className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50"
                onClick={() => setExpanded(expanded === p.pillar ? null : p.pillar)}
              >
                <span className="text-xs font-semibold text-gray-700">{p.pillar}</span>
                <div className="flex items-center gap-2">
                  <Badge label={`${p.fully} full`} color="green" />
                  <Badge label={`${p.partial} partial`} color="blue" />
                  <Badge label={`${p.none} none`} color="gray" />
                  {p.blocking > 0 && <Badge label={`${p.blocking} blocking`} color="red" />}
                  <span className="text-xs text-gray-400">{expanded === p.pillar ? '▲' : '▼'}</span>
                </div>
              </button>
              {expanded === p.pillar && (
                <div className="px-4 pb-4 bg-gray-50">
                  <table className="w-full text-xs mt-2">
                    <thead><tr className="text-left text-gray-500 border-b border-gray-200">
                      <th className="pb-2 font-medium">Rec ID</th>
                      <th className="pb-2 font-medium">Name</th>
                      <th className="pb-2 font-medium">Quality</th>
                      <th className="pb-2 font-medium">Blocking</th>
                    </tr></thead>
                    <tbody>
                      {RECOMMENDATIONS.filter(r => r.pillar === p.pillar).map((r, i) => {
                        const qualities = ['full', 'partial', 'partial', 'none'];
                        const quality = qualities[i % qualities.length];
                        const isBlocking = p.blocking > 0 && i === 0;
                        return (
                          <tr key={r.id} className={`border-b border-gray-100 ${isBlocking ? 'bg-red-50' : ''}`}>
                            <td className="py-1.5"><Badge label={r.id} color="blue" /></td>
                            <td className="py-1.5">{r.name}</td>
                            <td className="py-1.5">
                              <Badge label={quality} color={quality === 'full' ? 'green' : quality === 'partial' ? 'blue' : 'gray'} />
                            </td>
                            <td className="py-1.5">{isBlocking ? <Badge label="Blocking Gap" color="red" /> : '-'}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

// ── Tab 3: Sector Supplement ─────────────────────────────────────────────────
function SectorSupplementTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);
  const [selectedSector] = useState('financial_institutions');

  useEffect(() => {
    axios.get(`${API}/api/v1/tcfd-metrics/ref/sector-supplements`)
      .then(r => setData(r.data))
      .catch(e => setErr(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-xs text-gray-400 py-4 text-center">Loading sector supplements...</div>;
  if (err) return <ErrBox msg={err} />;

  return (
    <div>
      <Section title="TCFD Sector-Specific Supplement Metrics">
        <div className="grid grid-cols-2 gap-4">
          {(data?.sectors || data || []).map(s => {
            const isSelected = s.sector_id === selectedSector || s.sector === selectedSector;
            return (
              <div key={s.sector_id || s.sector}
                className={`border rounded-lg p-3 ${isSelected ? 'border-emerald-300 bg-emerald-50' : 'border-gray-200 bg-white'}`}>
                <div className="flex items-center gap-2 mb-2">
                  <p className="text-xs font-semibold text-gray-800">{s.sector_name || s.sector}</p>
                  {isSelected && <Badge label="Selected" color="green" />}
                </div>
                {(s.additional_metrics || s.metrics || []).length > 0 ? (
                  <ul className="text-xs text-gray-600 space-y-1">
                    {(s.additional_metrics || s.metrics).map((m, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-emerald-500 mt-0.5">-</span>
                        <span>{typeof m === 'string' ? m : m.name || m.metric}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-gray-400 italic">No sector-specific metrics defined</p>
                )}
              </div>
            );
          })}
        </div>
      </Section>
    </div>
  );
}

// ── Tab 4: Recommendations Reference ────────────────────────────────────────
function RecommendationsReferenceTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    axios.get(`${API}/api/v1/tcfd-metrics/ref/recommendations`)
      .then(r => setData(r.data))
      .catch(e => setErr(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-xs text-gray-400 py-4 text-center">Loading recommendations...</div>;
  if (err) return <ErrBox msg={err} />;

  const PILLARS = ['Governance', 'Strategy', 'Risk Management', 'Metrics & Targets'];
  const PILLAR_COLORS = {
    'Governance':        { border: 'border-blue-200',    bg: 'bg-blue-50',    text: 'text-blue-700' },
    'Strategy':          { border: 'border-emerald-200', bg: 'bg-emerald-50', text: 'text-emerald-700' },
    'Risk Management':   { border: 'border-amber-200',   bg: 'bg-amber-50',   text: 'text-amber-700' },
    'Metrics & Targets': { border: 'border-purple-200',  bg: 'bg-purple-50',  text: 'text-purple-700' },
  };

  const allRecs = data?.recommendations || data || RECOMMENDATIONS;

  return (
    <div>
      <div className="grid grid-cols-2 gap-4">
        {PILLARS.map(pillar => {
          const c = PILLAR_COLORS[pillar];
          const pillarRecs = allRecs.filter(r => r.pillar === pillar);
          return (
            <div key={pillar} className={`border rounded-lg p-3 ${c.border} ${c.bg}`}>
              <p className={`text-xs font-bold mb-3 ${c.text}`}>{pillar}</p>
              <div className="space-y-3">
                {pillarRecs.map(r => (
                  <div key={r.id || r.recommendation_id} className="bg-white border border-gray-100 rounded p-2.5">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge label={r.id || r.recommendation_id} color="blue" />
                      <span className="text-xs font-semibold text-gray-700">{r.name}</span>
                      {r.blocking && <span className="text-red-500 text-xs font-bold" title="Blocking">★</span>}
                    </div>
                    {r.description && <p className="text-[10px] text-gray-500 mb-1.5">{r.description}</p>}
                    {(r.elements || r.disclosure_elements || []).length > 0 && (
                      <ul className="text-[10px] text-gray-500 space-y-0.5">
                        {(r.elements || r.disclosure_elements).map((el, i) => (
                          <li key={i} className="flex items-center gap-1">
                            <span className="text-emerald-500">✓</span>
                            {typeof el === 'string' ? el : el.element || el.name}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Tab 5: Cross-Framework ───────────────────────────────────────────────────
function CrossFrameworkTab() {
  const [fw, setFw] = useState(null);
  const [maturity, setMaturity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/api/v1/tcfd-metrics/ref/cross-framework`),
      axios.get(`${API}/api/v1/tcfd-metrics/ref/maturity-levels`),
    ])
      .then(([f, m]) => { setFw(f.data); setMaturity(m.data); })
      .catch(e => setErr(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-xs text-gray-400 py-4 text-center">Loading...</div>;
  if (err) return <ErrBox msg={err} />;

  const MATURITY_STYLES = {
    1: { bg: 'bg-red-50',     border: 'border-red-200',    text: 'text-red-700' },
    2: { bg: 'bg-orange-50',  border: 'border-orange-200', text: 'text-orange-700' },
    3: { bg: 'bg-yellow-50',  border: 'border-yellow-200', text: 'text-yellow-700' },
    4: { bg: 'bg-blue-50',    border: 'border-blue-200',   text: 'text-blue-700' },
    5: { bg: 'bg-emerald-50', border: 'border-emerald-200',text: 'text-emerald-700' },
  };

  return (
    <div>
      {fw && (
        <Section title="TCFD — Cross-Framework Mapping">
          <table className="w-full text-xs mb-3">
            <thead><tr className="text-left text-gray-500 border-b border-gray-100">
              <th className="pb-2 font-medium">Framework</th>
              <th className="pb-2 font-medium">TCFD Equivalent</th>
              <th className="pb-2 font-medium">Alignment</th>
              <th className="pb-2 font-medium">Notes</th>
            </tr></thead>
            <tbody>
              {(fw.mappings || fw || []).map((m, i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="py-1.5 font-semibold">{m.framework}</td>
                  <td className="py-1.5 text-gray-600">{m.tcfd_equivalent || m.linkage || '-'}</td>
                  <td className="py-1.5">
                    <Badge label={m.alignment_level || m.alignment || 'Partial'}
                      color={{ high: 'green', medium: 'blue', low: 'amber' }[m.alignment_level || m.alignment] || 'gray'} />
                  </td>
                  <td className="py-1.5 text-gray-500 text-[10px]">{m.notes || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}

      {maturity && (
        <Section title="TCFD Maturity Levels (1–5)">
          <div className="grid grid-cols-5 gap-3">
            {[1, 2, 3, 4, 5].map(level => {
              const s = MATURITY_STYLES[level];
              const levelData = (maturity.levels || maturity || []).find(l => l.level === level || l.maturity_level === level) || {};
              return (
                <div key={level} className={`border rounded-lg p-3 ${s.border} ${s.bg}`}>
                  <p className={`text-sm font-bold mb-1 ${s.text}`}>Level {level}</p>
                  <p className="text-xs font-semibold text-gray-700 mb-1">{levelData.name || levelData.title || ['Initial', 'Developing', 'Defined', 'Managed', 'Optimising'][level - 1]}</p>
                  <p className="text-[10px] text-gray-500">{levelData.description || ['Ad-hoc disclosure, minimal awareness', 'Basic awareness, fragmented disclosure', 'Systematic approach, most pillars covered', 'Integrated, quantitative, scenario-based', 'Industry-leading, fully integrated, verified'][level - 1]}</p>
                </div>
              );
            })}
          </div>
        </Section>
      )}
    </div>
  );
}

// ── Page Shell ───────────────────────────────────────────────────────────────
const TABS = [
  { id: 'assess',    label: 'TCFD Assessment' },
  { id: 'pillars',   label: 'Pillar Breakdown' },
  { id: 'sector',    label: 'Sector Supplement' },
  { id: 'recs',      label: 'Recommendations Ref' },
  { id: 'cross',     label: 'Cross-Framework' },
];

export default function TCFDMetricsPage() {
  const [tab, setTab] = useState('assess');
  const [lastResult, setLastResult] = useState(null);

  return (
    <div className="p-4 max-w-6xl mx-auto">
      <div className="mb-4">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-lg font-semibold text-gray-900">TCFD Metrics & Targets Assessment</h1>
          <Badge label="TCFD 2017" color="blue" />
          <Badge label="11 Recommendations" color="gray" />
        </div>
        <p className="text-xs text-gray-500">
          4 Pillars (Governance / Strategy / Risk Management / Metrics & Targets) · 11 Recommendations · Sector Supplements · Maturity Level 1–5
        </p>
      </div>
      <div className="flex gap-1 mb-4 border-b border-gray-200">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-3 py-2 text-xs font-medium rounded-t transition-colors ${tab === t.id ? 'bg-black text-white' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}`}>
            {t.label}
          </button>
        ))}
      </div>
      {tab === 'assess'  && <TCFDAssessmentTab onResult={setLastResult} />}
      {tab === 'pillars' && <PillarBreakdownTab result={lastResult} />}
      {tab === 'sector'  && <SectorSupplementTab />}
      {tab === 'recs'    && <RecommendationsReferenceTab />}
      {tab === 'cross'   && <CrossFrameworkTab />}
    </div>
  );
}
