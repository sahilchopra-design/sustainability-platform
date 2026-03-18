/**
 * EBAPillar3Page.jsx
 * Route: /eba-pillar3
 * E20 — EBA Pillar 3 ESG Disclosures (GL/2022/03, CRR Art 449a)
 * Tabs:
 *   1. Compliance Assessment  — template checklist, compliance score
 *   2. Physical Risk Heatmap  — NACE × hazard grid
 *   3. Template T7: Financed Emissions — Scope 1/2/3 BarChart by NACE
 *   4. Carbon-Related Assets  — Template 3 horizontal BarChart
 *   5. Reference              — template catalog, disclosure timeline
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const EM = '#10b981';

// ── Primitives ────────────────────────────────────────────────────────────
function Section({ title, subtitle, children, action }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-4">
      {(title || action) && (
        <div className="flex items-start justify-between mb-4">
          <div>
            {title && <h3 className="text-sm font-semibold text-gray-900">{title}</h3>}
            {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

function KpiCard({ label, value, sub, accent, badge }) {
  const accentCls = accent === 'green' ? 'text-emerald-600' : accent === 'red' ? 'text-red-600' : accent === 'amber' ? 'text-amber-600' : 'text-gray-900';
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="flex items-start justify-between mb-1">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">{label}</span>
        {badge && <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">{badge}</span>}
      </div>
      <div className={`text-2xl font-bold font-mono ${accentCls}`}>{value}</div>
      {sub && <div className="text-[11px] text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-3">
      <label className="text-xs font-medium text-gray-600 w-44 shrink-0">{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Inp({ value, onChange, type = 'text', min, max, step, placeholder }) {
  return (
    <input
      type={type} value={value} min={min} max={max} step={step}
      placeholder={placeholder}
      onChange={e => onChange(e.target.value)}
      className="w-full text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-black/20 bg-white"
    />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select
      value={value} onChange={e => onChange(e.target.value)}
      className="w-full text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-black/20 bg-white"
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Btn({ onClick, children, loading }) {
  return (
    <button
      onClick={onClick} disabled={loading}
      className={`px-4 py-2 rounded-lg text-xs font-semibold bg-black text-white hover:bg-gray-800 transition-colors ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}
    >
      {loading ? 'Running…' : children}
    </button>
  );
}

// ── Static seed data ───────────────────────────────────────────────────────
const TEMPLATES = [
  { id: 'T1',  name: 'Qualitative info on ESG risks', mandatory: 'All G-SIIs/O-SIIs', article: 'GL 2022/03 §3.1' },
  { id: 'T2',  name: 'ESG risks - governance & strategy', mandatory: 'All G-SIIs/O-SIIs', article: '§3.2' },
  { id: 'T3',  name: 'Carbon-related assets', mandatory: 'G-SIIs', article: 'CRR Art 449a(e)' },
  { id: 'T4',  name: 'Alignment metrics — carbon budget', mandatory: 'G-SIIs', article: '§4.1' },
  { id: 'T5',  name: 'Climate risk mitigation actions', mandatory: 'G-SIIs/O-SIIs', article: '§4.2' },
  { id: 'T6',  name: 'Exposures to physical climate risk', mandatory: 'G-SIIs/O-SIIs', article: '§5.1' },
  { id: 'T7',  name: 'Financed emissions', mandatory: 'G-SIIs', article: '§5.2 / PCAF' },
  { id: 'T8',  name: 'Weighted avg carbon intensity', mandatory: 'G-SIIs', article: '§5.3' },
  { id: 'T9',  name: 'Social risk exposures', mandatory: 'G-SIIs/O-SIIs', article: '§6.1' },
  { id: 'T10', name: 'Governance risk exposures', mandatory: 'G-SIIs/O-SIIs', article: '§7.1' },
];

const NACE_SECTORS = [
  'A — Agriculture', 'B — Mining', 'C — Manufacturing',
  'D — Energy', 'E — Water/Waste', 'F — Construction',
  'G — Trade', 'H — Transport',
];

const HAZARDS = ['Heat Stress', 'Flood', 'Drought', 'Sea-Level Rise', 'Wildfire', 'Cold Wave'];

const HEATMAP_SEED = [
  [82, 74, 68, 45, 55, 39],
  [55, 48, 71, 62, 44, 31],
  [61, 53, 59, 41, 37, 42],
  [88, 79, 64, 72, 43, 29],
  [67, 61, 80, 55, 38, 33],
  [72, 65, 57, 50, 41, 28],
  [54, 47, 52, 38, 35, 26],
  [63, 56, 61, 44, 49, 31],
];

const T7_DATA = [
  { sector: 'Agriculture', s1: 420, s2: 180, s3: 680 },
  { sector: 'Mining',      s1: 860, s2: 340, s3: 1240 },
  { sector: 'Mfg',         s1: 1100, s2: 520, s3: 2300 },
  { sector: 'Energy',      s1: 2400, s2: 890, s3: 3100 },
  { sector: 'Transport',   s1: 740, s2: 260, s3: 1880 },
  { sector: 'Real Estate', s1: 310, s2: 420, s3: 560 },
];

const CARBON_DATA = [
  { sector: 'C19 Petroleum Refining', exposure: 4.8 },
  { sector: 'B06 Coal/Oil Extraction', exposure: 3.2 },
  { sector: 'D35 Electricity Supply',  exposure: 6.1 },
  { sector: 'C20 Chemicals',           exposure: 2.7 },
  { sector: 'H51 Air Transport',       exposure: 1.9 },
];

const TIMELINE = [
  { date: 'Jun 2022', milestone: 'EBA GL/2022/03 published', type: 'published' },
  { date: 'Jun 2023', milestone: 'First full disclosure (Dec 2022 FY)', type: 'deadline' },
  { date: 'Dec 2023', milestone: 'Phased-in T3/T7/T8 disclosure due', type: 'deadline' },
  { date: 'Jun 2024', milestone: 'All templates mandatory for G-SIIs', type: 'deadline' },
  { date: 'Dec 2024', milestone: 'Enhanced quantitative templates (Pillar 3+)', type: 'upcoming' },
];

const cellColor = v => v >= 70 ? '#fca5a5' : v >= 50 ? '#fde68a' : '#a7f3d0';
const cellText  = v => v >= 70 ? '#7f1d1d' : v >= 50 ? '#78350f' : '#064e3b';

// ── Tabs ──────────────────────────────────────────────────────────────────
const TABS = ['Compliance Assessment', 'Physical Risk Heatmap', 'Template T7: Financed Emissions', 'Carbon-Related Assets', 'Reference'];

export default function EBAPillar3Page() {
  const [tab, setTab] = useState(0);

  // Tab 1 state
  const [entityName, setEntityName] = useState('Eurobank AG');
  const [totalAssets, setTotalAssets] = useState(120);
  const [instType, setInstType] = useState('G-SII');
  const [checkedTemplates, setCheckedTemplates] = useState({ T1: true, T2: true, T3: false, T4: false, T5: true, T6: true, T7: false, T8: false, T9: true, T10: true });
  const [assessResult, setAssessResult] = useState(null);
  const [assessLoading, setAssessLoading] = useState(false);
  const [assessError, setAssessError] = useState('');

  // Tab 3 state
  const [t7Loading, setT7Loading] = useState(false);
  const [t7Result, setT7Result] = useState(null);
  const [t7Error, setT7Error] = useState('');

  // Tab 4 state
  const [carbonLoading, setCarbonLoading] = useState(false);
  const [carbonResult, setCarbonResult] = useState(null);
  const [carbonError, setCarbonError] = useState('');

  const toggleTemplate = id => setCheckedTemplates(p => ({ ...p, [id]: !p[id] }));
  const completedCount = Object.values(checkedTemplates).filter(Boolean).length;
  const mandatoryIds = instType === 'G-SII' ? ['T1','T2','T3','T4','T5','T6','T7','T8','T9','T10'] : ['T1','T2','T5','T6','T9','T10'];
  const missingMandatory = mandatoryIds.filter(id => !checkedTemplates[id]);
  const complianceScore = Math.round((completedCount / (instType === 'G-SII' ? 10 : 6)) * 100);

  async function runAssess() {
    setAssessLoading(true); setAssessError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/eba-pillar3/assess`, {
        entity_name: entityName, total_assets_bn: totalAssets,
        institution_type: instType, completed_templates: Object.keys(checkedTemplates).filter(k => checkedTemplates[k]),
      });
      setAssessResult(data);
    } catch {
      setAssessError('API unavailable — showing local calculation.');
      setAssessResult({ compliance_score: complianceScore, missing_mandatory: missingMandatory, next_disclosure_date: '2025-06-30' });
    } finally { setAssessLoading(false); }
  }

  async function runT7() {
    setT7Loading(true); setT7Error('');
    try {
      const { data } = await axios.post(`${API}/api/v1/eba-pillar3/template-t7`, { entity_name: entityName });
      setT7Result(data);
    } catch {
      setT7Error('API unavailable — showing seed data.');
      setT7Result({ data: T7_DATA, intensity_avg: 148, paris_gap_pct: 34 });
    } finally { setT7Loading(false); }
  }

  async function runCarbon() {
    setCarbonLoading(true); setCarbonError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/eba-pillar3/carbon-related-assets`, { entity_name: entityName });
      setCarbonResult(data);
    } catch {
      setCarbonError('API unavailable — showing seed data.');
      setCarbonResult({ exposures: CARBON_DATA, stranded_risk_score: 62, carbon_assets_pct: 8.4 });
    } finally { setCarbonLoading(false); }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Title bar */}
      <div className="bg-black text-white px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold tracking-tight">EBA Pillar 3 ESG Disclosures</h1>
          <p className="text-xs text-gray-400 mt-0.5">GL/2022/03 · CRR Article 449a · Templates T1–T10</p>
        </div>
        <span className="text-[10px] font-bold px-2 py-1 rounded border border-emerald-500 text-emerald-400">E20</span>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 px-6 py-4">
        <KpiCard label="Templates Completed" value={`${completedCount}/10`} sub="Checked above" accent={completedCount >= 8 ? 'green' : 'amber'} />
        <KpiCard label="Compliance Score" value={`${complianceScore}%`} sub={instType} accent={complianceScore >= 80 ? 'green' : complianceScore >= 60 ? 'amber' : 'red'} />
        <KpiCard label="Financed Emissions Intensity" value="148" sub="tCO₂/MEUR avg" badge="T7" />
        <KpiCard label="Carbon-Related Assets" value="8.4%" sub="of total exposure" accent="amber" />
      </div>

      {/* Tab bar */}
      <div className="px-6 border-b border-gray-200 bg-white">
        <div className="flex gap-1 overflow-x-auto">
          {TABS.map((t, i) => (
            <button
              key={i} onClick={() => setTab(i)}
              className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors ${tab === i ? 'border-emerald-500 text-emerald-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >{t}</button>
          ))}
        </div>
      </div>

      <div className="px-6 py-4">

        {/* ── Tab 0: Compliance Assessment ── */}
        {tab === 0 && (
          <>
            <Section title="Institution Details" subtitle="Configure entity parameters for compliance assessment">
              <Row label="Entity Name"><Inp value={entityName} onChange={setEntityName} type="text" /></Row>
              <Row label="Total Assets (€bn)">
                <div className="flex items-center gap-3">
                  <input type="range" min={1} max={2000} value={totalAssets} onChange={e => setTotalAssets(+e.target.value)} className="flex-1 accent-emerald-500" />
                  <span className="text-sm font-mono w-20 text-right">€{totalAssets}bn</span>
                </div>
              </Row>
              <Row label="Institution Type">
                <Sel value={instType} onChange={setInstType} options={[{ value: 'G-SII', label: 'G-SII (Global Systemically Important)' }, { value: 'O-SII', label: 'O-SII (Other Systemically Important)' }, { value: 'Other', label: 'Other Institution' }]} />
              </Row>
            </Section>
            <Section title="Template Checklist" subtitle="Check all templates that have been completed in your Pillar 3 report">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-4">
                {TEMPLATES.map(t => {
                  const isMandatory = mandatoryIds.includes(t.id);
                  const checked = checkedTemplates[t.id];
                  return (
                    <label key={t.id} className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer ${checked ? 'border-emerald-300 bg-emerald-50' : 'border-gray-200 bg-white'}`}>
                      <input type="checkbox" checked={checked} onChange={() => toggleTemplate(t.id)} className="mt-0.5 accent-emerald-500" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-gray-700">{t.id}</span>
                          {isMandatory && <span className="text-[9px] px-1.5 py-0.5 rounded bg-black text-white font-bold">MANDATORY</span>}
                        </div>
                        <div className="text-xs text-gray-600 truncate">{t.name}</div>
                        <div className="text-[10px] text-gray-400">{t.article}</div>
                      </div>
                    </label>
                  );
                })}
              </div>
              <Btn onClick={runAssess} loading={assessLoading}>Run Compliance Assessment</Btn>
            </Section>
            {assessError && <div className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded p-3 mb-3">{assessError}</div>}
            {assessResult && (
              <Section title="Assessment Results">
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className={`text-3xl font-bold font-mono ${assessResult.compliance_score >= 80 ? 'text-emerald-600' : assessResult.compliance_score >= 60 ? 'text-amber-600' : 'text-red-600'}`}>{assessResult.compliance_score}%</div>
                    <div className="text-xs text-gray-500 mt-1">Compliance Score</div>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className="text-3xl font-bold font-mono text-red-600">{assessResult.missing_mandatory?.length || 0}</div>
                    <div className="text-xs text-gray-500 mt-1">Missing Mandatory</div>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className="text-sm font-bold text-gray-700">{assessResult.next_disclosure_date}</div>
                    <div className="text-xs text-gray-500 mt-1">Next Disclosure Date</div>
                  </div>
                </div>
                {assessResult.missing_mandatory?.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-gray-700 mb-2">Missing Mandatory Templates</div>
                    <div className="flex flex-wrap gap-2">
                      {assessResult.missing_mandatory.map(id => (
                        <span key={id} className="px-2 py-1 text-xs font-bold rounded bg-red-100 text-red-700 border border-red-300">{id}</span>
                      ))}
                    </div>
                  </div>
                )}
              </Section>
            )}
          </>
        )}

        {/* ── Tab 1: Physical Risk Heatmap ── */}
        {tab === 1 && (
          <Section title="Physical Risk Heatmap — NACE × Hazard Exposure" subtitle="Color scale: green (low) → amber (medium) → red (high exposure)">
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr>
                    <th className="text-left p-2 font-semibold text-gray-600 w-40">NACE Sector</th>
                    {HAZARDS.map(h => <th key={h} className="p-2 font-semibold text-gray-600 text-center whitespace-nowrap">{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {NACE_SECTORS.map((sector, si) => (
                    <tr key={sector}>
                      <td className="p-2 font-medium text-gray-700 text-xs">{sector}</td>
                      {HEATMAP_SEED[si].map((val, hi) => (
                        <td key={hi} style={{ backgroundColor: cellColor(val), color: cellText(val) }} className="p-2 text-center font-mono font-bold rounded">
                          {val}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="flex items-center gap-4 mt-4 text-xs text-gray-500">
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded inline-block bg-red-200"></span> High (&ge;70)</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded inline-block bg-yellow-200"></span> Medium (50–69)</span>
              <span className="flex items-center gap-1"><span className="w-3 h-3 rounded inline-block bg-emerald-200"></span> Low (&lt;50)</span>
              <span className="ml-auto text-gray-400">Source: EBA GL/2022/03 §5.1 — seed data</span>
            </div>
          </Section>
        )}

        {/* ── Tab 2: Template T7 ── */}
        {tab === 2 && (
          <>
            <Section title="Template T7 — Financed Emissions by NACE Sector" subtitle="Scope 1 / 2 / 3 breakdown (tCO₂e)">
              <Btn onClick={runT7} loading={t7Loading}>Load T7 Data</Btn>
              {t7Error && <div className="text-xs text-amber-600 mt-3">{t7Error}</div>}
            </Section>
            {(t7Result || !t7Loading) && (
              <Section title="Scope 1 / 2 / 3 by Sector">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={T7_DATA} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                    <XAxis dataKey="sector" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} unit=" kt" />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                    <Bar dataKey="s1" name="Scope 1" stackId="a" fill="#10b981" />
                    <Bar dataKey="s2" name="Scope 2" stackId="a" fill="#6ee7b7" />
                    <Bar dataKey="s3" name="Scope 3" stackId="a" fill="#d1fae5" />
                  </BarChart>
                </ResponsiveContainer>
                <table className="w-full text-xs mt-4">
                  <thead><tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-gray-500">Sector</th>
                    <th className="text-right py-2 text-gray-500">Scope 1</th>
                    <th className="text-right py-2 text-gray-500">Scope 2</th>
                    <th className="text-right py-2 text-gray-500">Scope 3</th>
                    <th className="text-right py-2 text-gray-500">Intensity (tCO₂/MEUR)</th>
                    <th className="text-right py-2 text-gray-500">Paris Gap %</th>
                  </tr></thead>
                  <tbody>
                    {T7_DATA.map((r, i) => {
                      const intensity = [148, 220, 185, 410, 270, 95][i];
                      const gap = [28, 45, 38, 62, 51, 18][i];
                      return (
                        <tr key={r.sector} className="border-b border-gray-100">
                          <td className="py-1.5 font-medium">{r.sector}</td>
                          <td className="py-1.5 text-right font-mono">{r.s1.toLocaleString()}</td>
                          <td className="py-1.5 text-right font-mono">{r.s2.toLocaleString()}</td>
                          <td className="py-1.5 text-right font-mono">{r.s3.toLocaleString()}</td>
                          <td className="py-1.5 text-right font-mono">{intensity}</td>
                          <td className={`py-1.5 text-right font-bold ${gap > 40 ? 'text-red-600' : gap > 25 ? 'text-amber-600' : 'text-emerald-600'}`}>{gap}%</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </Section>
            )}
          </>
        )}

        {/* ── Tab 3: Carbon-Related Assets ── */}
        {tab === 3 && (
          <>
            <Section title="Template T3 — Carbon-Related Asset Exposure" subtitle="Fossil fuel sector exposure as % of total lending">
              <Btn onClick={runCarbon} loading={carbonLoading}>Load Carbon Exposure Data</Btn>
              {carbonError && <div className="text-xs text-amber-600 mt-3">{carbonError}</div>}
            </Section>
            <Section title="Fossil Fuel Exposure by NACE (€bn)">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={CARBON_DATA} layout="vertical" margin={{ top: 4, right: 40, bottom: 4, left: 140 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis type="number" tick={{ fontSize: 10 }} unit="€bn" />
                  <YAxis type="category" dataKey="sector" tick={{ fontSize: 10 }} width={140} />
                  <Tooltip />
                  <Bar dataKey="exposure" name="Exposure (€bn)" fill={EM} radius={[0, 4, 4, 0]}>
                    {CARBON_DATA.map((_, i) => <Cell key={i} fill={['#ef4444','#f97316','#eab308','#10b981','#6366f1'][i]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="p-4 rounded-xl bg-gray-50 text-center">
                  <div className="text-2xl font-bold font-mono text-amber-600">62</div>
                  <div className="text-xs text-gray-500 mt-1">Stranded Asset Risk Score</div>
                </div>
                <div className="p-4 rounded-xl bg-gray-50 text-center">
                  <div className="text-2xl font-bold font-mono text-red-600">8.4%</div>
                  <div className="text-xs text-gray-500 mt-1">Carbon Assets / Total Exposure</div>
                </div>
              </div>
            </Section>
          </>
        )}

        {/* ── Tab 4: Reference ── */}
        {tab === 4 && (
          <>
            <Section title="Template Catalog — EBA GL/2022/03">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-gray-500">ID</th>
                  <th className="text-left py-2 text-gray-500">Name</th>
                  <th className="text-left py-2 text-gray-500">Mandatory For</th>
                  <th className="text-left py-2 text-gray-500">Article</th>
                </tr></thead>
                <tbody>
                  {TEMPLATES.map(t => (
                    <tr key={t.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-1.5 font-bold text-emerald-700">{t.id}</td>
                      <td className="py-1.5">{t.name}</td>
                      <td className="py-1.5 text-gray-500">{t.mandatory}</td>
                      <td className="py-1.5 font-mono text-gray-400">{t.article}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="Disclosure Timeline">
              <div className="relative pl-6">
                {TIMELINE.map((e, i) => (
                  <div key={i} className="flex items-start gap-3 mb-4 relative">
                    <div className={`w-3 h-3 rounded-full mt-0.5 shrink-0 ${e.type === 'published' ? 'bg-gray-400' : e.type === 'deadline' ? 'bg-red-400' : 'bg-emerald-400'}`} style={{ marginLeft: -18 }} />
                    <div>
                      <div className="text-xs font-bold text-gray-700">{e.date}</div>
                      <div className="text-xs text-gray-500">{e.milestone}</div>
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
