import React from 'react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Thermometer, Star, GitCompare, Leaf, Activity, ChevronRight } from 'lucide-react';

const TIER_COLORS = {
  tier_1: 'bg-blue-600', tier_2: 'bg-teal-600', tier_3: 'bg-amber-600',
  tier_4: 'bg-violet-600', tier_5: 'bg-emerald-600', tier_6: 'bg-rose-600',
};

export function ScenarioCard({ scenario, viewMode, isFavorite, onToggleFavorite, onOpenDetail, onAddCompare, sourceTier }) {
  const isReal = scenario.external_id?.includes('|');
  const isGrid = viewMode === 'grid';

  if (!isGrid) {
    // List view
    return (
      <Card className="hover:shadow-sm transition-shadow cursor-pointer group" onClick={onOpenDetail}
        data-testid={`sc-card-${scenario.id}`}>
        <CardContent className="py-2.5 px-4 flex items-center gap-3">
          <div className={`w-1.5 h-10 rounded-full shrink-0 ${TIER_COLORS[sourceTier] || 'bg-gray-400'}`} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium truncate">{scenario.display_name || scenario.name}</span>
              {scenario.temperature_target && (
                <Badge variant="outline" className="text-[10px] shrink-0 gap-0.5">
                  <Thermometer className="h-2.5 w-2.5" />{scenario.temperature_target}°C
                </Badge>
              )}
              {isReal && <Badge className="bg-blue-100 text-blue-700 text-[9px] shrink-0">REAL</Badge>}
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="text-[10px] text-muted-foreground">{scenario.source_name}</span>
              {scenario.category && <Badge variant="secondary" className="text-[9px] py-0">{scenario.category}</Badge>}
              <span className="text-[10px] text-muted-foreground ml-auto">{scenario.trajectory_count} traj</span>
            </div>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={e => { e.stopPropagation(); onToggleFavorite(); }}
              data-testid={`fav-${scenario.id}`}>
              <Star className={`h-3.5 w-3.5 ${isFavorite ? 'fill-amber-400 text-amber-400' : 'text-muted-foreground'}`} />
            </Button>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={e => { e.stopPropagation(); onAddCompare(); }}
              data-testid={`compare-add-${scenario.id}`}>
              <GitCompare className="h-3.5 w-3.5 text-muted-foreground" />
            </Button>
            <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Grid view
  return (
    <Card className="hover:shadow-md transition-all cursor-pointer group h-full flex flex-col" onClick={onOpenDetail}
      data-testid={`sc-card-${scenario.id}`}>
      <CardContent className="pt-4 pb-3 px-4 flex-1 flex flex-col">
        <div className="flex items-start justify-between mb-2">
          <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${TIER_COLORS[sourceTier] || 'bg-gray-400'}`} />
          <div className="flex gap-1">
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={e => { e.stopPropagation(); onToggleFavorite(); }}>
              <Star className={`h-3 w-3 ${isFavorite ? 'fill-amber-400 text-amber-400' : 'text-muted-foreground'}`} />
            </Button>
            <Button variant="ghost" size="icon" className="h-6 w-6" onClick={e => { e.stopPropagation(); onAddCompare(); }}>
              <GitCompare className="h-3 w-3 text-muted-foreground" />
            </Button>
          </div>
        </div>
        <h3 className="font-medium text-sm leading-tight mb-1 line-clamp-2">{scenario.display_name || scenario.name}</h3>
        <p className="text-[10px] text-muted-foreground line-clamp-2 mb-2 flex-1">{scenario.description}</p>
        <div className="flex flex-wrap gap-1 mb-2">
          <Badge variant="secondary" className="text-[9px] py-0">{scenario.source_name}</Badge>
          {scenario.category && <Badge variant="outline" className="text-[9px] py-0">{scenario.category}</Badge>}
          {isReal && <Badge className="bg-blue-100 text-blue-700 text-[9px] py-0">REAL</Badge>}
        </div>
        <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t">
          <div className="flex items-center gap-2">
            {scenario.temperature_target && (
              <span className="flex items-center gap-0.5"><Thermometer className="h-3 w-3" />{scenario.temperature_target}°C</span>
            )}
            {scenario.carbon_neutral_year && (
              <span className="flex items-center gap-0.5"><Leaf className="h-3 w-3" />NZ {scenario.carbon_neutral_year}</span>
            )}
          </div>
          <span className="flex items-center gap-0.5"><Activity className="h-3 w-3" />{scenario.trajectory_count}</span>
        </div>
      </CardContent>
    </Card>
  );
}
