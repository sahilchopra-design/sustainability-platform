import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Skeleton } from '../ui/skeleton';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../ui/tooltip';
import { Badge } from '../ui/badge';
import { Grid3X3, Info } from 'lucide-react';
import { cn } from '../../lib/utils';

// Color scales
const COLOR_SCALES = {
  risk: ['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444', '#dc2626'],
  exposure: ['#eff6ff', '#bfdbfe', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8'],
  neutral: ['#f1f5f9', '#e2e8f0', '#cbd5e1', '#94a3b8', '#64748b', '#475569'],
};

function getColorFromScale(value, min, max, scale = 'risk') {
  const colors = COLOR_SCALES[scale];
  const normalized = max > min ? (value - min) / (max - min) : 0;
  const index = Math.min(Math.floor(normalized * colors.length), colors.length - 1);
  return colors[index];
}

function formatValue(value, format) {
  if (value === null || value === undefined) return '--';
  
  switch (format) {
    case 'currency':
      if (Math.abs(value) >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
      if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
      if (Math.abs(value) >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
      return `$${value.toFixed(0)}`;
    case 'percent':
      return `${(value * 100).toFixed(1)}%`;
    case 'decimal':
      return value.toFixed(2);
    default:
      return value.toLocaleString();
  }
}

function HeatmapCell({ value, min, max, format, rowLabel, colLabel, scale }) {
  const bgColor = getColorFromScale(value, min, max, scale);
  const textColor = value > (max - min) / 2 + min ? 'white' : 'inherit';
  
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={cn(
              "h-10 flex items-center justify-center text-xs font-medium",
              "transition-all hover:ring-2 hover:ring-primary/50 cursor-pointer"
            )}
            style={{ backgroundColor: bgColor, color: textColor }}
            data-testid={`heatmap-cell-${rowLabel}-${colLabel}`}
          >
            {formatValue(value, format)}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <div className="text-sm">
            <p className="font-medium">{rowLabel} / {colLabel}</p>
            <p className="text-muted-foreground">{formatValue(value, format)}</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function HeatmapVisualization({
  data = null,
  loading = false,
  title = "Risk Heatmap",
  description = "Sector and geographic exposure analysis",
  className,
}) {
  const [metric, setMetric] = useState('exposure');
  const [colorScale, setColorScale] = useState('risk');

  // Generate sample heatmap data from portfolio data
  const heatmapData = useMemo(() => {
    if (!data) {
      // Return sample data for demo
      const sectors = ['Energy', 'Utilities', 'Industrials', 'Financials', 'Technology'];
      const geographies = ['US', 'EU', 'UK', 'APAC', 'LatAm'];
      
      return {
        rows: sectors,
        cols: geographies,
        values: sectors.map(sector => 
          geographies.map(() => Math.random() * 100e6)
        ),
        format: 'currency',
      };
    }

    // Transform provided data
    const { sectorBreakdown = {}, geoBreakdown = {} } = data;
    
    const sectors = Object.keys(sectorBreakdown).slice(0, 6);
    const geographies = Object.keys(geoBreakdown).slice(0, 5);
    
    // Create cross-tabulation (simplified - in real app this would come from actual data)
    const values = sectors.map(sector => 
      geographies.map(geo => {
        const sectorValue = sectorBreakdown[sector] || 0;
        const geoValue = geoBreakdown[geo] || 0;
        const total = Object.values(sectorBreakdown).reduce((a, b) => a + b, 0) || 1;
        return (sectorValue * geoValue) / total;
      })
    );

    return {
      rows: sectors,
      cols: geographies,
      values,
      format: 'currency',
    };
  }, [data]);

  const { min, max } = useMemo(() => {
    const allValues = heatmapData.values.flat();
    return {
      min: Math.min(...allValues),
      max: Math.max(...allValues),
    };
  }, [heatmapData]);

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
    <Card className={className} data-testid="heatmap-visualization">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Grid3X3 className="h-5 w-5" />
              {title}
            </CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Select value={colorScale} onValueChange={setColorScale}>
              <SelectTrigger className="w-[120px]" data-testid="color-scale-select">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="risk">Risk Scale</SelectItem>
                <SelectItem value="exposure">Exposure Scale</SelectItem>
                <SelectItem value="neutral">Neutral</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div className="min-w-[400px]">
            {/* Column Headers */}
            <div className="flex">
              <div className="w-24 shrink-0" /> {/* Empty corner */}
              {heatmapData.cols.map(col => (
                <div 
                  key={col} 
                  className="flex-1 min-w-[80px] text-xs font-medium text-center py-2 text-muted-foreground"
                >
                  {col}
                </div>
              ))}
            </div>

            {/* Rows */}
            {heatmapData.rows.map((row, rowIndex) => (
              <div key={row} className="flex">
                {/* Row Label */}
                <div className="w-24 shrink-0 flex items-center text-xs font-medium pr-2 text-muted-foreground truncate">
                  {row}
                </div>
                {/* Cells */}
                {heatmapData.cols.map((col, colIndex) => (
                  <div key={col} className="flex-1 min-w-[80px] p-0.5">
                    <HeatmapCell
                      value={heatmapData.values[rowIndex][colIndex]}
                      min={min}
                      max={max}
                      format={heatmapData.format}
                      rowLabel={row}
                      colLabel={col}
                      scale={colorScale}
                    />
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Info className="h-3 w-3" />
            <span>Hover over cells for details</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Low</span>
            <div className="flex h-4">
              {COLOR_SCALES[colorScale].map((color, i) => (
                <div key={i} className="w-6 h-full" style={{ backgroundColor: color }} />
              ))}
            </div>
            <span className="text-xs text-muted-foreground">High</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
