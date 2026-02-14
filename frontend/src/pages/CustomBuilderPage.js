import React, { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Slider } from '../components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Separator } from '../components/ui/separator';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import {
  Wrench, Play, Save, RefreshCw, Thermometer, TrendingUp,
  Shield, AlertTriangle, DollarSign, Leaf, BarChart3, Zap,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function CustomBuilderPage() {
  const [baseScenarios, setBaseScenarios] = useState([]);
  const [selectedBaseId, setSelectedBaseId] = useState('');
  const [customizations, setCustomizations] = useState([]);
  const [impacts, setImpacts] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);
  const [savedScenarios, setSavedScenarios] = useState([]);
  const [scenarioName, setScenarioName] = useState('');

  useEffect(() => {
    fetch(`${API_URL}/api/v1/scenario-builder/base-scenarios`).then(r => r.json()).then(setBaseScenarios);
    fetch(`${API_URL}/api/v1/scenario-builder/custom`).then(r => r.json()).then(setSavedScenarios);
  }, []);

  const selectedBase = baseScenarios.find(s => s.id === selectedBaseId);

  const addCustomization = (variable) => {
    if (customizations.find(c => c.variable_name === variable)) return;
    setCustomizations(prev => [...prev, {
      variable_name: variable, region: 'World',
      customized_values: { '2030': 20, '2040': 10, '2050': 0 },
      interpolation_method: 'linear',
    }]);
  };

  const updateCustomValue = (idx, year, value) => {
    setCustomizations(prev => prev.map((c, i) => {
      if (i !== idx) return c;
      return { ...c, customized_values: { ...c.customized_values, [year]: Number(value) } };
    }));
  };

  const removeCustomization = (idx) => {
    setCustomizations(prev => prev.filter((_, i) => i !== idx));
  };

  const runPreview = async () => {
    if (!selectedBaseId) return;
    setPreviewLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/v1/scenario-builder/preview`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ base_scenario_id: selectedBaseId, customizations }),
      });
      const d = await r.json();
      setImpacts(d.impacts);
      toast.success('Preview calculated');
    } catch { toast.error('Preview failed'); }
    finally { setPreviewLoading(false); }
  };

  const handleSave = async () => {
    if (!selectedBaseId || !scenarioName.trim()) return;
    try {
      const r = await fetch(`${API_URL}/api/v1/scenario-builder/customize`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ base_scenario_id: selectedBaseId, name: scenarioName, customizations }),
      });
      const d = await r.json();
      toast.success(`Saved: ${d.name}`);
      setSavedScenarios(prev => [d, ...prev]);

      // Run Monte Carlo
      setSimLoading(true);
      const sr = await fetch(`${API_URL}/api/v1/scenario-builder/simulate`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ custom_scenario_id: d.id, simulation_type: 'monte_carlo', iterations: 1000 }),
      });
      setSimResult((await sr.json()).results);
      setSimLoading(false);
    } catch { toast.error('Save failed'); setSimLoading(false); }
  };

  const COMMON_VARS = [
    { name: 'Emissions|CO2', label: 'CO2 Emissions', icon: <TrendingUp className="h-3 w-3" /> },
    { name: 'Price|Carbon', label: 'Carbon Price', icon: <DollarSign className="h-3 w-3" /> },
    { name: 'Primary Energy', label: 'Primary Energy', icon: <Zap className="h-3 w-3" /> },
    { name: 'Primary Energy|Coal', label: 'Coal Energy', icon: <Zap className="h-3 w-3" /> },
    { name: 'GDP|PPP', label: 'GDP', icon: <BarChart3 className="h-3 w-3" /> },
  ];

  return (
    <div className="p-6 space-y-6" data-testid="custom-builder-page">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Wrench className="h-6 w-6 text-primary" />Custom Scenario Builder
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Customize any of {baseScenarios.length} scenarios and run impact simulations</p>
      </div>

      <Tabs defaultValue="build">
        <TabsList>
          <TabsTrigger value="build" data-testid="tab-build">Build</TabsTrigger>
          <TabsTrigger value="results" data-testid="tab-results" disabled={!impacts}>Results</TabsTrigger>
          <TabsTrigger value="simulation" data-testid="tab-simulation" disabled={!simResult}>Simulation</TabsTrigger>
          <TabsTrigger value="saved" data-testid="tab-saved">Saved ({savedScenarios.length})</TabsTrigger>
        </TabsList>

        {/* BUILD TAB */}
        <TabsContent value="build" className="space-y-4 mt-4">
          {/* Base scenario selector */}
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">1. Select Base Scenario</CardTitle></CardHeader>
            <CardContent>
              <Select value={selectedBaseId} onValueChange={setSelectedBaseId}>
                <SelectTrigger data-testid="base-select"><SelectValue placeholder="Choose a scenario to customize..." /></SelectTrigger>
                <SelectContent>
                  {baseScenarios.map(s => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.name} — {s.source_name} {s.temperature_target ? `(${s.temperature_target}°C)` : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedBase && (
                <div className="flex gap-2 mt-2">
                  <Badge variant="secondary">{selectedBase.source_name}</Badge>
                  {selectedBase.temperature_target && <Badge variant="outline">{selectedBase.temperature_target}°C</Badge>}
                  <Badge variant="outline">{selectedBase.trajectory_count} trajectories</Badge>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Parameter customization */}
          {selectedBaseId && (
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">2. Customize Parameters</CardTitle>
                  <div className="flex gap-1">
                    {COMMON_VARS.filter(v => !customizations.find(c => c.variable_name === v.name)).map(v => (
                      <Button key={v.name} size="sm" variant="outline" className="h-7 text-xs"
                        onClick={() => addCustomization(v.name)} data-testid={`add-${v.name}`}>
                        {v.icon}<span className="ml-1">{v.label}</span>
                      </Button>
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {customizations.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">Click a parameter button above to start customizing</p>
                )}
                {customizations.map((c, idx) => (
                  <div key={idx} className="border rounded-lg p-3 space-y-2" data-testid={`custom-${idx}`}>
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium">{c.variable_name}</h4>
                      <Button size="sm" variant="ghost" className="h-6 text-xs text-destructive" onClick={() => removeCustomization(idx)}>Remove</Button>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                      {['2030', '2040', '2050'].map(year => (
                        <div key={year}>
                          <label className="text-[10px] text-muted-foreground">{year}</label>
                          <Input type="number" value={c.customized_values[year] ?? ''} className="h-8 text-sm"
                            onChange={e => updateCustomValue(idx, year, e.target.value)}
                            data-testid={`val-${idx}-${year}`} />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          {selectedBaseId && customizations.length > 0 && (
            <div className="flex gap-3">
              <Button onClick={runPreview} disabled={previewLoading} data-testid="preview-btn">
                {previewLoading ? <RefreshCw className="h-4 w-4 animate-spin mr-1" /> : <Play className="h-4 w-4 mr-1" />}
                Preview Impacts
              </Button>
              <Input placeholder="Scenario name..." value={scenarioName} onChange={e => setScenarioName(e.target.value)}
                className="max-w-xs" data-testid="scenario-name-input" />
              <Button variant="outline" onClick={handleSave} disabled={!scenarioName.trim()} data-testid="save-simulate-btn">
                <Save className="h-4 w-4 mr-1" />Save & Simulate
              </Button>
            </div>
          )}
        </TabsContent>

        {/* RESULTS TAB */}
        <TabsContent value="results" className="space-y-4 mt-4">
          {impacts && <ImpactDashboard impacts={impacts} />}
        </TabsContent>

        {/* SIMULATION TAB */}
        <TabsContent value="simulation" className="space-y-4 mt-4">
          {simLoading && <p className="text-center py-8 text-muted-foreground"><RefreshCw className="h-4 w-4 inline animate-spin mr-2" />Running Monte Carlo...</p>}
          {simResult && <SimulationResults results={simResult} />}
        </TabsContent>

        {/* SAVED TAB */}
        <TabsContent value="saved" className="space-y-3 mt-4">
          {savedScenarios.length === 0 ? (
            <p className="text-center py-8 text-muted-foreground">No saved custom scenarios yet.</p>
          ) : savedScenarios.map(cs => (
            <Card key={cs.id} data-testid={`saved-${cs.id}`}>
              <CardContent className="py-3 px-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-sm">{cs.name}</h3>
                    <p className="text-xs text-muted-foreground">
                      Base: {cs.base_scenario?.name} — {cs.customizations?.length || 0} customizations
                    </p>
                  </div>
                  <div className="flex gap-1">
                    {cs.calculated_impacts?.risk_indicators && (
                      <Badge variant="outline" className="text-xs">Risk: {cs.calculated_impacts.risk_indicators.overall_climate_risk}</Badge>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ImpactDashboard({ impacts }) {
  const temp = impacts.temperature_outcome || {};
  const risks = impacts.risk_indicators || {};
  const econ = impacts.economic_impacts || {};
  const emis = impacts.emissions_trajectory || {};

  const radarData = [
    { metric: 'Physical', value: risks.physical_risk_score || 0 },
    { metric: 'Transition', value: risks.transition_risk_score || 0 },
    { metric: 'Overall', value: risks.overall_climate_risk || 0 },
  ];

  return (
    <div className="space-y-4" data-testid="impact-dashboard">
      {/* Top metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard icon={<Thermometer className="h-4 w-4 text-orange-500" />}
          label="Temp by 2100" value={temp.by_2100 ? `${temp.by_2100.toFixed(2)}°C` : '—'} />
        <MetricCard icon={<Leaf className="h-4 w-4 text-emerald-500" />}
          label="P(< 1.5°C)" value={`${temp.probability_1_5C || 0}%`} />
        <MetricCard icon={<Shield className="h-4 w-4 text-blue-500" />}
          label="Physical Risk" value={`${risks.physical_risk_score || '—'}/10`}
          sub={risks.physical_risk_label} />
        <MetricCard icon={<AlertTriangle className="h-4 w-4 text-amber-500" />}
          label="Transition Risk" value={`${risks.transition_risk_score || '—'}/10`}
          sub={risks.transition_risk_label} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Temperature trajectory */}
        {temp.trajectory?.length > 0 && (
          <Card>
            <CardHeader className="pb-1"><CardTitle className="text-sm">Temperature Trajectory (°C)</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={temp.trajectory}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} domain={['auto', 'auto']} />
                  <Tooltip contentStyle={{ fontSize: 11, background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: 6 }} />
                  <Line type="monotone" dataKey="value" stroke="#dc2626" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        )}

        {/* Emissions */}
        {emis.annual_emissions?.length > 0 && (
          <Card>
            <CardHeader className="pb-1"><CardTitle className="text-sm">Emissions (Gt CO2/yr)</CardTitle></CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={emis.annual_emissions}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="value" stroke="#059669" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
              <p className="text-[10px] text-muted-foreground mt-1">
                Cumulative: {emis.cumulative_emissions_gt} Gt | 1.5°C budget: {emis.carbon_budget_1_5c_consumed_pct}% used
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function SimulationResults({ results }) {
  const td = results.temperature_distribution || {};
  const rd = results.risk_distribution || {};

  return (
    <div className="space-y-4" data-testid="simulation-results">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard icon={<BarChart3 className="h-4 w-4 text-blue-500" />}
          label="Iterations" value={results.iterations} />
        <MetricCard icon={<Thermometer className="h-4 w-4 text-orange-500" />}
          label="Temp (median)" value={`${td.p50}°C`} sub={`Range: ${td.p5}–${td.p95}°C`} />
        <MetricCard icon={<Leaf className="h-4 w-4 text-emerald-500" />}
          label="P(< 1.5°C)" value={`${results.probability_below_1_5c}%`} />
        <MetricCard icon={<Shield className="h-4 w-4 text-blue-500" />}
          label="P(< 2°C)" value={`${results.probability_below_2c}%`} />
      </div>
      <Card>
        <CardHeader className="pb-1"><CardTitle className="text-sm">Temperature Distribution (Monte Carlo)</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-6 gap-2 text-center">
            {['p5', 'p25', 'p50', 'p75', 'p95', 'mean'].map(k => (
              <div key={k}>
                <p className="text-[10px] text-muted-foreground">{k.toUpperCase()}</p>
                <p className="text-sm font-semibold tabular-nums">{td[k]}°C</p>
              </div>
            ))}
          </div>
          <Progress value={results.probability_below_2c} className="mt-3 h-3" />
          <p className="text-xs text-muted-foreground text-center mt-1">{results.probability_below_2c}% probability of staying below 2°C</p>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ icon, label, value, sub }) {
  return (
    <Card>
      <CardContent className="pt-3 pb-2 px-4 flex items-center gap-3">
        {icon}
        <div>
          <p className="text-[10px] text-muted-foreground">{label}</p>
          <p className="text-lg font-semibold tabular-nums leading-tight">{value}</p>
          {sub && <p className="text-[10px] text-muted-foreground">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  );
}
