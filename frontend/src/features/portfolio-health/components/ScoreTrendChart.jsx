/**
 * ScoreTrendChart
 *
 * Minimal sparkline chart showing 12-period trend of one or all health scores.
 * No axes labels — pure signal, WHOOP-style.
 *
 * Props:
 *   data     array  [{ period: '2024', climate_health: 72, ... }]
 *   metric   string 'climate_health' | 'financial_resilience' | 'transition_readiness'
 *   colour   string hex colour for the line
 *   height   number default 60
 */
import React from 'react';
import {
  LineChart,
  Line,
  ResponsiveContainer,
  ReferenceLine,
  Tooltip,
} from 'recharts';

const METRIC_COLOURS = {
  climate_health:        '#22d3ee',
  financial_resilience:  '#a78bfa',
  transition_readiness:  '#34d399',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0d1628] border border-white/10 rounded px-2 py-1 text-xs tabular-nums">
      <span className="text-white/50">{label}: </span>
      <span className="text-white font-semibold">{payload[0]?.value?.toFixed(1)}</span>
    </div>
  );
};

export function ScoreTrendChart({
  data = [],
  metric = 'climate_health',
  colour,
  height = 60,
}) {
  const lineColour = colour || METRIC_COLOURS[metric] || '#38bdf8';

  if (!data.length) {
    return (
      <div
        className="flex items-center justify-center text-white/20 text-xs"
        style={{ height }}
      >
        No trend data
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 4, right: 4, left: 4, bottom: 4 }}>
        {/* 70 = GREEN threshold */}
        <ReferenceLine y={70} stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
        {/* 40 = RED threshold */}
        <ReferenceLine y={40} stroke="rgba(255,255,255,0.06)" strokeDasharray="3 3" />

        <Tooltip content={<CustomTooltip />} />

        <Line
          type="monotone"
          dataKey={metric}
          stroke={lineColour}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 3, fill: lineColour }}
          isAnimationActive={true}
          animationDuration={600}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
