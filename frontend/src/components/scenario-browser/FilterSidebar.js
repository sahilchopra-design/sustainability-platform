import React, { useMemo } from 'react';
import { ScrollArea } from '../ui/scroll-area';
import { Checkbox } from '../ui/checkbox';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Slider } from '../ui/slider';
import { Separator } from '../ui/separator';
import { Input } from '../ui/input';
import {
  Globe, Layers, RefreshCw, Thermometer, Filter, X, Search,
} from 'lucide-react';

const TIER_LABELS = { tier_1: 'Primary', tier_2: 'Models', tier_3: 'Regional',
  tier_4: 'Sector', tier_5: 'Pricing', tier_6: 'Physical' };
const TIER_COLORS = { tier_1: 'bg-blue-600', tier_2: 'bg-teal-600', tier_3: 'bg-amber-600',
  tier_4: 'bg-violet-600', tier_5: 'bg-emerald-600', tier_6: 'bg-rose-600' };

export function FilterSidebar({
  sources, selectedSourceIds, toggleSource,
  categories, selectedCategories, toggleCategory,
  temperatureRange, setTemperatureRange,
  searchQuery, setSearchQuery, applySearch,
  clearFilters, activeFilterCount,
}) {
  const sourcesByTier = useMemo(() => {
    const m = {};
    sources.forEach(s => {
      if (!m[s.tier]) m[s.tier] = [];
      m[s.tier].push(s);
    });
    return m;
  }, [sources]);

  return (
    <aside className="w-64 border-r border-border bg-card shrink-0 flex flex-col h-full" data-testid="filter-sidebar">
      {/* Search */}
      <div className="p-3 border-b border-border">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input placeholder="Search scenarios..." className="pl-8 h-8 text-sm" value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && applySearch()}
            data-testid="sidebar-search" />
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-3 space-y-4">
          {/* Active filters */}
          {activeFilterCount > 0 && (
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium">{activeFilterCount} filter{activeFilterCount > 1 ? 's' : ''} active</span>
              <Button variant="ghost" size="sm" className="h-6 text-xs" onClick={clearFilters}>
                <X className="h-3 w-3 mr-1" />Clear
              </Button>
            </div>
          )}

          {/* Temperature slider */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
              <Thermometer className="h-3 w-3" />Temperature Target
            </h4>
            <Slider min={1} max={5} step={0.1} value={temperatureRange}
              onValueChange={setTemperatureRange} className="mt-1" data-testid="temp-slider" />
            <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
              <span>{temperatureRange[0].toFixed(1)}°C</span>
              <span>{temperatureRange[1].toFixed(1)}°C</span>
            </div>
          </div>

          <Separator />

          {/* Sources by tier */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
              <Globe className="h-3 w-3" />Data Sources
            </h4>
            {['tier_1', 'tier_2', 'tier_3', 'tier_4', 'tier_5', 'tier_6'].map(tier => {
              const tierSources = sourcesByTier[tier];
              if (!tierSources || tierSources.length === 0) return null;
              return (
                <div key={tier} className="mb-2">
                  <div className="flex items-center gap-1.5 mb-1">
                    <div className={`w-2 h-2 rounded-full ${TIER_COLORS[tier]}`} />
                    <span className="text-[10px] font-medium text-muted-foreground">{TIER_LABELS[tier]}</span>
                  </div>
                  {tierSources.map(src => (
                    <label key={src.id} className="flex items-center gap-2 py-0.5 px-1 rounded hover:bg-muted/50 cursor-pointer"
                      data-testid={`src-filter-${src.short_name}`}>
                      <Checkbox checked={selectedSourceIds.includes(src.id)}
                        onCheckedChange={() => toggleSource(src.id)} className="h-3.5 w-3.5" />
                      <span className="text-xs flex-1 truncate">{src.short_name.toUpperCase()}</span>
                      <span className="text-[10px] text-muted-foreground tabular-nums">{src.scenario_count}</span>
                    </label>
                  ))}
                </div>
              );
            })}
          </div>

          <Separator />

          {/* Categories */}
          <div>
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
              <Layers className="h-3 w-3" />Categories
            </h4>
            <div className="space-y-0.5 max-h-[200px] overflow-y-auto">
              {categories.map(cat => (
                <label key={cat} className="flex items-center gap-2 py-0.5 px-1 rounded hover:bg-muted/50 cursor-pointer">
                  <Checkbox checked={selectedCategories.includes(cat)}
                    onCheckedChange={() => toggleCategory(cat)} className="h-3.5 w-3.5" />
                  <span className="text-xs truncate">{cat}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </ScrollArea>
    </aside>
  );
}
