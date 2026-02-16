/**
 * Scenario Builder Component
 * Interactive tool for building custom scenarios with modifications
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Badge } from '../../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { useBuildScenario, useProperties, useTemplates, useApplyTemplate } from '../hooks/useScenarios';
import { Plus, Trash2, Zap, TrendingUp, TrendingDown, Calculator, Lightbulb } from 'lucide-react';

const modificationTypes = [
  { value: 'rent_growth', label: 'Rent Growth Rate', unit: '%', defaultValue: 0.03 },
  { value: 'vacancy', label: 'Vacancy Rate', unit: '%', defaultValue: 0.05 },
  { value: 'expenses', label: 'Expense Ratio', unit: '%', defaultValue: 0.35 },
  { value: 'cap_rate', label: 'Cap Rate', unit: '%', defaultValue: 0.055 },
  { value: 'exit_cap_rate', label: 'Exit Cap Rate', unit: '%', defaultValue: 0.06 },
  { value: 'discount_rate', label: 'Discount Rate', unit: '%', defaultValue: 0.08 },
  { value: 'rent_psf', label: 'Rent ($/SF)', unit: '$/SF', defaultValue: 65 },
];

const formatCurrency = (value) => {
  if (!value) return '$0';
  const num = parseFloat(value);
  if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
  return `$${num.toLocaleString()}`;
};

export function ScenarioBuilder() {
  const [selectedProperty, setSelectedProperty] = useState('');
  const [scenarioName, setScenarioName] = useState('');
  const [modifications, setModifications] = useState([
    { type: 'rent_growth', parameter: 'rent_growth_rate', new_value: 0.03, description: '' }
  ]);
  const [result, setResult] = useState(null);

  const { data: propertiesData } = useProperties();
  const { data: templatesData } = useTemplates();
  const buildMutation = useBuildScenario();
  const applyTemplateMutation = useApplyTemplate();

  const properties = propertiesData?.properties || [];
  const templates = templatesData?.templates || [];

  const addModification = () => {
    setModifications([...modifications, { 
      type: 'cap_rate', 
      parameter: 'cap_rate', 
      new_value: 0.055, 
      description: '' 
    }]);
  };

  const removeModification = (index) => {
    setModifications(modifications.filter((_, i) => i !== index));
  };

  const updateModification = (index, field, value) => {
    const updated = [...modifications];
    updated[index][field] = value;
    
    // Update parameter based on type
    if (field === 'type') {
      updated[index].parameter = value === 'rent_growth' ? 'rent_growth_rate' : value;
      const modType = modificationTypes.find(m => m.value === value);
      updated[index].new_value = modType?.defaultValue || 0;
    }
    
    setModifications(updated);
  };

  const handleBuild = () => {
    if (!selectedProperty || !scenarioName) return;
    
    buildMutation.mutate({
      base_property_id: selectedProperty,
      scenario_name: scenarioName,
      modifications: modifications.map(m => ({
        ...m,
        description: m.description || `${m.type} = ${m.new_value}`
      })),
    }, {
      onSuccess: (data) => setResult(data),
    });
  };

  const handleApplyTemplate = (templateName) => {
    if (!selectedProperty) return;
    
    applyTemplateMutation.mutate({
      propertyId: selectedProperty,
      templateName,
    }, {
      onSuccess: (data) => setResult(data),
    });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Builder Form */}
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Calculator className="h-4 w-4 text-blue-600" />
              Build Custom Scenario
            </CardTitle>
            <CardDescription>
              Create scenarios by modifying key valuation parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Base Property</Label>
                <Select value={selectedProperty} onValueChange={setSelectedProperty}>
                  <SelectTrigger data-testid="scenario-property-select">
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
              <div>
                <Label>Scenario Name</Label>
                <Input
                  data-testid="scenario-name-input"
                  value={scenarioName}
                  onChange={(e) => setScenarioName(e.target.value)}
                  placeholder="e.g., Optimistic Case"
                />
              </div>
            </div>

            {/* Modifications */}
            <div className="space-y-3 pt-4 border-t">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">Modifications</Label>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={addModification}
                  data-testid="add-modification-btn"
                >
                  <Plus className="h-4 w-4 mr-1" /> Add
                </Button>
              </div>

              {modifications.map((mod, idx) => (
                <div key={idx} className="flex items-center gap-2 p-3 bg-slate-50 rounded-lg">
                  <Select 
                    value={mod.type} 
                    onValueChange={(v) => updateModification(idx, 'type', v)}
                  >
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {modificationTypes.map((t) => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  <Input
                    type="number"
                    step="0.01"
                    className="w-24"
                    value={mod.new_value}
                    onChange={(e) => updateModification(idx, 'new_value', parseFloat(e.target.value))}
                  />
                  
                  <span className="text-sm text-slate-500">
                    {modificationTypes.find(t => t.value === mod.type)?.unit}
                  </span>
                  
                  <Input
                    className="flex-1"
                    placeholder="Description (optional)"
                    value={mod.description}
                    onChange={(e) => updateModification(idx, 'description', e.target.value)}
                  />
                  
                  <Button 
                    variant="ghost" 
                    size="sm" 
                    onClick={() => removeModification(idx)}
                    disabled={modifications.length === 1}
                  >
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              ))}
            </div>

            <Button
              className="w-full bg-blue-600 hover:bg-blue-700"
              onClick={handleBuild}
              disabled={buildMutation.isPending || !selectedProperty || !scenarioName}
              data-testid="build-scenario-btn"
            >
              {buildMutation.isPending ? 'Building...' : 'Build Scenario'}
            </Button>
          </CardContent>
        </Card>

        {/* Quick Templates */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-amber-500" />
              Quick Templates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-2">
              {templates.slice(0, 4).map((t) => (
                <Button
                  key={t.name}
                  variant="outline"
                  size="sm"
                  className="justify-start text-xs h-auto py-2"
                  onClick={() => handleApplyTemplate(t.name)}
                  disabled={!selectedProperty || applyTemplateMutation.isPending}
                >
                  <Zap className="h-3 w-3 mr-1 text-amber-500" />
                  {t.name}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Results */}
      <div className="space-y-4">
        {result && (
          <>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  {result.value_change_pct > 0 ? (
                    <TrendingUp className="h-4 w-4 text-emerald-600" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  )}
                  Scenario Result: {result.scenario_name}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="p-3 bg-slate-50 rounded-lg text-center">
                    <div className="text-xs text-slate-500 mb-1">Base Value</div>
                    <div className="text-lg font-bold text-slate-700">
                      {formatCurrency(result.base_value)}
                    </div>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg text-center">
                    <div className="text-xs text-blue-600 mb-1">Adjusted Value</div>
                    <div className="text-lg font-bold text-blue-700">
                      {formatCurrency(result.adjusted_value)}
                    </div>
                  </div>
                  <div className={`p-3 rounded-lg text-center ${
                    result.value_change_pct > 0 ? 'bg-emerald-50' : 'bg-red-50'
                  }`}>
                    <div className={`text-xs mb-1 ${
                      result.value_change_pct > 0 ? 'text-emerald-600' : 'text-red-600'
                    }`}>Change</div>
                    <div className={`text-lg font-bold ${
                      result.value_change_pct > 0 ? 'text-emerald-700' : 'text-red-700'
                    }`}>
                      {result.value_change_pct > 0 ? '+' : ''}{parseFloat(result.value_change_pct).toFixed(2)}%
                    </div>
                  </div>
                </div>

                {/* Component Impacts */}
                <div className="space-y-2">
                  <div className="text-sm font-medium text-slate-600">Impact Breakdown</div>
                  {result.component_impacts?.map((impact, idx) => (
                    <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-100">
                      <div>
                        <div className="text-sm text-slate-700">{impact.modification}</div>
                        <div className="text-xs text-slate-500">
                          {impact.old_value?.toFixed(4)} → {impact.new_value?.toFixed(4)}
                        </div>
                      </div>
                      <Badge className={
                        impact.impact_pct > 0 
                          ? 'bg-emerald-100 text-emerald-700' 
                          : 'bg-red-100 text-red-700'
                      }>
                        {impact.impact_pct > 0 ? '+' : ''}{parseFloat(impact.impact_pct).toFixed(2)}%
                      </Badge>
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
              <Calculator className="h-12 w-12 mx-auto mb-4 text-slate-300" />
              <p>Select a property and add modifications to build a scenario</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
