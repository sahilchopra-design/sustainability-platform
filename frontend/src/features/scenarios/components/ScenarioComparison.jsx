/**
 * Scenario Comparison Component
 * Compare multiple scenarios side by side
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Checkbox } from '../../../components/ui/checkbox';
import { useCompareScenarios, useScenarios, useProperties } from '../hooks/useScenarios';
import { GitCompare, Trophy, AlertTriangle, TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend,
} from 'recharts';
import { ExportButton } from '../../../components/shared/ExportButton';
import { exportScenarioAnalysis } from '../../../lib/exportUtils';

const formatCurrency = (value) => {
  if (!value) return '$0';
  const num = parseFloat(value);
  if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
  return `$${num.toLocaleString()}`;
};

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export function ScenarioComparison() {
  const [selectedProperty, setSelectedProperty] = useState('');
  const [selectedScenarioIds, setSelectedScenarioIds] = useState([]);
  const [result, setResult] = useState(null);

  const { data: propertiesData } = useProperties();
  const { data: scenariosData } = useScenarios({});
  const compareMutation = useCompareScenarios();

  const properties = propertiesData?.properties || [];
  const scenarios = scenariosData?.items || [];

  const toggleScenario = (id) => {
    if (selectedScenarioIds.includes(id)) {
      setSelectedScenarioIds(selectedScenarioIds.filter(s => s !== id));
    } else {
      setSelectedScenarioIds([...selectedScenarioIds, id]);
    }
  };

  const handleCompare = () => {
    if (!selectedProperty || selectedScenarioIds.length === 0) return;
    
    compareMutation.mutate({
      base_property_id: selectedProperty,
      scenario_ids: selectedScenarioIds,
      metrics: ['value', 'noi', 'cap_rate', 'irr'],
    }, {
      onSuccess: (data) => setResult(data),
    });
  };

  // Prepare chart data
  const chartData = result?.comparison_table?.map((row, idx) => ({
    name: row.scenario_name,
    value: parseFloat(row.value) / 1e6,
    change: parseFloat(row.value_change_pct),
    color: COLORS[idx % COLORS.length],
  })) || [];
  
  const handleExport = async (format) => {
    if (!result) return;
    await exportScenarioAnalysis({
      base_property_id: selectedProperty,
      scenario_ids: selectedScenarioIds,
      comparison_table: result.comparison_table || [],
      best_scenario: result.best_scenario,
      worst_scenario: result.worst_scenario,
      key_differentiators: result.key_differentiators || [],
    }, format);
  };

  return (
    <div className="space-y-6">
      {/* Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <GitCompare className="h-4 w-4 text-blue-300" />
              Compare Scenarios
            </CardTitle>
            <CardDescription>
              Select scenarios to compare against the base property
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <Select value={selectedProperty} onValueChange={setSelectedProperty}>
                <SelectTrigger data-testid="compare-property-select">
                  <SelectValue placeholder="Select base property..." />
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

            {scenarios.length > 0 ? (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {scenarios.map((s) => (
                  <div 
                    key={s.id} 
                    className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                      selectedScenarioIds.includes(s.id) 
                        ? 'bg-blue-500/10 border border-blue-500/20' 
                        : 'bg-white/[0.02] hover:bg-white/[0.06]'
                    }`}
                    onClick={() => toggleScenario(s.id)}
                  >
                    <Checkbox
                      checked={selectedScenarioIds.includes(s.id)}
                      onCheckedChange={() => toggleScenario(s.id)}
                    />
                    <div className="flex-1">
                      <div className="font-medium text-sm">{s.scenario_name}</div>
                      <div className="text-xs text-white/40">
                        {formatCurrency(s.adjusted_value)} 
                        <span className={parseFloat(s.value_change_pct) > 0 ? 'text-emerald-400' : 'text-red-400'}>
                          {' '}({parseFloat(s.value_change_pct) > 0 ? '+' : ''}{parseFloat(s.value_change_pct).toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-white/40 text-sm">
                No scenarios created yet. Build scenarios first.
              </div>
            )}

            <Button
              className="w-full mt-4 bg-blue-600 hover:bg-blue-700"
              onClick={handleCompare}
              disabled={compareMutation.isPending || !selectedProperty || selectedScenarioIds.length === 0}
              data-testid="compare-scenarios-btn"
            >
              {compareMutation.isPending ? 'Comparing...' : `Compare ${selectedScenarioIds.length} Scenario(s)`}
            </Button>
          </CardContent>
        </Card>

        {/* Quick Stats */}
        {result && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Comparison Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-3 bg-emerald-500/10 rounded-lg">
                <div className="flex items-center gap-2 text-emerald-400 mb-1">
                  <Trophy className="h-4 w-4" />
                  <span className="text-xs font-medium">Best Scenario</span>
                </div>
                <div className="font-bold text-emerald-300">{result.best_scenario}</div>
              </div>
              
              <div className="p-3 bg-red-500/10 rounded-lg">
                <div className="flex items-center gap-2 text-red-400 mb-1">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-xs font-medium">Worst Scenario</span>
                </div>
                <div className="font-bold text-red-300">{result.worst_scenario}</div>
              </div>

              <div className="pt-2 border-t">
                <div className="text-xs text-white/40 mb-2">Key Differentiators</div>
                {result.key_differentiators?.map((d, idx) => (
                  <div key={idx} className="text-xs text-white/60 mb-1">• {d}</div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-white/70">Comparison Results</h3>
            <ExportButton 
              onExport={handleExport}
              label="Export Comparison"
              data-testid="scenario-export-btn"
            />
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Value Comparison Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-violet-600" />
                Value Comparison
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45} 
                      textAnchor="end" 
                      height={80}
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis tickFormatter={(v) => `$${v}M`} />
                    <Tooltip 
                      formatter={(value) => [`$${value.toFixed(1)}M`, 'Value']}
                    />
                    <Bar dataKey="value" name="Value">
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Comparison Table */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Detailed Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2 px-2">Scenario</th>
                      <th className="text-right py-2 px-2">Value</th>
                      <th className="text-right py-2 px-2">Change</th>
                      <th className="text-right py-2 px-2">Cap Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.comparison_table?.map((row, idx) => (
                      <tr key={idx} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                        <td className="py-2 px-2">
                          <div className="flex items-center gap-2">
                            <div 
                              className="w-2 h-2 rounded-full" 
                              style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                            />
                            <span className="font-medium">{row.scenario_name}</span>
                          </div>
                        </td>
                        <td className="py-2 px-2 text-right font-medium">
                          {formatCurrency(row.value)}
                        </td>
                        <td className="py-2 px-2 text-right">
                          <Badge className={
                            parseFloat(row.value_change_pct) > 0 
                              ? 'bg-emerald-100 text-emerald-400' 
                              : parseFloat(row.value_change_pct) < 0
                                ? 'bg-red-100 text-red-400'
                                : 'bg-white/[0.06] text-white/70'
                          }>
                            {parseFloat(row.value_change_pct) > 0 ? (
                              <TrendingUp className="h-3 w-3 mr-1 inline" />
                            ) : parseFloat(row.value_change_pct) < 0 ? (
                              <TrendingDown className="h-3 w-3 mr-1 inline" />
                            ) : null}
                            {parseFloat(row.value_change_pct).toFixed(1)}%
                          </Badge>
                        </td>
                        <td className="py-2 px-2 text-right text-white/60">
                          {(parseFloat(row.cap_rate) * 100).toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
        </div>
      )}

      {!result && !compareMutation.isPending && (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center text-white/40">
            <GitCompare className="h-12 w-12 mx-auto mb-4 text-white/20" />
            <p>Select scenarios to compare them side by side</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
