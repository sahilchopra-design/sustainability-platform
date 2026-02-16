/**
 * Sensitivity Analysis Component
 * Interactive tornado and spider chart visualizations
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Badge } from '../../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Checkbox } from '../../../components/ui/checkbox';
import { useSensitivityAnalysis, useProperties, useSensitivityPresets } from '../hooks/useScenarios';
import { BarChart3, Activity, TrendingUp, TrendingDown, Settings2, Play } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend,
} from 'recharts';

const defaultVariables = [
  { name: 'cap_rate', label: 'Cap Rate', base: 0.055, min: 0.04, max: 0.07, selected: true },
  { name: 'rent_growth', label: 'Rent Growth', base: 0.025, min: 0.01, max: 0.04, selected: true },
  { name: 'vacancy_rate', label: 'Vacancy Rate', base: 0.05, min: 0.02, max: 0.10, selected: true },
  { name: 'expense_ratio', label: 'Expense Ratio', base: 0.35, min: 0.28, max: 0.42, selected: false },
  { name: 'exit_cap_rate', label: 'Exit Cap', base: 0.06, min: 0.045, max: 0.075, selected: false },
  { name: 'discount_rate', label: 'Discount Rate', base: 0.08, min: 0.06, max: 0.10, selected: false },
];

const formatCurrency = (value) => {
  if (!value) return '$0';
  const num = parseFloat(value);
  if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
  return `$${num.toLocaleString()}`;
};

export function SensitivityAnalysis() {
  const [selectedProperty, setSelectedProperty] = useState('');
  const [variables, setVariables] = useState(defaultVariables);
  const [result, setResult] = useState(null);

  const { data: propertiesData } = useProperties();
  const { data: presetsData } = useSensitivityPresets();
  const analysisMutation = useSensitivityAnalysis();

  const properties = propertiesData?.properties || [];
  const presets = presetsData?.presets || [];

  const toggleVariable = (name) => {
    setVariables(variables.map(v => 
      v.name === name ? { ...v, selected: !v.selected } : v
    ));
  };

  const updateVariable = (name, field, value) => {
    setVariables(variables.map(v =>
      v.name === name ? { ...v, [field]: parseFloat(value) } : v
    ));
  };

  const handleAnalyze = () => {
    if (!selectedProperty) return;
    
    const selectedVars = variables.filter(v => v.selected);
    
    analysisMutation.mutate({
      property_id: selectedProperty,
      variables: selectedVars.map(v => ({
        name: v.name,
        base_value: v.base,
        range: { min: v.min, max: v.max },
        steps: 10,
      })),
    }, {
      onSuccess: (data) => setResult(data),
    });
  };

  const applyPreset = (preset) => {
    setVariables(defaultVariables.map(v => {
      const presetVar = preset.variables.find(pv => pv.name === v.name);
      if (presetVar) {
        return { ...v, base: presetVar.base, min: presetVar.low, max: presetVar.high, selected: true };
      }
      return { ...v, selected: false };
    }));
  };

  // Prepare tornado chart data
  const tornadoData = result?.tornado_data?.map(t => ({
    variable: t.variable,
    positive: parseFloat(t.high_impact),
    negative: parseFloat(t.low_impact),
    swing: parseFloat(t.swing),
  })) || [];

  // Prepare spider chart data
  const spiderData = result?.spider_chart_data?.variables?.map((v, i) => {
    const obj = { variable: v };
    result.spider_chart_data.scenarios.forEach((s) => {
      obj[s.name] = s.values[i];
    });
    return obj;
  }) || [];

  return (
    <div className="space-y-6">
      {/* Configuration */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Settings2 className="h-4 w-4 text-violet-600" />
              Sensitivity Variables
            </CardTitle>
            <CardDescription>
              Select variables and configure ranges for analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <Label>Base Property</Label>
              <Select value={selectedProperty} onValueChange={setSelectedProperty}>
                <SelectTrigger data-testid="sensitivity-property-select">
                  <SelectValue placeholder="Select property..." />
                </SelectTrigger>
                <SelectContent>
                  {properties.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name} ({formatCurrency(p.current_value)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              {variables.map((v) => (
                <div key={v.name} className={`flex items-center gap-3 p-3 rounded-lg ${
                  v.selected ? 'bg-violet-50 border border-violet-200' : 'bg-slate-50'
                }`}>
                  <Checkbox
                    checked={v.selected}
                    onCheckedChange={() => toggleVariable(v.name)}
                  />
                  <span className="w-28 text-sm font-medium">{v.label}</span>
                  <div className="flex items-center gap-2 flex-1">
                    <Input
                      type="number"
                      step="0.001"
                      className="w-20 h-8 text-xs"
                      value={v.min}
                      onChange={(e) => updateVariable(v.name, 'min', e.target.value)}
                      disabled={!v.selected}
                    />
                    <span className="text-slate-400">to</span>
                    <Input
                      type="number"
                      step="0.001"
                      className="w-20 h-8 text-xs"
                      value={v.max}
                      onChange={(e) => updateVariable(v.name, 'max', e.target.value)}
                      disabled={!v.selected}
                    />
                    <span className="text-xs text-slate-500">(base: {v.base})</span>
                  </div>
                </div>
              ))}
            </div>

            <Button
              className="w-full mt-4 bg-violet-600 hover:bg-violet-700"
              onClick={handleAnalyze}
              disabled={analysisMutation.isPending || !selectedProperty || !variables.some(v => v.selected)}
              data-testid="run-sensitivity-btn"
            >
              <Play className="h-4 w-4 mr-2" />
              {analysisMutation.isPending ? 'Analyzing...' : 'Run Sensitivity Analysis'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Quick Presets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {presets.map((p) => (
                <Button
                  key={p.name}
                  variant="outline"
                  size="sm"
                  className="w-full justify-start text-xs"
                  onClick={() => applyPreset(p)}
                >
                  <Activity className="h-3 w-3 mr-2 text-violet-500" />
                  {p.name}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Results */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Tornado Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-blue-600" />
                Tornado Chart
              </CardTitle>
              <CardDescription>
                Impact of each variable on valuation (% change from base)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    layout="vertical"
                    data={tornadoData}
                    margin={{ top: 20, right: 30, left: 80, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" domain={[-30, 30]} tickFormatter={(v) => `${v}%`} />
                    <YAxis type="category" dataKey="variable" />
                    <Tooltip 
                      formatter={(value) => [`${value.toFixed(1)}%`, 'Impact']}
                      labelStyle={{ fontWeight: 'bold' }}
                    />
                    <ReferenceLine x={0} stroke="#666" />
                    <Bar dataKey="negative" stackId="a" fill="#ef4444" name="Downside">
                      {tornadoData.map((entry, index) => (
                        <Cell key={`cell-neg-${index}`} fill={entry.negative < 0 ? '#ef4444' : '#22c55e'} />
                      ))}
                    </Bar>
                    <Bar dataKey="positive" stackId="a" fill="#22c55e" name="Upside">
                      {tornadoData.map((entry, index) => (
                        <Cell key={`cell-pos-${index}`} fill={entry.positive > 0 ? '#22c55e' : '#ef4444'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Swing Summary */}
              <div className="mt-4 space-y-2">
                {tornadoData.slice(0, 3).map((t, idx) => (
                  <div key={idx} className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">{t.variable}</span>
                    <Badge variant="outline" className="bg-violet-50 text-violet-700">
                      Swing: {t.swing.toFixed(1)}%
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Spider Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="h-4 w-4 text-emerald-600" />
                Spider Chart (Scenario Comparison)
              </CardTitle>
              <CardDescription>
                Compare base, optimistic, and pessimistic scenarios
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={spiderData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="variable" tick={{ fontSize: 11 }} />
                    <PolarRadiusAxis angle={30} domain={[0, 'auto']} />
                    <Radar
                      name="Base Case"
                      dataKey="Base Case"
                      stroke="#6366f1"
                      fill="#6366f1"
                      fillOpacity={0.3}
                    />
                    <Radar
                      name="Optimistic"
                      dataKey="Optimistic"
                      stroke="#22c55e"
                      fill="#22c55e"
                      fillOpacity={0.2}
                    />
                    <Radar
                      name="Pessimistic"
                      dataKey="Pessimistic"
                      stroke="#ef4444"
                      fill="#ef4444"
                      fillOpacity={0.2}
                    />
                    <Legend />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Base Valuation Summary */}
          <Card className="lg:col-span-2">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500">Base Valuation</div>
                  <div className="text-2xl font-bold text-slate-800">
                    {formatCurrency(result.base_valuation)}
                  </div>
                </div>
                <div className="flex gap-4">
                  {result.tornado_data?.slice(0, 2).map((t, idx) => (
                    <div key={idx} className="text-center">
                      <div className="text-xs text-slate-500 mb-1">{t.variable} Impact</div>
                      <div className="flex gap-2">
                        <Badge className="bg-red-100 text-red-700">
                          <TrendingDown className="h-3 w-3 mr-1" />
                          {parseFloat(t.low_impact).toFixed(1)}%
                        </Badge>
                        <Badge className="bg-emerald-100 text-emerald-700">
                          <TrendingUp className="h-3 w-3 mr-1" />
                          +{parseFloat(t.high_impact).toFixed(1)}%
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {!result && (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center text-slate-500">
            <BarChart3 className="h-12 w-12 mx-auto mb-4 text-slate-300" />
            <p>Select a property and variables to run sensitivity analysis</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
