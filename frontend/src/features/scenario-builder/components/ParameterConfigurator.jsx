/**
 * ParameterConfigurator — organized parameter groups with sliders and value inputs.
 * Groups: Carbon, Macro, Physical, Transition, Financial.
 * Shows baseline vs adjusted value; supports reset per parameter.
 */
import React, { useState, useCallback } from 'react';
import { PARAMETER_GROUPS, NGFS_FAMILY_META } from '../data/ngfsData';

// ─── Icons ─────────────────────────────────────────────────────────────────────

const GROUP_ICONS = {
  carbon:     'M11 20A7 7 0 019.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10z',
  macro:      'M23 6l-9.5 9.5-5-5L1 18M17 6h6v6',
  physical:   'M14 14.76V3.5a2.5 2.5 0 00-5 0v11.26a4.5 4.5 0 105 0z',
  transition: 'M13 10V3L4 14h7v7l9-11h-7z',
  financial:  'M12 2v20M17 5H9.5a3.5 3.5 0 100 7h5a3.5 3.5 0 110 7H6',
};

// ─── Single parameter row ────────────────────────────────────────────────────

function ParameterRow({ param, ngfsFamily, onChangeValue, onReset }) {
  const ngfsTarget = param.trajectories?.[ngfsFamily]?.[2050] ?? param.baseline;
  const delta      = param.value - ngfsTarget;
  const pctDelta   = ngfsTarget !== 0 ? (delta / Math.abs(ngfsTarget)) * 100 : 0;
  const isModified = Math.abs(delta) > 0.001;

  const handleSlider = useCallback((e) => {
    onChangeValue(param.id, parseFloat(e.target.value));
  }, [param.id, onChangeValue]);

  const handleInput = useCallback((e) => {
    const v = parseFloat(e.target.value);
    if (!isNaN(v)) onChangeValue(param.id, v);
  }, [param.id, onChangeValue]);

  return (
    <div className="group" data-testid={`param-row-${param.id}`}>
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-[12px] font-medium text-gray-800 truncate">{param.label}</span>
          {isModified && (
            <span className={`text-[9px] font-semibold px-1 py-0.5 rounded ${
              delta > 0
                ? 'text-amber-400 bg-amber-500/10'
                : 'text-emerald-400 bg-emerald-500/10'
            }`}>
              {delta > 0 ? '+' : ''}{pctDelta.toFixed(1)}%
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {/* Numeric input */}
          <input
            type="number"
            value={param.value}
            min={param.min}
            max={param.max}
            step={param.step}
            onChange={handleInput}
            className="w-20 text-right text-[11px] bg-gray-50 border border-black/10 rounded px-1.5 py-0.5 text-gray-800 focus:outline-none focus:border-blue-500"
          />
          <span className="text-[10px] text-gray-500 min-w-[32px]">{param.unit}</span>

          {/* Reset */}
          {isModified && (
            <button
              onClick={() => onReset(param.id)}
              title="Reset to NGFS baseline"
              className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-500 hover:text-gray-700 p-0.5 rounded"
            >
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Slider */}
      <div className="relative mb-1">
        {/* NGFS target marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-gray-400 rounded pointer-events-none"
          style={{
            left: `${((ngfsTarget - param.min) / (param.max - param.min)) * 100}%`,
          }}
        />
        <input
          type="range"
          min={param.min}
          max={param.max}
          step={param.step}
          value={param.value}
          onChange={handleSlider}
          className="w-full h-1 appearance-none rounded cursor-pointer
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:w-3
            [&::-webkit-slider-thumb]:h-3
            [&::-webkit-slider-thumb]:rounded-full
            [&::-webkit-slider-thumb]:bg-[#164E8A]
            [&::-webkit-slider-thumb]:shadow-[0_0_4px_rgba(34,211,238,0.6)]"
          style={{
            background: `linear-gradient(to right, rgba(34,211,238,0.5) 0%, rgba(34,211,238,0.5) ${
              ((param.value - param.min) / (param.max - param.min)) * 100
            }%, rgba(255,255,255,0.06) ${
              ((param.value - param.min) / (param.max - param.min)) * 100
            }%, rgba(255,255,255,0.06) 100%)`,
          }}
        />
      </div>

      {/* Range labels + NGFS reference */}
      <div className="flex items-center justify-between text-[9px] text-gray-400 mb-0.5">
        <span>{param.min} {param.unit}</span>
        <span className="text-gray-500">NGFS {ngfsFamily}: {ngfsTarget}</span>
        <span>{param.max} {param.unit}</span>
      </div>

      {/* Description (tooltip on hover) */}
      {param.description && (
        <p className="text-[10px] text-gray-400 leading-relaxed hidden group-hover:block transition-all">
          {param.description}
        </p>
      )}
    </div>
  );
}

// ─── Group accordion ──────────────────────────────────────────────────────────

function ParameterGroup({ group, parameters, ngfsFamily, onChangeValue, onReset }) {
  const [expanded, setExpanded] = useState(true);
  const iconPath = GROUP_ICONS[group.id] || GROUP_ICONS.macro;

  const hasModified = parameters.some(p => {
    const target = p.trajectories?.[ngfsFamily]?.[2050] ?? p.baseline;
    return Math.abs(p.value - target) > 0.001;
  });

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden mb-2" data-testid={`param-group-${group.id}`}>
      {/* Group header */}
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full flex items-center justify-between px-3.5 py-2.5 bg-gray-50 hover:bg-white/[0.05] transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg className="h-3.5 w-3.5 shrink-0" style={{ color: group.color }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round" d={iconPath} />
          </svg>
          <span className="text-[12px] font-semibold text-gray-800">{group.label}</span>
          {hasModified && (
            <span className="text-[9px] text-amber-400/70 bg-amber-500/10 px-1.5 py-0.5 rounded">
              Modified
            </span>
          )}
        </div>
        <svg
          className={`h-3.5 w-3.5 text-gray-500 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Parameters */}
      {expanded && (
        <div className="px-3.5 py-3 space-y-4 bg-white/60">
          {parameters.map(param => (
            <ParameterRow
              key={param.id}
              param={param}
              ngfsFamily={ngfsFamily}
              onChangeValue={onChangeValue}
              onReset={onReset}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main component ────────────────────────────────────────────────────────────

export function ParameterConfigurator({ scenario, onChangeValue, onReset, onChangeFamily, onChangeHorizon }) {
  const familyMeta = NGFS_FAMILY_META[scenario.ngfsFamily] || {};

  return (
    <div className="flex flex-col h-full" data-testid="parameter-configurator">
      {/* Controls row */}
      <div className="flex flex-wrap items-center gap-2 mb-4 pb-3 border-b border-gray-200">
        {/* NGFS Family */}
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] text-gray-500">Base scenario:</span>
          <div className="flex gap-1">
            {['Orderly', 'Disorderly', 'Hot house world'].map(fam => {
              const m = NGFS_FAMILY_META[fam];
              const active = scenario.ngfsFamily === fam;
              return (
                <button
                  key={fam}
                  onClick={() => onChangeFamily(fam)}
                  className={`text-[10px] font-semibold px-2 py-1 rounded border transition-colors ${
                    active
                      ? `${m.bgClass} ${m.textClass} ${m.borderClass}`
                      : 'bg-gray-50 text-gray-500 border-black/10 hover:border-black/20'
                  }`}
                >
                  {fam === 'Hot house world' ? 'Hot House' : fam}
                </button>
              );
            })}
          </div>
        </div>

        {/* Time horizon */}
        <div className="flex items-center gap-1.5 ml-auto">
          <span className="text-[11px] text-gray-500">Horizon:</span>
          {[2030, 2040, 2050].map(yr => (
            <button
              key={yr}
              onClick={() => onChangeHorizon(yr)}
              className={`text-[10px] font-semibold px-2 py-1 rounded border transition-colors ${
                scenario.timeHorizon === yr
                  ? 'bg-gray-200 text-gray-800 border-gray-300'
                  : 'bg-gray-50 text-gray-500 border-black/10 hover:border-black/20'
              }`}
            >
              {yr}
            </button>
          ))}
        </div>
      </div>

      {/* Scroll area for groups */}
      <div className="flex-1 overflow-y-auto pr-0.5">
        {Object.values(PARAMETER_GROUPS).map(group => {
          const groupParams = scenario.parameters.filter(p => p.groupId === group.id);
          if (!groupParams.length) return null;
          return (
            <ParameterGroup
              key={group.id}
              group={group}
              parameters={groupParams}
              ngfsFamily={scenario.ngfsFamily}
              onChangeValue={onChangeValue}
              onReset={onReset}
            />
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-3 pt-3 mt-2 border-t border-gray-200 text-[10px] text-gray-500">
        <div className="flex items-center gap-1">
          <div className="w-4 h-0.5 bg-gray-400" />
          <span>NGFS baseline</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded-full bg-[#164E8A] shadow-[0_0_4px_rgba(34,211,238,0.6)]" />
          <span>Current value</span>
        </div>
      </div>
    </div>
  );
}

export default ParameterConfigurator;
