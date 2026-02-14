import React, { useEffect, useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Separator } from '../components/ui/separator';
import { toast } from 'sonner';
import {
  Calculator, Play, RefreshCw, TrendingUp, AlertTriangle,
  DollarSign, Shield, BarChart3, Layers, Download, FileText, Table2,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, Cell,
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const COLORS = ['#1e40af', '#dc2626', '#059669', '#d97706', '#7c3aed'];

export default function ImpactCalculatorPage() {
  const [portfolios, setPortfolios] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState('');
  const [selectedScenario, setSelectedScenario] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/api/portfolios`).then(r => r.json()).then(d => setPortfolios(d.portfolios || []));
    fetch(`${API_URL}/api/v1/data-hub/scenarios?limit=200`).then(r => r.json()).then(d => setScenarios(d.scenarios || []));
  }, []);

  const handleCalculate = async () => {
    if (!selectedPortfolio || !selectedScenario) return;
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/v1/analysis/impact`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_id: selectedScenario, portfolio_id: selectedPortfolio }),
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
      toast.success('Impact calculated');
    } catch (e) { toast.error('Calculation failed: ' + e.message); }
    finally { setLoading(false); }
  };

  const portfolio = portfolios.find(p => p.id === selectedPortfolio);
  const scenario = scenarios.find(s => s.id === selectedScenario);

  return (
    <div className="p-6 space-y-6" data-testid="impact-calculator-page">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
          <Calculator className="h-6 w-6 text-primary" />
          Scenario Impact Calculator
        </h1>
        <p className="text-sm text-muted-foreground mt-1">Calculate how climate scenarios affect your portfolio's risk metrics</p>
      </div>

      {/* Selectors */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <label className="text-xs font-medium text-muted-foreground block mb-1.5">Portfolio</label>
            <Select value={selectedPortfolio} onValueChange={setSelectedPortfolio}>
              <SelectTrigger data-testid="portfolio-select"><SelectValue placeholder="Select portfolio..." /></SelectTrigger>
              <SelectContent>
                {portfolios.filter(p => p.num_assets > 0).map(p => (
                  <SelectItem key={p.id} value={p.id}>{p.name} ({p.num_assets} assets)</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {portfolio && <p className="text-xs text-muted-foreground mt-1">${portfolio.total_exposure?.toLocaleString()} total exposure</p>}
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <label className="text-xs font-medium text-muted-foreground block mb-1.5">Scenario</label>
            <Select value={selectedScenario} onValueChange={setSelectedScenario}>
              <SelectTrigger data-testid="scenario-select"><SelectValue placeholder="Select scenario..." /></SelectTrigger>
              <SelectContent>
                {scenarios.slice(0, 50).map(s => (
                  <SelectItem key={s.id} value={s.id}>{s.display_name || s.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {scenario && (
              <div className="flex gap-1 mt-1">
                <Badge variant="secondary" className="text-[9px]">{scenario.source_name}</Badge>
                {scenario.temperature_target && <Badge variant="outline" className="text-[9px]">{scenario.temperature_target}°C</Badge>}
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 flex flex-col justify-between h-full">
            <label className="text-xs font-medium text-muted-foreground block mb-1.5">Calculate</label>
            <Button onClick={handleCalculate} disabled={!selectedPortfolio || !selectedScenario || loading}
              className="w-full" data-testid="calculate-btn">
              {loading ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
              {loading ? 'Calculating...' : 'Run Impact Analysis'}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Results */}
      {result && (
        <>
          <Separator />
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">Impact Results</h2>
            <Badge>{result.scenario_name}</Badge>
            <Badge variant="outline">{result.engine_scenario}</Badge>
          </div>

          {/* Metrics cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {result.horizons.map(h => (
              <Card key={h.horizon}>
                <CardContent className="pt-3 pb-2">
                  <p className="text-xs text-muted-foreground">{h.horizon} Expected Loss</p>
                  <p className="text-xl font-semibold tabular-nums">${h.expected_loss?.toLocaleString()}</p>
                  <p className="text-xs text-muted-foreground">{(h.expected_loss_pct * 100).toFixed(1)}% of exposure</p>
                </CardContent>
              </Card>
            ))}
            {result.horizons.length > 0 && (
              <Card>
                <CardContent className="pt-3 pb-2">
                  <p className="text-xs text-muted-foreground">{result.horizons[result.horizons.length - 1].horizon} VaR 95%</p>
                  <p className="text-xl font-semibold tabular-nums text-red-600">
                    ${result.horizons[result.horizons.length - 1].var_95?.toLocaleString()}
                  </p>
                  <p className="text-xs text-muted-foreground">PD change: {result.horizons[result.horizons.length - 1].avg_pd_change_pct}%</p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-1"><CardTitle className="text-sm">Expected Loss by Horizon</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={result.horizons.map(h => ({ horizon: String(h.horizon), el: h.expected_loss, var95: h.var_95 }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="horizon" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `$${(v / 1e6).toFixed(1)}M`} />
                    <Tooltip formatter={v => [`$${v?.toLocaleString()}`, '']} />
                    <Legend />
                    <Bar dataKey="el" name="Expected Loss" fill="#1e40af" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="var95" name="VaR 95%" fill="#dc2626" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-1"><CardTitle className="text-sm">PD Change by Horizon</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={result.horizons.map(h => ({ horizon: String(h.horizon), pd_change: h.avg_pd_change_pct, el_pct: h.expected_loss_pct * 100 }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="horizon" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 10 }} unit="%" />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="pd_change" name="PD Change %" stroke="#d97706" strokeWidth={2} dot />
                    <Line type="monotone" dataKey="el_pct" name="EL % of Exposure" stroke="#dc2626" strokeWidth={2} dot />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Multipliers */}
          {result.multipliers && (
            <Card>
              <CardHeader className="pb-1"><CardTitle className="text-sm">Scenario Multipliers</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  {result.multipliers.carbon_price_2030 != null && (
                    <div><span className="text-xs text-muted-foreground">Carbon Price 2030</span><p className="font-medium">${result.multipliers.carbon_price_2030?.toFixed(1)}/tCO2</p></div>
                  )}
                  {result.multipliers.carbon_price_2050 != null && (
                    <div><span className="text-xs text-muted-foreground">Carbon Price 2050</span><p className="font-medium">${result.multipliers.carbon_price_2050?.toFixed(1)}/tCO2</p></div>
                  )}
                  {result.multipliers.emissions_change_pct != null && (
                    <div><span className="text-xs text-muted-foreground">Emissions Change</span><p className="font-medium">{result.multipliers.emissions_change_pct > 0 ? '+' : ''}{result.multipliers.emissions_change_pct}%</p></div>
                  )}
                  {result.multipliers.temperature_2050 != null && (
                    <div><span className="text-xs text-muted-foreground">Temp 2050</span><p className="font-medium">{result.multipliers.temperature_2050?.toFixed(2)}°C</p></div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
