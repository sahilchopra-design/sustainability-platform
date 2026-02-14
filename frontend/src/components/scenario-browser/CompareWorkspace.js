import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../ui/select';
import { GitCompare, X, Play, RefreshCw, Trash2 } from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const COLORS = ['#1e40af', '#dc2626', '#059669', '#d97706', '#7c3aed', '#0d9488', '#be123c', '#0284c7', '#4f46e5', '#ca8a04'];

export function CompareWorkspace({ scenarios, onRemove, onClear, onRun, compareData, loading, availableVariables }) {
  const [selectedVar, setSelectedVar] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');

  const handleRun = () => {
    const vars = selectedVar ? [selectedVar] : [];
    const regs = selectedRegion ? [selectedRegion] : [];
    onRun(vars, regs);
  };

  if (scenarios.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground" data-testid="compare-empty">
        <GitCompare className="h-10 w-10 mb-3 opacity-30" />
        <p className="text-sm">Add scenarios to compare</p>
        <p className="text-xs mt-1">Click the compare icon on any scenario card</p>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="compare-workspace">
      {/* Selected scenarios */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Compare Workspace ({scenarios.length}/10)</CardTitle>
            <Button variant="ghost" size="sm" onClick={onClear} className="h-7 text-xs">
              <Trash2 className="h-3 w-3 mr-1" />Clear
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-1.5 mb-3">
            {scenarios.map((sc, i) => (
              <Badge key={sc.id} className="gap-1 pr-1" style={{ backgroundColor: COLORS[i % COLORS.length], color: 'white' }}>
                <span className="truncate max-w-[140px] text-xs">{sc.display_name || sc.name}</span>
                {i === 0 && <span className="text-[8px] opacity-60">(BASE)</span>}
                <button onClick={() => onRemove(sc.id)} className="ml-1 hover:bg-white/20 rounded p-0.5">
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <label className="text-[10px] text-muted-foreground mb-0.5 block">Variable</label>
              <Select value={selectedVar || '__all__'} onValueChange={v => setSelectedVar(v === '__all__' ? '' : v)}>
                <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="All" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">All Variables</SelectItem>
                  {availableVariables.slice(0, 30).map(v => <SelectItem key={v.variable} value={v.variable} className="text-xs">{v.variable}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1">
              <label className="text-[10px] text-muted-foreground mb-0.5 block">Region</label>
              <Select value={selectedRegion || '__all__'} onValueChange={v => setSelectedRegion(v === '__all__' ? '' : v)}>
                <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="All" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">All Regions</SelectItem>
                  <SelectItem value="World">World</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button size="sm" onClick={handleRun} disabled={scenarios.length < 2 || loading} className="shrink-0"
              data-testid="run-compare-btn">
              {loading ? <RefreshCw className="h-3.5 w-3.5 animate-spin mr-1" /> : <Play className="h-3.5 w-3.5 mr-1" />}
              Compare
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Charts */}
      {compareData?.groups?.map((grp, i) => (
        <CompareChart key={i} group={grp} />
      ))}
    </div>
  );
}

function CompareChart({ group }) {
  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="text-sm flex items-center gap-2">
          {group.variable}
          <Badge variant="outline" className="text-[10px] font-normal">{group.region}</Badge>
          {group.unit && <span className="text-[10px] text-muted-foreground font-normal">({group.unit})</span>}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={group.chart_data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="year" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: 6, fontSize: 11 }} />
            <Legend wrapperStyle={{ fontSize: 10 }} />
            {group.scenarios.map((name, i) => (
              <Line key={name} type="monotone" dataKey={name} stroke={COLORS[i % COLORS.length]}
                strokeWidth={2} dot={false} activeDot={{ r: 3 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
        {group.statistics?.summary?.year && (
          <div className="flex gap-3 text-[10px] text-muted-foreground border-t pt-2 mt-2">
            <span>@{group.statistics.summary.year}:</span>
            <span>Min <strong>{group.statistics.summary.min?.toLocaleString()}</strong></span>
            <span>Max <strong>{group.statistics.summary.max?.toLocaleString()}</strong></span>
            <span>Spread <strong>{group.statistics.summary.spread_pct?.toFixed(1)}%</strong></span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
