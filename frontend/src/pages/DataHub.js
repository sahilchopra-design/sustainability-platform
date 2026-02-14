import React, { useEffect, useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Separator } from '../components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { toast } from 'sonner';
import {
  Database, Globe, Search, RefreshCw, ChevronRight, Thermometer,
  BarChart3, Layers, Clock, Star, Activity, Filter, X, ArrowLeft,
} from 'lucide-react';
import { useDataHubStore } from '../store/dataHubStore';
import TrajectoryViewer from '../components/data-hub/TrajectoryViewer';

const TIER_LABELS = {
  tier_1: 'Tier 1',
  tier_2: 'Tier 2',
  tier_3: 'Tier 3',
};
const TIER_COLORS = {
  tier_1: 'bg-blue-100 text-blue-800',
  tier_2: 'bg-emerald-100 text-emerald-800',
  tier_3: 'bg-amber-100 text-amber-800',
};

export default function DataHub() {
  const {
    stats, statsLoading, fetchStats,
    sources, sourcesLoading, fetchSources,
    scenarios, scenariosTotal, scenariosLoading, fetchScenarios, searchScenarios,
    selectedScenario, selectScenario, clearSelectedScenario,
    trajectories, trajectoriesLoading,
    syncSource, syncAll, seedSources, fetchSyncLogs, syncLogs,
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
  }, []);

  const handleSearch = () => {
    if (searchQuery.trim()) {
      searchScenarios(searchQuery.trim());
    } else {
      fetchScenarios(activeSourceId, activeCategory);
    }
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
      toast.success('All sources synced successfully');
      await Promise.all([fetchStats(), fetchSources(), fetchScenarios(), fetchSyncLogs()]);
    } catch {
      toast.error('Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const handleSyncSource = async (sourceId) => {
    setSyncing(true);
    try {
      await syncSource(sourceId);
      toast.success('Source synced');
      await Promise.all([fetchStats(), fetchSources(), fetchScenarios(activeSourceId, activeCategory), fetchSyncLogs()]);
    } catch {
      toast.error('Sync failed');
    } finally {
      setSyncing(false);
    }
  };

  const categories = useMemo(() => {
    const cats = new Set();
    scenarios.forEach(s => { if (s.category) cats.add(s.category); });
    return [...cats].sort();
  }, [scenarios]);

  // If a scenario is selected, show the detail view
  if (selectedScenario) {
    return (
      <div className="p-6 space-y-6" data-testid="data-hub-detail">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={clearSelectedScenario} data-testid="back-to-browser">
            <ArrowLeft className="h-4 w-4 mr-1" /> Back
          </Button>
          <Separator orientation="vertical" className="h-6" />
          <h1 className="text-xl font-semibold">{selectedScenario.name}</h1>
          <Badge variant="outline">{selectedScenario.source_name}</Badge>
          {selectedScenario.temperature_target && (
            <Badge className="bg-orange-100 text-orange-800 border-orange-200">
              <Thermometer className="h-3 w-3 mr-1" />
              {selectedScenario.temperature_target}°C
            </Badge>
          )}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card><CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Category</p>
            <p className="font-medium">{selectedScenario.category || '-'}</p>
          </CardContent></Card>
          <Card><CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Model</p>
            <p className="font-medium text-sm">{selectedScenario.model || '-'}</p>
          </CardContent></Card>
          <Card><CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Horizon</p>
            <p className="font-medium">{selectedScenario.time_horizon_start}–{selectedScenario.time_horizon_end}</p>
          </CardContent></Card>
          <Card><CardContent className="pt-4">
            <p className="text-xs text-muted-foreground">Trajectories</p>
            <p className="font-medium">{selectedScenario.trajectory_count}</p>
          </CardContent></Card>
        </div>
        {selectedScenario.description && (
          <Card><CardContent className="pt-4">
            <p className="text-sm text-muted-foreground">{selectedScenario.description}</p>
          </CardContent></Card>
        )}
        <TrajectoryViewer
          trajectories={trajectories}
          loading={trajectoriesLoading}
          scenarioName={selectedScenario.name}
        />
      </div>
    );
  }

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
            Browse climate scenarios from {stats?.total_sources || 0} sources with {stats?.total_scenarios || 0} scenarios
          </p>
        </div>
        <Button onClick={handleSyncAll} disabled={syncing} variant="outline" size="sm" data-testid="sync-all-btn">
          <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
          Sync All
        </Button>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard label="Sources" value={stats?.total_sources} icon={<Globe className="h-4 w-4" />} loading={statsLoading} />
        <StatCard label="Scenarios" value={stats?.total_scenarios} icon={<Layers className="h-4 w-4" />} loading={statsLoading} />
        <StatCard label="Trajectories" value={stats?.total_trajectories} icon={<Activity className="h-4 w-4" />} loading={statsLoading} />
        <StatCard label="Comparisons" value={stats?.total_comparisons} icon={<BarChart3 className="h-4 w-4" />} loading={statsLoading} />
        <StatCard label="Active Sources" value={stats?.active_sources} icon={<Star className="h-4 w-4" />} loading={statsLoading} />
      </div>

      <Tabs defaultValue="browse">
        <TabsList>
          <TabsTrigger value="browse" data-testid="tab-browse">Browse Scenarios</TabsTrigger>
          <TabsTrigger value="sources" data-testid="tab-sources">Data Sources</TabsTrigger>
          <TabsTrigger value="sync" data-testid="tab-sync">Sync History</TabsTrigger>
        </TabsList>

        {/* Browse tab */}
        <TabsContent value="browse" className="space-y-4 mt-4">
          {/* Search + filters */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative flex-1 min-w-[200px] max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                data-testid="scenario-search"
                placeholder="Search scenarios..."
                className="pl-9"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <Button size="sm" onClick={handleSearch} data-testid="search-btn">Search</Button>
            {(activeSourceId || activeCategory || searchQuery) && (
              <Button size="sm" variant="ghost" onClick={() => { setActiveSourceId(null); setActiveCategory(null); setSearchQuery(''); fetchScenarios(); }} data-testid="clear-filters">
                <X className="h-3 w-3 mr-1" /> Clear
              </Button>
            )}
          </div>

          {/* Source pills */}
          <div className="flex flex-wrap gap-2">
            {sources.map(src => (
              <Badge
                key={src.id}
                variant={activeSourceId === src.id ? 'default' : 'outline'}
                className="cursor-pointer hover:opacity-80 transition-opacity"
                onClick={() => handleSourceFilter(src.id)}
                data-testid={`source-filter-${src.short_name}`}
              >
                {src.short_name.toUpperCase()} ({src.scenario_count})
              </Badge>
            ))}
          </div>

          {/* Category pills */}
          {categories.length > 0 && (
            <div className="flex flex-wrap gap-2">
              <Filter className="h-4 w-4 text-muted-foreground mt-0.5" />
              {categories.map(cat => (
                <Badge
                  key={cat}
                  variant={activeCategory === cat ? 'default' : 'secondary'}
                  className="cursor-pointer hover:opacity-80 text-xs"
                  onClick={() => handleCategoryFilter(cat)}
                >
                  {cat}
                </Badge>
              ))}
            </div>
          )}

          {/* Scenario list */}
          {scenariosLoading ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground" data-testid="scenarios-loading">
              <RefreshCw className="h-5 w-5 animate-spin mr-2" /> Loading scenarios...
            </div>
          ) : scenarios.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground" data-testid="no-scenarios">
              No scenarios found. Try syncing sources first.
            </div>
          ) : (
            <div className="grid gap-3" data-testid="scenario-list">
              {scenarios.map(sc => (
                <ScenarioCard key={sc.id} scenario={sc} onSelect={() => selectScenario(sc)} />
              ))}
              <p className="text-xs text-muted-foreground text-right">
                Showing {scenarios.length} of {scenariosTotal}
              </p>
            </div>
          )}
        </TabsContent>

        {/* Sources tab */}
        <TabsContent value="sources" className="space-y-4 mt-4">
          <div className="grid gap-3" data-testid="source-list">
            {sourcesLoading ? (
              <p className="text-muted-foreground py-8 text-center">Loading sources...</p>
            ) : sources.map(src => (
              <SourceCard key={src.id} source={src} onSync={() => handleSyncSource(src.id)} syncing={syncing} />
            ))}
          </div>
        </TabsContent>

        {/* Sync tab */}
        <TabsContent value="sync" className="space-y-4 mt-4">
          <div className="grid gap-2" data-testid="sync-log-list">
            {syncLogs.length === 0 ? (
              <p className="text-muted-foreground text-sm py-8 text-center">No sync logs yet.</p>
            ) : syncLogs.map(log => (
              <Card key={log.id} className="p-3">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <Badge variant={log.status === 'success' ? 'default' : 'destructive'} className="text-xs">
                      {log.status}
                    </Badge>
                    <span className="text-muted-foreground">{log.source_id.substring(0, 8)}...</span>
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
          </div>
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
          <p className="text-xl font-semibold tabular-nums">
            {loading ? '...' : (value?.toLocaleString() ?? '0')}
          </p>
        </div>
        <div className="text-muted-foreground">{icon}</div>
      </CardContent>
    </Card>
  );
}

function ScenarioCard({ scenario, onSelect }) {
  return (
    <Card
      className="hover:shadow-md transition-shadow cursor-pointer group"
      onClick={onSelect}
      data-testid={`scenario-card-${scenario.id}`}
    >
      <CardContent className="py-4 px-5">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-medium text-sm truncate">{scenario.name}</h3>
              {scenario.temperature_target && (
                <Badge variant="outline" className="text-xs whitespace-nowrap shrink-0">
                  <Thermometer className="h-3 w-3 mr-1" />
                  {scenario.temperature_target}°C
                </Badge>
              )}
            </div>
            <p className="text-xs text-muted-foreground line-clamp-1 mb-2">{scenario.description}</p>
            <div className="flex flex-wrap gap-1.5">
              <Badge variant="secondary" className="text-xs">{scenario.source_name}</Badge>
              {scenario.category && <Badge variant="outline" className="text-xs">{scenario.category}</Badge>}
              {scenario.model && <Badge variant="outline" className="text-xs">{scenario.model}</Badge>}
              <span className="text-xs text-muted-foreground ml-1">
                {scenario.trajectory_count} trajectories
              </span>
            </div>
          </div>
          <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors shrink-0 ml-3 mt-1" />
        </div>
      </CardContent>
    </Card>
  );
}

function SourceCard({ source, onSync, syncing }) {
  return (
    <Card data-testid={`source-card-${source.short_name}`}>
      <CardContent className="py-4 px-5">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-medium">{source.name}</h3>
              <Badge className={`text-xs ${TIER_COLORS[source.tier] || 'bg-gray-100 text-gray-800'}`}>
                {TIER_LABELS[source.tier] || source.tier}
              </Badge>
              {source.is_active && <Badge variant="outline" className="text-xs text-emerald-600 border-emerald-300">Active</Badge>}
            </div>
            <p className="text-xs text-muted-foreground mb-2">{source.description}</p>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span><Layers className="h-3 w-3 inline mr-1" />{source.scenario_count} scenarios</span>
              <span><Activity className="h-3 w-3 inline mr-1" />{source.trajectory_count} trajectories</span>
              {source.last_synced_at && (
                <span><Clock className="h-3 w-3 inline mr-1" />Synced {new Date(source.last_synced_at).toLocaleDateString()}</span>
              )}
            </div>
          </div>
          <Button size="sm" variant="outline" onClick={onSync} disabled={syncing} data-testid={`sync-${source.short_name}`}>
            <RefreshCw className={`h-3 w-3 mr-1 ${syncing ? 'animate-spin' : ''}`} />
            Sync
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
