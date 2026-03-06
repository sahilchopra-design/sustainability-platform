/**
 * PeerBenchmarkPage.jsx
 * Route: /peer-benchmark
 *
 * TCFD / ISSB / ESRS / PCAF peer gap assessment across 12 global financial institutions.
 * Real CSRD report data (8 processed reports) enriches analyst estimates where available.
 *
 * Tabs:
 *   1. Peer Matrix   — institution × framework heatmap (18 categories)
 *   2. Institution Profile — radar chart + strengths / gaps + analyst note
 *   3. Framework Coverage — bar chart by framework group
 *   4. Regional Benchmarks — Europe / Asia Pacific / North America comparison
 *   5. Real Reports — processed annual reports with filter by regulation / sector / type
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell,
} from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// ─── Design tokens ────────────────────────────────────────────────────────────
const C = {
  green:   '#10b981',
  amber:   '#f59e0b',
  red:     '#ef4444',
  cyan:    'hsl(199,89%,56%)',
  bg:      'hsl(222,35%,7%)',
  surface: 'hsl(222,30%,11%)',
  border:  'hsl(222,25%,18%)',
  muted:   'hsl(222,15%,45%)',
  text:    'hsl(210,40%,96%)',
};

// ─── RAG helpers ──────────────────────────────────────────────────────────────
const rag = (score) => {
  if (score == null) return { bg: 'rgba(255,255,255,0.03)', border: C.border, text: C.muted, label: 'N/A' };
  if (score >= 75)   return { bg: 'rgba(16,185,129,0.14)',  border: C.green,  text: C.green,  label: 'GREEN' };
  if (score >= 50)   return { bg: 'rgba(245,158,11,0.14)',  border: C.amber,  text: C.amber,  label: 'AMBER' };
  return              { bg: 'rgba(239,68,68,0.12)',          border: C.red,    text: C.red,    label: 'RED'   };
};

const ragDot = (score) => {
  if (score == null) return C.muted;
  if (score >= 75) return C.green;
  if (score >= 50) return C.amber;
  return C.red;
};

// ─── Category abbreviations ───────────────────────────────────────────────────
const CAT_ABBR = {
  tcfd_governance:    'TCFD-G', tcfd_strategy:    'TCFD-S',
  tcfd_risk_mgmt:     'TCFD-R', tcfd_metrics:     'TCFD-M',
  issb_s1:            'S1',     issb_s2:          'S2',
  esrs_e1:            'E1',     esrs_env_other:   'E2-5',
  esrs_social:        'Soc.',   esrs_governance:  'Gov.',
  double_materiality: 'DMA',    pcaf_financed:    'PCAF',
  scope3_cat15:       'Cat15',  paris_alignment:  'Paris',
  transition_plan:    'Trans.', physical_risk:    'Phys.',
  scenario_analysis:  'Scen.',  tnfd_nature:      'TNFD',
};

const CAT_GROUPS = {
  TCFD:               ['tcfd_governance','tcfd_strategy','tcfd_risk_mgmt','tcfd_metrics'],
  ISSB:               ['issb_s1','issb_s2'],
  'ESRS/CSRD':        ['esrs_e1','esrs_env_other','esrs_social','esrs_governance','double_materiality'],
  'Financed Emissions':['pcaf_financed','scope3_cat15'],
  'Net Zero':         ['paris_alignment','transition_plan'],
  'Climate Risk':     ['physical_risk','scenario_analysis'],
  Nature:             ['tnfd_nature'],
};

// 8 radar dimensions (aggregate of related categories)
const RADAR_DIMS = [
  { key: 'tcfd',        label: 'TCFD',             cats: ['tcfd_governance','tcfd_strategy','tcfd_risk_mgmt','tcfd_metrics'] },
  { key: 'issb',        label: 'ISSB',             cats: ['issb_s1','issb_s2'] },
  { key: 'esrs_e1',     label: 'ESRS Climate',     cats: ['esrs_e1'] },
  { key: 'esrs_other',  label: 'ESRS Other',       cats: ['esrs_env_other','esrs_social','esrs_governance'] },
  { key: 'dma',         label: 'Double Materiality',cats: ['double_materiality'] },
  { key: 'financed',    label: 'Financed Emissions',cats: ['pcaf_financed','scope3_cat15'] },
  { key: 'net_zero',    label: 'Net Zero',          cats: ['paris_alignment','transition_plan'] },
  { key: 'nature',      label: 'Nature (TNFD)',     cats: ['tnfd_nature'] },
];

// Region flags
const REGION_FLAG = {
  'North America': '🌎',
  'Europe':        '🌍',
  'Asia Pacific':  '🌏',
};

const avg = (vals) =>
  vals.length === 0 ? 0 : Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);

const radarData = (scores) =>
  RADAR_DIMS.map((dim) => ({
    subject: dim.label,
    value: avg(dim.cats.map((c) => scores[c] ?? 0)),
    fullMark: 100,
  }));

// ─── Sub-components ───────────────────────────────────────────────────────────

function KpiCard({ label, value, unit, sub }) {
  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10,
      padding: '14px 18px', minWidth: 120,
    }}>
      <div style={{ fontSize: 11, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 26, fontWeight: 700, color: C.cyan, fontFamily: 'IBM Plex Mono, monospace' }}>
        {value}<span style={{ fontSize: 13, color: C.muted, marginLeft: 3 }}>{unit}</span>
      </div>
      {sub && <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function Badge({ children, color = C.cyan, bg }) {
  return (
    <span style={{
      background: bg || `${color}1a`, border: `1px solid ${color}55`,
      color, borderRadius: 4, fontSize: 10, fontWeight: 700,
      padding: '2px 7px', letterSpacing: '0.05em', textTransform: 'uppercase',
    }}>
      {children}
    </span>
  );
}

function Tab({ label, active, onClick, badge }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '8px 16px', borderRadius: 6, border: 'none', cursor: 'pointer',
        fontFamily: 'IBM Plex Sans, sans-serif', fontSize: 13, fontWeight: 600,
        background: active ? C.cyan : 'transparent',
        color: active ? C.bg : C.muted,
        transition: 'all 0.15s',
        display: 'flex', alignItems: 'center', gap: 6,
      }}
    >
      {label}
      {badge && (
        <span style={{
          background: active ? C.bg : C.cyan, color: active ? C.cyan : C.bg,
          borderRadius: 10, fontSize: 9, fontWeight: 800, padding: '1px 5px',
        }}>
          {badge}
        </span>
      )}
    </button>
  );
}

// ─── Heatmap Tab ──────────────────────────────────────────────────────────────

function HeatmapTab({ heatmap, filterRegion, setFilterRegion }) {
  if (!heatmap) return <Spinner />;
  const { rows = [], categories = [] } = heatmap;

  const regions = ['All', ...new Set(rows.map((r) => r.region))];
  const filtered = filterRegion === 'All' ? rows : rows.filter((r) => r.region === filterRegion);

  return (
    <div>
      {/* Filter bar */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ color: C.muted, fontSize: 12 }}>Region:</span>
        {regions.map((r) => (
          <button
            key={r}
            onClick={() => setFilterRegion(r)}
            style={{
              padding: '4px 12px', borderRadius: 20, border: `1px solid ${filterRegion === r ? C.cyan : C.border}`,
              background: filterRegion === r ? `${C.cyan}1a` : 'transparent',
              color: filterRegion === r ? C.cyan : C.muted,
              cursor: 'pointer', fontSize: 12, fontFamily: 'IBM Plex Sans, sans-serif',
            }}
          >
            {REGION_FLAG[r] || ''} {r}
          </button>
        ))}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 10, alignItems: 'center' }}>
          {[['≥ 75', C.green, 'rgba(16,185,129,0.14)'], ['50–74', C.amber, 'rgba(245,158,11,0.14)'], ['< 50', C.red, 'rgba(239,68,68,0.12)']].map(([lbl, clr, bg]) => (
            <span key={lbl} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: C.muted }}>
              <span style={{ width: 12, height: 12, borderRadius: 2, background: bg, border: `1px solid ${clr}`, display: 'inline-block' }} />
              {lbl}
            </span>
          ))}
          <Badge color={C.cyan}>Real data available</Badge>
        </div>
      </div>

      {/* Matrix */}
      <div style={{ overflowX: 'auto', borderRadius: 10, border: `1px solid ${C.border}` }}>
        <table style={{ borderCollapse: 'collapse', width: '100%', minWidth: 900 }}>
          <thead>
            {/* Group header row */}
            <tr>
              <th style={{ width: 200, background: C.surface, borderBottom: `1px solid ${C.border}` }} />
              {Object.entries(CAT_GROUPS).map(([grp, cats]) => (
                <th
                  key={grp}
                  colSpan={cats.length}
                  style={{
                    background: C.surface, color: C.muted, fontSize: 10,
                    fontFamily: 'IBM Plex Sans, sans-serif', fontWeight: 700,
                    letterSpacing: '0.07em', textTransform: 'uppercase',
                    borderBottom: `1px solid ${C.border}`,
                    borderLeft: `1px solid ${C.border}`, textAlign: 'center', padding: '6px 4px',
                  }}
                >
                  {grp}
                </th>
              ))}
              <th style={{ background: C.surface, borderBottom: `1px solid ${C.border}`, borderLeft: `1px solid ${C.border}`, width: 70, color: C.muted, fontSize: 10, padding: '6px 4px', textAlign: 'center' }}>
                OVERALL
              </th>
            </tr>
            {/* Category abbrev row */}
            <tr style={{ background: `${C.surface}cc` }}>
              <th style={{ textAlign: 'left', padding: '6px 12px', color: C.muted, fontSize: 11, fontFamily: 'IBM Plex Sans, sans-serif', fontWeight: 600, borderBottom: `1px solid ${C.border}` }}>
                Institution
              </th>
              {categories.map((cat) => (
                <th
                  key={cat.key}
                  style={{
                    width: 46, padding: '4px 2px', textAlign: 'center',
                    color: C.muted, fontSize: 10, fontFamily: 'IBM Plex Mono, monospace',
                    borderBottom: `1px solid ${C.border}`,
                    borderLeft: `1px solid ${C.border}88`,
                    fontWeight: 600, letterSpacing: '0.02em',
                  }}
                  title={cat.label}
                >
                  {CAT_ABBR[cat.key] || cat.key}
                </th>
              ))}
              <th style={{ borderBottom: `1px solid ${C.border}`, borderLeft: `1px solid ${C.border}` }} />
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, ri) => {
              const hasReal = row.has_real_data;
              return (
                <tr
                  key={row.slug}
                  style={{
                    background: ri % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)',
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(0,198,255,0.04)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = ri % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)'; }}
                >
                  {/* Institution name cell */}
                  <td style={{ padding: '7px 12px', borderBottom: `1px solid ${C.border}33` }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span style={{ fontSize: 14 }}>{REGION_FLAG[row.region] || '🏦'}</span>
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 700, color: C.text, fontFamily: 'IBM Plex Sans, sans-serif' }}>
                          {row.name}
                          {hasReal && (
                            <span
                              title="Real CSRD report data"
                              style={{ marginLeft: 5, width: 6, height: 6, borderRadius: '50%', background: C.cyan, display: 'inline-block' }}
                            />
                          )}
                        </div>
                        <div style={{ fontSize: 10, color: C.muted }}>{row.region}</div>
                      </div>
                    </div>
                  </td>
                  {/* Score cells */}
                  {categories.map((cat) => {
                    const score = row[cat.key]?.score;
                    const r = rag(score);
                    return (
                      <td
                        key={cat.key}
                        data-testid={`heatmap-${row.slug}-${cat.key}`}
                        style={{
                          width: 46, textAlign: 'center', padding: '6px 2px',
                          background: r.bg,
                          borderBottom: `1px solid ${C.border}22`,
                          borderLeft: `1px solid ${C.border}44`,
                          fontSize: 11, fontFamily: 'IBM Plex Mono, monospace',
                          fontWeight: 700, color: r.text,
                        }}
                        title={`${row.name} — ${cat.label}: ${score ?? 'N/A'}`}
                      >
                        {score ?? '—'}
                      </td>
                    );
                  })}
                  {/* Overall score */}
                  <td style={{
                    textAlign: 'center', borderLeft: `1px solid ${C.border}`,
                    borderBottom: `1px solid ${C.border}22`,
                    padding: '6px 4px',
                  }}>
                    <span style={{
                      background: rag(row.weighted_avg).bg,
                      color: rag(row.weighted_avg).text,
                      border: `1px solid ${rag(row.weighted_avg).border}`,
                      borderRadius: 6, padding: '2px 6px',
                      fontSize: 11, fontFamily: 'IBM Plex Mono, monospace', fontWeight: 800,
                    }}>
                      {row.weighted_avg ? Math.round(row.weighted_avg) : '—'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Real data note */}
      <div style={{ marginTop: 12, fontSize: 11, color: C.muted, display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ width: 6, height: 6, borderRadius: '50%', background: C.cyan, display: 'inline-block' }} />
        Blue dot = institution has a processed CSRD annual report in the system. Scores for those entities
        blend real extracted KPI coverage with analyst estimates.
      </div>
    </div>
  );
}

// ─── Institution Profile Tab ───────────────────────────────────────────────────

function ProfileTab({ institutions, selectedSlug, setSelectedSlug }) {
  const [profile, setProfile] = useState(null);
  const [gaps, setGaps] = useState([]);
  const [profileLoading, setProfileLoading] = useState(false);

  const loadProfile = useCallback(async (slug) => {
    setProfileLoading(true);
    try {
      const [pRes, gRes] = await Promise.all([
        axios.get(`${API}/api/v1/peer-benchmark/institution/${slug}`),
        axios.get(`${API}/api/v1/peer-benchmark/institution/${slug}/top-gaps?top_n=6`),
      ]);
      setProfile(pRes.data);
      setGaps(gRes.data.gaps || []);
    } catch (e) {
      console.error('Profile load failed', e);
    } finally {
      setProfileLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedSlug) loadProfile(selectedSlug);
  }, [selectedSlug, loadProfile]);

  if (!profile && !profileLoading) return (
    <div style={{ color: C.muted, textAlign: 'center', padding: 40 }}>Select an institution to view its profile</div>
  );

  if (profileLoading) return <Spinner />;

  const rd = radarData(profile.scores || {});
  const overallRag = rag(profile.weighted_score);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
      {/* Left: selector + profile card */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Institution selector */}
        <select
          value={selectedSlug}
          onChange={(e) => setSelectedSlug(e.target.value)}
          style={{
            background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8,
            color: C.text, padding: '8px 12px', fontSize: 13,
            fontFamily: 'IBM Plex Sans, sans-serif', cursor: 'pointer', width: '100%',
          }}
        >
          {institutions.map((i) => (
            <option key={i.slug} value={i.slug}>{i.name} ({i.country})</option>
          ))}
        </select>

        {/* Profile card */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: C.text, fontFamily: 'Space Grotesk, sans-serif', marginBottom: 4 }}>
                {profile.name}
              </div>
              <div style={{ fontSize: 12, color: C.muted }}>{profile.country} · {profile.region}</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{
                fontSize: 32, fontWeight: 800, fontFamily: 'IBM Plex Mono, monospace',
                color: overallRag.text,
              }}>
                {profile.weighted_score ? Math.round(profile.weighted_score) : '—'}
              </div>
              <div style={{ fontSize: 10, color: C.muted }}>Overall Score</div>
            </div>
          </div>

          {/* Badges */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
            <Badge color={C.cyan}>{profile.institution_type}</Badge>
            {profile.nzba_member && <Badge color={C.green}>NZBA</Badge>}
            {profile.pcaf_member && <Badge color={C.green}>PCAF</Badge>}
            {profile.tnfd_supporter && <Badge color='#8b5cf6'>TNFD</Badge>}
            {profile.has_real_data && <Badge color={C.cyan}>Real CSRD Data</Badge>}
            {profile.net_zero_target_year && (
              <Badge color={C.amber}>NZ {profile.net_zero_target_year}</Badge>
            )}
          </div>

          {/* AUM */}
          {profile.assets_usd_bn && (
            <div style={{ marginBottom: 12, fontSize: 12, color: C.muted }}>
              <span style={{ color: C.text, fontWeight: 600 }}>AUM: </span>
              ${profile.assets_usd_bn.toLocaleString()}bn USD
            </div>
          )}

          {/* Mandatory frameworks */}
          {profile.mandatory_frameworks?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
                Mandatory Frameworks
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {profile.mandatory_frameworks.map((f) => (
                  <span key={f} style={{ fontSize: 10, color: C.amber, background: `${C.amber}12`, borderRadius: 3, padding: '1px 6px', border: `1px solid ${C.amber}33` }}>
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Analyst note */}
          {profile.analyst_note && (
            <div style={{
              marginTop: 14, padding: 12, background: `${C.cyan}08`,
              border: `1px solid ${C.cyan}22`, borderRadius: 8,
              fontSize: 12, color: `${C.text}cc`, fontStyle: 'italic', lineHeight: 1.6,
            }}>
              {profile.analyst_note}
            </div>
          )}
        </div>

        {/* Top Gaps */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 12, fontFamily: 'Space Grotesk, sans-serif' }}>
            Priority Gaps
          </div>
          {gaps.map((gap, i) => (
            <div
              key={gap.key}
              style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '8px 0',
                borderBottom: i < gaps.length - 1 ? `1px solid ${C.border}44` : 'none',
              }}
            >
              <div style={{
                width: 24, height: 24, borderRadius: '50%', background: rag(gap.score).bg,
                border: `1px solid ${rag(gap.score).border}`, display: 'flex', alignItems: 'center',
                justifyContent: 'center', fontSize: 9, fontWeight: 800, color: rag(gap.score).text,
                fontFamily: 'IBM Plex Mono, monospace', flexShrink: 0,
              }}>
                {i + 1}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{gap.label}</div>
                <div style={{ fontSize: 10, color: C.muted }}>{gap.group}</div>
              </div>
              <div style={{
                fontSize: 13, fontWeight: 800, color: rag(gap.score).text,
                fontFamily: 'IBM Plex Mono, monospace', minWidth: 28, textAlign: 'right',
              }}>
                {gap.score}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right: Radar + Strengths */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Radar chart */}
        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8, fontFamily: 'Space Grotesk, sans-serif' }}>
            Framework Coverage Radar
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={rd} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
              <PolarGrid stroke={C.border} />
              <PolarAngleAxis dataKey="subject" tick={{ fill: C.muted, fontSize: 11, fontFamily: 'IBM Plex Sans, sans-serif' }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: C.muted, fontSize: 9 }} tickCount={5} />
              <Radar
                name={profile.name}
                dataKey="value"
                stroke={C.cyan}
                fill={C.cyan}
                fillOpacity={0.18}
                dot={{ fill: C.cyan, r: 3 }}
              />
              <Tooltip
                contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: C.text }}
                itemStyle={{ color: C.cyan }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Key Strengths */}
        {profile.key_strengths?.length > 0 && (
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.green, marginBottom: 10, fontFamily: 'Space Grotesk, sans-serif' }}>
              Key Strengths
            </div>
            <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
              {profile.key_strengths.map((s, i) => (
                <li key={i} style={{
                  padding: '5px 0', borderBottom: i < profile.key_strengths.length - 1 ? `1px solid ${C.border}44` : 'none',
                  fontSize: 12, color: `${C.text}cc`, display: 'flex', gap: 8,
                }}>
                  <span style={{ color: C.green, flexShrink: 0 }}>+</span>
                  {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Priority Gaps (text) */}
        {profile.priority_gaps?.length > 0 && (
          <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.red, marginBottom: 10, fontFamily: 'Space Grotesk, sans-serif' }}>
              Identified Gaps
            </div>
            <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
              {profile.priority_gaps.map((g, i) => (
                <li key={i} style={{
                  padding: '5px 0', borderBottom: i < profile.priority_gaps.length - 1 ? `1px solid ${C.border}44` : 'none',
                  fontSize: 12, color: `${C.text}cc`, display: 'flex', gap: 8,
                }}>
                  <span style={{ color: C.red, flexShrink: 0 }}>!</span>
                  {g}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Framework Coverage Tab ────────────────────────────────────────────────────

function CoverageTab({ frameworkCoverage, institutions }) {
  const [activeGroup, setActiveGroup] = useState('All');

  if (!frameworkCoverage?.length) return <Spinner />;

  const groups = ['All', ...Object.keys(CAT_GROUPS)];
  const filtered = activeGroup === 'All'
    ? frameworkCoverage
    : frameworkCoverage.filter((fc) => fc.group === activeGroup);

  // Build bar chart data: one bar per institution, grouped by category
  const barData = filtered.map((fc) => {
    const entry = { category: CAT_ABBR[fc.key] || fc.key };
    institutions.forEach((inst) => {
      entry[inst.slug] = inst.scores?.[fc.key] ?? 0;
    });
    entry.peer_avg = fc.peer_avg;
    return entry;
  });

  const COLORS = [
    C.cyan, '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#f97316',
    '#06b6d4', '#84cc16', '#a855f7', '#14b8a6', '#eab308', '#64748b',
  ];

  return (
    <div>
      {/* Group filter */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' }}>
        {groups.map((g) => (
          <button
            key={g}
            onClick={() => setActiveGroup(g)}
            style={{
              padding: '5px 13px', borderRadius: 20, border: `1px solid ${activeGroup === g ? C.cyan : C.border}`,
              background: activeGroup === g ? `${C.cyan}1a` : 'transparent',
              color: activeGroup === g ? C.cyan : C.muted,
              cursor: 'pointer', fontSize: 11, fontFamily: 'IBM Plex Sans, sans-serif', fontWeight: 600,
            }}
          >
            {g}
          </button>
        ))}
      </div>

      {/* Bar chart */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20, marginBottom: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 12, fontFamily: 'Space Grotesk, sans-serif' }}>
          Institution Scores by Framework Category
        </div>
        <ResponsiveContainer width="100%" height={360}>
          <BarChart data={barData} margin={{ top: 4, right: 16, left: 0, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
            <XAxis
              dataKey="category"
              tick={{ fill: C.muted, fontSize: 10, fontFamily: 'IBM Plex Mono, monospace' }}
              angle={-35} textAnchor="end" interval={0}
            />
            <YAxis tick={{ fill: C.muted, fontSize: 10 }} domain={[0, 100]} />
            <Tooltip
              contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 11 }}
              cursor={{ fill: 'rgba(0,198,255,0.05)' }}
            />
            <Legend wrapperStyle={{ fontSize: 10, color: C.muted, paddingTop: 8 }} />
            {institutions.slice(0, 12).map((inst, i) => (
              <Bar key={inst.slug} dataKey={inst.slug} name={inst.name} fill={COLORS[i % COLORS.length]} opacity={0.85} radius={[2, 2, 0, 0]} maxBarSize={16} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Peer average table */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 16 }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: C.text, marginBottom: 10, fontFamily: 'Space Grotesk, sans-serif' }}>
          Peer-Group Averages
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 8 }}>
          {filtered.map((fc) => {
            const r = rag(fc.peer_avg);
            return (
              <div
                key={fc.key}
                style={{
                  padding: '10px 12px', borderRadius: 8,
                  background: r.bg, border: `1px solid ${r.border}44`,
                }}
              >
                <div style={{ fontSize: 10, color: C.muted, marginBottom: 3 }}>{fc.label}</div>
                <div style={{ fontSize: 20, fontWeight: 800, fontFamily: 'IBM Plex Mono, monospace', color: r.text }}>
                  {Math.round(fc.peer_avg)}
                </div>
                <div style={{ fontSize: 9, color: r.text, marginTop: 2, opacity: 0.8 }}>{r.label}</div>
                <div style={{ marginTop: 6, height: 3, borderRadius: 2, background: C.border }}>
                  <div style={{ height: '100%', borderRadius: 2, background: r.text, width: `${fc.peer_avg}%`, transition: 'width 0.6s' }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ─── Regional Benchmarks Tab ───────────────────────────────────────────────────

function RegionalTab({ regionalAvgs }) {
  if (!regionalAvgs?.length) return <Spinner />;

  const groupedData = RADAR_DIMS.map((dim) => {
    const entry = { subject: dim.label };
    regionalAvgs.forEach((ra) => {
      entry[ra.region] = avg(dim.cats.map((c) => ra.avg_scores?.[c] ?? 0));
    });
    return entry;
  });

  const REGION_COLORS = { Europe: '#10b981', 'Asia Pacific': C.cyan, 'North America': '#f59e0b' };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
      {/* Summary cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {regionalAvgs.map((ra) => (
          <div
            key={ra.region}
            style={{
              background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 700, color: C.text, fontFamily: 'Space Grotesk, sans-serif' }}>
                  {REGION_FLAG[ra.region] || ''} {ra.region}
                </div>
                <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>{ra.institution_count} institutions</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 28, fontWeight: 800, fontFamily: 'IBM Plex Mono, monospace', color: REGION_COLORS[ra.region] || C.cyan }}>
                  {Math.round(ra.overall_avg)}
                </div>
                <div style={{ fontSize: 10, color: C.muted }}>Weighted Avg</div>
              </div>
            </div>
            {/* Mini bars for key categories */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
              {['esrs_e1', 'pcaf_financed', 'paris_alignment', 'tcfd_metrics'].map((cat) => {
                const score = ra.avg_scores?.[cat] ?? 0;
                return (
                  <div key={cat}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                      <span style={{ fontSize: 9, color: C.muted }}>{CAT_ABBR[cat]}</span>
                      <span style={{ fontSize: 9, color: ragDot(score), fontFamily: 'IBM Plex Mono, monospace' }}>{Math.round(score)}</span>
                    </div>
                    <div style={{ height: 3, borderRadius: 2, background: C.border }}>
                      <div style={{ height: '100%', borderRadius: 2, background: ragDot(score), width: `${score}%`, transition: 'width 0.6s' }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Radar comparison */}
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: C.text, marginBottom: 8, fontFamily: 'Space Grotesk, sans-serif' }}>
          Regional Radar Comparison
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <RadarChart data={groupedData} margin={{ top: 10, right: 20, bottom: 10, left: 20 }}>
            <PolarGrid stroke={C.border} />
            <PolarAngleAxis dataKey="subject" tick={{ fill: C.muted, fontSize: 10, fontFamily: 'IBM Plex Sans, sans-serif' }} />
            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: C.muted, fontSize: 9 }} tickCount={5} />
            {regionalAvgs.map((ra) => (
              <Radar
                key={ra.region}
                name={ra.region}
                dataKey={ra.region}
                stroke={REGION_COLORS[ra.region] || C.cyan}
                fill={REGION_COLORS[ra.region] || C.cyan}
                fillOpacity={0.12}
                dot={{ fill: REGION_COLORS[ra.region] || C.cyan, r: 2 }}
              />
            ))}
            <Legend wrapperStyle={{ fontSize: 11, color: C.muted }} />
            <Tooltip
              contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 11 }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ─── Real Reports Tab ──────────────────────────────────────────────────────────

const REG_COLORS = {
  CSRD: '#10b981',
  SFDR: '#38bdf8',
  ISSB: '#a78bfa',
  TCFD: '#fb923c',
  BRSR: '#f472b6',
};

const SECTOR_ICONS = {
  'Banks & Financial Institutions': '🏦',
  'Insurance':                       '🛡',
  'Asset Management':                '📊',
  'Energy & Utilities':              '⚡',
  'Real Estate':                     '🏢',
  'Technology':                      '💻',
  'Other':                           '🏭',
};

function ReportCard({ r }) {
  return (
    <div
      data-testid={`real-report-card-${r.id}`}
      style={{
        background: C.surface,
        border: `1px solid ${C.border}`,
        borderRadius: 12,
        padding: 16,
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text, fontFamily: 'IBM Plex Sans, sans-serif' }}>
            {r.entity_name || r.registry_name}
          </div>
          <div style={{ fontSize: 11, color: C.muted, marginTop: 3 }}>
            {SECTOR_ICONS[r.sector] || '🏭'} {r.sector} · {r.country} · {r.reporting_year}
          </div>
        </div>
        <div style={{
          fontSize: 10, fontWeight: 700, letterSpacing: '0.05em',
          background: `${C.green}18`, color: C.green,
          padding: '3px 8px', borderRadius: 6, whiteSpace: 'nowrap',
        }}>
          {r.report_type || 'Report'}
        </div>
      </div>

      {/* Regulation badges */}
      <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
        {(r.regulations || ['CSRD']).map((reg) => (
          <span
            key={reg}
            style={{
              fontSize: 10, fontWeight: 700, letterSpacing: '0.04em',
              padding: '2px 7px', borderRadius: 4,
              background: `${REG_COLORS[reg] || C.cyan}18`,
              color: REG_COLORS[reg] || C.cyan,
              border: `1px solid ${REG_COLORS[reg] || C.cyan}33`,
            }}
          >
            {reg}
          </span>
        ))}
      </div>

      {/* KPI metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <div style={{ background: `${C.green}10`, borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
          <div style={{ fontSize: 18, fontWeight: 800, fontFamily: 'IBM Plex Mono, monospace', color: C.green }}>
            {r.kpis_extracted ?? '—'}
          </div>
          <div style={{ fontSize: 10, color: C.muted }}>KPIs Extracted</div>
        </div>
        <div style={{ background: `${C.amber}10`, borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
          <div style={{ fontSize: 18, fontWeight: 800, fontFamily: 'IBM Plex Mono, monospace', color: C.amber }}>
            {r.gaps_found ?? '—'}
          </div>
          <div style={{ fontSize: 10, color: C.muted }}>Gaps Found</div>
        </div>
      </div>

      {r.processed_at && (
        <div style={{ fontSize: 10, color: C.muted }}>
          Processed: {new Date(r.processed_at).toLocaleDateString()}
        </div>
      )}
    </div>
  );
}

function FilterChips({ label, options, active, onChange }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
      <span style={{ fontSize: 11, color: C.muted, fontWeight: 600, minWidth: 80 }}>{label}:</span>
      {['All', ...options].map((opt) => (
        <button
          key={opt}
          onClick={() => onChange(opt)}
          style={{
            padding: '4px 12px', borderRadius: 20, border: '1px solid',
            borderColor: active === opt ? C.cyan : C.border,
            background: active === opt ? `${C.cyan}18` : 'transparent',
            color: active === opt ? C.cyan : C.muted,
            fontSize: 11, fontWeight: active === opt ? 700 : 400,
            cursor: 'pointer', transition: 'all 0.15s',
          }}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

function RealReportsTab({ reports }) {
  const [filterReg,    setFilterReg]    = useState('All');
  const [filterSector, setFilterSector] = useState('All');
  const [filterType,   setFilterType]   = useState('All');

  if (!reports) return <Spinner />;

  // Derive unique filter options from data
  const allRegulations = [...new Set(reports.flatMap((r) => r.regulations || ['CSRD']))].sort();
  const allSectors     = [...new Set(reports.map((r) => r.sector).filter(Boolean))].sort();
  const allTypes       = [...new Set(reports.map((r) => r.report_type).filter(Boolean))].sort();

  const filtered = reports.filter((r) => {
    const matchReg    = filterReg    === 'All' || (r.regulations || ['CSRD']).includes(filterReg);
    const matchSector = filterSector === 'All' || r.sector === filterSector;
    const matchType   = filterType   === 'All' || r.report_type === filterType;
    return matchReg && matchSector && matchType;
  });

  // Group by sector for section headers
  const grouped = {};
  filtered.forEach((r) => {
    const s = r.sector || 'Other';
    if (!grouped[s]) grouped[s] = [];
    grouped[s].push(r);
  });

  return (
    <div data-testid="real-reports-tab">
      {/* Summary strip */}
      <div style={{
        display: 'flex', gap: 16, marginBottom: 20, padding: '12px 16px',
        background: C.surface, borderRadius: 10, border: `1px solid ${C.border}`,
        flexWrap: 'wrap',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 20, fontWeight: 800, fontFamily: 'IBM Plex Mono, monospace', color: C.cyan }}>
            {reports.length}
          </div>
          <div style={{ fontSize: 10, color: C.muted }}>Total Reports</div>
        </div>
        <div style={{ width: 1, background: C.border, margin: '0 4px' }} />
        {allRegulations.map((reg) => (
          <div key={reg} style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 20, fontWeight: 800, fontFamily: 'IBM Plex Mono, monospace', color: REG_COLORS[reg] || C.cyan }}>
              {reports.filter((r) => (r.regulations || ['CSRD']).includes(reg)).length}
            </div>
            <div style={{ fontSize: 10, color: C.muted }}>{reg}</div>
          </div>
        ))}
        <div style={{ width: 1, background: C.border, margin: '0 4px' }} />
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 20, fontWeight: 800, fontFamily: 'IBM Plex Mono, monospace', color: C.green }}>
            {reports.reduce((sum, r) => sum + (r.kpis_extracted || 0), 0)}
          </div>
          <div style={{ fontSize: 10, color: C.muted }}>Total KPIs</div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 20, fontWeight: 800, fontFamily: 'IBM Plex Mono, monospace', color: C.amber }}>
            {reports.reduce((sum, r) => sum + (r.gaps_found || 0), 0)}
          </div>
          <div style={{ fontSize: 10, color: C.muted }}>Total Gaps</div>
        </div>
      </div>

      {/* Filters */}
      <div style={{
        display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20,
        padding: '14px 16px', background: C.surface, borderRadius: 10,
        border: `1px solid ${C.border}`,
      }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: C.text, letterSpacing: '0.05em', marginBottom: 4 }}>
          FILTER REPORTS
        </div>
        <FilterChips label="Regulation" options={allRegulations} active={filterReg}    onChange={setFilterReg}    />
        <FilterChips label="Sector"     options={allSectors}     active={filterSector} onChange={setFilterSector} />
        <FilterChips label="Type"       options={allTypes}        active={filterType}   onChange={setFilterType}   />
      </div>

      {/* Results count */}
      <div style={{ fontSize: 12, color: C.muted, marginBottom: 14 }}>
        Showing {filtered.length} of {reports.length} reports
        {filterReg !== 'All' && ` · ${filterReg}`}
        {filterSector !== 'All' && ` · ${filterSector}`}
        {filterType !== 'All' && ` · ${filterType}`}
      </div>

      {/* Cards grouped by sector */}
      {Object.entries(grouped).map(([sector, sectorReports]) => (
        <div key={sector} style={{ marginBottom: 24 }}>
          <div style={{
            fontSize: 12, fontWeight: 700, color: C.muted, letterSpacing: '0.06em',
            textTransform: 'uppercase', marginBottom: 10,
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <span>{SECTOR_ICONS[sector] || '🏭'} {sector}</span>
            <span style={{
              background: `${C.cyan}15`, color: C.cyan, border: `1px solid ${C.cyan}30`,
              padding: '1px 7px', borderRadius: 10, fontSize: 11, fontWeight: 600,
            }}>
              {sectorReports.length}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
            {sectorReports.map((r) => <ReportCard key={r.id} r={r} />)}
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: C.muted }}>
          No reports match the selected filters.
        </div>
      )}

      {reports.length === 0 && (
        <div style={{ textAlign: 'center', padding: 40, color: C.muted }}>
          No processed reports found. Upload reports via the Regulatory module.
        </div>
      )}

      {/* Upload CTA */}
      <div style={{
        marginTop: 24, padding: 16, background: `${C.cyan}08`,
        border: `1px solid ${C.cyan}22`, borderRadius: 12,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: C.text }}>Expand coverage</div>
          <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>
            Upload TCFD, ISSB or CSRD reports for Barclays, JPMorgan, Goldman Sachs,
            Prologis, Vonovia or other peers to enrich analyst estimates with real data.
          </div>
        </div>
        <a
          href="/regulatory"
          style={{
            padding: '8px 16px', borderRadius: 8, background: `${C.cyan}22`,
            border: `1px solid ${C.cyan}55`, color: C.cyan,
            textDecoration: 'none', fontSize: 12, fontWeight: 700, whiteSpace: 'nowrap',
          }}
        >
          Upload Report →
        </a>
      </div>
    </div>
  );
}

// ─── Spinner ──────────────────────────────────────────────────────────────────

function Spinner() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: 60 }}>
      <div style={{
        width: 28, height: 28, border: `3px solid ${C.border}`,
        borderTop: `3px solid ${C.cyan}`, borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); }}`}</style>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function PeerBenchmarkPage() {
  const [activeTab, setActiveTab] = useState('matrix');
  const [heatmap, setHeatmap] = useState(null);
  const [institutions, setInstitutions] = useState([]);
  const [selectedSlug, setSelectedSlug] = useState('ing');
  const [regionalAvgs, setRegionalAvgs] = useState([]);
  const [frameworkCoverage, setFrameworkCoverage] = useState([]);
  const [reports, setReports] = useState(null);
  const [loading, setLoading] = useState(true);
  const [computing, setComputing] = useState(false);
  const [lastComputed, setLastComputed] = useState(null);
  const [filterRegion, setFilterRegion] = useState('All');
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [hmRes, instRes, regRes, covRes, rpRes] = await Promise.all([
        axios.get(`${API}/api/v1/peer-benchmark/heatmap`),
        axios.get(`${API}/api/v1/peer-benchmark/institutions`),
        axios.get(`${API}/api/v1/peer-benchmark/regional-averages`),
        axios.get(`${API}/api/v1/peer-benchmark/framework-coverage`),
        axios.get(`${API}/api/v1/peer-benchmark/processed-reports`),
      ]);
      setHeatmap(hmRes.data);
      setInstitutions(instRes.data.institutions || []);
      setRegionalAvgs(regRes.data.regional_averages || []);
      setFrameworkCoverage(covRes.data.framework_coverage || []);
      setReports(rpRes.data.reports || []);
    } catch (e) {
      setError('Failed to load benchmark data. Ensure the backend is running.');
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleCompute = async () => {
    setComputing(true);
    try {
      const res = await axios.post(`${API}/api/v1/peer-benchmark/compute?reporting_year=2024`);
      setLastComputed(res.data.computed_at);
      // Reload all data to reflect DB-enriched scores
      await loadData();
    } catch (e) {
      console.error('Compute failed', e);
    } finally {
      setComputing(false);
    }
  };

  // Summary stats
  const totalInst = institutions.length;
  const greenCount = institutions.filter((i) => (i.weighted_score || 0) >= 75).length;
  const redCount   = institutions.filter((i) => (i.weighted_score || 0) < 50).length;
  // Use count from /processed-reports endpoint (authoritative DB source) rather than
  // filtering the institutions list, which may undercount if the engine profile is absent.
  const realCount  = reports?.length || 0;

  const TABS = [
    { id: 'matrix',    label: 'Peer Matrix',         badge: totalInst },
    { id: 'profile',   label: 'Institution Profile' },
    { id: 'coverage',  label: 'Framework Coverage' },
    { id: 'regional',  label: 'Regional Benchmarks' },
    { id: 'reports',   label: 'Real Reports',         badge: reports?.length || 0 },
  ];

  return (
    <div style={{ padding: '24px 28px', fontFamily: 'IBM Plex Sans, sans-serif', color: C.text, minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <h1 style={{
            fontSize: 22, fontWeight: 800, fontFamily: 'Space Grotesk, sans-serif',
            color: C.text, margin: 0, marginBottom: 4,
          }}>
            Peer Benchmark Gap Assessment
          </h1>
          <p style={{ margin: 0, fontSize: 13, color: C.muted, maxWidth: 600 }}>
            TCFD · ISSB S1/S2 · ESRS/CSRD · PCAF Financed Emissions · Paris Alignment ·
            TNFD Nature — 12 global financial institutions, 18 framework categories.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          {lastComputed && (
            <span style={{ fontSize: 11, color: C.muted }}>
              Last computed: {new Date(lastComputed).toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={handleCompute}
            disabled={computing || loading}
            data-testid="peer-benchmark-compute-btn"
            style={{
              padding: '8px 16px', borderRadius: 8, border: `1px solid ${C.cyan}66`,
              background: computing ? `${C.cyan}10` : `${C.cyan}1a`,
              color: computing ? C.muted : C.cyan,
              cursor: computing ? 'not-allowed' : 'pointer',
              fontSize: 12, fontWeight: 700, fontFamily: 'IBM Plex Sans, sans-serif',
              transition: 'all 0.15s',
            }}
          >
            {computing ? 'Computing…' : '⟳ Refresh from Reports'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={{ padding: 14, background: `${C.red}12`, border: `1px solid ${C.red}44`, borderRadius: 10, marginBottom: 20, fontSize: 13, color: C.red }}>
          {error}
        </div>
      )}

      {/* KPI summary cards */}
      {!loading && (
        <div style={{ display: 'flex', gap: 14, marginBottom: 24, flexWrap: 'wrap' }}>
          <KpiCard label="Institutions Assessed" value={totalInst} unit="" sub="Global peer group — 10+ sectors" />
          <KpiCard label="Green (≥ 75)" value={greenCount} unit="" sub="Above benchmark threshold" />
          <KpiCard label="Red (< 50)" value={redCount} unit="" sub="Priority improvement needed" />
          <KpiCard label="Framework Categories" value={18} unit="" sub="TCFD · ISSB · ESRS · PCAF" />
          <KpiCard label="Real Reports" value={realCount} unit="" sub="Processed annual reports" />
        </div>
      )}

      {/* Tab bar */}
      <div style={{
        display: 'flex', gap: 4, marginBottom: 20,
        background: C.surface, padding: 4, borderRadius: 10,
        border: `1px solid ${C.border}`, width: 'fit-content',
      }}>
        {TABS.map((t) => (
          <Tab
            key={t.id}
            label={t.label}
            badge={t.badge}
            active={activeTab === t.id}
            onClick={() => setActiveTab(t.id)}
          />
        ))}
      </div>

      {/* Tab content */}
      {loading ? (
        <Spinner />
      ) : (
        <div data-testid={`peer-benchmark-tab-${activeTab}`}>
          {activeTab === 'matrix' && (
            <HeatmapTab
              heatmap={heatmap}
              filterRegion={filterRegion}
              setFilterRegion={setFilterRegion}
            />
          )}
          {activeTab === 'profile' && (
            <ProfileTab
              institutions={institutions}
              selectedSlug={selectedSlug}
              setSelectedSlug={setSelectedSlug}
            />
          )}
          {activeTab === 'coverage' && (
            <CoverageTab
              frameworkCoverage={frameworkCoverage}
              institutions={institutions}
            />
          )}
          {activeTab === 'regional' && (
            <RegionalTab regionalAvgs={regionalAvgs} />
          )}
          {activeTab === 'reports' && (
            <RealReportsTab reports={reports} />
          )}
        </div>
      )}
    </div>
  );
}
