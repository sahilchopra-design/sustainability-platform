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
          color: 'text-emerald-600',
          bgColor: 'bg-emerald-50'
        };
      case 'down':
        return {
          icon: TrendingDown,
          color: 'text-rose-600',
          bgColor: 'bg-rose-50'
        };
      default:
        return {
          icon: Minus,
          color: 'text-slate-500',
          bgColor: 'bg-slate-50'
        };
    }
  };

  const trendConfig = getTrendConfig();
  const TrendIcon = trendConfig.icon;

  return (
    <div
      className={`
        bg-white rounded-xl border border-slate-200 p-6
        cursor-pointer transition-all duration-200
        hover:shadow-md hover:-translate-y-0.5
        ${className}
      `}
      onClick={onClick}
      data-testid={`metric-card-${title?.toLowerCase().replace(/\s+/g, '-')}`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`p-2.5 rounded-lg ${trendConfig.bgColor}`}>
          {Icon && <Icon className="w-5 h-5 text-blue-600" />}
        </div>
        {trendValue && (
          <div className={`flex items-center gap-1 text-sm font-medium ${trendConfig.color}`}>
            <TrendIcon className="w-4 h-4" />
            <span>{trendValue}</span>
          </div>
        )}
      </div>

      <div className="space-y-1">
        <p className="text-sm font-medium text-slate-500">{title}</p>
        <div className="flex items-baseline gap-1.5">
          <span className="text-3xl font-bold text-slate-900 tabular-nums">{value}</span>
          {unit && <span className="text-sm text-slate-500">{unit}</span>}
        </div>
      </div>
    </div>
  );
};

export default MetricCard;
