import React, { useState, useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, Sector } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Skeleton } from '../ui/skeleton';
import { ChevronRight, PieChart as PieIcon, Globe, Building2 } from 'lucide-react';
import { cn } from '../../lib/utils';

// Color palettes
const SECTOR_COLORS = {
  Energy: '#ef4444',
  Utilities: '#f97316', 
  'Basic Materials': '#84cc16',
  Industrials: '#06b6d4',
  Technology: '#8b5cf6',
  Financials: '#3b82f6',
  Healthcare: '#ec4899',
  'Consumer Staples': '#14b8a6',
  'Consumer Discretionary': '#f59e0b',
  'Real Estate': '#6366f1',
  Communications: '#a855f7',
  Unknown: '#94a3b8',
};

const GEO_COLORS = {
  'United States': '#3b82f6',
  'United Kingdom': '#ef4444',
  Germany: '#f59e0b',
  France: '#8b5cf6',
  Japan: '#ec4899',
  China: '#ef4444',
  Canada: '#06b6d4',
  Australia: '#84cc16',
  Brazil: '#14b8a6',
  India: '#f97316',
  Unknown: '#94a3b8',
};

const DEFAULT_COLORS = [
  '#3b82f6', '#ef4444', '#84cc16', '#f97316', '#8b5cf6',
  '#06b6d4', '#ec4899', '#f59e0b', '#14b8a6', '#6366f1'
];

function formatCurrency(value) {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
}

// Custom active shape for drill-down effect
const renderActiveShape = (props) => {
  const { cx, cy, innerRadius, outerRadius, startAngle, endAngle, fill, payload, percent } = props;

  return (
    <g>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 8}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        style={{ filter: 'drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1))' }}
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 12}
        outerRadius={outerRadius + 16}
        fill={fill}
      />
    </g>
  );
};

// Custom tooltip
const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-popover border border-border rounded-lg shadow-lg p-3">
        <p className="font-medium text-sm">{data.name}</p>
        <p className="text-muted-foreground text-sm">{formatCurrency(data.value)}</p>
        <p className="text-xs text-muted-foreground">{formatPercent(data.percent)} of total</p>
      </div>
    );
  }
  return null;
};

export function ExposureBreakdownChart({
  sectorBreakdown = {},
  geoBreakdown = {},
  ratingBreakdown = {},
  loading = false,
  onDrillDown,
  className,
}) {
  const [activeTab, setActiveTab] = useState('sector');
  const [activeIndex, setActiveIndex] = useState(null);

  const prepareChartData = (breakdown, colorMap) => {
    const total = Object.values(breakdown).reduce((sum, val) => sum + val, 0);
    return Object.entries(breakdown)
      .map(([name, value], index) => ({
        name,
        value,
        percent: total > 0 ? value / total : 0,
        color: colorMap[name] || DEFAULT_COLORS[index % DEFAULT_COLORS.length],
      }))
      .sort((a, b) => b.value - a.value);
  };

  const sectorData = useMemo(() => prepareChartData(sectorBreakdown, SECTOR_COLORS), [sectorBreakdown]);
  const geoData = useMemo(() => prepareChartData(geoBreakdown, GEO_COLORS), [geoBreakdown]);
  const ratingData = useMemo(() => prepareChartData(ratingBreakdown, {}), [ratingBreakdown]);

  const currentData = activeTab === 'sector' ? sectorData : activeTab === 'geo' ? geoData : ratingData;
  const totalExposure = currentData.reduce((sum, d) => sum + d.value, 0);

  if (loading) {
    return (
      <Card className={className}>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full rounded-lg" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className} data-testid="exposure-breakdown-chart">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <PieIcon className="h-5 w-5" />
              Exposure Breakdown
            </CardTitle>
            <CardDescription>Portfolio concentration by {activeTab}</CardDescription>
          </div>
          <Badge variant="outline" className="text-sm tabular-nums">
            Total: {formatCurrency(totalExposure)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-4" data-testid="breakdown-tabs">
            <TabsTrigger value="sector" data-testid="tab-sector">
              <Building2 className="h-4 w-4 mr-1" />
              Sector
            </TabsTrigger>
            <TabsTrigger value="geo" data-testid="tab-geo">
              <Globe className="h-4 w-4 mr-1" />
              Geography
            </TabsTrigger>
            <TabsTrigger value="rating" data-testid="tab-rating">
              Rating
            </TabsTrigger>
          </TabsList>

          {['sector', 'geo', 'rating'].map(tab => (
            <TabsContent key={tab} value={tab} className="m-0">
              <div className="flex gap-6">
                {/* Donut Chart */}
                <div className="flex-1 h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={currentData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={2}
                        dataKey="value"
                        activeIndex={activeIndex}
                        activeShape={renderActiveShape}
                        onMouseEnter={(_, index) => setActiveIndex(index)}
                        onMouseLeave={() => setActiveIndex(null)}
                        onClick={(data) => onDrillDown?.(activeTab, data.name)}
                      >
                        {currentData.map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.color}
                            style={{ cursor: onDrillDown ? 'pointer' : 'default' }}
                          />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Legend List */}
                <div className="w-48 space-y-1 overflow-auto max-h-[280px] pr-2">
                  {currentData.slice(0, 8).map((item, index) => (
                    <button
                      key={item.name}
                      className={cn(
                        "w-full flex items-center gap-2 p-2 rounded-lg text-left transition-colors",
                        "hover:bg-muted",
                        activeIndex === index && "bg-muted"
                      )}
                      onMouseEnter={() => setActiveIndex(index)}
                      onMouseLeave={() => setActiveIndex(null)}
                      onClick={() => onDrillDown?.(activeTab, item.name)}
                      data-testid={`legend-item-${item.name}`}
                    >
                      <div 
                        className="w-3 h-3 rounded-sm shrink-0" 
                        style={{ backgroundColor: item.color }}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium truncate">{item.name}</p>
                        <p className="text-xs text-muted-foreground tabular-nums">
                          {formatPercent(item.percent)}
                        </p>
                      </div>
                      {onDrillDown && (
                        <ChevronRight className="h-3 w-3 text-muted-foreground" />
                      )}
                    </button>
                  ))}
                  {currentData.length > 8 && (
                    <p className="text-xs text-muted-foreground text-center py-2">
                      +{currentData.length - 8} more
                    </p>
                  )}
                </div>
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </CardContent>
    </Card>
  );
}
