import React, { useMemo, useState } from 'react';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '../ui/sheet';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../ui/select';
import {
  Thermometer, Leaf, Star, GitCompare, Activity, Globe,
  Calendar, Database, ExternalLink, RefreshCw, ShieldCheck,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const COLORS = ['#1e40af', '#0d9488', '#d97706', '#dc2626', '#7c3aed', '#059669'];

export function ScenarioDetailDrawer({ scenario, trajectories, loading, open, onClose, isFavorite, onToggleFavorite, onAddCompare, onRunConsistency }) {
  const [selectedVar, setSelectedVar] = useState(null);

  const variables = useMemo(() => {
    const s = new Set();
    trajectories.forEach(t => s.add(t.variable_name));
    return [...s].sort();
  }, [trajectories]);

  const activeVar = selectedVar || variables[0] || null;

  const chartData = useMemo(() => {
    if (!activeVar) return [];
    const filtered = trajectories.filter(t => t.variable_name === activeVar);
    const yearSet = new Set();
    filtered.forEach(t => Object.keys(t.time_series).forEach(y => yearSet.add(y)));
    const years = [...yearSet].sort();
    return years.map(y => {
      const row = { year: y };
      filtered.forEach(t => { row[t.region] = t.time_series[y]; });
      return row;
    });
  }, [trajectories, activeVar]);

  const regionKeys = useMemo(() => {
    if (!activeVar) return [];
    const s = new Set();
    trajectories.filter(t => t.variable_name === activeVar).forEach(t => s.add(t.region));
    return [...s];
  }, [trajectories, activeVar]);

  const unit = trajectories.find(t => t.variable_name === activeVar)?.unit || '';
  const isReal = scenario?.external_id?.includes('|');

  if (!scenario) return null;

  return (
    <Sheet open={open} onOpenChange={v => !v && onClose()}>
      <SheetContent className="w-[520px] sm:w-[580px] overflow-y-auto p-0" data-testid="detail-drawer">
        <SheetHeader className="p-5 pb-3 border-b">
          <SheetTitle className="text-lg leading-tight pr-8">{scenario.display_name || scenario.name}</SheetTitle>
          <div className="flex flex-wrap gap-1.5 mt-1">
            <Badge variant="secondary" className="text-xs">{scenario.source_name}</Badge>
            {scenario.category && <Badge variant="outline" className="text-xs">{scenario.category}</Badge>}
            {isReal && <Badge className="bg-blue-100 text-blue-700 text-xs">REAL DATA</Badge>}
            {scenario.model && <Badge variant="outline" className="text-xs">{scenario.model}</Badge>}
          </div>
        </SheetHeader>

        <div className="p-5 space-y-5">
          {/* Metadata cards */}
          <div className="grid grid-cols-3 gap-2">
            {scenario.temperature_target && (
              <MetaChip icon={<Thermometer className="h-3.5 w-3.5 text-orange-500" />} label="Temp Target" value={`${scenario.temperature_target}°C`} />
            )}
            {scenario.carbon_neutral_year && (
              <MetaChip icon={<Leaf className="h-3.5 w-3.5 text-emerald-500" />} label="Net Zero" value={String(scenario.carbon_neutral_year)} />
            )}
            <MetaChip icon={<Activity className="h-3.5 w-3.5 text-blue-500" />} label="Trajectories" value={String(scenario.trajectory_count)} />
            {scenario.time_horizon_start && (
              <MetaChip icon={<Calendar className="h-3.5 w-3.5 text-muted-foreground" />} label="Horizon" value={`${scenario.time_horizon_start}–${scenario.time_horizon_end}`} />
            )}
            {scenario.version && (
              <MetaChip icon={<Database className="h-3.5 w-3.5 text-muted-foreground" />} label="Version" value={scenario.version} />
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button size="sm" variant={isFavorite ? 'default' : 'outline'} onClick={onToggleFavorite} data-testid="drawer-fav">
              <Star className={`h-3.5 w-3.5 mr-1 ${isFavorite ? 'fill-white' : ''}`} />
              {isFavorite ? 'Favorited' : 'Favorite'}
            </Button>
            <Button size="sm" variant="outline" onClick={onAddCompare} data-testid="drawer-compare">
              <GitCompare className="h-3.5 w-3.5 mr-1" />Compare
            </Button>
            <Button size="sm" variant="outline" onClick={onRunConsistency} data-testid="drawer-consistency">
              <ShieldCheck className="h-3.5 w-3.5 mr-1" />Check
            </Button>
          </div>

          {scenario.description && (
            <p className="text-sm text-muted-foreground">{scenario.description}</p>
          )}

          <Separator />

          {/* Trajectory preview */}
          <div>
            <h4 className="text-sm font-semibold mb-2">Trajectory Preview</h4>
            {loading ? (
              <div className="flex items-center justify-center py-8 text-muted-foreground text-sm">
                <RefreshCw className="h-4 w-4 animate-spin mr-2" />Loading...
              </div>
            ) : variables.length === 0 ? (
              <p className="text-sm text-muted-foreground py-4 text-center">No trajectory data.</p>
            ) : (
              <>
                <Select value={activeVar || ''} onValueChange={setSelectedVar}>
                  <SelectTrigger className="h-8 text-xs mb-3" data-testid="drawer-var-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {variables.map(v => <SelectItem key={v} value={v} className="text-xs">{v}</SelectItem>)}
                  </SelectContent>
                </Select>

                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ fontSize: 11, background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: 6 }} />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                    {regionKeys.map((key, i) => (
                      <Line key={key} type="monotone" dataKey={key} stroke={COLORS[i % COLORS.length]}
                        strokeWidth={1.5} dot={false} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
                <p className="text-[10px] text-muted-foreground text-right mt-1">{unit}</p>
              </>
            )}
          </div>

          {/* Tags & regions */}
          {((scenario.tags && scenario.tags.length > 0) || (scenario.regions && scenario.regions.length > 0)) && (
            <>
              <Separator />
              {scenario.tags?.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground mb-1.5">Tags</h4>
                  <div className="flex flex-wrap gap-1">{scenario.tags.map(t => <Badge key={t} variant="secondary" className="text-[10px]">{t}</Badge>)}</div>
                </div>
              )}
              {scenario.regions?.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-muted-foreground mb-1.5">Regions</h4>
                  <div className="flex flex-wrap gap-1">{scenario.regions.map(r => <Badge key={r} variant="outline" className="text-[10px]">{r}</Badge>)}</div>
                </div>
              )}
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function MetaChip({ icon, label, value }) {
  return (
    <div className="flex items-center gap-2 rounded-md border p-2">
      {icon}
      <div>
        <p className="text-[10px] text-muted-foreground leading-none">{label}</p>
        <p className="text-xs font-medium leading-tight mt-0.5">{value}</p>
      </div>
    </div>
  );
}
