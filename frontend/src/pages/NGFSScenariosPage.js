import React, { useEffect, useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Input } from '../components/ui/input';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '../components/ui/sheet';
import { Separator } from '../components/ui/separator';
import { Checkbox } from '../components/ui/checkbox';
import { toast } from 'sonner';
import {
  Thermometer, Leaf, TrendingUp, DollarSign, Globe, Search,
  ChevronRight, BarChart3, RefreshCw, Shield, AlertTriangle, X,
  GitCompare, Play,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, BarChart, Bar, Cell,
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const COLORS = ['#1e40af', '#dc2626', '#059669', '#d97706', '#7c3aed', '#0d9488', '#be123c', '#0284c7', '#4f46e5', '#ca8a04'];
const PHASE_COLORS = { 1: 'bg-blue-100 text-blue-800', 2: 'bg-teal-100 text-teal-800', 3: 'bg-violet-100 text-violet-800' };
const CAT_COLORS = { Orderly: 'bg-emerald-100 text-emerald-800', Disorderly: 'bg-amber-100 text-amber-800',
  'Hot House World': 'bg-red-100 text-red-800', Insufficient: 'bg-orange-100 text-orange-800' };
const RISK_COLORS = { Low: 'text-emerald-600', 'Low-Moderate': 'text-emerald-500', Moderate: 'text-amber-500',
  'Moderate-High': 'text-orange-500', High: 'text-red-500', 'Very High': 'text-red-600', Catastrophic: 'text-red-700', Minimal: 'text-gray-400' };

export default function NGFSScenariosPage() {
  const [scenarios, setScenarios] = useState([]);
  const [meta, setMeta] = useState({});
  const [loading, setLoading] = useState(true);
  const [phaseFilter, setPhaseFilter] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [detailId, setDetailId] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [detailParams, setDetailParams] = useState([]);
  const [compareIds, setCompareIds] = useState([]);
  const [compareData, setCompareData] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);

  const fetchScenarios = async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (phaseFilter) params.set('phase', phaseFilter);
    const r = await fetch(`${API_URL}/api/v1/ngfs-scenarios?${params}`);
    const d = await r.json();
    setScenarios(d.data || []);
    setMeta(d.meta || {});
    setLoading(false);
  };

  useEffect(() => { fetchScenarios(); }, [phaseFilter]); // eslint-disable-line

  const filteredScenarios = useMemo(() => {
    if (!searchQuery.trim()) return scenarios;
    const q = searchQuery.toLowerCase();
    return scenarios.filter(s => s.name.toLowerCase().includes(q) || s.category?.toLowerCase().includes(q) || s.description?.toLowerCase().includes(q));
  }, [scenarios, searchQuery]);

  const openDetail = async (id) => {
    setDetailId(id);
    const [sc, params] = await Promise.all([
      fetch(`${API_URL}/api/v1/ngfs-scenarios/${id}`).then(r => r.json()),
      fetch(`${API_URL}/api/v1/ngfs-scenarios/${id}/parameters`).then(r => r.json()),
    ]);
    setDetailData(sc.data);
    setDetailParams(params.data || []);
  };

  const toggleCompare = (id) => {
    setCompareIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : prev.length < 8 ? [...prev, id] : prev);
  };

  const runCompare = async () => {
    if (compareIds.length < 2) return;
    setCompareLoading(true);
    const r = await fetch(`${API_URL}/api/v1/ngfs-scenarios/compare`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_ids: compareIds }),
    });
    setCompareData((await r.json()).data);
    setCompareLoading(false);
    toast.success('Comparison ready');
  };

  return (
    <div className="p-6 space-y-6" data-testid="ngfs-scenarios-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <Globe className="h-6 w-6 text-primary" />NGFS Scenario Catalog
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {meta.total_scenarios || 0} scenarios across 3 phases — {meta.temperature_range?.min}°C to {meta.temperature_range?.max}°C
          </p>
        </div>
        {compareIds.length >= 2 && (
          <Button onClick={runCompare} disabled={compareLoading} data-testid="compare-btn">
            <GitCompare className="h-4 w-4 mr-1" />{compareLoading ? 'Comparing...' : `Compare ${compareIds.length} Scenarios`}
          </Button>
        )}
      </div>

      {/* Phase tabs + search */}
      <div className="flex items-center gap-3">
        <div className="flex gap-1">
          {[null, 1, 2, 3].map(p => (
            <Button key={p ?? 'all'} size="sm" variant={phaseFilter === p ? 'default' : 'outline'}
              onClick={() => setPhaseFilter(p)} data-testid={`phase-${p ?? 'all'}`}>
              {p ? `Phase ${p}` : 'All'}
            </Button>
          ))}
        </div>
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input placeholder="Search scenarios..." className="pl-9 h-9" value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)} data-testid="ngfs-search" />
        </div>
        {compareIds.length > 0 && (
          <Button size="sm" variant="ghost" onClick={() => setCompareIds([])}><X className="h-3 w-3 mr-1" />Clear ({compareIds.length})</Button>
        )}
      </div>

      <Tabs defaultValue="grid">
        <TabsList>
          <TabsTrigger value="grid" data-testid="tab-grid">Scenarios</TabsTrigger>
          <TabsTrigger value="compare" data-testid="tab-compare" disabled={!compareData}>Comparison</TabsTrigger>
        </TabsList>

        <TabsContent value="grid" className="mt-4">
          {loading ? (
            <div className="text-center py-12 text-muted-foreground"><RefreshCw className="h-5 w-5 inline animate-spin mr-2" />Loading...</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3" data-testid="ngfs-grid">
              {filteredScenarios.map(sc => {
                const isComparing = compareIds.includes(sc.id);
                return (
                  <Card key={sc.id} className={`hover:shadow-md transition-all cursor-pointer group ${isComparing ? 'ring-2 ring-primary' : ''}`}
                    data-testid={`ngfs-card-${sc.slug}`}>
                    <CardContent className="pt-4 pb-3 px-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex gap-1.5">
                          <Badge className={`text-[10px] ${PHASE_COLORS[sc.phase] || ''}`}>P{sc.phase}</Badge>
                          <Badge className={`text-[10px] ${CAT_COLORS[sc.category] || 'bg-gray-100 text-gray-800'}`}>{sc.category}</Badge>
                        </div>
                        <Checkbox checked={isComparing} onCheckedChange={() => toggleCompare(sc.id)} className="h-4 w-4" />
                      </div>
                      <h3 className="font-medium text-sm mb-1 cursor-pointer group-hover:text-primary" onClick={() => openDetail(sc.id)}>{sc.name}</h3>
                      <p className="text-[10px] text-muted-foreground line-clamp-2 mb-2">{sc.description}</p>
                      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-0.5"><Thermometer className="h-3 w-3" />{sc.temperature_by_2100}°C</span>
                        {sc.carbon_neutral_year && <span className="flex items-center gap-0.5"><Leaf className="h-3 w-3" />NZ {sc.carbon_neutral_year}</span>}
                        {sc.physical_risk_level && <span className={`flex items-center gap-0.5 ${RISK_COLORS[sc.physical_risk_level] || ''}`}><Shield className="h-3 w-3" />{sc.physical_risk_level}</span>}
                        {sc.transition_risk_level && <span className={`flex items-center gap-0.5 ${RISK_COLORS[sc.transition_risk_level] || ''}`}><AlertTriangle className="h-3 w-3" />{sc.transition_risk_level}</span>}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="compare" className="mt-4 space-y-4">
          {compareData && (
            <>
              <div className="flex flex-wrap gap-1.5">
                {compareData.scenarios?.map((sc, i) => (
                  <Badge key={sc.id} style={{ backgroundColor: COLORS[i % COLORS.length], color: 'white' }} className="text-xs">{sc.name}</Badge>
                ))}
              </div>
              {Object.entries(compareData.metrics || {}).map(([metric, mdata]) => (
                <ComparisonChart key={metric} metric={metric} data={mdata} scenarios={compareData.scenarios} />
              ))}
            </>
          )}
        </TabsContent>
      </Tabs>

      {/* Detail Sheet */}
      <Sheet open={!!detailId} onOpenChange={v => !v && setDetailId(null)}>
        <SheetContent className="w-[520px] sm:w-[580px] overflow-y-auto p-0" data-testid="ngfs-detail">
          {detailData && (
            <>
              <SheetHeader className="p-5 pb-3 border-b">
                <SheetTitle className="text-lg">{detailData.name}</SheetTitle>
                <div className="flex gap-1.5 mt-1">
                  <Badge className={PHASE_COLORS[detailData.phase]}>Phase {detailData.phase} ({detailData.phase_year})</Badge>
                  <Badge className={CAT_COLORS[detailData.category] || 'bg-gray-100'}>{detailData.category}</Badge>
                </div>
              </SheetHeader>
              <div className="p-5 space-y-4">
                <div className="grid grid-cols-2 gap-2">
                  <MiniCard icon={<Thermometer className="h-3.5 w-3.5 text-orange-500" />} label="Temp 2100" value={`${detailData.temperature_by_2100}°C`} />
                  {detailData.carbon_neutral_year && <MiniCard icon={<Leaf className="h-3.5 w-3.5 text-emerald-500" />} label="Net Zero" value={String(detailData.carbon_neutral_year)} />}
                  {detailData.physical_risk_level && <MiniCard icon={<Shield className="h-3.5 w-3.5 text-blue-500" />} label="Physical Risk" value={detailData.physical_risk_level} />}
                  {detailData.transition_risk_level && <MiniCard icon={<AlertTriangle className="h-3.5 w-3.5 text-amber-500" />} label="Transition Risk" value={detailData.transition_risk_level} />}
                </div>
                <p className="text-sm text-muted-foreground">{detailData.description}</p>
                {detailData.policy_implications && (
                  <div><h4 className="text-xs font-semibold text-muted-foreground mb-1">Policy Implications</h4><p className="text-xs text-muted-foreground">{detailData.policy_implications}</p></div>
                )}
                <Separator />
                {/* Parameter charts */}
                {detailParams.map(param => (
                  <ParameterChart key={param.parameter_name} param={param} />
                ))}
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}

function MiniCard({ icon, label, value }) {
  return (
    <div className="flex items-center gap-2 rounded-md border p-2">
      {icon}
      <div><p className="text-[10px] text-muted-foreground">{label}</p><p className="text-xs font-medium">{value}</p></div>
    </div>
  );
}

function ParameterChart({ param }) {
  const data = param.time_series?.map(t => ({ year: t.year, value: t.value })) || [];
  return (
    <div>
      <h4 className="text-sm font-medium mb-1">{param.display_name} <span className="text-xs text-muted-foreground font-normal">({param.unit})</span></h4>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
          <XAxis dataKey="year" tick={{ fontSize: 9 }} />
          <YAxis tick={{ fontSize: 9 }} />
          <Tooltip contentStyle={{ fontSize: 10, background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: 6 }} />
          <Line type="monotone" dataKey="value" stroke="#1e40af" strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function ComparisonChart({ metric, data, scenarios }) {
  const LABELS = { carbon_price: 'Carbon Price (USD/tCO2)', emissions: 'CO2 Emissions (Gt/yr)', temperature: 'Temperature (°C)', gdp_impact: 'GDP Impact (%)' };
  const series = data.series || {};
  const allYears = new Set();
  Object.values(series).forEach(ts => Object.keys(ts).forEach(y => allYears.add(y)));
  const chartData = [...allYears].sort().map(y => {
    const row = { year: y };
    Object.entries(series).forEach(([name, ts]) => { row[name] = ts[y]; });
    return row;
  });
  const names = Object.keys(series);

  return (
    <Card>
      <CardHeader className="pb-1"><CardTitle className="text-sm">{LABELS[metric] || metric}</CardTitle></CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="year" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip contentStyle={{ fontSize: 10, background: 'hsl(var(--card))', border: '1px solid hsl(var(--border))', borderRadius: 6 }} />
            <Legend wrapperStyle={{ fontSize: 9 }} />
            {names.map((name, i) => (
              <Line key={name} type="monotone" dataKey={name} stroke={COLORS[i % COLORS.length]} strokeWidth={1.5} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
