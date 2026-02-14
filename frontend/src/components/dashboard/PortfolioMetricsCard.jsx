import React from 'react';
import { TrendingUp, TrendingDown, Minus, Info, DollarSign, Percent, AlertTriangle, Users } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import { Skeleton } from '../ui/skeleton';
import { cn } from '../../lib/utils';

const METRIC_CONFIGS = {
  totalExposure: {
    label: 'Total Exposure',
    icon: DollarSign,
    format: 'currency',
    tooltip: 'Sum of all credit exposures in the portfolio',
  },
  expectedLoss: {
    label: 'Expected Loss',
    icon: AlertTriangle,
    format: 'currency',
    tooltip: 'Baseline expected loss (EL = PD × LGD × EAD)',
  },
  avgPD: {
    label: 'Avg. PD',
    icon: Percent,
    format: 'percent',
    tooltip: 'Average probability of default across all holdings',
  },
  avgLGD: {
    label: 'Avg. LGD',
    icon: Percent,
    format: 'percent',
    tooltip: 'Average loss given default across all holdings',
  },
  numAssets: {
    label: 'Holdings',
    icon: Users,
    format: 'number',
    tooltip: 'Total number of counterparty holdings',
  },
};

function formatValue(value, format) {
  if (value === null || value === undefined) return '--';
  
  switch (format) {
    case 'currency':
      if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
      if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
      if (value >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
      return `$${value.toFixed(0)}`;
    case 'percent':
      return `${value.toFixed(2)}%`;
    case 'number':
      return value.toLocaleString();
    default:
      return value.toString();
  }
}

function TrendIndicator({ delta, isNegativeGood = false }) {
  if (delta === null || delta === undefined) return null;
  
  const isPositive = delta > 0;
  const isGood = isNegativeGood ? !isPositive : isPositive;
  
  if (Math.abs(delta) < 0.01) {
    return (
      <span className="flex items-center text-muted-foreground text-xs">
        <Minus className="h-3 w-3 mr-0.5" />
        No change
      </span>
    );
  }
  
  return (
    <span className={cn(
      "flex items-center text-xs",
      isGood ? "text-success" : "text-destructive"
    )}>
      {isPositive ? (
        <TrendingUp className="h-3 w-3 mr-0.5" />
      ) : (
        <TrendingDown className="h-3 w-3 mr-0.5" />
      )}
      {isPositive ? '+' : ''}{delta.toFixed(1)}%
    </span>
  );
}

export function PortfolioMetricsCard({ 
  metrics, 
  loading = false,
  previousMetrics = null,
  className,
}) {
  if (loading) {
    return (
      <div className={cn("grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4", className)}>
        {[1, 2, 3, 4, 5].map(i => (
          <Card key={i}>
            <CardContent className="pt-6">
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-8 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!metrics) {
    return (
      <Card className={className}>
        <CardContent className="py-12 text-center">
          <DollarSign className="h-12 w-12 mx-auto text-muted-foreground opacity-50 mb-4" />
          <p className="text-muted-foreground">Select a portfolio to view metrics</p>
        </CardContent>
      </Card>
    );
  }

  const metricKeys = ['totalExposure', 'expectedLoss', 'avgPD', 'avgLGD', 'numAssets'];

  return (
    <div className={cn("grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4", className)} data-testid="portfolio-metrics-cards">
      {metricKeys.map(key => {
        const config = METRIC_CONFIGS[key];
        const Icon = config.icon;
        const value = metrics[key];
        const prevValue = previousMetrics?.[key];
        const delta = prevValue ? ((value - prevValue) / prevValue) * 100 : null;

        return (
          <Card key={key} className="hover:shadow-md transition-shadow" data-testid={`metric-card-${key}`}>
            <CardContent className="pt-6">
              <div className="flex items-start justify-between mb-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center gap-1.5 text-muted-foreground">
                        <Icon className="h-4 w-4" />
                        <span className="text-xs font-medium">{config.label}</span>
                        <Info className="h-3 w-3 opacity-50" />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p className="text-xs">{config.tooltip}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <p className="text-2xl font-semibold tabular-nums text-foreground" data-testid={`kpi-card-primary-value-${key}`}>
                {formatValue(value, config.format)}
              </p>
              {delta !== null && (
                <div className="mt-1" data-testid={`kpi-card-delta-${key}`}>
                  <TrendIndicator 
                    delta={delta} 
                    isNegativeGood={key === 'expectedLoss' || key === 'avgPD'} 
                  />
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

// Single metric card variant
export function MetricCard({
  label,
  value,
  format = 'number',
  icon: Icon,
  delta,
  deltaLabel,
  tooltip,
  loading = false,
  className,
}) {
  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="pt-6">
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-8 w-32" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("hover:shadow-md transition-shadow", className)} data-testid="kpi-card">
      <CardContent className="pt-6">
        <div className="flex items-start justify-between mb-2">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  {Icon && <Icon className="h-4 w-4" />}
                  <span className="text-xs font-medium">{label}</span>
                  {tooltip && <Info className="h-3 w-3 opacity-50" />}
                </div>
              </TooltipTrigger>
              {tooltip && (
                <TooltipContent>
                  <p className="text-xs">{tooltip}</p>
                </TooltipContent>
              )}
            </Tooltip>
          </TooltipProvider>
        </div>
        <p className="text-2xl font-semibold tabular-nums text-foreground" data-testid="kpi-card-primary-value">
          {formatValue(value, format)}
        </p>
        {delta !== undefined && (
          <div className="mt-1 flex items-center gap-2" data-testid="kpi-card-delta">
            <TrendIndicator delta={delta} />
            {deltaLabel && (
              <span className="text-xs text-muted-foreground">{deltaLabel}</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
