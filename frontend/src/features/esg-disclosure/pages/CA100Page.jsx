/**
 * CA100+ Net Zero Company Benchmark Page
 * Climate Action 100+ assessment scores for 169 focus companies.
 * Sources: Climate Action 100+ Net Zero Company Benchmark 2025
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

/* ── Palette ───────────────────────────────────────────────────────────────── */
const SECTOR_COLORS = [
  '#6366f1', '#06b6d4', '#10b981', '#f59e0b', '#ef4444',
  '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', '#64748b',
];

const ASSESSMENT_COLORS = {
  'Partially Aligned': '#f59e0b',
  'Not Aligned': '#ef4444',
  'Aligned': '#10b981',
  'Not Assessed': '#475569',
};

/* ── Reusable Components ───────────────────────────────────────────────────── */
function Card({ title, subtitle, badge, children, className = '' }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            {title && <h2 className="text-sm font-semibold text-gray-900">{title}</h2>}
            {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {badge && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-700 border border-gray-200">
              {badge}
            </span>
          )}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}

function StatCard({ label, value, sub, color = 'text-gray-900' }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
      <p className="text-xs text-gray-500 font-medium mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </p>
      {sub && <p className="text-[11px] text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

function Spinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="w-8 h-8 border-2 border-black border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

/* ── Indicator Short Labels ─────────────────────────────────────────────── */
const INDICATOR_SHORT = {
  indicator_1: 'Net Zero 2050',
  indicator_2: 'Long-term Target',
  indicator_3: 'Medium-term Target',
  indicator_4: 'Short-term Target',
  indicator_5: 'Decarb Strategy',
  indicator_6: 'Capital Alignment',
  indicator_7: 'Policy Engagement',
  indicator_8: 'Governance',
  indicator_9: 'Just Transition',
  indicator_10: 'TCFD Disclosure',
};

/* ── Tab Pill ───────────────────────────────────────────────────────────── */
function TabPill({ tabs, active, onChange }) {
  return (
    <div className="inline-flex bg-[#f0f0f0] rounded-lg p-1 border border-gray-200">
      {tabs.map(t => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all ${
            active === t.id
              ? 'bg-gray-100 text-gray-700 border border-gray-300'
              : 'text-gray-500 hover:text-gray-600'
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
export default function CA100Page() {
  const [tab, setTab] = useState('overview');
  const [companies, setCompanies] = useState([]);
  const [total, setTotal] = useState(0);
  const [sectors, setSectors] = useState(null);
  const [filters, setFilters] = useState(null);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [companyDetail, setCompanyDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  // Filters state
  const [searchQ, setSearchQ] = useState('');
  const [filterSector, setFilterSector] = useState('');
  const [filterRegion, setFilterRegion] = useState('');
  const [page, setPage] = useState(0);
  const LIMIT = 25;

  /* ── Load initial data ───────────────────────────────────────────── */
  const loadCompanies = useCallback(async () => {
    try {
      const params = new URLSearchParams({ limit: LIMIT, offset: page * LIMIT });
      if (searchQ) params.set('q', searchQ);
      if (filterSector) params.set('sector_cluster', filterSector);
      if (filterRegion) params.set('hq_region', filterRegion);

      const { data } = await axios.get(`${API}/api/v1/ca100/companies?${params}`);
      setCompanies(data.companies || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('CA100 companies load error:', err);
    }
  }, [searchQ, filterSector, filterRegion, page]);

  useEffect(() => {
    async function init() {
      setLoading(true);
      try {
        const [filtersRes, sectorsRes] = await Promise.all([
          axios.get(`${API}/api/v1/ca100/filters`),
          axios.get(`${API}/api/v1/ca100/sectors`),
        ]);
        setFilters(filtersRes.data);
        setSectors(sectorsRes.data);
      } catch (err) {
        console.error('CA100 init error:', err);
      }
      setLoading(false);
    }
    init();
  }, []);

  useEffect(() => { loadCompanies(); }, [loadCompanies]);

  const loadDetail = useCallback(async (id) => {
    try {
      const { data } = await axios.get(`${API}/api/v1/ca100/companies/${id}`);
      setCompanyDetail(data);
      setSelectedCompany(id);
    } catch (err) {
      console.error('CA100 detail error:', err);
    }
  }, []);

  if (loading) return <div className="p-8"><Spinner /></div>;

  /* ── Sector Pie Data ──────────────────────────────────────────── */
  const sectorPieData = sectors?.sector_clusters?.map(sc => ({
    name: sc.sector_cluster,
    value: sc.company_count,
  })) || [];

  /* ── Sector Bar Data ──────────────────────────────────────────── */
  const sectorBarData = sectors?.sector_clusters?.flatMap(sc =>
    Object.entries(sc.sectors || {}).map(([sec, cnt]) => ({
      sector: sec,
      cluster: sc.sector_cluster,
      companies: cnt,
    }))
  ).sort((a, b) => b.companies - a.companies).slice(0, 15) || [];

  const TABS = [
    { id: 'overview', label: 'Overview' },
    { id: 'companies', label: 'Companies' },
    { id: 'detail', label: 'Company Detail' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            Climate Action 100+ Net Zero Benchmark
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Assessment of {total} focus companies against 10 net-zero indicators
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded">
            2025 BENCHMARK
          </span>
          <span className="text-[10px] font-bold bg-violet-500/10 text-violet-400 border border-violet-500/20 px-2 py-0.5 rounded">
            CA100+
          </span>
        </div>
      </div>

      {/* Tabs */}
      <TabPill tabs={TABS} active={tab} onChange={setTab} />

      {/* ── OVERVIEW TAB ─────────────────────────────────────────────── */}
      {tab === 'overview' && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Companies" value={sectors?.total_companies || 0} color="text-gray-700" />
            <StatCard label="Sector Clusters" value={sectors?.sector_clusters?.length || 0} color="text-violet-400" />
            <StatCard
              label="Sectors Covered"
              value={filters?.sectors?.length || 0}
              color="text-emerald-400"
            />
            <StatCard
              label="Regions"
              value={filters?.hq_regions?.length || 0}
              color="text-amber-400"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Sector Cluster Distribution */}
            <Card title="Sector Cluster Distribution" subtitle="Companies by sector cluster">
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={sectorPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={120}
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    labelLine={false}
                  >
                    {sectorPieData.map((_, i) => (
                      <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: '#ffffff', border: '1px solid rgba(0,0,0,0.1)', borderRadius: 8 }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </Card>

            {/* Top Sectors Bar */}
            <Card title="Top 15 Sectors" subtitle="Company count by specific sector">
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={sectorBarData} layout="vertical" margin={{ left: 100 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis type="number" stroke="rgba(255,255,255,0.2)" tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} />
                  <YAxis
                    type="category"
                    dataKey="sector"
                    width={95}
                    stroke="rgba(255,255,255,0.2)"
                    tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 10 }}
                  />
                  <Tooltip
                    contentStyle={{ background: '#ffffff', border: '1px solid rgba(0,0,0,0.1)', borderRadius: 8 }}
                    itemStyle={{ color: '#e2e8f0' }}
                  />
                  <Bar dataKey="companies" fill="#6366f1" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>

          {/* Region Overview */}
          <Card title="Regional Breakdown" subtitle="Number of focus companies per HQ region">
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
              {(filters?.hq_regions || []).map(reg => {
                const cnt = companies.length ? '...' : '-';
                return (
                  <div key={reg} className="bg-white rounded-lg p-3 border border-gray-200 text-center">
                    <p className="text-[10px] text-gray-500 mb-1 truncate">{reg}</p>
                    <p className="text-lg font-bold text-gray-800">{cnt}</p>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      )}

      {/* ── COMPANIES TAB ─────────────────────────────────────────── */}
      {tab === 'companies' && (
        <div className="space-y-4">
          {/* Filters */}
          <Card>
            <div className="flex flex-wrap gap-3 items-end">
              <div className="flex-1 min-w-[200px]">
                <label className="text-[10px] text-gray-500 font-medium block mb-1">Search</label>
                <input
                  type="text"
                  value={searchQ}
                  onChange={e => { setSearchQ(e.target.value); setPage(0); }}
                  placeholder="Company name or ISIN..."
                  className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="w-48">
                <label className="text-[10px] text-gray-500 font-medium block mb-1">Sector Cluster</label>
                <select
                  value={filterSector}
                  onChange={e => { setFilterSector(e.target.value); setPage(0); }}
                  className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Clusters</option>
                  {(filters?.sector_clusters || []).map(sc => (
                    <option key={sc} value={sc}>{sc}</option>
                  ))}
                </select>
              </div>
              <div className="w-44">
                <label className="text-[10px] text-gray-500 font-medium block mb-1">Region</label>
                <select
                  value={filterRegion}
                  onChange={e => { setFilterRegion(e.target.value); setPage(0); }}
                  className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-800 focus:outline-none focus:border-blue-500"
                >
                  <option value="">All Regions</option>
                  {(filters?.hq_regions || []).map(r => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={() => { setSearchQ(''); setFilterSector(''); setFilterRegion(''); setPage(0); }}
                className="px-3 py-2 text-xs text-gray-500 hover:text-gray-700 border border-gray-300 rounded-lg"
              >
                Clear
              </button>
            </div>
          </Card>

          {/* Results Count */}
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-500">
              Showing {page * LIMIT + 1}–{Math.min((page + 1) * LIMIT, total)} of {total} companies
            </p>
            <div className="flex gap-2">
              <button
                disabled={page === 0}
                onClick={() => setPage(p => p - 1)}
                className="px-3 py-1 text-xs rounded bg-gray-50 text-gray-500 disabled:opacity-30 hover:bg-gray-50"
              >
                Prev
              </button>
              <button
                disabled={(page + 1) * LIMIT >= total}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1 text-xs rounded bg-gray-50 text-gray-500 disabled:opacity-30 hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          </div>

          {/* Table */}
          <Card>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">Company</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">ISIN</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">Sector</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">Region</th>
                    <th className="text-left py-3 px-3 text-gray-500 font-medium">Assessment</th>
                    <th className="text-center py-3 px-3 text-gray-500 font-medium">Year</th>
                    <th className="text-center py-3 px-3 text-gray-500 font-medium">Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map(c => (
                    <tr key={c.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="py-2.5 px-3 text-gray-800 font-medium">{c.company_name}</td>
                      <td className="py-2.5 px-3 text-gray-500 font-mono text-[10px]">{c.isin || '-'}</td>
                      <td className="py-2.5 px-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-violet-500/10 text-violet-400 border border-violet-500/20">
                          {c.sector || c.sector_cluster || '-'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-gray-500">{c.hq_region || '-'}</td>
                      <td className="py-2.5 px-3">
                        {c.overall_assessment ? (
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] border ${
                            c.overall_assessment === 'Aligned'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : c.overall_assessment === 'Partially Aligned'
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                              : 'bg-red-500/10 text-red-400 border-red-500/20'
                          }`}>
                            {c.overall_assessment}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-[10px]">Not Assessed</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-center text-gray-500">{c.assessment_year || '-'}</td>
                      <td className="py-2.5 px-3 text-center">
                        <button
                          onClick={() => { loadDetail(c.id); setTab('detail'); }}
                          className="text-gray-700 hover:text-gray-800 text-[10px] font-medium"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* ── DETAIL TAB ────────────────────────────────────────────── */}
      {tab === 'detail' && (
        <div className="space-y-6">
          {!companyDetail ? (
            <Card>
              <p className="text-gray-500 text-sm text-center py-12">
                Select a company from the Companies tab to view its detailed assessment.
              </p>
            </Card>
          ) : (
            <>
              {/* Company Header */}
              <Card>
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">{companyDetail.company_name}</h2>
                    <div className="flex gap-4 mt-2 text-xs text-gray-500">
                      <span>ISIN: <span className="text-gray-700 font-mono">{companyDetail.isin || 'N/A'}</span></span>
                      <span>HQ: <span className="text-gray-700">{companyDetail.hq_location || 'N/A'}</span></span>
                      <span>Region: <span className="text-gray-700">{companyDetail.hq_region || 'N/A'}</span></span>
                    </div>
                    <div className="flex gap-3 mt-2">
                      {companyDetail.sector_cluster && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-gray-800/10 text-gray-700 border border-black/20">
                          {companyDetail.sector_cluster}
                        </span>
                      )}
                      {companyDetail.sector && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-violet-500/10 text-violet-400 border border-violet-500/20">
                          {companyDetail.sector}
                        </span>
                      )}
                      {companyDetail.secondary_sector && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] bg-purple-500/10 text-purple-400 border border-purple-500/20">
                          2nd: {companyDetail.secondary_sector}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => setTab('companies')}
                    className="text-xs text-gray-500 hover:text-gray-700 border border-gray-300 rounded-lg px-3 py-1.5"
                  >
                    Back to List
                  </button>
                </div>
              </Card>

              {/* Indicator Scores */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="Net Zero Indicator Scores" subtitle="10-indicator assessment scorecard">
                  <div className="space-y-3">
                    {Object.entries(companyDetail.indicators || {}).map(([key, ind]) => {
                      const score = ind.score;
                      const scoreColor = score === 'Yes' || score === 'Aligned'
                        ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                        : score === 'Partial' || score === 'Partially Aligned'
                        ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                        : score === 'No' || score === 'Not Aligned'
                        ? 'bg-red-500/20 text-red-400 border-red-500/30'
                        : 'bg-gray-50 text-gray-500 border-gray-200';
                      return (
                        <div key={key} className="flex items-center justify-between py-2 border-b border-gray-100">
                          <div className="flex-1 min-w-0 pr-4">
                            <p className="text-xs text-gray-700 truncate">{ind.label}</p>
                            <p className="text-[10px] text-gray-500">{INDICATOR_SHORT[key]}</p>
                          </div>
                          <span className={`inline-flex items-center px-2.5 py-1 rounded text-[10px] font-medium border ${scoreColor}`}>
                            {score || 'N/A'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </Card>

                {/* Radar Chart */}
                <Card title="Indicator Radar" subtitle="Visual assessment coverage">
                  <ResponsiveContainer width="100%" height={360}>
                    <RadarChart
                      data={Object.entries(companyDetail.indicators || {}).map(([key, ind]) => ({
                        indicator: INDICATOR_SHORT[key] || key,
                        score: ind.score === 'Yes' || ind.score === 'Aligned' ? 3
                          : ind.score === 'Partial' || ind.score === 'Partially Aligned' ? 2
                          : ind.score === 'No' || ind.score === 'Not Aligned' ? 1
                          : 0,
                        fullMark: 3,
                      }))}
                    >
                      <PolarGrid stroke="rgba(255,255,255,0.08)" />
                      <PolarAngleAxis
                        dataKey="indicator"
                        tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 9 }}
                      />
                      <PolarRadiusAxis
                        angle={90}
                        domain={[0, 3]}
                        tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 9 }}
                      />
                      <Radar
                        name="Score"
                        dataKey="score"
                        stroke="#6366f1"
                        fill="#6366f1"
                        fillOpacity={0.25}
                        strokeWidth={2}
                      />
                      <Tooltip
                        contentStyle={{ background: '#ffffff', border: '1px solid rgba(0,0,0,0.1)', borderRadius: 8 }}
                        itemStyle={{ color: '#e2e8f0' }}
                        formatter={v => ['Not Assessed', 'No', 'Partial', 'Yes'][v] || v}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </Card>
              </div>

              {/* Scope 3 & Additional Info */}
              {companyDetail.scope3_category && (
                <Card title="Scope 3 Category" subtitle="CA100+ material scope 3 classification">
                  <p className="text-sm text-gray-700">{companyDetail.scope3_category}</p>
                </Card>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
