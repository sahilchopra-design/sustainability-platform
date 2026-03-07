/**
 * IRENA Five Pillars Energy Transition Assessment Panel
 * Based on: IRENA World Energy Transitions Outlook 2023
 *           IRENA Energy Transition Readiness Assessment Framework
 *
 * Five Pillars:
 *   1. Physical Infrastructure (grid, storage, interconnectors)
 *   2. Policy & Regulation (RE targets, carbon pricing, subsidy reform)
 *   3. Financing & Investment (green bonds, blended finance, risk mitigation)
 *   4. Human Capital & Institutional Capacity (skills, R&D, workforce)
 *   5. Technology & Innovation (RE deployment, efficiency, digitalisation)
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadialBarChart, RadialBar, Cell,
} from 'recharts';

const API = 'http://localhost:8001/api/v1/irena-five-pillars';

const RATING_COLORS = {
  'Advanced': '#22c55e',
  'Progressing': '#3b82f6',
  'Emerging': '#eab308',
  'Early Stage': '#ef4444',
};

const READINESS_COLORS = {
  'Transition-Ready': '#22c55e',
  'On Track': '#3b82f6',
  'Needs Acceleration': '#eab308',
  'Significant Gaps': '#ef4444',
};

const KPI = ({ label, value, sub, accent }) => (
  <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
    <div className={`text-2xl font-bold ${accent || 'text-white'}`}>{value}</div>
    <div className="text-[11px] text-white/40 mt-1">{label}</div>
    {sub && <div className="text-[10px] text-white/25 mt-0.5">{sub}</div>}
  </div>
);

export function IrenaFivePillarsPanel() {
  const [framework, setFramework] = useState(null);
  const [form, setForm] = useState({
    entity_name: 'Country Assessment',
    entity_type: 'country',
    country_iso2: 'DE',
    assessment_year: 2025,
    notes: '',
  });
  const [scores, setScores] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load framework on mount
  useEffect(() => {
    axios.get(`${API}/framework`).then(r => {
      setFramework(r.data.pillars);
      // Initialize all scores to 5
      const init = {};
      for (const p of r.data.pillars) {
        init[p.id] = {};
        for (const c of p.criteria) {
          init[p.id][c.id] = 5;
        }
      }
      setScores(init);
    }).catch(() => {});
  }, []);

  const setScore = (pillarId, critId, val) => {
    setScores(s => ({
      ...s,
      [pillarId]: { ...s[pillarId], [critId]: Math.min(10, Math.max(0, Number(val) || 0)) },
    }));
  };

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const pillar_scores = Object.entries(scores).map(([pillar_id, s]) => ({
        pillar_id,
        scores: s,
      }));
      const { data } = await axios.post(`${API}/assess`, { ...form, pillar_scores });
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  // Build radar data from result
  const radarData = result?.pillar_results?.map(p => ({
    pillar: p.name.split(' ')[0],
    fullName: p.name,
    score: p.pct,
  })) || [];

  // Build per-pillar bar data
  const pillarBars = result?.pillar_results?.map(p => ({
    name: p.name.length > 18 ? p.name.substring(0, 18) + '..' : p.name,
    fullName: p.name,
    pct: p.pct,
    weighted: p.weighted_score,
    fill: RATING_COLORS[p.rating] || '#666',
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
        <h2 className="text-xl font-bold text-white">IRENA Five Pillars Transition Readiness</h2>
        <p className="text-xs text-white/40 mt-1">
          IRENA World Energy Transitions Outlook 2023 / Energy Transition Readiness Assessment Framework
        </p>
      </div>

      {/* Entity Info */}
      <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
        <h3 className="text-sm font-semibold text-white/70 mb-4">Assessment Entity</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="text-[11px] text-white/40 block mb-1">Entity Name</label>
            <input type="text" value={form.entity_name}
              onChange={e => setForm(f => ({ ...f, entity_name: e.target.value }))}
              className="w-full bg-[#1a2332] border border-white/[0.08] rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[11px] text-white/40 block mb-1">Entity Type</label>
            <select value={form.entity_type}
              onChange={e => setForm(f => ({ ...f, entity_type: e.target.value }))}
              className="w-full bg-[#1a2332] border border-white/[0.08] rounded px-2 py-1.5 text-sm text-white">
              <option value="country">Country</option>
              <option value="organisation">Organisation</option>
              <option value="project">Project</option>
            </select>
          </div>
          <div>
            <label className="text-[11px] text-white/40 block mb-1">Country (ISO2)</label>
            <input type="text" value={form.country_iso2} maxLength={2}
              onChange={e => setForm(f => ({ ...f, country_iso2: e.target.value.toUpperCase() }))}
              className="w-full bg-[#1a2332] border border-white/[0.08] rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[11px] text-white/40 block mb-1">Assessment Year</label>
            <input type="number" value={form.assessment_year}
              onChange={e => setForm(f => ({ ...f, assessment_year: Number(e.target.value) }))}
              className="w-full bg-[#1a2332] border border-white/[0.08] rounded px-2 py-1.5 text-sm text-white" />
          </div>
        </div>
      </div>

      {/* Scoring Grid */}
      {framework && (
        <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
          <h3 className="text-sm font-semibold text-white/70 mb-4">
            Pillar Scores (0-10 per criterion)
          </h3>
          <div className="space-y-6">
            {framework.map(pillar => (
              <div key={pillar.id}>
                <div className="flex items-baseline gap-2 mb-3">
                  <span className="text-sm font-semibold text-white">{pillar.name}</span>
                  <span className="text-[10px] text-white/30">Weight: {(pillar.weight * 100).toFixed(0)}%</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                  {pillar.criteria.map(crit => (
                    <div key={crit.id}>
                      <label className="text-[10px] text-white/40 block mb-1">{crit.label}</label>
                      <input
                        type="range" min={0} max={crit.max} step={0.5}
                        value={scores[pillar.id]?.[crit.id] || 0}
                        onChange={e => setScore(pillar.id, crit.id, e.target.value)}
                        className="w-full accent-blue-500"
                      />
                      <div className="text-center text-xs text-white/60 mt-0.5">
                        {scores[pillar.id]?.[crit.id] || 0} / {crit.max}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <button onClick={run} disabled={loading}
            className="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium disabled:opacity-40 transition-colors">
            {loading ? 'Assessing...' : 'Run Five Pillars Assessment'}
          </button>
          {error && <div className="mt-3 text-sm text-red-400">{error}</div>}
        </div>
      )}

      {/* Results */}
      {result && (
        <>
          {/* Overall KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <KPI label="Overall Score"
              value={`${result.overall_pct}%`}
              sub={`${result.overall_score} / ${result.overall_max}`}
              accent={`text-[${RATING_COLORS[result.overall_rating]}]`} />
            <KPI label="Overall Rating" value={result.overall_rating}
              accent={result.overall_rating === 'Advanced' ? 'text-green-400' :
                result.overall_rating === 'Progressing' ? 'text-blue-400' :
                result.overall_rating === 'Emerging' ? 'text-amber-400' : 'text-red-400'} />
            <KPI label="Transition Readiness" value={result.transition_readiness}
              accent={result.transition_readiness === 'Transition-Ready' ? 'text-green-400' :
                result.transition_readiness === 'On Track' ? 'text-blue-400' :
                result.transition_readiness === 'Needs Acceleration' ? 'text-amber-400' : 'text-red-400'} />
            <KPI label="Entity" value={result.entity_name}
              sub={`${result.country_iso2} | ${result.assessment_year}`} />
          </div>

          {/* Radar + Bar Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Radar */}
            <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
              <h3 className="text-sm font-semibold text-white/70 mb-4">Five Pillars Radar</h3>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#ffffff10" />
                  <PolarAngleAxis dataKey="pillar" tick={{ fill: '#ffffff80', fontSize: 10 }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={{ fill: '#ffffff40', fontSize: 9 }} />
                  <Radar name="Score %" dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25} strokeWidth={2} />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Pillar Scores Bar */}
            <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
              <h3 className="text-sm font-semibold text-white/70 mb-4">Pillar Scores (%)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={pillarBars} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
                  <XAxis type="number" domain={[0, 100]} tick={{ fill: '#ffffff60', fontSize: 10 }} />
                  <YAxis dataKey="name" type="category" tick={{ fill: '#ffffff60', fontSize: 10 }} width={120} />
                  <Tooltip contentStyle={{ background: '#111827', border: '1px solid #ffffff15', borderRadius: 8, fontSize: 11 }}
                    formatter={(v, n) => [`${v}%`, n]} />
                  <Bar dataKey="pct" name="Score %">
                    {pillarBars.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Pillar Detail Cards */}
          <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
            <h3 className="text-sm font-semibold text-white/70 mb-4">Pillar Details</h3>
            <div className="space-y-4">
              {result.pillar_results.map(p => (
                <div key={p.id} className="bg-[#111827] rounded-lg border border-white/[0.04] p-4">
                  <div className="flex items-baseline justify-between mb-3">
                    <div>
                      <span className="text-sm font-semibold text-white">{p.name}</span>
                      <span className="text-[10px] text-white/30 ml-2">Weight: {(p.weight * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold" style={{ color: RATING_COLORS[p.rating] }}>
                        {p.pct}%
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded"
                        style={{ background: RATING_COLORS[p.rating] + '20', color: RATING_COLORS[p.rating] }}>
                        {p.rating}
                      </span>
                    </div>
                  </div>
                  {/* Progress bar */}
                  <div className="w-full bg-white/[0.05] rounded-full h-1.5 mb-3">
                    <div className="h-1.5 rounded-full transition-all"
                      style={{ width: `${p.pct}%`, background: RATING_COLORS[p.rating] }} />
                  </div>
                  {/* Criteria */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                    {p.criteria.map(c => (
                      <div key={c.id} className="text-center">
                        <div className={`text-xs font-bold ${c.pct >= 60 ? 'text-green-400' : c.pct >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
                          {c.score}/{c.max_score}
                        </div>
                        <div className="text-[9px] text-white/30 mt-0.5 leading-tight">{c.label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Gap Analysis */}
          {result.gap_analysis.length > 0 && (
            <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
              <h3 className="text-sm font-semibold text-white/70 mb-4">
                Gap Analysis (below 50%)
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-white/40 border-b border-white/[0.06]">
                      <th className="text-left py-2 px-2">Pillar</th>
                      <th className="text-left py-2 px-2">Criterion</th>
                      <th className="text-right py-2 px-2">Score</th>
                      <th className="text-right py-2 px-2">Max</th>
                      <th className="text-right py-2 px-2">%</th>
                      <th className="text-right py-2 px-2">Gap to 50%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.gap_analysis.map((g, i) => (
                      <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                        <td className="py-2 px-2 text-white/60">{g.pillar}</td>
                        <td className="py-2 px-2 text-white">{g.criterion}</td>
                        <td className="py-2 px-2 text-right text-red-400">{g.score}</td>
                        <td className="py-2 px-2 text-right text-white/40">{g.max}</td>
                        <td className="py-2 px-2 text-right text-red-400">{g.pct}%</td>
                        <td className="py-2 px-2 text-right text-amber-400">+{g.gap_to_50pct}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Recommendations */}
          {result.recommendations.length > 0 && (
            <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
              <h3 className="text-sm font-semibold text-white/70 mb-4">Recommendations</h3>
              <div className="space-y-2">
                {result.recommendations.map((r, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className="text-blue-400 mt-0.5 text-xs">{i + 1}.</span>
                    <span className="text-sm text-white/80">{r}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Country Benchmarks */}
          {result.country_benchmarks && Object.keys(result.country_benchmarks).length > 0 && (
            <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-6">
              <h3 className="text-sm font-semibold text-white/70 mb-4">
                Country Benchmarks
                {result.country_benchmarks.country_name &&
                  ` -- ${result.country_benchmarks.country_name}`}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(result.country_benchmarks)
                  .filter(([k]) => k !== 'country_name')
                  .map(([idx, val]) => (
                    <div key={idx} className="bg-[#111827] rounded-lg p-3 text-center">
                      <div className="text-lg font-bold text-white">
                        {val.score !== null ? val.score.toFixed(1) : 'N/A'}
                      </div>
                      <div className="text-[10px] text-white/40 mt-1">{idx}</div>
                      {val.rank && <div className="text-[10px] text-white/25">Rank: {val.rank}</div>}
                    </div>
                  ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default IrenaFivePillarsPanel;
