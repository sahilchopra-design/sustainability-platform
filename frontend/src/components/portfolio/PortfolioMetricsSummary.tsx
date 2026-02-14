import React, { useMemo } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Users, PieChart, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { Skeleton } from '../ui/skeleton';
import { PortfolioMetrics } from '../../types/portfolio';
import { cn } from '../../lib/utils';

export interface PortfolioMetricsSummaryProps {
  metrics: PortfolioMetrics | null;
  loading?: boolean;
  currency?: string;
}

export const PortfolioMetricsSummary: React.FC<PortfolioMetricsSummaryProps> = ({
  metrics,
  loading = false,
  currency = 'USD',
}) => {
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(amount);
  };

  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat('en-US', {
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(num);
  };

  const getConcentrationRisk = (concentration: number): { label: string; color: string } => {
    if (concentration > 0.25) return { label: 'High', color: 'text-destructive' };
    if (concentration > 0.15) return { label: 'Medium', color: 'text-[hsl(var(--warning))]' };
    return { label: 'Low', color: 'text-[hsl(var(--success))]' };
  };

  const topSectors = useMemo(() => {
    if (!metrics?.sector_distribution) return [];
    return Object.entries(metrics.sector_distribution)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([sector, amount]) => ({
        sector,
        amount,
        percentage: (amount / metrics.total_exposure) * 100,
      }));
  }, [metrics]);

  const topCurrencies = useMemo(() => {
    if (!metrics?.currency_distribution) return [];
    return Object.entries(metrics.currency_distribution)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3);
  }, [metrics]);

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="portfolio-metrics-loading">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-3">
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-32 mb-2" />
              <Skeleton className="h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!metrics) {
    return (
      <Card data-testid="portfolio-metrics-empty">
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground">
            <AlertCircle className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
            <p>No metrics available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const concentrationRisk = getConcentrationRisk(metrics.concentration);

  return (
    <div className="space-y-4" data-testid="portfolio-metrics-summary">
      {/* Primary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Exposure */}
        <Card data-testid="metric-total-exposure">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Total Exposure
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-semibold tabular-nums" data-testid="total-exposure-value">
              {formatCurrency(metrics.total_exposure)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Across {metrics.holdings_count} holdings
            </p>
          </CardContent>
        </Card>

        {/* Holdings Count */}
        <Card data-testid="metric-holdings-count">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Users className="h-4 w-4" />
              Holdings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl sm:text-3xl font-semibold tabular-nums" data-testid="holdings-count-value">
              {formatNumber(metrics.holdings_count)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Avg: {formatCurrency(metrics.average_exposure)}
            </p>
          </CardContent>
        </Card>

        {/* Concentration Risk */}
        <Card data-testid="metric-concentration">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <PieChart className="h-4 w-4" />
              Concentration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline gap-2">
              <div className="text-2xl sm:text-3xl font-semibold tabular-nums">
                {(metrics.concentration * 100).toFixed(1)}%
              </div>
              <Badge
                variant="outline"
                className={cn('text-xs', concentrationRisk.color)}
                data-testid="concentration-risk-badge"
              >
                {concentrationRisk.label}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">HHI Index</p>
          </CardContent>
        </Card>

        {/* Currency Distribution */}
        <Card data-testid="metric-currencies">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Top Currencies
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {topCurrencies.length > 0 ? (
                topCurrencies.map(([curr, amount]) => (
                  <div key={curr} className="flex items-center justify-between text-sm">
                    <span className="font-mono font-medium">{curr}</span>
                    <span className="text-muted-foreground tabular-nums">
                      {formatCurrency(amount)}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-muted-foreground">No data</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sector Distribution */}
      {topSectors.length > 0 && (
        <Card data-testid="metric-sector-distribution">
          <CardHeader>
            <CardTitle className="text-base">Top Sectors by Exposure</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topSectors.map(({ sector, amount, percentage }) => (
                <div key={sector} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">{sector || 'Unknown'}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-muted-foreground tabular-nums">
                        {formatCurrency(amount)}
                      </span>
                      <span className="text-xs text-muted-foreground font-mono w-12 text-right tabular-nums">
                        {percentage.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <Progress value={percentage} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Last Updated */}
      <div className="text-xs text-muted-foreground text-right" data-testid="metrics-last-updated">
        Last updated: {new Date(metrics.last_updated).toLocaleString()}
      </div>
    </div>
  );
};