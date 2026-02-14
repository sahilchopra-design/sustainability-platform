import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { RefreshCw, TrendingUp, Table as TableIcon } from 'lucide-react';

const COLORS = ['#1e40af', '#0d9488', '#d97706', '#dc2626', '#7c3aed', '#059669', '#0284c7', '#be123c'];

export default function TrajectoryViewer({ trajectories, loading, scenarioName }) {
  const [selectedVariable, setSelectedVariable] = useState(null);
  const [selectedRegion, setSelectedRegion] = useState(null);

  const variables = useMemo(() => {
    const set = new Set();
    trajectories.forEach(t => set.add(t.variable_name));
    return [...set].sort();
  }, [trajectories]);

  const regions = useMemo(() => {
    const set = new Set();
    trajectories.forEach(t => set.add(t.region));
    return [...set].sort();
  }, [trajectories]);

  // Auto-select first variable
  const activeVar = selectedVariable || variables[0] || null;
  const activeRegion = selectedRegion; // null means all regions

  const filteredTrajectories = useMemo(() => {
    return trajectories.filter(t => {
      if (activeVar && t.variable_name !== activeVar) return false;
      if (activeRegion && t.region !== activeRegion) return false;
      return true;
    });
  }, [trajectories, activeVar, activeRegion]);

  // Build chart data: rows = years, columns = region lines
  const chartData = useMemo(() => {
    if (filteredTrajectories.length === 0) return [];
    const yearSet = new Set();
    filteredTrajectories.forEach(t => {
      Object.keys(t.time_series).forEach(y => yearSet.add(y));
    });
    const years = [...yearSet].sort();
    return years.map(year => {
      const row = { year };
      filteredTrajectories.forEach(t => {
        const label = t.region;
        row[label] = t.time_series[year] ?? null;
      });
      return row;
    });
  }, [filteredTrajectories]);

  const lineKeys = useMemo(() => {
    const keys = new Set();
    filteredTrajectories.forEach(t => keys.add(t.region));
    return [...keys];
  }, [filteredTrajectories]);

  const unit = filteredTrajectories[0]?.unit || '';

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground" data-testid="traj-loading">
        <RefreshCw className="h-5 w-5 animate-spin mr-2" /> Loading trajectories...
      </div>
    );
  }

  if (trajectories.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground" data-testid="no-trajectories">
          No trajectory data available for this scenario.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4" data-testid="trajectory-viewer">
      {/* Variable + Region selectors */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Variable</span>
          <Select value={activeVar || ''} onValueChange={setSelectedVariable}>
            <SelectTrigger className="w-[260px]" data-testid="variable-select">
              <SelectValue placeholder="Select variable" />
            </SelectTrigger>
            <SelectContent>
              {variables.map(v => <SelectItem key={v} value={v}>{v}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">Region</span>
          <Select value={activeRegion || '__all__'} onValueChange={v => setSelectedRegion(v === '__all__' ? null : v)}>
            <SelectTrigger className="w-[200px]" data-testid="region-select">
              <SelectValue placeholder="All regions" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__all__">All Regions</SelectItem>
              {regions.map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <Badge variant="outline" className="text-xs ml-auto">{filteredTrajectories.length} series</Badge>
      </div>

      <Tabs defaultValue="chart">
        <TabsList>
          <TabsTrigger value="chart" data-testid="tab-chart"><TrendingUp className="h-3 w-3 mr-1" />Chart</TabsTrigger>
          <TabsTrigger value="table" data-testid="tab-table"><TableIcon className="h-3 w-3 mr-1" />Table</TabsTrigger>
        </TabsList>

        <TabsContent value="chart" className="mt-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">
                {activeVar} {unit && <span className="text-muted-foreground font-normal">({unit})</span>}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={380}>
                  <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip
                      contentStyle={{
                        background: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: 8,
                        fontSize: 12,
                      }}
                    />
                    <Legend />
                    {lineKeys.map((key, i) => (
                      <Line
                        key={key}
                        type="monotone"
                        dataKey={key}
                        stroke={COLORS[i % COLORS.length]}
                        strokeWidth={2}
                        dot={false}
                        activeDot={{ r: 4 }}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-muted-foreground py-8 text-center">No data for current filters.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="table" className="mt-4">
          <Card>
            <CardContent className="pt-4 overflow-auto max-h-[500px]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="sticky left-0 bg-card z-10">Year</TableHead>
                    {lineKeys.map(key => (
                      <TableHead key={key} className="text-right">{key}</TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {chartData.map(row => (
                    <TableRow key={row.year}>
                      <TableCell className="font-medium sticky left-0 bg-card z-10">{row.year}</TableCell>
                      {lineKeys.map(key => (
                        <TableCell key={key} className="text-right tabular-nums">
                          {row[key] != null ? Number(row[key]).toLocaleString(undefined, { maximumFractionDigits: 2 }) : '-'}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
