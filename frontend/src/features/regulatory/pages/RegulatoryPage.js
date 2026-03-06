/**
 * Regulatory Reporting Page
 * SFDR PAI Indicators, EU Taxonomy Alignment, TCFD Disclosure, CSRD / ESRS
 * Standards: SFDR (EU 2019/2088), EU Taxonomy (2020/852), TCFD 2023, CSRD/ESRS S1-E1-G1
 */
import React, { useState } from 'react';
import axios from 'axios';
import MASPanel from '../MASPanel';
import { TransitionFinancePanel } from '../TransitionFinancePanel';
import { SLGSTrackerPanel } from '../SLGSTrackerPanel';
import SecClimatePanel from '../SecClimatePanel';
import UkTcfdPanel from '../UkTcfdPanel';
import ApraCpg229Panel from '../ApraCpg229Panel';
import Gri305Panel from '../Gri305Panel';
import EudrPanel from '../EudrPanel';
import EuEtsPanel from '../EuEtsPanel';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadialBarChart, RadialBar, Cell,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

/* ── Helpers ─────────────────────────────────────────────────────────────── */
function Badge({ label, color = 'bg-[#0d1424]/[0.06] text-white/40' }) {
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>{label}</span>;
}
function Card({ title, subtitle, children, className = '' }) {
  return (
    <div className={`bg-[#0d1424] rounded-xl border border-white/[0.06] ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-white/[0.05]">
          {title && <h2 className="text-sm font-semibold text-white/90">{title}</h2>}
          {subtitle && <p className="text-xs text-white/40 mt-0.5">{subtitle}</p>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}
function StatCard({ label, value, unit, sub, color = 'text-white' }) {
  return (
    <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-5">
      <p className="text-xs text-white/40 font-medium mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {value}{unit && <span className="text-sm font-normal text-white/40 ml-1">{unit}</span>}
      </p>
      {sub && <p className="text-[11px] text-white/30 mt-1">{sub}</p>}
    </div>
  );
}
function Field({ label, hint, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-white/60 mb-1">{label}</label>
      {children}
      {hint && <p className="text-[10px] text-white/30 mt-0.5">{hint}</p>}
    </div>
  );
}

/* ── SFDR PAI Panel ─────────────────────────────────────────────────────── */
const SFDR_SECTORS = [
  'Energy','Materials','Industrials','Consumer Discretionary','Consumer Staples',
  'Healthcare','Financials','Information Technology','Communication Services',
  'Utilities','Real Estate',
];

function SFDRPanel() {
  const [reportingYear, setReportingYear] = useState(2024);
  const [investees, setInvestees] = useState([{
    investee_id: 'INV_001', name: '', sector: 'Energy', country_iso: 'GB',
    investment_value_gbp: 5000000, enterprise_value_gbp: 50000000,
    revenue_gbp: 20000000, scope1_tco2e: 8000, scope2_tco2e: 2000, scope3_tco2e: null,
    pcaf_data_quality_score: 3,
  }]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const addInvestee = () => setInvestees(prev => [...prev, {
    investee_id: `INV_00${prev.length + 1}`, name: '', sector: 'Energy', country_iso: 'GB',
    investment_value_gbp: 1000000, enterprise_value_gbp: 10000000,
    revenue_gbp: 5000000, scope1_tco2e: null, scope2_tco2e: null, scope3_tco2e: null,
    pcaf_data_quality_score: 3,
  }]);

  const updateInvestee = (idx, k, v) => setInvestees(prev => {
    const arr = [...prev]; arr[idx] = { ...arr[idx], [k]: v }; return arr;
  });

  const removeInvestee = (idx) => setInvestees(prev => prev.filter((_, i) => i !== idx));

  const handleCalc = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/v1/pcaf/sfdr-pai`, {
        investees, reporting_year: reportingYear,
      });
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const mandatoryChart = result?.mandatory_indicators?.slice(0, 8).map(i => ({
    name: i.indicator_id.replace(/_/g, ' ').slice(0, 16),
    coverage: parseFloat(i.coverage_pct?.toFixed(0)),
    dq: parseFloat((i.data_quality_score * 100).toFixed(0)),
  })) || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="SFDR Art. 7 / RTS 2023" color="bg-blue-400/10 text-blue-300" />
        <Badge label="PAI Indicators 1–18" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="PCAF Standard v2.0" color="bg-emerald-400/10 text-emerald-400" />
        <Badge label="EBA GL/2022/16" color="bg-white/[0.06] text-white/60" />
      </div>

      <Card title="SFDR PAI — Portfolio Setup" subtitle="Principal Adverse Impact indicators per SFDR Annex I, Table 1 (mandatory) + Tables 2 & 3 (optional)">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-xs font-medium text-white/60 mb-1">Reporting Year</label>
              <input type="number" className="border border-white/[0.06] rounded-lg px-3 py-2 text-sm w-28 bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
                value={reportingYear} onChange={e => setReportingYear(parseInt(e.target.value))} />
            </div>
          </div>
          <button onClick={addInvestee}
            className="text-sm text-cyan-400 hover:text-cyan-300 font-medium border border-cyan-400/20 rounded-lg px-3 py-1.5">
            + Add Investee
          </button>
        </div>

        <div className="space-y-4">
          {investees.map((inv, idx) => (
            <div key={idx} className="border border-white/[0.06] rounded-lg p-4 relative">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-cyan-400">Investee {idx + 1}</span>
                {investees.length > 1 && (
                  <button onClick={() => removeInvestee(idx)} className="text-red-400 hover:text-red-600 text-xs">Remove</button>
                )}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Field label="Investee ID">
                  <input className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                    value={inv.investee_id} onChange={e => updateInvestee(idx, 'investee_id', e.target.value)} />
                </Field>
                <Field label="Company Name">
                  <input className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                    value={inv.name || ''} onChange={e => updateInvestee(idx, 'name', e.target.value)} placeholder="Optional" />
                </Field>
                <Field label="Sector">
                  <select className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                    value={inv.sector} onChange={e => updateInvestee(idx, 'sector', e.target.value)}>
                    {SFDR_SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </Field>
                <Field label="Country (ISO2)">
                  <input className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                    value={inv.country_iso} onChange={e => updateInvestee(idx, 'country_iso', e.target.value)} />
                </Field>
                <Field label="Investment Value (GBP)">
                  <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                    value={inv.investment_value_gbp} onChange={e => updateInvestee(idx, 'investment_value_gbp', parseFloat(e.target.value))} />
                </Field>
                <Field label="Enterprise Value (EVIC, GBP)">
                  <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                    value={inv.enterprise_value_gbp || ''} onChange={e => updateInvestee(idx, 'enterprise_value_gbp', parseFloat(e.target.value) || null)} />
                </Field>
                <Field label="Revenue (GBP)">
                  <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                    value={inv.revenue_gbp || ''} onChange={e => updateInvestee(idx, 'revenue_gbp', parseFloat(e.target.value) || null)} />
                </Field>
                <Field label="Scope 1 (tCO₂e)">
                  <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                    value={inv.scope1_tco2e || ''} onChange={e => updateInvestee(idx, 'scope1_tco2e', parseFloat(e.target.value) || null)} placeholder="Optional" />
                </Field>
                <Field label="Scope 2 (tCO₂e)">
                  <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                    value={inv.scope2_tco2e || ''} onChange={e => updateInvestee(idx, 'scope2_tco2e', parseFloat(e.target.value) || null)} placeholder="Optional" />
                </Field>
                <Field label="Scope 3 (tCO₂e)">
                  <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                    value={inv.scope3_tco2e || ''} onChange={e => updateInvestee(idx, 'scope3_tco2e', parseFloat(e.target.value) || null)} placeholder="Optional" />
                </Field>
                <Field label="PCAF Data Quality (1–5)" hint="1=best, 5=worst">
                  <select className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                    value={inv.pcaf_data_quality_score} onChange={e => updateInvestee(idx, 'pcaf_data_quality_score', parseInt(e.target.value))}>
                    {[1,2,3,4,5].map(n => <option key={n} value={n}>{n} — {['Company Reported','Company Reported (verified)','Third-Party Estimate','Model-Based','Fallback'][n-1]}</option>)}
                  </select>
                </Field>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end">
          <button onClick={handleCalc} disabled={loading}
            className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-[#080e1c] text-sm font-semibold px-8 py-2.5 rounded-lg shadow transition-colors">
            {loading ? 'Calculating PAI…' : 'Calculate SFDR PAI Indicators'}
          </button>
        </div>
      </Card>

      {error && <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-700">{error}</div>}

      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Mandatory PAI Indicators" value={result.mandatory_indicators?.length || 0}
              sub="SFDR Annex I Table 1" color="text-cyan-300" />
            <StatCard label="Optional PAI Indicators" value={result.optional_indicators?.length || 0}
              sub="Tables 2 & 3" />
            <StatCard label="Overall Data Coverage" value={`${result.overall_data_coverage_pct?.toFixed(0)}%`}
              color={result.overall_data_coverage_pct > 75 ? 'text-emerald-700' : 'text-amber-400'} />
            <StatCard label="Validity" value={result.validation_summary?.is_valid ? 'Valid' : 'Incomplete'}
              color={result.validation_summary?.is_valid ? 'text-emerald-700' : 'text-red-600'}
              sub={`DQ: ${((result.validation_summary?.data_quality_score || 0) * 100).toFixed(0)}%`} />
          </div>

          {mandatoryChart.length > 0 && (
            <Card title="Mandatory PAI — Coverage & Data Quality">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={mandatoryChart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 8 }} angle={-20} textAnchor="end" height={50} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(v) => [`${v}%`]} />
                  <Legend />
                  <Bar dataKey="coverage" name="Coverage %" fill="#6366f1" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="dq" name="Data Quality %" fill="#10b981" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}

          <Card title="Mandatory PAI Indicators — SFDR Annex I Table 1"
            subtitle="18 mandatory principal adverse impact indicators (climate + social)">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    {['ID','Indicator','Value','Unit','Coverage','Data Quality','Notes'].map(h => (
                      <th key={h} className="text-left text-white/40 font-semibold py-2 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.mandatory_indicators?.map((ind, i) => (
                    <tr key={i} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                      <td className="py-2 pr-4 font-mono text-white/40">{ind.indicator_id}</td>
                      <td className="pr-4 font-medium text-white/70 max-w-[200px]">{ind.indicator_name}</td>
                      <td className="pr-4 font-mono font-semibold text-cyan-400">
                        {ind.value != null ? ind.value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
                      </td>
                      <td className="pr-4 text-white/40">{ind.unit}</td>
                      <td className="pr-4">
                        <div className="flex items-center gap-1.5">
                          <div className="h-1.5 w-12 bg-white/[0.06] rounded-full">
                            <div className="h-full bg-cyan-400 rounded-full" style={{ width: `${Math.min(ind.coverage_pct, 100)}%` }} />
                          </div>
                          <span>{ind.coverage_pct?.toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="pr-4">
                        <span className={`font-medium ${ind.data_quality_score > 0.7 ? 'text-emerald-400' : ind.data_quality_score > 0.4 ? 'text-amber-400' : 'text-red-500'}`}>
                          {(ind.data_quality_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="text-white/30 text-[10px] max-w-[180px] truncate">{ind.notes || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

/* ── EU Taxonomy Panel ───────────────────────────────────────────────────── */
const EU_TAX_OBJECTIVES = [
  { v: 'climate_mitigation', l: 'Climate Change Mitigation' },
  { v: 'climate_adaptation', l: 'Climate Change Adaptation' },
  { v: 'water', l: 'Sustainable Use of Water' },
  { v: 'circular_economy', l: 'Circular Economy' },
  { v: 'pollution', l: 'Pollution Prevention' },
  { v: 'biodiversity', l: 'Biodiversity & Ecosystems' },
];

const OBJECTIVE_COLORS = ['#6366f1','#8b5cf6','#06b6d4','#10b981','#f59e0b','#ef4444'];

function EUTaxonomyPanel() {
  const [reportingYear, setReportingYear] = useState(2024);
  const [entities, setEntities] = useState([{
    entity_id: 'ENT_001', name: '', sector: 'Utilities', country_iso: 'GB',
    activities: [{ activity_code: 'EU_4.1', activity_name: 'Electricity from wind', turnover_pct: 60, capex_pct: 70, substantial_contribution_objective: 'climate_mitigation' }],
    total_revenue_gbp: 50000000, total_capex_gbp: 20000000,
  }]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleCalc = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/v1/pcaf/eu-taxonomy`, {
        entities, reporting_year: reportingYear,
      });
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const addActivity = (entityIdx) => {
    setEntities(prev => {
      const arr = [...prev];
      arr[entityIdx] = {
        ...arr[entityIdx],
        activities: [...arr[entityIdx].activities, {
          activity_code: '', activity_name: '', turnover_pct: 0, capex_pct: 0, substantial_contribution_objective: 'climate_mitigation'
        }]
      };
      return arr;
    });
  };

  const updateActivity = (entityIdx, actIdx, k, v) => {
    setEntities(prev => {
      const arr = [...prev];
      const acts = [...arr[entityIdx].activities];
      acts[actIdx] = { ...acts[actIdx], [k]: v };
      arr[entityIdx] = { ...arr[entityIdx], activities: acts };
      return arr;
    });
  };

  const alignmentPie = result?.portfolio_summary?.objective_alignments?.map((obj, i) => ({
    name: obj.objective.replace(/_/g, ' '),
    value: parseFloat(obj.aligned_turnover_pct?.toFixed(1)),
    fill: OBJECTIVE_COLORS[i % OBJECTIVE_COLORS.length],
  })) || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="EU Taxonomy Regulation 2020/852" color="bg-emerald-400/10 text-emerald-400" />
        <Badge label="Delegated Acts 2021/2139" color="bg-blue-400/10 text-blue-300" />
        <Badge label="DNSH Criteria" color="bg-amber-500/10 text-amber-700" />
        <Badge label="Minimum Safeguards" color="bg-white/[0.06] text-white/60" />
      </div>

      <Card title="EU Taxonomy — Entity Activity Data"
        subtitle="Map entity economic activities to EU Taxonomy technical screening criteria. Eligible = screened, Aligned = screened + DNSH + minimum safeguards.">
        <div className="flex items-center gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Reporting Year</label>
            <input type="number" className="border border-white/[0.06] rounded-lg px-3 py-2 text-sm w-28 bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={reportingYear} onChange={e => setReportingYear(parseInt(e.target.value))} />
          </div>
        </div>

        {entities.map((ent, ei) => (
          <div key={ei} className="border border-white/[0.06] rounded-xl p-5 mb-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <Field label="Entity ID">
                <input className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                  value={ent.entity_id} onChange={e => setEntities(prev => { const a=[...prev]; a[ei]={...a[ei],entity_id:e.target.value}; return a; })} />
              </Field>
              <Field label="Sector">
                <input className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                  value={ent.sector} onChange={e => setEntities(prev => { const a=[...prev]; a[ei]={...a[ei],sector:e.target.value}; return a; })} />
              </Field>
              <Field label="Revenue (GBP)">
                <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                  value={ent.total_revenue_gbp} onChange={e => setEntities(prev => { const a=[...prev]; a[ei]={...a[ei],total_revenue_gbp:parseFloat(e.target.value)}; return a; })} />
              </Field>
              <Field label="CapEx (GBP)">
                <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                  value={ent.total_capex_gbp} onChange={e => setEntities(prev => { const a=[...prev]; a[ei]={...a[ei],total_capex_gbp:parseFloat(e.target.value)}; return a; })} />
              </Field>
            </div>

            <p className="text-xs font-semibold text-white/60 mb-2">Economic Activities</p>
            {ent.activities.map((act, ai) => (
              <div key={ai} className="grid grid-cols-6 gap-2 mb-2 items-center">
                <input className="border border-white/[0.06] rounded px-2 py-1.5 text-xs focus:outline-none"
                  placeholder="Activity code" value={act.activity_code}
                  onChange={e => updateActivity(ei, ai, 'activity_code', e.target.value)} />
                <input className="col-span-2 border border-white/[0.06] rounded px-2 py-1.5 text-xs focus:outline-none"
                  placeholder="Activity name" value={act.activity_name}
                  onChange={e => updateActivity(ei, ai, 'activity_name', e.target.value)} />
                <input type="number" className="border border-white/[0.06] rounded px-2 py-1.5 text-xs focus:outline-none"
                  placeholder="Turnover %" value={act.turnover_pct}
                  onChange={e => updateActivity(ei, ai, 'turnover_pct', parseFloat(e.target.value))} />
                <input type="number" className="border border-white/[0.06] rounded px-2 py-1.5 text-xs focus:outline-none"
                  placeholder="CapEx %" value={act.capex_pct}
                  onChange={e => updateActivity(ei, ai, 'capex_pct', parseFloat(e.target.value))} />
                <select className="border border-white/[0.06] rounded px-2 py-1.5 text-xs focus:outline-none"
                  value={act.substantial_contribution_objective}
                  onChange={e => updateActivity(ei, ai, 'substantial_contribution_objective', e.target.value)}>
                  {EU_TAX_OBJECTIVES.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
                </select>
              </div>
            ))}
            <button onClick={() => addActivity(ei)} className="text-xs text-cyan-400 hover:text-cyan-300 font-medium mt-1">+ Add Activity</button>
          </div>
        ))}

        <div className="flex justify-end mt-4">
          <button onClick={handleCalc} disabled={loading}
            className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-[#080e1c] text-sm font-semibold px-8 py-2.5 rounded-lg shadow transition-colors">
            {loading ? 'Assessing…' : 'Calculate EU Taxonomy Alignment'}
          </button>
        </div>
      </Card>

      {error && <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-700">{error}</div>}

      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Eligible Turnover" value={`${result.portfolio_summary?.eligible_turnover_pct?.toFixed(1)}%`}
              color="text-blue-300" sub="Taxonomy-eligible activities" />
            <StatCard label="Aligned Turnover" value={`${result.portfolio_summary?.aligned_turnover_pct?.toFixed(1)}%`}
              color="text-emerald-700" sub="Fully taxonomy-aligned" />
            <StatCard label="Eligible CapEx" value={`${result.portfolio_summary?.eligible_capex_pct?.toFixed(1)}%`}
              color="text-blue-300" />
            <StatCard label="Aligned CapEx" value={`${result.portfolio_summary?.aligned_capex_pct?.toFixed(1)}%`}
              color="text-emerald-400" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card title="Alignment by EU Taxonomy Objective">
              <div className="space-y-3">
                {result.portfolio_summary?.objective_alignments?.map((obj, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: OBJECTIVE_COLORS[i % OBJECTIVE_COLORS.length] }} />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-xs font-medium text-white/70">{obj.objective.replace(/_/g, ' ')}</span>
                        <span className="text-xs font-bold text-emerald-700">{obj.aligned_turnover_pct?.toFixed(1)}%</span>
                      </div>
                      <div className="h-1.5 bg-white/[0.06] rounded-full">
                        <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${Math.min(obj.aligned_turnover_pct, 100)}%` }} />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card title="DNSH Compliance Summary" subtitle="Do Not Significantly Harm checks across 6 environmental objectives">
              {result.per_entity?.map((ent, i) => (
                <div key={i} className="mb-4">
                  <p className="text-xs font-semibold text-white/60 mb-2">{ent.entity_id}</p>
                  <div className="grid grid-cols-2 gap-2">
                    {ent.activity_results?.map((act, j) => (
                      <div key={j} className={`p-2.5 rounded-lg border ${act.dnsh_compliant ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
                        <p className="text-[10px] font-medium text-white/70 truncate">{act.activity_name || act.activity_code}</p>
                        <p className={`text-[10px] font-bold ${act.dnsh_compliant ? 'text-emerald-700' : 'text-red-600'}`}>
                          {act.dnsh_compliant ? 'DNSH Compliant' : 'DNSH Non-Compliant'}
                        </p>
                        <p className="text-[10px] text-white/30">Aligned: T {act.aligned_turnover_pct?.toFixed(0)}% | C {act.aligned_capex_pct?.toFixed(0)}%</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── TCFD Panel ─────────────────────────────────────────────────────────── */
const TCFD_PILLARS = [
  {
    id: 'governance', label: 'Governance', color: 'bg-blue-500/10 border-blue-500/20 text-blue-300',
    elements: [
      { id: 'board_oversight', label: 'Board oversight of climate-related risks and opportunities' },
      { id: 'management_role', label: "Management's role in assessing and managing climate risks" },
    ],
  },
  {
    id: 'strategy', label: 'Strategy', color: 'bg-cyan-500/10 border-cyan-500/20 text-cyan-300',
    elements: [
      { id: 'climate_risks_opps', label: 'Climate-related risks and opportunities identified' },
      { id: 'impact_on_business', label: 'Impact on business, strategy and financial planning' },
      { id: 'scenario_resilience', label: 'Resilience of strategy under different climate scenarios' },
    ],
  },
  {
    id: 'risk_management', label: 'Risk Management', color: 'bg-purple-500/10 border-purple-500/20 text-purple-300',
    elements: [
      { id: 'risk_identification', label: 'Process for identifying and assessing climate risks' },
      { id: 'risk_management_process', label: 'Process for managing climate-related risks' },
      { id: 'integration', label: 'Integration into overall risk management' },
    ],
  },
  {
    id: 'metrics_targets', label: 'Metrics & Targets', color: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-800',
    elements: [
      { id: 'metrics_used', label: 'Metrics used to assess climate-related risks and opportunities' },
      { id: 'scope_1_2_3', label: 'Scope 1, 2 and 3 GHG emissions disclosed' },
      { id: 'targets', label: 'Targets and performance against targets' },
    ],
  },
];

const MATURITY_LEVELS = [
  { v: 0, l: '0 — Not Disclosed' },
  { v: 1, l: '1 — Partial / Initial' },
  { v: 2, l: '2 — Developing' },
  { v: 3, l: '3 — Established' },
  { v: 4, l: '4 — Advanced / Leading Practice' },
];

function TCFDPanel() {
  const [disclosures, setDisclosures] = useState(() => {
    const init = {};
    TCFD_PILLARS.forEach(p => p.elements.forEach(e => { init[e.id] = { maturity: 1, notes: '' }; }));
    return init;
  });
  const [result, setResult] = useState(null);

  const setDisclosure = (elementId, k, v) => {
    setDisclosures(prev => ({ ...prev, [elementId]: { ...prev[elementId], [k]: v } }));
  };

  const computeResult = () => {
    const pillarScores = TCFD_PILLARS.map(p => {
      const avg = p.elements.reduce((s, e) => s + (disclosures[e.id]?.maturity || 0), 0) / p.elements.length;
      return { pillar: p.label, score: parseFloat(avg.toFixed(2)), maxScore: 4 };
    });
    const overall = pillarScores.reduce((s, p) => s + p.score, 0) / pillarScores.length;
    setResult({ pillarScores, overall: parseFloat(overall.toFixed(2)) });
  };

  const maturityColor = (m) => m >= 3 ? 'text-emerald-400' : m >= 2 ? 'text-amber-400' : 'text-red-500';

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="TCFD 2023 Recommendations" color="bg-blue-400/10 text-blue-300" />
        <Badge label="ISSB IFRS S2" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="UK TCFD-Aligned Mandate" color="bg-white/[0.06] text-white/60" />
        <Badge label="SEC Climate Disclosure Rule" color="bg-purple-400/10 text-purple-300" />
      </div>

      <Card title="TCFD Self-Assessment — Maturity Scoring" subtitle="Rate disclosure maturity across all 11 recommended disclosures (4 pillars). Score 0-4.">
        <div className="space-y-6">
          {TCFD_PILLARS.map(pillar => (
            <div key={pillar.id} className={`border rounded-xl p-4 ${pillar.color}`}>
              <h3 className="text-sm font-bold mb-3">{pillar.label}</h3>
              <div className="space-y-3">
                {pillar.elements.map(el => (
                  <div key={el.id} className="bg-[#0d1424] rounded-lg p-3 border border-white/50">
                    <p className="text-xs font-medium text-white/70 mb-2">{el.label}</p>
                    <div className="flex items-center gap-3">
                      <select className="border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50 w-64"
                        value={disclosures[el.id]?.maturity || 0}
                        onChange={e => setDisclosure(el.id, 'maturity', parseInt(e.target.value))}>
                        {MATURITY_LEVELS.map(m => <option key={m.v} value={m.v}>{m.l}</option>)}
                      </select>
                      <input className="flex-1 border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
                        placeholder="Notes / evidence (optional)"
                        value={disclosures[el.id]?.notes || ''}
                        onChange={e => setDisclosure(el.id, 'notes', e.target.value)} />
                      <span className={`text-sm font-bold min-w-[24px] ${maturityColor(disclosures[el.id]?.maturity || 0)}`}>
                        {disclosures[el.id]?.maturity || 0}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-6 flex justify-end">
          <button onClick={computeResult}
            className="bg-cyan-400 hover:bg-cyan-300 text-[#080e1c] text-sm font-semibold px-8 py-2.5 rounded-lg shadow transition-colors">
            Generate TCFD Assessment
          </button>
        </div>
      </Card>

      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="col-span-1 bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-400/10 rounded-xl p-5 text-white text-center">
              <p className="text-xs font-medium text-cyan-200/60 mb-1">Overall TCFD Score</p>
              <p className="text-3xl font-bold">{result.overall.toFixed(1)}<span className="text-lg text-cyan-200/60">/4</span></p>
              <p className="text-xs text-cyan-200/60 mt-1">
                {result.overall >= 3 ? 'Advanced' : result.overall >= 2 ? 'Developing' : 'Initial'}
              </p>
            </div>
            {result.pillarScores.map((p, i) => (
              <StatCard key={i} label={p.pillar} value={`${p.score.toFixed(1)}/4`}
                color={p.score >= 3 ? 'text-emerald-700' : p.score >= 2 ? 'text-amber-400' : 'text-red-600'}
                sub="Maturity score" />
            ))}
          </div>

          <Card title="Pillar Scores vs Target (4.0 = Leading Practice)">
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={result.pillarScores}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="pillar" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 4]} ticks={[0,1,2,3,4]} tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v) => [`${v}/4`]} />
                <Bar dataKey="score" name="Score" fill="#6366f1" radius={[4, 4, 0, 0]}>
                  {result.pillarScores.map((p, i) => (
                    <Cell key={i} fill={p.score >= 3 ? '#10b981' : p.score >= 2 ? '#f59e0b' : '#ef4444'} />
                  ))}
                </Bar>
                <Bar dataKey="maxScore" name="Target (4)" fill="#e2e8f0" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          <Card title="Disclosure Gap Analysis">
            {TCFD_PILLARS.map(pillar => {
              const gapElements = pillar.elements.filter(e => (disclosures[e.id]?.maturity || 0) < 3);
              if (!gapElements.length) return (
                <div key={pillar.id} className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg mb-2">
                  <span className="text-xs font-semibold text-emerald-700">{pillar.label}</span>
                  <span className="text-xs text-emerald-400 ml-2">All elements at maturity ≥ 3</span>
                </div>
              );
              return (
                <div key={pillar.id} className="p-3 bg-amber-500/10 border border-amber-200 rounded-lg mb-2">
                  <p className="text-xs font-semibold text-amber-800 mb-2">{pillar.label} — Gaps identified</p>
                  {gapElements.map(e => (
                    <div key={e.id} className="flex items-center gap-2 text-xs text-amber-700 mb-1">
                      <span className="font-bold">{disclosures[e.id]?.maturity}/4</span>
                      <span>{e.label}</span>
                    </div>
                  ))}
                </div>
              );
            })}
          </Card>
        </div>
      )}
    </div>
  );
}

/* ── CSRD / ESRS Panel ──────────────────────────────────────────────────── */
const ESRS_STANDARDS = [
  {
    code: 'ESRS 2', name: 'General Disclosures', category: 'Cross-Cutting', mandatory: true,
    topics: ['Governance', 'Strategy', 'Impact/Risk/Opportunity Management', 'Metrics & Targets'],
  },
  {
    code: 'ESRS E1', name: 'Climate Change', category: 'Environment', mandatory: true,
    topics: ['GHG Emissions', 'Climate Transition Plan', 'Physical Climate Risk', 'Energy'],
  },
  {
    code: 'ESRS E2', name: 'Pollution', category: 'Environment', mandatory: false,
    topics: ['Air Pollution', 'Water Pollution', 'Soil Pollution', 'Substances of Concern'],
  },
  {
    code: 'ESRS E3', name: 'Water & Marine Resources', category: 'Environment', mandatory: false,
    topics: ['Water Consumption', 'Water Withdrawals', 'Marine Ecosystems'],
  },
  {
    code: 'ESRS E4', name: 'Biodiversity & Ecosystems', category: 'Environment', mandatory: false,
    topics: ['Biodiversity Loss', 'Land Use', 'Ecosystem Services', 'TNFD Alignment'],
  },
  {
    code: 'ESRS E5', name: 'Resource Use & Circular Economy', category: 'Environment', mandatory: false,
    topics: ['Resource Inflows', 'Resource Outflows', 'Waste Management'],
  },
  {
    code: 'ESRS S1', name: 'Own Workforce', category: 'Social', mandatory: true,
    topics: ['Working Conditions', 'Equal Treatment', 'Social Protection', 'Health & Safety'],
  },
  {
    code: 'ESRS S2', name: 'Workers in Value Chain', category: 'Social', mandatory: false,
    topics: ['Supplier Labour Rights', 'Modern Slavery Risk', 'Working Conditions'],
  },
  {
    code: 'ESRS S3', name: 'Affected Communities', category: 'Social', mandatory: false,
    topics: ['Community Impact', 'Indigenous Peoples', 'Social & Economic Rights'],
  },
  {
    code: 'ESRS S4', name: 'Consumers & End-Users', category: 'Social', mandatory: false,
    topics: ['Product Safety', 'Privacy', 'Social Inclusion', 'Access to Products'],
  },
  {
    code: 'ESRS G1', name: 'Business Conduct', category: 'Governance', mandatory: true,
    topics: ['Anti-Corruption', 'Anti-Bribery', 'Lobbying', 'Supplier Relationships'],
  },
];

const READINESS_LEVELS = [
  { v: 'not_started', l: 'Not Started' },
  { v: 'planning', l: 'Planning Phase' },
  { v: 'data_collection', l: 'Data Collection' },
  { v: 'drafting', l: 'Drafting' },
  { v: 'review', l: 'Under Review' },
  { v: 'complete', l: 'Complete' },
];

const READINESS_COLOR = {
  not_started: 'bg-red-500/10 text-red-600 border-red-500/20',
  planning: 'bg-amber-500/10 text-amber-400 border-amber-200',
  data_collection: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  drafting: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
  review: 'bg-cyan-400/10 text-cyan-400 border-cyan-400/20',
  complete: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
};

function CSRDPanel() {
  const [readiness, setReadiness] = useState(() => {
    const init = {};
    ESRS_STANDARDS.forEach(s => { init[s.code] = { status: 'not_started', notes: '' }; });
    return init;
  });
  const [entitySize, setEntitySize] = useState('large_piu');
  const [firstYear, setFirstYear] = useState(2025);

  const setStatus = (code, k, v) => setReadiness(prev => ({ ...prev, [code]: { ...prev[code], [k]: v } }));

  const completedCount = Object.values(readiness).filter(r => r.status === 'complete').length;
  const mandatory = ESRS_STANDARDS.filter(s => s.mandatory);
  const mandatoryComplete = mandatory.filter(s => readiness[s.code]?.status === 'complete').length;

  const ENTITY_SIZES = [
    { v: 'large_piu', l: 'Large PIE (>500 employees) — FY2024 reporting' },
    { v: 'large_non_piu', l: 'Large Non-PIE — FY2025 reporting' },
    { v: 'sme_listed', l: 'Listed SME — FY2026 reporting' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="CSRD (EU 2022/2464)" color="bg-emerald-400/10 text-emerald-400" />
        <Badge label="ESRS Set 1 (2023)" color="bg-blue-400/10 text-blue-300" />
        <Badge label="Double Materiality" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="EFRAG Guidance" color="bg-white/[0.06] text-white/60" />
      </div>

      <Card title="CSRD Readiness Assessment" subtitle="Track ESRS disclosure readiness across all 11 topic standards. Supports double materiality assessment.">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Entity Classification</label>
            <select className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={entitySize} onChange={e => setEntitySize(e.target.value)}>
              {ENTITY_SIZES.map(e => <option key={e.v} value={e.v}>{e.l}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">First Reporting Year</label>
            <input type="number" className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={firstYear} onChange={e => setFirstYear(parseInt(e.target.value))} />
          </div>
          <div className="flex items-end gap-4">
            <div className="text-center p-3 bg-cyan-400/[0.06] rounded-lg flex-1">
              <p className="text-2xl font-bold text-cyan-300">{completedCount}/{ESRS_STANDARDS.length}</p>
              <p className="text-xs text-white/40">Standards Complete</p>
            </div>
            <div className="text-center p-3 bg-emerald-400/[0.06] rounded-lg flex-1">
              <p className="text-2xl font-bold text-emerald-700">{mandatoryComplete}/{mandatory.length}</p>
              <p className="text-xs text-white/40">Mandatory Complete</p>
            </div>
          </div>
        </div>

        {['Cross-Cutting', 'Environment', 'Social', 'Governance'].map(cat => {
          const catStandards = ESRS_STANDARDS.filter(s => s.category === cat);
          return (
            <div key={cat} className="mb-5">
              <h3 className="text-xs font-bold text-white/40 uppercase tracking-wide mb-2">{cat}</h3>
              <div className="space-y-2">
                {catStandards.map(std => (
                  <div key={std.code} className="border border-white/[0.06] rounded-lg p-3">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-20">
                        <span className="text-xs font-bold text-cyan-400">{std.code}</span>
                        {std.mandatory && <Badge label="Mandatory" color="bg-cyan-400/10 text-cyan-400" />}
                      </div>
                      <div className="flex-1">
                        <p className="text-xs font-semibold text-white/90">{std.name}</p>
                        <p className="text-[10px] text-white/30 mb-2">{std.topics.join(' · ')}</p>
                        <div className="flex items-center gap-3">
                          <select
                            className={`border rounded px-2 py-1 text-xs focus:outline-none w-48 ${READINESS_COLOR[readiness[std.code]?.status] || ''}`}
                            value={readiness[std.code]?.status}
                            onChange={e => setStatus(std.code, 'status', e.target.value)}>
                            {READINESS_LEVELS.map(l => <option key={l.v} value={l.v}>{l.l}</option>)}
                          </select>
                          <input className="flex-1 border border-white/[0.06] rounded px-2 py-1 text-xs focus:outline-none"
                            placeholder="Notes / gaps / owner"
                            value={readiness[std.code]?.notes || ''}
                            onChange={e => setStatus(std.code, 'notes', e.target.value)} />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </Card>

      {/* Readiness Summary */}
      <Card title="CSRD Readiness Summary — Disclosure Tracker">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {READINESS_LEVELS.map(level => {
            const count = Object.values(readiness).filter(r => r.status === level.v).length;
            return (
              <div key={level.v} className={`p-3 rounded-lg border ${READINESS_COLOR[level.v] || 'bg-white/[0.02] border-white/[0.06]'}`}>
                <p className="text-xl font-bold">{count}</p>
                <p className="text-xs font-medium">{level.l}</p>
              </div>
            );
          })}
        </div>
        <div className="mt-4 bg-white/[0.02] rounded-lg p-4">
          <p className="text-xs font-semibold text-white/60 mb-2">Mandatory Standards ({mandatory.length}) — Readiness</p>
          <div className="h-3 bg-white/[0.06] rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 rounded-full transition-all"
              style={{ width: `${(mandatoryComplete / mandatory.length) * 100}%` }} />
          </div>
          <p className="text-xs text-white/40 mt-1">{mandatoryComplete}/{mandatory.length} complete ({((mandatoryComplete / mandatory.length) * 100).toFixed(0)}%)</p>
        </div>
      </Card>
    </div>
  );
}

/* ── ISSB IFRS S1 / S2 Panel ────────────────────────────────────────────── */
const ISSB_S1_DISCLOSURES = [
  {
    category: 'Governance',
    items: [
      { id: 's1_gov_1', label: 'Board oversight of sustainability-related risks and opportunities' },
      { id: 's1_gov_2', label: "Management's role in sustainability risk/opportunity governance" },
    ],
  },
  {
    category: 'Strategy',
    items: [
      { id: 's1_str_1', label: 'Sustainability-related risks and opportunities identified' },
      { id: 's1_str_2', label: 'Effect on business model, value chain, strategy and financial planning' },
      { id: 's1_str_3', label: 'Resilience of strategy and business model' },
    ],
  },
  {
    category: 'Risk Management',
    items: [
      { id: 's1_rm_1', label: 'Process for identifying, assessing and prioritising risks/opportunities' },
      { id: 's1_rm_2', label: 'Integration into overall risk management processes' },
    ],
  },
  {
    category: 'Metrics & Targets',
    items: [
      { id: 's1_mt_1', label: 'Metrics used to measure and monitor sustainability-related risks' },
      { id: 's1_mt_2', label: 'Targets set and performance against targets' },
    ],
  },
];

const ISSB_S2_DISCLOSURES = [
  {
    category: 'Governance',
    items: [
      { id: 's2_gov_1', label: 'Governance body/individual responsible for climate-related risks' },
      { id: 's2_gov_2', label: 'Skills and competencies of governance body on climate' },
    ],
  },
  {
    category: 'Strategy',
    items: [
      { id: 's2_str_1', label: 'Climate-related physical and transition risks/opportunities' },
      { id: 's2_str_2', label: 'Current and anticipated effects on business model and value chain' },
      { id: 's2_str_3', label: 'Resilience of strategy — scenario analysis (1.5°C and 2°C+)' },
      { id: 's2_str_4', label: 'Planned/underway climate-related transition plan (if applicable)' },
    ],
  },
  {
    category: 'Risk Management',
    items: [
      { id: 's2_rm_1', label: 'Climate risk identification and assessment process' },
      { id: 's2_rm_2', label: 'Climate risk integration into overall risk management' },
    ],
  },
  {
    category: 'Metrics & Targets',
    items: [
      { id: 's2_mt_1', label: 'Scope 1, 2 and 3 GHG emissions (tCO₂e) — cross-industry metric' },
      { id: 's2_mt_2', label: 'Climate-related transition risks financial metric' },
      { id: 's2_mt_3', label: 'Climate-related physical risks financial metric' },
      { id: 's2_mt_4', label: 'Capital deployment towards climate-related opportunities' },
      { id: 's2_mt_5', label: 'Internal carbon price (USD/tCO₂e)' },
      { id: 's2_mt_6', label: 'Remuneration linked to climate considerations (% of exec pay)' },
    ],
  },
];

const ISSB_CATEGORY_COLORS = {
  Governance: 'bg-blue-500/10 border-blue-500/20 text-blue-300',
  Strategy: 'bg-cyan-500/10 border-cyan-500/20 text-cyan-300',
  'Risk Management': 'bg-purple-500/10 border-purple-500/20 text-purple-300',
  'Metrics & Targets': 'bg-emerald-500/10 border-emerald-500/20 text-emerald-800',
};

const ISSB_MATURITY = [
  { v: 0, l: '0 — Not Disclosed' },
  { v: 1, l: '1 — Partial Disclosure' },
  { v: 2, l: '2 — Developing' },
  { v: 3, l: '3 — Substantially Compliant' },
  { v: 4, l: '4 — Fully Compliant' },
];

function ISSBPanel() {
  const [activeStd, setActiveStd] = useState('s1');
  const [disclosures, setDisclosures] = useState(() => {
    const init = {};
    [...ISSB_S1_DISCLOSURES, ...ISSB_S2_DISCLOSURES].forEach(cat =>
      cat.items.forEach(item => { init[item.id] = { maturity: 0, notes: '' }; })
    );
    return init;
  });
  const [result, setResult] = useState(null);

  const set = (id, k, v) => setDisclosures(prev => ({ ...prev, [id]: { ...prev[id], [k]: v } }));

  const compute = () => {
    const s1Items = ISSB_S1_DISCLOSURES.flatMap(c => c.items);
    const s2Items = ISSB_S2_DISCLOSURES.flatMap(c => c.items);
    const s1Score = s1Items.reduce((s, i) => s + (disclosures[i.id]?.maturity || 0), 0) / s1Items.length;
    const s2Score = s2Items.reduce((s, i) => s + (disclosures[i.id]?.maturity || 0), 0) / s2Items.length;
    setResult({ s1Score: parseFloat(s1Score.toFixed(2)), s2Score: parseFloat(s2Score.toFixed(2)) });
  };

  const activeDisclosures = activeStd === 's1' ? ISSB_S1_DISCLOSURES : ISSB_S2_DISCLOSURES;
  const maturityColor = (m) => m >= 3 ? 'text-emerald-400' : m >= 2 ? 'text-amber-400' : m >= 1 ? 'text-blue-300' : 'text-red-500';

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="IFRS S1 (General Requirements)" color="bg-blue-400/10 text-blue-300" />
        <Badge label="IFRS S2 (Climate-Related Disclosures)" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="ISSB 2023" color="bg-purple-400/10 text-purple-300" />
        <Badge label="TCFD-Compatible" color="bg-emerald-400/10 text-emerald-400" />
        <Badge label="IOSCO Endorsed" color="bg-white/[0.06] text-white/60" />
      </div>

      {result && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-400/10 rounded-xl p-5 text-white text-center">
            <p className="text-xs text-blue-200 mb-1">IFRS S1 — Sustainability</p>
            <p className="text-3xl font-bold">{result.s1Score.toFixed(1)}<span className="text-lg text-blue-200">/4</span></p>
            <p className="text-xs text-blue-200 mt-1">{result.s1Score >= 3 ? 'Substantially Compliant' : result.s1Score >= 2 ? 'Developing' : 'Early Stage'}</p>
          </div>
          <div className="bg-gradient-to-br from-cyan-500/20 to-purple-500/20 border border-cyan-400/10 rounded-xl p-5 text-white text-center">
            <p className="text-xs text-cyan-200/60 mb-1">IFRS S2 — Climate</p>
            <p className="text-3xl font-bold">{result.s2Score.toFixed(1)}<span className="text-lg text-cyan-200/60">/4</span></p>
            <p className="text-xs text-cyan-200/60 mt-1">{result.s2Score >= 3 ? 'Substantially Compliant' : result.s2Score >= 2 ? 'Developing' : 'Early Stage'}</p>
          </div>
        </div>
      )}

      <Card title="ISSB IFRS Sustainability Disclosure Standards" subtitle="Self-assessment against IFRS S1 (general requirements) and IFRS S2 (climate-specific disclosures). Score 0–4.">
        <div className="flex gap-3 mb-5">
          <button onClick={() => setActiveStd('s1')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold border transition-all ${activeStd === 's1' ? 'bg-blue-500 text-white border-blue-500' : 'bg-[#0d1424] text-white/60 border-white/[0.06] hover:border-blue-400/50'}`}>
            IFRS S1 — General Requirements ({ISSB_S1_DISCLOSURES.flatMap(c=>c.items).length} disclosures)
          </button>
          <button onClick={() => setActiveStd('s2')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold border transition-all ${activeStd === 's2' ? 'bg-cyan-400 text-[#080e1c] border-cyan-400' : 'bg-[#0d1424] text-white/60 border-white/[0.06] hover:border-cyan-400/50'}`}>
            IFRS S2 — Climate ({ISSB_S2_DISCLOSURES.flatMap(c=>c.items).length} disclosures)
          </button>
        </div>

        <div className="space-y-4">
          {activeDisclosures.map(cat => (
            <div key={cat.category} className={`border rounded-xl p-4 ${ISSB_CATEGORY_COLORS[cat.category] || 'bg-white/[0.02] border-white/[0.06] text-white/90'}`}>
              <h3 className="text-xs font-bold mb-3">{cat.category}</h3>
              <div className="space-y-2">
                {cat.items.map(item => (
                  <div key={item.id} className="bg-[#0d1424] rounded-lg p-3 border border-white/50">
                    <p className="text-xs font-medium text-white/70 mb-2">{item.label}</p>
                    <div className="flex items-center gap-3">
                      <select className="border border-white/[0.06] rounded px-2 py-1 text-xs focus:outline-none w-56"
                        value={disclosures[item.id]?.maturity || 0}
                        onChange={e => set(item.id, 'maturity', parseInt(e.target.value))}>
                        {ISSB_MATURITY.map(m => <option key={m.v} value={m.v}>{m.l}</option>)}
                      </select>
                      <input className="flex-1 border border-white/[0.06] rounded px-2 py-1 text-xs focus:outline-none"
                        placeholder="Evidence / notes"
                        value={disclosures[item.id]?.notes || ''}
                        onChange={e => set(item.id, 'notes', e.target.value)} />
                      <span className={`text-sm font-bold min-w-[24px] ${maturityColor(disclosures[item.id]?.maturity || 0)}`}>
                        {disclosures[item.id]?.maturity || 0}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-6 flex justify-end">
          <button onClick={compute}
            className="bg-cyan-400 hover:bg-cyan-300 text-[#080e1c] text-sm font-semibold px-8 py-2.5 rounded-lg shadow transition-colors">
            Score ISSB Assessment
          </button>
        </div>
      </Card>
    </div>
  );
}

/* ── BRSR Panel (India SEBI) ─────────────────────────────────────────────── */
const BRSR_PRINCIPLES = [
  { id: 'p1', label: 'P1 — Ethical Governance & Transparency', mandatory: true,
    indicators: ['Director/KMP disclosures', 'Anti-corruption & bribery policy', 'Compliance with laws', 'Fines & penalties'] },
  { id: 'p2', label: 'P2 — Safe & Sustainable Products/Services', mandatory: true,
    indicators: ['R&D spend', 'Sustainable sourcing %', 'End-of-life product reclaim', 'Packaging sustainability'] },
  { id: 'p3', label: 'P3 — Employee Wellbeing', mandatory: true,
    indicators: ['Permanent employees', 'Contract workers', 'Health & safety incidents', 'Training hours', 'Diversity & inclusion'] },
  { id: 'p4', label: 'P4 — Stakeholder Engagement', mandatory: true,
    indicators: ['Vulnerable/marginalised group identification', 'CSR projects', 'Community engagement'] },
  { id: 'p5', label: 'P5 — Human Rights', mandatory: true,
    indicators: ['Human rights training', 'Complaints received', 'Minimum wage compliance', 'Child/forced labour policy'] },
  { id: 'p6', label: 'P6 — Environment', mandatory: true,
    indicators: ['Scope 1 & 2 GHG (tCO₂e)', 'Scope 3 GHG', 'Energy consumption (GJ)', 'Water intensity', 'Waste generated & disposed', 'Biodiversity impact'] },
  { id: 'p7', label: 'P7 — Policy & Regulatory Engagement', mandatory: false,
    indicators: ['Trade/industry memberships', 'Anti-competitive conduct cases', 'Public policy advocacy'] },
  { id: 'p8', label: 'P8 — Inclusive Growth', mandatory: true,
    indicators: ['CSR spend', 'Social impact projects', 'MSMEs in supply chain', 'IP licensing to SMEs'] },
  { id: 'p9', label: 'P9 — Customer Value', mandatory: true,
    indicators: ['Consumer complaint mechanisms', 'Cybersecurity incidents', 'Product labelling compliance', 'Data privacy breaches'] },
];

const BRSR_READINESS = [
  { v: 'not_started', l: 'Not Started' },
  { v: 'data_gap', l: 'Data Gap Identified' },
  { v: 'in_progress', l: 'In Progress' },
  { v: 'disclosed', l: 'Disclosed (BRSR)' },
];

const BRSR_READINESS_COLOR = {
  not_started: 'bg-red-500/10 text-red-600 border-red-500/20',
  data_gap: 'bg-amber-500/10 text-amber-400 border-amber-200',
  in_progress: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
  disclosed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
};

function BRSRPanel() {
  const [applicability, setApplicability] = useState('top1000');
  const [reportingYear, setReportingYear] = useState(2024);
  const [readiness, setReadiness] = useState(() => {
    const init = {};
    BRSR_PRINCIPLES.forEach(p => { init[p.id] = { status: 'not_started', notes: '', score: 0 }; });
    return init;
  });

  const set = (id, k, v) => setReadiness(prev => ({ ...prev, [id]: { ...prev[id], [k]: v } }));

  const disclosedCount = Object.values(readiness).filter(r => r.status === 'disclosed').length;
  const mandatoryPrinciples = BRSR_PRINCIPLES.filter(p => p.mandatory);
  const mandatoryDisclosed = mandatoryPrinciples.filter(p => readiness[p.id]?.status === 'disclosed').length;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="SEBI BRSR (2021)" color="bg-blue-400/10 text-blue-300" />
        <Badge label="BRSR Core (FY2024)" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="9 Principles / NVGs" color="bg-amber-500/10 text-amber-700" />
        <Badge label="NSE / BSE Listed" color="bg-emerald-400/10 text-emerald-400" />
      </div>

      <Card title="Business Responsibility & Sustainability Report (BRSR)" subtitle="SEBI Circular SEBI/HO/CFD/CMD-2/P/CIR/2021/562 — 9 Principles of NVG SEGs. Mandatory for Top 1000 listed companies (by market cap) from FY2022-23.">
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Applicability</label>
            <select className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={applicability} onChange={e => setApplicability(e.target.value)}>
              <option value="top500">Top 500 Listed (by M-Cap)</option>
              <option value="top1000">Top 1000 Listed (by M-Cap)</option>
              <option value="voluntary">Voluntary Reporter</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Reporting Year</label>
            <input type="number" className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={reportingYear} onChange={e => setReportingYear(parseInt(e.target.value))} />
          </div>
          <div className="flex items-end gap-3">
            <div className="text-center p-3 bg-cyan-400/[0.06] rounded-lg flex-1">
              <p className="text-xl font-bold text-cyan-300">{disclosedCount}/{BRSR_PRINCIPLES.length}</p>
              <p className="text-xs text-white/40">Principles Disclosed</p>
            </div>
            <div className="text-center p-3 bg-emerald-400/[0.06] rounded-lg flex-1">
              <p className="text-xl font-bold text-emerald-700">{mandatoryDisclosed}/{mandatoryPrinciples.length}</p>
              <p className="text-xs text-white/40">Mandatory Disclosed</p>
            </div>
          </div>
        </div>

        <div className="space-y-3">
          {BRSR_PRINCIPLES.map(p => (
            <div key={p.id} className="border border-white/[0.06] rounded-xl p-4">
              <div className="flex items-start gap-3 mb-3">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                  readiness[p.id]?.status === 'disclosed' ? 'bg-emerald-100 text-emerald-700' :
                  readiness[p.id]?.status === 'in_progress' ? 'bg-blue-400/10 text-blue-300' :
                  'bg-white/[0.06] text-white/40'
                }`}>{p.id.replace('p','')}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-white/90">{p.label}</span>
                    {p.mandatory && <Badge label="Mandatory" color="bg-cyan-400/10 text-cyan-400" />}
                  </div>
                  <p className="text-[10px] text-white/30">{p.indicators.join(' · ')}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <select className={`border rounded px-2 py-1.5 text-xs w-48 focus:outline-none ${BRSR_READINESS_COLOR[readiness[p.id]?.status] || ''}`}
                  value={readiness[p.id]?.status}
                  onChange={e => set(p.id, 'status', e.target.value)}>
                  {BRSR_READINESS.map(r => <option key={r.v} value={r.v}>{r.l}</option>)}
                </select>
                <input className="flex-1 border border-white/[0.06] rounded px-2 py-1.5 text-xs focus:outline-none"
                  placeholder="Data sources / notes / data gaps"
                  value={readiness[p.id]?.notes || ''}
                  onChange={e => set(p.id, 'notes', e.target.value)} />
                <div>
                  <label className="text-[10px] text-white/30 mr-1">Score (0–10)</label>
                  <input type="number" min="0" max="10" className="border border-white/[0.06] rounded px-2 py-1 text-xs w-14 focus:outline-none"
                    value={readiness[p.id]?.score || 0}
                    onChange={e => set(p.id, 'score', Math.min(10, Math.max(0, parseInt(e.target.value) || 0)))} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card title="BRSR Core — Enhanced KPIs (FY2024 onwards)" subtitle="Mandatory BRSR Core indicators with third-party assurance requirement">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { label: 'Greenhouse Gas Footprint (Scope 1+2, tCO₂e/INR Cr turnover)', category: 'E' },
            { label: 'Water Intensity (kL/INR Cr turnover)', category: 'E' },
            { label: 'Energy Intensity (GJ/INR Cr turnover)', category: 'E' },
            { label: 'Waste Intensity (MT/INR Cr turnover)', category: 'E' },
            { label: 'Pay ratio — CEO to median employee remuneration', category: 'S' },
            { label: 'Diversity — women in workforce (%)', category: 'S' },
            { label: 'LTIFR (Lost Time Injury Frequency Rate)', category: 'S' },
            { label: 'Training coverage — employees (%)', category: 'S' },
            { label: 'Board independence (%)', category: 'G' },
            { label: 'CSR spend as % of net profit', category: 'G' },
          ].map((kpi, i) => (
            <div key={i} className={`p-3 rounded-lg border ${kpi.category === 'E' ? 'bg-emerald-500/10 border-emerald-500/20' : kpi.category === 'S' ? 'bg-blue-500/10 border-blue-500/20' : 'bg-purple-500/10 border-purple-500/20'}`}>
              <div className="flex items-center gap-2 mb-1">
                <span className={`text-[10px] font-bold px-1 py-0.5 rounded ${kpi.category === 'E' ? 'bg-emerald-500/20 text-emerald-300' : kpi.category === 'S' ? 'bg-blue-500/20 text-blue-300' : 'bg-purple-500/20 text-purple-300'}`}>{kpi.category}</span>
                <span className="text-xs font-medium text-white/70">{kpi.label}</span>
              </div>
              <input className="w-full border border-white/50 bg-[#0d1424] rounded px-2 py-1 text-xs focus:outline-none mt-1"
                placeholder="Enter value or 'N/A'" />
            </div>
          ))}
        </div>
        <p className="text-xs text-white/40 mt-4">
          BRSR Core KPIs require reasonable assurance from an independent third party (SEBI Circular CIR/CFD/CMD1/114/2023).
          Top 150 listed companies (by M-Cap) from FY2023-24, expanding to Top 1000 by FY2026-27.
        </p>
      </Card>
    </div>
  );
}

/* ── Sustainable Finance Taxonomies Panel ───────────────────────────────── */
const GLOBAL_TAXONOMIES = [
  {
    id: 'eu_taxonomy', name: 'EU Taxonomy', jurisdiction: 'European Union',
    status: 'In Force', year: 2020, objectives: 6, color: 'bg-blue-500/10 border-blue-500/20',
    badge: 'bg-blue-400/10 text-blue-300',
    description: 'First comprehensive green taxonomy globally. 6 environmental objectives, technical screening criteria, DNSH & minimum safeguards.',
    alignment: ['Paris Agreement', 'EU Green Deal', 'SFDR', 'NFRD/CSRD'],
    url_ref: 'EU Regulation 2020/852',
  },
  {
    id: 'uk_taxonomy', name: 'UK Green Taxonomy', jurisdiction: 'United Kingdom',
    status: 'Developing (2024)', year: 2022, objectives: 6, color: 'bg-red-500/10 border-red-500/20',
    badge: 'bg-red-500/10 text-red-700',
    description: 'Based on EU Taxonomy with UK-specific technical criteria. ISSB-aligned. Full implementation expected by 2025.',
    alignment: ['Paris Agreement', 'UK Green Finance Strategy', 'ISSB', 'TCFD'],
    url_ref: 'UK Green Finance Strategy 2023',
  },
  {
    id: 'singapore_taxonomy', name: 'Singapore Green Taxonomy', jurisdiction: 'Singapore',
    status: 'In Force (v2)', year: 2023, objectives: 8, color: 'bg-emerald-500/10 border-emerald-500/20',
    badge: 'bg-emerald-400/10 text-emerald-400',
    description: 'MAS-led taxonomy covering 8 sectors. Amber/transition tier included. ASEAN taxonomy compatible.',
    alignment: ['Paris Agreement', 'ASEAN Taxonomy', 'ISSB', 'TCFD'],
    url_ref: 'MAS Green Taxonomy v2 (2023)',
  },
  {
    id: 'asean_taxonomy', name: 'ASEAN Taxonomy', jurisdiction: 'ASEAN',
    status: 'In Force (v3)', year: 2023, objectives: 4, color: 'bg-teal-50 border-teal-200',
    badge: 'bg-teal-50 text-teal-700',
    description: 'Principle and Foundation Framework. Transition category included. Covers 6 focal sectors.',
    alignment: ['Paris Agreement', 'SDGs', 'ISSB', 'TCFD'],
    url_ref: 'ASEAN Taxonomy v3 (2023)',
  },
  {
    id: 'china_taxonomy', name: 'China Green Bond Endorsed Projects Catalogue', jurisdiction: 'China',
    status: 'In Force', year: 2021, objectives: 6, color: 'bg-amber-500/10 border-amber-200',
    badge: 'bg-amber-500/10 text-amber-700',
    description: 'PBoC/NDRC/CSRC catalogue. 6 categories (clean energy, energy saving, clean transport, etc.). Common Ground Taxonomy with EU.',
    alignment: ['Paris Agreement', 'China Peak Carbon & Carbon Neutral'],
    url_ref: 'PBoC 2021/Green Bond Catalogue',
  },
  {
    id: 'canada_taxonomy', name: 'Canada Taxonomy', jurisdiction: 'Canada',
    status: 'Pilot Phase', year: 2024, objectives: 5, color: 'bg-red-500/10 border-red-100',
    badge: 'bg-rose-50 text-rose-700',
    description: 'Sustainable Finance Action Council (SFAC) taxonomy. Transition finance inclusion. Net-zero aligned.',
    alignment: ['Paris Agreement', 'ISSB', 'TCFD', 'IFRS S2'],
    url_ref: 'SFAC Taxonomy Roadmap (2023)',
  },
  {
    id: 'australia_taxonomy', name: 'Australia Sustainable Finance Taxonomy', jurisdiction: 'Australia',
    status: 'Developing', year: 2024, objectives: 5, color: 'bg-yellow-50 border-yellow-200',
    badge: 'bg-yellow-50 text-yellow-700',
    description: 'ASFI-led framework. Transition finance explicitly included. Climate, biodiversity, water, circular economy.',
    alignment: ['Paris Agreement', 'ISSB', 'TCFD'],
    url_ref: 'ASFI Taxonomy Consultation (2024)',
  },
  {
    id: 'south_africa_taxonomy', name: 'SA Sustainable Finance Taxonomy', jurisdiction: 'South Africa',
    status: 'Developing', year: 2023, objectives: 4, color: 'bg-green-500/10 border-green-500/20',
    badge: 'bg-green-400/10 text-green-400',
    description: 'SBSA/National Treasury initiative. Just transition focus. Integration with African SDG frameworks.',
    alignment: ['Paris Agreement', 'SDGs', 'Just Transition'],
    url_ref: 'SBSA Taxonomy Discussion Paper (2023)',
  },
  {
    id: 'india_taxonomy', name: 'India Sustainable Finance Framework', jurisdiction: 'India',
    status: 'Developing', year: 2023, objectives: 5, color: 'bg-orange-500/10 border-orange-200',
    badge: 'bg-orange-500/10 text-orange-700',
    description: 'SEBI IFSC taxonomy and RBI sustainable finance guidelines. BRSR-linked. India\'s National Action Plan on Climate Change aligned.',
    alignment: ['Paris Agreement', 'BRSR', 'SDGs', 'India NDC'],
    url_ref: 'SEBI / RBI Sustainable Finance Guidelines',
  },
  {
    id: 'oecd_sustainable', name: 'OECD Sustainable Finance Taxonomy Guidance', jurisdiction: 'International',
    status: 'Guidance', year: 2020, objectives: null, color: 'bg-white/[0.02] border-white/[0.06]',
    badge: 'bg-white/[0.06] text-white/60',
    description: 'International comparability guidance. No binding criteria — framework for national taxonomy design.',
    alignment: ['Paris Agreement', 'SDGs', 'G20 SFWG'],
    url_ref: 'OECD Sustainable Finance Taxonomy 2020',
  },
];

function SustainableTaxonomyPanel() {
  const [selected, setSelected] = useState(null);
  const [portfolioTaxonomy, setPortfolioTaxonomy] = useState('eu_taxonomy');
  const [alignmentScores, setAlignmentScores] = useState({});

  const setScore = (tid, v) => setAlignmentScores(prev => ({ ...prev, [tid]: v }));

  const portfolioTax = GLOBAL_TAXONOMIES.find(t => t.id === portfolioTaxonomy);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="EU Taxonomy 2020/852" color="bg-blue-400/10 text-blue-300" />
        <Badge label="UK Green Taxonomy" color="bg-red-500/10 text-red-700" />
        <Badge label="ASEAN Taxonomy v3" color="bg-teal-50 text-teal-700" />
        <Badge label="Singapore MAS" color="bg-emerald-400/10 text-emerald-400" />
        <Badge label="Common Ground Taxonomy (EU-China)" color="bg-amber-500/10 text-amber-700" />
        <Badge label="ICMA Green Bond Principles" color="bg-white/[0.06] text-white/60" />
      </div>

      <Card title="Global Sustainable Finance Taxonomies — Comparison" subtitle="10 jurisdictions covered. Select a taxonomy for detailed information and self-assessment.">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {GLOBAL_TAXONOMIES.map(tax => (
            <div key={tax.id}
              onClick={() => setSelected(selected?.id === tax.id ? null : tax)}
              className={`border rounded-xl p-4 cursor-pointer transition-all hover:shadow-md ${tax.color} ${selected?.id === tax.id ? 'ring-2 ring-cyan-400/50' : ''}`}>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-bold text-white/90">{tax.name}</span>
                    <Badge label={tax.status} color={tax.badge} />
                  </div>
                  <p className="text-[10px] text-white/40">{tax.jurisdiction} · {tax.year} · {tax.objectives ? `${tax.objectives} objectives` : 'Multi-objective'}</p>
                </div>
                <span className="text-xs text-white/30">{selected?.id === tax.id ? '▲' : '▼'}</span>
              </div>
              <p className="text-xs text-white/60">{tax.description}</p>

              {selected?.id === tax.id && (
                <div className="mt-3 pt-3 border-t border-white/50">
                  <p className="text-[10px] font-semibold text-white/60 mb-1">Alignment Frameworks:</p>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {tax.alignment.map((a, i) => <Badge key={i} label={a} color="bg-[#0d1424]/70 text-white/60" />)}
                  </div>
                  <p className="text-[10px] text-white/40 mb-2">Reference: {tax.url_ref}</p>
                  <div className="flex items-center gap-2">
                    <label className="text-[10px] text-white/60 font-medium">Portfolio Alignment Score (0–100%):</label>
                    <input type="number" min="0" max="100"
                      className="border border-white/50 bg-[#0d1424] rounded px-2 py-1 text-xs w-20 focus:outline-none"
                      value={alignmentScores[tax.id] || ''}
                      onChange={e => setScore(tax.id, Math.min(100, Math.max(0, parseFloat(e.target.value) || 0)))}
                      placeholder="%" />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      <Card title="Portfolio Taxonomy Alignment Assessment" subtitle="Score your portfolio against a selected sustainable finance taxonomy">
        <div className="mb-4">
          <label className="block text-xs font-medium text-white/60 mb-1">Primary Taxonomy for Portfolio Assessment</label>
          <select className="border border-white/[0.06] rounded-lg px-3 py-2 text-sm w-72 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
            value={portfolioTaxonomy} onChange={e => setPortfolioTaxonomy(e.target.value)}>
            {GLOBAL_TAXONOMIES.map(t => <option key={t.id} value={t.id}>{t.name} ({t.jurisdiction})</option>)}
          </select>
        </div>

        {portfolioTax && (
          <div className={`border rounded-xl p-5 ${portfolioTax.color}`}>
            <h3 className="text-sm font-bold text-white/90 mb-1">{portfolioTax.name}</h3>
            <p className="text-xs text-white/60 mb-3">{portfolioTax.description}</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-[#0d1424] rounded-lg p-3 text-center">
                <p className="text-lg font-bold text-cyan-300">{portfolioTax.year}</p>
                <p className="text-[10px] text-white/40">Published</p>
              </div>
              <div className="bg-[#0d1424] rounded-lg p-3 text-center">
                <p className="text-lg font-bold text-emerald-700">{portfolioTax.objectives || 'Multi'}</p>
                <p className="text-[10px] text-white/40">Objectives</p>
              </div>
              <div className="bg-[#0d1424] rounded-lg p-3 text-center">
                <p className="text-sm font-bold text-blue-300">{portfolioTax.status}</p>
                <p className="text-[10px] text-white/40">Status</p>
              </div>
              <div className="bg-[#0d1424] rounded-lg p-3 text-center">
                <p className="text-lg font-bold text-purple-300">{alignmentScores[portfolioTax.id] || 0}%</p>
                <p className="text-[10px] text-white/40">Portfolio Aligned</p>
              </div>
            </div>
          </div>
        )}

        {/* Cross-taxonomy comparison if multiple scored */}
        {Object.keys(alignmentScores).length > 1 && (
          <div className="mt-5">
            <p className="text-xs font-semibold text-white/60 mb-3">Cross-Taxonomy Alignment Comparison</p>
            <div className="space-y-2">
              {GLOBAL_TAXONOMIES.filter(t => alignmentScores[t.id] != null).map(t => (
                <div key={t.id} className="flex items-center gap-3">
                  <span className="text-xs text-white/60 w-40 truncate">{t.name}</span>
                  <div className="flex-1 h-2 bg-white/[0.06] rounded-full">
                    <div className="h-full bg-cyan-400 rounded-full" style={{ width: `${alignmentScores[t.id]}%` }} />
                  </div>
                  <span className="text-xs font-bold text-cyan-300 w-10">{alignmentScores[t.id]}%</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

/* ── China ESG Intelligence Panel ───────────────────────────────────────── */
const CT_API_REG = process.env.REACT_APP_API_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const CT_BASE_REG = `${CT_API_REG}/api/v1/china-trade`;

function ChinaESGPanel() {
  const [csrdData, setCsrdData] = React.useState(null);
  const [scenarioData, setScenarioData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    Promise.all([
      fetch(`${CT_BASE_REG}/cross-module/regulatory-csrd`).then(r => r.json()).catch(() => null),
      fetch(`${CT_BASE_REG}/cross-module/scenario-cets-ngfs`).then(r => r.json()).catch(() => null),
    ]).then(([c, s]) => { setCsrdData(c); setScenarioData(s); setLoading(false); });
  }, []);

  if (loading) return <div className="text-center py-12 text-white/30 text-sm">Loading China ESG data…</div>;

  const COVERAGE_COLOR = (pct) =>
    pct >= 80 ? 'text-emerald-400' : pct >= 60 ? 'text-cyan-400' : pct >= 40 ? 'text-amber-400' : 'text-red-400';

  const NGFS_COLORS = { 'Net Zero 2050': '#10b981', 'Below 2 Degrees': '#6366f1', 'Delayed Transition': '#f59e0b', 'Current Policies': '#ef4444' };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h2 className="text-base font-bold text-white">China ESG Intelligence</h2>
          <p className="text-xs text-white/40 mt-0.5">
            SSE/SZSE 2024 mandatory ESG disclosures mapped to CSRD ESRS E1, SFDR PAI, and ISSB S2
          </p>
        </div>
        <div className="flex gap-2 flex-wrap text-[10px]">
          {["SSE/SZSE 2024","CSRD ESRS E1","SFDR PAI 1-7","ISSB S2","NDRC CETS"].map(b => (
            <span key={b} className="px-2 py-0.5 bg-cyan-500/10 text-cyan-400 rounded border border-cyan-500/20">{b}</span>
          ))}
        </div>
      </div>

      {/* CETS / ESG summary stats */}
      {csrdData && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
            <p className="text-xs text-white/40 mb-1">Entities Assessed</p>
            <p className="text-xl font-bold text-white">{csrdData.entity_count}</p>
            <p className="text-[10px] text-white/30">SSE/SZSE listed</p>
          </div>
          <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
            <p className="text-xs text-white/40 mb-1">Regulation</p>
            <p className="text-sm font-bold text-cyan-300">SSE/SZSE 2024</p>
            <p className="text-[10px] text-white/30">Mandatory ESG</p>
          </div>
          <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
            <p className="text-xs text-white/40 mb-1">Key Gaps</p>
            <p className="text-xl font-bold text-amber-400">{csrdData.key_gaps?.length}</p>
            <p className="text-[10px] text-white/30">vs CSRD requirements</p>
          </div>
          <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4">
            <p className="text-xs text-white/40 mb-1">Source</p>
            <p className="text-sm font-bold text-white/70">CSME 2024</p>
            <p className="text-[10px] text-white/30">Exchange guidelines</p>
          </div>
        </div>
      )}

      {/* Cross-standard mapping table */}
      {csrdData?.csrd_sfdr_issb_mapping && (
        <Card title="Cross-Standard Mapping — SSE/SZSE → CSRD / SFDR PAI / ISSB S2"
          subtitle={`${csrdData.regulation} · Effective: ${csrdData.effective_date}`}>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">China Disclosure</th>
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">CSRD ESRS</th>
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">SFDR PAI</th>
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">ISSB S2</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">Coverage</th>
                  <th className="text-left py-2 text-white/40 font-medium">Gap</th>
                </tr>
              </thead>
              <tbody>
                {csrdData.csrd_sfdr_issb_mapping.map((row, i) => (
                  <tr key={i} className="border-b border-white/[0.02]">
                    <td className="py-2.5 pr-4 text-white/70">{row.china_disclosure}</td>
                    <td className="py-2.5 pr-4 text-cyan-300/80 text-[10px] font-mono">{row.csrd_esrs}</td>
                    <td className="py-2.5 pr-4 text-blue-300/80 text-[10px]">{row.sfdr_pai}</td>
                    <td className="py-2.5 pr-4 text-purple-300/80 text-[10px]">{row.issb_s2}</td>
                    <td className={`py-2.5 pr-4 text-right font-bold ${COVERAGE_COLOR(row.coverage_pct)}`}>
                      {row.coverage_pct}%
                    </td>
                    <td className="py-2.5 text-amber-300/70 text-[10px]">{row.gap}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 pt-3 border-t border-white/[0.04]">
            <p className="text-xs text-white/40 font-medium mb-2">Material disclosure gaps (China vs CSRD)</p>
            <div className="flex flex-wrap gap-2">
              {(csrdData.key_gaps || []).map((g, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 bg-amber-500/10 text-amber-400 rounded border border-amber-500/20">{g}</span>
              ))}
            </div>
          </div>
        </Card>
      )}

      {/* NGFS × CETS scenario */}
      {scenarioData?.scenarios && (
        <Card title="CETS Price Trajectories — NGFS v4 Scenarios"
          subtitle={`China ETS transition risk overlay · Base: ¥${scenarioData.base_case_price_cny}/tCO2 (€${scenarioData.base_case_price_eur})`}>
          <div className="overflow-x-auto mb-4">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">NGFS Scenario</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">2025 (¥)</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">2030 (¥)</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">2035 (¥)</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">2040 (¥)</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">CBAM Arb. 2030 (€)</th>
                  <th className="text-left py-2 text-white/40 font-medium">Transition Risk</th>
                </tr>
              </thead>
              <tbody>
                {scenarioData.scenarios.map((s, i) => (
                  <tr key={i} className="border-b border-white/[0.02]">
                    <td className="py-2.5 pr-4 font-medium" style={{ color: NGFS_COLORS[s.ngfs_scenario] || '#fff' }}>
                      {s.ngfs_scenario}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-white/60">¥{s.cets_2025_cny}</td>
                    <td className="py-2.5 pr-4 text-right text-white/80 font-bold">¥{s.cets_2030_cny}</td>
                    <td className="py-2.5 pr-4 text-right text-white/60">¥{s.cets_2035_cny}</td>
                    <td className="py-2.5 pr-4 text-right text-white/60">¥{s.cets_2040_cny}</td>
                    <td className={`py-2.5 pr-4 text-right font-bold ${s.cbam_arbitrage_2030_eur > 30 ? 'text-red-400' : s.cbam_arbitrage_2030_eur > 15 ? 'text-amber-400' : 'text-emerald-400'}`}>
                      €{s.cbam_arbitrage_2030_eur}
                    </td>
                    <td className="py-2.5 text-white/50 text-[10px]">{s.transition_risk}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-white/[0.02] rounded-lg p-3">
              <p className="text-[10px] text-white/40 mb-1">China NDC Peak Emissions</p>
              <p className="text-lg font-bold text-white">{scenarioData.china_ndc_peak_year}</p>
            </div>
            <div className="bg-white/[0.02] rounded-lg p-3">
              <p className="text-[10px] text-white/40 mb-1">Carbon Neutrality Target</p>
              <p className="text-lg font-bold text-white">{scenarioData.china_ndc_neutrality_year}</p>
            </div>
          </div>
          <p className="text-[10px] text-white/20 mt-3 pt-2 border-t border-white/[0.04]">
            Sources: {scenarioData.source} · Full CETS data at <a href="/china-trade" className="text-cyan-400 hover:underline">/china-trade</a>
          </p>
        </Card>
      )}
    </div>
  );
}

/* ── Main Page ───────────────────────────────────────────────────────────── */
const PANELS = [
  { id: 'sfdr', label: 'SFDR PAI', sub: 'Principal Adverse Impact Indicators' },
  { id: 'taxonomy', label: 'EU Taxonomy', sub: 'Alignment Assessment' },
  { id: 'tcfd', label: 'TCFD Disclosure', sub: 'Climate Governance & Risk' },
  { id: 'csrd', label: 'CSRD / ESRS', sub: 'Readiness Tracker' },
  { id: 'issb', label: 'ISSB S1 / S2', sub: 'IFRS Sustainability Standards' },
  { id: 'brsr', label: 'BRSR', sub: 'India SEBI Disclosure' },
  { id: 'sf_taxonomies', label: 'Sustainable Finance Taxonomies', sub: '10 Global Jurisdictions' },
  { id: 'mas', label: 'MAS Regulatory', sub: 'ERM / Notice 637 / SGT / SLGS' },
  { id: 'transition_finance', label: 'Transition Finance', sub: 'EU Taxonomy / ICMA / CBI / SGT' },
  { id: 'slgs_tracker', label: 'SLGS Grant Tracker', sub: 'MAS CMG 02/2022' },
  { id: 'sec_climate', label: 'SEC Climate Rule', sub: 'US Reg S-K / S-X' },
  { id: 'uk_tcfd', label: 'UK Mandatory TCFD', sub: 'FCA PS21/23 / LR 9.8.6R' },
  { id: 'apra_cpg229', label: 'APRA CPG 229', sub: 'Climate Financial Risks' },
  { id: 'gri_305', label: 'GRI 305 Emissions', sub: 'Scope 1, 2, 3 GHG Standard' },
  { id: 'eudr', label: 'EUDR Compliance', sub: 'EU 2023/1115 Deforestation' },
  { id: 'eu_ets', label: 'EU ETS Phase 4', sub: 'Carbon Market Compliance' },
  { id: 'china_esg', label: 'China ESG Intelligence', sub: 'SSE/SZSE · CSRD · SFDR' },
];

export default function RegulatoryPage() {
  const [activePanel, setActivePanel] = useState('sfdr');

  return (
    <div className="flex flex-col h-full bg-white/[0.02]">
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-8 py-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Regulatory Reporting</h1>
            <p className="text-sm text-white/40 mt-0.5">
              SFDR, EU Taxonomy, TCFD, CSRD/ESRS, ISSB S1/S2, BRSR, SEC Climate Rule, UK TCFD, APRA CPG 229, GRI 305, EUDR, EU ETS Phase 4
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge label="SFDR 2019/2088" color="bg-blue-400/10 text-blue-300" />
            <Badge label="EU Taxonomy 2020/852" color="bg-emerald-400/10 text-emerald-400" />
            <Badge label="TCFD 2023" color="bg-purple-400/10 text-purple-300" />
            <Badge label="CSRD/ESRS" color="bg-cyan-400/10 text-cyan-300" />
            <Badge label="ISSB S1/S2" color="bg-blue-400/10 text-blue-300" />
            <Badge label="BRSR (SEBI)" color="bg-amber-500/10 text-amber-700" />
            <Badge label="SEC 33-7211" color="bg-purple-400/10 text-purple-300" />
            <Badge label="APRA CPG 229" color="bg-orange-500/10 text-orange-400" />
            <Badge label="GRI 305" color="bg-emerald-400/10 text-emerald-400" />
            <Badge label="EUDR 2023/1115" color="bg-green-400/10 text-green-400" />
            <Badge label="EU ETS Phase 4" color="bg-blue-400/10 text-blue-300" />
          </div>
        </div>
      </div>

      <div className="bg-[#0d1424] border-b border-white/[0.06] px-8 overflow-x-auto">
        <div className="flex gap-0 min-w-max">
          {PANELS.map(p => (
            <button key={p.id} onClick={() => setActivePanel(p.id)}
              className={`px-4 py-3.5 border-b-2 transition-all ${
                activePanel === p.id ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-white/40 hover:text-white/70 hover:border-white/20'
              }`}>
              <span className="text-xs font-semibold block whitespace-nowrap">{p.label}</span>
              <span className="text-[10px] text-white/30 whitespace-nowrap">{p.sub}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        {activePanel === 'sfdr' && <SFDRPanel />}
        {activePanel === 'taxonomy' && <EUTaxonomyPanel />}
        {activePanel === 'tcfd' && <TCFDPanel />}
        {activePanel === 'csrd' && <CSRDPanel />}
        {activePanel === 'issb' && <ISSBPanel />}
        {activePanel === 'brsr' && <BRSRPanel />}
        {activePanel === 'sf_taxonomies' && <SustainableTaxonomyPanel />}
        {activePanel === 'mas' && <MASPanel />}
        {activePanel === 'transition_finance' && <TransitionFinancePanel />}
        {activePanel === 'slgs_tracker' && <SLGSTrackerPanel />}
        {activePanel === 'sec_climate' && <SecClimatePanel />}
        {activePanel === 'uk_tcfd' && <UkTcfdPanel />}
        {activePanel === 'apra_cpg229' && <ApraCpg229Panel />}
        {activePanel === 'gri_305' && <Gri305Panel />}
        {activePanel === 'eudr' && <EudrPanel />}
        {activePanel === 'eu_ets' && <EuEtsPanel />}
        {activePanel === 'china_esg' && <ChinaESGPanel />}
      </div>
    </div>
  );
}
