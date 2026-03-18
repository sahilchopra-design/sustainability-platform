/**
 * Disclosure Frameworks Page
 * Tabbed interface for 5 backend regulatory disclosure engines:
 *   1. TNFD Assessment  (/api/v1/tnfd)
 *   2. CDP Scoring       (/api/v1/cdp)
 *   3. GRI Standards     (/api/v1/gri)
 *   4. SASB Industry     (/api/v1/sasb)
 *   5. SEC Climate       (/api/v1/sec-climate)
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Legend,
} from 'recharts';
import {
  Leaf, BarChart3, FileText, Building2, Scale,
  ChevronDown, ChevronRight, Loader2, AlertTriangle,
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

/* ── Shared helpers ──────────────────────────────────────────────────────── */

const inputCls = 'w-full bg-[#f5f6f8] border border-gray-300 rounded px-3 py-2 text-sm text-gray-900 focus:border-blue-500 focus:outline-none';
const btnCls   = 'px-4 py-2 bg-[#164E8A] hover:bg-[#12407A] text-gray-900 rounded text-sm font-medium transition-colors';

function Badge({ label, color = 'bg-gray-50 text-gray-500' }) {
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>{label}</span>;
}

function Section({ title, subtitle, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-xl bg-white">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3 text-left"
      >
        <div>
          {title && <h3 className="text-sm font-semibold text-gray-900">{title}</h3>}
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
        {open ? <ChevronDown className="w-4 h-4 text-gray-500" /> : <ChevronRight className="w-4 h-4 text-gray-500" />}
      </button>
      {open && <div className="px-5 pb-5 border-t border-gray-200">{children}</div>}
    </div>
  );
}

function KPI({ label, value, sub, color = 'text-gray-900' }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

function Spinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="w-6 h-6 text-gray-700 animate-spin" />
      <span className="ml-2 text-sm text-gray-500">Loading...</span>
    </div>
  );
}

function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div className="flex items-start gap-2 p-3 rounded-lg border border-red-500/20 bg-red-500/10 text-red-400 text-sm">
      <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
      <span>{message}</span>
    </div>
  );
}

function RefTable({ title, rows, columns }) {
  if (!rows || rows.length === 0) return null;
  return (
    <div className="mt-3">
      <p className="text-xs font-semibold text-gray-600 mb-2">{title}</p>
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-gray-700">
          <thead>
            <tr className="border-b border-gray-200">
              {columns.map(c => <th key={c.key} className="text-left py-1.5 px-2 text-gray-500 font-medium">{c.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 20).map((r, i) => (
              <tr key={i} className="border-b border-gray-100">
                {columns.map(c => <td key={c.key} className="py-1.5 px-2">{typeof c.render === 'function' ? c.render(r) : String(r[c.key] ?? '')}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const tooltipStyle = { background: '#ffffff', border: '1px solid #ffffff10', borderRadius: 8 };

/* ══════════════════════════════════════════════════════════════════════════ */
/*  Tab 1: TNFD Assessment                                                 */
/* ══════════════════════════════════════════════════════════════════════════ */
function TNFDPanel() {
  const [ref, setRef] = useState({ disclosures: null, leapPhases: null, sectors: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refLoaded, setRefLoaded] = useState(false);
  const [result, setResult] = useState(null);

  const [form, setForm] = useState({
    entity_name: '', sector: '', reporting_year: 2025,
  });
  const [disclosureScores, setDisclosureScores] = useState({});

  const loadRef = useCallback(async () => {
    if (refLoaded) return;
    setLoading(true);
    try {
      const [d, l, s] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/tnfd/ref/recommended-disclosures`),
        axios.get(`${API_BASE}/api/v1/tnfd/ref/leap-phases`),
        axios.get(`${API_BASE}/api/v1/tnfd/ref/sector-guidance`),
      ]);
      const disclosures = d.data?.disclosures || d.data || [];
      const leapPhases = l.data?.phases || l.data || [];
      const sectors = s.data?.sectors || s.data || [];
      setRef({ disclosures, leapPhases, sectors });
      const init = {};
      (Array.isArray(disclosures) ? disclosures : []).forEach(disc => { init[disc.id || disc.code] = 0; });
      setDisclosureScores(init);
      setRefLoaded(true);
    } catch (e) {
      setError(`Failed to load TNFD reference data: ${e.message}`);
    } finally { setLoading(false); }
  }, [refLoaded]);

  useEffect(() => { loadRef(); }, [loadRef]);

  const submit = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/tnfd/assess-disclosures`, {
        entity_name: form.entity_name, sector: form.sector, reporting_year: form.reporting_year,
        disclosures: disclosureScores,
        leap_data: {}, nature_dependencies: [], nature_impacts: [],
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  if (loading && !refLoaded) return <Spinner />;

  const pillarColors = { Governance: '#6366f1', Strategy: '#3b82f6', 'Risk & Impact Management': '#f59e0b', 'Metrics & Targets': '#10b981' };

  return (
    <div className="space-y-5">
      <ErrorBanner message={error} />

      <Section title="Reference Data" subtitle="TNFD recommended disclosures and LEAP phases" defaultOpen={false}>
        <RefTable title="Recommended Disclosures" rows={Array.isArray(ref.disclosures) ? ref.disclosures : []}
          columns={[
            { key: 'id', label: 'ID', render: r => r.id || r.code || '' },
            { key: 'pillar', label: 'Pillar' },
            { key: 'title', label: 'Disclosure', render: r => r.title || r.name || r.description || '' },
          ]}
        />
        <RefTable title="LEAP Phases" rows={Array.isArray(ref.leapPhases) ? ref.leapPhases : []}
          columns={[
            { key: 'phase', label: 'Phase', render: r => r.phase || r.id || '' },
            { key: 'name', label: 'Name' },
            { key: 'description', label: 'Description' },
          ]}
        />
      </Section>

      <Section title="TNFD Assessment" subtitle="Assess disclosure readiness against the 14 TNFD recommended disclosures">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3 mb-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Entity Name</label>
            <input className={inputCls} value={form.entity_name} onChange={e => setForm(p => ({ ...p, entity_name: e.target.value }))} placeholder="Acme Corp" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Sector</label>
            <select className={inputCls} value={form.sector} onChange={e => setForm(p => ({ ...p, sector: e.target.value }))}>
              <option value="">Select sector...</option>
              {(Array.isArray(ref.sectors) ? ref.sectors : []).map(s => (
                <option key={s.id || s.code || s} value={s.id || s.code || s}>{s.name || s.label || s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Reporting Year</label>
            <input type="number" className={inputCls} value={form.reporting_year} onChange={e => setForm(p => ({ ...p, reporting_year: parseInt(e.target.value) || 2025 }))} />
          </div>
        </div>

        <p className="text-xs text-gray-500 mb-2">Score each disclosure (0 = not addressed, 4 = fully disclosed):</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {Object.keys(disclosureScores).map(k => (
            <div key={k} className="flex items-center gap-2 bg-[#f5f6f8] rounded p-2 border border-gray-200">
              <Badge label={k} color="bg-gray-800/10 text-gray-600" />
              <select className="bg-[#f5f6f8] border border-gray-300 rounded px-2 py-1 text-xs text-gray-700 focus:outline-none"
                value={disclosureScores[k]} onChange={e => setDisclosureScores(p => ({ ...p, [k]: parseInt(e.target.value) }))}>
                {[0,1,2,3,4].map(v => <option key={v} value={v}>{v}</option>)}
              </select>
            </div>
          ))}
        </div>

        <div className="mt-4 flex justify-end">
          <button className={btnCls} onClick={submit} disabled={loading}>
            {loading ? 'Assessing...' : 'Run TNFD Assessment'}
          </button>
        </div>
      </Section>

      {result && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPI label="Overall Score" value={`${(result.overall_score ?? result.score ?? 0).toFixed(0)}%`} color="text-gray-600" sub="Across all pillars" />
            {Object.entries(result.pillar_scores || {}).map(([p, s]) => (
              <KPI key={p} label={p} value={`${(s ?? 0).toFixed(0)}%`} color={s >= 75 ? 'text-emerald-400' : s >= 50 ? 'text-amber-400' : 'text-red-400'} />
            ))}
          </div>

          {result.pillar_scores && (
            <Section title="LEAP Readiness Radar" defaultOpen={true}>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={Object.entries(result.pillar_scores).map(([p, s]) => ({ subject: p, score: s, fullMark: 100 }))}>
                  <PolarGrid stroke="#ffffff10" />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#ffffff60' }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 8, fill: '#ffffff40' }} />
                  <Radar name="Score" dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </Section>
          )}

          {(result.gaps || []).length > 0 && (
            <Section title={`Disclosure Gaps (${result.gaps.length})`}>
              <div className="space-y-2 mt-2">
                {result.gaps.map((g, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 border border-amber-500/20 bg-amber-500/[0.06] rounded-lg">
                    <Badge label={g.pillar || g.category || 'Gap'} color="bg-amber-500/15 text-amber-400" />
                    <span className="text-xs text-gray-600 flex-1">{g.description || g.title || g.disclosure || JSON.stringify(g)}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════ */
/*  Tab 2: CDP Scoring                                                     */
/* ══════════════════════════════════════════════════════════════════════════ */
function CDPPanel() {
  const [ref, setRef] = useState({ modules: null, bands: null, groups: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refLoaded, setRefLoaded] = useState(false);
  const [result, setResult] = useState(null);
  const [mode, setMode] = useState('climate');

  const [form, setForm] = useState({
    entity_name: '', activity_group: '', reporting_year: 2025,
  });
  const [moduleResponses, setModuleResponses] = useState({});

  const loadRef = useCallback(async () => {
    if (refLoaded) return;
    setLoading(true);
    try {
      const [m, b, g] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/cdp/ref/climate-modules`),
        axios.get(`${API_BASE}/api/v1/cdp/ref/score-bands`),
        axios.get(`${API_BASE}/api/v1/cdp/ref/activity-groups`),
      ]);
      const modules = m.data?.modules || m.data || [];
      const bands = b.data?.bands || b.data || [];
      const groups = g.data?.groups || g.data || [];
      setRef({ modules, bands, groups });
      const init = {};
      (Array.isArray(modules) ? modules : []).forEach(mod => { init[mod.id || mod.code] = 50; });
      setModuleResponses(init);
      setRefLoaded(true);
    } catch (e) {
      setError(`Failed to load CDP reference data: ${e.message}`);
    } finally { setLoading(false); }
  }, [refLoaded]);

  useEffect(() => { loadRef(); }, [loadRef]);

  const submit = async () => {
    setLoading(true); setError(''); setResult(null);
    const endpoint = mode === 'climate' ? '/assess-climate' : '/assess-water';
    try {
      const res = await axios.post(`${API_BASE}/api/v1/cdp${endpoint}`, {
        entity_name: form.entity_name, activity_group: form.activity_group,
        reporting_year: form.reporting_year, module_responses: moduleResponses,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  if (loading && !refLoaded) return <Spinner />;

  const gradeColor = (g) => {
    if (!g) return 'text-gray-500';
    if (g === 'A' || g === 'A-') return 'text-emerald-400';
    if (g.startsWith('B')) return 'text-blue-400';
    if (g.startsWith('C')) return 'text-amber-400';
    return 'text-red-400';
  };

  const levelColors = { disclosure: '#6366f1', awareness: '#3b82f6', management: '#f59e0b', leadership: '#10b981' };

  return (
    <div className="space-y-5">
      <ErrorBanner message={error} />

      <Section title="Reference Data" subtitle="CDP climate modules, scoring bands and activity groups" defaultOpen={false}>
        <RefTable title="Score Bands" rows={Array.isArray(ref.bands) ? ref.bands : []}
          columns={[
            { key: 'grade', label: 'Grade', render: r => r.grade || r.band || '' },
            { key: 'label', label: 'Label', render: r => r.label || r.name || '' },
            { key: 'range', label: 'Range', render: r => r.range || r.description || '' },
          ]}
        />
        <RefTable title="Activity Groups" rows={Array.isArray(ref.groups) ? ref.groups : []}
          columns={[
            { key: 'id', label: 'ID', render: r => r.id || r.code || '' },
            { key: 'name', label: 'Name', render: r => r.name || r.label || '' },
          ]}
        />
      </Section>

      <Section title="CDP Assessment" subtitle="Score climate (C0-C14) or water (W0-W8) questionnaire modules">
        <div className="flex gap-2 mt-3 mb-4">
          <button className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${mode === 'climate' ? 'bg-blue-100 text-blue-800' : 'bg-gray-50 text-gray-500 hover:bg-gray-50'}`}
            onClick={() => setMode('climate')}>Climate (C0-C14)</button>
          <button className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${mode === 'water' ? 'bg-blue-100 text-blue-800' : 'bg-gray-50 text-gray-500 hover:bg-gray-50'}`}
            onClick={() => setMode('water')}>Water (W0-W8)</button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Entity Name</label>
            <input className={inputCls} value={form.entity_name} onChange={e => setForm(p => ({ ...p, entity_name: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Activity Group</label>
            <select className={inputCls} value={form.activity_group} onChange={e => setForm(p => ({ ...p, activity_group: e.target.value }))}>
              <option value="">Select...</option>
              {(Array.isArray(ref.groups) ? ref.groups : []).map(g => (
                <option key={g.id || g.code || g} value={g.id || g.code || g}>{g.name || g.label || g}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Reporting Year</label>
            <input type="number" className={inputCls} value={form.reporting_year} onChange={e => setForm(p => ({ ...p, reporting_year: parseInt(e.target.value) || 2025 }))} />
          </div>
        </div>

        <p className="text-xs text-gray-500 mb-2">Module scores (0-100):</p>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {Object.keys(moduleResponses).map(k => (
            <div key={k} className="flex items-center gap-2 bg-[#f5f6f8] rounded p-2 border border-gray-200">
              <span className="text-xs text-gray-500 w-10">{k}</span>
              <input type="number" min="0" max="100" className="flex-1 bg-[#f5f6f8] border border-gray-300 rounded px-2 py-1 text-xs text-gray-700 focus:outline-none w-16"
                value={moduleResponses[k]} onChange={e => setModuleResponses(p => ({ ...p, [k]: parseInt(e.target.value) || 0 }))} />
            </div>
          ))}
        </div>

        <div className="mt-4 flex justify-end">
          <button className={btnCls} onClick={submit} disabled={loading}>
            {loading ? 'Scoring...' : `Run CDP ${mode === 'climate' ? 'Climate' : 'Water'} Assessment`}
          </button>
        </div>
      </Section>

      {result && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-400/10 rounded-xl p-5 text-center">
              <p className="text-xs text-gray-500 mb-1">Overall Grade</p>
              <p className={`text-4xl font-bold ${gradeColor(result.grade || result.letter_grade)}`}>{result.grade || result.letter_grade || 'N/A'}</p>
            </div>
            {Object.entries(result.level_scores || result.breakdown || {}).map(([lvl, sc]) => (
              <KPI key={lvl} label={lvl.charAt(0).toUpperCase() + lvl.slice(1)} value={`${(sc ?? 0).toFixed(0)}%`}
                color={sc >= 75 ? 'text-emerald-400' : sc >= 50 ? 'text-amber-400' : 'text-red-400'} />
            ))}
          </div>

          {(result.level_scores || result.breakdown) && (
            <Section title="4-Level Breakdown" defaultOpen={true}>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={Object.entries(result.level_scores || result.breakdown || {}).map(([k, v]) => ({ name: k, score: v }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#ffffff60' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#ffffff40' }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {Object.entries(result.level_scores || result.breakdown || {}).map(([k], i) => (
                      <Cell key={i} fill={levelColors[k] || '#6366f1'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}

          {(result.module_scores) && (
            <Section title="Module-Level Scores" defaultOpen={false}>
              <div className="overflow-x-auto mt-2">
                <table className="w-full text-xs text-gray-700">
                  <thead><tr className="border-b border-gray-200">
                    <th className="text-left py-1.5 px-2 text-gray-500">Module</th>
                    <th className="text-left py-1.5 px-2 text-gray-500">Score</th>
                    <th className="text-left py-1.5 px-2 text-gray-500">Band</th>
                  </tr></thead>
                  <tbody>
                    {Object.entries(result.module_scores).map(([m, s]) => (
                      <tr key={m} className="border-b border-gray-100">
                        <td className="py-1.5 px-2">{m}</td>
                        <td className="py-1.5 px-2 font-medium">{(s?.score ?? s ?? 0).toFixed(0)}%</td>
                        <td className="py-1.5 px-2">{s?.band || ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          )}
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════ */
/*  Tab 3: GRI Standards                                                   */
/* ══════════════════════════════════════════════════════════════════════════ */
function GRIPanel() {
  const [ref, setRef] = useState({ topics: [], sectors: [], sdg: [], principles: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refLoaded, setRefLoaded] = useState(false);
  const [result, setResult] = useState(null);

  const [form, setForm] = useState({
    entity_name: '', reporting_year: 2025, sector_standard: '', universal_standards_complete: true,
  });
  const [topicsReported, setTopicsReported] = useState([]);

  const loadRef = useCallback(async () => {
    if (refLoaded) return;
    setLoading(true);
    try {
      const [t, s, sdg, p] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/gri/ref/topic-standards`),
        axios.get(`${API_BASE}/api/v1/gri/ref/sector-standards`),
        axios.get(`${API_BASE}/api/v1/gri/ref/sdg-linkage`),
        axios.get(`${API_BASE}/api/v1/gri/ref/reporting-principles`),
      ]);
      setRef({
        topics: t.data?.standards || t.data || [],
        sectors: s.data?.sectors || s.data || [],
        sdg: sdg.data?.linkages || sdg.data || [],
        principles: p.data?.principles || p.data || [],
      });
      setRefLoaded(true);
    } catch (e) {
      setError(`Failed to load GRI reference data: ${e.message}`);
    } finally { setLoading(false); }
  }, [refLoaded]);

  useEffect(() => { loadRef(); }, [loadRef]);

  const toggleTopic = (id) => {
    setTopicsReported(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const submit = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/gri/content-index`, {
        entity_name: form.entity_name, reporting_year: form.reporting_year,
        topics_reported: topicsReported, sector_standard: form.sector_standard || null,
        universal_standards_complete: form.universal_standards_complete,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  if (loading && !refLoaded) return <Spinner />;

  const complianceColor = (lvl) => {
    if (lvl === 'in_accordance') return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20';
    if (lvl === 'with_reference') return 'bg-amber-500/15 text-amber-400 border-amber-500/20';
    return 'bg-red-500/15 text-red-400 border-red-500/20';
  };

  return (
    <div className="space-y-5">
      <ErrorBanner message={error} />

      <Section title="Reference Data" subtitle="GRI topic standards, sector standards and SDG linkage" defaultOpen={false}>
        <RefTable title="Topic Standards" rows={Array.isArray(ref.topics) ? ref.topics : []}
          columns={[
            { key: 'id', label: 'ID', render: r => r.id || r.standard_id || '' },
            { key: 'name', label: 'Standard Name', render: r => r.name || r.title || '' },
            { key: 'category', label: 'Category', render: r => r.category || r.group || '' },
          ]}
        />
        <RefTable title="Sector Standards" rows={Array.isArray(ref.sectors) ? ref.sectors : []}
          columns={[
            { key: 'id', label: 'ID', render: r => r.id || r.sector_id || '' },
            { key: 'name', label: 'Sector', render: r => r.name || r.sector || '' },
          ]}
        />
      </Section>

      <Section title="GRI Content Index Assessment" subtitle="Select reported topic standards to assess compliance level">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-3 mb-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Entity Name</label>
            <input className={inputCls} value={form.entity_name} onChange={e => setForm(p => ({ ...p, entity_name: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Reporting Year</label>
            <input type="number" className={inputCls} value={form.reporting_year} onChange={e => setForm(p => ({ ...p, reporting_year: parseInt(e.target.value) || 2025 }))} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Sector Standard (optional)</label>
            <select className={inputCls} value={form.sector_standard} onChange={e => setForm(p => ({ ...p, sector_standard: e.target.value }))}>
              <option value="">None</option>
              {(Array.isArray(ref.sectors) ? ref.sectors : []).map(s => (
                <option key={s.id || s.sector_id || s} value={s.id || s.sector_id || s}>{s.name || s.sector || s}</option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
              <input type="checkbox" className="accent-indigo-500" checked={form.universal_standards_complete}
                onChange={e => setForm(p => ({ ...p, universal_standards_complete: e.target.checked }))} />
              Universal Standards Complete
            </label>
          </div>
        </div>

        <p className="text-xs text-gray-500 mb-2">Select reported topic standards:</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {(Array.isArray(ref.topics) ? ref.topics : []).map(t => {
            const id = t.id || t.standard_id || t;
            const checked = topicsReported.includes(id);
            return (
              <label key={id} className={`flex items-center gap-2 p-2 rounded border cursor-pointer text-xs transition-colors ${checked ? 'border-gray-300 bg-gray-800/[0.06] text-gray-800' : 'border-gray-200 text-gray-500 hover:bg-gray-50'}`}>
                <input type="checkbox" className="accent-indigo-500" checked={checked} onChange={() => toggleTopic(id)} />
                <span>{t.name || t.title || id}</span>
              </label>
            );
          })}
        </div>

        <div className="mt-4 flex justify-end">
          <button className={btnCls} onClick={submit} disabled={loading}>
            {loading ? 'Assessing...' : 'Assess GRI Content Index'}
          </button>
        </div>
      </Section>

      {result && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className={`rounded-xl border p-5 text-center ${complianceColor(result.compliance_level || result.level)}`}>
              <p className="text-xs mb-1">Compliance Level</p>
              <p className="text-lg font-bold">{(result.compliance_level || result.level || '').replace(/_/g, ' ')}</p>
            </div>
            <KPI label="Topics Reported" value={`${topicsReported.length}/${(Array.isArray(ref.topics) ? ref.topics : []).length}`} color="text-gray-600" />
            <KPI label="Completeness" value={`${(result.completeness ?? result.topic_completeness ?? 0).toFixed(0)}%`}
              color={result.completeness >= 75 ? 'text-emerald-400' : 'text-amber-400'} />
            <KPI label="SDG Coverage" value={`${(result.sdg_alignment ?? result.sdg_coverage ?? 0).toFixed(0)}%`} color="text-blue-300" />
          </div>

          {(result.topic_scores || result.topic_completeness_detail) && (
            <Section title="Topic Completeness" defaultOpen={true}>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={Object.entries(result.topic_scores || result.topic_completeness_detail || {}).map(([k, v]) => ({ name: k, score: typeof v === 'number' ? v : v?.score ?? 0 }))} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 9, fill: '#ffffff40' }} />
                  <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 9, fill: '#ffffff60' }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {Object.entries(result.topic_scores || result.topic_completeness_detail || {}).map(([, v], i) => {
                      const s = typeof v === 'number' ? v : v?.score ?? 0;
                      return <Cell key={i} fill={s >= 75 ? '#10b981' : s >= 50 ? '#f59e0b' : '#ef4444'} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}

          {(result.gaps || []).length > 0 && (
            <Section title={`Gaps (${result.gaps.length})`}>
              <div className="space-y-2 mt-2">
                {result.gaps.map((g, i) => (
                  <div key={i} className="flex items-start gap-2 p-2 border border-amber-500/20 bg-amber-500/[0.06] rounded-lg">
                    <Badge label={g.standard || g.topic || 'Missing'} color="bg-amber-500/15 text-amber-400" />
                    <span className="text-xs text-gray-600 flex-1">{g.description || g.message || JSON.stringify(g)}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════ */
/*  Tab 4: SASB Industry                                                   */
/* ══════════════════════════════════════════════════════════════════════════ */
function SASBPanel() {
  const [ref, setRef] = useState({ sectors: [], industryCodes: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refLoaded, setRefLoaded] = useState(false);
  const [result, setResult] = useState(null);

  const [form, setForm] = useState({
    entity_name: '', industry_code: '', reporting_year: 2025,
  });
  const [metricsReported, setMetricsReported] = useState('');
  const [metricValues, setMetricValues] = useState('');

  const loadRef = useCallback(async () => {
    if (refLoaded) return;
    setLoading(true);
    try {
      const [s, ic] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/sasb/ref/sics-sectors`),
        axios.get(`${API_BASE}/api/v1/sasb/ref/industry-codes`),
      ]);
      setRef({
        sectors: s.data?.sectors || s.data || [],
        industryCodes: ic.data?.codes || ic.data || [],
      });
      setRefLoaded(true);
    } catch (e) {
      setError(`Failed to load SASB reference data: ${e.message}`);
    } finally { setLoading(false); }
  }, [refLoaded]);

  useEffect(() => { loadRef(); }, [loadRef]);

  const submit = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      let parsedMetrics = [];
      try { parsedMetrics = metricsReported ? JSON.parse(metricsReported) : []; } catch { parsedMetrics = metricsReported.split(',').map(s => s.trim()).filter(Boolean); }
      let parsedValues = {};
      try { parsedValues = metricValues ? JSON.parse(metricValues) : {}; } catch { parsedValues = {}; }

      const res = await axios.post(`${API_BASE}/api/v1/sasb/assess-industry`, {
        entity_name: form.entity_name, industry_code: form.industry_code,
        reporting_year: form.reporting_year, metrics_reported: parsedMetrics,
        metric_values: parsedValues,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  if (loading && !refLoaded) return <Spinner />;

  return (
    <div className="space-y-5">
      <ErrorBanner message={error} />

      <Section title="Reference Data" subtitle="SICS sectors and industry classification codes" defaultOpen={false}>
        <RefTable title="SICS Sectors" rows={Array.isArray(ref.sectors) ? ref.sectors : []}
          columns={[
            { key: 'code', label: 'Code', render: r => r.code || r.id || '' },
            { key: 'name', label: 'Sector', render: r => r.name || r.sector || '' },
            { key: 'industries', label: 'Industries', render: r => r.industry_count || (r.industries || []).length || '' },
          ]}
        />
        <RefTable title="Industry Codes" rows={Array.isArray(ref.industryCodes) ? ref.industryCodes.slice(0, 30) : []}
          columns={[
            { key: 'code', label: 'SICS Code', render: r => r.code || r.id || '' },
            { key: 'name', label: 'Industry', render: r => r.name || r.industry || '' },
            { key: 'sector', label: 'Sector', render: r => r.sector || '' },
          ]}
        />
      </Section>

      <Section title="SASB Industry Assessment" subtitle="Assess metric completeness and materiality coverage for your industry">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3 mb-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Entity Name</label>
            <input className={inputCls} value={form.entity_name} onChange={e => setForm(p => ({ ...p, entity_name: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Industry Code</label>
            <select className={inputCls} value={form.industry_code} onChange={e => setForm(p => ({ ...p, industry_code: e.target.value }))}>
              <option value="">Select industry...</option>
              {(Array.isArray(ref.industryCodes) ? ref.industryCodes : []).map(ic => (
                <option key={ic.code || ic.id || ic} value={ic.code || ic.id || ic}>{ic.name || ic.industry || ic} ({ic.code || ic.id || ''})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Reporting Year</label>
            <input type="number" className={inputCls} value={form.reporting_year} onChange={e => setForm(p => ({ ...p, reporting_year: parseInt(e.target.value) || 2025 }))} />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Metrics Reported (JSON array or comma-separated IDs)</label>
            <textarea className={`${inputCls} h-20`} value={metricsReported}
              onChange={e => setMetricsReported(e.target.value)}
              placeholder='["IF-EN-110a.1","IF-EN-110a.2"] or IF-EN-110a.1, IF-EN-110a.2' />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Metric Values (JSON object)</label>
            <textarea className={`${inputCls} h-20`} value={metricValues}
              onChange={e => setMetricValues(e.target.value)}
              placeholder='{"IF-EN-110a.1": 12500, "IF-EN-110a.2": 0.85}' />
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <button className={btnCls} onClick={submit} disabled={loading}>
            {loading ? 'Assessing...' : 'Run SASB Assessment'}
          </button>
        </div>
      </Section>

      {result && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPI label="Completeness" value={`${(result.completeness ?? result.completeness_pct ?? 0).toFixed(0)}%`}
              color={result.completeness >= 75 ? 'text-emerald-400' : 'text-amber-400'} />
            <KPI label="Materiality Coverage" value={`${(result.materiality_coverage ?? result.materiality_pct ?? 0).toFixed(0)}%`}
              color={result.materiality_coverage >= 80 ? 'text-emerald-400' : 'text-amber-400'} />
            <KPI label="Metrics Reported" value={result.metrics_reported_count ?? result.reported ?? 0} color="text-gray-600"
              sub={`of ${result.total_metrics ?? result.required ?? '?'} required`} />
            <KPI label="Industry" value={form.industry_code || 'N/A'} color="text-gray-700" sub={result.industry_name || ''} />
          </div>

          {(result.sector_comparison || result.comparison) && (
            <Section title="Sector Comparison" defaultOpen={true}>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={result.sector_comparison || result.comparison || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis dataKey="entity" tick={{ fontSize: 9, fill: '#ffffff60' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#ffffff40' }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="completeness" name="Completeness %" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}

          {(result.cross_framework || result.framework_references) && (
            <Section title="Cross-Framework References" defaultOpen={false}>
              <div className="overflow-x-auto mt-2">
                <table className="w-full text-xs text-gray-700">
                  <thead><tr className="border-b border-gray-200">
                    <th className="text-left py-1.5 px-2 text-gray-500">SASB Metric</th>
                    <th className="text-left py-1.5 px-2 text-gray-500">Framework</th>
                    <th className="text-left py-1.5 px-2 text-gray-500">Reference</th>
                  </tr></thead>
                  <tbody>
                    {(result.cross_framework || result.framework_references || []).map((r, i) => (
                      <tr key={i} className="border-b border-gray-100">
                        <td className="py-1.5 px-2">{r.sasb_metric || r.metric || ''}</td>
                        <td className="py-1.5 px-2">{r.framework || ''}</td>
                        <td className="py-1.5 px-2">{r.reference || r.mapping || ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          )}
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════ */
/*  Tab 5: SEC Climate                                                     */
/* ══════════════════════════════════════════════════════════════════════════ */
function SECPanel() {
  const [ref, setRef] = useState({ filerCategories: [], regSK: [], regSX: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [refLoaded, setRefLoaded] = useState(false);
  const [result, setResult] = useState(null);

  const [form, setForm] = useState({
    entity_name: '', filer_category: 'LAF', fiscal_year_end: '2025-12-31',
    total_revenue_usd: '', ghg_scope1: '', ghg_scope2: '', ghg_scope3: '',
    attestation_provider: '',
  });
  const [regSKResponses, setRegSKResponses] = useState({});
  const [regSXResponses, setRegSXResponses] = useState({});

  const loadRef = useCallback(async () => {
    if (refLoaded) return;
    setLoading(true);
    try {
      const [fc, sk, sx] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/sec-climate/ref/filer-categories`),
        axios.get(`${API_BASE}/api/v1/sec-climate/ref/reg-sk-items`),
        axios.get(`${API_BASE}/api/v1/sec-climate/ref/reg-sx-items`),
      ]);
      const filerCategories = fc.data?.categories || fc.data || [];
      const regSK = sk.data?.items || sk.data || [];
      const regSX = sx.data?.items || sx.data || [];
      setRef({ filerCategories, regSK, regSX });

      const skInit = {};
      (Array.isArray(regSK) ? regSK : []).forEach(item => { skInit[item.id || item.item_id || item.code] = { maturity: 0, notes: '' }; });
      setRegSKResponses(skInit);

      const sxInit = {};
      (Array.isArray(regSX) ? regSX : []).forEach(item => { sxInit[item.id || item.item_id || item.code] = { maturity: 0, notes: '' }; });
      setRegSXResponses(sxInit);

      setRefLoaded(true);
    } catch (e) {
      setError(`Failed to load SEC reference data: ${e.message}`);
    } finally { setLoading(false); }
  }, [refLoaded]);

  useEffect(() => { loadRef(); }, [loadRef]);

  const submit = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/sec-climate/filer-assessment`, {
        entity_name: form.entity_name, filer_category: form.filer_category,
        fiscal_year_end: form.fiscal_year_end,
        total_revenue_usd: parseFloat(form.total_revenue_usd) || 0,
        ghg_scope1: parseFloat(form.ghg_scope1) || 0,
        ghg_scope2: parseFloat(form.ghg_scope2) || 0,
        ghg_scope3: parseFloat(form.ghg_scope3) || 0,
        attestation_provider: form.attestation_provider,
        reg_sk_responses: regSKResponses,
        reg_sx_responses: regSXResponses,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  };

  if (loading && !refLoaded) return <Spinner />;

  const filerOpts = Array.isArray(ref.filerCategories) && ref.filerCategories.length > 0
    ? ref.filerCategories
    : [
        { code: 'LAF', name: 'Large Accelerated Filer' },
        { code: 'AF', name: 'Accelerated Filer' },
        { code: 'NAF', name: 'Non-Accelerated Filer' },
        { code: 'SRC', name: 'Smaller Reporting Company' },
        { code: 'EGC', name: 'Emerging Growth Company' },
      ];

  return (
    <div className="space-y-5">
      <ErrorBanner message={error} />

      <Section title="Reference Data" subtitle="SEC filer categories, Reg S-K and S-X items" defaultOpen={false}>
        <RefTable title="Filer Categories" rows={filerOpts}
          columns={[
            { key: 'code', label: 'Code', render: r => r.code || r.id || '' },
            { key: 'name', label: 'Category', render: r => r.name || r.label || '' },
          ]}
        />
        <RefTable title="Reg S-K Items" rows={Array.isArray(ref.regSK) ? ref.regSK : []}
          columns={[
            { key: 'id', label: 'Item', render: r => r.id || r.item_id || r.code || '' },
            { key: 'title', label: 'Title', render: r => r.title || r.name || '' },
            { key: 'description', label: 'Description', render: r => (r.description || '').slice(0, 120) },
          ]}
        />
        <RefTable title="Reg S-X Items" rows={Array.isArray(ref.regSX) ? ref.regSX : []}
          columns={[
            { key: 'id', label: 'Item', render: r => r.id || r.item_id || r.code || '' },
            { key: 'title', label: 'Title', render: r => r.title || r.name || '' },
          ]}
        />
      </Section>

      <Section title="SEC Climate Filer Assessment" subtitle="Reg S-K Items 1501-1505 and Reg S-X Art. 14-02 compliance scoring">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3 mb-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Entity Name</label>
            <input className={inputCls} value={form.entity_name} onChange={e => setForm(p => ({ ...p, entity_name: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Filer Category</label>
            <select className={inputCls} value={form.filer_category} onChange={e => setForm(p => ({ ...p, filer_category: e.target.value }))}>
              {filerOpts.map(f => (
                <option key={f.code || f.id} value={f.code || f.id}>{f.name || f.label} ({f.code || f.id})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Fiscal Year End</label>
            <input type="date" className={inputCls} value={form.fiscal_year_end} onChange={e => setForm(p => ({ ...p, fiscal_year_end: e.target.value }))} />
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Total Revenue (USD)</label>
            <input type="number" className={inputCls} value={form.total_revenue_usd} onChange={e => setForm(p => ({ ...p, total_revenue_usd: e.target.value }))} placeholder="e.g. 500000000" />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">GHG Scope 1 (tCO2e)</label>
            <input type="number" className={inputCls} value={form.ghg_scope1} onChange={e => setForm(p => ({ ...p, ghg_scope1: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">GHG Scope 2 (tCO2e)</label>
            <input type="number" className={inputCls} value={form.ghg_scope2} onChange={e => setForm(p => ({ ...p, ghg_scope2: e.target.value }))} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">GHG Scope 3 (tCO2e)</label>
            <input type="number" className={inputCls} value={form.ghg_scope3} onChange={e => setForm(p => ({ ...p, ghg_scope3: e.target.value }))} />
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-xs text-gray-500 mb-1">Attestation Provider (if any)</label>
          <input className={inputCls} value={form.attestation_provider} onChange={e => setForm(p => ({ ...p, attestation_provider: e.target.value }))} placeholder="e.g. Deloitte, PwC" />
        </div>

        {Object.keys(regSKResponses).length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-semibold text-gray-600 mb-2">Reg S-K Item Readiness (0-4):</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {Object.keys(regSKResponses).map(k => {
                const item = (Array.isArray(ref.regSK) ? ref.regSK : []).find(i => (i.id || i.item_id || i.code) === k);
                return (
                  <div key={k} className="flex items-center gap-2 bg-[#f5f6f8] rounded p-2 border border-gray-200">
                    <Badge label={k} color="bg-blue-500/10 text-blue-300" />
                    <span className="text-xs text-gray-500 flex-1 truncate">{item?.title || item?.name || ''}</span>
                    <select className="bg-[#f5f6f8] border border-gray-300 rounded px-2 py-1 text-xs text-gray-700 focus:outline-none"
                      value={regSKResponses[k]?.maturity ?? 0}
                      onChange={e => setRegSKResponses(p => ({ ...p, [k]: { ...p[k], maturity: parseInt(e.target.value) } }))}>
                      {[0,1,2,3,4].map(v => <option key={v} value={v}>{v}</option>)}
                    </select>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {Object.keys(regSXResponses).length > 0 && (
          <div className="mb-4">
            <p className="text-xs font-semibold text-gray-600 mb-2">Reg S-X Item Readiness (0-4):</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {Object.keys(regSXResponses).map(k => {
                const item = (Array.isArray(ref.regSX) ? ref.regSX : []).find(i => (i.id || i.item_id || i.code) === k);
                return (
                  <div key={k} className="flex items-center gap-2 bg-[#f5f6f8] rounded p-2 border border-gray-200">
                    <Badge label={k} color="bg-purple-500/10 text-purple-300" />
                    <span className="text-xs text-gray-500 flex-1 truncate">{item?.title || item?.name || ''}</span>
                    <select className="bg-[#f5f6f8] border border-gray-300 rounded px-2 py-1 text-xs text-gray-700 focus:outline-none"
                      value={regSXResponses[k]?.maturity ?? 0}
                      onChange={e => setRegSXResponses(p => ({ ...p, [k]: { ...p[k], maturity: parseInt(e.target.value) } }))}>
                      {[0,1,2,3,4].map(v => <option key={v} value={v}>{v}</option>)}
                    </select>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <button className={btnCls} onClick={submit} disabled={loading}>
            {loading ? 'Assessing...' : 'Run SEC Filer Assessment'}
          </button>
        </div>
      </Section>

      {result && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className={`rounded-xl border p-5 text-center ${(result.compliance_score ?? result.score ?? 0) >= 75 ? 'bg-emerald-500/10 border-emerald-500/20' : (result.compliance_score ?? result.score ?? 0) >= 50 ? 'bg-amber-500/10 border-amber-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
              <p className="text-xs text-gray-500 mb-1">Compliance Score</p>
              <p className={`text-3xl font-bold ${(result.compliance_score ?? result.score ?? 0) >= 75 ? 'text-emerald-400' : (result.compliance_score ?? result.score ?? 0) >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                {(result.compliance_score ?? result.score ?? 0).toFixed(0)}%
              </p>
            </div>
            <KPI label="Filer Category" value={form.filer_category} color="text-gray-700" sub={result.phase_in_deadline || ''} />
            <KPI label="Attestation" value={result.attestation_readiness || result.attestation_status || 'N/A'} color="text-blue-300" />
            <KPI label="Safe Harbor" value={result.safe_harbor_applicable ? 'Applicable' : 'Limited'} color="text-gray-800" />
            <KPI label="Phase-In" value={result.phase_in_year || result.effective_year || 'TBD'} color="text-gray-700" sub="Effective compliance year" />
          </div>

          {(result.item_scores || result.reg_sk_scores) && (
            <Section title="Reg S-K Item Scores" defaultOpen={true}>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={Object.entries(result.item_scores || result.reg_sk_scores || {}).map(([k, v]) => ({ name: k, score: typeof v === 'number' ? v : v?.score ?? 0 }))} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={false} />
                  <XAxis type="number" domain={[0, 4]} ticks={[0,1,2,3,4]} tick={{ fontSize: 9, fill: '#ffffff40' }} />
                  <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 9, fill: '#ffffff60' }} />
                  <Tooltip contentStyle={tooltipStyle} formatter={v => [`${v}/4`]} />
                  <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                    {Object.entries(result.item_scores || result.reg_sk_scores || {}).map(([, v], i) => {
                      const s = typeof v === 'number' ? v : v?.score ?? 0;
                      return <Cell key={i} fill={s >= 3 ? '#10b981' : s >= 2 ? '#f59e0b' : '#ef4444'} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
          )}

          {result.phase_in_timeline && (
            <Section title="Phase-In Timeline" defaultOpen={false}>
              <div className="space-y-2 mt-2">
                {(Array.isArray(result.phase_in_timeline) ? result.phase_in_timeline : Object.entries(result.phase_in_timeline).map(([k, v]) => ({ year: k, ...v }))).map((item, i) => (
                  <div key={i} className="flex items-center gap-3 p-2 bg-[#f5f6f8] rounded border border-gray-200">
                    <Badge label={item.year || item.date || ''} color="bg-gray-800/10 text-gray-600" />
                    <span className="text-xs text-gray-600">{item.description || item.requirement || JSON.stringify(item)}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════ */
/*  Main Page                                                              */
/* ══════════════════════════════════════════════════════════════════════════ */
const TABS = [
  { id: 'tnfd',  label: 'TNFD',          Icon: Leaf,      color: 'text-emerald-400' },
  { id: 'cdp',   label: 'CDP',           Icon: BarChart3, color: 'text-blue-400' },
  { id: 'gri',   label: 'GRI Standards', Icon: FileText,  color: 'text-purple-400' },
  { id: 'sasb',  label: 'SASB Industry', Icon: Building2, color: 'text-gray-700' },
  { id: 'sec',   label: 'SEC Climate',   Icon: Scale,     color: 'text-amber-400' },
];

export default function DisclosureFrameworksPage() {
  const [activeTab, setActiveTab] = useState('tnfd');

  return (
    <div className="min-h-screen bg-white text-gray-900 p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Disclosure Frameworks</h1>
        <p className="text-sm text-gray-500 mt-1">
          Assess compliance across TNFD, CDP, GRI, SASB and SEC climate disclosure frameworks
        </p>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 p-1 bg-white rounded-xl border border-gray-200 overflow-x-auto">
        {TABS.map(tab => {
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                active
                  ? 'bg-gray-200 border border-gray-300 text-gray-900'
                  : 'text-gray-500 hover:text-gray-600 hover:bg-gray-50'
              }`}
            >
              <tab.Icon className={`w-4 h-4 ${active ? tab.color : ''}`} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="min-h-[500px]">
        {activeTab === 'tnfd' && <TNFDPanel />}
        {activeTab === 'cdp'  && <CDPPanel />}
        {activeTab === 'gri'  && <GRIPanel />}
        {activeTab === 'sasb' && <SASBPanel />}
        {activeTab === 'sec'  && <SECPanel />}
      </div>
    </div>
  );
}
