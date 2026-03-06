/**
 * TrajectoryVisualizer — interactive 2025–2050 trajectory chart with editable points.
 * Shows user-defined trajectory vs all three NGFS baselines.
 * Click/drag a point to edit. Reset per-year or full trajectory.
 */
import React, { useState, useCallback, useRef } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Legend, Dot,
} from 'recharts';
import { ALL_PARAMETERS, NGFS_FAMILY_META, buildTrajectory } from '../data/ngfsData';

const YEARS = [2025, 2030, 2035, 2040, 2045, 2050];

const FAMILY_COLORS = {
  Orderly:           '#22d3ee',
  Disorderly:        '#f59e0b',
  'Hot house world': '#f87171',
};

// ─── Custom editable dot ─────────────────────────────────────────────────────

function EditableDot(props) {
  const { cx, cy, payload, onEditPoint, activeYear } = props;
  const isActive = activeYear === payload.year;
  return (
    <circle
      cx={cx}
      cy={cy}
      r={isActive ? 7 : 5}
      fill={isActive ? '#22d3ee' : 'rgba(34,211,238,0.6)'}
      stroke={isActive ? '#fff' : 'rgba(34,211,238,0.8)'}
      strokeWidth={isActive ? 2 : 1}
      style={{ cursor: 'pointer', filter: isActive ? 'drop-shadow(0 0 6px rgba(34,211,238,0.8))' : 'none' }}
      onClick={() => onEditPoint(payload.year, payload.custom)}
    />
  );
}

// ─── Edit popover ─────────────────────────────────────────────────────────────

function EditPopover({ year, currentValue, param, onSave, onClose }) {
  const [value, setValue] = useState(String(currentValue ?? ''));

  const handleSave = () => {
    const num = parseFloat(value);
    if (!isNaN(num) && num >= param.min && num <= param.max) {
      onSave(year, num);
      onClose();
    }
  };

  return (
    <div className="absolute z-10 bg-[#0d1526] border border-cyan-500/30 rounded-lg p-3 shadow-xl w-52"
         style={{ top: '10px', right: '10px' }}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-semibold text-cyan-300">{year} — {param.label}</span>
        <button onClick={onClose} className="text-white/30 hover:text-white/70">
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div className="flex items-center gap-2 mb-2">
        <input
          type="number"
          value={value}
          min={param.min}
          max={param.max}
          step={param.step}
          onChange={e => setValue(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSave()}
          className="flex-1 text-[12px] bg-white/5 border border-white/10 rounded px-2 py-1 text-white/80 focus:outline-none focus:border-cyan-500/40"
          autoFocus
        />
        <span className="text-[10px] text-white/40">{param.unit}</span>
      </div>
      <div className="flex gap-1.5">
        <button
          onClick={handleSave}
          className="flex-1 text-[11px] bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 rounded px-2 py-1 hover:bg-cyan-500/30 transition-colors"
        >
          Apply
        </button>
        <button
          onClick={onClose}
          className="text-[11px] bg-white/5 text-white/50 border border-white/10 rounded px-2 py-1 hover:bg-white/10 transition-colors"
        >
          Cancel
        </button>
      </div>
      <p className="text-[9px] text-white/25 mt-1.5">Range: {param.min}–{param.max} {param.unit}</p>
    </div>
  );
}

// ─── Custom tooltip ───────────────────────────────────────────────────────────

function CustomTooltip({ active, payload, label, unit }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0d1526] border border-white/10 rounded-lg p-2.5 shadow-xl text-[11px]">
      <p className="font-semibold text-white/70 mb-1.5">{label}</p>
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-white/50">{entry.name}:</span>
          </div>
          <span className="font-mono font-semibold" style={{ color: entry.color }}>
            {entry.value?.toFixed(2)} {unit}
          </span>
        </div>
      ))}
    </div>
  );
}

// ─── Main component ────────────────────────────────────────────────────────────

export function TrajectoryVisualizer({ scenario, paramId, onUpdatePoint, onResetTrajectory }) {
  const [editState, setEditState]   = useState(null); // { year, value }
  const [activeYear, setActiveYear] = useState(null);
  const [showNgfs, setShowNgfs]     = useState({ Orderly: true, Disorderly: false, 'Hot house world': false });

  const param = ALL_PARAMETERS.find(p => p.id === paramId);
  const scenParam = scenario.parameters.find(p => p.id === paramId);

  // Hooks must be declared before any conditional return
  const handleEditPoint = useCallback((year, currentValue) => {
    setActiveYear(year);
    setEditState({ year, value: currentValue });
  }, []);

  const handleSaveEdit = useCallback((year, value) => {
    onUpdatePoint(paramId, year, value);
    setEditState(null);
    setActiveYear(null);
  }, [paramId, onUpdatePoint]);

  if (!param || !scenParam) {
    return (
      <div className="flex items-center justify-center h-48 text-white/30 text-sm">
        Select a parameter to visualize its trajectory
      </div>
    );
  }

  const NGFS_FAMILIES = ['Orderly', 'Disorderly', 'Hot house world'];

  // Build chart data — merge user trajectory + NGFS reference lines
  const chartData = YEARS.map(yr => {
    const userPt = (scenParam.trajectory || []).find(pt => pt.year === yr);
    const row = { year: yr, custom: userPt?.value ?? null };
    NGFS_FAMILIES.forEach(fam => {
      row[fam] = param.trajectories?.[fam]?.[yr] ?? null;
    });
    return row;
  });

  // Determine Y-axis domain
  const allVals = chartData.flatMap(d =>
    [d.custom, ...NGFS_FAMILIES.map(f => d[f])].filter(v => v != null)
  );
  const yMin = Math.min(...allVals, param.min);
  const yMax = Math.max(...allVals, param.max * 0.5);
  const yPad = (yMax - yMin) * 0.12;

  return (
    <div className="flex flex-col h-full" data-testid={`trajectory-visualizer-${paramId}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <h4 className="text-[13px] font-semibold text-white/90">{param.label}</h4>
          <p className="text-[10px] text-white/35">{param.unit} · Click any point to edit</p>
        </div>
        <div className="flex items-center gap-2">
          {/* Toggle NGFS overlays */}
          {NGFS_FAMILIES.map(fam => {
            const meta = NGFS_FAMILY_META[fam];
            return (
              <button
                key={fam}
                onClick={() => setShowNgfs(s => ({ ...s, [fam]: !s[fam] }))}
                className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border transition-colors ${
                  showNgfs[fam]
                    ? `${meta.bgClass} ${meta.textClass} ${meta.borderClass}`
                    : 'bg-white/5 text-white/25 border-white/8'
                }`}
              >
                {fam === 'Hot house world' ? 'HH' : fam}
              </button>
            );
          })}
          {/* Reset button */}
          <button
            onClick={() => { onResetTrajectory(paramId); setActiveYear(null); setEditState(null); }}
            className="text-[10px] text-white/40 hover:text-white/70 flex items-center gap-1 px-2 py-0.5 rounded border border-white/8 hover:border-white/16 transition-colors"
          >
            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Reset
          </button>
        </div>
      </div>

      {/* Chart */}
      <div className="relative flex-1" style={{ minHeight: 240 }}>
        {editState && (
          <EditPopover
            year={editState.year}
            currentValue={editState.value}
            param={param}
            onSave={handleSaveEdit}
            onClose={() => { setEditState(null); setActiveYear(null); }}
          />
        )}
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 10, right: 16, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="year" tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              domain={[yMin - yPad, yMax + yPad]}
              tick={{ fill: 'rgba(255,255,255,0.25)', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              width={42}
              tickFormatter={v => v >= 1000 ? `${(v/1000).toFixed(1)}k` : v.toFixed(1)}
            />
            <Tooltip content={<CustomTooltip unit={param.unit} />} />

            {/* NGFS reference lines */}
            {NGFS_FAMILIES.map(fam =>
              showNgfs[fam] ? (
                <Line
                  key={fam}
                  dataKey={fam}
                  stroke={FAMILY_COLORS[fam]}
                  strokeWidth={1.5}
                  strokeDasharray="5 3"
                  dot={false}
                  name={fam}
                  opacity={0.5}
                />
              ) : null
            )}

            {/* User trajectory */}
            <Line
              dataKey="custom"
              stroke="#22d3ee"
              strokeWidth={2.5}
              name="Your Scenario"
              connectNulls
              dot={(props) => (
                <EditableDot
                  {...props}
                  onEditPoint={handleEditPoint}
                  activeYear={activeYear}
                />
              )}
              activeDot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Data table */}
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-[10px]">
          <thead>
            <tr className="border-b border-white/8">
              <th className="text-left text-white/30 font-normal pb-1 pr-3">Scenario</th>
              {YEARS.map(yr => <th key={yr} className="text-right text-white/30 font-normal pb-1 px-1">{yr}</th>)}
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-white/5">
              <td className="text-cyan-400 font-medium py-1 pr-3">Your Scenario</td>
              {YEARS.map(yr => {
                const pt = (scenParam.trajectory || []).find(p => p.year === yr);
                return (
                  <td
                    key={yr}
                    className={`text-right px-1 py-1 cursor-pointer hover:bg-cyan-500/5 rounded ${
                      pt?.isEdited ? 'text-amber-400 font-semibold' : 'text-white/70'
                    }`}
                    onClick={() => handleEditPoint(yr, pt?.value)}
                  >
                    {pt?.value?.toFixed(1) ?? '—'}
                  </td>
                );
              })}
            </tr>
            {NGFS_FAMILIES.map(fam => (
              <tr key={fam} className="border-b border-white/5">
                <td className="py-1 pr-3" style={{ color: FAMILY_COLORS[fam] + '99' }}>
                  {fam === 'Hot house world' ? 'Hot House' : fam}
                </td>
                {YEARS.map(yr => (
                  <td key={yr} className="text-right px-1 py-1 text-white/30">
                    {param.trajectories?.[fam]?.[yr]?.toFixed(1) ?? '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TrajectoryVisualizer;
