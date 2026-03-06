/**
 * MASPanel — MAS ERM / Notice 637 / Singapore Green Finance Taxonomy / SLGS.
 * Embedded in RegulatoryPage.
 * Sprint 5 — WHOOP for Sustainability platform.
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const STATUS_OPTIONS = ['Compliant', 'Partial', 'Not Started'];

const STATUS_COLOURS = {
  Compliant: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  Partial: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30' },
  'Not Started': { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20' },
  'Not Assessed': { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/20' },
};

const RAG_COLOURS = {
  GREEN: { text: 'text-emerald-400', bg: 'bg-emerald-500/20', border: 'border-emerald-500/30' },
  AMBER: { text: 'text-amber-400', bg: 'bg-amber-500/20', border: 'border-amber-500/30' },
  RED: { text: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500/30' },
};

const StatusBadge = ({ status }) => {
  const c = STATUS_COLOURS[status] || STATUS_COLOURS['Not Assessed'];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${c.bg} ${c.text} ${c.border}`}>
      {status}
    </span>
  );
};

const SectionTitle = ({ children }) => (
  <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">{children}</h3>
);

// ─────────────────────────────────────────────────────────
// Sub-tab: ERM Self-Assessment
// ─────────────────────────────────────────────────────────
const ERMTab = () => {
  const [principles, setPrinciples] = useState([]);
  const [responses, setResponses] = useState({});
  const [assessmentResult, setAssessmentResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios.get(`${API}/api/v1/mas-regulatory/erm/principles`)
      .then(res => {
        setPrinciples(res.data.principles || []);
        const initial = {};
        (res.data.principles || []).forEach(p => { initial[p.id] = 'Not Started'; });
        setResponses(initial);
      })
      .catch(() => {});
  }, []);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const resp = await axios.post(`${API}/api/v1/mas-regulatory/erm/self-assessment`, { responses });
      setAssessmentResult(resp.data);
    } catch (err) {
      console.error(err);
    } finally { setLoading(false); }
  };

  const ragInfo = assessmentResult ? (RAG_COLOURS[assessmentResult.rag] || RAG_COLOURS.RED) : null;

  return (
    <div className="space-y-5">
      <p className="text-sm text-gray-400">
        Rate your compliance against MAS Guidelines on Environmental Risk Management (Banks) 2022 —
        covering board oversight, risk policies, scenario analysis, and TCFD disclosure.
      </p>

      {/* Assessment result */}
      {assessmentResult && (
        <div className={`rounded-lg p-4 border ${ragInfo?.border} ${ragInfo?.bg}`}>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-gray-400 mb-1">Overall ERM Compliance Score</div>
              <div className="text-3xl font-bold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
                {assessmentResult.score_pct}%
              </div>
              <div className={`text-sm font-medium mt-1 ${ragInfo?.text}`}>{assessmentResult.status}</div>
            </div>
            <div className="text-right text-xs text-gray-400 space-y-1">
              <div><span className="text-emerald-400">{assessmentResult.compliant_count}</span> Compliant</div>
              <div><span className="text-amber-400">{assessmentResult.partial_count}</span> Partial</div>
              <div><span className="text-red-400">{assessmentResult.not_started_count}</span> Not Started</div>
            </div>
          </div>
          {assessmentResult.gaps?.length > 0 && (
            <div className="mt-3 pt-3 border-t border-white/10">
              <div className="text-xs text-gray-400 mb-2">Priority Gaps:</div>
              {assessmentResult.gaps.map(g => (
                <div key={g.id} className="text-xs text-red-300 mb-1">• {g.title}: {g.description}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Principles checklist */}
      <div className="space-y-3">
        {principles.map(p => (
          <div key={p.id} className="rounded-lg border border-white/10 bg-white/3 p-3">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="text-sm font-medium text-white">{p.section}. {p.title}</div>
                <div className="text-xs text-gray-500 mt-0.5">{p.description}</div>
              </div>
              <select
                value={responses[p.id] || 'Not Started'}
                onChange={e => setResponses(prev => ({ ...prev, [p.id]: e.target.value }))}
                className={`text-xs rounded px-2 py-1 border focus:outline-none flex-shrink-0
                  ${STATUS_COLOURS[responses[p.id] || 'Not Started'].bg}
                  ${STATUS_COLOURS[responses[p.id] || 'Not Started'].text}
                  ${STATUS_COLOURS[responses[p.id] || 'Not Started'].border}
                  bg-transparent`}
              >
                {STATUS_OPTIONS.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
          </div>
        ))}
      </div>

      <button onClick={handleSubmit} disabled={loading}
        className="w-full py-3 rounded-lg text-sm font-semibold text-white disabled:opacity-50"
        style={{ background: 'linear-gradient(135deg, hsl(199,89%,40%), hsl(199,89%,30%))' }}
        data-testid="mas-erm-submit-btn">
        {loading ? 'Calculating...' : 'Calculate Compliance Score'}
      </button>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// Sub-tab: Notice 637 Pillar 2
// ─────────────────────────────────────────────────────────
const Notice637Tab = () => {
  const [items, setItems] = useState([]);

  useEffect(() => {
    axios.get(`${API}/api/v1/mas-regulatory/notice-637/requirements`)
      .then(res => setItems(res.data.items || []))
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-400">
        MAS Notice 637 — Pillar 2 environmental risk requirements for banks operating in Singapore.
        These form part of the ICAAP / ILAAP and annual SREP assessment.
      </p>
      {items.map(item => (
        <div key={item.id} className="rounded-lg border border-white/10 bg-white/3 p-4">
          <div className="flex items-start justify-between gap-3 mb-2">
            <span className="text-xs bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded px-2 py-0.5">{item.pillar}</span>
          </div>
          <div className="text-sm font-medium text-white">{item.item}</div>
          <div className="text-xs text-gray-400 mt-1">{item.requirement}</div>
        </div>
      ))}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// Sub-tab: SGT Taxonomy
// ─────────────────────────────────────────────────────────
const SGTTab = () => {
  const [sectors, setSectors] = useState([]);
  const [check, setCheck] = useState({ sector: 'Energy', activity: '', entity_name: '' });
  const [checkResult, setCheckResult] = useState(null);
  const [expandedSectors, setExpandedSectors] = useState(new Set(['Energy']));

  useEffect(() => {
    axios.get(`${API}/api/v1/mas-regulatory/sgt/sectors`)
      .then(res => setSectors(res.data.sectors || []))
      .catch(() => {});
  }, []);

  const handleCheck = async () => {
    try {
      const resp = await axios.post(`${API}/api/v1/mas-regulatory/sgt/check-activity`, check);
      setCheckResult(resp.data);
    } catch (err) {
      setCheckResult({ qualifies: false, status: err.response?.data?.detail || 'Error', eligible_activities_in_sector: [] });
    }
  };

  const toggleSector = (s) => {
    setExpandedSectors(prev => {
      const n = new Set(prev);
      n.has(s) ? n.delete(s) : n.add(s);
      return n;
    });
  };

  return (
    <div className="space-y-5">
      <p className="text-sm text-gray-400">
        Singapore Green and Transition Taxonomy v2.0 (2024) — eligible activities for green/transition finance.
      </p>

      {/* Activity checker */}
      <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-4">
        <SectionTitle>Activity Eligibility Check</SectionTitle>
        <div className="grid grid-cols-3 gap-3 mb-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Sector</label>
            <select value={check.sector} onChange={e => setCheck(p => ({ ...p, sector: e.target.value }))}
              className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60">
              {sectors.map(s => <option key={s.sector} value={s.sector}>{s.sector}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Activity</label>
            <input type="text" value={check.activity} onChange={e => setCheck(p => ({ ...p, activity: e.target.value }))}
              placeholder="e.g. Solar PV generation"
              className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Entity Name</label>
            <input type="text" value={check.entity_name} onChange={e => setCheck(p => ({ ...p, entity_name: e.target.value }))}
              placeholder="Company name"
              className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60" />
          </div>
        </div>
        <button onClick={handleCheck}
          className="px-4 py-2 rounded text-sm font-medium text-white border border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20"
          data-testid="sgt-check-btn">
          Check Eligibility
        </button>
        {checkResult && (
          <div className={`mt-3 rounded p-3 text-sm border ${checkResult.qualifies ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-red-500/10 border-red-500/30 text-red-400'}`}>
            {checkResult.status}
          </div>
        )}
      </div>

      {/* Sectors accordion */}
      <div className="space-y-2">
        {sectors.map(s => (
          <div key={s.sector} className="rounded-lg border border-white/10 overflow-hidden">
            <button
              className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-white hover:bg-white/3 text-left"
              onClick={() => toggleSector(s.sector)}>
              {s.sector}
              <span className="text-gray-500">{expandedSectors.has(s.sector) ? '▲' : '▼'}</span>
            </button>
            {expandedSectors.has(s.sector) && (
              <div className="px-4 pb-3 flex flex-wrap gap-1.5">
                {s.activities.map(a => (
                  <span key={a} className="inline-block bg-white/5 text-gray-300 border border-white/10 rounded px-2 py-0.5 text-xs">{a}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// Sub-tab: SLGS Application Tracker
// ─────────────────────────────────────────────────────────
const SLGSTab = () => {
  const [stages, setStages] = useState([]);
  const [form, setForm] = useState({
    entity_name: '',
    current_stage: 1,
    tcfd_report_year: '',
    financed_emissions_baseline_year: '',
    net_zero_commitment_year: '',
    notes: '',
  });
  const [trackResult, setTrackResult] = useState(null);

  useEffect(() => {
    axios.get(`${API}/api/v1/mas-regulatory/slgs/stages`)
      .then(res => setStages(res.data.stages || []))
      .catch(() => {});
  }, []);

  const handleTrack = async () => {
    try {
      const resp = await axios.post(`${API}/api/v1/mas-regulatory/slgs/application`, {
        ...form,
        current_stage: parseInt(form.current_stage),
        tcfd_report_year: form.tcfd_report_year ? parseInt(form.tcfd_report_year) : null,
        financed_emissions_baseline_year: form.financed_emissions_baseline_year ? parseInt(form.financed_emissions_baseline_year) : null,
        net_zero_commitment_year: form.net_zero_commitment_year ? parseInt(form.net_zero_commitment_year) : null,
      });
      setTrackResult(resp.data);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-5">
      <p className="text-sm text-gray-400">
        Singapore Green Lane for Sustainability (SLGS) — MAS incentive programme for FIs demonstrating strong climate action.
      </p>

      {/* Stages timeline */}
      <div>
        <SectionTitle>SLGS Application Journey</SectionTitle>
        <div className="flex items-start gap-0 overflow-x-auto pb-2">
          {stages.map((s, i) => (
            <div key={s.stage} className="flex items-start" style={{ minWidth: '140px' }}>
              <div className="flex flex-col items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 ${
                  form.current_stage >= s.stage ? 'bg-cyan-500/30 border-cyan-400 text-cyan-400' : 'bg-white/5 border-white/20 text-gray-500'
                }`}>
                  {s.stage}
                </div>
                {i < stages.length - 1 && (
                  <div className={`w-full h-0.5 mt-4 ${form.current_stage > s.stage ? 'bg-cyan-500/40' : 'bg-white/10'}`} style={{ width: '100px' }} />
                )}
              </div>
              <div className="ml-2 mt-1">
                <div className="text-xs font-medium text-white">{s.name}</div>
                <div className="text-xs text-gray-500 mt-0.5 pr-4">{s.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tracker form */}
      <div className="grid grid-cols-2 gap-3">
        <div className="col-span-2">
          <label className="block text-xs text-gray-400 mb-1">Entity Name</label>
          <input type="text" value={form.entity_name} onChange={e => setForm(p => ({ ...p, entity_name: e.target.value }))}
            placeholder="Your FI name"
            className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60" />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Current Stage</label>
          <select value={form.current_stage} onChange={e => setForm(p => ({ ...p, current_stage: e.target.value }))}
            className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60">
            {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>Stage {n}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">TCFD Report Year</label>
          <input type="number" value={form.tcfd_report_year} onChange={e => setForm(p => ({ ...p, tcfd_report_year: e.target.value }))}
            placeholder="e.g. 2023" min={2019} max={2030}
            className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60"
            style={{ fontFamily: 'IBM Plex Mono, monospace' }} />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Financed Emissions Baseline Year</label>
          <input type="number" value={form.financed_emissions_baseline_year} onChange={e => setForm(p => ({ ...p, financed_emissions_baseline_year: e.target.value }))}
            placeholder="e.g. 2022" min={2018} max={2025}
            className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60"
            style={{ fontFamily: 'IBM Plex Mono, monospace' }} />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Net-Zero Commitment Year</label>
          <input type="number" value={form.net_zero_commitment_year} onChange={e => setForm(p => ({ ...p, net_zero_commitment_year: e.target.value }))}
            placeholder="e.g. 2050" min={2035} max={2060}
            className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60"
            style={{ fontFamily: 'IBM Plex Mono, monospace' }} />
        </div>
      </div>

      <button onClick={handleTrack}
        className="w-full py-3 rounded-lg text-sm font-semibold text-white"
        style={{ background: 'linear-gradient(135deg, hsl(199,89%,40%), hsl(199,89%,30%))' }}
        data-testid="slgs-track-btn">
        Track Application Progress
      </button>

      {trackResult && (
        <div className="rounded-lg border border-white/10 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-white">{trackResult.entity_name || 'Application Status'}</div>
            <div className="text-sm font-bold text-cyan-400" style={{ fontFamily: 'IBM Plex Mono' }}>{trackResult.completion_pct}% complete</div>
          </div>
          <div className="w-full bg-white/10 rounded-full h-2">
            <div className="bg-cyan-500 h-2 rounded-full transition-all" style={{ width: `${trackResult.completion_pct}%` }} />
          </div>
          {trackResult.next_stage && (
            <div className="text-xs text-gray-400">
              Next: <span className="text-white font-medium">Stage {trackResult.next_stage.stage} — {trackResult.next_stage.name}</span>
            </div>
          )}
          {trackResult.outstanding_checklist?.length > 0 && (
            <div>
              <div className="text-xs text-amber-400 font-medium mb-1">Outstanding Actions:</div>
              {trackResult.outstanding_checklist.map((item, i) => (
                <div key={i} className="text-xs text-gray-400 mb-0.5">• {item}</div>
              ))}
            </div>
          )}
          {trackResult.on_track && (
            <div className="text-xs text-emerald-400">All prerequisites met — ready to advance to next stage.</div>
          )}
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// Main Panel
// ─────────────────────────────────────────────────────────
const MAS_TABS = [
  { id: 'erm', label: 'ERM Guidelines', subtitle: 'Self-assessment' },
  { id: 'notice637', label: 'Notice 637', subtitle: 'Pillar 2' },
  { id: 'sgt', label: 'Green Taxonomy', subtitle: 'SGT v2.0' },
  { id: 'slgs', label: 'SLGS', subtitle: 'Application Tracker' },
];

export default function MASPanel() {
  const [activeTab, setActiveTab] = useState('erm');

  const tabStatus = {
    erm: 'Not Assessed',
    notice637: 'Not Assessed',
    sgt: 'Not Assessed',
    slgs: 'Not Assessed',
  };

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>MAS Regulatory</h2>
        <p className="text-sm text-gray-400 mt-0.5">
          Monetary Authority of Singapore — ERM Guidelines, Notice 637, Singapore Green Taxonomy, SLGS programme
        </p>
      </div>

      {/* Sub-tab navigation with status badges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {MAS_TABS.map(tab => {
          const c = STATUS_COLOURS[tabStatus[tab.id]] || STATUS_COLOURS['Not Assessed'];
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-lg p-3 text-left border transition-all ${
                activeTab === tab.id
                  ? 'border-cyan-500/50 bg-cyan-500/10'
                  : 'border-white/10 bg-white/3 hover:border-white/20'
              }`}
              data-testid={`mas-tab-${tab.id}`}
            >
              <div className="text-sm font-medium text-white">{tab.label}</div>
              <div className="text-xs text-gray-500 mt-0.5">{tab.subtitle}</div>
              <div className="mt-1.5">
                <StatusBadge status={tabStatus[tab.id]} />
              </div>
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="rounded-xl border border-white/10 p-5" style={{ background: 'hsl(222,35%,9%)' }}>
        {activeTab === 'erm' && <ERMTab />}
        {activeTab === 'notice637' && <Notice637Tab />}
        {activeTab === 'sgt' && <SGTTab />}
        {activeTab === 'slgs' && <SLGSTab />}
      </div>
    </div>
  );
}
