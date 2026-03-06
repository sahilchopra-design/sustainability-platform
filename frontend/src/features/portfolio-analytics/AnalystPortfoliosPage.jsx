/**
 * AnalystPortfoliosPage.jsx
 * Route: /analyst-portfolios
 *
 * Four pre-built analyst portfolios based on entities from:
 *   - 8 processed CSRD annual reports (ING, Rabobank, BNP Paribas, ABN AMRO, Ørsted, RWE, ENGIE, EDP)
 *   - 12-institution peer benchmark group
 *
 * Each portfolio is designed around a distinct regulatory use case.
 * The gap assessment shows per-entity CSRD/TCFD/ISSB/PCAF coverage vs. required data points.
 *
 * Tabs per portfolio:
 *   1. Overview     — portfolio summary, entity cards, key metrics
 *   2. Gap Heatmap  — entity × framework coverage matrix (RAG)
 *   3. Framework    — portfolio-level bar chart by framework group
 *   4. Entities     — per-entity detailed breakdown with top-3 gaps
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
} from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// ─── Design tokens ────────────────────────────────────────────────────────────
const C = {
  green:   '#10b981',
  amber:   '#f59e0b',
  red:     '#ef4444',
  cyan:    'hsl(199,89%,56%)',
  blue:    '#3b82f6',
  purple:  '#8b5cf6',
  bg:      'hsl(222,35%,7%)',
  surface: 'hsl(222,30%,11%)',
  surface2:'hsl(222,28%,14%)',
  border:  'hsl(222,25%,18%)',
  muted:   'hsl(222,15%,45%)',
  text:    'hsl(210,40%,96%)',
};

const rag = (pct) => {
  if (pct == null) return { bg: 'rgba(255,255,255,0.03)', border: C.border, text: C.muted };
  if (pct >= 75)   return { bg: 'rgba(16,185,129,0.15)',  border: C.green,  text: C.green  };
  if (pct >= 50)   return { bg: 'rgba(245,158,11,0.15)',  border: C.amber,  text: C.amber  };
  return             { bg: 'rgba(239,68,68,0.15)',   border: C.red,    text: C.red    };
};

const groupColor = { TCFD: C.cyan, ISSB: C.blue, ESRS: C.purple, PCAF: C.green, Emissions: C.amber, Strategy: '#ec4899', Nature: '#14b8a6' };

// ─── Small helpers ─────────────────────────────────────────────────────────────
const Spinner = () => (
  <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
    <div style={{ width: 28, height: 28, border: `3px solid ${C.border}`, borderTopColor: C.cyan, borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
    <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
  </div>
);

const Badge = ({ children, color = C.cyan, small }) => (
  <span style={{
    display: 'inline-block', borderRadius: 5, padding: small ? '1px 5px' : '2px 7px',
    fontSize: small ? 9 : 10, fontWeight: 700, letterSpacing: '0.04em',
    background: `${color}22`, border: `1px solid ${color}44`, color,
    fontFamily: 'IBM Plex Mono, monospace', whiteSpace: 'nowrap',
  }}>{children}</span>
);

const ScoreRing = ({ score, size = 56 }) => {
  const r = rag(score);
  return (
    <div style={{ width: size, height: size, position: 'relative', flexShrink: 0 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={size/2 - 3} fill="none" stroke={C.border} strokeWidth={3} />
        <circle
          cx={size/2} cy={size/2} r={size/2 - 3}
          fill="none" stroke={r.text} strokeWidth={3}
          strokeDasharray={`${(score / 100) * Math.PI * (size - 6)} ${Math.PI * (size - 6)}`}
          strokeDashoffset={Math.PI * (size - 6) * 0.25}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: size > 48 ? 14 : 11, fontWeight: 800, color: r.text, fontFamily: 'IBM Plex Mono, monospace' }}>
        {Math.round(score)}
      </div>
    </div>
  );
};

// ─── Portfolio selector cards ──────────────────────────────────────────────────
const USE_CASE_ICONS = {
  'demo-eu-banking-sfdr':       '🏦',
  'demo-energy-transition':     '⚡',
  'demo-apac-institutions':     '🌏',
  'demo-global-climate-leaders':'🌍',
};

const PortfolioSelectorCard = ({ portfolio, selected, onClick }) => {
  const r = rag(portfolio.avg_peer_score);
  const icon = USE_CASE_ICONS[portfolio.id] || '📊';
  return (
    <div
      onClick={onClick}
      data-testid={`portfolio-card-${portfolio.id}`}
      style={{
        background: selected ? C.surface2 : C.surface,
        border: `2px solid ${selected ? C.cyan : C.border}`,
        borderRadius: 12, padding: '14px 16px', cursor: 'pointer',
        transition: 'all 0.18s',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 10 }}>
        <div style={{ fontSize: 22, lineHeight: 1 }}>{icon}</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13, fontWeight: 800, color: C.text, fontFamily: 'Space Grotesk, sans-serif', marginBottom: 2 }}>
            {portfolio.name}
          </div>
          <div style={{ fontSize: 10, color: C.muted, lineHeight: 1.4 }}>{portfolio.use_case}</div>
        </div>
        <ScoreRing score={portfolio.avg_peer_score} size={44} />
      </div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        <Badge color={C.cyan} small>{portfolio.entity_count} entities</Badge>
        <Badge color={C.green} small>€{(portfolio.total_exposure_eur_mn / 1000).toFixed(1)}B</Badge>
        {portfolio.csrd_report_coverage > 0 && (
          <Badge color={C.amber} small>{portfolio.csrd_report_coverage} CSRD reports</Badge>
        )}
      </div>
    </div>
  );
};

// ─── Overview Tab ──────────────────────────────────────────────────────────────
const OverviewTab = ({ portfolio, assessment }) => {
  if (!portfolio || !assessment) return <Spinner />;

  const { summary } = portfolio;
  const kpis = [
    { label: 'Total Exposure',  value: `€${(summary.total_exposure_eur_mn / 1000).toFixed(2)}B`, color: C.cyan },
    { label: 'Avg Peer Score',  value: `${summary.avg_peer_score}`, color: rag(summary.avg_peer_score).text },
    { label: 'NZBA Members',    value: `${summary.nzba_members}/${summary.entity_count}`, color: C.green },
    { label: 'PCAF Members',    value: `${summary.pcaf_members}/${summary.entity_count}`, color: C.blue },
    { label: 'CSRD Reports',    value: `${summary.csrd_report_coverage}/${summary.entity_count}`, color: C.amber },
    { label: 'Portfolio Score', value: `${assessment.overall_portfolio_score}`, color: rag(assessment.overall_portfolio_score).text },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* KPI row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: 12 }}>
        {kpis.map((k) => (
          <div key={k.label} style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: '12px 14px' }}>
            <div style={{ fontSize: 9, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4 }}>{k.label}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: k.color, fontFamily: 'IBM Plex Mono, monospace' }}>{k.value}</div>
          </div>
        ))}
      </div>

      {/* Description + regulatory focus */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 18 }}>
        <div style={{ fontSize: 11, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>Use Case</div>
        <div style={{ fontSize: 13, color: C.text, lineHeight: 1.6, marginBottom: 12 }}>{portfolio.description}</div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {portfolio.regulatory_focus?.map((f) => <Badge key={f} color={C.cyan}>{f}</Badge>)}
        </div>
      </div>

      {/* Entity cards */}
      <div>
        <div style={{ fontSize: 11, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>Portfolio Entities</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 10 }}>
          {assessment.entities.map((ent) => {
            const r = rag(ent.gap_assessment.weighted_avg);
            return (
              <div key={ent.slug} style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: C.text, fontFamily: 'Space Grotesk, sans-serif' }}>{ent.name}</div>
                    <div style={{ fontSize: 10, color: C.muted }}>{ent.country} · {ent.sector}</div>
                  </div>
                  <ScoreRing score={ent.gap_assessment.weighted_avg} size={40} />
                </div>
                <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 8 }}>
                  <Badge color={C.cyan} small>{ent.asset_type}</Badge>
                  <Badge color={C.green} small>€{ent.exposure_eur_mn}M</Badge>
                  {ent.has_csrd_report && <Badge color={C.amber} small>CSRD</Badge>}
                  {ent.nzba_member && <Badge color={C.green} small>NZBA</Badge>}
                </div>
                <div style={{ fontSize: 10, color: C.muted, marginBottom: 4 }}>Top gaps:</div>
                {ent.gap_assessment.top_gaps.map((g) => (
                  <div key={g} style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 2 }}>
                    <div style={{ width: 6, height: 6, borderRadius: '50%', background: C.red, flexShrink: 0 }} />
                    <div style={{ fontSize: 10, color: C.muted }}>{g}</div>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// ─── Gap Heatmap Tab ───────────────────────────────────────────────────────────
const GapHeatmapTab = ({ assessment }) => {
  if (!assessment) return <Spinner />;
  const { entities, framework_categories } = assessment;

  return (
    <div style={{ overflowX: 'auto' }}>
      <div style={{ fontSize: 11, color: C.muted, marginBottom: 12 }}>
        Coverage % per entity × framework category. Green ≥ 75% · Amber 50–74% · Red &lt; 50%
      </div>
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 11 }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left', padding: '8px 12px', color: C.muted, fontWeight: 600, borderBottom: `1px solid ${C.border}`, minWidth: 150, position: 'sticky', left: 0, background: C.bg, zIndex: 2 }}>
              Entity
            </th>
            {framework_categories.map((cat) => (
              <th
                key={cat.key}
                style={{ textAlign: 'center', padding: '6px 4px', color: groupColor[cat.group] || C.muted, fontWeight: 700, borderBottom: `1px solid ${C.border}`, minWidth: 52, fontSize: 9, letterSpacing: '0.03em' }}
                title={cat.label}
              >
                <div style={{ writingMode: 'vertical-lr', transform: 'rotate(180deg)', height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {cat.label.replace('TCFD ', '').replace('ISSB ', '').replace('ESRS ', '').replace('PCAF ', '').replace('Scope 3 ', 'S3 ')}
                </div>
              </th>
            ))}
            <th style={{ textAlign: 'center', padding: '6px 8px', color: C.text, fontWeight: 800, borderBottom: `1px solid ${C.border}`, minWidth: 60 }}>Overall</th>
          </tr>
        </thead>
        <tbody>
          {entities.map((ent) => {
            const catMap = {};
            ent.gap_assessment.categories.forEach((c) => { catMap[c.key] = c; });
            const overallR = rag(ent.gap_assessment.weighted_avg);
            return (
              <tr key={ent.slug} style={{ borderBottom: `1px solid ${C.border}22` }}>
                <td style={{ padding: '8px 12px', position: 'sticky', left: 0, background: C.bg, zIndex: 1 }}>
                  <div style={{ fontWeight: 700, color: C.text }}>{ent.name}</div>
                  <div style={{ fontSize: 9, color: C.muted }}>{ent.country} · {ent.asset_type}</div>
                  {ent.has_csrd_report && <Badge color={C.amber} small>CSRD</Badge>}
                </td>
                {framework_categories.map((cat) => {
                  const c = catMap[cat.key];
                  const r = rag(c?.coverage_pct);
                  return (
                    <td
                      key={cat.key}
                      data-testid={`gap-${ent.slug}-${cat.key}`}
                      style={{ textAlign: 'center', padding: '6px 2px', background: r.bg, borderLeft: `1px solid ${C.border}33`, fontFamily: 'IBM Plex Mono, monospace', fontWeight: 700, color: r.text, fontSize: 10 }}
                      title={`${ent.name} — ${cat.label}: ${c?.coverage_pct ?? 'N/A'}% (${c?.disclosed_dps ?? 0}/${cat.required_dps} DPs)`}
                    >
                      {c?.coverage_pct != null ? `${Math.round(c.coverage_pct)}` : '—'}
                    </td>
                  );
                })}
                <td style={{ textAlign: 'center', padding: '6px 8px' }}>
                  <span style={{ background: overallR.bg, color: overallR.text, border: `1px solid ${overallR.border}`, borderRadius: 6, padding: '2px 7px', fontSize: 11, fontFamily: 'IBM Plex Mono, monospace', fontWeight: 800 }}>
                    {Math.round(ent.gap_assessment.weighted_avg)}
                  </span>
                </td>
              </tr>
            );
          })}
          {/* Portfolio aggregate row */}
          <tr style={{ borderTop: `2px solid ${C.border}` }}>
            <td style={{ padding: '8px 12px', position: 'sticky', left: 0, background: C.bg, fontWeight: 800, color: C.text, fontSize: 11 }}>
              PORTFOLIO AVG
            </td>
            {framework_categories.map((cat) => {
              const v = assessment.portfolio_coverage[cat.key];
              const r = rag(v?.coverage_pct);
              return (
                <td key={cat.key} style={{ textAlign: 'center', padding: '6px 2px', background: r.bg, borderLeft: `1px solid ${C.border}33`, fontFamily: 'IBM Plex Mono, monospace', fontWeight: 800, color: r.text, fontSize: 10 }}>
                  {v?.coverage_pct != null ? `${Math.round(v.coverage_pct)}` : '—'}
                </td>
              );
            })}
            <td style={{ textAlign: 'center', padding: '6px 8px' }}>
              <span style={{ background: rag(assessment.overall_portfolio_score).bg, color: rag(assessment.overall_portfolio_score).text, border: `1px solid ${rag(assessment.overall_portfolio_score).border}`, borderRadius: 6, padding: '2px 7px', fontSize: 11, fontFamily: 'IBM Plex Mono, monospace', fontWeight: 800 }}>
                {Math.round(assessment.overall_portfolio_score)}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

// ─── Framework Coverage Tab ────────────────────────────────────────────────────
const FrameworkTab = ({ assessment }) => {
  if (!assessment) return <Spinner />;

  const groups = {};
  Object.entries(assessment.portfolio_coverage).forEach(([key, val]) => {
    const g = val.group;
    if (!groups[g]) groups[g] = [];
    groups[g].push({ name: val.label.replace(`${val.group} `, '').replace(val.group, '').trim(), coverage: val.coverage_pct, full: val.label, rag: val.rag });
  });

  const chartData = Object.entries(assessment.portfolio_coverage).map(([key, val]) => ({
    name: val.label.length > 22 ? val.label.slice(0, 20) + '…' : val.label,
    coverage: Math.round(val.coverage_pct),
    missing: Math.round(100 - val.coverage_pct),
    group: val.group,
    rag: val.rag,
  }));

  const CustomBar = (props) => {
    const { x, y, width, height, coverage, rag: r } = props;
    const color = r === 'GREEN' ? C.green : r === 'AMBER' ? C.amber : C.red;
    return <rect x={x} y={y} width={width} height={height} fill={color} rx={2} opacity={0.8} />;
  };

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: '10px 14px' }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: C.text, marginBottom: 4 }}>{d.name}</div>
        <div style={{ fontSize: 12, color: rag(d.coverage).text }}>{d.coverage}% covered</div>
        <div style={{ fontSize: 11, color: C.muted }}>{100 - d.coverage}% gap remaining</div>
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Group legends */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        {Object.entries(groupColor).map(([g, color]) => (
          <div key={g} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{ width: 10, height: 10, borderRadius: 2, background: color }} />
            <div style={{ fontSize: 11, color: C.muted }}>{g}</div>
          </div>
        ))}
      </div>

      {/* Main bar chart */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 20 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: C.text, marginBottom: 16 }}>Portfolio Coverage % by Framework Category</div>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} layout="vertical" margin={{ left: 140, right: 40, top: 4, bottom: 4 }}>
            <CartesianGrid horizontal={false} stroke={`${C.border}44`} />
            <XAxis type="number" domain={[0, 100]} tick={{ fill: C.muted, fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
            <YAxis type="category" dataKey="name" tick={{ fill: C.muted, fontSize: 10 }} width={136} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="coverage" shape={<CustomBar />} barSize={14}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.rag === 'GREEN' ? C.green : entry.rag === 'AMBER' ? C.amber : C.red} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Group summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 }}>
        {Object.entries(groups).map(([grp, cats]) => {
          const avg = Math.round(cats.reduce((a, b) => a + b.coverage, 0) / cats.length);
          const r = rag(avg);
          return (
            <div key={grp} style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <div style={{ fontSize: 12, fontWeight: 800, color: groupColor[grp] || C.cyan, fontFamily: 'Space Grotesk, sans-serif' }}>{grp}</div>
                <div style={{ fontSize: 18, fontWeight: 800, color: r.text, fontFamily: 'IBM Plex Mono, monospace' }}>{avg}%</div>
              </div>
              {cats.map((c) => {
                const cr = rag(c.coverage);
                return (
                  <div key={c.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <div style={{ fontSize: 10, color: C.muted, flex: 1 }}>{c.name || c.full}</div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: cr.text, fontFamily: 'IBM Plex Mono, monospace' }}>{Math.round(c.coverage)}%</div>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ─── Entities Tab ──────────────────────────────────────────────────────────────
const EntitiesTab = ({ assessment }) => {
  const [selected, setSelected] = useState(assessment?.entities?.[0]?.slug ?? null);
  if (!assessment) return <Spinner />;
  const entity = assessment.entities.find((e) => e.slug === selected);

  const chartData = entity?.gap_assessment.categories.map((c) => ({
    name: c.label.length > 20 ? c.label.slice(0, 18) + '…' : c.label,
    coverage: Math.round(c.coverage_pct),
    missing: Math.round(100 - c.coverage_pct),
    disclosed: c.disclosed_dps,
    required: c.required_dps,
    rag: c.rag,
    full: c.label,
  })) || [];

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: '10px 14px' }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: C.text, marginBottom: 4 }}>{d.full}</div>
        <div style={{ fontSize: 12, color: rag(d.coverage).text }}>{d.coverage}% disclosed</div>
        <div style={{ fontSize: 11, color: C.muted }}>{d.disclosed} of {d.required} required data points</div>
        <div style={{ fontSize: 11, color: C.red }}>{d.required - d.disclosed} missing data points</div>
      </div>
    );
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: 16 }}>
      {/* Entity list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {assessment.entities.map((ent) => {
          const r = rag(ent.gap_assessment.weighted_avg);
          return (
            <div
              key={ent.slug}
              onClick={() => setSelected(ent.slug)}
              style={{
                background: selected === ent.slug ? C.surface2 : C.surface,
                border: `1px solid ${selected === ent.slug ? C.cyan : C.border}`,
                borderRadius: 8, padding: '10px 12px', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 10,
              }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: C.text }}>{ent.name}</div>
                <div style={{ fontSize: 9, color: C.muted }}>{ent.country} · €{ent.exposure_eur_mn}M</div>
              </div>
              <div style={{ fontSize: 16, fontWeight: 800, color: r.text, fontFamily: 'IBM Plex Mono, monospace' }}>{Math.round(ent.gap_assessment.weighted_avg)}</div>
            </div>
          );
        })}
      </div>

      {/* Entity detail */}
      {entity && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Header */}
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: C.text, fontFamily: 'Space Grotesk, sans-serif', marginBottom: 4 }}>{entity.name}</div>
              <div style={{ fontSize: 11, color: C.muted, marginBottom: 8 }}>{entity.country} · {entity.sector} · {entity.asset_type} · €{entity.exposure_eur_mn}M</div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {entity.has_csrd_report && <Badge color={C.amber}>CSRD Report Processed</Badge>}
                {entity.nzba_member && <Badge color={C.green}>NZBA Member</Badge>}
                {entity.pcaf_member && <Badge color={C.blue}>PCAF Member</Badge>}
                <Badge color={{ Approved: C.green, Committed: C.amber, 'Not Committed': C.red }[entity.sbti_status] || C.muted}>
                  SBTi: {entity.sbti_status}
                </Badge>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 36, fontWeight: 800, color: rag(entity.gap_assessment.weighted_avg).text, fontFamily: 'IBM Plex Mono, monospace' }}>
                {Math.round(entity.gap_assessment.weighted_avg)}
              </div>
              <div style={{ fontSize: 10, color: C.muted }}>Overall Coverage</div>
              <div style={{ fontSize: 10, color: C.muted }}>Source: {entity.gap_assessment.data_source}</div>
            </div>
          </div>

          {/* Top 3 gaps */}
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 14 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: C.red, marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Priority Gaps</div>
            <div style={{ display: 'flex', gap: 8 }}>
              {entity.gap_assessment.top_gaps.map((g, i) => (
                <div key={g} style={{ flex: 1, background: 'rgba(239,68,68,0.08)', border: `1px solid ${C.red}44`, borderRadius: 8, padding: '8px 12px' }}>
                  <div style={{ fontSize: 9, color: C.red, fontWeight: 700, marginBottom: 3 }}>Gap #{i + 1}</div>
                  <div style={{ fontSize: 11, color: C.text }}>{g}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Coverage bar chart */}
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: C.text, marginBottom: 12 }}>Framework Coverage — {entity.name}</div>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData} layout="vertical" margin={{ left: 130, right: 50, top: 2, bottom: 2 }}>
                <CartesianGrid horizontal={false} stroke={`${C.border}44`} />
                <XAxis type="number" domain={[0, 100]} tick={{ fill: C.muted, fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
                <YAxis type="category" dataKey="name" tick={{ fill: C.muted, fontSize: 10 }} width={126} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="coverage" barSize={11} radius={2}>
                  {chartData.map((d, i) => (
                    <Cell key={i} fill={d.rag === 'GREEN' ? C.green : d.rag === 'AMBER' ? C.amber : C.red} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Data points table */}
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 16, overflowX: 'auto' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: C.text, marginBottom: 12 }}>Data Point Coverage Detail</div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11 }}>
              <thead>
                <tr>
                  {['Framework Category', 'Group', 'Disclosed DPs', 'Required DPs', 'Missing', 'Coverage', 'Status'].map((h) => (
                    <th key={h} style={{ textAlign: 'left', padding: '6px 10px', color: C.muted, fontWeight: 600, borderBottom: `1px solid ${C.border}`, fontSize: 10 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {entity.gap_assessment.categories.map((c) => {
                  const r = rag(c.coverage_pct);
                  return (
                    <tr key={c.key} style={{ borderBottom: `1px solid ${C.border}22` }}>
                      <td style={{ padding: '6px 10px', color: C.text }}>{c.label}</td>
                      <td style={{ padding: '6px 10px' }}><Badge color={groupColor[c.group] || C.cyan} small>{c.group}</Badge></td>
                      <td style={{ padding: '6px 10px', fontFamily: 'IBM Plex Mono, monospace', color: C.green }}>{c.disclosed_dps}</td>
                      <td style={{ padding: '6px 10px', fontFamily: 'IBM Plex Mono, monospace', color: C.muted }}>{c.required_dps}</td>
                      <td style={{ padding: '6px 10px', fontFamily: 'IBM Plex Mono, monospace', color: c.missing_dps > 0 ? C.red : C.green }}>{c.missing_dps}</td>
                      <td style={{ padding: '6px 10px', fontFamily: 'IBM Plex Mono, monospace', color: r.text, fontWeight: 700 }}>{Math.round(c.coverage_pct)}%</td>
                      <td style={{ padding: '6px 10px' }}><Badge color={r.border} small>{c.rag}</Badge></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Main Page ─────────────────────────────────────────────────────────────────
export default function AnalystPortfoliosPage() {
  const [portfolioList, setPortfolioList]     = useState([]);
  const [selectedId, setSelectedId]           = useState(null);
  const [selectedPortfolio, setSelectedPortfolio] = useState(null);
  const [assessment, setAssessment]           = useState(null);
  const [loading, setLoading]                 = useState(true);
  const [loadingAssessment, setLoadingAssessment] = useState(false);
  const [seeding, setSeeding]                 = useState(false);
  const [seedMsg, setSeedMsg]                 = useState(null);
  const [activeTab, setActiveTab]             = useState('overview');

  // Load portfolio list
  useEffect(() => {
    setLoading(true);
    axios.get(`${API}/api/v1/analyst-portfolios/`)
      .then((r) => {
        setPortfolioList(r.data.portfolios || []);
        if (r.data.portfolios?.length) setSelectedId(r.data.portfolios[0].id);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Load portfolio detail + gap assessment when selection changes
  useEffect(() => {
    if (!selectedId) return;
    setLoadingAssessment(true);
    setSelectedPortfolio(null);
    setAssessment(null);
    setActiveTab('overview');

    Promise.all([
      axios.get(`${API}/api/v1/analyst-portfolios/${selectedId}`),
      axios.get(`${API}/api/v1/analyst-portfolios/${selectedId}/gap-assessment`),
    ])
      .then(([portRes, gapRes]) => {
        setSelectedPortfolio(portRes.data);
        setAssessment(gapRes.data);
      })
      .catch(console.error)
      .finally(() => setLoadingAssessment(false));
  }, [selectedId]);

  const handleSeed = useCallback(async () => {
    setSeeding(true);
    setSeedMsg(null);
    try {
      const r = await axios.post(`${API}/api/v1/analyst-portfolios/seed`);
      const d = r.data;
      setSeedMsg(`${d.message} — portfolios are now available in Portfolio Analytics.`);
    } catch (e) {
      setSeedMsg('Seed failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setSeeding(false);
    }
  }, []);

  const TABS = [
    { id: 'overview',   label: 'Overview'          },
    { id: 'heatmap',    label: 'Gap Heatmap'        },
    { id: 'framework',  label: 'Framework Coverage' },
    { id: 'entities',   label: 'Entity Detail'      },
  ];

  return (
    <div data-testid="analyst-portfolios-page" style={{ display: 'flex', flexDirection: 'column', gap: 0, height: '100%' }}>
      {/* Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: C.text, fontFamily: 'Space Grotesk, sans-serif' }}>
              Analyst Portfolio Workbench
            </h1>
            <p style={{ margin: '6px 0 0', fontSize: 12, color: C.muted }}>
              4 pre-built portfolios based on 8 processed CSRD reports and 12-institution peer benchmark group.
              Gap assessment across TCFD · ISSB S1/S2 · ESRS/CSRD · PCAF · TNFD — 18 framework categories.
            </p>
          </div>
          <button
            onClick={handleSeed}
            disabled={seeding}
            data-testid="seed-portfolios-btn"
            style={{
              background: seeding ? C.surface : 'rgba(16,185,129,0.15)',
              border: `1px solid ${C.green}`,
              borderRadius: 8, padding: '8px 16px',
              color: C.green, fontSize: 12, fontWeight: 700, cursor: seeding ? 'not-allowed' : 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            {seeding ? 'Seeding…' : 'Seed to Portfolio Analytics'}
          </button>
        </div>
        {seedMsg && (
          <div style={{ marginTop: 8, padding: '8px 12px', background: 'rgba(16,185,129,0.08)', border: `1px solid ${C.green}44`, borderRadius: 6, fontSize: 11, color: C.green }}>
            {seedMsg}
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: 16, flex: 1 }}>
        {/* Left: portfolio selector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 2 }}>Select Portfolio</div>
          {loading ? <Spinner /> : portfolioList.map((p) => (
            <PortfolioSelectorCard
              key={p.id}
              portfolio={p}
              selected={selectedId === p.id}
              onClick={() => setSelectedId(p.id)}
            />
          ))}

          {/* Legend */}
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: 12, marginTop: 6 }}>
            <div style={{ fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>Coverage Legend</div>
            {[['≥ 75%', C.green, 'Adequate'], ['50–74%', C.amber, 'Partial'], ['< 50%', C.red, 'Insufficient']].map(([label, color, sub]) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5 }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: color }} />
                <div style={{ fontSize: 10, color: C.text }}>{label}</div>
                <div style={{ fontSize: 9, color: C.muted }}>— {sub}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: tabs + content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {/* Tab bar */}
          <div style={{ display: 'flex', gap: 4, borderBottom: `1px solid ${C.border}`, marginBottom: 20, paddingBottom: 0 }}>
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                data-testid={`analyst-tab-${t.id}`}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  padding: '8px 16px',
                  fontSize: 12, fontWeight: activeTab === t.id ? 800 : 500,
                  color: activeTab === t.id ? C.cyan : C.muted,
                  borderBottom: activeTab === t.id ? `2px solid ${C.cyan}` : '2px solid transparent',
                  marginBottom: -1, transition: 'all 0.15s',
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {loadingAssessment ? (
            <Spinner />
          ) : (
            <>
              {activeTab === 'overview'   && <OverviewTab portfolio={selectedPortfolio} assessment={assessment} />}
              {activeTab === 'heatmap'    && <GapHeatmapTab assessment={assessment} />}
              {activeTab === 'framework'  && <FrameworkTab assessment={assessment} />}
              {activeTab === 'entities'   && <EntitiesTab assessment={assessment} />}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
