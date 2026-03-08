/**
 * Country Risk & Governance Page
 * Unified view of CPI, FSI, Freedom House FIW, UNDP GII and coal capacity data.
 * Sources: Transparency International, Fund for Peace, Freedom House, UNDP HDR, GEM
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, ScatterChart,
  Scatter, ZAxis,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

/* ── Palette ───────────────────────────────────────────────────────────────── */
const INDEX_COLORS = {
  CPI: '#10b981',
  FSI: '#ef4444',
  FH_FIW: '#6366f1',
  UNDP_GII: '#f59e0b',
};
const COMPARE_COLORS = ['#06b6d4', '#8b5cf6', '#f59e0b', '#ec4899', '#10b981'];

/* ── Reusable Components ───────────────────────────────────────────────────── */
function Card({ title, subtitle, badge, children, className = '' }) {
  return (
    <div className={`bg-[#0d1424] rounded-xl border border-white/[0.06] shadow-sm ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-white/[0.04] flex items-center justify-between">
          <div>
            {title && <h2 className="text-sm font-semibold text-white/90">{title}</h2>}
            {subtitle && <p className="text-xs text-white/40 mt-0.5">{subtitle}</p>}
          </div>
          {badge && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              {badge}
            </span>
          )}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}

function StatCard({ label, value, unit, sub, color = 'text-white' }) {
  return (
    <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] shadow-sm p-5">
      <p className="text-xs text-white/40 font-medium mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 1 }) : value}
        {unit && <span className="text-sm font-normal text-white/40 ml-1">{unit}</span>}
      </p>
      {sub && <p className="text-[11px] text-white/30 mt-1">{sub}</p>}
    </div>
  );
}

function Spinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

function TabPill({ tabs, active, onChange }) {
  return (
    <div className="inline-flex bg-[#0a0f1e] rounded-lg p-1 border border-white/[0.06] flex-wrap">
      {tabs.map(t => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
            active === t.id
              ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/30'
              : 'text-white/40 hover:text-white/60'
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
export default function CountryRiskPage() {
  const [tab, setTab] = useState('overview');
  const [indices, setIndices] = useState([]);
  const [loading, setLoading] = useState(true);

  // Rankings state
  const [selectedIndex, setSelectedIndex] = useState('CPI');
  const [rankings, setRankings] = useState(null);
  const [rankingsLoading, setRankingsLoading] = useState(false);

  // Country profile
  const [profileIso, setProfileIso] = useState('');
  const [profileData, setProfileData] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);

  // Comparison
  const [compareInput, setCompareInput] = useState('GBR,DEU,FRA,USA,JPN');
  const [compareIndex, setCompareIndex] = useState('');
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);

  // Coal
  const [coalData, setCoalData] = useState(null);
  const [coalSearch, setCoalSearch] = useState('');

  /* ── Init ────────────────────────────────────────────────────── */
  useEffect(() => {
    async function init() {
      setLoading(true);
      try {
        const { data } = await axios.get(`${API}/api/v1/country-risk/indices`);
        setIndices(data.indices || []);
      } catch (err) {
        console.error('Country risk init error:', err);
      }
      setLoading(false);
    }
    init();
  }, []);

  /* ── Load Rankings ───────────────────────────────────────────── */
  const loadRankings = useCallback(async (indexName) => {
    setRankingsLoading(true);
    try {
      const { data } = await axios.get(`${API}/api/v1/country-risk/rankings/${indexName}?limit=50`);
      setRankings(data);
    } catch (err) {
      console.error('Rankings error:', err);
    }
    setRankingsLoading(false);
  }, []);

  useEffect(() => {
    if (tab === 'rankings') loadRankings(selectedIndex);
  }, [tab, selectedIndex, loadRankings]);

  /* ── Load Country Profile ────────────────────────────────────── */
  const loadProfile = useCallback(async () => {
    if (!profileIso || profileIso.length < 3) return;
    setProfileLoading(true);
    try {
      const { data } = await axios.get(`${API}/api/v1/country-risk/country/${profileIso.toUpperCase()}`);
      setProfileData(data);
    } catch (err) {
      console.error('Profile error:', err);
      setProfileData(null);
    }
    setProfileLoading(false);
  }, [profileIso]);

  /* ── Load Compare ────────────────────────────────────────────── */
  const loadCompare = useCallback(async () => {
    if (!compareInput) return;
    setCompareLoading(true);
    try {
      const params = new URLSearchParams({ countries: compareInput });
      if (compareIndex) params.set('index_name', compareIndex);
      const { data } = await axios.get(`${API}/api/v1/country-risk/compare?${params}`);
      setCompareData(data);
    } catch (err) {
      console.error('Compare error:', err);
    }
    setCompareLoading(false);
  }, [compareInput, compareIndex]);

  /* ── Load Coal ───────────────────────────────────────────────── */
  const loadCoal = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: 100 });
      if (coalSearch) params.set('country', coalSearch);
      const { data } = await axios.get(`${API}/api/v1/country-risk/coal-capacity?${params}`);
      setCoalData(data);
    } catch (err) {
      console.error('Coal error:', err);
    }
  }, [coalSearch]);

  if (loading) return <div className="p-8"><Spinner /></div>;

  const TABS = [
    { id: 'overview', label: 'Overview' },
    { id: 'rankings', label: 'Rankings' },
    { id: 'profile', label: 'Country Profile' },
    { id: 'compare', label: 'Compare' },
    { id: 'coal', label: 'Coal Capacity' },
  ];

  /* ── Index Summary Data ──────────────────────────────────────── */
  const totalRecords = indices.reduce((s, i) => s + (i.record_count || 0), 0);

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white/90">Country Risk & Governance</h1>
          <p className="text-sm text-white/40 mt-1">
            {indices.length} indices covering {totalRecords.toLocaleString()} country-year records
          </p>
        </div>
        <div className="flex items-center gap-2">
          {Object.entries(INDEX_COLORS).map(([k, c]) => (
            <span
              key={k}
              className="text-[10px] font-bold px-2 py-0.5 rounded border"
              style={{ color: c, borderColor: `${c}33`, backgroundColor: `${c}11` }}
            >
              {k}
            </span>
          ))}
        </div>
      </div>

      <TabPill tabs={TABS} active={tab} onChange={setTab} />

      {/* ── OVERVIEW ──────────────────────────────────────────────── */}
      {tab === 'overview' && (
        <div className="space-y-6">
          {/* Index KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {indices.map(idx => (
              <div
                key={idx.index_name}
                className="bg-[#0d1424] rounded-xl border border-white/[0.06] shadow-sm p-5 cursor-pointer hover:border-cyan-500/20 transition-colors"
                onClick={() => { setSelectedIndex(idx.index_name); setTab('rankings'); }}
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className="text-[10px] font-bold px-2 py-0.5 rounded border"
                    style={{
                      color: INDEX_COLORS[idx.index_name] || '#94a3b8',
                      borderColor: `${INDEX_COLORS[idx.index_name] || '#94a3b8'}33`,
                      backgroundColor: `${INDEX_COLORS[idx.index_name] || '#94a3b8'}11`,
                    }}
                  >
                    {idx.index_name}
                  </span>
                  <span className="text-[10px] text-white/30">{idx.category}</span>
                </div>
                <p className="text-sm font-semibold text-white/80 mb-1">{idx.full_name}</p>
                <p className="text-[10px] text-white/30">{idx.source}</p>
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/[0.04]">
                  <div>
                    <p className="text-lg font-bold text-white/80">{idx.country_count}</p>
                    <p className="text-[10px] text-white/30">countries</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold text-white/60">{idx.year_range?.min}–{idx.year_range?.max}</p>
                    <p className="text-[10px] text-white/30">{idx.record_count?.toLocaleString()} records</p>
                  </div>
                </div>
                <p className="text-[10px] text-white/20 mt-2">{idx.scale}</p>
              </div>
            ))}
          </div>

          {/* Total Stats */}
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Total Records" value={totalRecords} color="text-cyan-400" />
            <StatCard label="Indices Available" value={indices.length} color="text-violet-400" />
            <StatCard
              label="Max Country Coverage"
              value={Math.max(...indices.map(i => i.country_count || 0))}
              sub="countries"
              color="text-emerald-400"
            />
          </div>
        </div>
      )}

      {/* ── RANKINGS ──────────────────────────────────────────────── */}
      {tab === 'rankings' && (
        <div className="space-y-4">
          <Card>
            <div className="flex items-center gap-4">
              <label className="text-xs text-white/40">Index:</label>
              {Object.keys(INDEX_COLORS).map(idx => (
                <button
                  key={idx}
                  onClick={() => setSelectedIndex(idx)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
                    selectedIndex === idx
                      ? 'border-cyan-500/30 bg-cyan-500/10 text-cyan-400'
                      : 'border-white/[0.06] text-white/40 hover:text-white/60'
                  }`}
                >
                  {idx}
                </button>
              ))}
            </div>
          </Card>

          {rankingsLoading ? <Spinner /> : rankings && (
            <>
              <div className="flex items-center justify-between">
                <p className="text-xs text-white/40">
                  {rankings.full_name} — {rankings.year} — Top 50 of {rankings.total} countries
                </p>
                <p className="text-[10px] text-white/20">{rankings.scale}</p>
              </div>

              {/* Bar Chart */}
              <Card title={`${rankings.index_name} Rankings ${rankings.year}`} subtitle={rankings.source}>
                <ResponsiveContainer width="100%" height={Math.max(400, (rankings.rankings?.length || 0) * 20)}>
                  <BarChart
                    data={(rankings.rankings || []).slice(0, 30)}
                    layout="vertical"
                    margin={{ left: 120 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis type="number" stroke="rgba(255,255,255,0.2)" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} />
                    <YAxis
                      type="category"
                      dataKey="country_name"
                      width={115}
                      stroke="rgba(255,255,255,0.2)"
                      tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10 }}
                    />
                    <Tooltip
                      contentStyle={{ background: '#0d1424', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                      itemStyle={{ color: '#e2e8f0' }}
                    />
                    <Bar
                      dataKey="score"
                      fill={INDEX_COLORS[rankings.index_name] || '#6366f1'}
                      radius={[0, 4, 4, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              {/* Table */}
              <Card>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-white/[0.06]">
                        <th className="text-left py-3 px-3 text-white/40 font-medium w-12">#</th>
                        <th className="text-left py-3 px-3 text-white/40 font-medium">Country</th>
                        <th className="text-left py-3 px-3 text-white/40 font-medium w-16">ISO3</th>
                        <th className="text-right py-3 px-3 text-white/40 font-medium w-20">Score</th>
                        <th className="text-center py-3 px-3 text-white/40 font-medium w-16">Rank</th>
                        <th className="text-center py-3 px-3 text-white/40 font-medium w-20">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(rankings.rankings || []).map(r => (
                        <tr key={r.country_iso3} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                          <td className="py-2 px-3 text-white/30">{r.rank}</td>
                          <td className="py-2 px-3 text-white/80 font-medium">{r.country_name}</td>
                          <td className="py-2 px-3 text-white/40 font-mono text-[10px]">{r.country_iso3}</td>
                          <td className="py-2 px-3 text-right">
                            <span className="font-bold" style={{ color: INDEX_COLORS[rankings.index_name] || '#e2e8f0' }}>
                              {r.score?.toFixed(1)}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-center text-white/40">{r.original_rank || r.rank}</td>
                          <td className="py-2 px-3 text-center">
                            <button
                              onClick={() => { setProfileIso(r.country_iso3); setTab('profile'); }}
                              className="text-cyan-400 hover:text-cyan-300 text-[10px] font-medium"
                            >
                              Profile
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </>
          )}
        </div>
      )}

      {/* ── COUNTRY PROFILE ───────────────────────────────────────── */}
      {tab === 'profile' && (
        <div className="space-y-4">
          <Card>
            <div className="flex items-end gap-3">
              <div className="flex-1 max-w-xs">
                <label className="text-[10px] text-white/40 font-medium block mb-1">Country ISO3 Code</label>
                <input
                  type="text"
                  value={profileIso}
                  onChange={e => setProfileIso(e.target.value.toUpperCase().slice(0, 3))}
                  placeholder="e.g. GBR, USA, DEU"
                  className="w-full bg-[#080e1c] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/80 font-mono placeholder:text-white/20 focus:outline-none focus:border-cyan-500/40"
                  maxLength={3}
                />
              </div>
              <button
                onClick={loadProfile}
                className="px-4 py-2 text-xs font-medium bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded-lg hover:bg-cyan-500/30 transition-colors"
              >
                Load Profile
              </button>
            </div>
          </Card>

          {profileLoading ? <Spinner /> : profileData && (
            <>
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-white/90">
                  {profileData.country_name} ({profileData.country_iso3})
                </h2>
                <span className="text-[10px] text-white/30">{profileData.indices?.length || 0} indices available</span>
              </div>

              {/* Latest Scores Overview */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {(profileData.indices || []).map(idx => (
                  <div
                    key={idx.index_name}
                    className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-5"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span
                        className="text-[10px] font-bold px-2 py-0.5 rounded border"
                        style={{
                          color: INDEX_COLORS[idx.index_name] || '#94a3b8',
                          borderColor: `${INDEX_COLORS[idx.index_name] || '#94a3b8'}33`,
                          backgroundColor: `${INDEX_COLORS[idx.index_name] || '#94a3b8'}11`,
                        }}
                      >
                        {idx.index_name}
                      </span>
                      <span className="text-[10px] text-white/30">{idx.latest_year}</span>
                    </div>
                    <p className="text-2xl font-bold" style={{ color: INDEX_COLORS[idx.index_name] || '#e2e8f0' }}>
                      {idx.latest_score?.toFixed(1) || 'N/A'}
                    </p>
                    <p className="text-[10px] text-white/30 mt-1">{idx.full_name}</p>
                    {idx.latest_rank && (
                      <p className="text-xs text-white/50 mt-1">Rank #{idx.latest_rank}</p>
                    )}
                  </div>
                ))}
              </div>

              {/* Time Series (for FH_FIW which has multi-year data) */}
              {(profileData.indices || []).filter(idx => idx.time_series?.length > 1).map(idx => (
                <Card
                  key={idx.index_name}
                  title={`${idx.full_name} Time Series`}
                  subtitle={`${idx.source} — ${idx.time_series.length} years`}
                >
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={[...idx.time_series].reverse()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="year" stroke="rgba(255,255,255,0.2)" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} />
                      <YAxis stroke="rgba(255,255,255,0.2)" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{ background: '#0d1424', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                        itemStyle={{ color: '#e2e8f0' }}
                      />
                      <Line
                        type="monotone"
                        dataKey="score"
                        stroke={INDEX_COLORS[idx.index_name] || '#6366f1'}
                        strokeWidth={2}
                        dot={{ r: 3 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              ))}

              {/* Coal Capacity */}
              {profileData.coal_capacity && (
                <Card title="Coal Plant Capacity" subtitle="GEM Coal Plant Tracker">
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                    {Object.entries(profileData.coal_capacity).map(([kpi, d]) => (
                      <div key={kpi} className="bg-[#080e1c] rounded-lg p-3 border border-white/[0.04]">
                        <p className="text-[10px] text-white/40 mb-1 truncate">{kpi.replace(/coal_capacity_/g, '').replace(/_/g, ' ')}</p>
                        <p className="text-lg font-bold text-amber-400">
                          {d.value?.toLocaleString() || 0}
                          <span className="text-xs font-normal text-white/30 ml-1">{d.unit}</span>
                        </p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Radar across indices (normalized) */}
              {profileData.indices?.length >= 2 && (
                <Card title="Multi-Index Radar" subtitle="Normalised scores across all available indices">
                  <ResponsiveContainer width="100%" height={320}>
                    <RadarChart
                      data={(profileData.indices || []).map(idx => {
                        // Normalise to 0-100 for radar
                        let norm = idx.latest_score || 0;
                        if (idx.index_name === 'FSI') norm = Math.max(0, 120 - norm); // Invert FSI
                        if (idx.index_name === 'FH_FIW') norm = Math.max(0, (14 - norm) / 14 * 100); // Invert FH
                        if (idx.index_name === 'UNDP_GII') norm = Math.max(0, (1 - norm) * 100); // Invert GII
                        return {
                          index: idx.index_name,
                          score: Math.round(norm * 10) / 10,
                          fullMark: 100,
                        };
                      })}
                    >
                      <PolarGrid stroke="rgba(255,255,255,0.08)" />
                      <PolarAngleAxis dataKey="index" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 9 }} />
                      <Radar
                        name="Normalised Score"
                        dataKey="score"
                        stroke="#06b6d4"
                        fill="#06b6d4"
                        fillOpacity={0.2}
                        strokeWidth={2}
                      />
                      <Tooltip
                        contentStyle={{ background: '#0d1424', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                        itemStyle={{ color: '#e2e8f0' }}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                  <p className="text-[10px] text-white/20 mt-2 text-center">
                    Higher = better governance. FSI, FH_FIW, and UNDP_GII scores inverted for comparability.
                  </p>
                </Card>
              )}
            </>
          )}
        </div>
      )}

      {/* ── COMPARE ───────────────────────────────────────────────── */}
      {tab === 'compare' && (
        <div className="space-y-4">
          <Card>
            <div className="flex items-end gap-3 flex-wrap">
              <div className="flex-1 min-w-[280px]">
                <label className="text-[10px] text-white/40 font-medium block mb-1">
                  Countries (comma-separated ISO3)
                </label>
                <input
                  type="text"
                  value={compareInput}
                  onChange={e => setCompareInput(e.target.value.toUpperCase())}
                  placeholder="GBR,DEU,FRA,USA,JPN"
                  className="w-full bg-[#080e1c] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/80 font-mono placeholder:text-white/20 focus:outline-none focus:border-cyan-500/40"
                />
              </div>
              <div className="w-40">
                <label className="text-[10px] text-white/40 font-medium block mb-1">Index (optional)</label>
                <select
                  value={compareIndex}
                  onChange={e => setCompareIndex(e.target.value)}
                  className="w-full bg-[#080e1c] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/80 focus:outline-none focus:border-cyan-500/40"
                >
                  <option value="">All Indices</option>
                  {indices.map(i => (
                    <option key={i.index_name} value={i.index_name}>{i.index_name} — {i.full_name}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={loadCompare}
                className="px-4 py-2 text-xs font-medium bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded-lg hover:bg-cyan-500/30 transition-colors"
              >
                Compare
              </button>
            </div>
          </Card>

          {compareLoading ? <Spinner /> : compareData && (
            <>
              {/* Bar comparison per index */}
              {(compareData.indices_included || []).map(idxName => {
                const chartData = (compareData.countries || []).map(c => {
                  const idxData = c.indices?.[idxName];
                  return {
                    country: `${c.country_name} (${c.country_iso3})`,
                    score: idxData?.latest?.score || 0,
                    rank: idxData?.latest?.rank,
                    year: idxData?.latest?.year,
                  };
                }).filter(d => d.score > 0);

                return (
                  <Card
                    key={idxName}
                    title={`${idxName} Comparison`}
                    subtitle={`Latest available year`}
                  >
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="country" stroke="rgba(255,255,255,0.2)" tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10 }} />
                        <YAxis stroke="rgba(255,255,255,0.2)" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} />
                        <Tooltip
                          contentStyle={{ background: '#0d1424', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                          itemStyle={{ color: '#e2e8f0' }}
                          formatter={(v, n, p) => [`Score: ${v?.toFixed(1)}, Rank: ${p.payload.rank || '-'}`, idxName]}
                        />
                        <Bar dataKey="score" fill={INDEX_COLORS[idxName] || '#6366f1'} radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </Card>
                );
              })}

              {/* Summary Table */}
              <Card title="Comparison Summary">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-white/[0.06]">
                        <th className="text-left py-3 px-3 text-white/40 font-medium">Country</th>
                        {(compareData.indices_included || []).map(idx => (
                          <th key={idx} className="text-center py-3 px-3 text-white/40 font-medium">{idx}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(compareData.countries || []).map((c, ci) => (
                        <tr key={c.country_iso3} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                          <td className="py-2 px-3 text-white/80 font-medium">
                            {c.country_name}
                            <span className="text-white/30 ml-1 font-mono text-[10px]">({c.country_iso3})</span>
                          </td>
                          {(compareData.indices_included || []).map(idx => {
                            const d = c.indices?.[idx];
                            return (
                              <td key={idx} className="py-2 px-3 text-center">
                                {d?.latest ? (
                                  <div>
                                    <span className="font-bold" style={{ color: INDEX_COLORS[idx] || '#e2e8f0' }}>
                                      {d.latest.score?.toFixed(1)}
                                    </span>
                                    {d.latest.rank && (
                                      <span className="text-white/20 text-[10px] ml-1">#{d.latest.rank}</span>
                                    )}
                                  </div>
                                ) : <span className="text-white/20">-</span>}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </>
          )}
        </div>
      )}

      {/* ── COAL CAPACITY ─────────────────────────────────────────── */}
      {tab === 'coal' && (
        <div className="space-y-4">
          <Card>
            <div className="flex items-end gap-3">
              <div className="flex-1 max-w-xs">
                <label className="text-[10px] text-white/40 font-medium block mb-1">Search Country</label>
                <input
                  type="text"
                  value={coalSearch}
                  onChange={e => setCoalSearch(e.target.value)}
                  placeholder="Country name..."
                  className="w-full bg-[#080e1c] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/80 placeholder:text-white/20 focus:outline-none focus:border-cyan-500/40"
                />
              </div>
              <button
                onClick={loadCoal}
                className="px-4 py-2 text-xs font-medium bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-lg hover:bg-amber-500/30 transition-colors"
              >
                Load Coal Data
              </button>
            </div>
          </Card>

          {coalData && (
            <>
              <p className="text-xs text-white/40">{coalData.total_countries} countries returned</p>

              {/* Coal Bar Chart — top countries by operating capacity */}
              <Card title="Coal Capacity by Country" subtitle="GEM Coal Plant Tracker — operating capacity">
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart
                    data={(coalData.countries || [])
                      .map(c => ({
                        country: c.country,
                        operating: c.capacities?.coal_capacity_operating?.value_mw || 0,
                        construction: c.capacities?.coal_capacity_construction?.value_mw || 0,
                        announced: c.capacities?.coal_capacity_announced?.value_mw || 0,
                      }))
                      .sort((a, b) => b.operating - a.operating)
                      .slice(0, 25)}
                    layout="vertical"
                    margin={{ left: 120 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis type="number" stroke="rgba(255,255,255,0.2)" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 10 }} />
                    <YAxis
                      type="category"
                      dataKey="country"
                      width={115}
                      stroke="rgba(255,255,255,0.2)"
                      tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10 }}
                    />
                    <Tooltip
                      contentStyle={{ background: '#0d1424', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
                      itemStyle={{ color: '#e2e8f0' }}
                      formatter={v => `${v?.toLocaleString()} MW`}
                    />
                    <Legend wrapperStyle={{ color: 'rgba(255,255,255,0.5)', fontSize: 11 }} />
                    <Bar dataKey="operating" name="Operating" fill="#ef4444" stackId="a" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="construction" name="Construction" fill="#f59e0b" stackId="a" />
                    <Bar dataKey="announced" name="Announced" fill="#64748b" stackId="a" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>

              {/* Table */}
              <Card>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-white/[0.06]">
                        <th className="text-left py-3 px-3 text-white/40 font-medium">Country</th>
                        <th className="text-right py-3 px-3 text-white/40 font-medium">Operating (MW)</th>
                        <th className="text-right py-3 px-3 text-white/40 font-medium">Construction</th>
                        <th className="text-right py-3 px-3 text-white/40 font-medium">Announced</th>
                        <th className="text-right py-3 px-3 text-white/40 font-medium">Retired</th>
                        <th className="text-right py-3 px-3 text-white/40 font-medium">Cancelled</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(coalData.countries || []).map(c => (
                        <tr key={c.country} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                          <td className="py-2 px-3 text-white/80 font-medium">{c.country}</td>
                          <td className="py-2 px-3 text-right text-red-400 font-mono">
                            {(c.capacities?.coal_capacity_operating?.value_mw || 0).toLocaleString()}
                          </td>
                          <td className="py-2 px-3 text-right text-amber-400 font-mono">
                            {(c.capacities?.coal_capacity_construction?.value_mw || 0).toLocaleString()}
                          </td>
                          <td className="py-2 px-3 text-right text-white/40 font-mono">
                            {(c.capacities?.coal_capacity_announced?.value_mw || 0).toLocaleString()}
                          </td>
                          <td className="py-2 px-3 text-right text-emerald-400 font-mono">
                            {(c.capacities?.coal_capacity_retired_since_2010?.value_mw || 0).toLocaleString()}
                          </td>
                          <td className="py-2 px-3 text-right text-cyan-400 font-mono">
                            {(c.capacities?.coal_capacity_cancelled_since_2010?.value_mw || 0).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </>
          )}
        </div>
      )}
    </div>
  );
}
