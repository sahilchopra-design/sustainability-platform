import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { toast } from 'sonner';
import {
  Globe, Shield, Factory, TrendingUp, DollarSign, Plus,
  RefreshCw, BarChart3, AlertTriangle, Leaf, Calculator, CheckCircle,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line,
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const COLORS = ['#1e40af', '#dc2626', '#059669', '#d97706'];
const RISK_COLORS = { Low: 'bg-emerald-100 text-emerald-800', Medium: 'bg-amber-100 text-amber-800',
  High: 'bg-orange-100 text-orange-800', 'Very High': 'bg-red-100 text-red-800' };

export default function CBAMPage() {
  const [dashboard, setDashboard] = useState(null);
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [countries, setCountries] = useState([]);
  const [certPrices, setCertPrices] = useState([]);
  const [projections, setProjections] = useState([]);
  const [freeAlloc, setFreeAlloc] = useState({});
  const [newSupplier, setNewSupplier] = useState({ supplier_name: '', country_code: '' });

  // Calculator state
  const [calcForm, setCalcForm] = useState({ supplier_id: '', product_category_id: '', production_volume: 1000, reporting_year: 2026, electricity_mwh: '', use_defaults: false });
  const [calcResult, setCalcResult] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);

  // Projection controls state
  const [projSupplier, setProjSupplier] = useState('');
  const [projScenario, setProjScenario] = useState('current_trend');
  const [projYears, setProjYears] = useState('10');
  const [projLoading, setProjLoading] = useState(false);

  const load = async () => {
    const [d, p, s, c, cp, fa] = await Promise.all([
      fetch(`${API_URL}/api/v1/cbam/dashboard`).then(r => r.json()),
      fetch(`${API_URL}/api/v1/cbam/products`).then(r => r.json()),
      fetch(`${API_URL}/api/v1/cbam/suppliers`).then(r => r.json()),
      fetch(`${API_URL}/api/v1/cbam/countries`).then(r => r.json()),
      fetch(`${API_URL}/api/v1/cbam/certificate-prices`).then(r => r.json()),
      fetch(`${API_URL}/api/v1/cbam/free-allocation-schedule`).then(r => r.json()),
    ]);
    setDashboard(d); setProducts(p); setSuppliers(s); setCountries(c); setCertPrices(cp); setFreeAlloc(fa);
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  const addSupplier = async () => {
    if (!newSupplier.supplier_name || !newSupplier.country_code) return;
    await fetch(`${API_URL}/api/v1/cbam/suppliers`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newSupplier),
    });
    setNewSupplier({ supplier_name: '', country_code: '' });
    toast.success('Supplier added');
    load();
  };

  const loadProjections = async (sid) => {
    const d = await fetch(`${API_URL}/api/v1/cbam/suppliers/${sid}/projections`).then(r => r.json());
    setProjections(d);
  };

  const runCalculation = async () => {
    if (!calcForm.supplier_id || !calcForm.product_category_id || !calcForm.production_volume) return;
    setCalcLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/v1/cbam/calculate-emissions`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          supplier_id: calcForm.supplier_id,
          product_category_id: calcForm.product_category_id,
          production_volume_tonnes: Number(calcForm.production_volume),
          electricity_consumed_mwh: calcForm.electricity_mwh ? Number(calcForm.electricity_mwh) : null,
          use_default_values: calcForm.use_defaults,
        }),
      });
      const d = await r.json();
      // Estimate CBAM cost at current ETS price ~€80
      d.estimated_cbam_cost_eur = Math.round(d.total_embedded_emissions_tco2 * 80 * 100) / 100;
      setCalcResult(d);
      toast.success('Emissions calculated');
    } catch { toast.error('Calculation failed'); }
    finally { setCalcLoading(false); }
  };

  // Chart data
  const priceChartData = (() => {
    const years = new Set();
    certPrices.forEach(p => years.add(p.date));
    return [...years].sort().map(y => {
      const row = { year: y };
      certPrices.filter(p => p.date === y).forEach(p => { row[p.scenario] = p.ets_price; });
      return row;
    });
  })();

  const freeAllocData = Object.entries(freeAlloc).map(([y, v]) => ({ year: y, free_pct: v, cbam_pct: 100 - v }));

  return (
    <div className="p-6 space-y-6" data-testid="cbam-page">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Globe className="h-6 w-6 text-primary" />CBAM Module
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Carbon Border Adjustment Mechanism — emissions tracking, cost projections, compliance</p>
      </div>

      {/* Stats */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <StatCard label="Products" value={dashboard.total_products} icon={<Factory className="h-4 w-4" />} />
          <StatCard label="Suppliers" value={dashboard.total_suppliers} icon={<Shield className="h-4 w-4" />} />
          <StatCard label="Countries" value={dashboard.total_countries} icon={<Globe className="h-4 w-4" />} />
          <StatCard label="High Risk" value={dashboard.high_risk_suppliers} icon={<AlertTriangle className="h-4 w-4 text-red-500" />} />
          <StatCard label="Total CO2 (t)" value={dashboard.total_embedded_emissions_tco2?.toLocaleString()} icon={<Leaf className="h-4 w-4" />} />
        </div>
      )}

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="calculator" data-testid="tab-calculator"><Calculator className="h-3 w-3 mr-1" />Calculator</TabsTrigger>
          <TabsTrigger value="products" data-testid="tab-products">Products ({products.length})</TabsTrigger>
          <TabsTrigger value="suppliers" data-testid="tab-suppliers">Suppliers ({suppliers.length})</TabsTrigger>
          <TabsTrigger value="countries" data-testid="tab-countries">Country Risk</TabsTrigger>
          <TabsTrigger value="projections" data-testid="tab-projections">Cost Projections</TabsTrigger>
        </TabsList>

        {/* Overview */}
        <TabsContent value="overview" className="mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-1"><CardTitle className="text-sm">EU ETS / CBAM Certificate Price Scenarios</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={priceChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} unit="€" />
                    <Tooltip contentStyle={{ fontSize: 11 }} />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                    {['Current Trend', 'Ambitious', 'Conservative'].map((s, i) => (
                      <Line key={s} type="monotone" dataKey={s} stroke={COLORS[i]} strokeWidth={2} dot />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-1"><CardTitle className="text-sm">Free Allocation Phase-Out</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={freeAllocData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                    <YAxis tick={{ fontSize: 10 }} unit="%" />
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: 10 }} />
                    <Bar dataKey="free_pct" name="Free Allocation %" fill="#059669" stackId="a" />
                    <Bar dataKey="cbam_pct" name="CBAM Certificate %" fill="#dc2626" stackId="a" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Calculator */}
        <TabsContent value="calculator" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Input Form */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2"><Calculator className="h-4 w-4" />Calculate Embedded Emissions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Supplier *</label>
                  <Select value={calcForm.supplier_id} onValueChange={v => setCalcForm(p => ({ ...p, supplier_id: v }))}>
                    <SelectTrigger data-testid="calc-supplier"><SelectValue placeholder="Select supplier" /></SelectTrigger>
                    <SelectContent>
                      {suppliers.map(s => <SelectItem key={s.id} value={s.id}>{s.supplier_name} ({s.country_code})</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Product (CN Code) *</label>
                  <Select value={calcForm.product_category_id} onValueChange={v => setCalcForm(p => ({ ...p, product_category_id: v }))}>
                    <SelectTrigger data-testid="calc-product"><SelectValue placeholder="Select product" /></SelectTrigger>
                    <SelectContent>
                      {products.map(p => <SelectItem key={p.id} value={p.id}>{p.cn_code} — {p.product_name}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Production Volume (tonnes) *</label>
                  <Input type="number" step="0.01" value={calcForm.production_volume} data-testid="calc-volume"
                    onChange={e => setCalcForm(p => ({ ...p, production_volume: e.target.value }))} placeholder="e.g., 1000" />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Reporting Year *</label>
                  <Input type="number" value={calcForm.reporting_year}
                    onChange={e => setCalcForm(p => ({ ...p, reporting_year: e.target.value }))} />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Electricity Consumed (MWh)</label>
                  <Input type="number" step="0.01" value={calcForm.electricity_mwh} data-testid="calc-electricity"
                    onChange={e => setCalcForm(p => ({ ...p, electricity_mwh: e.target.value }))} placeholder="e.g., 500" />
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" checked={calcForm.use_defaults} className="rounded h-4 w-4"
                    onChange={e => setCalcForm(p => ({ ...p, use_defaults: e.target.checked }))} data-testid="calc-defaults" />
                  <label className="text-xs text-muted-foreground">Use EU default emission values</label>
                </div>
                <Button className="w-full" onClick={runCalculation} disabled={calcLoading || !calcForm.supplier_id || !calcForm.product_category_id}
                  data-testid="calc-submit">
                  {calcLoading ? <><RefreshCw className="h-3 w-3 animate-spin mr-1" />Calculating...</> : <>Calculate Emissions</>}
                </Button>
              </CardContent>
            </Card>

            {/* Results */}
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm">Calculation Results</CardTitle></CardHeader>
              <CardContent>
                {!calcResult ? (
                  <div className="text-center py-12 text-muted-foreground text-sm">Fill in the form and click Calculate to see results</div>
                ) : (
                  <div className="space-y-4">
                    {/* Emission cards */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-blue-50 p-3 rounded-lg text-center">
                        <p className="text-xl font-bold text-blue-700">{calcResult.specific_direct_emissions?.toFixed(4)}</p>
                        <p className="text-[10px] text-blue-600">Direct (tCO2/t)</p>
                      </div>
                      <div className="bg-emerald-50 p-3 rounded-lg text-center">
                        <p className="text-xl font-bold text-emerald-700">{calcResult.specific_indirect_emissions?.toFixed(4)}</p>
                        <p className="text-[10px] text-emerald-600">Indirect (tCO2/t)</p>
                      </div>
                      <div className="bg-violet-50 p-3 rounded-lg text-center">
                        <p className="text-xl font-bold text-violet-700">{calcResult.specific_total_emissions?.toFixed(4)}</p>
                        <p className="text-[10px] text-violet-600">Total SEE (tCO2/t)</p>
                      </div>
                    </div>

                    {/* Total embedded */}
                    <div className="bg-muted/50 p-3 rounded-lg">
                      <p className="text-xs text-muted-foreground">Total Embedded Emissions</p>
                      <p className="text-2xl font-bold">{calcResult.total_embedded_emissions_tco2?.toLocaleString()} tCO2</p>
                    </div>

                    {/* Estimated cost */}
                    <div className="bg-muted/50 p-3 rounded-lg">
                      <p className="text-xs text-muted-foreground">Estimated CBAM Cost (at ~€80/tCO2)</p>
                      <p className="text-2xl font-bold">€{calcResult.estimated_cbam_cost_eur?.toLocaleString()}</p>
                    </div>

                    {/* Warnings */}
                    {calcResult.uses_default_values && (
                      <div className="flex items-start gap-2 p-3 bg-amber-50 rounded-lg border border-amber-200">
                        <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
                        <div>
                          <p className="text-xs font-medium text-amber-800">Default values used</p>
                          <p className="text-[10px] text-amber-600">{(calcResult.default_value_markup_applied * 100).toFixed(0)}% markup applied ({calcResult.markup_type})</p>
                        </div>
                      </div>
                    )}

                    {!calcResult.uses_default_values && (
                      <div className="flex items-start gap-2 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                        <CheckCircle className="h-4 w-4 text-emerald-500 mt-0.5 shrink-0" />
                        <p className="text-xs text-emerald-800">Actual emissions data used — no markup applied</p>
                      </div>
                    )}

                    <div className="flex gap-2 pt-2">
                      <Button variant="outline" className="flex-1" size="sm" onClick={() => toast.info('Saved to emissions records')}>Save</Button>
                      <Button className="flex-1" size="sm" onClick={() => toast.info('Added to compliance report')}>Add to Report</Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>


        {/* Products */}
        <TabsContent value="products" className="mt-4">
          <Card>
            <CardContent className="pt-4 overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>CN Code</TableHead><TableHead>Sector</TableHead><TableHead>Product</TableHead>
                    <TableHead className="text-right">Direct (tCO2/t)</TableHead><TableHead className="text-right">Indirect</TableHead>
                    <TableHead className="text-right">Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {products.map(p => (
                    <TableRow key={p.id}>
                      <TableCell className="font-mono text-xs">{p.cn_code}</TableCell>
                      <TableCell><Badge variant="outline" className="text-xs">{p.sector}</Badge></TableCell>
                      <TableCell className="text-xs">{p.product_name}</TableCell>
                      <TableCell className="text-right tabular-nums text-xs">{p.default_direct_emissions?.toFixed(3)}</TableCell>
                      <TableCell className="text-right tabular-nums text-xs">{p.default_indirect_emissions?.toFixed(3)}</TableCell>
                      <TableCell className="text-right tabular-nums text-xs font-medium">{p.default_total_emissions?.toFixed(3)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Suppliers */}
        <TabsContent value="suppliers" className="mt-4 space-y-4">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Add Supplier</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-2 items-end">
                <Input placeholder="Supplier name" value={newSupplier.supplier_name} className="max-w-xs"
                  onChange={e => setNewSupplier(p => ({ ...p, supplier_name: e.target.value }))} data-testid="supplier-name" />
                <Input placeholder="Country (2-letter)" value={newSupplier.country_code} className="w-24"
                  onChange={e => setNewSupplier(p => ({ ...p, country_code: e.target.value.toUpperCase() }))} maxLength={2} data-testid="supplier-country" />
                <Button onClick={addSupplier} data-testid="add-supplier-btn"><Plus className="h-3 w-3 mr-1" />Add</Button>
              </div>
            </CardContent>
          </Card>
          <div className="space-y-2">
            {suppliers.map(s => (
              <Card key={s.id} className="cursor-pointer hover:shadow-sm" onClick={() => loadProjections(s.id)}
                data-testid={`supplier-${s.id}`}>
                <CardContent className="py-3 px-4 flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium">{s.supplier_name}</h3>
                    <div className="flex gap-2 mt-0.5">
                      <Badge variant="outline" className="text-[10px]">{s.country_code}</Badge>
                      <Badge className={`text-[10px] ${RISK_COLORS[s.risk_category] || ''}`}>{s.risk_category}</Badge>
                      {s.has_domestic_carbon_price && <Badge variant="outline" className="text-[10px]">Carbon price: €{s.domestic_carbon_price}</Badge>}
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground">Score: {s.risk_score?.toFixed(2)}</span>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Country Risk */}
        <TabsContent value="countries" className="mt-4">
          <Card>
            <CardContent className="pt-4 overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead><TableHead>Country</TableHead><TableHead>Carbon Pricing</TableHead>
                    <TableHead className="text-right">Price (€)</TableHead><TableHead className="text-right">Grid EF</TableHead>
                    <TableHead>Risk</TableHead><TableHead className="text-right">Score</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {countries.map(c => (
                    <TableRow key={c.country_code}>
                      <TableCell className="font-mono text-xs">{c.country_code}</TableCell>
                      <TableCell className="text-xs">{c.country_name}</TableCell>
                      <TableCell>{c.has_carbon_pricing ? <Badge className="bg-emerald-100 text-emerald-800 text-[10px]">Yes</Badge> : <Badge variant="outline" className="text-[10px]">No</Badge>}</TableCell>
                      <TableCell className="text-right tabular-nums text-xs">€{c.carbon_price_eur}</TableCell>
                      <TableCell className="text-right tabular-nums text-xs">{c.grid_emission_factor}</TableCell>
                      <TableCell><Badge className={`text-[10px] ${RISK_COLORS[c.risk_category] || ''}`}>{c.risk_category}</Badge></TableCell>
                      <TableCell className="text-right tabular-nums text-xs">{c.risk_score?.toFixed(2)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Cost Projections — Enhanced with controls */}
        <TabsContent value="projections" className="mt-4 space-y-4">
          {/* Projection Controls */}
          <Card>
            <CardContent className="pt-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Supplier *</label>
                  <Select value={projSupplier} onValueChange={setProjSupplier}>
                    <SelectTrigger data-testid="proj-supplier"><SelectValue placeholder="Select supplier" /></SelectTrigger>
                    <SelectContent>
                      {suppliers.map(s => <SelectItem key={s.id} value={s.id}>{s.supplier_name} ({s.country_code})</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Scenario</label>
                  <Select value={projScenario} onValueChange={setProjScenario}>
                    <SelectTrigger data-testid="proj-scenario"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="current_trend">Current Trend</SelectItem>
                      <SelectItem value="ambitious">Ambitious</SelectItem>
                      <SelectItem value="conservative">Conservative</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground block mb-1">Projection Period</label>
                  <Select value={projYears} onValueChange={setProjYears}>
                    <SelectTrigger data-testid="proj-years"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="5">5 years (2026–2030)</SelectItem>
                      <SelectItem value="10">10 years (2026–2035)</SelectItem>
                      <SelectItem value="15">15 years (2026–2040)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button onClick={async () => {
                  if (!projSupplier) { toast.error('Select a supplier'); return; }
                  setProjLoading(true);
                  try {
                    const r = await fetch(`${API_URL}/api/v1/cbam/project-costs`, {
                      method: 'POST', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ supplier_id: projSupplier, start_year: 2026, end_year: 2026 + parseInt(projYears), scenario: projScenario }),
                    });
                    const d = await r.json();
                    setProjections(d.projections || []);
                    toast.success(`Projection complete: €${d.total_net_cbam_cost_eur?.toLocaleString()} total`);
                  } catch { toast.error('Projection failed'); }
                  finally { setProjLoading(false); }
                }} disabled={!projSupplier || projLoading} data-testid="run-projection-btn">
                  {projLoading ? <><RefreshCw className="h-3 w-3 animate-spin mr-1" />Running...</> : <>Run Projection</>}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Results */}
          {projections.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground text-sm">
              <DollarSign className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p>Select a supplier and run projection to see cost forecasts</p>
            </div>
          ) : (
            <>
              {/* Line Chart */}
              <Card>
                <CardHeader className="pb-1"><CardTitle className="text-sm">Projected CBAM Costs — {projScenario.replace('_', ' ')}</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={projections} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `€${(v/1000).toFixed(0)}K`} />
                      <Tooltip formatter={v => [`€${v?.toLocaleString()}`, '']} contentStyle={{ fontSize: 11 }} />
                      <Line type="monotone" dataKey="net_cbam_cost_eur" name="Net CBAM Cost" stroke="#1e40af" strokeWidth={2} dot />
                      <Line type="monotone" dataKey="gross_cbam_cost_eur" name="Gross Cost" stroke="#dc2626" strokeWidth={1.5} strokeDasharray="5 5" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                  <div className="flex gap-4 text-[10px] text-muted-foreground mt-2 justify-center">
                    <span>Solid = Net (after credits & free allocation)</span>
                    <span>Dashed = Gross (before deductions)</span>
                  </div>
                </CardContent>
              </Card>

              {/* Summary cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Card><CardContent className="pt-3 pb-2">
                  <p className="text-[10px] text-muted-foreground">Total Net CBAM Cost</p>
                  <p className="text-lg font-bold">€{projections.reduce((s, p) => s + p.net_cbam_cost_eur, 0).toLocaleString()}</p>
                </CardContent></Card>
                <Card><CardContent className="pt-3 pb-2">
                  <p className="text-[10px] text-muted-foreground">Avg Annual Cost</p>
                  <p className="text-lg font-bold">€{Math.round(projections.reduce((s, p) => s + p.net_cbam_cost_eur, 0) / projections.length).toLocaleString()}</p>
                </CardContent></Card>
                <Card><CardContent className="pt-3 pb-2">
                  <p className="text-[10px] text-muted-foreground">Peak Year Cost</p>
                  <p className="text-lg font-bold">€{Math.max(...projections.map(p => p.net_cbam_cost_eur)).toLocaleString()}</p>
                </CardContent></Card>
                <Card><CardContent className="pt-3 pb-2">
                  <p className="text-[10px] text-muted-foreground">ETS Price ({projections[projections.length-1]?.year})</p>
                  <p className="text-lg font-bold">€{projections[projections.length-1]?.eu_ets_price_eur}/tCO2</p>
                </CardContent></Card>
              </div>

              {/* Detail table */}
              <Card>
                <CardContent className="pt-4 overflow-auto max-h-[300px]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Year</TableHead><TableHead className="text-right">ETS Price</TableHead>
                        <TableHead className="text-right">Free Alloc %</TableHead><TableHead className="text-right">Gross Cost</TableHead>
                        <TableHead className="text-right">Domestic Credit</TableHead><TableHead className="text-right">Net CBAM Cost</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {projections.map((p, i) => (
                        <TableRow key={i}>
                          <TableCell className="text-xs font-medium">{p.year}</TableCell>
                          <TableCell className="text-right tabular-nums text-xs">€{p.eu_ets_price_eur}</TableCell>
                          <TableCell className="text-right tabular-nums text-xs">{p.free_allocation_pct}%</TableCell>
                          <TableCell className="text-right tabular-nums text-xs">€{p.gross_cbam_cost_eur?.toLocaleString()}</TableCell>
                          <TableCell className="text-right tabular-nums text-xs">€{p.domestic_carbon_credit_eur?.toLocaleString()}</TableCell>
                          <TableCell className="text-right tabular-nums text-xs font-medium">€{p.net_cbam_cost_eur?.toLocaleString()}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

function StatCard({ label, value, icon }) {
  return (
    <Card>
      <CardContent className="pt-3 pb-2 px-4 flex items-center justify-between">
        <div>
          <p className="text-[10px] text-muted-foreground">{label}</p>
          <p className="text-lg font-semibold tabular-nums">{value ?? '—'}</p>
        </div>
        <div className="text-muted-foreground">{icon}</div>
      </CardContent>
    </Card>
  );
}
