/**
 * Portfolio Analytics Page
 * PCAF Standard v2.0 financed emissions · WACI · ITR · DQS · Glidepath · Scenarios
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Badge } from '../../../components/ui/badge';
import {
  LayoutDashboard, Building2, FileText, GitCompare,
  PieChart, Calendar, Leaf, Play, RefreshCw,
} from 'lucide-react';
import {
  PieChart as RechartsPieChart, Pie, Cell,
  ComposedChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

import { PortfolioSelector } from '../components/PortfolioSelector';
import { PortfolioDashboard } from '../components/PortfolioDashboard';
import { HoldingsTable } from '../components/HoldingsTable';
import { ReportGenerator } from '../components/ReportGenerator';
import { ScenarioComparison } from '../components/ScenarioComparison';
import { ScheduledReportsManager } from '../../../components/shared/ScheduledReportsManager';
import {
  usePortfolios,
  useDashboard,
  useHoldings,
  usePCAFResults,
  useRunPCAF,
  useWACIHistory,
} from '../hooks/usePortfolioAnalytics';

// ── Constants ─────────────────────────────────────────────────────────────────

/** DQS tier colour map — 1 = verified primary data (green), 5 = proxy estimate (red) */
const DQS_COLOURS = {
  1: '#10b981',
  2: '#34d399',
  3: '#f59e0b',
  4: '#f97316',
  5: '#ef4444',
};

const DQS_LABELS = {
  1: 'DQS 1 — Verified',
  2: 'DQS 2 — Reported',
  3: 'DQS 3 — Primary',
  4: 'DQS 4 — Estimated',
  5: 'DQS 5 — Proxy',
};

// ── Utilities ─────────────────────────────────────────────────────────────────

function fmt(value, decimals = 1) {
  if (value == null) return '—';
  return Number(value).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function dqsColour(dqs) {
  return DQS_COLOURS[Math.round(dqs)] || '#9ca3af';
}

// ── PCAF KPI Strip ─────────────────────────────────────────────────────────────

function PcafKpiStrip({ portfolioId, pcafResults, pcafLoading, onRunPcaf, isRunning }) {
  const summary = pcafResults?.portfolio_summary;
  const isDemo = pcafResults?.data_quality_note === 'dqs5_demo';

  const kpis = [
    {
      label: 'WACI',
      value: summary?.waci_tco2e_meur != null
        ? `${fmt(summary.waci_tco2e_meur)} tCO₂e/MEUR`
        : null,
      sub: 'Weighted Avg Carbon Intensity',
      colour: '#38bdf8',
      testId: 'pcaf-kpi-waci',
    },
    {
      label: 'Implied Temp Rise',
      value: summary?.implied_temp_rise != null
        ? `${fmt(summary.implied_temp_rise, 2)} °C`
        : null,
      sub: 'ITR — portfolio warming score',
      colour: summary?.implied_temp_rise > 2.0 ? '#ef4444' : summary?.implied_temp_rise > 1.5 ? '#f59e0b' : '#10b981',
      testId: 'pcaf-kpi-itr',
    },
    {
      label: 'PCAF Coverage',
      value: summary?.pcaf_coverage_pct != null
        ? `${fmt(summary.pcaf_coverage_pct, 1)} %`
        : null,
      sub: 'Assets with emissions data',
      colour: '#a78bfa',
      testId: 'pcaf-kpi-coverage',
    },
    {
      label: 'Weighted DQS',
      value: summary?.weighted_avg_dqs != null
        ? fmt(summary.weighted_avg_dqs, 2)
        : null,
      sub: '1 = best · 5 = proxy estimate',
      colour: summary?.weighted_avg_dqs != null ? dqsColour(summary.weighted_avg_dqs) : '#9ca3af',
      testId: 'pcaf-kpi-dqs',
    },
  ];

  return (
    <div
      className="mb-4 rounded-xl border border-white/[0.07] bg-[#0d1424] px-4 py-3"
      data-testid="pcaf-kpi-strip"
    >
      {/* Strip header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <Leaf className="h-4 w-4 text-emerald-400 flex-shrink-0" />
          <span className="text-xs font-semibold text-white/60 uppercase tracking-wider">
            PCAF Standard v2.0 — Financed Emissions
          </span>
          {isDemo && (
            <span
              className="rounded px-1.5 py-0.5 text-[10px] font-semibold tracking-wide"
              style={{ background: 'rgba(239,68,68,0.15)', color: '#ef4444' }}
              data-testid="pcaf-demo-badge"
            >
              DQS-5 DEMO DATA
            </span>
          )}
        </div>
        <button
          onClick={() => onRunPcaf(portfolioId)}
          disabled={!portfolioId || isRunning}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all flex-shrink-0"
          style={{
            background: isRunning ? 'rgba(56,189,248,0.05)' : 'rgba(56,189,248,0.12)',
            color: '#38bdf8',
            border: '1px solid rgba(56,189,248,0.20)',
            opacity: !portfolioId ? 0.4 : 1,
            cursor: !portfolioId ? 'not-allowed' : 'pointer',
          }}
          data-testid="pcaf-run-button"
        >
          {isRunning
            ? <RefreshCw className="h-3 w-3 animate-spin" />
            : <Play className="h-3 w-3" />
          }
          {isRunning ? 'Calculating…' : 'Run PCAF Calculation'}
        </button>
      </div>

      {/* KPI cards */}
      {pcafLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-14 rounded-lg bg-white/5 animate-pulse" />
          ))}
        </div>
      ) : !summary ? (
        <p className="text-xs text-white/30 py-2">
          No PCAF data yet — select a portfolio and click Run PCAF Calculation.
        </p>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {kpis.map(kpi => (
            <div
              key={kpi.label}
              className="rounded-lg px-3 py-2.5 bg-white/[0.04] border border-white/[0.06]"
              data-testid={kpi.testId}
            >
              <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">
                {kpi.label}
              </p>
              <p
                className="text-base font-bold font-mono tabular-nums leading-snug"
                style={{ color: kpi.colour }}
              >
                {kpi.value || '—'}
              </p>
              <p className="text-[10px] text-white/30 mt-0.5">{kpi.sub}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── DQS Donut Chart ────────────────────────────────────────────────────────────

function DqsDonutChart({ dqsDistribution }) {
  if (!dqsDistribution || Object.keys(dqsDistribution).length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-white/20 text-xs gap-1">
        <span>Run PCAF to see DQS distribution</span>
      </div>
    );
  }

  const data = Object.entries(dqsDistribution)
    .map(([k, v]) => ({
      name: DQS_LABELS[Number(k)] || `DQS ${k}`,
      value: Number((Number(v) * 100).toFixed(1)),
      dqs: Number(k),
    }))
    .filter(d => d.value > 0);

  return (
    <div data-testid="pcaf-dqs-donut">
      <ResponsiveContainer width="100%" height={220}>
        <RechartsPieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map(entry => (
              <Cell key={`dqs-${entry.dqs}`} fill={DQS_COLOURS[entry.dqs] || '#9ca3af'} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: '#0d1424',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8,
              fontSize: 11,
            }}
            formatter={(v, n) => [`${v}%`, n]}
          />
          <Legend
            formatter={value => (
              <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.55)' }}>{value}</span>
            )}
          />
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Glidepath Preview Chart ────────────────────────────────────────────────────

function GlidepathPreviewChart({ waciHistory }) {
  const navigate = useNavigate();
  const history = waciHistory?.history || [];

  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 text-white/20 text-xs gap-2">
        <span>No trajectory data yet</span>
        <span>Run PCAF Calculation to populate glidepath</span>
      </div>
    );
  }

  const chartData = history.map(h => ({
    year: h.year,
    'Actual WACI': h.waci != null ? Number(Number(h.waci).toFixed(1)) : null,
    'NZBA Target': h.glidepath_value != null ? Number(Number(h.glidepath_value).toFixed(1)) : null,
  }));

  return (
    <div data-testid="pcaf-glidepath-preview">
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
          <XAxis
            dataKey="year"
            tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.4)' }}
            axisLine={false}
            tickLine={false}
            unit=" t"
            width={45}
          />
          <Tooltip
            contentStyle={{
              background: '#0d1424',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8,
              fontSize: 11,
            }}
          />
          <Legend
            formatter={value => (
              <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.55)' }}>{value}</span>
            )}
          />
          <Line
            type="monotone"
            dataKey="Actual WACI"
            stroke="#38bdf8"
            strokeWidth={2}
            dot={{ r: 3, fill: '#38bdf8' }}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="NZBA Target"
            stroke="rgba(255,255,255,0.30)"
            strokeWidth={1.5}
            strokeDasharray="5 3"
            dot={false}
            connectNulls
          />
        </ComposedChart>
      </ResponsiveContainer>
      <div className="mt-2 text-right">
        <button
          onClick={() => navigate('/glidepath-tracker')}
          className="text-[11px] transition-opacity hover:opacity-70"
          style={{ color: '#38bdf8' }}
        >
          View Full Glidepath Tracker →
        </button>
      </div>
    </div>
  );
}

// ── Investee Attribution Table ─────────────────────────────────────────────────

function InvesteeTable({ investees }) {
  if (!investees || investees.length === 0) {
    return (
      <div className="text-center py-8 text-white/30 text-xs">
        No investee data — run PCAF calculation first.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto" data-testid="pcaf-investee-table">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-white/[0.07] text-left">
            {['Company', 'Sector', 'Asset Class', 'Attrib. Factor', 'Financed tCO₂e', 'WACI Contrib.', 'DQS'].map(h => (
              <th
                key={h}
                className="pb-2 pr-4 text-white/40 font-medium uppercase tracking-wider text-[10px]"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {investees.map((inv, i) => {
            const dqs = Math.round(inv.dqs_score ?? inv.data_quality_score ?? 5);
            return (
              <tr
                key={i}
                className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors"
              >
                <td className="py-2 pr-4 text-white/80 font-medium truncate max-w-[140px]">
                  {inv.company_name || '—'}
                </td>
                <td className="py-2 pr-4 text-white/50">{inv.sector || '—'}</td>
                <td className="py-2 pr-4 text-white/50">{inv.asset_class || '—'}</td>
                <td className="py-2 pr-4 font-mono tabular-nums text-white/70">
                  {inv.attribution_factor != null
                    ? `${(inv.attribution_factor * 100).toFixed(1)} %`
                    : '—'}
                </td>
                <td className="py-2 pr-4 font-mono tabular-nums text-white/70">
                  {inv.financed_emissions_tco2e != null ? fmt(inv.financed_emissions_tco2e, 0) : '—'}
                </td>
                <td className="py-2 pr-4 font-mono tabular-nums text-white/70">
                  {inv.waci_contribution != null ? fmt(inv.waci_contribution, 2) : '—'}
                </td>
                <td className="py-2">
                  <span
                    className="rounded px-1.5 py-0.5 text-[10px] font-semibold"
                    style={{
                      background: `${DQS_COLOURS[dqs] || '#9ca3af'}22`,
                      color: DQS_COLOURS[dqs] || '#9ca3af',
                    }}
                  >
                    {dqs}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ── PCAF Tab Content ───────────────────────────────────────────────────────────

function PcafTabContent({ portfolioId, pcafResults, waciHistory }) {
  const hasSectorBreakdown = pcafResults?.sector_breakdown?.length > 0;
  const hasPai = pcafResults?.pai_indicators &&
    Object.keys(pcafResults.pai_indicators).length > 0;

  return (
    <div className="space-y-4">
      {/* DQS donut + Glidepath preview — side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-white/[0.07] bg-[#0d1424] p-4">
          <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-3">
            DQS Distribution — % of Financed Emissions
          </h3>
          <DqsDonutChart dqsDistribution={pcafResults?.dqs_distribution} />
        </div>
        <div className="rounded-xl border border-white/[0.07] bg-[#0d1424] p-4">
          <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-3">
            WACI Trajectory vs. NZBA Glidepath
          </h3>
          <GlidepathPreviewChart waciHistory={waciHistory} portfolioId={portfolioId} />
        </div>
      </div>

      {/* Sector breakdown */}
      {hasSectorBreakdown && (
        <div className="rounded-xl border border-white/[0.07] bg-[#0d1424] p-4">
          <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-3">
            Sector Attribution
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.07] text-left">
                  {['Sector', 'WACI (tCO₂e/MEUR)', 'Total tCO₂e', 'Assets', '% Portfolio WACI'].map(h => (
                    <th key={h} className="pb-2 pr-4 text-white/40 font-medium uppercase tracking-wider text-[10px]">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pcafResults.sector_breakdown.map((s, i) => (
                  <tr key={i} className="border-b border-white/[0.04] hover:bg-white/[0.02] transition-colors">
                    <td className="py-2 pr-4 text-white/80">{s.sector}</td>
                    <td className="py-2 pr-4 font-mono tabular-nums text-cyan-400">
                      {fmt(s.waci, 1)}
                    </td>
                    <td className="py-2 pr-4 font-mono tabular-nums text-white/70">
                      {fmt(s.total_tco2e, 0)}
                    </td>
                    <td className="py-2 pr-4 text-white/50">{s.asset_count}</td>
                    <td className="py-2 pr-4 text-white/50">
                      {s.pct_portfolio_waci != null ? `${fmt(s.pct_portfolio_waci, 1)} %` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Investee attribution */}
      <div className="rounded-xl border border-white/[0.07] bg-[#0d1424] p-4">
        <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-3">
          Investee Attribution — PCAF Standard v2.0
        </h3>
        <InvesteeTable investees={pcafResults?.investee_results} />
      </div>

      {/* SFDR PAI indicators */}
      {hasPai && (
        <div className="rounded-xl border border-white/[0.07] bg-[#0d1424] p-4">
          <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider mb-3">
            SFDR PAI Indicators
          </h3>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {Object.entries(pcafResults.pai_indicators).map(([key, value]) => (
              <div
                key={key}
                className="rounded-lg px-3 py-2.5 bg-white/[0.04] border border-white/[0.06]"
              >
                <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">
                  {key.replace(/_/g, ' ')}
                </p>
                <p className="text-sm font-bold font-mono tabular-nums text-white/80">
                  {typeof value === 'number' ? fmt(value, 1) : String(value)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function PortfolioAnalyticsPage() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedPortfolioId, setSelectedPortfolioId] = useState(null);

  const { data: portfolios, isLoading: portfoliosLoading } = usePortfolios();
  const { data: dashboard, isLoading: dashboardLoading } = useDashboard(selectedPortfolioId);
  const { data: holdings, isLoading: holdingsLoading } = useHoldings(selectedPortfolioId);
  const { data: pcafResults, isLoading: pcafLoading } = usePCAFResults(selectedPortfolioId);
  const { data: waciHistory } = useWACIHistory(selectedPortfolioId, 10);
  const runPcafMutation = useRunPCAF();

  // Auto-select first portfolio
  React.useEffect(() => {
    if (portfolios?.items?.length > 0 && !selectedPortfolioId) {
      setSelectedPortfolioId(portfolios.items[0].id);
    }
  }, [portfolios, selectedPortfolioId]);

  const selectedPortfolio = portfolios?.items?.find(p => p.id === selectedPortfolioId);

  function handleRunPcaf(portfolioId) {
    if (!portfolioId || runPcafMutation.isPending) return;
    runPcafMutation.mutate(portfolioId);
  }

  return (
    <div className="min-h-screen bg-white/[0.02]" data-testid="portfolio-analytics-page">
      {/* Page header */}
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-cyan-400/10 rounded-lg">
            <PieChart className="h-6 w-6 text-cyan-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Portfolio Analytics</h1>
            <p className="text-sm text-white/40">
              PCAF Standard v2.0 financed emissions · WACI · ITR · Glidepath · Scenario comparison
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-4">
          <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/20">
            <LayoutDashboard className="h-3 w-3 mr-1" />
            Executive Dashboard
          </Badge>
          <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
            <Leaf className="h-3 w-3 mr-1" />
            PCAF Standard v2.0
          </Badge>
          <Badge variant="outline" className="bg-violet-500/10 text-violet-300 border-violet-500/20">
            <GitCompare className="h-3 w-3 mr-1" />
            Scenario Comparison
          </Badge>
          <Badge variant="outline" className="bg-violet-500/10 text-violet-300 border-violet-500/20">
            <FileText className="h-3 w-3 mr-1" />
            Multi-Format Reports
          </Badge>
        </div>
      </div>

      {/* Main content */}
      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar — Portfolio Selector */}
          <div className="lg:col-span-1">
            <PortfolioSelector
              portfolios={portfolios}
              selectedId={selectedPortfolioId}
              onSelect={setSelectedPortfolioId}
              isLoading={portfoliosLoading}
            />
          </div>

          {/* Main content area */}
          <div className="lg:col-span-3">
            {/* PCAF KPI strip — always visible when portfolio selected */}
            {selectedPortfolioId && (
              <PcafKpiStrip
                portfolioId={selectedPortfolioId}
                pcafResults={pcafResults}
                pcafLoading={pcafLoading}
                onRunPcaf={handleRunPcaf}
                isRunning={runPcafMutation.isPending}
              />
            )}

            {/* Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-6 mb-6 bg-[#0d1424] border border-white/[0.06]">
                <TabsTrigger
                  value="dashboard"
                  className="flex items-center gap-1.5 data-[state=active]:bg-cyan-400/10 data-[state=active]:text-cyan-300"
                  data-testid="tab-dashboard"
                >
                  <LayoutDashboard className="h-3.5 w-3.5" />
                  <span className="hidden md:inline text-xs">Dashboard</span>
                </TabsTrigger>
                <TabsTrigger
                  value="holdings"
                  className="flex items-center gap-1.5 data-[state=active]:bg-blue-500/10 data-[state=active]:text-blue-300"
                  data-testid="tab-holdings"
                >
                  <Building2 className="h-3.5 w-3.5" />
                  <span className="hidden md:inline text-xs">Holdings</span>
                </TabsTrigger>
                <TabsTrigger
                  value="scenarios"
                  className="flex items-center gap-1.5 data-[state=active]:bg-violet-500/10 data-[state=active]:text-violet-300"
                  data-testid="tab-scenarios"
                >
                  <GitCompare className="h-3.5 w-3.5" />
                  <span className="hidden md:inline text-xs">Scenarios</span>
                </TabsTrigger>
                <TabsTrigger
                  value="pcaf"
                  className="flex items-center gap-1.5 data-[state=active]:bg-emerald-500/10 data-[state=active]:text-emerald-400"
                  data-testid="tab-pcaf"
                >
                  <Leaf className="h-3.5 w-3.5" />
                  <span className="hidden md:inline text-xs">PCAF</span>
                </TabsTrigger>
                <TabsTrigger
                  value="reports"
                  className="flex items-center gap-1.5 data-[state=active]:bg-amber-500/10 data-[state=active]:text-amber-400"
                  data-testid="tab-reports"
                >
                  <FileText className="h-3.5 w-3.5" />
                  <span className="hidden md:inline text-xs">Reports</span>
                </TabsTrigger>
                <TabsTrigger
                  value="scheduled"
                  className="flex items-center gap-1.5 data-[state=active]:bg-white/10 data-[state=active]:text-white/80"
                  data-testid="tab-scheduled"
                >
                  <Calendar className="h-3.5 w-3.5" />
                  <span className="hidden md:inline text-xs">Scheduled</span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="dashboard" className="mt-0">
                <PortfolioDashboard
                  dashboard={dashboard}
                  isLoading={dashboardLoading && selectedPortfolioId}
                />
              </TabsContent>

              <TabsContent value="holdings" className="mt-0">
                <HoldingsTable
                  holdings={holdings}
                  isLoading={holdingsLoading && selectedPortfolioId}
                />
              </TabsContent>

              <TabsContent value="scenarios" className="mt-0">
                <ScenarioComparison portfolioId={selectedPortfolioId} />
              </TabsContent>

              <TabsContent value="pcaf" className="mt-0">
                <PcafTabContent
                  portfolioId={selectedPortfolioId}
                  pcafResults={pcafResults}
                  waciHistory={waciHistory}
                />
              </TabsContent>

              <TabsContent value="reports" className="mt-0">
                <ReportGenerator
                  portfolioId={selectedPortfolioId}
                  portfolioName={selectedPortfolio?.name}
                />
              </TabsContent>

              <TabsContent value="scheduled" className="mt-0">
                <ScheduledReportsManager />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}
