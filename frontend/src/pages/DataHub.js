import React, { useEffect, useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Separator } from '../components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import {
  Database, Globe, Search, RefreshCw, ChevronRight, Thermometer,
  BarChart3, Layers, Clock, Activity, Filter, X, ArrowLeft,
  Zap, MapPin, TrendingUp, Leaf,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { useDataHubStore } from '../store/dataHubStore';
import TrajectoryViewer from '../components/data-hub/TrajectoryViewer';

const TIER_LABELS = { tier_1: 'Tier 1 — Primary', tier_2: 'Tier 2 — Models', tier_3: 'Tier 3 — Regional',
  tier_4: 'Tier 4 — Sector', tier_5: 'Tier 5 — Carbon Pricing', tier_6: 'Tier 6 — Physical Risk' };
const TIER_COLORS = { tier_1: 'bg-blue-600 text-white', tier_2: 'bg-teal-600 text-white',
  tier_3: 'bg-amber-600 text-white', tier_4: 'bg-violet-600 text-white',
  tier_5: 'bg-emerald-600 text-white', tier_6: 'bg-rose-600 text-white' };
const TIER_SHORT = { tier_1: 'T1', tier_2: 'T2', tier_3: 'T3', tier_4: 'T4', tier_5: 'T5', tier_6: 'T6' };
const PIE_COLORS = ['#1e40af', '#0d9488', '#d97706', '#7c3aed', '#059669', '#dc2626', '#0284c7', '#be123c'];

export default function DataHub() {
  const {
    stats, statsLoading, fetchStats,
    sources, sourcesLoading, fetchSources,
    scenarios, scenariosTotal, scenariosLoading, fetchScenarios, searchScenarios,
    selectedScenario, selectScenario, clearSelectedScenario,
    trajectories, trajectoriesLoading,
    syncSource, syncAll, fetchSyncLogs, syncLogs,
    analytics, analyticsLoading, temperatureAnalytics, availableVariables, fetchAnalytics,
  } = useDataHubStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeSourceId, setActiveSourceId] = useState(null);
  const [activeCategory, setActiveCategory] = useState(null);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchSources();
    fetchScenarios();
    fetchSyncLogs();
    fetchAnalytics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = () => {
    if (searchQuery.trim()) searchScenarios(searchQuery.trim());
    else fetchScenarios(activeSourceId, activeCategory);
  };

  const handleSourceFilter = (sourceId) => {
    const newId = activeSourceId === sourceId ? null : sourceId;
    setActiveSourceId(newId);
    setSearchQuery('');
    fetchScenarios(newId, activeCategory);
  };

  const handleCategoryFilter = (cat) => {
    const newCat = activeCategory === cat ? null : cat;
    setActiveCategory(newCat);
    fetchScenarios(activeSourceId, newCat);
  };

  const handleSyncAll = async () => {
    setSyncing(true);
    try {
      await syncAll();
      toast.success('All sources synced');
      await Promise.all([fetchStats(), fetchSources(), fetchScenarios(), fetchSyncLogs(), fetchAnalytics()]);
    } catch { toast.error('Sync failed'); }
    finally { setSyncing(false); }
  };

  const handleSyncSource = async (sourceId) => {
    setSyncing(true);
    try {
      await syncSource(sourceId);
      toast.success('Source synced');
      await Promise.all([fetchStats(), fetchSources(), fetchScenarios(activeSourceId, activeCategory), fetchSyncLogs()]);
    } catch { toast.error('Sync failed'); }
    finally { setSyncing(false); }
  };

  const categories = useMemo(() => {
    const cats = new Set();
    scenarios.forEach(s => { if (s.category) cats.add(s.category); });
    return [...cats].sort();
  }, [scenarios]);

  // ---- Scenario Detail View ----
  if (selectedScenario) {
    return (
      <div className="p-6 space-y-6" data-testid="data-hub-detail">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={clearSelectedScenario} data-testid="back-to-browser">
            <ArrowLeft className="h-4 w-4 mr-1" /> Back
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <h1 className="text-xl font-semibold">{selectedScenario.display_name || selectedScenario.name}</h1>
          <Badge variant="outline">{selectedScenario.source_name}</Badge>
          {selectedScenario.temperature_target && (
            <Badge className="bg-orange-100 text-orange-800 border-orange-200">
              <Thermometer className="h-3 w-3 mr-1" />{selectedScenario.temperature_target}°C
            </Badge>
          )}
          {selectedScenario.carbon_neutral_year && (
            <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">
              <Leaf className="h-3 w-3 mr-1" />Net Zero {selectedScenario.carbon_neutral_year}
            </Badge>
          )}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <MiniCard label="Category" value={selectedScenario.category || '-'} />
          <MiniCard label="Model" value={selectedScenario.model || '-'} />
          <MiniCard label="Horizon" value={`${selectedScenario.time_horizon_start}–${selectedScenario.time_horizon_end}`} />
          <MiniCard label="Trajectories" value={selectedScenario.trajectory_count} />
          <MiniCard label="Data Quality" value={selectedScenario.external_id?.includes('|') ? 'Real Data' : 'Synthetic'} />
        </div>
        {selectedScenario.description && (
          <Card><CardContent className="pt-4"><p className="text-sm text-muted-foreground">{selectedScenario.description}</p></CardContent></Card>
        )}
        <TrajectoryViewer trajectories={trajectories} loading={trajectoriesLoading} scenarioName={selectedScenario.name} />
      </div>
    );
  }

  // ---- Main Browser View ----
  return (
    <div className="p-6 space-y-6" data-testid="data-hub-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <Database className="h-6 w-6 text-primary" />
            Universal Scenario Data Hub
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {stats?.total_sources || 0} sources across 6 tiers — {stats?.total_scenarios || 0} scenarios — {stats?.total_trajectories?.toLocaleString() || 0} trajectory series
          </p>
        </div>
        <Button onClick={handleSyncAll} disabled={syncing} variant="outline" size="sm" data-testid="sync-all-btn">
          <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />Sync All
        </Button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard label="Sources" value={stats?.total_sources} icon={<Globe className="h-4 w-4" />} loading={statsLoading} />
        <StatCard label="Scenarios" value={stats?.total_scenarios} icon={<Layers className="h-4 w-4" />} loading={statsLoading} />
        <StatCard label="Trajectories" value={stats?.total_trajectories} icon={<Activity className="h-4 w-4" />} loading={statsLoading} />
        <StatCard label="Variables" value={availableVariables?.length} icon={<TrendingUp className="h-4 w-4" />} loading={analyticsLoading} />
        <StatCard label="Regions" value={analytics?.total_regions} icon={<MapPin className="h-4 w-4" />} loading={analyticsLoading} />
      </div>

      <Tabs defaultValue="browse">
        <TabsList>
          <TabsTrigger value="browse" data-testid="tab-browse">Browse Scenarios</TabsTrigger>
          <TabsTrigger value="sources" data-testid="tab-sources">Data Sources ({sources.length})</TabsTrigger>
          <TabsTrigger value="analytics" data-testid="tab-analytics">Analytics</TabsTrigger>
          <TabsTrigger value="sync" data-testid="tab-sync">Sync History</TabsTrigger>
        </TabsList>

        {/* ---- Browse Tab ---- */}
        <TabsContent value="browse" className="space-y-4 mt-4">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative flex-1 min-w-[200px] max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input data-testid="scenario-search" placeholder="Search scenarios..." className="pl-9"
                value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()} />
            </div>
            <Button size="sm" onClick={handleSearch} data-testid="search-btn">Search</Button>
            {(activeSourceId || activeCategory || searchQuery) && (
              <Button size="sm" variant="ghost" onClick={() => { setActiveSourceId(null); setActiveCategory(null); setSearchQuery(''); fetchScenarios(); }} data-testid="clear-filters">
                <X className="h-3 w-3 mr-1" /> Clear
              </Button>
            )}
          </div>

          {/* Source filter pills */}
          <div className="flex flex-wrap gap-1.5">
            {sources.map(src => (
              <Badge key={src.id}
                variant={activeSourceId === src.id ? 'default' : 'outline'}
                className="cursor-pointer hover:opacity-80 transition-opacity text-xs"
                onClick={() => handleSourceFilter(src.id)}
                data-testid={`source-filter-${src.short_name}`}>
                <span className={`inline-block w-4 h-4 rounded text-[9px] font-bold mr-1 flex items-center justify-center ${TIER_COLORS[src.tier] || 'bg-gray-500 text-white'}`}>
                  {TIER_SHORT[src.tier] || '?'}
                </span>
                {src.short_name.toUpperCase()} ({src.scenario_count})
              </Badge>
            ))}
          </div>

          {/* Category pills */}
          {categories.length > 0 && (
            <div className="flex flex-wrap gap-1.5 items-center">
              <Filter className="h-3.5 w-3.5 text-muted-foreground" />
              {categories.slice(0, 15).map(cat => (
                <Badge key={cat} variant={activeCategory === cat ? 'default' : 'secondary'}
                  className="cursor-pointer hover:opacity-80 text-xs" onClick={() => handleCategoryFilter(cat)}>
                  {cat}
                </Badge>
              ))}
              {categories.length > 15 && <span className="text-xs text-muted-foreground">+{categories.length - 15} more</span>}
            </div>
          )}

          {/* Scenario list */}
          {scenariosLoading ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground" data-testid="scenarios-loading">
              <RefreshCw className="h-5 w-5 animate-spin mr-2" /> Loading...
            </div>
          ) : scenarios.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground" data-testid="no-scenarios">No scenarios found.</div>
          ) : (
            <div className="grid gap-2" data-testid="scenario-list">
              {scenarios.map(sc => <ScenarioCard key={sc.id} scenario={sc} onSelect={() => selectScenario(sc)} />)}
              <p className="text-xs text-muted-foreground text-right">Showing {scenarios.length} of {scenariosTotal}</p>
            </div>
          )}
        </TabsContent>

        {/* ---- Sources Tab ---- */}
        <TabsContent value="sources" className="space-y-4 mt-4">
          {['tier_1', 'tier_2', 'tier_3', 'tier_4', 'tier_5', 'tier_6'].map(tier => {
            const tierSources = sources.filter(s => s.tier === tier);
            if (tierSources.length === 0) return null;
            return (
              <div key={tier}>
                <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                  <span className={`inline-block px-2 py-0.5 rounded text-xs ${TIER_COLORS[tier]}`}>{TIER_SHORT[tier]}</span>
                  {TIER_LABELS[tier]} ({tierSources.length})
                </h3>
                <div className="grid gap-2" data-testid={`source-list-${tier}`}>
                  {tierSources.map(src => (
                    <SourceCard key={src.id} source={src} onSync={() => handleSyncSource(src.id)} syncing={syncing} />
                  ))}
                </div>
              </div>
            );
          })}
        </TabsContent>

        {/* ---- Analytics Tab ---- */}
        <TabsContent value="analytics" className="space-y-4 mt-4">
          {analyticsLoading ? (
            <p className="text-muted-foreground py-8 text-center">Loading analytics...</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Temperature distribution */}
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Temperature Target Distribution</CardTitle></CardHeader>
                <CardContent>
                  {temperatureAnalytics && (
                    <ResponsiveContainer width="100%" height={250}>
                      <BarChart data={Object.entries(temperatureAnalytics.buckets).map(([k, v]) => ({ range: k, count: v }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="range" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Bar dataKey="count" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>

              {/* Scenarios by tier */}
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Scenarios by Tier</CardTitle></CardHeader>
                <CardContent>
                  {analytics?.by_tier && (
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie data={Object.entries(analytics.by_tier).map(([t, d]) => ({
                          name: TIER_LABELS[t.replace('SourceTier.', '').toLowerCase()] || t,
                          value: d.scenarios
                        }))} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label>
                          {Object.keys(analytics.by_tier).map((_, i) => (
                            <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend wrapperStyle={{ fontSize: 11 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>

              {/* Scenarios by category (top 10) */}
              <Card className="md:col-span-2">
                <CardHeader className="pb-2"><CardTitle className="text-sm">Scenarios by Category (Top 12)</CardTitle></CardHeader>
                <CardContent>
                  {analytics?.by_category && (
                    <ResponsiveContainer width="100%" height={280}>
                      <BarChart data={Object.entries(analytics.by_category)
                        .sort((a, b) => b[1] - a[1]).slice(0, 12)
                        .map(([k, v]) => ({ category: k, count: v }))} layout="vertical" margin={{ left: 120 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis type="number" tick={{ fontSize: 11 }} />
                        <YAxis type="category" dataKey="category" width={110} tick={{ fontSize: 10 }} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#0d9488" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* ---- Sync History Tab ---- */}
        <TabsContent value="sync" className="space-y-2 mt-4">
          {syncLogs.length === 0 ? (
            <p className="text-muted-foreground text-sm py-8 text-center">No sync logs yet.</p>
          ) : syncLogs.map(log => (
            <Card key={log.id} className="p-3">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <Badge variant={log.status === 'success' ? 'default' : 'destructive'} className="text-xs">{log.status}</Badge>
                  <Badge variant="outline" className="text-xs">{log.sync_type || 'full'}</Badge>
                  <span className="text-muted-foreground text-xs">{log.source_id.substring(0, 8)}...</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>+{log.scenarios_added} sc</span>
                  <span>+{log.trajectories_added} traj</span>
                  <span>{new Date(log.started_at).toLocaleString()}</span>
                </div>
              </div>
              {log.error_message && <p className="text-xs text-destructive mt-1">{log.error_message}</p>}
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}

/* ---- Sub-components ---- */

function StatCard({ label, value, icon, loading }) {
  return (
    <Card>
      <CardContent className="pt-4 pb-3 px-4 flex items-center justify-between">
        <div>
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="text-xl font-semibold tabular-nums">{loading ? '...' : (value?.toLocaleString() ?? '0')}</p>
        </div>
        <div className="text-muted-foreground">{icon}</div>
      </CardContent>
    </Card>
  );
}

function MiniCard({ label, value }) {
  return (
    <Card><CardContent className="pt-3 pb-2 px-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium text-sm truncate">{value}</p>
    </CardContent></Card>
  );
}

function ScenarioCard({ scenario, onSelect }) {
  const isReal = scenario.external_id?.includes('|');
  return (
    <Card className="hover:shadow-md transition-shadow cursor-pointer group" onClick={onSelect}
      data-testid={`scenario-card-${scenario.id}`}>
      <CardContent className="py-3 px-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <h3 className="font-medium text-sm truncate">{scenario.display_name || scenario.name}</h3>
              {scenario.temperature_target && (
                <Badge variant="outline" className="text-xs whitespace-nowrap shrink-0">
                  <Thermometer className="h-3 w-3 mr-1" />{scenario.temperature_target}°C
                </Badge>
              )}
              {isReal && <Badge className="bg-blue-100 text-blue-700 text-[10px] shrink-0">REAL DATA</Badge>}
            </div>
            <p className="text-xs text-muted-foreground line-clamp-1 mb-1.5">{scenario.description}</p>
            <div className="flex flex-wrap gap-1">
              <Badge variant="secondary" className="text-[10px]">{scenario.source_name}</Badge>
              {scenario.category && <Badge variant="outline" className="text-[10px]">{scenario.category}</Badge>}
              {scenario.carbon_neutral_year && (
                <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-300">NZ {scenario.carbon_neutral_year}</Badge>
              )}
              <span className="text-[10px] text-muted-foreground ml-1">{scenario.trajectory_count} traj</span>
            </div>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors shrink-0 ml-2 mt-1" />
        </div>
      </CardContent>
    </Card>
  );
}

function SourceCard({ source, onSync, syncing }) {
  return (
    <Card data-testid={`source-card-${source.short_name}`}>
      <CardContent className="py-3 px-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-medium text-sm">{source.name}</h3>
              {source.is_active && <Badge variant="outline" className="text-[10px] text-emerald-600 border-emerald-300">Active</Badge>}
              {source.update_frequency && <span className="text-[10px] text-muted-foreground">{source.update_frequency}</span>}
            </div>
            <p className="text-xs text-muted-foreground mb-1.5 line-clamp-1">{source.description}</p>
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <span><Layers className="h-3 w-3 inline mr-0.5" />{source.scenario_count} scenarios</span>
              <span><Activity className="h-3 w-3 inline mr-0.5" />{source.trajectory_count} trajectories</span>
              {source.last_synced_at && <span><Clock className="h-3 w-3 inline mr-0.5" />{new Date(source.last_synced_at).toLocaleDateString()}</span>}
            </div>
          </div>
          <Button size="sm" variant="outline" onClick={onSync} disabled={syncing} data-testid={`sync-${source.short_name}`}>
            <RefreshCw className={`h-3 w-3 mr-1 ${syncing ? 'animate-spin' : ''}`} />Sync
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
