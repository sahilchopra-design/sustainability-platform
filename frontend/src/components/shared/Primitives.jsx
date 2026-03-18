/**
 * Shared UI Primitives — used across all feature pages
 * Professional finance-app styling with readable contrast
 */
import React, { useState } from "react";
import { ChevronDown, ChevronUp, RefreshCw } from "lucide-react";

/* ── Deterministic seeded random ─────────────────────────────────────── */
export function sr(seed) {
  let s = seed;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

/* ── Tooltip style for Recharts ──────────────────────────────────────── */
export const TOOLTIP_STYLE = {
  backgroundColor: "#fff",
  border: "1px solid #E5E7EB",
  borderRadius: "6px",
  color: "#1F2937",
  fontSize: "12px",
  boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
};

/* ── Chart color palette ─────────────────────────────────────────────── */
export const CHART_COLORS = [
  "#2563EB", // blue
  "#059669", // emerald
  "#D97706", // amber
  "#DC2626", // red
  "#7C3AED", // violet
  "#0891B2", // cyan
  "#C026D3", // fuchsia
  "#65A30D", // lime
];

/* ── Section — collapsible card ──────────────────────────────────────── */
export function Section({ title, children, defaultOpen = true, icon: Icon }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden mb-4 bg-white shadow-sm">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-4 w-4 text-gray-500" />}
          <span className="font-semibold text-sm text-gray-800">{title}</span>
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 text-gray-400" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-400" />
        )}
      </button>
      {open && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
}

/* ── KPI Card ────────────────────────────────────────────────────────── */
export function KpiCard({ label, value, sub, color, trend }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <p className="text-[11px] text-gray-500 uppercase tracking-wider font-medium mb-1.5">
        {label}
      </p>
      <p className={`text-xl font-bold font-mono tabular-nums ${color || "text-gray-900"}`}>
        {value}
      </p>
      {sub && (
        <p className="text-[11px] text-gray-500 mt-1">{sub}</p>
      )}
      {trend !== undefined && (
        <span className={`text-[11px] font-mono font-semibold mt-1 inline-block ${
          trend > 0 ? "text-emerald-600" : trend < 0 ? "text-red-600" : "text-gray-500"
        }`}>
          {trend > 0 ? "+" : ""}{trend}%
        </span>
      )}
    </div>
  );
}

/* ── Form Row ────────────────────────────────────────────────────────── */
export function Row({ label, children }) {
  return (
    <div className="flex items-center gap-3 mb-2.5">
      <label className="text-[12px] text-gray-600 w-44 shrink-0 font-medium">
        {label}
      </label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

/* ── Text Input ──────────────────────────────────────────────────────── */
export function Inp({ value, onChange, type = "text", placeholder }) {
  return (
    <input
      type={type}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full bg-white border border-gray-300 rounded-md px-3 py-2 text-sm text-gray-800
        placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500
        transition-colors"
    />
  );
}

/* ── Select ──────────────────────────────────────────────────────────── */
export function Sel({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full bg-white border border-gray-300 rounded-md px-3 py-2 text-sm text-gray-800
        focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
    >
      {options.map((o) => (
        <option key={o.v} value={o.v}>
          {o.l}
        </option>
      ))}
    </select>
  );
}

/* ── Button ──────────────────────────────────────────────────────────── */
export function Btn({ onClick, disabled, loading, children, variant = "primary" }) {
  const base = "inline-flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all disabled:opacity-50";
  const variants = {
    primary: `${base} bg-[#164E8A] text-white hover:bg-[#12407A] shadow-sm`,
    secondary: `${base} bg-white text-gray-700 border border-gray-300 hover:bg-gray-50`,
    danger: `${base} bg-red-600 text-white hover:bg-red-700 shadow-sm`,
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={variants[variant] || variants.primary}
    >
      {loading && <RefreshCw className="h-3.5 w-3.5 animate-spin" />}
      {children}
    </button>
  );
}

/* ── Status Badge ────────────────────────────────────────────────────── */
export function StatusBadge({ status, label }) {
  const styles = {
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    danger: "bg-red-50 text-red-700 border-red-200",
    info: "bg-blue-50 text-blue-700 border-blue-200",
    neutral: "bg-gray-100 text-gray-600 border-gray-200",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full border text-[11px] font-semibold ${
      styles[status] || styles.neutral
    }`}>
      {label}
    </span>
  );
}

/* ── Score Ring ───────────────────────────────────────────────────────── */
export function ScoreRing({ score, size = 48, label }) {
  const r = (size - 6) / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.min(Math.max(score, 0), 100);
  const offset = circ * (1 - pct / 100);
  const color = pct >= 75 ? "#059669" : pct >= 50 ? "#D97706" : "#DC2626";
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#E5E7EB" strokeWidth={4} />
        <circle
          cx={size / 2} cy={size / 2} r={r} fill="none"
          stroke={color} strokeWidth={4} strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
        />
      </svg>
      <span className="text-xs font-bold text-gray-800">{score}%</span>
      {label && <span className="text-[10px] text-gray-500">{label}</span>}
    </div>
  );
}

/* ── Tab Bar ─────────────────────────────────────────────────────────── */
export function TabBar({ tabs, active, onChange }) {
  return (
    <div className="flex border-b border-gray-200 mb-4 overflow-x-auto">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-all ${
            active === tab.key
              ? "text-[#164E8A] border-[#164E8A]"
              : "text-gray-500 border-transparent hover:text-gray-800 hover:border-gray-300"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

/* ── Data Table ──────────────────────────────────────────────────────── */
export function DataTable({ columns, rows }) {
  return (
    <div className="overflow-x-auto border border-gray-200 rounded-lg">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            {columns.map((col) => (
              <th key={col.key} className="px-3 py-2.5 text-left text-[11px] font-semibold text-gray-600 uppercase tracking-wider">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-gray-100 hover:bg-gray-50/50 transition-colors">
              {columns.map((col) => (
                <td key={col.key} className="px-3 py-2.5 text-gray-700 font-mono tabular-nums text-[13px]">
                  {col.render ? col.render(row[col.key], row) : row[col.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ── Page Header ─────────────────────────────────────────────────────── */
export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">{title}</h1>
        {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </div>
  );
}
