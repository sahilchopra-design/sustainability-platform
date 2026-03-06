/**
 * MetricCard Component
 * Displays a single metric with trend indicator
 */

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export const MetricCard = ({
  title,
  value,
  unit,
  trend = 'neutral',
  trendValue,
  icon: Icon,
  onClick,
  className = ''
}) => {
  const getTrendConfig = () => {
    switch (trend) {
      case 'up':
        return {
          icon: TrendingUp,
          color: 'text-emerald-400',
          bgColor: 'bg-emerald-500/10'
        };
      case 'down':
        return {
          icon: TrendingDown,
          color: 'text-rose-400',
          bgColor: 'bg-rose-500/10'
        };
      default:
        return {
          icon: Minus,
          color: 'text-white/40',
          bgColor: 'bg-white/[0.02]'
        };
    }
  };

  const trendConfig = getTrendConfig();
  const TrendIcon = trendConfig.icon;

  return (
    <div
      className={`
        bg-[#0d1424] rounded-xl border border-white/[0.06] p-6
        cursor-pointer transition-all duration-200
        hover:shadow-md hover:-translate-y-0.5
        ${className}
      `}
      onClick={onClick}
      data-testid={`metric-card-${title?.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`p-2.5 rounded-lg ${trendConfig.bgColor}`}>
          {Icon && <Icon className="w-5 h-5 text-blue-300" />}
        </div>
        {trendValue && (
          <div className={`flex items-center gap-1 text-sm font-medium ${trendConfig.color}`}>
            <TrendIcon className="w-4 h-4" />
            <span>{trendValue}</span>
          </div>
        )}
      </div>

      <div className="space-y-1">
        <p className="text-sm font-medium text-white/40">{title}</p>
        <div className="flex items-baseline gap-1.5">
          <span className="text-3xl font-bold text-white tabular-nums">{value}</span>
          {unit && <span className="text-sm text-white/40">{unit}</span>}
        </div>
      </div>
    </div>
  );
};

export default MetricCard;
