import React, { useState, useMemo, useCallback } from 'react';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend,
  AreaChart, Area,
} from 'recharts';
import {
  MessageCircle, TrendingUp, TrendingDown, AlertTriangle, Activity,
  Users, Shield, Eye, Globe, Zap, ChevronDown, ChevronUp,
  Radio, BarChart2, Target, Layers,
} from 'lucide-react';
import DemoBanner from '../../../components/shared/DemoBanner';

/* ────────────────────────────────────────────────────────── */
/*  Deterministic seed-based data generation                  */
/* ────────────────────────────────────────────────────────── */
function seededRandom(seed) {
  let s = seed;
  return () => { s = (s * 16807 + 0) % 2147483647; return (s - 1) / 2147483646; };
}

const STAKEHOLDER_GROUPS = [
  { key: 'investor',   label: 'Investors',   icon: TrendingUp, color: '#10b981' },
  { key: 'employee',   label: 'Employees',   icon: Users,      color: '#3b82f6' },
  { key: 'customer',   label: 'Customers',   icon: Target,     color: '#8b5cf6' },
  { key: 'regulator',  label: 'Regulators',  icon: Shield,     color: '#f59e0b' },
  { key: 'community',  label: 'Community',   icon: Globe,      color: '#06b6d4' },
  { key: 'ngo',        label: 'NGOs',        icon: Eye,        color: '#ef4444' },
  { key: 'media',      label: 'Media',       icon: Radio,      color: '#ec4899' },
  { key: 'supplier',   label: 'Suppliers',   icon: Layers,     color: '#f97316' },
];

const ENTITIES = [
  'Deutsche Bank AG', 'Shell PLC', 'TotalEnergies SE', 'Glencore PLC',
  'ArcelorMittal SA', 'HeidelbergCement AG', 'RWE AG', 'BP PLC',
  'Volkswagen AG', 'BASF SE', 'Siemens Energy AG', 'Unilever PLC',
];

const ESG_PILLARS = ['Environmental', 'Social', 'Governance'];

const SIGNAL_SOURCES = [
  { name: 'Bloomberg News', type: 'news', tier: 2 },
  { name: 'Reuters', type: 'news', tier: 2 },
  { name: 'Financial Times', type: 'news', tier: 2 },
  { name: 'GDELT', type: 'news', tier: 2 },
  { name: 'SEC EDGAR', type: 'regulatory', tier: 1 },
  { name: 'RepRisk', type: 'ngo', tier: 2 },
  { name: 'Glassdoor', type: 'social_media', tier: 3 },
  { name: 'Twitter/X', type: 'social_media', tier: 4 },
  { name: 'LinkedIn', type: 'social_media', tier: 3 },
  { name: 'CDP Disclosures', type: 'ngo', tier: 2 },
];

const MODULE_CONNECTIONS = {
  inbound: [
    { module: 'NLP Pulse Engine', type: 'score_input' },
    { module: 'Greenwashing Engine', type: 'controversy_flag' },
    { module: 'GDELT Controversy', type: 'score_input' },
    { module: 'Company Profiles', type: 'entity_metadata' },
    { module: 'Engagement Tracker', type: 'score_input' },
    { module: 'Factor Overlay Engine', type: 'adjustment_factor' },
    { module: 'CSRD Entity Registry', type: 'entity_metadata' },
    { module: 'Regulatory Compiler', type: 'score_input' },
  ],
  outbound: [
    { module: 'ECL Calculator', type: 'PD adjustment' },
    { module: 'Portfolio Analytics', type: 'heatmap' },
    { module: 'DMI Engine', type: 'materiality signal' },
    { module: 'Alert Engine', type: 'alert trigger' },
    { module: 'Greenwashing Engine', type: 'divergence check' },
    { module: 'Sovereign Risk', type: 'country context' },
    { module: 'Double Materiality', type: 'stakeholder salience' },
    { module: 'RE Valuation', type: 'brand adjustment' },
    { module: 'PE Deal Pipeline', type: 'reputation score' },
    { module: 'Contagion Engine', type: 'cascade propagation' },
  ],
};

function generateEntityData(entity, seed) {
  const r = seededRandom(seed);
  const stakeholder = {};
  STAKEHOLDER_GROUPS.forEach(sg => {
    stakeholder[sg.key] = +(r() * 2 - 1).toFixed(3);
  });
  const composite = STAKEHOLDER_GROUPS.reduce((sum, sg) => {
    const w = { investor: 0.20, regulator: 0.18, employee: 0.15, customer: 0.14, media: 0.12, ngo: 0.08, community: 0.07, supplier: 0.06 };
    return sum + stakeholder[sg.key] * (w[sg.key] || 0.1);
  }, 0);

  const esg = { Environmental: +(r() * 2 - 1).toFixed(3), Social: +(r() * 2 - 1).toFixed(3), Governance: +(r() * 2 - 1).toFixed(3) };
  const velocity = +(r() * 0.6 - 0.3).toFixed(4);
  const acceleration = +(r() * 0.4 - 0.2).toFixed(4);
  const zScore = +(velocity / 0.15).toFixed(3);
  const regime = zScore < -2 ? 'crisis' : zScore < -0.5 ? 'deteriorating' : zScore < 0.5 ? 'stable' : 'improving';
  const signalCount = Math.floor(r() * 200) + 20;
  const diversity = +(1 - 1 / (Math.floor(r() * 12) + 3)).toFixed(3);

  let alertTier = null;
  if (composite <= -0.9) alertTier = 'EXTREME';
  else if (composite <= -0.7) alertTier = 'CRITICAL';
  else if (composite <= -0.5) alertTier = 'ELEVATED';
  else if (composite <= -0.3) alertTier = 'WATCH';

  // Time series (90 days)
  const timeseries = [];
  let val = composite;
  for (let i = 89; i >= 0; i--) {
    val += (r() * 0.1 - 0.05);
    val = Math.max(-1, Math.min(1, val));
    timeseries.push({ day: -i, value: +val.toFixed(3), signals: Math.floor(r() * 15) + 1 });
  }

  return { entity, composite: +composite.toFixed(4), stakeholder, esg, velocity, acceleration, zScore, regime, signalCount, diversity, alertTier, timeseries };
}

/* ────────────────────────────────────────────────────────── */
/*  Reusable primitives                                       */
/* ────────────────────────────────────────────────────────── */
const Section = ({ title, icon: Icon, children, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e5e7eb', marginBottom: 16 }}>
      <div onClick={() => setOpen(!open)} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 20px', cursor: 'pointer', borderBottom: open ? '1px solid #e5e7eb' : 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600, fontSize: 15 }}>
          {Icon && <Icon size={18} style={{ color: '#10b981' }} />}
          {title}
        </div>
        {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </div>
      {open && <div style={{ padding: 20 }}>{children}</div>}
    </div>
  );
};

const KpiCard = ({ label, value, sub, color = '#111' }) => (
  <div style={{ flex: '1 1 200px', background: '#f9fafb', borderRadius: 10, padding: '16px 20px', border: '1px solid #e5e7eb' }}>
    <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 4 }}>{label}</div>
    <div style={{ fontSize: 24, fontWeight: 700, color }}>{value}</div>
    {sub && <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>{sub}</div>}
  </div>
);

const Badge = ({ text, color = '#10b981' }) => (
  <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 6, fontSize: 10, fontWeight: 700, letterSpacing: 0.5, background: color + '18', color, textTransform: 'uppercase' }}>{text}</span>
);

const REGIME_COLORS = { crisis: '#ef4444', deteriorating: '#f59e0b', stable: '#10b981', improving: '#3b82f6' };
const ALERT_COLORS = { EXTREME: '#7c2d12', CRITICAL: '#ef4444', ELEVATED: '#f59e0b', WATCH: '#3b82f6' };

/* ────────────────────────────────────────────────────────── */
/*  Tabs                                                      */
/* ────────────────────────────────────────────────────────── */
const TABS = [
  { key: 'overview',      label: 'Entity Overview' },
  { key: 'stakeholders',  label: 'Stakeholder Analysis' },
  { key: 'portfolio',     label: 'Portfolio Sentiment' },
  { key: 'signals',       label: 'Signal Feed' },
  { key: 'connections',   label: 'Module Connections' },
];

/* ────────────────────────────────────────────────────────── */
/*  Main Page Component                                       */
/* ────────────────────────────────────────────────────────── */
export default function SentimentAnalysisPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedEntity, setSelectedEntity] = useState(ENTITIES[0]);
  const [lookbackDays, setLookbackDays] = useState(90);

  // Generate entity data
  const allEntityData = useMemo(() => {
    return ENTITIES.map((e, i) => generateEntityData(e, 42000 + i * 7919));
  }, []);

  const entityData = useMemo(() => {
    return allEntityData.find(d => d.entity === selectedEntity) || allEntityData[0];
  }, [selectedEntity, allEntityData]);

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '0 20px 24px', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
      <DemoBanner message="Sentiment scores, signal velocities, and controversy data display deterministic sample data. Connect a live news or social feed to see real-time values." />
      <div style={{ height: 24 }} />
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, margin: 0 }}>Sentiment Analysis</h1>
          <p style={{ color: '#6b7280', fontSize: 14, margin: '4px 0 0' }}>
            Multi-stakeholder sentiment monitoring — news, social media, regulatory filings, NGO reports, validated public sources
          </p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <Badge text="Multi-Source" color="#10b981" />
          <Badge text="8 Stakeholders" color="#3b82f6" />
          <Badge text="NLP" color="#8b5cf6" />
          <Badge text="EWMA" color="#f59e0b" />
          <Badge text="Cross-Module" color="#ef4444" />
        </div>
      </div>

      {/* Tab bar */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '2px solid #e5e7eb', paddingBottom: 0 }}>
        {TABS.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            style={{ padding: '10px 18px', border: 'none', borderBottom: activeTab === t.key ? '2px solid #10b981' : '2px solid transparent', background: 'none', fontWeight: activeTab === t.key ? 700 : 400, color: activeTab === t.key ? '#10b981' : '#6b7280', cursor: 'pointer', fontSize: 13, marginBottom: -2 }}>
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Entity Overview ── */}
      {activeTab === 'overview' && (
        <>
          {/* Entity Selector */}
          <Section title="Entity Selector" icon={Target}>
            <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
              <div>
                <label style={{ fontSize: 12, color: '#6b7280' }}>Entity</label>
                <select value={selectedEntity} onChange={e => setSelectedEntity(e.target.value)}
                  style={{ display: 'block', padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 13, minWidth: 220 }}>
                  {ENTITIES.map(e => <option key={e} value={e}>{e}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 12, color: '#6b7280' }}>Lookback (days)</label>
                <input type="number" value={lookbackDays} onChange={e => setLookbackDays(+e.target.value)}
                  style={{ display: 'block', padding: '8px 12px', borderRadius: 8, border: '1px solid #d1d5db', fontSize: 13, width: 80 }} />
              </div>
            </div>
          </Section>

          {/* KPI Cards */}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
            <KpiCard label="COMPOSITE SCORE" value={entityData.composite.toFixed(3)}
              color={entityData.composite > 0.2 ? '#10b981' : entityData.composite < -0.2 ? '#ef4444' : '#6b7280'}
              sub="Weighted stakeholder average" />
            <KpiCard label="SENTIMENT VELOCITY" value={entityData.velocity.toFixed(4)}
              color={entityData.velocity > 0 ? '#10b981' : '#ef4444'}
              sub={`Z-score: ${entityData.zScore}`} />
            <KpiCard label="REGIME" value={entityData.regime.toUpperCase()}
              color={REGIME_COLORS[entityData.regime] || '#6b7280'}
              sub="EWMA-smoothed direction" />
            <KpiCard label="SIGNAL COUNT" value={entityData.signalCount}
              sub={`Diversity: ${entityData.diversity}`} />
            <KpiCard label="ALERT"
              value={entityData.alertTier || 'NONE'}
              color={ALERT_COLORS[entityData.alertTier] || '#10b981'}
              sub={entityData.alertTier ? 'Sentiment threshold breached' : 'All clear'} />
          </div>

          {/* Sentiment Timeseries */}
          <Section title="Sentiment Timeseries" icon={Activity}>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={entityData.timeseries}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} label={{ value: 'Days ago', position: 'insideBottom', offset: -5, fontSize: 11 }} />
                <YAxis domain={[-1, 1]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Area type="monotone" dataKey="value" stroke="#10b981" fill="#10b98130" strokeWidth={2} name="Sentiment" />
                <Line type="monotone" dataKey={() => -0.3} stroke="#f59e0b" strokeDasharray="5 5" name="WATCH" />
                <Line type="monotone" dataKey={() => -0.7} stroke="#ef4444" strokeDasharray="5 5" name="CRITICAL" />
              </AreaChart>
            </ResponsiveContainer>
          </Section>

          {/* ESG Breakdown */}
          <Section title="ESG Pillar Breakdown" icon={BarChart2}>
            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
              <div style={{ flex: '1 1 400px' }}>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={ESG_PILLARS.map(p => ({ pillar: p, score: entityData.esg[p] }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="pillar" tick={{ fontSize: 12 }} />
                    <YAxis domain={[-1, 1]} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="score" name="Sentiment">
                      {ESG_PILLARS.map((p, i) => (
                        <Cell key={i} fill={entityData.esg[p] > 0 ? '#10b981' : '#ef4444'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div style={{ flex: '1 1 300px' }}>
                <ResponsiveContainer width="100%" height={250}>
                  <RadarChart data={STAKEHOLDER_GROUPS.map(sg => ({
                    stakeholder: sg.label,
                    score: (entityData.stakeholder[sg.key] + 1) / 2, // normalize to 0-1
                  }))}>
                    <PolarGrid stroke="#e5e7eb" />
                    <PolarAngleAxis dataKey="stakeholder" tick={{ fontSize: 10 }} />
                    <PolarRadiusAxis domain={[0, 1]} tick={{ fontSize: 9 }} />
                    <Radar dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.3} name="Normalized Score" />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </Section>
        </>
      )}

      {/* ── Tab: Stakeholder Analysis ── */}
      {activeTab === 'stakeholders' && (
        <>
          <Section title="Stakeholder Sentiment Breakdown" icon={Users}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
              {STAKEHOLDER_GROUPS.map(sg => {
                const score = entityData.stakeholder[sg.key];
                const Icon = sg.icon;
                return (
                  <div key={sg.key} style={{ padding: 16, borderRadius: 10, border: '1px solid #e5e7eb', background: '#f9fafb' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <Icon size={16} style={{ color: sg.color }} />
                      <span style={{ fontWeight: 600, fontSize: 14 }}>{sg.label}</span>
                    </div>
                    <div style={{ fontSize: 28, fontWeight: 700, color: score > 0.2 ? '#10b981' : score < -0.2 ? '#ef4444' : '#6b7280' }}>
                      {score > 0 ? '+' : ''}{score.toFixed(3)}
                    </div>
                    <div style={{ marginTop: 8, height: 6, borderRadius: 3, background: '#e5e7eb', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%', borderRadius: 3,
                        width: `${((score + 1) / 2) * 100}%`,
                        background: score > 0.2 ? '#10b981' : score < -0.2 ? '#ef4444' : '#9ca3af',
                      }} />
                    </div>
                    <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>
                      Weight: {({ investor: '20%', regulator: '18%', employee: '15%', customer: '14%', media: '12%', ngo: '8%', community: '7%', supplier: '6%' })[sg.key]}
                    </div>
                  </div>
                );
              })}
            </div>
          </Section>

          <Section title="Stakeholder Contribution to Composite" icon={BarChart2}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={STAKEHOLDER_GROUPS.map(sg => ({
                group: sg.label,
                score: entityData.stakeholder[sg.key],
                contribution: +(entityData.stakeholder[sg.key] * ({ investor: 0.20, regulator: 0.18, employee: 0.15, customer: 0.14, media: 0.12, ngo: 0.08, community: 0.07, supplier: 0.06 })[sg.key]).toFixed(4),
              }))} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" domain={[-0.3, 0.3]} tick={{ fontSize: 11 }} />
                <YAxis dataKey="group" type="category" width={100} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="contribution" name="Weighted Contribution">
                  {STAKEHOLDER_GROUPS.map((sg, i) => (
                    <Cell key={i} fill={entityData.stakeholder[sg.key] > 0 ? '#10b981' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Section>
        </>
      )}

      {/* ── Tab: Portfolio Sentiment ── */}
      {activeTab === 'portfolio' && (
        <>
          <Section title="Portfolio Sentiment Heatmap" icon={Layers}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    <th style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Entity</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', borderBottom: '1px solid #e5e7eb' }}>Composite</th>
                    {STAKEHOLDER_GROUPS.slice(0, 4).map(sg => (
                      <th key={sg.key} style={{ padding: '10px 8px', textAlign: 'center', borderBottom: '1px solid #e5e7eb', fontSize: 11 }}>{sg.label}</th>
                    ))}
                    <th style={{ padding: '10px 12px', textAlign: 'center', borderBottom: '1px solid #e5e7eb' }}>Regime</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', borderBottom: '1px solid #e5e7eb' }}>Alert</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', borderBottom: '1px solid #e5e7eb' }}>Signals</th>
                  </tr>
                </thead>
                <tbody>
                  {allEntityData.map(d => (
                    <tr key={d.entity} style={{ borderBottom: '1px solid #f0f0f0', cursor: 'pointer', background: d.entity === selectedEntity ? '#f0fdf4' : 'transparent' }}
                        onClick={() => { setSelectedEntity(d.entity); setActiveTab('overview'); }}>
                      <td style={{ padding: '10px 12px', fontWeight: 500 }}>{d.entity}</td>
                      <td style={{ padding: '10px 12px', textAlign: 'center', fontWeight: 700, color: d.composite > 0.2 ? '#10b981' : d.composite < -0.2 ? '#ef4444' : '#6b7280' }}>
                        {d.composite > 0 ? '+' : ''}{d.composite.toFixed(3)}
                      </td>
                      {STAKEHOLDER_GROUPS.slice(0, 4).map(sg => {
                        const v = d.stakeholder[sg.key];
                        const bg = v > 0.3 ? '#dcfce7' : v < -0.3 ? '#fee2e2' : v > 0 ? '#f0fdf4' : v < 0 ? '#fef2f2' : '#f9fafb';
                        return (
                          <td key={sg.key} style={{ padding: '8px', textAlign: 'center', background: bg, fontSize: 12 }}>
                            {v > 0 ? '+' : ''}{v.toFixed(2)}
                          </td>
                        );
                      })}
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        <Badge text={d.regime} color={REGIME_COLORS[d.regime] || '#6b7280'} />
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        {d.alertTier ? <Badge text={d.alertTier} color={ALERT_COLORS[d.alertTier]} /> : <span style={{ color: '#9ca3af', fontSize: 12 }}>None</span>}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'center', fontSize: 12 }}>{d.signalCount}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title="Portfolio Composite Distribution" icon={BarChart2}>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={allEntityData.map(d => ({ name: d.entity.split(' ')[0], composite: d.composite }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 11, angle: -30 }} height={50} />
                <YAxis domain={[-1, 1]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="composite" name="Composite Sentiment">
                  {allEntityData.map((d, i) => (
                    <Cell key={i} fill={d.composite > 0.2 ? '#10b981' : d.composite < -0.2 ? '#ef4444' : '#9ca3af'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Section>
        </>
      )}

      {/* ── Tab: Signal Feed ── */}
      {activeTab === 'signals' && (
        <>
          <Section title="Signal Source Configuration" icon={Radio}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    <th style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Source</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', borderBottom: '1px solid #e5e7eb' }}>Type</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', borderBottom: '1px solid #e5e7eb' }}>Credibility Tier</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', borderBottom: '1px solid #e5e7eb' }}>Weight</th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', borderBottom: '1px solid #e5e7eb' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {SIGNAL_SOURCES.map(src => (
                    <tr key={src.name} style={{ borderBottom: '1px solid #f0f0f0' }}>
                      <td style={{ padding: '10px 12px', fontWeight: 500 }}>{src.name}</td>
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        <Badge text={src.type} color={src.type === 'regulatory' ? '#3b82f6' : src.type === 'news' ? '#10b981' : src.type === 'ngo' ? '#ef4444' : '#8b5cf6'} />
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        <span style={{ fontWeight: 700 }}>T{src.tier}</span>
                        <span style={{ color: '#9ca3af', fontSize: 11, marginLeft: 4 }}>
                          ({['', 'Authoritative', 'High Quality', 'Standard', 'Mixed', 'Low'][src.tier]})
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'center', fontWeight: 600 }}>
                        {[0, 1.00, 0.85, 0.65, 0.45, 0.25][src.tier]}
                      </td>
                      <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                        <Badge text="Active" color="#10b981" />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title="Signal Processing Pipeline" icon={Zap}>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', padding: '20px 0' }}>
              {['INGEST', 'CLASSIFY', 'SCORE', 'WEIGHT', 'DECAY', 'AGGREGATE', 'VELOCITY', 'ALERT'].map((step, i) => (
                <React.Fragment key={step}>
                  <div style={{ padding: '12px 20px', background: '#f0fdf4', border: '1px solid #10b981', borderRadius: 10, fontWeight: 600, fontSize: 12, color: '#065f46', textAlign: 'center', minWidth: 80 }}>
                    <div style={{ fontSize: 9, color: '#10b981', marginBottom: 2 }}>STEP {i + 1}</div>
                    {step}
                  </div>
                  {i < 7 && <div style={{ alignSelf: 'center', color: '#d1d5db', fontSize: 18 }}>&rarr;</div>}
                </React.Fragment>
              ))}
            </div>
            <div style={{ fontSize: 12, color: '#6b7280', textAlign: 'center', marginTop: 8 }}>
              Raw signal &rarr; Stakeholder + ESG classification &rarr; Sentiment (-1 to +1) &rarr; Credibility weighting &rarr; Time decay &rarr; Entity composite &rarr; EWMA velocity &rarr; 4-tier alerts
            </div>
          </Section>

          <Section title="Decay Categories" icon={Activity} defaultOpen={false}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 10 }}>
              {Object.entries({ instant: 1, fast: 7, medium: 30, slow: 90, chronic: 365, permanent: 3650 }).map(([cat, days]) => (
                <div key={cat} style={{ padding: 12, borderRadius: 8, border: '1px solid #e5e7eb', textAlign: 'center' }}>
                  <div style={{ fontWeight: 600, fontSize: 13, textTransform: 'capitalize' }}>{cat}</div>
                  <div style={{ fontSize: 20, fontWeight: 700, color: '#10b981', marginTop: 4 }}>{days}d</div>
                  <div style={{ fontSize: 10, color: '#9ca3af' }}>half-life</div>
                </div>
              ))}
            </div>
          </Section>
        </>
      )}

      {/* ── Tab: Module Connections ── */}
      {activeTab === 'connections' && (
        <>
          <Section title="Inbound Feeds (Consume From)" icon={TrendingDown}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 10 }}>
              {MODULE_CONNECTIONS.inbound.map(c => (
                <div key={c.module} style={{ padding: 14, borderRadius: 10, border: '1px solid #dbeafe', background: '#eff6ff' }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: '#1e40af' }}>{c.module}</div>
                  <div style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>Feed type: {c.type}</div>
                  <div style={{ marginTop: 6 }}><Badge text="INBOUND" color="#3b82f6" /></div>
                </div>
              ))}
            </div>
          </Section>

          <Section title="Outbound Feeds (Produce For)" icon={TrendingUp}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 10 }}>
              {MODULE_CONNECTIONS.outbound.map(c => (
                <div key={c.module} style={{ padding: 14, borderRadius: 10, border: '1px solid #dcfce7', background: '#f0fdf4' }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: '#065f46' }}>{c.module}</div>
                  <div style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>Feed type: {c.type}</div>
                  <div style={{ marginTop: 6 }}><Badge text="OUTBOUND" color="#10b981" /></div>
                </div>
              ))}
            </div>
          </Section>

          <Section title="Integration Architecture" icon={Layers}>
            <div style={{ textAlign: 'center', padding: 20 }}>
              <div style={{ display: 'inline-block', textAlign: 'left', padding: 24, borderRadius: 12, border: '2px solid #10b981', background: '#f0fdf4' }}>
                <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 12, textAlign: 'center', color: '#065f46' }}>Sentiment Analysis Engine</div>
                <div style={{ display: 'flex', gap: 40, justifyContent: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 12, color: '#3b82f6', marginBottom: 6 }}>8 INBOUND</div>
                    {MODULE_CONNECTIONS.inbound.map(c => (
                      <div key={c.module} style={{ fontSize: 11, color: '#6b7280', padding: '2px 0' }}>&larr; {c.module}</div>
                    ))}
                  </div>
                  <div style={{ borderLeft: '1px solid #d1d5db', paddingLeft: 40 }}>
                    <div style={{ fontWeight: 600, fontSize: 12, color: '#10b981', marginBottom: 6 }}>10 OUTBOUND</div>
                    {MODULE_CONNECTIONS.outbound.map(c => (
                      <div key={c.module} style={{ fontSize: 11, color: '#6b7280', padding: '2px 0' }}>&rarr; {c.module}</div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </Section>
        </>
      )}
    </div>
  );
}
