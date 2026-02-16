/**
 * What-If Analysis Component
 * Real-time parameter changes with cascading effects
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Badge } from '../../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Switch } from '../../../components/ui/switch';
import { useWhatIfAnalysis, useProperties, useWhatIfParameters } from '../hooks/useScenarios';
import { Zap, Plus, Trash2, ArrowRight, TrendingUp, TrendingDown, RefreshCw, HelpCircle } from 'lucide-react';

const formatCurrency = (value) => {
  if (!value) return '$0';
  const num = parseFloat(value);
  if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
  return `$${num.toLocaleString()}`;
};

export function WhatIfAnalysis() {
  const [selectedProperty, setSelectedProperty] = useState('');
  const [cascadeEffects, setCascadeEffects] = useState(true);
  const [changes, setChanges] = useState([
    { parameter: 'vacancy_rate', change_type: 'percentage', change_value: 0.1 }
  ]);
  const [result, setResult] = useState(null);

  const { data: propertiesData } = useProperties();
  const { data: parametersData } = useWhatIfParameters();
  const analysisMutation = useWhatIfAnalysis();

  const properties = propertiesData?.properties || [];
  const parameters = parametersData?.parameters || [];
  const changeTypes = parametersData?.change_types || [];

  const addChange = () => {
    setChanges([...changes, { 
      parameter: 'cap_rate', 
      change_type: 'percentage', 
      change_value: 0 
    }]);
  };

  const removeChange = (index) => {
    setChanges(changes.filter((_, i) => i !== index));
  };

  const updateChange = (index, field, value) => {
    const updated = [...changes];
    updated[index][field] = field === 'change_value' ? parseFloat(value) : value;
    setChanges(updated);
  };

  const handleAnalyze = () => {
    if (!selectedProperty || changes.length === 0) return;
    
    analysisMutation.mutate({
      property_id: selectedProperty,
      changes,
      cascade_effects: cascadeEffects,
    }, {
      onSuccess: (data) => setResult(data),
    });
  };

  const getParameterLabel = (paramName) => {
    const param = parameters.find(p => p.name === paramName);
    return param?.label || paramName;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Zap className="h-4 w-4 text-amber-600" />
            What-If Analysis
          </CardTitle>
          <CardDescription>
            See how parameter changes affect valuation in real-time
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Base Property</Label>
            <Select value={selectedProperty} onValueChange={setSelectedProperty}>
              <SelectTrigger data-testid="whatif-property-select">
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

          {/* Cascade Toggle */}
          <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
            <div className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4 text-amber-600" />
              <div>
                <div className="text-sm font-medium">Cascade Effects</div>
                <div className="text-xs text-slate-500">Include secondary impacts</div>
              </div>
            </div>
            <Switch
              checked={cascadeEffects}
              onCheckedChange={setCascadeEffects}
            />
          </div>

          {/* Changes */}
          <div className="space-y-3 pt-4 border-t">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">Parameter Changes</Label>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={addChange}
                data-testid="add-whatif-change-btn"
              >
                <Plus className="h-4 w-4 mr-1" /> Add
              </Button>
            </div>

            {changes.map((change, idx) => (
              <div key={idx} className="p-3 bg-slate-50 rounded-lg space-y-2">
                <div className="flex items-center gap-2">
                  <Select 
                    value={change.parameter} 
                    onValueChange={(v) => updateChange(idx, 'parameter', v)}
                  >
                    <SelectTrigger className="w-36">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {parameters.map((p) => (
                        <SelectItem key={p.name} value={p.name}>{p.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Select
                    value={change.change_type}
                    onValueChange={(v) => updateChange(idx, 'change_type', v)}
                  >
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {changeTypes.map((ct) => (
                        <SelectItem key={ct.value} value={ct.value}>{ct.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Input
                    type="number"
                    step="0.01"
                    className="w-24"
                    value={change.change_value}
                    onChange={(e) => updateChange(idx, 'change_value', e.target.value)}
                    placeholder="0.1"
                  />

                  <span className="text-xs text-slate-500">
                    {change.change_type === 'percentage' ? '(e.g., 0.1 = +10%)' : '(absolute)'}
                  </span>

                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => removeChange(idx)}
                    disabled={changes.length === 1}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <Button
            className="w-full bg-amber-600 hover:bg-amber-700"
            onClick={handleAnalyze}
            disabled={analysisMutation.isPending || !selectedProperty || changes.length === 0}
            data-testid="run-whatif-btn"
          >
            {analysisMutation.isPending ? 'Analyzing...' : 'Analyze Impact'}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-4">
        {result && (
          <>
            {/* Value Impact */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  {parseFloat(result.total_change_pct) > 0 ? (
                    <TrendingUp className="h-4 w-4 text-emerald-600" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  )}
                  Valuation Impact
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center gap-6 py-4">
                  <div className="text-center">
                    <div className="text-xs text-slate-500 mb-1">Base Value</div>
                    <div className="text-xl font-bold text-slate-700">
                      {formatCurrency(result.base_valuation)}
                    </div>
                  </div>
                  
                  <ArrowRight className="h-6 w-6 text-slate-400" />
                  
                  <div className="text-center">
                    <div className="text-xs text-slate-500 mb-1">Adjusted Value</div>
                    <div className={`text-xl font-bold ${
                      parseFloat(result.total_change_pct) > 0 ? 'text-emerald-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(result.adjusted_valuation)}
                    </div>
                  </div>
                </div>

                <div className="flex justify-center">
                  <Badge className={`text-lg px-4 py-2 ${
                    parseFloat(result.total_change_pct) > 0 
                      ? 'bg-emerald-100 text-emerald-700' 
                      : 'bg-red-100 text-red-700'
                  }`}>
                    {parseFloat(result.total_change_pct) > 0 ? '+' : ''}
                    {parseFloat(result.total_change_pct).toFixed(2)}%
                    ({formatCurrency(result.total_change)})
                  </Badge>
                </div>

                {result.cascade_effects_applied && (
                  <div className="mt-4 p-2 bg-amber-50 rounded text-center text-xs text-amber-700">
                    <RefreshCw className="h-3 w-3 inline mr-1" />
                    Cascade effects included in calculation
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Change Breakdown */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Change Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {result.change_breakdown?.map((cb, idx) => (
                    <div key={idx} className="p-3 bg-slate-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-sm">
                          {getParameterLabel(cb.parameter)}
                        </span>
                        <Badge className={
                          parseFloat(cb.total_impact) > 0 
                            ? 'bg-emerald-100 text-emerald-700' 
                            : 'bg-red-100 text-red-700'
                        }>
                          {parseFloat(cb.total_impact) > 0 ? '+' : ''}
                          {formatCurrency(cb.total_impact)}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-xs text-slate-500">
                        <span>{cb.old_value?.toFixed(4)}</span>
                        <ArrowRight className="h-3 w-3" />
                        <span className="font-medium text-slate-700">{cb.new_value?.toFixed(4)}</span>
                      </div>
                      {parseFloat(cb.cascading_impacts) !== 0 && (
                        <div className="mt-2 text-xs text-amber-600">
                          <RefreshCw className="h-3 w-3 inline mr-1" />
                          Cascading impact: {formatCurrency(cb.cascading_impacts)}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {!result && (
          <Card className="border-dashed">
            <CardContent className="py-12 text-center text-slate-500">
              <Zap className="h-12 w-12 mx-auto mb-4 text-slate-300" />
              <p>Add parameter changes to see their impact on valuation</p>
              <div className="mt-4 flex items-center justify-center gap-2 text-xs">
                <HelpCircle className="h-3 w-3" />
                <span>Percentage: 0.1 = +10%, -0.05 = -5%</span>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
