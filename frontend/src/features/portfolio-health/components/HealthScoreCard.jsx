/**
 * HealthScoreCard
 *
 * Displays a single health score (0–100) as a circular SVG arc gauge,
 * colour-coded by RAG status, with label and action prompt below.
 *
 * Props:
 *   title          string   e.g. "Climate Health"
 *   score          number   0–100
 *   rag            string   "GREEN" | "AMBER" | "RED"
 *   label          string   one-line status description
 *   action         string   actionable next step
 *   actionLink     string   route to navigate to
 *   loading        bool     show skeleton
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';

const RAG_COLOURS = {
  GREEN: { stroke: '#10b981', text: '#10b981', bg: 'rgba(16,185,129,0.08)' },
  AMBER: { stroke: '#f59e0b', text: '#f59e0b', bg: 'rgba(245,158,11,0.08)' },
  RED:   { stroke: '#ef4444', text: '#ef4444', bg: 'rgba(239,68,68,0.08)' },
};

const RAG_LABELS = { GREEN: 'On Track', AMBER: 'Caution', RED: 'At Risk' };

// SVG arc gauge params
const R   = 42;   // circle radius
const CX  = 56;   // centre X
const CY  = 56;   // centre Y
const CIRCUMFERENCE = 2 * Math.PI * R;

export function HealthScoreCard({
  title,
  score = 50,
  rag = 'AMBER',
  label = '',
  action = '',
  actionLink = '/',
  loading = false,
}) {
  const navigate = useNavigate();
  const colours = RAG_COLOURS[rag] || RAG_COLOURS.AMBER;

  // Arc covers 270° (from 225° to 135° going clockwise — bottom-left to bottom-right)
  const ARC_DEGREES = 270;
  const startAngle  = 135;          // degrees from 12 o'clock, clockwise
  const progress    = Math.min(Math.max(score / 100, 0), 1);
  const dashArc     = (ARC_DEGREES / 360) * CIRCUMFERENCE;
  const dashFilled  = progress * dashArc;
  const dashGap     = CIRCUMFERENCE - dashFilled;

  // Convert start angle to SVG coordinates (SVG 0° = 3 o'clock, counter-clockwise via transform)
  const svgStartAngle = startAngle - 90;  // shift so 0° = 12 o'clock

  if (loading) {
    return (
      <div className="flex flex-col items-center p-6 rounded-xl border border-white/10 bg-white/[0.02] animate-pulse">
        <div className="w-28 h-28 rounded-full bg-white/10 mb-4" />
        <div className="h-4 w-28 bg-white/10 rounded mb-2" />
        <div className="h-3 w-36 bg-white/10 rounded" />
      </div>
    );
  }

  return (
    <div
      className="flex flex-col items-center p-6 rounded-xl border border-white/10 transition-all duration-200"
      style={{ background: colours.bg }}
      data-testid={`health-score-card-${title?.toLowerCase().replace(/\s+/g, '-')}`}
    >
      {/* Title */}
      <div className="text-xs font-semibold uppercase tracking-wider text-white/50 mb-4">
        {title}
      </div>

      {/* SVG gauge */}
      <div className="relative mb-3">
        <svg width="112" height="112" viewBox="0 0 112 112">
          {/* Background track */}
          <circle
            cx={CX} cy={CY} r={R}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="8"
            strokeDasharray={`${dashArc} ${CIRCUMFERENCE - dashArc}`}
            strokeDashoffset={0}
            strokeLinecap="round"
            transform={`rotate(${svgStartAngle} ${CX} ${CY})`}
          />
          {/* Filled arc */}
          <circle
            cx={CX} cy={CY} r={R}
            fill="none"
            stroke={colours.stroke}
            strokeWidth="8"
            strokeDasharray={`${dashFilled} ${dashGap + (CIRCUMFERENCE - dashArc)}`}
            strokeDashoffset={0}
            strokeLinecap="round"
            transform={`rotate(${svgStartAngle} ${CX} ${CY})`}
            style={{ transition: 'stroke-dasharray 0.6s ease-in-out' }}
          />
        </svg>

        {/* Score number in centre */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-display text-3xl font-bold tabular-nums leading-none"
            style={{ color: colours.text, fontFamily: "'Space Grotesk', sans-serif" }}
            data-testid={`health-score-value-${title?.toLowerCase().replace(/\s+/g, '-')}`}
          >
            {Math.round(score)}
          </span>
          <span className="text-[10px] text-white/30 mt-0.5">/100</span>
        </div>
      </div>

      {/* RAG badge */}
      <div
        className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider mb-3"
        style={{ color: colours.text, border: `1px solid ${colours.stroke}` }}
      >
        {RAG_LABELS[rag] || rag}
      </div>

      {/* Status label */}
      <p className="text-xs text-white/60 text-center leading-snug mb-3 px-2">
        {label}
      </p>

      {/* Action link */}
      {action && (
        <button
          onClick={() => navigate(actionLink)}
          className="text-[11px] font-medium underline underline-offset-2 transition-opacity hover:opacity-80"
          style={{ color: colours.text }}
          data-testid={`health-score-action-${title?.toLowerCase().replace(/\s+/g, '-')}`}
        >
          {action} →
        </button>
      )}
    </div>
  );
}
