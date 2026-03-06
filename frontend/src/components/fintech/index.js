/**
 * Fintech Analytics UI Component Library
 * Dark-mode, investor-grade components used across all feature pages.
 */
import React from 'react';

// ─── Colour palette constants ─────────────────────────────────────────────────

export const CHART_COLORS = {
  cyan:    '#22d3ee',
  blue:    '#3b82f6',
  indigo:  '#6366f1',
  violet:  '#8b5cf6',
  green:   '#10b981',
  amber:   '#f59e0b',
  red:     '#ef4444',
  rose:    '#f43f5e',
  teal:    '#14b8a6',
  sky:     '#0ea5e9',
  lime:    '#84cc16',
  orange:  '#f97316',
};

export const SCENARIO_PALETTE = {
  'Net Zero 2050':      '#10b981',
  'Below 2°C':          '#22d3ee',
  'Delayed Transition': '#f59e0b',
  'Hot House World':    '#ef4444',
  'NDCs':               '#8b5cf6',
  'Orderly':            '#10b981',
  'Disorderly':         '#f59e0b',
  'Hot house world':    '#ef4444',
};

export const SECTOR_PALETTE = {
  'Power Generation': '#6366f1',
  'Oil & Gas':        '#f59e0b',
  'Metals & Mining':  '#8b5cf6',
  'Automotive':       '#3b82f6',
  'Airlines':         '#ec4899',
  'Real Estate':      '#14b8a6',
  'Technology':       '#22d3ee',
  'Agriculture':      '#84cc16',
  'Finance':          '#f97316',
};

// ─── Number formatters ────────────────────────────────────────────────────────

export const fmt = {
  currency:  (v, digits = 1) => {
    if (v == null || isNaN(v)) return '—';
    const abs = Math.abs(v);
    const sign = v < 0 ? '-' : '';
    if (abs >= 1e12) return `${sign}$${(abs / 1e12).toFixed(digits)}T`;
    if (abs >= 1e9)  return `${sign}$${(abs / 1e9).toFixed(digits)}B`;
    if (abs >= 1e6)  return `${sign}$${(abs / 1e6).toFixed(digits)}M`;
    if (abs >= 1e3)  return `${sign}$${(abs / 1e3).toFixed(0)}K`;
    return `${sign}$${abs.toFixed(digits)}`;
  },
  pct:       (v, d = 2) => v == null ? '—' : `${(v * 100).toFixed(d)}%`,
  pctRaw:    (v, d = 1) => v == null ? '—' : `${v.toFixed(d)}%`,
  num:       (v, d = 1) => v == null ? '—' : v.toFixed(d),
  bps:       (v)        => v == null ? '—' : `${(v * 10000).toFixed(0)} bps`,
  tCO2:      (v, d = 1) => v == null ? '—' : `${(v / 1e3).toFixed(d)}kt CO₂e`,
  tCO2full:  (v)        => v == null ? '—' : `${v.toLocaleString()} tCO₂e`,
  year:      (v)        => v == null ? '—' : String(Math.round(v)),
  int:       (v)        => v == null ? '—' : Math.round(v).toLocaleString(),
};

// ─── Page wrapper ─────────────────────────────────────────────────────────────

export function PageShell({ title, subtitle, badge, actions, children }) {
  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Page header */}
      <div className="px-6 py-4 border-b border-white/[0.06] bg-[#070d1a] shrink-0">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <h1 className="text-sm font-semibold text-white/90">{title}</h1>
              {badge && (
                <span className="text-[9px] font-mono font-bold text-cyan-400/70 bg-cyan-400/10 border border-cyan-400/20 px-1.5 py-0.5 rounded uppercase tracking-wide">
                  {badge}
                </span>
              )}
            </div>
            {subtitle && <p className="text-[11px] text-white/35">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
        </div>
      </div>
      {/* Content */}
      <div className="flex-1 overflow-auto p-6 space-y-5">
        {children}
      </div>
    </div>
  );
}

// ─── KPI card ─────────────────────────────────────────────────────────────────

export function KpiCard({ label, value, sub, delta, deltaLabel, color = 'cyan', icon, loading, size = 'md' }) {
  const accentMap = {
    cyan:   { border: 'border-cyan-500/20',   icon: 'text-cyan-400',    bg: 'bg-cyan-400/8' },
    green:  { border: 'border-emerald-500/20', icon: 'text-emerald-400', bg: 'bg-emerald-400/8' },
    amber:  { border: 'border-amber-500/20',   icon: 'text-amber-400',  bg: 'bg-amber-400/8' },
    red:    { border: 'border-red-500/20',     icon: 'text-red-400',    bg: 'bg-red-400/8' },
    violet: { border: 'border-violet-500/20',  icon: 'text-violet-400', bg: 'bg-violet-400/8' },
    blue:   { border: 'border-blue-500/20',    icon: 'text-blue-400',   bg: 'bg-blue-400/8' },
  };
  const a = accentMap[color] || accentMap.cyan;
  const valueSize = size === 'lg' ? 'text-3xl' : 'text-xl';

  return (
    <div className={`bg-[#0d1424] border ${a.border} rounded-lg p-4 flex flex-col gap-2`}>
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold text-white/40 uppercase tracking-[0.1em]">{label}</span>
        {icon && (
          <div className={`${a.bg} ${a.icon} rounded p-1.5`}>
            {icon}
          </div>
        )}
      </div>
      {loading ? (
        <div className="h-7 w-28 bg-white/5 rounded animate-pulse" />
      ) : (
        <span className={`${valueSize} font-bold text-white mono-num leading-none`}>{value}</span>
      )}
      <div className="flex items-center gap-2">
        {delta != null && (
          <span className={`text-[10px] font-mono font-semibold px-1 py-0.5 rounded ${
            delta > 0 ? 'text-red-400 bg-red-400/10' :
            delta < 0 ? 'text-emerald-400 bg-emerald-400/10' :
                        'text-white/30 bg-white/5'
          }`}>
            {delta > 0 ? '+' : ''}{delta.toFixed(1)}%
          </span>
        )}
        {sub && <span className="text-[10px] text-white/30">{sub}</span>}
        {deltaLabel && <span className="text-[10px] text-white/25">{deltaLabel}</span>}
      </div>
    </div>
  );
}

// ─── Section card ─────────────────────────────────────────────────────────────

export function Section({ title, subtitle, actions, children, className = '' }) {
  return (
    <div className={`bg-[#0d1424] border border-white/[0.06] rounded-lg overflow-hidden ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.05]">
          <div>
            <p className="text-xs font-semibold text-white/80">{title}</p>
            {subtitle && <p className="text-[10px] text-white/35 mt-0.5">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}

// ─── Data table ───────────────────────────────────────────────────────────────

export function DataTable({ columns, rows, loading, emptyText = 'No data', maxRows }) {
  const data = maxRows ? rows?.slice(0, maxRows) : rows;
  return (
    <div className="overflow-auto">
      <table className="w-full text-[11px]">
        <thead>
          <tr className="border-b border-white/[0.06]">
            {columns.map(col => (
              <th
                key={col.key}
                className={`pb-2 text-[9px] font-semibold text-white/30 uppercase tracking-[0.1em] whitespace-nowrap ${
                  col.align === 'right' ? 'text-right pr-3' : col.align === 'center' ? 'text-center' : 'text-left pl-0'
                }`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: 5 }).map((_, i) => (
              <tr key={i} className="border-b border-white/[0.03]">
                {columns.map(col => (
                  <td key={col.key} className="py-2 pr-3">
                    <div className="h-3 bg-white/5 rounded animate-pulse" style={{ width: `${40 + Math.random() * 50}%` }} />
                  </td>
                ))}
              </tr>
            ))
          ) : data?.length ? (
            data.map((row, ri) => (
              <tr key={ri} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                {columns.map(col => (
                  <td
                    key={col.key}
                    className={`py-2 whitespace-nowrap ${
                      col.align === 'right' ? 'text-right pr-3 mono-num text-white/70' :
                      col.align === 'center' ? 'text-center text-white/70' :
                      'text-left text-white/70'
                    }`}
                  >
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length} className="py-8 text-center text-white/25">{emptyText}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

// ─── Status badge ─────────────────────────────────────────────────────────────

export function StatusBadge({ value, labels = {} }) {
  const map = {
    high:      'text-red-400 bg-red-400/10 border-red-400/20',
    medium:    'text-amber-400 bg-amber-400/10 border-amber-400/20',
    low:       'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    critical:  'text-rose-400 bg-rose-400/10 border-rose-400/20',
    pass:      'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    fail:      'text-red-400 bg-red-400/10 border-red-400/20',
    aligned:   'text-cyan-400 bg-cyan-400/10 border-cyan-400/20',
    partial:   'text-amber-400 bg-amber-400/10 border-amber-400/20',
    not_aligned:'text-red-400 bg-red-400/10 border-red-400/20',
    completed: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    pending:   'text-amber-400 bg-amber-400/10 border-amber-400/20',
    running:   'text-cyan-400 bg-cyan-400/10 border-cyan-400/20',
    error:     'text-red-400 bg-red-400/10 border-red-400/20',
  };
  const key = (value || '').toLowerCase().replace(' ', '_');
  const cls = map[key] || 'text-white/40 bg-white/5 border-white/10';
  const label = labels[key] || value;
  return (
    <span className={`inline-flex items-center text-[9px] font-mono font-bold uppercase tracking-wide border px-1.5 py-0.5 rounded ${cls}`}>
      {label}
    </span>
  );
}

// ─── Risk gauge bar ───────────────────────────────────────────────────────────

export function RiskBar({ value, max = 100, label, colorFn }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const color = colorFn
    ? colorFn(pct)
    : pct < 33 ? '#10b981' : pct < 66 ? '#f59e0b' : '#ef4444';
  return (
    <div className="space-y-1">
      <div className="flex justify-between items-center">
        <span className="text-[10px] text-white/50">{label}</span>
        <span className="text-[10px] font-mono text-white/70">{value.toFixed(1)}</span>
      </div>
      <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

// ─── Tab bar (lightweight, no Radix) ─────────────────────────────────────────

export function TabBar({ tabs, active, onChange }) {
  return (
    <div className="flex items-center gap-0.5 border-b border-white/[0.06] px-4">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-3 py-2.5 text-[11px] font-medium border-b-2 transition-colors whitespace-nowrap ${
            active === tab.id
              ? 'border-cyan-400 text-cyan-300'
              : 'border-transparent text-white/40 hover:text-white/70'
          }`}
        >
          {tab.label}
          {tab.count != null && (
            <span className="ml-1.5 text-[9px] font-mono text-white/25">{tab.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}

// ─── Action button ────────────────────────────────────────────────────────────

export function ActionButton({ onClick, disabled, loading, variant = 'primary', size = 'sm', children }) {
  const variants = {
    primary: 'bg-cyan-500/20 border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/30',
    ghost:   'bg-transparent border-white/10 text-white/50 hover:bg-white/5 hover:text-white/80',
    danger:  'bg-red-500/15 border-red-500/25 text-red-400 hover:bg-red-500/25',
    success: 'bg-emerald-500/15 border-emerald-500/25 text-emerald-400 hover:bg-emerald-500/25',
  };
  const sizes = {
    xs: 'text-[10px] px-2 py-1',
    sm: 'text-[11px] px-3 py-1.5',
    md: 'text-xs px-4 py-2',
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`flex items-center gap-1.5 font-medium border rounded transition-all ${variants[variant]} ${sizes[size]} disabled:opacity-40 disabled:cursor-not-allowed`}
    >
      {loading && (
        <svg className="h-3 w-3 animate-spin" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </button>
  );
}

// ─── Validation panel ─────────────────────────────────────────────────────────

export function ValidationPanel({ checks }) {
  const passed = checks.filter(c => c.pass).length;
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[10px] text-white/40">Compliance</span>
        <span className="text-[10px] font-mono font-bold text-white/60">{passed}/{checks.length}</span>
        <div className="flex-1 h-1 bg-white/[0.06] rounded-full overflow-hidden">
          <div
            className="h-full bg-cyan-400 rounded-full transition-all"
            style={{ width: `${(passed / checks.length) * 100}%` }}
          />
        </div>
      </div>
      {checks.map((c, i) => (
        <div key={i} className="flex items-start gap-2.5">
          <div className={`mt-0.5 flex-shrink-0 w-3.5 h-3.5 rounded-full flex items-center justify-center ${
            c.pass ? 'bg-emerald-400/15 text-emerald-400' : 'bg-red-400/15 text-red-400'
          }`}>
            <svg className="w-2 h-2" fill="currentColor" viewBox="0 0 24 24">
              {c.pass
                ? <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" />
                : <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
              }
            </svg>
          </div>
          <div>
            <p className="text-[10px] font-medium text-white/70">{c.label}</p>
            {c.detail && <p className="text-[9px] text-white/30 mt-0.5">{c.detail}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Tooltip custom ───────────────────────────────────────────────────────────

export function ChartTooltip({ active, payload, label, formatter }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0d1424] border border-white/10 rounded-lg p-3 shadow-xl text-[11px] min-w-[140px]">
      {label && <p className="text-white/50 text-[10px] mb-2 font-mono">{label}</p>}
      {payload.map((p, i) => (
        <div key={i} className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
            <span className="text-white/60">{p.name}</span>
          </div>
          <span className="text-white/90 font-mono font-semibold">
            {formatter ? formatter(p.value, p.name) : p.value}
          </span>
        </div>
      ))}
    </div>
  );
}

export const CHART_AXIS_STYLE = {
  tick:  { fill: 'rgba(255,255,255,0.3)', fontSize: 10, fontFamily: 'IBM Plex Mono, monospace' },
  axisLine: false,
  tickLine: false,
};

export const CHART_GRID_STYLE = {
  strokeDasharray: '3 3',
  stroke: 'rgba(255,255,255,0.05)',
  vertical: false,
};
