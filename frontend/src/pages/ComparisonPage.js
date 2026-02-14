import React, { useEffect, useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Separator } from '../components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '../components/ui/table';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import {
  GitCompare, Search, X, Play, Save, Thermometer, ChevronDown,
  AlertTriangle, CheckCircle, XCircle, BarChart3, TrendingUp, Target,
  ShieldCheck, RefreshCw,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, BarChart, Bar, Cell,
} from 'recharts';
import { useComparisonStore } from '../store/comparisonStore';

const COLORS = ['#1e40af', '#dc2626', '#059669', '#d97706', '#7c3aed', '#0d9488', '#be123c', '#0284c7', '#4f46e5', '#ca8a04'];

export default function ComparisonPage() {
  const {
    allScenarios, allScenariosLoading, fetchAllScenarios,
    availableVariables, fetchAvailableVariables,
    selectedScenarios, toggleScenario, clearSelection,
    selectedVariables, setSelectedVariables,
    selectedRegions, setSelectedRegions,
    comparisonData, comparisonLoading, runComparison,
    gapAnalysis, gapLoading, runGapAnalysis,
    consistencyChecks, consistencyLoading, runConsistencyCheck,
    saveComparison,
  } = useComparisonStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('builder');
  const [savedCompId, setSavedCompId] = useState(null);

  useEffect(() => {
    fetchAllScenarios();
    fetchAvailableVariables();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredScenarios = useMemo(() => {
    if (!searchQuery.trim()) return allScenarios;
    const q = searchQuery.toLowerCase();
    return allScenarios.filter(s =>
      s.name?.toLowerCase().includes(q) ||
      s.display_name?.toLowerCase().includes(q) ||
      s.source_name?.toLowerCase().includes(q) ||
      s.category?.toLowerCase().includes(q)
    );
  }, [allScenarios, searchQuery]);

  const handleRunComparison = async () => {
    await runComparison();
    setActiveTab('results');
    toast.success('Comparison complete');
  };

  const handleSaveAndAnalyze = async () => {
    const comp = await saveComparison('Comparison ' + new Date().toLocaleDateString(), '');
    if (comp?.id) {
      setSavedCompId(comp.id);
      await runGapAnalysis(comp.id);
      toast.success('Saved & gap analysis complete');
    }
  };

  const handleConsistencyCheck = async (scenarioId) => {
    await runConsistencyCheck(scenarioId);
    toast.success('Consistency check complete');
  };

  const uniqueVarNames = useMemo(() => {
    return [...new Set(availableVariables.map(v => v.variable))].sort();
  }, [availableVariables]);

  return (
    <div className="p-6 space-y-6" data-testid="comparison-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <GitCompare className="h-6 w-6 text-primary" />
            Scenario Comparison & Analysis
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Compare scenarios side-by-side, run gap analysis and consistency checks
          </p>
        </div>
        {selectedScenarios.length >= 2 && (
          <div className="flex gap-2">
            <Button onClick={handleRunComparison} disabled={comparisonLoading} data-testid="run-comparison-btn">
              <Play className="h-4 w-4 mr-1" />{comparisonLoading ? 'Running...' : 'Compare'}
            </Button>
            <Button variant="outline" onClick={handleSaveAndAnalyze} data-testid="save-analyze-btn">
              <Target className="h-4 w-4 mr-1" />Save & Analyze Gaps
            </Button>
          </div>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="builder" data-testid="tab-builder">
            Select Scenarios ({selectedScenarios.length})
          </TabsTrigger>
          <TabsTrigger value="results" data-testid="tab-results" disabled={!comparisonData}>
            Comparison Results
          </TabsTrigger>
          <TabsTrigger value="gaps" data-testid="tab-gaps" disabled={!gapAnalysis}>
            Gap Analysis
          </TabsTrigger>
          <TabsTrigger value="consistency" data-testid="tab-consistency" disabled={selectedScenarios.length === 0}>
            Consistency
          </TabsTrigger>
        </TabsList>

        {/* ---- Builder Tab ---- */}
        <TabsContent value="builder" className="space-y-4 mt-4">
          {/* Selected scenarios */}
          {selectedScenarios.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">Selected Scenarios ({selectedScenarios.length}/10)</CardTitle>
                  <Button variant="ghost" size="sm" onClick={clearSelection}><X className="h-3 w-3 mr-1" />Clear</Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {selectedScenarios.map((sc, i) => (
                    <Badge key={sc.id} className="gap-1 cursor-pointer" style={{ backgroundColor: COLORS[i % COLORS.length], color: 'white' }}
                      onClick={() => toggleScenario(sc)} data-testid={`selected-${sc.id}`}>
                      {sc.display_name || sc.name}
                      {i === 0 && <span className="text-[9px] opacity-70">(BASE)</span>}
                      <X className="h-3 w-3 ml-1" />
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Variable filter */}
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="text-xs font-medium text-muted-foreground mb-1 block">Filter Variables (optional)</label>
              <Select value={selectedVariables[0] || '__all__'} onValueChange={v => setSelectedVariables(v === '__all__' ? [] : [v])}>
                <SelectTrigger data-testid="variable-filter"><SelectValue placeholder="All Variables" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">All Variables</SelectItem>
                  {uniqueVarNames.slice(0, 30).map(v => <SelectItem key={v} value={v}>{v}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1">
              <label className="text-xs font-medium text-muted-foreground mb-1 block">Filter Region</label>
              <Select value={selectedRegions[0] || '__all__'} onValueChange={v => setSelectedRegions(v === '__all__' ? [] : [v])}>
                <SelectTrigger data-testid="region-filter"><SelectValue placeholder="All Regions" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">All Regions</SelectItem>
                  <SelectItem value="World">World</SelectItem>
                  <SelectItem value="R5.2OECD90+EU">OECD+EU</SelectItem>
                  <SelectItem value="R5.2ASIA">Asia</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Search + scenario list */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input placeholder="Search scenarios..." className="pl-9" value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)} data-testid="scenario-search" />
          </div>

          <div className="grid gap-2 max-h-[400px] overflow-y-auto" data-testid="scenario-picker">
            {allScenariosLoading ? (
              <p className="text-center py-8 text-muted-foreground">Loading scenarios...</p>
            ) : filteredScenarios.map(sc => {
              const isSelected = selectedScenarios.some(s => s.id === sc.id);
              return (
                <Card key={sc.id}
                  className={`cursor-pointer transition-all ${isSelected ? 'ring-2 ring-primary bg-primary/5' : 'hover:shadow-sm'}`}
                  onClick={() => toggleScenario(sc)} data-testid={`picker-${sc.id}`}>
                  <CardContent className="py-2.5 px-4 flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium truncate">{sc.display_name || sc.name}</span>
                        {sc.temperature_target && (
                          <Badge variant="outline" className="text-[10px] shrink-0">
                            <Thermometer className="h-2.5 w-2.5 mr-0.5" />{sc.temperature_target}°C
                          </Badge>
                        )}
                      </div>
                      <div className="flex gap-1 mt-0.5">
                        <Badge variant="secondary" className="text-[9px]">{sc.source_name}</Badge>
                        {sc.category && <Badge variant="outline" className="text-[9px]">{sc.category}</Badge>}
                      </div>
                    </div>
                    {isSelected && <CheckCircle className="h-5 w-5 text-primary shrink-0" />}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* ---- Results Tab ---- */}
        <TabsContent value="results" className="space-y-4 mt-4">
          {comparisonData ? (
            <>
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <Badge>{comparisonData.scenarios?.length} scenarios</Badge>
                <Badge variant="outline">{comparisonData.total_groups} variable×region groups</Badge>
              </div>
              {comparisonData.groups?.map((grp, i) => (
                <ComparisonChart key={i} group={grp} />
              ))}
            </>
          ) : (
            <p className="text-center py-12 text-muted-foreground">Run a comparison to see results.</p>
          )}
        </TabsContent>

        {/* ---- Gap Analysis Tab ---- */}
        <TabsContent value="gaps" className="space-y-4 mt-4">
          {gapLoading ? (
            <p className="text-center py-8 text-muted-foreground"><RefreshCw className="h-4 w-4 inline animate-spin mr-2" />Running gap analysis...</p>
          ) : gapAnalysis && gapAnalysis.length > 0 ? (
            <GapAnalysisView gaps={gapAnalysis} />
          ) : gapAnalysis ? (
            <p className="text-center py-8 text-muted-foreground">No gaps detected — scenarios may use different variables or regions.</p>
          ) : null}
        </TabsContent>

        {/* ---- Consistency Tab ---- */}
        <TabsContent value="consistency" className="space-y-4 mt-4">
          {!consistencyChecks && selectedScenarios.length > 0 && (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-3">Run consistency checks on a scenario</p>
              <div className="flex flex-wrap gap-2 justify-center">
                {selectedScenarios.map(sc => (
                  <Button key={sc.id} size="sm" variant="outline" onClick={() => handleConsistencyCheck(sc.id)}
                    data-testid={`check-${sc.id}`}>
                    <ShieldCheck className="h-3 w-3 mr-1" />{sc.display_name || sc.name}
                  </Button>
                ))}
              </div>
            </div>
          )}
          {consistencyLoading && (
            <p className="text-center py-8 text-muted-foreground"><RefreshCw className="h-4 w-4 inline animate-spin mr-2" />Checking...</p>
          )}
          {consistencyChecks && <ConsistencyView checks={consistencyChecks} />}
        </TabsContent>
      </Tabs>
    </div>
  );
}

/* ---- ComparisonChart ---- */
function ComparisonChart({ group }) {
  return (
    <Card data-testid={`chart-${group.variable}-${group.region}`}>
      <CardHeader className="pb-1">
        <CardTitle className="text-sm flex items-center gap-2">
          {group.variable}
          <Badge variant="outline" className="text-xs font-normal">{group.region}</Badge>
          {group.unit && <span className="text-xs text-muted-foreground font-normal">({group.unit})</span>}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={group.chart_data} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="year" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip contentStyle={{ background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: 8, fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {group.scenarios.map((name, i) => (
              <Line key={name} type="monotone" dataKey={name} stroke={COLORS[i % COLORS.length]}
                strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>

        {/* Stats summary */}
        {group.statistics?.summary?.year && (
          <div className="mt-3 flex gap-4 text-xs text-muted-foreground border-t pt-3">
            <span>At {group.statistics.summary.year}:</span>
            <span>Min: <strong>{group.statistics.summary.min?.toLocaleString()}</strong></span>
            <span>Max: <strong>{group.statistics.summary.max?.toLocaleString()}</strong></span>
            <span>Mean: <strong>{group.statistics.summary.mean?.toLocaleString()}</strong></span>
            <span>Spread: <strong>{group.statistics.summary.spread_pct?.toFixed(1)}%</strong></span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/* ---- GapAnalysisView ---- */
function GapAnalysisView({ gaps }) {
  const byType = useMemo(() => {
    const m = {};
    gaps.forEach(g => {
      if (!m[g.gap_type]) m[g.gap_type] = [];
      m[g.gap_type].push(g);
    });
    return m;
  }, [gaps]);

  const typeIcon = { policy: <Target className="h-4 w-4 text-blue-600" />, ambition: <TrendingUp className="h-4 w-4 text-orange-600" />, implementation: <BarChart3 className="h-4 w-4 text-violet-600" /> };

  return (
    <div className="space-y-4" data-testid="gap-analysis-view">
      {Object.entries(byType).map(([type, items]) => (
        <Card key={type}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              {typeIcon[type] || <AlertTriangle className="h-4 w-4" />}
              {type.charAt(0).toUpperCase() + type.slice(1)} Gaps ({items.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Variable</TableHead>
                  <TableHead>Year</TableHead>
                  <TableHead>Region</TableHead>
                  <TableHead className="text-right">Base</TableHead>
                  <TableHead className="text-right">Target</TableHead>
                  <TableHead className="text-right">Gap %</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((g, i) => (
                  <TableRow key={i}>
                    <TableCell className="text-xs">{g.variable}</TableCell>
                    <TableCell>{g.year}</TableCell>
                    <TableCell className="text-xs">{g.region}</TableCell>
                    <TableCell className="text-right tabular-nums">{g.base_value?.toLocaleString()}</TableCell>
                    <TableCell className="text-right tabular-nums">{g.target_value?.toLocaleString()}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant={Math.abs(g.gap_pct) > 20 ? 'destructive' : 'outline'} className="text-xs">
                        {g.gap_pct > 0 ? '+' : ''}{g.gap_pct?.toFixed(1)}%
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground max-w-[200px] truncate">{g.required_action}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/* ---- ConsistencyView ---- */
function ConsistencyView({ checks }) {
  const statusIcon = { pass: <CheckCircle className="h-5 w-5 text-emerald-600" />, warning: <AlertTriangle className="h-5 w-5 text-amber-500" />, fail: <XCircle className="h-5 w-5 text-red-600" /> };
  const statusColor = { pass: 'bg-emerald-50 border-emerald-200', warning: 'bg-amber-50 border-amber-200', fail: 'bg-red-50 border-red-200' };

  const overallScore = checks.length > 0
    ? (checks.reduce((a, c) => a + (c.score || 0), 0) / checks.length * 100).toFixed(0)
    : 0;

  return (
    <div className="space-y-4" data-testid="consistency-view">
      <Card>
        <CardContent className="pt-4 flex items-center gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Overall Consistency Score</p>
            <p className="text-3xl font-semibold tabular-nums">{overallScore}%</p>
          </div>
          <Progress value={Number(overallScore)} className="flex-1 h-3" />
        </CardContent>
      </Card>

      <div className="grid gap-3">
        {checks.map((c, i) => (
          <Card key={i} className={`border ${statusColor[c.status] || ''}`}>
            <CardContent className="py-3 px-4">
              <div className="flex items-start gap-3">
                {statusIcon[c.status]}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-sm capitalize">{c.check_type.replace(/_/g, ' ')}</h4>
                    <Badge variant="outline" className="text-xs">{(c.score * 100).toFixed(0)}%</Badge>
                    <Badge variant={c.status === 'pass' ? 'default' : c.status === 'warning' ? 'secondary' : 'destructive'} className="text-xs">{c.status}</Badge>
                  </div>
                  {c.issues && c.issues.length > 0 && (
                    <ul className="mt-1.5 space-y-0.5">
                      {c.issues.map((issue, j) => (
                        <li key={j} className="text-xs text-muted-foreground flex items-start gap-1">
                          <AlertTriangle className="h-3 w-3 mt-0.5 shrink-0 text-amber-500" />
                          {issue}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
