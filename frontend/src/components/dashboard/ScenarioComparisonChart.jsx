import React, { useState, useMemo } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, Cell, LabelList 
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Skeleton } from '../ui/skeleton';
import { Badge } from '../ui/badge';
import { Download, BarChart3, Info } from 'lucide-react';
import { Tooltip as UITooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import { cn } from '../../lib/utils';

const SCENARIO_COLORS = {
  'Net Zero 2050': '#22c55e',
  'Below 2°C': '#3b82f6',
  'Delayed Transition': '#f59e0b',
  'Current Policies': '#ef4444',
  'NDCs': '#8b5cf6',
  'Fragmented World': '#dc2626',
  'Orderly': '#22c55e',
  'Disorderly': '#f59e0b',
  'Hot house world': '#ef4444',
};

const METRICS = [
  { value: 'expected_loss', label: 'Expected Loss', format: 'currency' },
  { value: 'pd_change', label: 'PD Change', format: 'percent' },
  { value: 'lgd_change', label: 'LGD Change', format: 'percent' },
  { value: 'exposure_change', label: 'Exposure at Risk', format: 'currency' },
];

function formatValue(value, format) {
  if (value === null || value === undefined) return '--';
  
  switch (format) {
    case 'currency':
      if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
      if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
      if (Math.abs(value) >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
      return `$${value.toFixed(0)}`;
    case 'percent':
      return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(1)}%`;
    default:
      return value.toString();
  }
}

const CustomTooltip = ({ active, payload, label, format }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-popover border border-border rounded-lg shadow-lg p-3 min-w-[160px]">
        <p className="font-medium text-sm mb-2">{label}</p>
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center justify-between gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div 
                className="w-2.5 h-2.5 rounded-sm" 
                style={{ backgroundColor: entry.fill || entry.color }}
              />
              <span className="text-muted-foreground">{entry.name}</span>
            </div>
            <span className="font-medium tabular-nums">{formatValue(entry.value, format)}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function ScenarioComparisonChart({
  analysisResults = null,
  loading = false,
  className,
}) {
  const [selectedMetric, setSelectedMetric] = useState('expected_loss');
  const [selectedHorizon, setSelectedHorizon] = useState('2050');

  // Transform analysis results into chart data
  const chartData = useMemo(() => {
    if (!analysisResults?.results) return [];

    const scenarioGroups = {};
    
    analysisResults.results.forEach(result => {
      const scenario = result.scenario_name;
      const horizon = result.horizon;
      
      if (!scenarioGroups[horizon]) {
        scenarioGroups[horizon] = {};
      }
      
      scenarioGroups[horizon][scenario] = {
        expected_loss: result.portfolio_metrics?.expected_loss || 0,
        pd_change: result.portfolio_metrics?.avg_pd_change || 0,
        lgd_change: result.portfolio_metrics?.avg_lgd_change || 0,
        exposure_change: result.portfolio_metrics?.total_exposure_at_risk || 0,
      };
    });

    const horizonData = scenarioGroups[selectedHorizon] || {};
    
    return Object.entries(horizonData).map(([scenario, metrics]) => ({
      scenario,
      value: metrics[selectedMetric] || 0,
      color: SCENARIO_COLORS[scenario] || '#94a3b8',
    }));
  }, [analysisResults, selectedMetric, selectedHorizon]);

  const availableHorizons = useMemo(() => {
    if (!analysisResults?.results) return ['2030', '2040', '2050'];
    const horizons = [...new Set(analysisResults.results.map(r => r.horizon.toString()))];
    return horizons.sort();
  }, [analysisResults]);

  const currentMetricConfig = METRICS.find(m => m.value === selectedMetric) || METRICS[0];

  const handleExport = () => {
    const csvContent = [
      ['Scenario', currentMetricConfig.label, 'Horizon'],
      ...chartData.map(d => [d.scenario, d.value, selectedHorizon])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scenario_comparison_${selectedHorizon}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[350px] w-full rounded-lg" />
        </CardContent>
      </Card>
    );
  }

  if (!analysisResults) {
    return (
      <Card className={className} data-testid="scenario-comparison-chart">
        <CardContent className="py-12 text-center">
          <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground opacity-50 mb-4" />
          <p className="text-muted-foreground">Run an analysis to see scenario comparison</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className} data-testid="scenario-comparison-chart">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Scenario Comparison
            </CardTitle>
            <CardDescription>Compare climate risk impact across scenarios</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Select value={selectedMetric} onValueChange={setSelectedMetric}>
              <SelectTrigger className="w-[160px]" data-testid="metric-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {METRICS.map(metric => (
                  <SelectItem key={metric.value} value={metric.value}>
                    {metric.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={selectedHorizon} onValueChange={setSelectedHorizon}>
              <SelectTrigger className="w-[100px]" data-testid="horizon-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {availableHorizons.map(h => (
                  <SelectItem key={h} value={h}>{h}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <TooltipProvider>
              <UITooltip>
                <TooltipTrigger asChild>
                  <Button variant="outline" size="icon" onClick={handleExport} data-testid="export-chart-button">
                    <Download className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Export as CSV</TooltipContent>
              </UITooltip>
            </TooltipProvider>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            No data available for selected filters
          </div>
        ) : (
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                <XAxis 
                  type="number"
                  tickFormatter={(v) => formatValue(v, currentMetricConfig.format)}
                  tick={{ fontSize: 11 }}
                />
                <YAxis 
                  type="category"
                  dataKey="scenario"
                  width={130}
                  tick={{ fontSize: 11 }}
                />
                <Tooltip content={<CustomTooltip format={currentMetricConfig.format} />} />
                <Bar 
                  dataKey="value" 
                  name={currentMetricConfig.label}
                  radius={[0, 4, 4, 0]}
                  maxBarSize={40}
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                  <LabelList 
                    dataKey="value" 
                    position="right"
                    formatter={(v) => formatValue(v, currentMetricConfig.format)}
                    style={{ fontSize: 11, fill: 'var(--foreground)' }}
                  />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Legend */}
        <div className="flex flex-wrap gap-3 mt-4 pt-4 border-t justify-center">
          {chartData.map(item => (
            <div key={item.scenario} className="flex items-center gap-1.5">
              <div 
                className="w-3 h-3 rounded-sm" 
                style={{ backgroundColor: item.color }}
              />
              <span className="text-xs text-muted-foreground">{item.scenario}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
