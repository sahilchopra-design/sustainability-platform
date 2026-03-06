/**
 * Scenario Comparison Component
 * Compare multiple scenarios for a portfolio
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Checkbox } from '../../../components/ui/checkbox';
import { Label } from '../../../components/ui/label';
import { Skeleton } from '../../../components/ui/skeleton';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '../../../components/ui/table';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import {
  GitCompare, Loader2, TrendingUp, TrendingDown, AlertTriangle,
  CheckCircle, XCircle, Info
} from 'lucide-react';
import { useCompareScenarios } from '../hooks/usePortfolioAnalytics';

// Sample scenario IDs for demonstration
const AVAILABLE_SCENARIOS = [
  { id: '00000000-0000-0000-0000-000000000001', name: 'Optimistic Growth', description: 'Strong economic recovery' },
  { id: '00000000-0000-0000-0000-000000000002', name: 'Recession Stress', description: 'Economic downturn scenario' },
  { id: '00000000-0000-0000-0000-000000000003', name: 'Climate Transition', description: 'Rapid decarbonization' },
  { id: '00000000-0000-0000-0000-000000000004', name: 'Green Premium', description: 'ESG-focused value increase' },
  { id: '00000000-0000-0000-0000-000000000005', name: 'Rising Rates', description: 'Interest rate increase scenario' },
];

function formatCurrency(value) {
  if (!value) return '-';
  const num = parseFloat(value);
  if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
  return `$${num.toLocaleString()}`;
}

export function ScenarioComparison({ portfolioId }) {
  const [selectedScenarios, setSelectedScenarios] = useState([]);
  const [comparisonResult, setComparisonResult] = useState(null);
  
  const { mutate: compareScenarios, isPending } = useCompareScenarios();
  
  const toggleScenario = (scenarioId) => {
    setSelectedScenarios(prev => 
      prev.includes(scenarioId)
        ? prev.filter(id => id !== scenarioId)
        : [...prev, scenarioId]
    );
  };
  
  const handleCompare = () => {
    if (selectedScenarios.length === 0) return;
    
    setComparisonResult(null);
    compareScenarios(
      {
        portfolioId,
        data: {
          scenario_ids: selectedScenarios,
          time_horizon: 10,
        },
      },
      {
        onSuccess: (data) => {
          setComparisonResult(data);
        },
      }
    );
  };
  
  if (!portfolioId) {
    return (
      <Card className="bg-[#0d1424]" data-testid="scenario-comparison-disabled">
        <CardContent className="py-12 text-center text-white/40">
          <GitCompare className="h-12 w-12 mx-auto mb-4 text-white/20" />
          <p>Select a portfolio to compare scenarios</p>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card className="bg-[#0d1424]" data-testid="scenario-comparison">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-white/70 flex items-center gap-2">
          <GitCompare className="h-4 w-4 text-violet-500" />
          Scenario Comparison
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Scenario Selection */}
        <div>
          <Label className="text-xs text-white/60 mb-2 block">Select Scenarios to Compare</Label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {AVAILABLE_SCENARIOS.map((scenario) => (
              <label
                key={scenario.id}
                className={`flex items-start gap-2 p-2 rounded-lg border cursor-pointer transition-colors ${
                  selectedScenarios.includes(scenario.id)
                    ? 'bg-violet-50 border-violet-300'
                    : 'bg-[#0d1424] border-white/[0.06] hover:bg-white/[0.02]'
                }`}
              >
                <Checkbox
                  checked={selectedScenarios.includes(scenario.id)}
                  onCheckedChange={() => toggleScenario(scenario.id)}
                  className="mt-0.5"
                />
                <div>
                  <p className="text-sm font-medium text-white/70">{scenario.name}</p>
                  <p className="text-xs text-white/40">{scenario.description}</p>
                </div>
              </label>
            ))}
          </div>
        </div>
        
        {/* Compare Button */}
        <Button
          onClick={handleCompare}
          disabled={isPending || selectedScenarios.length === 0}
          className="w-full"
          data-testid="compare-scenarios-btn"
        >
          {isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Comparing...
            </>
          ) : (
            <>
              <GitCompare className="h-4 w-4 mr-2" />
              Compare {selectedScenarios.length} Scenario{selectedScenarios.length !== 1 ? 's' : ''}
            </>
          )}
        </Button>
        
        {/* Comparison Results */}
        {comparisonResult && (
          <div className="space-y-4" data-testid="comparison-results">
            {/* Summary */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                <div className="flex items-center gap-2 mb-1">
                  <CheckCircle className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs text-emerald-400 font-medium">Best Scenario</span>
                </div>
                <p className="font-semibold text-emerald-300">{comparisonResult.best_scenario}</p>
              </div>
              <div className="p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                <div className="flex items-center gap-2 mb-1">
                  <XCircle className="h-4 w-4 text-red-400" />
                  <span className="text-xs text-red-400 font-medium">Worst Scenario</span>
                </div>
                <p className="font-semibold text-red-300">{comparisonResult.worst_scenario}</p>
              </div>
            </div>
            
            {/* Value Spread */}
            <div className="p-3 bg-white/[0.02] rounded-lg">
              <div className="flex items-center justify-between">
                <span className="text-xs text-white/60">Value Spread</span>
                <span className="font-semibold text-white/90">
                  {formatCurrency(comparisonResult.value_spread)}
                </span>
              </div>
              <p className="text-xs text-white/40 mt-1">
                Base Value: {formatCurrency(comparisonResult.base_value)}
              </p>
            </div>
            
            {/* Comparison Chart */}
            {comparisonResult.comparison_table && (
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={comparisonResult.comparison_table.map(row => ({
                      name: row.scenario_name.length > 12 
                        ? row.scenario_name.substring(0, 12) + '...' 
                        : row.scenario_name,
                      value: parseFloat(row.total_value) / 1e6,
                      change: parseFloat(row.value_change_pct),
                    }))}
                    margin={{ top: 10, right: 10, left: 10, bottom: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" tick={{ fontSize: 9 }} angle={-20} textAnchor="end" height={50} />
                    <YAxis tickFormatter={(v) => `$${v}M`} tick={{ fontSize: 10 }} />
                    <Tooltip
                      formatter={(value, name) => [
                        name === 'value' ? `$${value.toFixed(1)}M` : `${value.toFixed(1)}%`,
                        name === 'value' ? 'Total Value' : 'Change %'
                      ]}
                      contentStyle={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '6px' }}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {comparisonResult.comparison_table.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`}
                          fill={parseFloat(entry.value_change_pct) >= 0 ? '#22c55e' : '#ef4444'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
            
            {/* Comparison Table */}
            <div className="border rounded-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-white/[0.02]">
                    <TableHead className="text-xs">Scenario</TableHead>
                    <TableHead className="text-xs text-right">Value</TableHead>
                    <TableHead className="text-xs text-right">Change</TableHead>
                    <TableHead className="text-xs text-right">Stranded</TableHead>
                    <TableHead className="text-xs text-right">VaR 95%</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {comparisonResult.comparison_table?.map((row) => {
                    const changePct = parseFloat(row.value_change_pct);
                    const isPositive = changePct >= 0;
                    
                    return (
                      <TableRow key={row.scenario_id}>
                        <TableCell className="font-medium text-sm">{row.scenario_name}</TableCell>
                        <TableCell className="text-right text-sm">
                          {formatCurrency(row.total_value)}
                        </TableCell>
                        <TableCell className="text-right">
                          <span className={`text-sm ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                            {isPositive ? '+' : ''}{changePct.toFixed(1)}%
                          </span>
                        </TableCell>
                        <TableCell className="text-right">
                          <Badge variant="outline" className={row.stranded_count > 0 ? 'bg-red-500/10 text-red-400' : ''}>
                            {row.stranded_count}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right text-sm text-white/60">
                          {formatCurrency(row.var_95)}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
            
            {/* Key Insights */}
            {comparisonResult.key_insights?.length > 0 && (
              <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <Info className="h-4 w-4 text-blue-300" />
                  <span className="text-sm font-medium text-blue-300">Key Insights</span>
                </div>
                <ul className="space-y-1">
                  {comparisonResult.key_insights.map((insight, i) => (
                    <li key={i} className="text-xs text-blue-300 flex items-start gap-1">
                      <span className="mt-0.5">•</span>
                      {insight}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
