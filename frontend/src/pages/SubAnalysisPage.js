import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Slider } from '../components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Separator } from '../components/ui/separator';
import { toast } from 'sonner';
import {
  Microscope, Play, RefreshCw, TrendingUp, ArrowRightLeft,
  BarChart3, Target, Layers, Zap, AlertTriangle, Download, Hash, LineChart as LineChartIcon,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, Legend, ReferenceLine, LineChart, Line,
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const COLORS = ['#1e40af', '#dc2626', '#059669', '#d97706', '#7c3aed', '#0d9488'];

export default function SubAnalysisPage() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScId, setSelectedScId] = useState('');
  const [targetMetric, setTargetMetric] = useState('temperature');
  const [variationRange, setVariationRange] = useState([0.2]);

  // Results
  const [sensitivity, setSensitivity] = useState(null);
  const [whatIf, setWhatIf] = useState(null);
  const [attribution, setAttribution] = useState(null);
  const [interactions, setInteractions] = useState(null);
  const [elasticity, setElasticity] = useState(null);
  const [ols, setOls] = useState(null);
  const [shapley, setShapley] = useState(null);
  const [loading, setLoading] = useState({});

  // What-if config
  const [wiParam, setWiParam] = useState('Emissions|CO2');
  const [wiChange, setWiChange] = useState(-20);
  const [wiYear, setWiYear] = useState(2030);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/scenario-builder/base-scenarios`).then(r => r.json()).then(setScenarios);
  }, []);

  const runSensitivity = async () => {
    if (!selectedScId) return;
    setLoading(p => ({ ...p, sensitivity: true }));
    try {
      const r = await fetch(`${API_URL}/api/v1/sub-parameter/sensitivity-analysis`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: selectedScId, target_metric: targetMetric, variation_range: variationRange[0] }),
      });
      setSensitivity(await r.json());
      toast.success('Sensitivity analysis complete');
    } catch { toast.error('Failed'); }
    finally { setLoading(p => ({ ...p, sensitivity: false })); }
  };

  const runWhatIf = async () => {
    if (!selectedScId) return;
    setLoading(p => ({ ...p, whatIf: true }));
    try {
      const r = await fetch(`${API_URL}/api/v1/sub-parameter/what-if`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ base_scenario_id: selectedScId, changes: [{ parameter: wiParam, change_type: 'relative', change_value: wiChange, apply_year: wiYear }] }),
      });
      setWhatIf(await r.json());
      toast.success('What-if complete');
    } catch { toast.error('Failed'); }
    finally { setLoading(p => ({ ...p, whatIf: false })); }
  };

  const runAttribution = async () => {
    if (!selectedScId) return;
    setLoading(p => ({ ...p, attribution: true }));
    try {
      const r = await fetch(`${API_URL}/api/v1/sub-parameter/attribution`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: selectedScId, outcome_metric: targetMetric }),
      });
      setAttribution(await r.json());
    } catch { toast.error('Failed'); }
    finally { setLoading(p => ({ ...p, attribution: false })); }
  };

  const runInteractions = async () => {
    if (!selectedScId) return;
    setLoading(p => ({ ...p, interactions: true }));
    try {
      const r = await fetch(`${API_URL}/api/v1/sub-parameter/interactions/${selectedScId}`);
      setInteractions(await r.json());
    } catch { toast.error('Failed'); }
    finally { setLoading(p => ({ ...p, interactions: false })); }
  };

  const runElasticity = async () => {
    if (!selectedScId) return;
    setLoading(p => ({ ...p, elasticity: true }));
    try {
      const r = await fetch(`${API_URL}/api/v1/sub-parameter/elasticity`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: selectedScId, target_metric: targetMetric }),
      });
      setElasticity(await r.json());
    } catch { toast.error('Failed'); }
    finally { setLoading(p => ({ ...p, elasticity: false })); }
  };

  const runOLS = async () => {
    if (!selectedScId) return;
    setLoading(p => ({ ...p, ols: true }));
    try {
      const r = await fetch(`${API_URL}/api/v1/sub-parameter/ols-attribution`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: selectedScId, target_metric: targetMetric }),
      });
      setOls(await r.json());
    } catch { toast.error('Failed'); }
    finally { setLoading(p => ({ ...p, ols: false })); }
  };

  const runShapley = async () => {
    if (!selectedScId) return;
    setLoading(p => ({ ...p, shapley: true }));
    try {
      const r = await fetch(`${API_URL}/api/v1/sub-parameter/shapley`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: selectedScId, target_metric: targetMetric, n_permutations: 15 }),
      });
      setShapley(await r.json());
    } catch { toast.error('Failed'); }
    finally { setLoading(p => ({ ...p, shapley: false })); }
  };

  const handleExport = async (format) => {
    const analyses = [sensitivity, elasticity, ols, shapley, attribution].filter(Boolean);
    if (!analyses.length) { toast.error('Run analyses first'); return; }
    try {
      const r = await fetch(`${API_URL}/api/v1/sub-parameter/export`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ analyses, format }),
      });
      const d = await r.json();
      window.open(`${API_URL}${d.download_url}`, '_blank');
      toast.success(`${format.toUpperCase()} exported`);
    } catch { toast.error('Export failed'); }
  };

  const runAll = () => { runSensitivity(); runElasticity(); runOLS(); runShapley(); runAttribution(); runInteractions(); };

  return (
    <div className="p-6 space-y-6" data-testid="sub-analysis-page">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Microscope className="h-6 w-6 text-primary" />Sub-Parameter Analysis
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Sensitivity, what-if, attribution, and interaction analysis for any scenario</p>
      </div>

      {/* Config */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <Card>
          <CardContent className="pt-3 pb-2">
            <label className="text-xs text-muted-foreground block mb-1">Scenario</label>
            <Select value={selectedScId} onValueChange={setSelectedScId}>
              <SelectTrigger className="h-8 text-xs" data-testid="scenario-select"><SelectValue placeholder="Select..." /></SelectTrigger>
              <SelectContent>
                {scenarios.slice(0, 50).map(s => <SelectItem key={s.id} value={s.id} className="text-xs">{s.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-3 pb-2">
            <label className="text-xs text-muted-foreground block mb-1">Target Metric</label>
            <Select value={targetMetric} onValueChange={setTargetMetric}>
              <SelectTrigger className="h-8 text-xs" data-testid="metric-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="temperature">Temperature</SelectItem>
                <SelectItem value="risk_physical">Physical Risk</SelectItem>
                <SelectItem value="risk_transition">Transition Risk</SelectItem>
                <SelectItem value="risk_overall">Overall Risk</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-3 pb-2">
            <label className="text-xs text-muted-foreground block mb-1">Variation: ±{(variationRange[0] * 100).toFixed(0)}%</label>
            <Slider min={0.05} max={0.5} step={0.05} value={variationRange} onValueChange={setVariationRange} className="mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-3 pb-2 flex items-end gap-2">
            <Button onClick={runAll} disabled={!selectedScId} className="flex-1" data-testid="run-all-btn">
              <Play className="h-4 w-4 mr-1" />Run All
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleExport('excel')} data-testid="export-excel">
              <Download className="h-3 w-3 mr-1" />Excel
            </Button>
            <Button variant="outline" size="sm" onClick={() => handleExport('pdf')} data-testid="export-pdf">
              <Download className="h-3 w-3 mr-1" />PDF
            </Button>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="sensitivity">
        <TabsList className="flex-wrap">
          <TabsTrigger value="sensitivity" data-testid="tab-sensitivity"><BarChart3 className="h-3 w-3 mr-1" />Tornado</TabsTrigger>
          <TabsTrigger value="elasticity" data-testid="tab-elasticity"><TrendingUp className="h-3 w-3 mr-1" />Elasticity</TabsTrigger>
          <TabsTrigger value="ols" data-testid="tab-ols"><Hash className="h-3 w-3 mr-1" />OLS</TabsTrigger>
          <TabsTrigger value="shapley" data-testid="tab-shapley"><Target className="h-3 w-3 mr-1" />Shapley</TabsTrigger>
          <TabsTrigger value="whatif" data-testid="tab-whatif"><ArrowRightLeft className="h-3 w-3 mr-1" />What-If</TabsTrigger>
          <TabsTrigger value="attribution" data-testid="tab-attribution"><Target className="h-3 w-3 mr-1" />Attribution</TabsTrigger>
          <TabsTrigger value="interactions" data-testid="tab-interactions"><Layers className="h-3 w-3 mr-1" />Interactions</TabsTrigger>
        </TabsList>

        {/* Sensitivity / Tornado */}
        <TabsContent value="sensitivity" className="mt-4 space-y-4">
          {loading.sensitivity ? <Loading /> : sensitivity ? (
            <>
              <div className="flex gap-2 text-sm text-muted-foreground">
                <Badge>{sensitivity.total_parameters_analyzed} parameters</Badge>
                <Badge variant="outline">Baseline: {sensitivity.baseline_value}</Badge>
                <Badge variant="outline">±{sensitivity.variation_range_pct}%</Badge>
              </div>
              <Card>
                <CardHeader className="pb-1"><CardTitle className="text-sm">Tornado Chart — {targetMetric}</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={Math.max(200, sensitivity.tornado_data.length * 45)}>
                    <BarChart data={sensitivity.tornado_data} layout="vertical" margin={{ left: 140, right: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis type="number" tick={{ fontSize: 10 }} />
                      <YAxis type="category" dataKey="parameter" width={130} tick={{ fontSize: 9 }} />
                      <Tooltip contentStyle={{ fontSize: 11 }} />
                      <ReferenceLine x={sensitivity.baseline_value} stroke="#666" strokeDasharray="3 3" />
                      <Bar dataKey="low_impact" name="Low (-)" fill="#1e40af" />
                      <Bar dataKey="high_impact" name="High (+)" fill="#dc2626" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-1"><CardTitle className="text-sm">Sensitivity Rankings</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {sensitivity.rankings.map((r, i) => (
                      <div key={i} className="flex items-center gap-3 text-sm">
                        <Badge variant="outline" className="w-8 text-center">#{r.rank}</Badge>
                        <span className="flex-1 text-xs truncate">{r.parameter}</span>
                        <div className="w-32 bg-muted rounded-full h-2">
                          <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.min(100, r.sensitivity_score)}%` }} />
                        </div>
                        <span className="text-xs tabular-nums w-16 text-right">{r.sensitivity_score}%</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          ) : <Empty msg="Select a scenario and run analysis" />}
        </TabsContent>

        {/* What-If */}
        <TabsContent value="whatif" className="mt-4 space-y-4">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Configure What-If Change</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-4 gap-3 items-end">
                <div>
                  <label className="text-xs text-muted-foreground">Parameter</label>
                  <Select value={wiParam} onValueChange={setWiParam}>
                    <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Emissions|CO2">Emissions CO2</SelectItem>
                      <SelectItem value="Price|Carbon">Carbon Price</SelectItem>
                      <SelectItem value="Primary Energy">Primary Energy</SelectItem>
                      <SelectItem value="GDP|PPP">GDP</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">Change (%)</label>
                  <Input type="number" value={wiChange} onChange={e => setWiChange(Number(e.target.value))} className="h-8 text-xs" data-testid="wi-change" />
                </div>
                <div>
                  <label className="text-xs text-muted-foreground">From Year</label>
                  <Input type="number" value={wiYear} onChange={e => setWiYear(Number(e.target.value))} className="h-8 text-xs" />
                </div>
                <Button onClick={runWhatIf} disabled={!selectedScId || loading.whatIf} className="h-8" data-testid="run-whatif-btn">
                  {loading.whatIf ? <RefreshCw className="h-3 w-3 animate-spin mr-1" /> : <ArrowRightLeft className="h-3 w-3 mr-1" />}Run
                </Button>
              </div>
            </CardContent>
          </Card>
          {whatIf && (
            <>
              {whatIf.key_insights?.length > 0 && (
                <Card>
                  <CardContent className="pt-3">
                    <h4 className="text-xs font-semibold mb-1">Key Insights</h4>
                    {whatIf.key_insights.map((ins, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <AlertTriangle className="h-3 w-3 text-amber-500 shrink-0" />{ins}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(whatIf.differences || {}).map(([key, d]) => (
                  <Card key={key}>
                    <CardContent className="pt-3 pb-2">
                      <p className="text-[10px] text-muted-foreground capitalize">{key.replace(/_/g, ' ')}</p>
                      <div className="flex items-baseline gap-2">
                        <span className="text-xs text-muted-foreground">{d.baseline?.toFixed(2)}</span>
                        <span className="text-lg font-semibold">{d.modified?.toFixed(2)}</span>
                      </div>
                      <Badge variant={d.pct_change > 0 ? 'destructive' : 'default'} className="text-[10px] mt-1">
                        {d.pct_change > 0 ? '+' : ''}{d.pct_change?.toFixed(1)}%
                      </Badge>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </TabsContent>

        {/* Attribution */}
        <TabsContent value="attribution" className="mt-4 space-y-4">
          {loading.attribution ? <Loading /> : attribution ? (
            <>
              <div className="flex gap-2 text-sm">
                <Badge>Outcome: {attribution.total_value?.toFixed(3)}</Badge>
                <Badge variant="outline">Explained: {attribution.total_explained_pct}%</Badge>
              </div>
              <Card>
                <CardHeader className="pb-1"><CardTitle className="text-sm">Attribution Breakdown</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={attribution.attributed_changes?.filter(a => a.contribution_pct > 0)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="label" tick={{ fontSize: 9 }} />
                      <YAxis tick={{ fontSize: 10 }} unit="%" />
                      <Tooltip contentStyle={{ fontSize: 11 }} />
                      <Bar dataKey="contribution_pct" name="Contribution %" radius={[3, 3, 0, 0]}>
                        {attribution.attributed_changes?.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </>
          ) : <Empty msg="Run attribution analysis" />}
        </TabsContent>

        {/* Interactions */}
        <TabsContent value="interactions" className="mt-4 space-y-4">
          {loading.interactions ? <Loading /> : interactions?.pairwise_interactions ? (
            <Card>
              <CardHeader className="pb-1"><CardTitle className="text-sm">Parameter Interactions</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {interactions.pairwise_interactions.map((ix, i) => (
                    <div key={i} className="flex items-center gap-3 p-2 border rounded text-xs">
                      <Badge variant="outline" className={
                        ix.interaction_type === 'synergistic' ? 'border-emerald-300 text-emerald-700' :
                        ix.interaction_type === 'antagonistic' ? 'border-red-300 text-red-700' : ''
                      }>{ix.interaction_type}</Badge>
                      <span className="flex-1">{ix.param1} × {ix.param2}</span>
                      <span className="tabular-nums">effect: {ix.interaction_effect?.toFixed(4)}</span>
                      <span className="tabular-nums text-muted-foreground">strength: {ix.interaction_strength?.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ) : <Empty msg="Run interaction analysis" />}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function Loading() {
  return <div className="text-center py-8 text-muted-foreground"><RefreshCw className="h-4 w-4 inline animate-spin mr-2" />Analyzing...</div>;
}
function Empty({ msg }) {
  return <div className="text-center py-12 text-muted-foreground text-sm">{msg}</div>;
}
