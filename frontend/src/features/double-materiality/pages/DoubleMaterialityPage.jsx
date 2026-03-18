/**
 * DoubleMaterialityPage.jsx
 * Route: /double-materiality
 *
 * Comprehensive Double Materiality Assessment (DMA) module aligned with CSRD / ESRS.
 * Covers all 10 ESRS topics (E1-E5, S1-S4, G1) across impact materiality,
 * financial materiality, stakeholder engagement quality, and cross-framework mapping.
 *
 * Backend API:
 *   POST /api/v1/double-materiality/impact-materiality
 *   POST /api/v1/double-materiality/financial-materiality
 *   POST /api/v1/double-materiality/assess
 *   POST /api/v1/double-materiality/stakeholder-engagement
 *   POST /api/v1/double-materiality/sector-defaults
 *   POST /api/v1/double-materiality/cross-framework
 *
 * Tabs:
 *   1. Double Materiality Matrix  -- scatter plot quadrant view
 *   2. Impact Materiality         -- scale / scope / irremediability breakdown
 *   3. Financial Materiality      -- risk vs opportunity, heatmap
 *   4. Stakeholder Engagement     -- quality dashboard
 *   5. Cross-Framework Mapping    -- GRI / TCFD / ISSB / UN SDG interop
 *
 * Design: digital skeleton -- white bg, black text, no cyan, no dark backgrounds.
 */
import React, { useState, useMemo } from 'react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, BarChart, Bar, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, ReferenceLine, LabelList,
} from 'recharts';
import {
  Target, TrendingUp, TrendingDown, Shield, Users, Link2,
  ChevronDown, ChevronUp, AlertTriangle, CheckCircle, Activity,
  BarChart3, Layers, Globe, Leaf, Building2, Factory, Cpu,
  Wheat, ArrowRight, Info, CircleDot, Gauge, Settings2, Grid3X3,
} from 'lucide-react';
import DemoBanner from '../../../components/shared/DemoBanner';

// ---------------------------------------------------------------------------
// Deterministic seed-based pseudo-random
// ---------------------------------------------------------------------------
function seededRandom(seed) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

// ---------------------------------------------------------------------------
// Tooltip style (consistent across all charts)
// ---------------------------------------------------------------------------
const TOOLTIP_STYLE = {
  backgroundColor: '#ffffff',
  border: '1px solid rgba(0,0,0,0.08)',
  color: '#111',
};

// ---------------------------------------------------------------------------
// ESRS Topics & Colour Scheme
// ---------------------------------------------------------------------------
const ESRS_TOPICS = [
  { id: 'E1', label: 'E1 Climate Change',       category: 'E', short: 'E1' },
  { id: 'E2', label: 'E2 Pollution',             category: 'E', short: 'E2' },
  { id: 'E3', label: 'E3 Water & Marine',        category: 'E', short: 'E3' },
  { id: 'E4', label: 'E4 Biodiversity',          category: 'E', short: 'E4' },
  { id: 'E5', label: 'E5 Circular Economy',      category: 'E', short: 'E5' },
  { id: 'S1', label: 'S1 Own Workforce',         category: 'S', short: 'S1' },
  { id: 'S2', label: 'S2 Workers in VC',         category: 'S', short: 'S2' },
  { id: 'S3', label: 'S3 Affected Communities',  category: 'S', short: 'S3' },
  { id: 'S4', label: 'S4 Consumers & End-users', category: 'S', short: 'S4' },
  { id: 'G1', label: 'G1 Business Conduct',      category: 'G', short: 'G1' },
];

const CATEGORY_COLORS = { E: '#10b981', S: '#3b82f6', G: '#f59e0b' };
const CATEGORY_BG     = { E: 'bg-emerald-50 text-emerald-700', S: 'bg-blue-50 text-blue-700', G: 'bg-amber-50 text-amber-700' };

// ---------------------------------------------------------------------------
// Sectors
// ---------------------------------------------------------------------------
const SECTORS = [
  { id: 'energy',             label: 'Energy' },
  { id: 'financial_services', label: 'Financial Services' },
  { id: 'manufacturing',      label: 'Manufacturing' },
  { id: 'real_estate',        label: 'Real Estate' },
  { id: 'technology',         label: 'Technology' },
  { id: 'agriculture',        label: 'Agriculture' },
];

// ---------------------------------------------------------------------------
// Stakeholder groups and engagement methods
// ---------------------------------------------------------------------------
const STAKEHOLDER_GROUPS = [
  'employees', 'customers', 'suppliers', 'investors', 'regulators',
  'communities', 'ngos', 'unions', 'board_members', 'industry_peers',
  'rating_agencies', 'academic_experts',
];

const ENGAGEMENT_METHODS = [
  'survey', 'interview', 'workshop', 'focus_group', 'advisory_panel', 'grievance_mechanism',
];

// ---------------------------------------------------------------------------
// Cross-framework reference data
// ---------------------------------------------------------------------------
const CROSS_FRAMEWORK = {
  E1: { gri: 'GRI 305 Emissions',            tcfd: 'Strategy / Metrics',   issb: 'IFRS S2 para 13-22', sdgs: [7, 13] },
  E2: { gri: 'GRI 305-7 / 306',              tcfd: 'Risk Management',      issb: 'IFRS S2 para 25',    sdgs: [3, 6, 12] },
  E3: { gri: 'GRI 303 Water',                 tcfd: 'Strategy',             issb: 'IFRS S2 para 21',    sdgs: [6, 14] },
  E4: { gri: 'GRI 304 Biodiversity',          tcfd: 'Strategy / Metrics',   issb: 'IFRS S2 para 21',    sdgs: [14, 15] },
  E5: { gri: 'GRI 301 Materials / 306 Waste', tcfd: 'Metrics',              issb: 'IFRS S2 para 29',    sdgs: [12] },
  S1: { gri: 'GRI 401-405',                   tcfd: '--',                   issb: 'IFRS S1 para 25',    sdgs: [5, 8, 10] },
  S2: { gri: 'GRI 414 Supplier Social',       tcfd: '--',                   issb: 'IFRS S1 para 25',    sdgs: [8] },
  S3: { gri: 'GRI 411 / 413',                 tcfd: '--',                   issb: 'IFRS S1 para 25',    sdgs: [1, 2, 16] },
  S4: { gri: 'GRI 416-418',                   tcfd: '--',                   issb: 'IFRS S1 para 25',    sdgs: [3, 16] },
  G1: { gri: 'GRI 205-206',                   tcfd: 'Governance',           issb: 'IFRS S1 para 6-9',   sdgs: [16] },
};

// ---------------------------------------------------------------------------
// Deterministic data generation per sector
// ---------------------------------------------------------------------------
function generateSectorData(sectorId) {
  const sectorSeed = SECTORS.findIndex(s => s.id === sectorId) + 1;
  const rng = seededRandom(sectorSeed * 7919);

  // Base weights per sector: energy skews E1/E2 high, tech skews G1/S4 high, etc.
  const sectorBias = {
    energy:             { E1: 1.5, E2: 1.3, E3: 1.1, E4: 1.0, E5: 0.9, S1: 1.0, S2: 0.8, S3: 1.2, S4: 0.6, G1: 1.0 },
    financial_services: { E1: 1.2, E2: 0.5, E3: 0.4, E4: 0.6, E5: 0.5, S1: 1.1, S2: 0.7, S3: 0.6, S4: 1.3, G1: 1.4 },
    manufacturing:      { E1: 1.3, E2: 1.4, E3: 1.0, E4: 0.8, E5: 1.3, S1: 1.2, S2: 1.1, S3: 0.9, S4: 1.0, G1: 1.0 },
    real_estate:        { E1: 1.4, E2: 0.7, E3: 0.9, E4: 0.8, E5: 1.1, S1: 0.9, S2: 0.5, S3: 1.3, S4: 0.7, G1: 1.1 },
    technology:         { E1: 0.8, E2: 0.4, E3: 0.5, E4: 0.3, E5: 0.9, S1: 1.3, S2: 0.9, S3: 0.6, S4: 1.4, G1: 1.3 },
    agriculture:        { E1: 1.1, E2: 1.2, E3: 1.4, E4: 1.5, E5: 1.0, S1: 0.9, S2: 1.2, S3: 1.3, S4: 0.8, G1: 0.8 },
  };

  const bias = sectorBias[sectorId] || sectorBias.energy;

  return ESRS_TOPICS.map(topic => {
    const b = bias[topic.id] || 1.0;
    const clamp = (v) => Math.min(5, Math.max(1, v));

    // Impact materiality dimensions
    const scale          = clamp(Math.round((rng() * 3 + 1.5) * b * 10) / 10);
    const scope          = clamp(Math.round((rng() * 3 + 1.2) * b * 10) / 10);
    const irremediability = clamp(Math.round((rng() * 3 + 1.0) * b * 10) / 10);
    const impactSeverity = Math.round(((scale * 0.4 + scope * 0.35 + irremediability * 0.25)) * 100) / 100;

    // Financial materiality dimensions
    const riskLikelihood      = clamp(Math.round((rng() * 3 + 1.3) * b * 10) / 10);
    const riskMagnitude       = clamp(Math.round((rng() * 3 + 1.1) * b * 10) / 10);
    const opportunityMagnitude = clamp(Math.round((rng() * 3 + 0.8) * b * 10) / 10);
    const financialScore = Math.round(((riskLikelihood * 0.35 + riskMagnitude * 0.35 + opportunityMagnitude * 0.30)) * 100) / 100;

    // Time horizon
    const horizons = ['short_term', 'medium_term', 'long_term'];
    const horizon = horizons[Math.floor(rng() * 3)];

    return {
      ...topic,
      scale, scope, irremediability, impactSeverity,
      riskLikelihood, riskMagnitude, opportunityMagnitude, financialScore,
      horizon,
    };
  });
}

function generateStakeholderData(sectorId) {
  const sectorSeed = SECTORS.findIndex(s => s.id === sectorId) + 1;
  const rng = seededRandom(sectorSeed * 6271);
  return STAKEHOLDER_GROUPS.map(group => {
    const method = ENGAGEMENT_METHODS[Math.floor(rng() * ENGAGEMENT_METHODS.length)];
    const quality = Math.round((rng() * 50 + 45) * 10) / 10;
    const coverage = Math.round((rng() * 60 + 30) * 10) / 10;
    const responseRate = Math.round((rng() * 50 + 35) * 10) / 10;
    const representativeness = Math.round((rng() * 40 + 50) * 10) / 10;
    const topicsCovered = Math.floor(rng() * 6 + 4);
    return { group, method, quality, coverage, responseRate, representativeness, topicsCovered };
  });
}

// ---------------------------------------------------------------------------
// Classification logic
// ---------------------------------------------------------------------------
function classify(impactSeverity, financialScore, impactThreshold, financialThreshold) {
  const impactMat   = impactSeverity >= impactThreshold;
  const financialMat = financialScore >= financialThreshold;
  if (impactMat && financialMat) return 'double_material';
  if (impactMat)                 return 'impact_only';
  if (financialMat)              return 'financial_only';
  return 'not_material';
}

const CLASS_CONFIG = {
  double_material: { label: 'Double Material', badge: 'bg-[#164E8A] text-white', dot: '#111' },
  impact_only:     { label: 'Impact Only',     badge: 'bg-emerald-50 text-emerald-700', dot: '#10b981' },
  financial_only:  { label: 'Financial Only',   badge: 'bg-blue-50 text-blue-700', dot: '#3b82f6' },
  not_material:    { label: 'Not Material',     badge: 'bg-gray-100 text-gray-500', dot: '#9ca3af' },
};

const HORIZON_LABEL = { short_term: 'Short-term', medium_term: 'Medium-term', long_term: 'Long-term' };

// ---------------------------------------------------------------------------
// Shared UI components
// ---------------------------------------------------------------------------
function Section({ title, children, defaultOpen = true, icon: Icon }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden mb-4 bg-white">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4 text-gray-500" />}
          <span className="font-medium text-sm text-gray-700">{title}</span>
        </div>
        {open
          ? <ChevronUp className="h-3.5 w-3.5 text-gray-400" />
          : <ChevronDown className="h-3.5 w-3.5 text-gray-400" />}
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
}

function KpiCard({ label, value, sub, icon: Icon }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-1">
        {Icon && <Icon className="h-3.5 w-3.5 text-gray-500" />}
        <p className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</p>
      </div>
      <p className="text-xl font-semibold text-gray-900 tracking-tight">{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function TabButton({ label, active, onClick, icon: Icon }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium rounded-md transition-colors flex items-center gap-1.5 ${
        active
          ? 'bg-[#164E8A] text-white'
          : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
      }`}
    >
      {Icon && <Icon className="h-3.5 w-3.5" />}
      {label}
    </button>
  );
}

function Badge({ text, className }) {
  return (
    <span className={`inline-flex items-center text-[11px] font-medium px-2 py-0.5 rounded-full ${className}`}>
      {text}
    </span>
  );
}

function SectorSelect({ value, onChange }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 uppercase tracking-wider">Sector</span>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="text-sm border border-gray-200 rounded-md px-3 py-1.5 bg-white text-gray-900 focus:outline-none focus:ring-1 focus:ring-black/10"
      >
        {SECTORS.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
      </select>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Custom scatter dot
// ---------------------------------------------------------------------------
function MatrixDot(props) {
  const { cx, cy, payload } = props;
  const cat = payload.category;
  const fill = CATEGORY_COLORS[cat] || '#6b7280';
  return (
    <g>
      <circle cx={cx} cy={cy} r={10} fill={fill} fillOpacity={0.18} stroke={fill} strokeWidth={1.5} />
      <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="central"
        fill={fill} fontSize={9} fontWeight={600}>{payload.short}</text>
    </g>
  );
}

// ---------------------------------------------------------------------------
// Custom heatmap cell renderer
// ---------------------------------------------------------------------------
function HeatCell({ value, max = 5 }) {
  const pct = (value / max) * 100;
  let bg = 'bg-gray-50 text-gray-400';
  if (pct >= 80) bg = 'bg-red-50 text-red-700';
  else if (pct >= 60) bg = 'bg-amber-50 text-amber-700';
  else if (pct >= 40) bg = 'bg-yellow-50 text-yellow-700';
  else if (pct >= 20) bg = 'bg-emerald-50 text-emerald-700';
  return (
    <td className={`px-2 py-1.5 text-center text-xs font-medium rounded ${bg}`}>
      {value.toFixed(1)}
    </td>
  );
}

// ===========================================================================
// MAIN COMPONENT
// ===========================================================================
export default function DoubleMaterialityPage() {
  const [activeTab, setActiveTab] = useState('matrix');
  const [sector, setSector] = useState('energy');
  const [impactThreshold, setImpactThreshold] = useState(3.0);
  const [financialThreshold, setFinancialThreshold] = useState(3.0);

  // ---- Computed data -------------------------------------------------------
  const topicData = useMemo(() => generateSectorData(sector), [sector]);
  const stakeholderData = useMemo(() => generateStakeholderData(sector), [sector]);

  const classified = useMemo(() => topicData.map(t => ({
    ...t,
    classification: classify(t.impactSeverity, t.financialScore, impactThreshold, financialThreshold),
  })), [topicData, impactThreshold, financialThreshold]);

  const counts = useMemo(() => {
    const c = { double_material: 0, impact_only: 0, financial_only: 0, not_material: 0 };
    classified.forEach(t => { c[t.classification]++; });
    c.total_material = c.double_material + c.impact_only + c.financial_only;
    return c;
  }, [classified]);

  // ---- Stakeholder aggregate -----------------------------------------------
  const stakeholderAgg = useMemo(() => {
    const total = stakeholderData.reduce((a, s) => a + s.quality, 0);
    const avgQuality = total / stakeholderData.length;
    const avgCoverage = stakeholderData.reduce((a, s) => a + s.coverage, 0) / stakeholderData.length;
    const avgResponse = stakeholderData.reduce((a, s) => a + s.responseRate, 0) / stakeholderData.length;
    const methodCounts = {};
    stakeholderData.forEach(s => { methodCounts[s.method] = (methodCounts[s.method] || 0) + 1; });
    return { avgQuality, avgCoverage, avgResponse, methodCounts };
  }, [stakeholderData]);

  // ---- Cross-framework coverage --------------------------------------------
  const frameworkCoverage = useMemo(() => {
    const material = classified.filter(t => t.classification !== 'not_material');
    const total = material.length || 1;
    let gri = 0, tcfd = 0, issb = 0, sdg = 0;
    material.forEach(t => {
      const cf = CROSS_FRAMEWORK[t.id];
      if (cf) {
        if (cf.gri !== '--') gri++;
        if (cf.tcfd !== '--') tcfd++;
        if (cf.issb !== '--') issb++;
        if (cf.sdgs && cf.sdgs.length > 0) sdg++;
      }
    });
    return {
      gri: Math.round((gri / total) * 100),
      tcfd: Math.round((tcfd / total) * 100),
      issb: Math.round((issb / total) * 100),
      sdg: Math.round((sdg / total) * 100),
    };
  }, [classified]);

  // =========================================================================
  // TAB CONTENT RENDERERS
  // =========================================================================

  // ---- Tab 1: Double Materiality Matrix ------------------------------------
  const renderMatrixTab = () => {
    const scatterData = classified.map(t => ({
      x: t.impactSeverity,
      y: t.financialScore,
      ...t,
    }));

    return (
      <div className="space-y-4">
        {/* KPI cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <KpiCard label="Total Material Topics" value={counts.total_material}
            sub={`of ${ESRS_TOPICS.length} assessed`} icon={Target} />
          <KpiCard label="Double Material" value={counts.double_material}
            sub="Impact + Financial" icon={Layers} />
          <KpiCard label="Impact Only" value={counts.impact_only}
            sub="Stakeholder driven" icon={Users} />
          <KpiCard label="Financial Only" value={counts.financial_only}
            sub="Risk-driven" icon={TrendingUp} />
        </div>

        {/* Threshold controls */}
        <Section title="Threshold Configuration" icon={Settings2} defaultOpen={false}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-xs text-gray-500 block mb-2">
                Impact Materiality Threshold: <span className="font-semibold text-gray-900">{impactThreshold.toFixed(1)}</span>
              </label>
              <input type="range" min="1" max="5" step="0.1" value={impactThreshold}
                onChange={e => setImpactThreshold(parseFloat(e.target.value))}
                className="w-full accent-black h-1.5" />
              <div className="flex justify-between text-[10px] text-gray-500 mt-1"><span>1.0</span><span>5.0</span></div>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-2">
                Financial Materiality Threshold: <span className="font-semibold text-gray-900">{financialThreshold.toFixed(1)}</span>
              </label>
              <input type="range" min="1" max="5" step="0.1" value={financialThreshold}
                onChange={e => setFinancialThreshold(parseFloat(e.target.value))}
                className="w-full accent-black h-1.5" />
              <div className="flex justify-between text-[10px] text-gray-500 mt-1"><span>1.0</span><span>5.0</span></div>
            </div>
          </div>
        </Section>

        {/* Scatter plot */}
        <Section title="Materiality Matrix" icon={CircleDot}>
          <div className="relative">
            {/* Quadrant labels */}
            <div className="absolute top-2 left-16 text-[10px] text-emerald-600/60 font-medium z-10">Impact Only</div>
            <div className="absolute top-2 right-8 text-[10px] text-gray-600 font-semibold z-10">Double Material</div>
            <div className="absolute bottom-10 left-16 text-[10px] text-gray-400 font-medium z-10">Not Material</div>
            <div className="absolute bottom-10 right-8 text-[10px] text-blue-600/60 font-medium z-10">Financial Only</div>

            <ResponsiveContainer width="100%" height={420}>
              <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                <XAxis type="number" dataKey="x" name="Impact Severity" domain={[1, 5]}
                  ticks={[1, 2, 3, 4, 5]} label={{ value: 'Impact Severity', position: 'bottom', offset: 0, style: { fill: '#666', fontSize: 11 } }}
                  tick={{ fontSize: 10, fill: '#999' }} />
                <YAxis type="number" dataKey="y" name="Financial Score" domain={[1, 5]}
                  ticks={[1, 2, 3, 4, 5]} label={{ value: 'Financial Score', angle: -90, position: 'insideLeft', offset: 5, style: { fill: '#666', fontSize: 11 } }}
                  tick={{ fontSize: 10, fill: '#999' }} />
                <ReferenceLine x={impactThreshold} stroke="rgba(0,0,0,0.15)" strokeDasharray="4 4" />
                <ReferenceLine y={financialThreshold} stroke="rgba(0,0,0,0.15)" strokeDasharray="4 4" />
                <Tooltip contentStyle={TOOLTIP_STYLE}
                  formatter={(val, name) => [val.toFixed(2), name]}
                  labelFormatter={() => ''} />
                <Scatter data={scatterData} shape={<MatrixDot />} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          {/* Legend */}
          <div className="flex items-center gap-4 mt-2 justify-center">
            {Object.entries(CATEGORY_COLORS).map(([k, c]) => (
              <div key={k} className="flex items-center gap-1.5">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: c, opacity: 0.7 }} />
                <span className="text-[11px] text-gray-500">
                  {k === 'E' ? 'Environmental' : k === 'S' ? 'Social' : 'Governance'}
                </span>
              </div>
            ))}
          </div>
        </Section>

        {/* Results table */}
        <Section title="Topic-Level Results" icon={BarChart3}>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">Topic</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Category</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Impact Severity</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Financial Score</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Classification</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Time Horizon</th>
                </tr>
              </thead>
              <tbody>
                {classified.map(t => {
                  const cls = CLASS_CONFIG[t.classification];
                  return (
                    <tr key={t.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-2 font-medium text-gray-800">{t.label}</td>
                      <td className="py-2 px-2 text-center">
                        <Badge text={t.category} className={CATEGORY_BG[t.category]} />
                      </td>
                      <td className="py-2 px-2 text-center font-mono text-gray-700">{t.impactSeverity.toFixed(2)}</td>
                      <td className="py-2 px-2 text-center font-mono text-gray-700">{t.financialScore.toFixed(2)}</td>
                      <td className="py-2 px-2 text-center">
                        <Badge text={cls.label} className={cls.badge} />
                      </td>
                      <td className="py-2 px-2 text-center text-gray-500">{HORIZON_LABEL[t.horizon]}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Section>
      </div>
    );
  };

  // ---- Tab 2: Impact Materiality -------------------------------------------
  const renderImpactTab = () => {
    // Stacked bar data
    const barData = classified.map(t => ({
      name: t.short,
      Scale: t.scale,
      Scope: t.scope,
      Irremediability: t.irremediability,
      severity: t.impactSeverity,
    }));

    // Radar data
    const radarData = classified.map(t => ({
      topic: t.short,
      severity: t.impactSeverity,
    }));

    // Rationale lookup
    const rationale = (t) => {
      if (t.impactSeverity >= 4.0) return 'High severity -- requires immediate action and detailed ESRS disclosure';
      if (t.impactSeverity >= 3.0) return 'Moderate severity -- material, standard ESRS disclosure required';
      if (t.impactSeverity >= 2.0) return 'Low severity -- monitor and reassess annually';
      return 'Negligible impact -- limited disclosure needed';
    };

    return (
      <div className="space-y-4">
        {/* Impact summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <KpiCard label="Avg Impact Severity"
            value={(classified.reduce((a, t) => a + t.impactSeverity, 0) / classified.length).toFixed(2)}
            sub="Across all topics" icon={Activity} />
          <KpiCard label="Highest Severity"
            value={Math.max(...classified.map(t => t.impactSeverity)).toFixed(2)}
            sub={classified.reduce((best, t) => t.impactSeverity > best.impactSeverity ? t : best, classified[0]).label}
            icon={AlertTriangle} />
          <KpiCard label="Material (Impact)"
            value={classified.filter(t => t.impactSeverity >= impactThreshold).length}
            sub={`Threshold: ${impactThreshold.toFixed(1)}`} icon={CheckCircle} />
          <KpiCard label="Avg Irremediability"
            value={(classified.reduce((a, t) => a + t.irremediability, 0) / classified.length).toFixed(2)}
            sub="Weighted 25%" icon={Shield} />
        </div>

        {/* Horizontal stacked bar chart */}
        <Section title="Impact Severity Breakdown by Topic" icon={BarChart3}>
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={barData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
              <XAxis type="number" domain={[0, 15]} tick={{ fontSize: 10, fill: '#999' }}
                label={{ value: 'Weighted Contribution', position: 'bottom', offset: 0, style: { fill: '#666', fontSize: 11 } }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#666' }} width={30} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="Scale" stackId="a" fill="#111111" fillOpacity={0.75} radius={[0, 0, 0, 0]} />
              <Bar dataKey="Scope" stackId="a" fill="#555555" fillOpacity={0.65} />
              <Bar dataKey="Irremediability" stackId="a" fill="#aaaaaa" fillOpacity={0.55} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Section>

        {/* Radar chart */}
        <Section title="Impact Severity Radar" icon={Target}>
          <div className="flex justify-center">
            <ResponsiveContainer width="100%" height={340}>
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="75%">
                <PolarGrid stroke="rgba(0,0,0,0.06)" />
                <PolarAngleAxis dataKey="topic" tick={{ fontSize: 10, fill: '#666' }} />
                <PolarRadiusAxis angle={90} domain={[0, 5]} tick={{ fontSize: 9, fill: '#999' }} />
                <Radar name="Impact Severity" dataKey="severity" stroke="#111"
                  fill="#111" fillOpacity={0.12} strokeWidth={1.5} dot={{ r: 3, fill: '#111' }} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </Section>

        {/* Detailed breakdown table */}
        <Section title="Per-Topic Impact Breakdown" icon={Layers}>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">Topic</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Scale (40%)</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Scope (35%)</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Irremediability (25%)</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Severity</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Material?</th>
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">Rationale</th>
                </tr>
              </thead>
              <tbody>
                {classified.map(t => (
                  <tr key={t.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-2 px-2 font-medium text-gray-800">{t.label}</td>
                    <HeatCell value={t.scale} />
                    <HeatCell value={t.scope} />
                    <HeatCell value={t.irremediability} />
                    <td className="py-2 px-2 text-center font-mono font-semibold text-gray-900">{t.impactSeverity.toFixed(2)}</td>
                    <td className="py-2 px-2 text-center">
                      {t.impactSeverity >= impactThreshold
                        ? <Badge text="Yes" className="bg-emerald-50 text-emerald-600" />
                        : <Badge text="No" className="bg-gray-100 text-gray-500" />}
                    </td>
                    <td className="py-2 px-2 text-gray-500 max-w-[220px]">{rationale(t)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      </div>
    );
  };

  // ---- Tab 3: Financial Materiality ----------------------------------------
  const renderFinancialTab = () => {
    // Grouped bar: risk vs opportunity
    const groupedData = classified.map(t => ({
      name: t.short,
      'Risk Score': Math.round((t.riskLikelihood * 0.5 + t.riskMagnitude * 0.5) * 100) / 100,
      'Opportunity Score': t.opportunityMagnitude,
    }));

    // Heatmap: likelihood rows x magnitude columns
    const likelihoodBuckets = [1, 2, 3, 4, 5];
    const magnitudeBuckets  = [1, 2, 3, 4, 5];
    const heatmapGrid = likelihoodBuckets.map(l => {
      const row = { likelihood: l };
      magnitudeBuckets.forEach(m => {
        const matching = classified.filter(t =>
          Math.round(t.riskLikelihood) === l && Math.round(t.riskMagnitude) === m
        );
        row[`m${m}`] = matching.length;
        row[`m${m}_topics`] = matching.map(t => t.short).join(', ');
      });
      return row;
    });

    const likelihoodLabels = ['Very Low', 'Low', 'Moderate', 'High', 'Very High'];
    const magnitudeLabels  = ['Negligible', 'Minor', 'Moderate', 'Significant', 'Severe'];

    return (
      <div className="space-y-4">
        {/* Financial KPI cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <KpiCard label="Avg Financial Score"
            value={(classified.reduce((a, t) => a + t.financialScore, 0) / classified.length).toFixed(2)}
            sub="Risk + Opportunity weighted" icon={TrendingUp} />
          <KpiCard label="Highest Risk"
            value={Math.max(...classified.map(t => (t.riskLikelihood * 0.5 + t.riskMagnitude * 0.5))).toFixed(2)}
            sub={classified.reduce((best, t) => {
              const s = t.riskLikelihood * 0.5 + t.riskMagnitude * 0.5;
              const bs = best.riskLikelihood * 0.5 + best.riskMagnitude * 0.5;
              return s > bs ? t : best;
            }, classified[0]).label}
            icon={AlertTriangle} />
          <KpiCard label="Highest Opportunity"
            value={Math.max(...classified.map(t => t.opportunityMagnitude)).toFixed(2)}
            sub={classified.reduce((best, t) => t.opportunityMagnitude > best.opportunityMagnitude ? t : best, classified[0]).label}
            icon={TrendingUp} />
          <KpiCard label="Financially Material"
            value={classified.filter(t => t.financialScore >= financialThreshold).length}
            sub={`Threshold: ${financialThreshold.toFixed(1)}`} icon={CheckCircle} />
        </div>

        {/* Grouped bar chart: risk vs opportunity */}
        <Section title="Risk Score vs Opportunity Score" icon={BarChart3}>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={groupedData} margin={{ top: 10, right: 30, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
              <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#666' }} />
              <YAxis domain={[0, 5]} tick={{ fontSize: 10, fill: '#999' }} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="Risk Score" fill="#111111" fillOpacity={0.8} radius={[3, 3, 0, 0]} />
              <Bar dataKey="Opportunity Score" fill="#10b981" fillOpacity={0.6} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Section>

        {/* Risk heatmap: likelihood x magnitude */}
        <Section title="Risk Heatmap: Likelihood x Magnitude" icon={Grid3X3}>
          <div className="overflow-x-auto">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr>
                  <th className="py-2 px-2 text-left text-gray-500 font-medium" rowSpan={2}>Likelihood</th>
                  <th className="py-1 px-2 text-center text-gray-500 font-medium border-b border-gray-200" colSpan={5}>
                    Risk Magnitude
                  </th>
                </tr>
                <tr>
                  {magnitudeLabels.map((m, i) => (
                    <th key={i} className="py-1 px-2 text-center text-[10px] text-gray-500 font-normal">{m}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {heatmapGrid.reverse().map((row, ri) => (
                  <tr key={ri} className="border-b border-gray-100">
                    <td className="py-2 px-2 text-gray-600 font-medium">{likelihoodLabels[row.likelihood - 1]}</td>
                    {magnitudeBuckets.map(m => {
                      const count = row[`m${m}`];
                      const topics = row[`m${m}_topics`];
                      const intensity = count === 0 ? 'bg-white' :
                        count === 1 ? 'bg-amber-50' :
                        count >= 2 ? 'bg-red-50' : 'bg-white';
                      return (
                        <td key={m} className={`py-2 px-2 text-center ${intensity} rounded`}
                          title={topics || 'None'}>
                          {count > 0
                            ? <span className="text-xs font-semibold text-gray-700">{topics}</span>
                            : <span className="text-gray-400">--</span>}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        {/* Financial details table */}
        <Section title="Per-Topic Financial Breakdown" icon={Layers}>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">Topic</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Risk Likelihood</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Risk Magnitude</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Opportunity Mag.</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Financial Score</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Material?</th>
                </tr>
              </thead>
              <tbody>
                {classified.map(t => (
                  <tr key={t.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-2 px-2 font-medium text-gray-800">{t.label}</td>
                    <HeatCell value={t.riskLikelihood} />
                    <HeatCell value={t.riskMagnitude} />
                    <td className="py-2 px-2 text-center">
                      <span className="inline-flex items-center gap-1 text-emerald-600 font-medium">
                        <TrendingUp className="h-3 w-3" /> {t.opportunityMagnitude.toFixed(1)}
                      </span>
                    </td>
                    <td className="py-2 px-2 text-center font-mono font-semibold text-gray-900">{t.financialScore.toFixed(2)}</td>
                    <td className="py-2 px-2 text-center">
                      {t.financialScore >= financialThreshold
                        ? <Badge text="Yes" className="bg-emerald-50 text-emerald-600" />
                        : <Badge text="No" className="bg-gray-100 text-gray-500" />}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      </div>
    );
  };

  // ---- Tab 4: Stakeholder Engagement ---------------------------------------
  const renderStakeholderTab = () => {
    const qualityGauge = stakeholderAgg.avgQuality;
    const gaugeColor = qualityGauge >= 75 ? 'text-emerald-600' : qualityGauge >= 50 ? 'text-amber-600' : 'text-red-600';

    // Coverage bar data
    const coverageBarData = stakeholderData.map(s => ({
      name: s.group.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      Coverage: s.coverage,
      Quality: s.quality,
    }));

    // Method breakdown
    const methodData = ENGAGEMENT_METHODS.map(m => ({
      method: m.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      count: stakeholderData.filter(s => s.method === m).length,
    }));

    return (
      <div className="space-y-4">
        {/* Overall quality */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-white border border-gray-200 rounded-lg p-4 col-span-1">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-2">Overall Quality Score</p>
            <div className="flex items-end gap-1">
              <span className={`text-3xl font-bold ${gaugeColor}`}>{qualityGauge.toFixed(0)}</span>
              <span className="text-sm text-gray-500 mb-1">/100</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 mt-2">
              <div className={`h-2 rounded-full ${qualityGauge >= 75 ? 'bg-emerald-500' : qualityGauge >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
                style={{ width: `${qualityGauge}%` }} />
            </div>
          </div>
          <KpiCard label="Avg Coverage" value={`${stakeholderAgg.avgCoverage.toFixed(0)}%`}
            sub="Topics covered per group" icon={Target} />
          <KpiCard label="Avg Response Rate" value={`${stakeholderAgg.avgResponse.toFixed(0)}%`}
            sub="Across all engagements" icon={Users} />
          <KpiCard label="Stakeholder Groups" value={STAKEHOLDER_GROUPS.length}
            sub="Active groups engaged" icon={Globe} />
        </div>

        {/* Coverage & Quality bar chart */}
        <Section title="Coverage & Quality by Stakeholder Group" icon={BarChart3}>
          <ResponsiveContainer width="100%" height={380}>
            <BarChart data={coverageBarData} layout="vertical" margin={{ top: 5, right: 30, left: 110, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: '#999' }}
                label={{ value: '%', position: 'right', offset: 10, style: { fill: '#999', fontSize: 10 } }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#666' }} width={105} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => `${v.toFixed(1)}%`} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="Coverage" fill="#111111" fillOpacity={0.7} radius={[0, 3, 3, 0]} />
              <Bar dataKey="Quality" fill="#10b981" fillOpacity={0.5} radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Section>

        {/* Engagement method breakdown */}
        <Section title="Engagement Method Distribution" icon={Activity}>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {methodData.map(m => (
              <div key={m.method} className="bg-white border border-gray-200 rounded-lg p-3 text-center">
                <p className="text-lg font-semibold text-gray-900">{m.count}</p>
                <p className="text-[10px] text-gray-500 mt-0.5">{m.method}</p>
              </div>
            ))}
          </div>
        </Section>

        {/* Stakeholder detail table */}
        <Section title="Stakeholder Engagement Details" icon={Users}>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">Stakeholder Group</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Method</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Quality Score</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Coverage %</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Response Rate</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Representativeness</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Topics Covered</th>
                </tr>
              </thead>
              <tbody>
                {stakeholderData.map(s => {
                  const qColor = s.quality >= 75 ? 'text-emerald-600' : s.quality >= 50 ? 'text-amber-600' : 'text-red-600';
                  return (
                    <tr key={s.group} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-2 px-2 font-medium text-gray-800">
                        {s.group.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                      </td>
                      <td className="py-2 px-2 text-center">
                        <Badge text={s.method.replace(/_/g, ' ')} className="bg-gray-100 text-gray-600" />
                      </td>
                      <td className={`py-2 px-2 text-center font-semibold ${qColor}`}>{s.quality.toFixed(1)}</td>
                      <td className="py-2 px-2 text-center font-mono text-gray-700">{s.coverage.toFixed(1)}%</td>
                      <td className="py-2 px-2 text-center font-mono text-gray-700">{s.responseRate.toFixed(1)}%</td>
                      <td className="py-2 px-2 text-center font-mono text-gray-700">{s.representativeness.toFixed(1)}%</td>
                      <td className="py-2 px-2 text-center text-gray-700">{s.topicsCovered}/10</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Section>

        {/* Quality indicators summary */}
        <Section title="Quality Indicators Summary" icon={Gauge} defaultOpen={false}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-3">Response Rate Distribution</p>
              {stakeholderData.map(s => (
                <div key={s.group} className="flex items-center gap-2 mb-1.5">
                  <span className="text-[10px] text-gray-500 w-24 truncate">
                    {s.group.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                    <div className="h-1.5 rounded-full bg-gray-400" style={{ width: `${s.responseRate}%` }} />
                  </div>
                  <span className="text-[10px] text-gray-500 w-10 text-right">{s.responseRate.toFixed(0)}%</span>
                </div>
              ))}
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-3">Topic Coverage Distribution</p>
              {stakeholderData.map(s => (
                <div key={s.group} className="flex items-center gap-2 mb-1.5">
                  <span className="text-[10px] text-gray-500 w-24 truncate">
                    {s.group.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                    <div className="h-1.5 rounded-full bg-emerald-500/60" style={{ width: `${s.coverage}%` }} />
                  </div>
                  <span className="text-[10px] text-gray-500 w-10 text-right">{s.coverage.toFixed(0)}%</span>
                </div>
              ))}
            </div>
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-3">Representativeness Distribution</p>
              {stakeholderData.map(s => (
                <div key={s.group} className="flex items-center gap-2 mb-1.5">
                  <span className="text-[10px] text-gray-500 w-24 truncate">
                    {s.group.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                    <div className="h-1.5 rounded-full bg-blue-500/50" style={{ width: `${s.representativeness}%` }} />
                  </div>
                  <span className="text-[10px] text-gray-500 w-10 text-right">{s.representativeness.toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>
        </Section>
      </div>
    );
  };

  // ---- Tab 5: Cross-Framework Mapping --------------------------------------
  const renderCrossFrameworkTab = () => {
    const materialTopics = classified.filter(t => t.classification !== 'not_material');

    // Framework badge colors
    const fwBadge = {
      gri:  'bg-emerald-50 text-emerald-700 border-emerald-200',
      tcfd: 'bg-blue-50 text-blue-700 border-blue-200',
      issb: 'bg-purple-50 text-purple-700 border-purple-200',
      sdg:  'bg-orange-50 text-orange-700 border-orange-200',
    };

    // Grouped mapping data for bar chart
    const mappingBarData = [
      { framework: 'GRI Standards', coverage: frameworkCoverage.gri, fill: '#10b981' },
      { framework: 'TCFD Pillars', coverage: frameworkCoverage.tcfd, fill: '#3b82f6' },
      { framework: 'ISSB S1/S2', coverage: frameworkCoverage.issb, fill: '#8b5cf6' },
      { framework: 'UN SDGs', coverage: frameworkCoverage.sdg, fill: '#f59e0b' },
    ];

    // All SDGs referenced
    const allSdgs = new Set();
    materialTopics.forEach(t => {
      const cf = CROSS_FRAMEWORK[t.id];
      if (cf && cf.sdgs) cf.sdgs.forEach(s => allSdgs.add(s));
    });

    return (
      <div className="space-y-4">
        {/* Coverage summary cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-emerald-500" />
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">GRI Coverage</p>
            </div>
            <p className="text-xl font-semibold text-gray-900">{frameworkCoverage.gri}%</p>
            <p className="text-xs text-gray-500">Material topics mapped</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">TCFD Coverage</p>
            </div>
            <p className="text-xl font-semibold text-gray-900">{frameworkCoverage.tcfd}%</p>
            <p className="text-xs text-gray-500">Pillar alignment</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-purple-500" />
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">ISSB Coverage</p>
            </div>
            <p className="text-xl font-semibold text-gray-900">{frameworkCoverage.issb}%</p>
            <p className="text-xs text-gray-500">S1/S2 paragraph mapping</p>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-orange-500" />
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">UN SDGs Linked</p>
            </div>
            <p className="text-xl font-semibold text-gray-900">{allSdgs.size}</p>
            <p className="text-xs text-gray-500">Unique SDGs referenced</p>
          </div>
        </div>

        {/* Coverage bar chart */}
        <Section title="Cross-Framework Coverage %" icon={BarChart3}>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={mappingBarData} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
              <XAxis dataKey="framework" tick={{ fontSize: 10, fill: '#666' }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#999' }}
                label={{ value: '%', angle: -90, position: 'insideLeft', style: { fill: '#999', fontSize: 10 } }} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={v => `${v}%`} />
              <Bar dataKey="coverage" radius={[4, 4, 0, 0]}>
                {mappingBarData.map((d, i) => <Cell key={i} fill={d.fill} fillOpacity={0.75} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        {/* Flow diagram: ESRS -> Frameworks */}
        <Section title="Material Topics to Framework Mapping" icon={Link2}>
          <div className="space-y-2">
            {materialTopics.map(t => {
              const cf = CROSS_FRAMEWORK[t.id];
              if (!cf) return null;
              const cls = CLASS_CONFIG[t.classification];
              return (
                <div key={t.id} className="flex flex-wrap items-center gap-2 py-2 px-3 border border-gray-100 rounded-lg hover:bg-gray-50">
                  <div className="flex items-center gap-2 min-w-[200px]">
                    <Badge text={t.category} className={CATEGORY_BG[t.category]} />
                    <span className="text-xs font-medium text-gray-800">{t.label}</span>
                  </div>
                  <ArrowRight className="h-3 w-3 text-gray-400 hidden sm:block" />
                  <div className="flex flex-wrap items-center gap-1.5">
                    {cf.gri !== '--' && (
                      <span className={`inline-flex items-center text-[10px] font-medium px-2 py-0.5 rounded border ${fwBadge.gri}`}>
                        GRI: {cf.gri}
                      </span>
                    )}
                    {cf.tcfd !== '--' && (
                      <span className={`inline-flex items-center text-[10px] font-medium px-2 py-0.5 rounded border ${fwBadge.tcfd}`}>
                        TCFD: {cf.tcfd}
                      </span>
                    )}
                    {cf.issb !== '--' && (
                      <span className={`inline-flex items-center text-[10px] font-medium px-2 py-0.5 rounded border ${fwBadge.issb}`}>
                        ISSB: {cf.issb}
                      </span>
                    )}
                    {cf.sdgs && cf.sdgs.length > 0 && cf.sdgs.map(sdg => (
                      <span key={sdg} className={`inline-flex items-center text-[10px] font-medium px-2 py-0.5 rounded border ${fwBadge.sdg}`}>
                        SDG {sdg}
                      </span>
                    ))}
                  </div>
                  <div className="ml-auto">
                    <Badge text={cls.label} className={cls.badge} />
                  </div>
                </div>
              );
            })}
          </div>
        </Section>

        {/* Comprehensive mapping table */}
        <Section title="Full Cross-Framework Reference Table" icon={Layers}>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">ESRS Topic</th>
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">GRI Standard</th>
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">TCFD Pillar</th>
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">ISSB Reference</th>
                  <th className="text-left py-2 px-2 text-gray-500 font-medium">UN SDGs</th>
                  <th className="text-center py-2 px-2 text-gray-500 font-medium">Material?</th>
                </tr>
              </thead>
              <tbody>
                {classified.map(t => {
                  const cf = CROSS_FRAMEWORK[t.id];
                  const cls = CLASS_CONFIG[t.classification];
                  const isMat = t.classification !== 'not_material';
                  return (
                    <tr key={t.id} className={`border-b border-gray-100 ${isMat ? '' : 'opacity-40'}`}>
                      <td className="py-2 px-2 font-medium text-gray-800">
                        <div className="flex items-center gap-1.5">
                          <Badge text={t.category} className={CATEGORY_BG[t.category]} />
                          {t.label}
                        </div>
                      </td>
                      <td className="py-2 px-2 text-gray-700">{cf?.gri || '--'}</td>
                      <td className="py-2 px-2 text-gray-700">{cf?.tcfd || '--'}</td>
                      <td className="py-2 px-2 text-gray-700">{cf?.issb || '--'}</td>
                      <td className="py-2 px-2">
                        {cf?.sdgs?.map(sdg => (
                          <span key={sdg} className="inline-flex items-center text-[10px] font-medium px-1.5 py-0.5 rounded bg-orange-50 text-orange-600 mr-1">
                            {sdg}
                          </span>
                        ))}
                      </td>
                      <td className="py-2 px-2 text-center">
                        <Badge text={cls.label} className={cls.badge} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Section>

        {/* SDG alignment summary */}
        <Section title="UN SDG Alignment" icon={Globe} defaultOpen={false}>
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">
            {Array.from({ length: 17 }, (_, i) => i + 1).map(sdg => {
              const linked = allSdgs.has(sdg);
              return (
                <div key={sdg}
                  className={`border rounded-lg p-3 text-center transition-colors ${
                    linked
                      ? 'border-orange-200 bg-orange-50'
                      : 'border-gray-200 bg-white opacity-40'
                  }`}>
                  <p className={`text-lg font-bold ${linked ? 'text-orange-700' : 'text-gray-500'}`}>
                    {sdg}
                  </p>
                  <p className="text-[9px] text-gray-500 mt-0.5">SDG {sdg}</p>
                </div>
              );
            })}
          </div>
        </Section>
      </div>
    );
  };

  // =========================================================================
  // TAB SELECTOR MAP
  // =========================================================================
  const TABS = [
    { id: 'matrix',      label: 'Materiality Matrix', icon: Target },
    { id: 'impact',      label: 'Impact Materiality', icon: Activity },
    { id: 'financial',   label: 'Financial Materiality', icon: TrendingUp },
    { id: 'stakeholder', label: 'Stakeholder Engagement', icon: Users },
    { id: 'crossfw',     label: 'Cross-Framework', icon: Link2 },
  ];

  const renderTab = () => {
    switch (activeTab) {
      case 'matrix':      return renderMatrixTab();
      case 'impact':       return renderImpactTab();
      case 'financial':    return renderFinancialTab();
      case 'stakeholder':  return renderStakeholderTab();
      case 'crossfw':      return renderCrossFrameworkTab();
      default:             return renderMatrixTab();
    }
  };

  // =========================================================================
  // RENDER
  // =========================================================================
  return (
    <div className="min-h-screen bg-[#f5f6f8]">
      <DemoBanner message="Materiality scores, IRO rankings, and stakeholder impact assessments display deterministic sample data. Import your materiality survey results to see entity-specific values." />
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <h1 className="text-lg font-semibold text-gray-900 tracking-tight">
                Double Materiality Assessment
              </h1>
              <p className="text-xs text-gray-500 mt-0.5">
                CSRD / ESRS Double Materiality -- Impact & Financial materiality across 10 ESRS topics
              </p>
            </div>
            <div className="flex items-center gap-3">
              <SectorSelect value={sector} onChange={setSector} />
              <div className="flex items-center gap-1.5 text-[10px] text-gray-500">
                <Info className="h-3 w-3" />
                <span>Deterministic demo data</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab navigation */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center gap-1 py-1.5 overflow-x-auto">
            {TABS.map(tab => (
              <TabButton
                key={tab.id}
                label={tab.label}
                icon={tab.icon}
                active={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Tab content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Classification legend (always visible) */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          {Object.entries(CLASS_CONFIG).map(([key, cfg]) => (
            <div key={key} className="flex items-center gap-1.5">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: cfg.dot }} />
              <span className="text-[11px] text-gray-500">{cfg.label}</span>
            </div>
          ))}
          <span className="text-[10px] text-gray-500 ml-auto">
            Sector: {SECTORS.find(s => s.id === sector)?.label} | Thresholds: Impact {impactThreshold.toFixed(1)} / Financial {financialThreshold.toFixed(1)}
          </span>
        </div>

        {renderTab()}

        {/* Footer */}
        <div className="mt-8 pt-4 border-t border-gray-200 text-center">
          <p className="text-[10px] text-gray-500">
            Double Materiality Assessment per EFRAG ESRS Implementation Guidance (IG-3) --
            10 ESRS topics, 6 sector benchmarks, 12 stakeholder groups, 4 cross-framework mappings
          </p>
        </div>
      </div>
    </div>
  );
}

// Re-export reference for Settings2 / Grid3X3 used above (lucide-react icons)
// These are imported at the top but referenced inside nested functions via closure.
// The import block at the top of the file includes all required icons.
