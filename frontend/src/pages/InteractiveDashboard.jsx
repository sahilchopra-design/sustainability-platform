/**
 * Interactive Analytics Dashboard
 * Fully interactive sustainability platform analytics hub with:
 * - Collapsible filter/parameter sidebar
 * - Live chart type switching per section
 * - Real-time KPI updates from parameter changes
 * - Multiple visualisation tabs: Overview, Climate Risk, Financial, Emissions, Sensitivity
 * - Backend API integration: portfolio fetch, live analysis run, KPI augmentation
 */
import React, { useState, useMemo, useCallback, useEffect, useRef } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  Legend, ResponsiveContainer, Cell, LineChart, Line, AreaChart, Area,
  PieChart, Pie, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ScatterChart, Scatter, ComposedChart, RadialBarChart, RadialBar, Treemap,
  ReferenceLine, LabelList,
} from 'recharts';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Slider } from '../components/ui/slider';
import { Checkbox } from '../components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Separator } from '../components/ui/separator';
import {
  TrendingUp, TrendingDown, BarChart3, PieChart as PieIcon, Activity,
  Leaf, Shield, AlertTriangle, DollarSign, Filter, ChevronLeft, ChevronRight,
  RefreshCw, Download, Settings2, LayoutDashboard, Thermometer, Zap,
  Building2, Globe2, LineChart as LineIcon, AreaChart as AreaIcon,
  RadarIcon, ScatterChart as ScatterIcon, Grid3X3, Play, Loader2,
} from 'lucide-react';
import { cn } from '../lib/utils';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const SCENARIO_COLORS = {
  'Net Zero 2050':    '#22c55e',
  'Below 2°C':        '#3b82f6',
  'Delayed Transition': '#f59e0b',
  'Hot House World':  '#ef4444',
  'NDCs':             '#8b5cf6',
  'Orderly':          '#22c55e',
  'Disorderly':       '#f59e0b',
  'Hot house world':  '#ef4444',
};

const SECTOR_COLORS = {
  'Power Generation': '#6366f1',
  'Oil & Gas':        '#f59e0b',
  'Metals & Mining':  '#8b5cf6',
  'Automotive':       '#3b82f6',
  'Airlines':         '#ec4899',
  'Real Estate':      '#14b8a6',
  'Technology':       '#06b6d4',
  'Agriculture':      '#84cc16',
  'Finance':          '#f97316',
};

const CHART_TYPES = [
  { id: 'bar',    label: 'Bar',    Icon: BarChart3 },
  { id: 'line',   label: 'Line',   Icon: LineIcon },
  { id: 'area',   label: 'Area',   Icon: AreaIcon },
  { id: 'pie',    label: 'Pie',    Icon: PieIcon },
  { id: 'radar',  label: 'Radar',  Icon: RadarIcon },
];

const ALL_SCENARIOS = ['Net Zero 2050', 'Below 2°C', 'Delayed Transition', 'Hot House World'];
const ALL_SECTORS   = ['Power Generation', 'Oil & Gas', 'Metals & Mining', 'Automotive', 'Airlines', 'Real Estate', 'Technology', 'Finance'];
const ALL_ASSET_TYPES = ['Loan', 'Bond', 'Equity', 'Derivative'];
const ALL_REGIONS   = ['Global', 'North America', 'Europe', 'Asia Pacific', 'Emerging Markets'];

// ─────────────────────────────────────────────────────────────────────────────
// Data generators (deterministic based on filter params)
// ─────────────────────────────────────────────────────────────────────────────

function seedRandom(seed) {
  let s = seed;
  return () => { s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 0xffffffff; };
}

function generatePortfolioData(sectors, assetTypes, horizon, confidenceLevel) {
  const rng = seedRandom(sectors.length * 17 + assetTypes.length * 7 + horizon * 3 + confidenceLevel);
  return sectors.map((sector, i) => {
    const baseExposure = 80 + rng() * 420;
    const risk = rng() * 0.35 + 0.05;
    return {
      sector,
      exposure: Math.round(baseExposure * 1e6),
      loans:    Math.round(baseExposure * 0.5 * (assetTypes.includes('Loan') ? 1 : 0.2) * 1e6),
      bonds:    Math.round(baseExposure * 0.3 * (assetTypes.includes('Bond') ? 1 : 0.2) * 1e6),
      equity:   Math.round(baseExposure * 0.2 * (assetTypes.includes('Equity') ? 1 : 0.1) * 1e6),
      riskScore: Math.round(risk * 100),
      expectedLoss: Math.round(baseExposure * risk * 1e4),
      carbonIntensity: Math.round(50 + rng() * 450),
      pd: parseFloat((0.01 + rng() * 0.09).toFixed(4)),
      lgd: parseFloat((0.25 + rng() * 0.45).toFixed(4)),
    };
  });
}

function generateScenarioData(scenarios, sectors, horizon) {
  const rng = seedRandom(scenarios.length * 13 + sectors.length * 5 + horizon);
  return scenarios.map((scenario, si) => {
    const multiplier = si === 0 ? 0.4 : si === 1 ? 0.65 : si === 2 ? 1.0 : 1.5;
    const baseEl = rng() * 15 + 5;
    return {
      scenario,
      expectedLoss:    parseFloat((baseEl * multiplier * (horizon / 2030)).toFixed(2)),
      pdChange:        parseFloat(((0.02 + rng() * 0.08) * multiplier).toFixed(4)),
      lgdChange:       parseFloat(((0.01 + rng() * 0.05) * multiplier).toFixed(4)),
      capitalCharge:   parseFloat((3 + rng() * 7 * multiplier).toFixed(2)),
      temperatureRise: parseFloat((1.5 + si * 0.7 + rng() * 0.3).toFixed(1)),
      co2Reduction:    parseFloat((80 - si * 20 + rng() * 10).toFixed(1)),
      transitionRisk:  parseFloat((10 + rng() * 20 * multiplier).toFixed(1)),
      physicalRisk:    parseFloat((5 + si * 8 + rng() * 10).toFixed(1)),
    };
  });
}

function generateTimeSeriesData(scenarios, horizon) {
  const years = [];
  for (let y = 2025; y <= horizon; y += 5) years.push(y);
  const rng = seedRandom(scenarios.length * 11 + horizon);
  return years.map((year, yi) => {
    const entry = { year };
    scenarios.forEach((s, si) => {
      const base = 5 + si * 3;
      const growth = 1 + yi * (0.08 + si * 0.06);
      entry[s] = parseFloat((base * growth + rng() * 2).toFixed(2));
    });
    return entry;
  });
}

function generateEmissionsData(sectors, horizon) {
  const rng = seedRandom(sectors.length * 23 + horizon);
  return sectors.map(sector => ({
    sector,
    scope1: Math.round(rng() * 800 + 50),
    scope2: Math.round(rng() * 400 + 20),
    scope3: Math.round(rng() * 1200 + 100),
    target2030: Math.round(rng() * 400 + 30),
    parisAligned: rng() > 0.5,
  }));
}

function generateSensitivityData(sectors, horizon) {
  const rng = seedRandom(sectors.length * 31 + horizon);
  const drivers = [
    'Carbon Price', 'Interest Rate', 'GDP Growth', 'Energy Price',
    'Regulatory Tightening', 'Physical Risk Events', 'Transition Speed',
    'Technology Adoption',
  ];
  return drivers.map(driver => ({
    driver,
    low:  parseFloat((-(rng() * 8 + 1)).toFixed(2)),
    high: parseFloat((rng() * 12 + 2).toFixed(2)),
    swing: parseFloat((rng() * 20 + 3).toFixed(2)),
  })).sort((a, b) => b.swing - a.swing);
}

function generateHeatmapData(scenarios, sectors) {
  const rng = seedRandom(scenarios.length * 41 + sectors.length * 19);
  return scenarios.map(scenario => {
    const row = { scenario };
    sectors.forEach(sector => {
      const si = ALL_SCENARIOS.indexOf(scenario);
      row[sector] = parseFloat((3 + si * 4 + rng() * 8).toFixed(1));
    });
    return row;
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Helper components
// ─────────────────────────────────────────────────────────────────────────────

const fmtCcy = (v, short = true) => {
  if (v == null) return '—';
  if (short) {
    if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
    if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
    if (Math.abs(v) >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
  }
  return `$${v.toLocaleString()}`;
};
const fmtPct = v => v == null ? '—' : `${(v * 100).toFixed(2)}%`;
const fmtNum = (v, d = 1) => v == null ? '—' : v.toFixed(d);

function ChartTypeSelector({ types = CHART_TYPES, value, onChange }) {
  return (
    <div className="flex items-center gap-0.5 bg-white/[0.04] rounded p-0.5">
      {types.map(({ id, label, Icon }) => (
        <button
          key={id}
          onClick={() => onChange(id)}
          title={label}
          className={cn(
            'p-1.5 rounded text-white/40 transition-all',
            value === id
              ? 'bg-cyan-500/20 text-cyan-300'
              : 'hover:text-white/70 hover:bg-white/[0.06]'
          )}
        >
          <Icon className="h-3.5 w-3.5" />
        </button>
      ))}
    </div>
  );
}

function KpiCard({ title, value, sub, trend, Icon, color = 'indigo', loading }) {
  const iconColors = {
    indigo: 'text-cyan-400 bg-cyan-400/10',
    green:  'text-emerald-400 bg-emerald-400/10',
    amber:  'text-amber-400 bg-amber-400/10',
    red:    'text-red-400 bg-red-400/10',
  };
  return (
    <div className="bg-[#0d1424] border border-white/[0.06] rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div className="space-y-1 min-w-0">
          <p className="text-[10px] font-semibold text-white/40 uppercase tracking-wider truncate">{title}</p>
          {loading
            ? <div className="h-8 w-24 bg-white/10 rounded animate-pulse" />
            : <p className="text-2xl font-bold text-white tabular-nums mono-num">{value}</p>
          }
          {sub && <p className="text-[11px] text-white/30 truncate">{sub}</p>}
        </div>
        <div className={cn('p-2 rounded-lg flex-shrink-0 ml-2', iconColors[color])}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      {trend !== undefined && !loading && (
        <div className={cn('flex items-center gap-1 mt-2 text-xs font-medium',
          trend >= 0 ? 'text-red-400' : 'text-emerald-400'
        )}>
          {trend >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
          <span>{Math.abs(trend).toFixed(1)}% vs base</span>
        </div>
      )}
    </div>
  );
}

const CustomTooltip = ({ active, payload, label, formatter }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0d1424] border border-white/[0.08] rounded-lg shadow-2xl p-3 text-xs min-w-[160px]">
      <p className="font-semibold text-white/80 mb-2 border-b border-white/[0.08] pb-1">{label}</p>
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center justify-between gap-3 py-0.5">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-sm flex-shrink-0" style={{ backgroundColor: entry.color || entry.fill }} />
            <span className="text-white/40">{entry.name}</span>
          </div>
          <span className="font-medium tabular-nums text-white/80 mono-num">
            {formatter ? formatter(entry.value, entry.name) : entry.value?.toLocaleString()}
          </span>
        </div>
      ))}
    </div>
  );
};

function SectionCard({ title, description, chartType, onChartTypeChange, chartTypeOptions, children }) {
  return (
    <div className="bg-[#0d1424] border border-white/[0.06] rounded-lg overflow-hidden">
      <div className="px-4 pt-4 pb-2">
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white/80 truncate">{title}</p>
            {description && <p className="text-[11px] text-white/30 mt-0.5 truncate">{description}</p>}
          </div>
          {onChartTypeChange && (
            <ChartTypeSelector
              types={chartTypeOptions || CHART_TYPES.slice(0, 4)}
              value={chartType}
              onChange={onChartTypeChange}
            />
          )}
        </div>
      </div>
      <div className="p-4 pt-0">{children}</div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Chart components per tab
// ─────────────────────────────────────────────────────────────────────────────

function ExposureChart({ data, chartType }) {
  const chartData = data.map(d => ({ name: d.sector.split(' ').slice(-1)[0], ...d }));
  if (chartType === 'pie') {
    return (
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie data={chartData} dataKey="exposure" nameKey="sector" cx="50%" cy="50%"
            innerRadius={60} outerRadius={100} paddingAngle={3}
            label={({ sector, percent }) => `${sector.split(' ')[0]} ${(percent * 100).toFixed(0)}%`}
            labelLine={false}
          >
            {chartData.map((_, i) => (
              <Cell key={i} fill={Object.values(SECTOR_COLORS)[i % 9]} />
            ))}
          </Pie>
          <RechartsTooltip content={<CustomTooltip formatter={fmtCcy} />} />
        </PieChart>
      </ResponsiveContainer>
    );
  }
  if (chartType === 'area') {
    return (
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={chartData} margin={{ left: 10, right: 10, bottom: 30 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} angle={-30} textAnchor="end" />
          <YAxis tickFormatter={v => fmtCcy(v)} tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
          <RechartsTooltip content={<CustomTooltip formatter={fmtCcy} />} />
          <Area type="monotone" dataKey="loans" stackId="1" fill="#6366f1" stroke="#6366f1" name="Loans" />
          <Area type="monotone" dataKey="bonds" stackId="1" fill="#3b82f6" stroke="#3b82f6" name="Bonds" />
          <Area type="monotone" dataKey="equity" stackId="1" fill="#8b5cf6" stroke="#8b5cf6" name="Equity" />
        </AreaChart>
      </ResponsiveContainer>
    );
  }
  if (chartType === 'radar') {
    return (
      <ResponsiveContainer width="100%" height={260}>
        <RadarChart data={chartData}>
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <PolarAngleAxis dataKey="name" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
          <PolarRadiusAxis tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.25)' }} tickFormatter={v => fmtCcy(v, true)} />
          <Radar name="Exposure" dataKey="exposure" fill="#6366f1" fillOpacity={0.4} stroke="#6366f1" />
          <RechartsTooltip content={<CustomTooltip formatter={fmtCcy} />} />
        </RadarChart>
      </ResponsiveContainer>
    );
  }
  // Default bar
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} margin={{ left: 10, right: 10, bottom: 30 }} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
        <XAxis type="number" tickFormatter={v => fmtCcy(v)} tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
        <YAxis type="category" dataKey="name" width={80} tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
        <RechartsTooltip content={<CustomTooltip formatter={fmtCcy} />} />
        <Bar dataKey="loans" stackId="a" fill="#6366f1" name="Loans" />
        <Bar dataKey="bonds" stackId="a" fill="#3b82f6" name="Bonds" />
        <Bar dataKey="equity" stackId="a" fill="#8b5cf6" name="Equity" radius={[0, 3, 3, 0]} />
        <Legend iconSize={10} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function ScenarioComparisonChart({ data, chartType, metric }) {
  const metricLabels = {
    expectedLoss: 'Expected Loss ($M)', pdChange: 'PD Change (%)',
    lgdChange: 'LGD Change (%)', capitalCharge: 'Capital Charge (%)',
    transitionRisk: 'Transition Risk Score', physicalRisk: 'Physical Risk Score',
  };
  const formatter = metric === 'expectedLoss'
    ? v => fmtCcy(v * 1e6)
    : v => fmtNum(v) + (metric.includes('hange') || metric.includes('Charge') ? '%' : '');

  if (chartType === 'radar') {
    return (
      <ResponsiveContainer width="100%" height={260}>
        <RadarChart data={data.map(d => ({ ...d, name: d.scenario.split(' ')[0] }))}>
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <PolarAngleAxis dataKey="name" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
          <PolarRadiusAxis tick={{ fontSize: 9, fill: 'rgba(255,255,255,0.25)' }} />
          {['expectedLoss', 'transitionRisk', 'physicalRisk'].map((k, i) => (
            <Radar key={k} name={metricLabels[k]?.split(' ')[0]} dataKey={k}
              fill={['#6366f1','#f59e0b','#ef4444'][i]} fillOpacity={0.3}
              stroke={['#6366f1','#f59e0b','#ef4444'][i]} />
          ))}
          <Legend iconSize={10} />
          <RechartsTooltip />
        </RadarChart>
      </ResponsiveContainer>
    );
  }
  if (chartType === 'line') {
    return (
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ left: 10, bottom: 30 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="scenario" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} angle={-20} textAnchor="end" />
          <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
          <RechartsTooltip content={<CustomTooltip formatter={formatter} />} />
          <Line dataKey={metric} stroke="#6366f1" strokeWidth={2} dot={{ r: 5, fill: '#6366f1' }}
            activeDot={{ r: 7 }} name={metricLabels[metric]} />
        </LineChart>
      </ResponsiveContainer>
    );
  }
  // Bar
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ left: 10, bottom: 30 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="scenario" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} angle={-20} textAnchor="end" />
        <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
        <RechartsTooltip content={<CustomTooltip formatter={formatter} />} />
        <Bar dataKey={metric} name={metricLabels[metric]} radius={[3, 3, 0, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={SCENARIO_COLORS[d.scenario] || '#6366f1'} />
          ))}
          <LabelList dataKey={metric} position="top" formatter={formatter} style={{ fontSize: 10, fill: 'rgba(255,255,255,0.5)' }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function TimeSeriesChart({ data, scenarios, chartType }) {
  const colors = scenarios.map(s => SCENARIO_COLORS[s] || '#6366f1');
  if (chartType === 'area') {
    return (
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis dataKey="year" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
          <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} label={{ value: 'Expected Loss $M', angle: -90, position: 'insideLeft', style: { fontSize: 9, fill: 'rgba(255,255,255,0.25)' } }} />
          <RechartsTooltip content={<CustomTooltip />} />
          <Legend iconSize={10} />
          {scenarios.map((s, i) => (
            <Area key={s} type="monotone" dataKey={s} stroke={colors[i]}
              fill={colors[i]} fillOpacity={0.15} strokeWidth={2} dot={false} />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  }
  // Line default
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="year" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
        <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} label={{ value: 'Expected Loss $M', angle: -90, position: 'insideLeft', style: { fontSize: 9, fill: 'rgba(255,255,255,0.25)' } }} />
        <RechartsTooltip content={<CustomTooltip />} />
        <Legend iconSize={10} />
        {scenarios.map((s, i) => (
          <Line key={s} type="monotone" dataKey={s} stroke={colors[i]}
            strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

function RiskHeatmap({ data, sectors }) {
  const allVals = data.flatMap(row => sectors.map(s => row[s] || 0));
  const min = Math.min(...allVals), max = Math.max(...allVals);
  const getColor = v => {
    const t = (v - min) / (max - min || 1);
    if (t < 0.25) return { bg: 'rgba(20,184,166,0.18)', text: '#5eead4' };
    if (t < 0.5)  return { bg: 'rgba(245,158,11,0.18)', text: '#fbbf24' };
    if (t < 0.75) return { bg: 'rgba(249,115,22,0.22)', text: '#fb923c' };
    return { bg: 'rgba(239,68,68,0.25)', text: '#f87171' };
  };
  const legend = [
    { bg: 'rgba(20,184,166,0.3)', label: 'Low' },
    { bg: 'rgba(245,158,11,0.3)', label: 'Med' },
    { bg: 'rgba(249,115,22,0.3)', label: 'High' },
    { bg: 'rgba(239,68,68,0.35)', label: 'Crit' },
  ];
  return (
    <div className="overflow-x-auto">
      <table className="text-xs w-full border-separate border-spacing-0.5">
        <thead>
          <tr>
            <th className="text-left p-1 text-white/30 w-28 font-normal">Scenario</th>
            {sectors.map(s => (
              <th key={s} className="text-center p-1 text-white/30 font-medium">
                {s.split(' ')[0]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map(row => (
            <tr key={row.scenario}>
              <td className="p-1 font-medium text-white/50 whitespace-nowrap">
                {row.scenario.split(' ').slice(0, 2).join(' ')}
              </td>
              {sectors.map(s => {
                const { bg, text } = getColor(row[s] || 0);
                return (
                  <td key={s}
                    className="text-center p-1 rounded font-medium transition-transform hover:scale-110 cursor-default mono-num"
                    style={{ backgroundColor: bg, color: text }}
                    title={`${row.scenario} / ${s}: ${(row[s] || 0).toFixed(1)}% EL`}
                  >
                    {(row[s] || 0).toFixed(1)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center gap-2 mt-2 text-xs text-white/30">
        {legend.map(({ bg, label }) => (
          <div key={label} className="flex items-center gap-1">
            <div className="w-4 h-3 rounded" style={{ backgroundColor: bg }} />
            <span>{label}</span>
          </div>
        ))}
        <span className="ml-auto">Values = Expected Loss %</span>
      </div>
    </div>
  );
}

function TornadoChart({ data }) {
  const maxSwing = Math.max(...data.map(d => d.swing));
  return (
    <div className="space-y-1.5">
      {data.map((d) => (
        <div key={d.driver} className="flex items-center gap-2 text-xs">
          <div className="w-32 text-right text-white/50 font-medium truncate">{d.driver}</div>
          <div className="flex-1 flex items-center gap-0.5 h-6">
            {/* Downside bar (left) */}
            <div className="flex-1 flex justify-end">
              <div
                className="h-5 rounded-l flex items-center justify-end pr-1 text-white text-[10px] font-medium mono-num"
                style={{ width: `${Math.abs(d.low) / maxSwing * 100}%`, backgroundColor: '#10b981', minWidth: 2 }}
              >
                {Math.abs(d.low) > 1 && `${d.low.toFixed(1)}%`}
              </div>
            </div>
            {/* Center line */}
            <div className="w-px h-5 bg-white/20" />
            {/* Upside bar (right) */}
            <div className="flex-1">
              <div
                className="h-5 rounded-r flex items-center pl-1 text-white text-[10px] font-medium mono-num"
                style={{ width: `${d.high / maxSwing * 100}%`, backgroundColor: '#ef4444', minWidth: 2 }}
              >
                {d.high > 1 && `+${d.high.toFixed(1)}%`}
              </div>
            </div>
          </div>
          <div className="w-12 text-white/30 mono-num">{d.swing.toFixed(1)}</div>
        </div>
      ))}
      <div className="flex items-center gap-3 text-xs text-white/30 mt-2">
        <div className="flex items-center gap-1"><div className="w-3 h-2 rounded" style={{ backgroundColor: '#10b981' }} /><span>Downside</span></div>
        <div className="flex items-center gap-1"><div className="w-3 h-2 bg-red-500 rounded" /><span>Upside impact</span></div>
        <span className="ml-auto">Swing = total range (%)</span>
      </div>
    </div>
  );
}

function EmissionsChart({ data, chartType }) {
  if (chartType === 'pie') {
    const totals = data.reduce((acc, d) => ({
      scope1: acc.scope1 + d.scope1,
      scope2: acc.scope2 + d.scope2,
      scope3: acc.scope3 + d.scope3,
    }), { scope1: 0, scope2: 0, scope3: 0 });
    const pie = [
      { name: 'Scope 1 (Direct)', value: totals.scope1, fill: '#ef4444' },
      { name: 'Scope 2 (Indirect)', value: totals.scope2, fill: '#f59e0b' },
      { name: 'Scope 3 (Value Chain)', value: totals.scope3, fill: '#8b5cf6' },
    ];
    return (
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie data={pie} dataKey="value" cx="50%" cy="50%" innerRadius={55} outerRadius={95}
            paddingAngle={4} label={({ name, percent }) => `${name.split(' ')[0]} ${(percent*100).toFixed(0)}%`}>
            {pie.map((e, i) => <Cell key={i} fill={e.fill} />)}
          </Pie>
          <RechartsTooltip formatter={(v) => `${v.toLocaleString()} tCO₂e`} />
        </PieChart>
      </ResponsiveContainer>
    );
  }
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ left: 10, bottom: 30 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="sector" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} angle={-25} textAnchor="end" />
        <YAxis tickFormatter={v => `${(v/1000).toFixed(0)}kt`} tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
        <RechartsTooltip content={<CustomTooltip formatter={v => `${v.toLocaleString()} tCO₂e`} />} />
        <Bar dataKey="scope1" stackId="a" fill="#ef4444" name="Scope 1" />
        <Bar dataKey="scope2" stackId="a" fill="#f59e0b" name="Scope 2" />
        <Bar dataKey="scope3" stackId="a" fill="#8b5cf6" name="Scope 3" radius={[3,3,0,0]} />
        <Legend iconSize={10} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function ECLStageChart({ data, chartType }) {
  const staged = data.map(d => ({
    sector: d.sector.split(' ')[0],
    stage1: parseFloat((d.exposure * d.pd * d.lgd * 0.12).toFixed(0)),
    stage2: parseFloat((d.exposure * d.pd * d.lgd * 0.35).toFixed(0)),
    stage3: parseFloat((d.exposure * d.pd * d.lgd * 0.70).toFixed(0)),
  }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={staged} margin={{ left: 10, bottom: 30 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="sector" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} angle={-25} textAnchor="end" />
        <YAxis tickFormatter={v => fmtCcy(v)} tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
        <RechartsTooltip content={<CustomTooltip formatter={fmtCcy} />} />
        <Bar dataKey="stage1" stackId="a" fill="#22c55e" name="Stage 1 (12-month ECL)" />
        <Bar dataKey="stage2" stackId="a" fill="#f59e0b" name="Stage 2 (Lifetime ECL)" />
        <Bar dataKey="stage3" stackId="a" fill="#ef4444" name="Stage 3 (Default)" radius={[3,3,0,0]} />
        <Legend iconSize={10} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function PdLgdScatter({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <ScatterChart margin={{ left: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis dataKey="pd" name="PD" tickFormatter={v => `${(v*100).toFixed(1)}%`}
          label={{ value: 'Probability of Default', position: 'insideBottom', offset: -5, style: { fontSize: 10 } }}
          tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
        <YAxis dataKey="lgd" name="LGD" tickFormatter={v => `${(v*100).toFixed(0)}%`}
          label={{ value: 'LGD', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }}
          tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
        <RechartsTooltip
          cursor={{ strokeDasharray: '3 3' }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const d = payload[0]?.payload;
            return (
              <div className="bg-[#0d1424] border border-white/[0.08] rounded-lg shadow-xl p-2 text-xs">
                <p className="font-semibold text-white/80">{d?.sector}</p>
                <p className="text-white/50">PD: {(d?.pd * 100).toFixed(2)}%</p>
                <p className="text-white/50">LGD: {(d?.lgd * 100).toFixed(1)}%</p>
                <p className="text-white/50">EL: {fmtCcy(d?.expectedLoss)}</p>
              </div>
            );
          }}
        />
        <Scatter data={data} fill="#6366f1" name="Assets">
          {data.map((d, i) => (
            <Cell key={i} fill={Object.values(SECTOR_COLORS)[i % 9]} r={Math.sqrt(d.exposure / 1e6) * 2 + 4} />
          ))}
        </Scatter>
      </ScatterChart>
    </ResponsiveContainer>
  );
}

function WhatIfPanel({ baseEl, onChange }) {
  const [carbonPrice, setCarbonPrice]       = useState(50);
  const [interestRate, setInterestRate]     = useState(4);
  const [gdpGrowth, setGdpGrowth]           = useState(2);
  const [tempTarget, setTempTarget]         = useState(2);

  const adjustedEl = useMemo(() => {
    const cpFactor  = (carbonPrice - 50) / 50 * 0.25 + 1;
    const irFactor  = (interestRate - 4) / 4 * 0.15 + 1;
    const gdpFactor = (2 - gdpGrowth) / 2 * 0.20 + 1;
    const tmpFactor = (tempTarget - 2) / 2 * 0.30 + 1;
    return baseEl * cpFactor * irFactor * gdpFactor * tmpFactor;
  }, [baseEl, carbonPrice, interestRate, gdpGrowth, tempTarget]);

  useEffect(() => { if (onChange) onChange(adjustedEl); }, [adjustedEl, onChange]);

  const pctChange = ((adjustedEl - baseEl) / baseEl * 100).toFixed(1);

  return (
    <div className="space-y-4">
      <div className={cn('p-3 rounded-lg border text-center',
        adjustedEl > baseEl ? 'bg-red-500/10 border-red-500/20' : 'bg-emerald-500/10 border-emerald-500/20'
      )}>
        <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Adjusted Expected Loss</p>
        <p className="text-2xl font-bold text-white mono-num">{fmtCcy(adjustedEl * 1e6)}</p>
        <p className={cn('text-sm font-medium mono-num', adjustedEl > baseEl ? 'text-red-400' : 'text-emerald-400')}>
          {adjustedEl >= baseEl ? '+' : ''}{pctChange}% vs base
        </p>
      </div>
      {[
        { label: 'Carbon Price ($/tCO₂)', value: carbonPrice, setter: setCarbonPrice, min: 0, max: 200, step: 5, unit: '$' },
        { label: 'Interest Rate (%)', value: interestRate, setter: setInterestRate, min: 0, max: 15, step: 0.25, unit: '%' },
        { label: 'GDP Growth (%)', value: gdpGrowth, setter: setGdpGrowth, min: -3, max: 6, step: 0.25, unit: '%' },
        { label: 'Temperature Target (°C)', value: tempTarget, setter: setTempTarget, min: 1.5, max: 4.0, step: 0.1, unit: '°C' },
      ].map(({ label, value, setter, min, max, step, unit }) => (
        <div key={label}>
          <div className="flex justify-between text-xs text-white/40 mb-1">
            <span>{label}</span>
            <span className="font-semibold tabular-nums text-cyan-300 mono-num">{unit}{value}</span>
          </div>
          <Slider min={min} max={max} step={step} value={[value]}
            onValueChange={([v]) => setter(v)} className="w-full" />
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Live Data indicator badge
// ─────────────────────────────────────────────────────────────────────────────

function LiveDataBadge({ isLive }) {
  return (
    <div className={cn(
      'flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-medium',
      isLive
        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
        : 'bg-white/[0.04] border-white/[0.08] text-white/30'
    )}>
      <div className={cn(
        'w-1.5 h-1.5 rounded-full',
        isLive ? 'bg-emerald-400 animate-pulse' : 'bg-white/20'
      )} />
      {isLive ? 'Live' : 'Demo'}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Portfolio info panel
// ─────────────────────────────────────────────────────────────────────────────

function PortfolioInfoPanel({ portfolio }) {
  if (!portfolio) return null;
  return (
    <div className="bg-cyan-400/[0.06] border border-cyan-400/10 rounded-lg p-2.5 space-y-1.5 text-xs">
      <p className="font-semibold text-cyan-300 truncate">{portfolio.name}</p>
      <div className="space-y-1">
        {portfolio.asset_count != null && (
          <div className="flex justify-between">
            <span className="text-white/40">Assets</span>
            <span className="font-medium tabular-nums text-white/70 mono-num">{portfolio.asset_count.toLocaleString()}</span>
          </div>
        )}
        {portfolio.total_exposure != null && (
          <div className="flex justify-between">
            <span className="text-white/40">Total Exposure</span>
            <span className="font-medium tabular-nums text-white/70 mono-num">{fmtCcy(portfolio.total_exposure)}</span>
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main dashboard
// ─────────────────────────────────────────────────────────────────────────────

export default function InteractiveDashboard() {
  // ── Sidebar state ──────────────────────────────────────────────────────────
  const [sidebarOpen, setSidebarOpen]           = useState(true);
  const [selectedScenarios, setSelectedScenarios] = useState(ALL_SCENARIOS);
  const [selectedSectors, setSelectedSectors]   = useState(ALL_SECTORS.slice(0, 6));
  const [selectedAssetTypes, setSelectedAssetTypes] = useState(['Loan', 'Bond', 'Equity']);
  const [horizon, setHorizon]                   = useState(2050);
  const [confidenceLevel, setConfidenceLevel]   = useState(95);
  const [discountRate, setDiscountRate]         = useState(4);
  const [activeTab, setActiveTab]               = useState('overview');

  // ── Chart type state per section ──────────────────────────────────────────
  const [exposureChartType, setExposureChartType]     = useState('bar');
  const [scenarioChartType, setScenarioChartType]     = useState('bar');
  const [scenarioMetric, setScenarioMetric]           = useState('expectedLoss');
  const [timeSeriesChartType, setTimeSeriesChartType] = useState('line');
  const [emissionsChartType, setEmissionsChartType]   = useState('bar');

  // ── API / portfolio state ─────────────────────────────────────────────────
  const [portfolios, setPortfolios]                 = useState([]);
  const [portfoliosLoading, setPortfoliosLoading]   = useState(false);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState('');
  const [isLiveData, setIsLiveData]                 = useState(false);

  // ── Live analysis run state ───────────────────────────────────────────────
  const [analysisRunning, setAnalysisRunning]       = useState(false);
  const [kpiLoading, setKpiLoading]                 = useState(false);
  const [liveKpis, setLiveKpis]                     = useState(null);
  // liveKpis shape: { totalExposure, avgExpectedLoss, portfolioVar, carbonFootprint }
  const pollTimerRef = useRef(null);

  // ── Fetch portfolios on mount ──────────────────────────────────────────────
  useEffect(() => {
    setPortfoliosLoading(true);
    fetch(`${API}/api/portfolios`)
      .then(r => {
        if (!r.ok) throw new Error('non-200');
        return r.json();
      })
      .then(d => {
        const list = d.portfolios || [];
        if (list.length > 0) {
          setPortfolios(list);
          setSelectedPortfolioId(list[0].id);
          setIsLiveData(true);
        }
      })
      .catch(() => {
        // Fall back to mock — isLiveData stays false
      })
      .finally(() => setPortfoliosLoading(false));
  }, []);

  // ── Derived selectedPortfolio object ──────────────────────────────────────
  const selectedPortfolioObj = useMemo(
    () => portfolios.find(p => p.id === selectedPortfolioId) || null,
    [portfolios, selectedPortfolioId]
  );

  // ── Cleanup poll timer on unmount ─────────────────────────────────────────
  useEffect(() => {
    return () => { if (pollTimerRef.current) clearTimeout(pollTimerRef.current); };
  }, []);

  // ── Run Live Analysis ──────────────────────────────────────────────────────
  const handleRunLiveAnalysis = useCallback(async () => {
    if (analysisRunning) return;
    setAnalysisRunning(true);
    setKpiLoading(true);
    setLiveKpis(null);

    const portfolioId = selectedPortfolioId || (portfolios[0]?.id ?? null);
    const scenario    = selectedScenarios[0] || 'Net Zero 2050';

    try {
      const runRes = await fetch(`${API}/api/analysis/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_id: portfolioId,
          scenario,
          time_horizon: horizon,
        }),
      });
      if (!runRes.ok) throw new Error('run failed');
      const { run_id } = await runRes.json();

      // Poll for results every 2 seconds, timeout after 30 seconds
      const deadline = Date.now() + 30_000;
      const poll = async () => {
        if (Date.now() > deadline) {
          setAnalysisRunning(false);
          setKpiLoading(false);
          return;
        }
        try {
          const resRes = await fetch(`${API}/api/analysis/runs/${run_id}/results`);
          if (resRes.ok) {
            const results = await resRes.json();
            if (results.status === 'completed') {
              // Map backend results to KPI overrides
              const kpis = {};
              if (results.total_exposure      != null) kpis.totalExposure      = results.total_exposure;
              if (results.avg_expected_loss   != null) kpis.avgExpectedLoss    = results.avg_expected_loss;
              if (results.portfolio_var       != null) kpis.portfolioVar       = results.portfolio_var;
              if (results.carbon_footprint    != null) kpis.carbonFootprint    = results.carbon_footprint;
              setLiveKpis(kpis);
              setIsLiveData(true);
              setAnalysisRunning(false);
              setKpiLoading(false);
              return;
            }
          }
        } catch (_) { /* continue polling */ }
        pollTimerRef.current = setTimeout(poll, 2000);
      };
      pollTimerRef.current = setTimeout(poll, 2000);
    } catch (_) {
      setAnalysisRunning(false);
      setKpiLoading(false);
    }
  }, [analysisRunning, selectedPortfolioId, portfolios, selectedScenarios, horizon]);

  // ── Derived data (recomputed on filter changes) ────────────────────────────
  const portfolioData  = useMemo(() => generatePortfolioData(selectedSectors, selectedAssetTypes, horizon, confidenceLevel), [selectedSectors, selectedAssetTypes, horizon, confidenceLevel]);
  const scenarioData   = useMemo(() => generateScenarioData(selectedScenarios, selectedSectors, horizon), [selectedScenarios, selectedSectors, horizon]);
  const timeSeriesData = useMemo(() => generateTimeSeriesData(selectedScenarios, horizon), [selectedScenarios, horizon]);
  const emissionsData  = useMemo(() => generateEmissionsData(selectedSectors, horizon), [selectedSectors, horizon]);
  const sensitivityData = useMemo(() => generateSensitivityData(selectedSectors, horizon), [selectedSectors, horizon]);
  const heatmapData    = useMemo(() => generateHeatmapData(selectedScenarios, selectedSectors.slice(0, 5)), [selectedScenarios, selectedSectors]);

  // ── KPI summary stats (seed-based, used as fallback) ─────────────────────
  const seedTotalExposure = useMemo(() => portfolioData.reduce((s, d) => s + d.exposure, 0), [portfolioData]);
  const seedTotalEl       = useMemo(() => scenarioData.reduce((s, d) => s + d.expectedLoss, 0) / (scenarioData.length || 1), [scenarioData]);
  const seedVarEstimate   = useMemo(() => seedTotalExposure * (confidenceLevel / 100 - 0.89) * 3.2, [seedTotalExposure, confidenceLevel]);
  const seedTotalCarbon   = useMemo(() => emissionsData.reduce((s, d) => s + d.scope1 + d.scope2 + d.scope3, 0), [emissionsData]);
  const worstScenario     = useMemo(() => scenarioData.reduce((w, d) => d.expectedLoss > (w?.expectedLoss || 0) ? d : w, null), [scenarioData]);

  // ── KPI values — use live data if available, otherwise seed ───────────────
  const totalExposure = liveKpis?.totalExposure   ?? seedTotalExposure;
  const totalEl       = liveKpis?.avgExpectedLoss ?? seedTotalEl;
  const varEstimate   = liveKpis?.portfolioVar    ?? seedVarEstimate;
  const totalCarbon   = liveKpis?.carbonFootprint ?? seedTotalCarbon;

  // ── Toggle helpers ────────────────────────────────────────────────────────
  const toggleScenario = useCallback(s => {
    setSelectedScenarios(prev => prev.includes(s) ? (prev.length > 1 ? prev.filter(x => x !== s) : prev) : [...prev, s]);
  }, []);
  const toggleSector = useCallback(s => {
    setSelectedSectors(prev => prev.includes(s) ? (prev.length > 1 ? prev.filter(x => x !== s) : prev) : [...prev, s]);
  }, []);
  const toggleAssetType = useCallback(t => {
    setSelectedAssetTypes(prev => prev.includes(t) ? (prev.length > 1 ? prev.filter(x => x !== t) : prev) : [...prev, t]);
  }, []);

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-full min-h-screen bg-[#080e1c] font-sans" data-testid="interactive-dashboard">

      {/* ── Sidebar ────────────────────────────────────────────────────── */}
      <aside className={cn(
        'flex-shrink-0 bg-[#0b1120] border-r border-white/[0.06] flex flex-col transition-all duration-300 overflow-hidden',
        sidebarOpen ? 'w-64' : 'w-10'
      )}>
        {/* Toggle */}
        <div className="flex items-center justify-between p-2 border-b border-white/[0.05]">
          {sidebarOpen && (
            <div className="flex items-center gap-2 px-1">
              <Filter className="h-3.5 w-3.5 text-cyan-400" />
              <span className="text-xs font-semibold text-white/60 uppercase tracking-wider">Filters</span>
            </div>
          )}
          <button onClick={() => setSidebarOpen(o => !o)}
            className="p-1 rounded hover:bg-white/[0.06] text-white/30 ml-auto transition-colors">
            {sidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        </div>

        {sidebarOpen && (
          <div className="flex-1 overflow-y-auto p-3 space-y-5 text-xs">

            {/* Portfolio selector */}
            <div>
              <p className="text-[10px] font-semibold text-white/30 uppercase tracking-wider mb-2">Portfolio</p>
              {portfoliosLoading ? (
                <div className="h-7 w-full bg-white/10 rounded animate-pulse" />
              ) : (
                <Select value={selectedPortfolioId} onValueChange={setSelectedPortfolioId}>
                  <SelectTrigger className="h-7 text-xs">
                    <SelectValue placeholder="Select portfolio" />
                  </SelectTrigger>
                  <SelectContent>
                    {portfolios.map(p => (
                      <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                    ))}
                    <SelectItem value="demo">Demo Portfolio</SelectItem>
                  </SelectContent>
                </Select>
              )}

              {/* Portfolio info panel */}
              {selectedPortfolioObj && (
                <div className="mt-2">
                  <PortfolioInfoPanel portfolio={selectedPortfolioObj} />
                </div>
              )}
            </div>

            <Separator />

            {/* Scenarios */}
            <div>
              <p className="text-[10px] font-semibold text-white/30 uppercase tracking-wider mb-2">Scenarios</p>
              <div className="space-y-1.5">
                {ALL_SCENARIOS.map(s => (
                  <label key={s} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={selectedScenarios.includes(s)}
                      onCheckedChange={() => toggleScenario(s)}
                      className="h-3.5 w-3.5"
                    />
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{ backgroundColor: SCENARIO_COLORS[s] }} />
                      <span className="text-white/50 leading-tight">{s}</span>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <Separator />

            {/* Horizon */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <p className="text-[10px] font-semibold text-white/30 uppercase tracking-wider">Time Horizon</p>
                <span className="font-bold text-cyan-300 mono-num">{horizon}</span>
              </div>
              <Slider min={2025} max={2050} step={5} value={[horizon]}
                onValueChange={([v]) => setHorizon(v)} />
              <div className="flex justify-between text-white/20 mt-1 text-[10px]">
                <span>2025</span><span>2050</span>
              </div>
            </div>

            <Separator />

            {/* Sectors */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <p className="text-[10px] font-semibold text-white/30 uppercase tracking-wider">Sectors</p>
                <button onClick={() => setSelectedSectors(ALL_SECTORS)}
                  className="text-cyan-400 hover:text-cyan-300 text-[10px]">All</button>
              </div>
              <div className="space-y-1.5">
                {ALL_SECTORS.map(s => (
                  <label key={s} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={selectedSectors.includes(s)}
                      onCheckedChange={() => toggleSector(s)}
                      className="h-3.5 w-3.5"
                    />
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-sm flex-shrink-0"
                        style={{ backgroundColor: SECTOR_COLORS[s] }} />
                      <span className="text-white/50">{s}</span>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <Separator />

            {/* Asset Types */}
            <div>
              <p className="text-[10px] font-semibold text-white/30 uppercase tracking-wider mb-2">Asset Types</p>
              <div className="space-y-1.5">
                {ALL_ASSET_TYPES.map(t => (
                  <label key={t} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={selectedAssetTypes.includes(t)}
                      onCheckedChange={() => toggleAssetType(t)}
                      className="h-3.5 w-3.5"
                    />
                    <span className="text-white/50">{t}</span>
                  </label>
                ))}
              </div>
            </div>

            <Separator />

            {/* Risk parameters */}
            <div>
              <p className="text-[10px] font-semibold text-white/30 uppercase tracking-wider mb-3">Risk Parameters</p>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-white/40">VaR Confidence</span>
                    <span className="font-semibold text-cyan-300 mono-num">{confidenceLevel}%</span>
                  </div>
                  <Slider min={90} max={99.9} step={0.5} value={[confidenceLevel]}
                    onValueChange={([v]) => setConfidenceLevel(v)} />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-white/40">Discount Rate</span>
                    <span className="font-semibold text-cyan-300 mono-num">{discountRate}%</span>
                  </div>
                  <Slider min={1} max={12} step={0.25} value={[discountRate]}
                    onValueChange={([v]) => setDiscountRate(v)} />
                </div>
              </div>
            </div>

            <Separator />

            {/* Run Live Analysis button */}
            <div className="space-y-2 pt-1">
              <Button
                size="sm"
                className={cn(
                  'w-full h-8 text-xs gap-1.5 font-medium text-[#080e1c]',
                  analysisRunning
                    ? 'bg-cyan-400/50 cursor-not-allowed'
                    : 'bg-cyan-400 hover:bg-cyan-300'
                )}
                onClick={handleRunLiveAnalysis}
                disabled={analysisRunning}
              >
                {analysisRunning ? (
                  <>
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Running…
                  </>
                ) : (
                  <>
                    <Play className="h-3 w-3" />
                    Run Live Analysis
                  </>
                )}
              </Button>

              <Button
                size="sm"
                variant="outline"
                className="w-full h-7 text-xs"
                onClick={() => {
                  setLiveKpis(null);
                  setIsLiveData(portfolios.length > 0);
                }}
              >
                <RefreshCw className="h-3 w-3 mr-1" />
                Reset to Seed Data
              </Button>
            </div>
          </div>
        )}
      </aside>

      {/* ── Main ───────────────────────────────────────────────────────── */}
      <main className="flex-1 min-w-0 flex flex-col">
        {/* Header */}
        <div className="bg-[#0b1120] border-b border-white/[0.05] px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-400/10 rounded-lg">
              <LayoutDashboard className="h-5 w-5 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white">Interactive Analytics</h1>
              <p className="text-[11px] text-white/30">
                {selectedScenarios.length} scenarios · {selectedSectors.length} sectors · Horizon {horizon}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <LiveDataBadge isLive={isLiveData && !!liveKpis} />
            <Button variant="outline" size="sm" className="h-7 text-xs gap-1 border-white/10 text-white/50 hover:text-white/80 hover:border-white/20 bg-transparent">
              <Download className="h-3 w-3" />Export
            </Button>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="p-4 grid grid-cols-2 lg:grid-cols-4 gap-3">
          <KpiCard
            title="Total Portfolio Exposure"
            value={fmtCcy(totalExposure)}
            sub={liveKpis?.totalExposure ? 'From live analysis' : `${selectedSectors.length} sectors`}
            Icon={DollarSign}
            color="indigo"
            trend={(selectedScenarios.length - 2) * 3.2}
            loading={kpiLoading}
          />
          <KpiCard
            title="Avg Expected Loss"
            value={fmtCcy(totalEl * (liveKpis?.avgExpectedLoss ? 1 : 1e6))}
            sub={liveKpis?.avgExpectedLoss ? 'From live analysis' : `Horizon ${horizon}`}
            Icon={AlertTriangle}
            color="amber"
            trend={totalEl * 1.5}
            loading={kpiLoading}
          />
          <KpiCard
            title={`VaR (${confidenceLevel.toFixed(0)}%)`}
            value={fmtCcy(varEstimate)}
            sub={liveKpis?.portfolioVar ? 'From live analysis' : 'Portfolio Value at Risk'}
            Icon={Shield}
            color="red"
            trend={(confidenceLevel - 95) * 2.1}
            loading={kpiLoading}
          />
          <KpiCard
            title="Portfolio Carbon Footprint"
            value={`${(totalCarbon / 1000).toFixed(0)}kt`}
            sub={liveKpis?.carbonFootprint ? 'From live analysis' : 'CO₂e Scope 1+2+3'}
            Icon={Leaf}
            color="green"
            trend={(horizon - 2040) * 0.8}
            loading={kpiLoading}
          />
        </div>

        {/* Tabs */}
        <div className="flex-1 px-4 pb-4">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-4 h-8 text-xs gap-1">
              <TabsTrigger value="overview"  className="text-xs h-7 px-3">Portfolio Overview</TabsTrigger>
              <TabsTrigger value="climate"   className="text-xs h-7 px-3">Climate Risk</TabsTrigger>
              <TabsTrigger value="financial" className="text-xs h-7 px-3">Financial Risk</TabsTrigger>
              <TabsTrigger value="emissions" className="text-xs h-7 px-3">Emissions</TabsTrigger>
              <TabsTrigger value="sensitivity" className="text-xs h-7 px-3">Sensitivity</TabsTrigger>
            </TabsList>

            {/* ── Overview ── */}
            <TabsContent value="overview" className="space-y-4 mt-0">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <SectionCard title="Exposure by Sector & Asset Class"
                  description="Filtered by selected sectors and asset types"
                  chartType={exposureChartType} onChartTypeChange={setExposureChartType}
                  chartTypeOptions={CHART_TYPES.filter(t => ['bar','area','pie','radar'].includes(t.id))}
                >
                  <ExposureChart data={portfolioData} chartType={exposureChartType} />
                </SectionCard>

                <SectionCard title="Risk Score by Sector"
                  description="Combined transition + physical risk score (0–100)"
                >
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={portfolioData.map(d => ({ name: d.sector.split(' ').slice(-1)[0], score: d.riskScore }))}
                      margin={{ left: 5, bottom: 30 }} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                      <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
                      <YAxis type="category" dataKey="name" width={70} tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
                      <RechartsTooltip formatter={v => `${v}/100`} />
                      <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                        {portfolioData.map((d, i) => (
                          <Cell key={i}
                            fill={d.riskScore < 35 ? '#22c55e' : d.riskScore < 65 ? '#f59e0b' : '#ef4444'} />
                        ))}
                        <LabelList dataKey="score" position="right" style={{ fontSize: 10, fill: 'rgba(255,255,255,0.5)' }} formatter={v => `${v}`} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </SectionCard>
              </div>

              <SectionCard title="Carbon Intensity by Sector" description="tCO₂e / $M exposure">
                <ResponsiveContainer width="100%" height={180}>
                  <ComposedChart data={portfolioData.map(d => ({
                    name: d.sector.split(' ')[0],
                    intensity: d.carbonIntensity,
                    target: 150,
                  }))} margin={{ left: 10, bottom: 30 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} angle={-25} textAnchor="end" />
                    <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} label={{ value: 'tCO₂e/$M', angle: -90, position: 'insideLeft', style: { fontSize: 9, fill: 'rgba(255,255,255,0.25)' } }} />
                    <RechartsTooltip formatter={v => `${v} tCO₂e/$M`} />
                    <Bar dataKey="intensity" fill="#6366f1" radius={[3, 3, 0, 0]} name="Carbon Intensity">
                      {portfolioData.map((d, i) => (
                        <Cell key={i} fill={d.carbonIntensity > 300 ? '#ef4444' : d.carbonIntensity > 150 ? '#f59e0b' : '#22c55e'} />
                      ))}
                    </Bar>
                    <Line dataKey="target" stroke="rgba(255,255,255,0.2)" strokeDasharray="4 4" name="2°C Target" dot={false} />
                    <Legend iconSize={10} />
                  </ComposedChart>
                </ResponsiveContainer>
              </SectionCard>
            </TabsContent>

            {/* ── Climate Risk ── */}
            <TabsContent value="climate" className="space-y-4 mt-0">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <SectionCard title="Scenario Expected Loss Comparison"
                  description={`Across ${selectedScenarios.length} scenarios · Horizon ${horizon}`}
                  chartType={scenarioChartType} onChartTypeChange={setScenarioChartType}
                  chartTypeOptions={CHART_TYPES.filter(t => ['bar','line','radar'].includes(t.id))}
                >
                  <div className="flex justify-end mb-2">
                    <Select value={scenarioMetric} onValueChange={setScenarioMetric}>
                      <SelectTrigger className="h-6 w-44 text-xs">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="expectedLoss">Expected Loss ($M)</SelectItem>
                        <SelectItem value="transitionRisk">Transition Risk</SelectItem>
                        <SelectItem value="physicalRisk">Physical Risk</SelectItem>
                        <SelectItem value="capitalCharge">Capital Charge (%)</SelectItem>
                        <SelectItem value="co2Reduction">CO₂ Reduction (%)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <ScenarioComparisonChart data={scenarioData} chartType={scenarioChartType} metric={scenarioMetric} />
                </SectionCard>

                <SectionCard title="Scenario × Sector Risk Heatmap"
                  description="Expected Loss % by scenario and sector">
                  <RiskHeatmap data={heatmapData} sectors={selectedSectors.slice(0, 5)} />
                </SectionCard>
              </div>

              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <SectionCard title="Loss Trajectory Over Time"
                  chartType={timeSeriesChartType} onChartTypeChange={setTimeSeriesChartType}
                  chartTypeOptions={CHART_TYPES.filter(t => ['line', 'area'].includes(t.id))}
                  description={`Expected Loss $M by scenario to ${horizon}`}
                >
                  <TimeSeriesChart data={timeSeriesData} scenarios={selectedScenarios} chartType={timeSeriesChartType} />
                </SectionCard>

                <SectionCard title="Transition vs Physical Risk Breakdown"
                  description="By scenario">
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={scenarioData} margin={{ left: 10, bottom: 30 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="scenario" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} angle={-20} textAnchor="end" />
                      <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
                      <RechartsTooltip content={<CustomTooltip formatter={v => `${v.toFixed(1)}`} />} />
                      <Bar dataKey="transitionRisk" name="Transition Risk" fill="#6366f1" stackId="a" />
                      <Bar dataKey="physicalRisk" name="Physical Risk" fill="#ef4444" stackId="a" radius={[3, 3, 0, 0]} />
                      <Legend iconSize={10} />
                    </BarChart>
                  </ResponsiveContainer>
                </SectionCard>
              </div>
            </TabsContent>

            {/* ── Financial Risk ── */}
            <TabsContent value="financial" className="space-y-4 mt-0">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <SectionCard title="IFRS 9 ECL by Staging" description="Climate-adjusted Expected Credit Loss by stage">
                  <ECLStageChart data={portfolioData} />
                </SectionCard>

                <SectionCard title="PD / LGD Bubble Chart"
                  description="Bubble size = exposure; colour = sector">
                  <PdLgdScatter data={portfolioData} />
                </SectionCard>
              </div>

              <SectionCard title="Capital Charge by Scenario" description="Regulatory capital requirement (%)">
                <ResponsiveContainer width="100%" height={200}>
                  <ComposedChart data={scenarioData} margin={{ left: 10, bottom: 30 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="scenario" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} angle={-20} textAnchor="end" />
                    <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} label={{ value: 'Capital %', angle: -90, position: 'insideLeft', style: { fontSize: 9, fill: 'rgba(255,255,255,0.25)' } }} />
                    <RechartsTooltip formatter={v => `${v.toFixed(2)}%`} />
                    <Bar dataKey="capitalCharge" fill="#6366f1" radius={[3,3,0,0]} name="Capital Charge">
                      {scenarioData.map((d,i) => <Cell key={i} fill={SCENARIO_COLORS[d.scenario] || '#6366f1'} />)}
                    </Bar>
                    <ReferenceLine y={8} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Min 8%', fill: '#ef4444', fontSize: 10 }} />
                    <Line dataKey="capitalCharge" stroke="rgba(255,255,255,0.2)" strokeWidth={2} dot={false} name="Trend" />
                  </ComposedChart>
                </ResponsiveContainer>
              </SectionCard>
            </TabsContent>

            {/* ── Emissions ── */}
            <TabsContent value="emissions" className="space-y-4 mt-0">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <SectionCard title="GHG Emissions by Scope & Sector"
                  chartType={emissionsChartType} onChartTypeChange={setEmissionsChartType}
                  chartTypeOptions={CHART_TYPES.filter(t => ['bar','pie'].includes(t.id))}
                  description="Financed emissions (tCO₂e)"
                >
                  <EmissionsChart data={emissionsData} chartType={emissionsChartType} />
                </SectionCard>

                <SectionCard title="Paris Alignment Status" description="By sector vs. 2030 Science-Based Target">
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {emissionsData.map(d => {
                      const total = d.scope1 + d.scope2 + d.scope3;
                      const pct = Math.min((d.target2030 / total) * 100, 100);
                      const aligned = total < d.target2030 * 3;
                      return (
                        <div key={d.sector} className="flex items-center gap-2 text-xs">
                          <div className="w-28 text-white/50 font-medium truncate">{d.sector}</div>
                          <div className="flex-1 bg-white/[0.06] rounded-full h-2 overflow-hidden">
                            <div className="h-full rounded-full transition-all"
                              style={{ width: `${pct}%`, backgroundColor: aligned ? '#10b981' : '#ef4444' }} />
                          </div>
                          <span className={cn('text-[10px] font-medium mono-num px-1.5 py-0.5 rounded',
                            aligned ? 'text-emerald-400 bg-emerald-400/10' : 'text-red-400 bg-red-400/10'
                          )}>
                            {aligned ? 'Aligned' : 'Off-Track'}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </SectionCard>
              </div>

              <SectionCard title="Weighted Average Carbon Intensity (WACI)" description="Portfolio WACI vs. benchmark (tCO₂e/$M revenue)">
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={emissionsData.map(d => ({
                    name: d.sector.split(' ')[0],
                    waci: Math.round((d.scope1 + d.scope2) / 50),
                    benchmark: 80,
                  }))} margin={{ left: 5, bottom: 30 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} angle={-25} textAnchor="end" />
                    <YAxis tick={{ fontSize: 10, fill: 'rgba(255,255,255,0.3)', fontFamily: 'IBM Plex Mono' }} />
                    <RechartsTooltip formatter={v => `${v} tCO₂e/$M`} />
                    <Bar dataKey="waci" name="Portfolio WACI" radius={[3,3,0,0]}>
                      {emissionsData.map((d, i) => {
                        const waci = Math.round((d.scope1 + d.scope2) / 50);
                        return <Cell key={i} fill={waci > 80 ? '#ef4444' : '#22c55e'} />;
                      })}
                    </Bar>
                    <ReferenceLine y={80} stroke="#6366f1" strokeDasharray="4 4" label={{ value: 'Benchmark 80', fill: '#6366f1', fontSize: 10 }} />
                    <Legend iconSize={10} />
                  </BarChart>
                </ResponsiveContainer>
              </SectionCard>
            </TabsContent>

            {/* ── Sensitivity ── */}
            <TabsContent value="sensitivity" className="space-y-4 mt-0">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                <SectionCard title="Tornado Chart — Key Risk Drivers"
                  description="Impact on Expected Loss (% change)">
                  <TornadoChart data={sensitivityData} />
                </SectionCard>

                <SectionCard title="What-If Parameter Studio"
                  description="Adjust macro parameters and see real-time impact on Expected Loss">
                  <WhatIfPanel baseEl={totalEl} />
                </SectionCard>
              </div>

              <SectionCard title="Scenario Sensitivity Matrix"
                description="Expected Loss sensitivity across scenario × horizon combinations">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs border-separate border-spacing-0.5">
                    <thead>
                      <tr>
                        <th className="text-left p-1.5 text-white/30 font-normal">Scenario</th>
                        {[2030, 2035, 2040, 2045, 2050].map(y => (
                          <th key={y} className="text-center p-1.5 text-white/30 font-medium mono-num">{y}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {selectedScenarios.map((s, si) => {
                        return (
                          <tr key={s}>
                            <td className="p-1.5 font-medium text-white/50 whitespace-nowrap">
                              <div className="flex items-center gap-1.5">
                                <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: SCENARIO_COLORS[s] }} />
                                {s}
                              </div>
                            </td>
                            {[2030, 2035, 2040, 2045, 2050].map(y => {
                              const mult = (si + 1) * 0.4;
                              const val = parseFloat((5 + mult * (y - 2025) / 5 + si * 2).toFixed(1));
                              const isHorizon = y === horizon;
                              const cellBg = val > 20 ? 'rgba(239,68,68,0.25)' : val > 12 ? 'rgba(249,115,22,0.22)' : val > 6 ? 'rgba(245,158,11,0.18)' : 'rgba(20,184,166,0.18)';
                              const cellColor = val > 20 ? '#f87171' : val > 12 ? '#fb923c' : val > 6 ? '#fbbf24' : '#5eead4';
                              return (
                                <td key={y} className={cn(
                                  'text-center p-1.5 rounded font-medium tabular-nums mono-num',
                                  isHorizon ? 'ring-1 ring-cyan-400/50' : ''
                                )}
                                  style={{ backgroundColor: cellBg, color: cellColor }}>
                                  {val}%
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  <p className="text-[11px] text-white/30 mt-2">Ring = selected horizon. Values = Expected Loss % of exposure.</p>
                </div>
              </SectionCard>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}
