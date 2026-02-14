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
  RefreshCw, BarChart3, AlertTriangle, Leaf,
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

        {/* Cost Projections */}
        <TabsContent value="projections" className="mt-4 space-y-4">
          {projections.length === 0 ? (
            <p className="text-center py-8 text-muted-foreground text-sm">Select a supplier to see cost projections</p>
          ) : (
            <>
              <Card>
                <CardHeader className="pb-1"><CardTitle className="text-sm">CBAM Cost Projection — {projections[0]?.supplier_name}</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={(() => {
                      const years = [...new Set(projections.map(p => p.year))].sort();
                      return years.map(y => {
                        const row = { year: y };
                        projections.filter(p => p.year === y).forEach(p => { row[p.scenario] = p.net_cbam_cost_eur; });
                        return row;
                      });
                    })()}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `€${(v/1000).toFixed(0)}K`} />
                      <Tooltip formatter={v => [`€${v?.toLocaleString()}`, '']} />
                      <Legend wrapperStyle={{ fontSize: 10 }} />
                      {['Current Trend', 'Ambitious', 'Conservative'].map((s, i) => (
                        <Bar key={s} dataKey={s} fill={COLORS[i]} radius={[2, 2, 0, 0]} />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4 overflow-auto max-h-[300px]">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Year</TableHead><TableHead>Scenario</TableHead><TableHead className="text-right">Volume (t)</TableHead>
                        <TableHead className="text-right">Emissions (tCO2)</TableHead><TableHead className="text-right">ETS Price</TableHead>
                        <TableHead className="text-right">Free Alloc %</TableHead><TableHead className="text-right">Net CBAM Cost</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {projections.slice(0, 30).map((p, i) => (
                        <TableRow key={i}>
                          <TableCell className="text-xs">{p.year}</TableCell>
                          <TableCell className="text-xs">{p.scenario}</TableCell>
                          <TableCell className="text-right tabular-nums text-xs">{p.import_volume_tonnes?.toLocaleString()}</TableCell>
                          <TableCell className="text-right tabular-nums text-xs">{p.embedded_emissions_tco2?.toLocaleString()}</TableCell>
                          <TableCell className="text-right tabular-nums text-xs">€{p.eu_ets_price_eur}</TableCell>
                          <TableCell className="text-right tabular-nums text-xs">{p.free_allocation_pct}%</TableCell>
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
