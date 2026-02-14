import React, { useEffect, useMemo } from 'react';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import {
  Database, Grid3X3, List, Star, GitCompare, BarChart3, RefreshCw,
  Layers, Globe, Activity, TrendingUp, MapPin, Thermometer,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';

import { useBrowserStore } from '../store/scenarioBrowserStore';
import { ScenarioCard } from '../components/scenario-browser/ScenarioCard';
import { FilterSidebar } from '../components/scenario-browser/FilterSidebar';
import { ScenarioDetailDrawer } from '../components/scenario-browser/ScenarioDetailDrawer';
import { CompareWorkspace } from '../components/scenario-browser/CompareWorkspace';

const PIE_COLORS = ['#1e40af', '#0d9488', '#d97706', '#7c3aed', '#059669', '#dc2626', '#0284c7'];
const TIER_LABELS_FULL = {
  'SourceTier.TIER_1': 'T1 Primary', 'SourceTier.TIER_2': 'T2 Models', 'SourceTier.TIER_3': 'T3 Regional',
  'SourceTier.TIER_4': 'T4 Sector', 'SourceTier.TIER_5': 'T5 Pricing', 'SourceTier.TIER_6': 'T6 Physical',
};

export default function ScenarioBrowserPage() {
  const store = useBrowserStore();
  const {
    sources, stats, analytics, temperatureAnalytics, availableVariables,
    selectedSourceIds, toggleSource, selectedCategories, toggleCategory,
    temperatureRange, setTemperatureRange,
    searchQuery, setSearchQuery, applySearch,
    sortBy, setSortBy, viewMode, setViewMode,
    clearFilters,
    detailScenario, detailTrajectories, detailLoading, openDetail, closeDetail,
    compareScenarios, addToCompare, removeFromCompare, clearCompare, runCompare, compareData, compareLoading,
    favorites, toggleFavorite, isFavorite,
    scenariosLoading,
  } = store;

  useEffect(() => {
    store.init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredScenarios = store.getFilteredScenarios();

  const categories = useMemo(() => {
    if (!analytics?.by_category) return [];
    return Object.keys(analytics.by_category).sort();
  }, [analytics]);

  const activeFilterCount = selectedSourceIds.length + selectedCategories.length
    + (temperatureRange[0] > 1.0 || temperatureRange[1] < 5.0 ? 1 : 0)
    + (searchQuery.trim() ? 1 : 0);

  const sourceMap = useMemo(() => {
    const m = {};
    sources.forEach(s => { m[s.id] = s; });
    return m;
  }, [sources]);

  const favoriteScenarios = useMemo(() => {
    const favIds = new Set(favorites.map(f => f.scenario_id));
    return filteredScenarios.filter(s => favIds.has(s.id));
  }, [favorites, filteredScenarios]);

  return (
    <div className="flex h-full" data-testid="scenario-browser">
      {/* Sidebar */}
      <FilterSidebar
        sources={sources}
        selectedSourceIds={selectedSourceIds}
        toggleSource={toggleSource}
        categories={categories}
        selectedCategories={selectedCategories}
        toggleCategory={toggleCategory}
        temperatureRange={temperatureRange}
        setTemperatureRange={setTemperatureRange}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        applySearch={applySearch}
        clearFilters={clearFilters}
        activeFilterCount={activeFilterCount}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-5 pt-5 pb-3 border-b border-border bg-background shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h1 className="text-xl font-semibold tracking-tight flex items-center gap-2">
                <Database className="h-5 w-5 text-primary" />
                Scenario Browser
              </h1>
              <p className="text-xs text-muted-foreground mt-0.5">
                {stats?.total_sources || 0} sources — {filteredScenarios.length} of {stats?.total_scenarios || 0} scenarios — {stats?.total_trajectories?.toLocaleString() || 0} trajectories
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="h-8 w-[140px] text-xs" data-testid="sort-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="name">Sort: Name</SelectItem>
                  <SelectItem value="temperature_target">Sort: Temp</SelectItem>
                  <SelectItem value="trajectory_count">Sort: Data Size</SelectItem>
                </SelectContent>
              </Select>
              <div className="flex border rounded-md">
                <Button variant={viewMode === 'grid' ? 'default' : 'ghost'} size="icon" className="h-8 w-8 rounded-r-none"
                  onClick={() => setViewMode('grid')} data-testid="view-grid">
                  <Grid3X3 className="h-3.5 w-3.5" />
                </Button>
                <Button variant={viewMode === 'list' ? 'default' : 'ghost'} size="icon" className="h-8 w-8 rounded-l-none"
                  onClick={() => setViewMode('list')} data-testid="view-list">
                  <List className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </div>

          {/* Active filter chips */}
          {activeFilterCount > 0 && (
            <div className="flex flex-wrap gap-1">
              {selectedSourceIds.map(id => {
                const src = sourceMap[id];
                return src ? (
                  <Badge key={id} variant="secondary" className="text-[10px] gap-1 cursor-pointer" onClick={() => toggleSource(id)}>
                    {src.short_name.toUpperCase()} ×
                  </Badge>
                ) : null;
              })}
              {selectedCategories.map(cat => (
                <Badge key={cat} variant="secondary" className="text-[10px] gap-1 cursor-pointer" onClick={() => toggleCategory(cat)}>
                  {cat} ×
                </Badge>
              ))}
              {(temperatureRange[0] > 1.0 || temperatureRange[1] < 5.0) && (
                <Badge variant="outline" className="text-[10px]">
                  <Thermometer className="h-2.5 w-2.5 mr-0.5" />{temperatureRange[0]}–{temperatureRange[1]}°C
                </Badge>
              )}
            </div>
          )}
        </div>

        {/* Tabs */}
        <Tabs defaultValue="browse" className="flex-1 flex flex-col overflow-hidden">
          <div className="px-5 pt-2 border-b border-border shrink-0">
            <TabsList className="h-9">
              <TabsTrigger value="browse" className="text-xs" data-testid="tab-browse">
                <Layers className="h-3 w-3 mr-1" />Browse ({filteredScenarios.length})
              </TabsTrigger>
              <TabsTrigger value="compare" className="text-xs" data-testid="tab-compare">
                <GitCompare className="h-3 w-3 mr-1" />Compare ({compareScenarios.length})
              </TabsTrigger>
              <TabsTrigger value="favorites" className="text-xs" data-testid="tab-favorites">
                <Star className="h-3 w-3 mr-1" />Favorites ({favorites.length})
              </TabsTrigger>
              <TabsTrigger value="analytics" className="text-xs" data-testid="tab-analytics">
                <BarChart3 className="h-3 w-3 mr-1" />Analytics
              </TabsTrigger>
            </TabsList>
          </div>

          {/* Browse */}
          <TabsContent value="browse" className="flex-1 overflow-auto mt-0 px-5 py-4">
            {scenariosLoading ? (
              <div className="flex items-center justify-center py-16 text-muted-foreground">
                <RefreshCw className="h-5 w-5 animate-spin mr-2" />Loading scenarios...
              </div>
            ) : filteredScenarios.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground">
                <p className="text-sm">No scenarios match your filters.</p>
                <Button variant="link" size="sm" onClick={clearFilters} className="mt-2">Clear all filters</Button>
              </div>
            ) : viewMode === 'grid' ? (
              <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3" data-testid="scenario-grid">
                {filteredScenarios.map(sc => (
                  <ScenarioCard key={sc.id} scenario={sc} viewMode="grid"
                    isFavorite={isFavorite(sc.id)} onToggleFavorite={() => toggleFavorite(sc.id)}
                    onOpenDetail={() => openDetail(sc)} onAddCompare={() => { addToCompare(sc); toast.success('Added to compare'); }}
                    sourceTier={sourceMap[sc.source_id]?.tier} />
                ))}
              </div>
            ) : (
              <div className="space-y-1.5" data-testid="scenario-list">
                {filteredScenarios.map(sc => (
                  <ScenarioCard key={sc.id} scenario={sc} viewMode="list"
                    isFavorite={isFavorite(sc.id)} onToggleFavorite={() => toggleFavorite(sc.id)}
                    onOpenDetail={() => openDetail(sc)} onAddCompare={() => { addToCompare(sc); toast.success('Added to compare'); }}
                    sourceTier={sourceMap[sc.source_id]?.tier} />
                ))}
              </div>
            )}
          </TabsContent>

          {/* Compare */}
          <TabsContent value="compare" className="flex-1 overflow-auto mt-0 px-5 py-4">
            <CompareWorkspace scenarios={compareScenarios} onRemove={removeFromCompare}
              onClear={clearCompare} onRun={runCompare} compareData={compareData}
              loading={compareLoading} availableVariables={availableVariables} />
          </TabsContent>

          {/* Favorites */}
          <TabsContent value="favorites" className="flex-1 overflow-auto mt-0 px-5 py-4">
            {favorites.length === 0 ? (
              <div className="text-center py-16 text-muted-foreground">
                <Star className="h-8 w-8 mx-auto mb-2 opacity-30" />
                <p className="text-sm">No favorites yet</p>
                <p className="text-xs mt-1">Star scenarios from the Browse tab</p>
              </div>
            ) : (
              <div className="space-y-1.5">
                {favoriteScenarios.map(sc => (
                  <ScenarioCard key={sc.id} scenario={sc} viewMode="list"
                    isFavorite={true} onToggleFavorite={() => toggleFavorite(sc.id)}
                    onOpenDetail={() => openDetail(sc)} onAddCompare={() => { addToCompare(sc); toast.success('Added to compare'); }}
                    sourceTier={sourceMap[sc.source_id]?.tier} />
                ))}
                {favoriteScenarios.length === 0 && favorites.length > 0 && (
                  <p className="text-sm text-muted-foreground text-center py-8">Favorited scenarios are hidden by current filters.</p>
                )}
              </div>
            )}
          </TabsContent>

          {/* Analytics */}
          <TabsContent value="analytics" className="flex-1 overflow-auto mt-0 px-5 py-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
              <StatCard label="Sources" value={stats?.total_sources} icon={<Globe className="h-4 w-4" />} />
              <StatCard label="Scenarios" value={stats?.total_scenarios} icon={<Layers className="h-4 w-4" />} />
              <StatCard label="Variables" value={availableVariables?.length} icon={<TrendingUp className="h-4 w-4" />} />
              <StatCard label="Regions" value={analytics?.total_regions} icon={<MapPin className="h-4 w-4" />} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Temperature Distribution */}
              <Card>
                <CardHeader className="pb-1"><CardTitle className="text-sm">Temperature Targets</CardTitle></CardHeader>
                <CardContent>
                  {temperatureAnalytics && (
                    <ResponsiveContainer width="100%" height={220}>
                      <BarChart data={Object.entries(temperatureAnalytics.buckets).map(([k, v]) => ({ range: k, count: v }))}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="range" tick={{ fontSize: 10 }} />
                        <YAxis tick={{ fontSize: 10 }} />
                        <Tooltip />
                        <Bar dataKey="count" fill="hsl(var(--primary))" radius={[3, 3, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
              {/* Tier pie */}
              <Card>
                <CardHeader className="pb-1"><CardTitle className="text-sm">Scenarios by Tier</CardTitle></CardHeader>
                <CardContent>
                  {analytics?.by_tier && (
                    <ResponsiveContainer width="100%" height={220}>
                      <PieChart>
                        <Pie data={Object.entries(analytics.by_tier).map(([t, d]) => ({
                          name: TIER_LABELS_FULL[t] || t, value: d.scenarios,
                        }))} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                          {Object.keys(analytics.by_tier).map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                        </Pie>
                        <Tooltip />
                        <Legend wrapperStyle={{ fontSize: 10 }} />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
              {/* Category bar */}
              <Card className="md:col-span-2">
                <CardHeader className="pb-1"><CardTitle className="text-sm">Top Categories</CardTitle></CardHeader>
                <CardContent>
                  {analytics?.by_category && (
                    <ResponsiveContainer width="100%" height={240}>
                      <BarChart data={Object.entries(analytics.by_category).sort((a, b) => b[1] - a[1]).slice(0, 10)
                        .map(([k, v]) => ({ cat: k, count: v }))} layout="vertical" margin={{ left: 100 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis type="number" tick={{ fontSize: 10 }} />
                        <YAxis type="category" dataKey="cat" width={95} tick={{ fontSize: 9 }} />
                        <Tooltip />
                        <Bar dataKey="count" fill="#0d9488" radius={[0, 3, 3, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Detail Drawer */}
      <ScenarioDetailDrawer
        scenario={detailScenario}
        trajectories={detailTrajectories}
        loading={detailLoading}
        open={!!detailScenario}
        onClose={closeDetail}
        isFavorite={detailScenario ? isFavorite(detailScenario.id) : false}
        onToggleFavorite={() => detailScenario && toggleFavorite(detailScenario.id)}
        onAddCompare={() => { if (detailScenario) { addToCompare(detailScenario); toast.success('Added to compare'); } }}
        onRunConsistency={() => toast.info('Use the Comparison page for consistency checks')}
      />
    </div>
  );
}

function StatCard({ label, value, icon }) {
  return (
    <Card>
      <CardContent className="pt-3 pb-2 px-4 flex items-center justify-between">
        <div>
          <p className="text-[10px] text-muted-foreground">{label}</p>
          <p className="text-lg font-semibold tabular-nums">{value?.toLocaleString() ?? '—'}</p>
        </div>
        <div className="text-muted-foreground">{icon}</div>
      </CardContent>
    </Card>
  );
}
