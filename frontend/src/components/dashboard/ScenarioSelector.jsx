import React, { useState, useEffect } from 'react';
import { Check, ChevronDown, Zap, Clock } from 'lucide-react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import { Checkbox } from '../ui/checkbox';
import { ScrollArea } from '../ui/scroll-area';
import { Skeleton } from '../ui/skeleton';
import { cn } from '../../lib/utils';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SCENARIO_COLORS = {
  net_zero_2050: 'bg-success/20 text-success border-success/30',
  below_2c: 'bg-info/20 text-info border-info/30',
  delayed_transition: 'bg-warning/20 text-warning border-warning/30',
  ndc: 'bg-primary/20 text-primary border-primary/30',
  current_policies: 'bg-muted text-muted-foreground border-muted',
  fragmented_world: 'bg-destructive/20 text-destructive border-destructive/30',
};

const HORIZONS = [
  { value: 2030, label: '2030' },
  { value: 2040, label: '2040' },
  { value: 2050, label: '2050' },
];

const QUICK_SELECTS = [
  { id: 'orderly', label: 'Orderly', scenarios: ['net_zero_2050', 'below_2c'] },
  { id: 'disorderly', label: 'Disorderly', scenarios: ['delayed_transition'] },
  { id: 'hot_house', label: 'Hot House', scenarios: ['current_policies', 'ndc', 'fragmented_world'] },
  { id: 'all', label: 'All Scenarios', scenarios: null },
];

export function ScenarioSelector({
  selectedScenarios = [],
  selectedHorizons = [2030, 2040, 2050],
  onScenariosChange,
  onHorizonsChange,
  className,
}) {
  const [scenariosOpen, setScenariosOpen] = useState(false);
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/scenarios/templates`);
      const data = res.ok ? await res.json() : [];
      setScenarios(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to fetch scenarios:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleScenarioToggle = (scenarioId) => {
    if (selectedScenarios.includes(scenarioId)) {
      onScenariosChange(selectedScenarios.filter(id => id !== scenarioId));
    } else {
      onScenariosChange([...selectedScenarios, scenarioId]);
    }
  };

  const handleHorizonToggle = (horizon) => {
    if (selectedHorizons.includes(horizon)) {
      if (selectedHorizons.length > 1) {
        onHorizonsChange(selectedHorizons.filter(h => h !== horizon));
      }
    } else {
      onHorizonsChange([...selectedHorizons, horizon].sort());
    }
  };

  const handleQuickSelect = (quickSelect) => {
    if (quickSelect.scenarios === null) {
      // Select all
      onScenariosChange(scenarios.map(s => s.id));
    } else {
      const matchingScenarios = scenarios.filter(s => 
        quickSelect.scenarios.includes(s.ngfs_scenario_type)
      );
      onScenariosChange(matchingScenarios.map(s => s.id));
    }
  };

  const getScenarioColor = (scenario) => {
    return SCENARIO_COLORS[scenario.ngfs_scenario_type] || 'bg-muted text-muted-foreground';
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Scenario Multi-select */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">Scenarios</label>
        <Popover open={scenariosOpen} onOpenChange={setScenariosOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-between min-h-[42px]"
              data-testid="scenario-selector-trigger"
            >
              <div className="flex items-center gap-2 flex-wrap">
                {selectedScenarios.length === 0 ? (
                  <span className="text-muted-foreground">Select scenarios...</span>
                ) : selectedScenarios.length === scenarios.length ? (
                  <Badge variant="secondary">All Scenarios</Badge>
                ) : (
                  <span className="text-sm">
                    {selectedScenarios.length} scenario{selectedScenarios.length !== 1 ? 's' : ''} selected
                  </span>
                )}
              </div>
              <ChevronDown className="h-4 w-4 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[400px] p-0" align="start">
            {/* Quick Select Buttons */}
            <div className="p-3 border-b">
              <p className="text-xs text-muted-foreground mb-2">Quick Select</p>
              <div className="flex flex-wrap gap-2">
                {QUICK_SELECTS.map(qs => (
                  <Button
                    key={qs.id}
                    variant="outline"
                    size="sm"
                    onClick={() => handleQuickSelect(qs)}
                    data-testid={`quick-select-${qs.id}`}
                  >
                    <Zap className="h-3 w-3 mr-1" />
                    {qs.label}
                  </Button>
                ))}
              </div>
            </div>
            
            <ScrollArea className="max-h-[300px]">
              {loading ? (
                <div className="p-3 space-y-2">
                  {[1, 2, 3, 4].map(i => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : (
                <div className="p-2 space-y-1">
                  {scenarios.map(scenario => (
                    <label
                      key={scenario.id}
                      className={cn(
                        "flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors",
                        "hover:bg-muted",
                        selectedScenarios.includes(scenario.id) && "bg-primary/5"
                      )}
                      data-testid={`scenario-option-${scenario.id}`}
                    >
                      <Checkbox
                        checked={selectedScenarios.includes(scenario.id)}
                        onCheckedChange={() => handleScenarioToggle(scenario.id)}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">{scenario.name}</span>
                          <Badge 
                            variant="outline" 
                            className={cn("text-xs", getScenarioColor(scenario))}
                          >
                            {scenario.ngfs_scenario_type?.replace(/_/g, ' ')}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                          {scenario.description}
                        </p>
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </ScrollArea>
            
            <div className="p-3 border-t flex justify-between items-center">
              <span className="text-xs text-muted-foreground">
                {selectedScenarios.length} of {scenarios.length} selected
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onScenariosChange([])}
              >
                Clear all
              </Button>
            </div>
          </PopoverContent>
        </Popover>

        {/* Selected Scenarios Pills */}
        {selectedScenarios.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {selectedScenarios.slice(0, 4).map(id => {
              const scenario = scenarios.find(s => s.id === id);
              if (!scenario) return null;
              return (
                <Badge 
                  key={id} 
                  variant="secondary" 
                  className={cn("text-xs", getScenarioColor(scenario))}
                >
                  {scenario.name.replace(' (5.0)', '')}
                </Badge>
              );
            })}
            {selectedScenarios.length > 4 && (
              <Badge variant="outline" className="text-xs">
                +{selectedScenarios.length - 4} more
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* Time Horizon Selector */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Time Horizons
        </label>
        <div className="flex gap-2">
          {HORIZONS.map(horizon => (
            <Button
              key={horizon.value}
              variant={selectedHorizons.includes(horizon.value) ? "default" : "outline"}
              size="sm"
              onClick={() => handleHorizonToggle(horizon.value)}
              className="flex-1"
              data-testid={`horizon-${horizon.value}`}
            >
              {selectedHorizons.includes(horizon.value) && (
                <Check className="h-3 w-3 mr-1" />
              )}
              {horizon.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
