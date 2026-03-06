/**
 * ScenarioVersionTimeline — version history with diff indicators and restore.
 * Shows each saved snapshot with date, author, summary, and modified parameters.
 */
import React, { useState } from 'react';
import { ALL_PARAMETERS } from '../data/ngfsData';

// ─── Version diff ─────────────────────────────────────────────────────────────

function computeDiff(current, previous) {
  if (!current || !previous) return [];
  const diffs = [];
  current.forEach(cp => {
    const pp = previous.find(p => p.id === cp.id);
    if (!pp) return;
    if (Math.abs(cp.value - pp.value) > 0.001) {
      diffs.push({ id: cp.id, label: cp.label, from: pp.value, to: cp.value, unit: cp.unit });
    }
  });
  return diffs;
}

// ─── Single version entry ────────────────────────────────────────────────────

function VersionEntry({ version, previous, isLatest, isFirst, onRestore, showDiff }) {
  const [expanded, setExpanded] = useState(false);
  const diffs = showDiff ? computeDiff(version.parameters, previous?.parameters) : [];

  return (
    <div className={`relative flex gap-3 ${isFirst ? '' : 'pt-4'}`} data-testid={`version-${version.id}`}>
      {/* Timeline spine */}
      {!isFirst && (
        <div className="absolute left-[13px] top-0 bottom-0 w-px bg-white/8" />
      )}

      {/* Dot */}
      <div className={`relative z-10 w-7 h-7 rounded-full border flex items-center justify-center shrink-0 ${
        isLatest
          ? 'bg-cyan-500/20 border-cyan-500/40 shadow-[0_0_8px_rgba(34,211,238,0.2)]'
          : 'bg-white/5 border-white/15'
      }`}>
        {isLatest ? (
          <div className="w-2 h-2 rounded-full bg-cyan-400" />
        ) : (
          <span className="text-[9px] font-bold text-white/30">{version.version}</span>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 pb-1">
        <div className="flex items-center justify-between gap-2 mb-0.5">
          <span className="text-[12px] font-semibold text-white/85">{version.label}</span>
          {isLatest && (
            <span className="text-[9px] font-bold text-cyan-400/80 bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/20">
              CURRENT
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-[10px] text-white/30 mb-1">
          <span>{version.changedBy}</span>
          <span>·</span>
          <span>{formatDate(version.changedAt)}</span>
          {diffs.length > 0 && (
            <>
              <span>·</span>
              <button
                onClick={() => setExpanded(v => !v)}
                className="text-amber-400/70 hover:text-amber-400 transition-colors"
              >
                {diffs.length} change{diffs.length !== 1 ? 's' : ''}
              </button>
            </>
          )}
        </div>

        {version.summary && (
          <p className="text-[11px] text-white/45 leading-snug mb-1">{version.summary}</p>
        )}

        {/* Parameter diffs */}
        {expanded && diffs.length > 0 && (
          <div className="mt-1.5 space-y-1">
            {diffs.map(d => (
              <div key={d.id} className="flex items-center gap-2 text-[10px] bg-white/3 rounded px-2 py-1">
                <span className="text-white/50 flex-1">{d.label}</span>
                <span className="text-white/30 line-through">{d.from?.toFixed(2)}</span>
                <svg className="h-2.5 w-2.5 text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                </svg>
                <span className="text-amber-400/80 font-semibold">{d.to?.toFixed(2)}</span>
                <span className="text-white/25">{d.unit}</span>
              </div>
            ))}
          </div>
        )}

        {/* Restore button (not for latest) */}
        {!isLatest && onRestore && (
          <button
            onClick={() => onRestore(version.id)}
            className="mt-1.5 text-[10px] text-white/30 hover:text-white/60 flex items-center gap-1 transition-colors"
          >
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            Restore this version
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Main component ────────────────────────────────────────────────────────────

export function ScenarioVersionTimeline({ scenario, onRestoreVersion }) {
  const versions = [...(scenario.versions || [])].reverse(); // newest first

  if (!versions.length) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-white/20 text-sm gap-2"
           data-testid="version-timeline-empty">
        <svg className="h-8 w-8 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-[12px]">No saved versions yet</p>
        <p className="text-[10px]">Save a draft to create version 1</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-0" data-testid="scenario-version-timeline">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-[12px] font-semibold text-white/70">Version History</h4>
        <span className="text-[10px] text-white/30">{versions.length} snapshot{versions.length !== 1 ? 's' : ''}</span>
      </div>

      <div className="space-y-0">
        {versions.map((v, idx) => {
          const prevV = idx < versions.length - 1 ? versions[idx + 1] : null;
          return (
            <VersionEntry
              key={v.id}
              version={v}
              previous={prevV}
              isLatest={idx === 0}
              isFirst={idx === 0}
              onRestore={onRestoreVersion}
              showDiff
            />
          );
        })}
      </div>
    </div>
  );
}

export default ScenarioVersionTimeline;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatDate(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
}
