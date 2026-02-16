/**
 * Replacement Cost Calculator
 * Cost Approach to value
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Button } from '../../../../components/ui/button';
import { Input } from '../../../../components/ui/input';
import { Label } from '../../../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../../components/ui/select';
import { Badge } from '../../../../components/ui/badge';
import { 
  Calculator, DollarSign, Building, Hammer,
  RefreshCw, Info, Minus, Plus, Trash2
} from 'lucide-react';
import { useReplacementCost } from '../../hooks/useValuation';

const formatCurrency = (value) => {
  if (!value) return '$0';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(parseFloat(value));
};

const formatPercent = (value) => {
  if (!value) return '0%';
  return `${(parseFloat(value) * 100).toFixed(1)}%`;
};

const CONSTRUCTION_TYPES = [
  { value: 'steel_frame', label: 'Steel Frame' },
  { value: 'concrete', label: 'Concrete' },
  { value: 'masonry', label: 'Masonry' },
  { value: 'wood_frame', label: 'Wood Frame' },
  { value: 'prefabricated', label: 'Prefabricated' },
  { value: 'mixed', label: 'Mixed' },
];

const QUALITY_CLASSES = [
  { value: 'class_a', label: 'Class A (Premium)' },
  { value: 'class_b', label: 'Class B (Standard)' },
  { value: 'class_c', label: 'Class C (Economy)' },
];

const CONDITION_RATINGS = [
  { value: 'excellent', label: 'Excellent' },
  { value: 'good', label: 'Good' },
  { value: 'fair', label: 'Fair' },
  { value: 'poor', label: 'Poor' },
];

export function CostApproachCalculator() {
  const { mutate: calculate, isPending, data: result, reset } = useReplacementCost();
  
  const [inputs, setInputs] = useState({
    land_area_acres: 2.5,
    land_value_per_acre: 5000000,
    building_area_sf: 100000,
    construction_type: 'steel_frame',
    quality: 'class_a',
    location_factor: 1.15,
    effective_age: 15,
    total_economic_life: 50,
    condition_rating: 'good',
    external_obsolescence_percent: 2,
  });

  const [deficiencies, setDeficiencies] = useState([]);
  const [superadequacies, setSuperadequacies] = useState([]);

  const handleChange = (field, value) => {
    setInputs(prev => ({ ...prev, [field]: value }));
  };

  const addDeficiency = () => {
    setDeficiencies(prev => [...prev, { description: '', cost_to_cure: 0 }]);
  };

  const updateDeficiency = (index, field, value) => {
    setDeficiencies(prev => prev.map((d, i) => 
      i === index ? { ...d, [field]: value } : d
    ));
  };

  const removeDeficiency = (index) => {
    setDeficiencies(prev => prev.filter((_, i) => i !== index));
  };

  const addSuperadequacy = () => {
    setSuperadequacies(prev => [...prev, { description: '', excess_cost: 0 }]);
  };

  const updateSuperadequacy = (index, field, value) => {
    setSuperadequacies(prev => prev.map((s, i) => 
      i === index ? { ...s, [field]: value } : s
    ));
  };

  const removeSuperadequacy = (index) => {
    setSuperadequacies(prev => prev.filter((_, i) => i !== index));
  };

  const handleCalculate = () => {
    calculate({
      land_area_acres: parseFloat(inputs.land_area_acres),
      land_value_per_acre: parseFloat(inputs.land_value_per_acre),
      building_area_sf: parseFloat(inputs.building_area_sf),
      construction_type: inputs.construction_type,
      quality: inputs.quality,
      location_factor: parseFloat(inputs.location_factor),
      effective_age: parseInt(inputs.effective_age),
      total_economic_life: parseInt(inputs.total_economic_life),
      condition_rating: inputs.condition_rating,
      functional_deficiencies: deficiencies.filter(d => d.description).map(d => ({
        description: d.description,
        cost_to_cure: parseFloat(d.cost_to_cure) || 0,
      })),
      superadequacies: superadequacies.filter(s => s.description).map(s => ({
        description: s.description,
        excess_cost: parseFloat(s.excess_cost) || 0,
      })),
      external_obsolescence_percent: parseFloat(inputs.external_obsolescence_percent) / 100,
    });
  };

  const handleReset = () => {
    reset();
    setInputs({
      land_area_acres: 2.5,
      land_value_per_acre: 5000000,
      building_area_sf: 100000,
      construction_type: 'steel_frame',
      quality: 'class_a',
      location_factor: 1.15,
      effective_age: 15,
      total_economic_life: 50,
      condition_rating: 'good',
      external_obsolescence_percent: 2,
    });
    setDeficiencies([]);
    setSuperadequacies([]);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Input Form */}
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Hammer className="h-5 w-5 text-amber-500" />
              Cost Approach Inputs
            </CardTitle>
            <CardDescription>
              Land value and construction cost parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Land Value */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-slate-700 border-b pb-2">
                Land Value
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Land Area (Acres)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={inputs.land_area_acres}
                    onChange={(e) => handleChange('land_area_acres', e.target.value)}
                    data-testid="input-land-area"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Value per Acre ($)</Label>
                  <Input
                    type="number"
                    value={inputs.land_value_per_acre}
                    onChange={(e) => handleChange('land_value_per_acre', e.target.value)}
                    data-testid="input-land-value"
                  />
                </div>
              </div>
            </div>

            {/* Building Characteristics */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-slate-700 border-b pb-2">
                Building Characteristics
              </h4>
              <div className="space-y-2">
                <Label>Building Area (SF)</Label>
                <Input
                  type="number"
                  value={inputs.building_area_sf}
                  onChange={(e) => handleChange('building_area_sf', e.target.value)}
                  data-testid="input-building-area"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Construction Type</Label>
                  <Select 
                    value={inputs.construction_type} 
                    onValueChange={(v) => handleChange('construction_type', v)}
                  >
                    <SelectTrigger data-testid="select-construction-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CONSTRUCTION_TYPES.map(t => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Quality Class</Label>
                  <Select 
                    value={inputs.quality} 
                    onValueChange={(v) => handleChange('quality', v)}
                  >
                    <SelectTrigger data-testid="select-quality">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {QUALITY_CLASSES.map(q => (
                        <SelectItem key={q.value} value={q.value}>{q.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Location Factor</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={inputs.location_factor}
                  onChange={(e) => handleChange('location_factor', e.target.value)}
                  data-testid="input-location-factor"
                />
                <p className="text-xs text-slate-500">1.0 = National Average</p>
              </div>
            </div>

            {/* Depreciation Parameters */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-slate-700 border-b pb-2">
                Depreciation Parameters
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Effective Age (Years)</Label>
                  <Input
                    type="number"
                    value={inputs.effective_age}
                    onChange={(e) => handleChange('effective_age', e.target.value)}
                    data-testid="input-effective-age"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Economic Life (Years)</Label>
                  <Input
                    type="number"
                    value={inputs.total_economic_life}
                    onChange={(e) => handleChange('total_economic_life', e.target.value)}
                    data-testid="input-economic-life"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Condition Rating</Label>
                  <Select 
                    value={inputs.condition_rating} 
                    onValueChange={(v) => handleChange('condition_rating', v)}
                  >
                    <SelectTrigger data-testid="select-condition">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CONDITION_RATINGS.map(c => (
                        <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>External Obsolescence (%)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={inputs.external_obsolescence_percent}
                    onChange={(e) => handleChange('external_obsolescence_percent', e.target.value)}
                    data-testid="input-external-obsolescence"
                  />
                </div>
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-3 pt-4">
              <Button 
                onClick={handleCalculate} 
                disabled={isPending}
                className="flex-1 bg-amber-600 hover:bg-amber-700"
                data-testid="btn-calculate-cost"
              >
                {isPending ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Calculator className="h-4 w-4 mr-2" />
                )}
                Calculate Value
              </Button>
              <Button variant="outline" onClick={handleReset}>
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Functional Obsolescence */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center justify-between">
              <span>Functional Deficiencies</span>
              <Button size="sm" variant="outline" onClick={addDeficiency}>
                <Plus className="h-3 w-3 mr-1" /> Add
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {deficiencies.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-2">No deficiencies added</p>
            ) : (
              deficiencies.map((d, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <Input
                    placeholder="Description"
                    value={d.description}
                    onChange={(e) => updateDeficiency(idx, 'description', e.target.value)}
                    className="flex-1"
                  />
                  <Input
                    type="number"
                    placeholder="Cost to cure"
                    value={d.cost_to_cure}
                    onChange={(e) => updateDeficiency(idx, 'cost_to_cure', e.target.value)}
                    className="w-32"
                  />
                  <Button size="icon" variant="ghost" onClick={() => removeDeficiency(idx)}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Results */}
      <Card className={result ? 'ring-2 ring-amber-200' : ''}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-emerald-500" />
            Cost Approach Results
          </CardTitle>
          <CardDescription>
            Replacement cost less depreciation
          </CardDescription>
        </CardHeader>
        <CardContent>
          {result ? (
            <div className="space-y-6">
              {/* Final Value */}
              <div className="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg p-6 text-center">
                <p className="text-sm text-amber-600 font-medium mb-1">Property Value</p>
                <p className="text-4xl font-bold text-amber-900">
                  {formatCurrency(result.property_value)}
                </p>
                <p className="text-sm text-amber-700 mt-2">
                  {formatCurrency(result.value_per_sf)} / SF
                </p>
              </div>

              {/* Breakdown */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                  <Building className="h-4 w-4" />
                  Value Breakdown
                </h4>
                <div className="bg-slate-50 rounded-lg p-4 space-y-2">
                  {/* Land */}
                  <div className="flex justify-between text-sm font-medium border-b pb-2">
                    <span>Land Value</span>
                    <span>{formatCurrency(result.land_value)}</span>
                  </div>
                  
                  {/* RCN */}
                  <div className="pt-2">
                    <div className="flex justify-between text-sm">
                      <span>Base Cost ({formatCurrency(result.base_cost_per_sf)}/SF)</span>
                      <span>{formatCurrency(result.rcn_before_adjustments)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Location Factor ({result.location_factor}x)</span>
                      <span className="font-medium">{formatCurrency(result.rcn)}</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">Replacement Cost New (RCN)</p>
                  </div>

                  {/* Depreciation */}
                  <div className="border-t pt-2 mt-2">
                    <p className="text-xs text-slate-600 mb-2">Less: Depreciation</p>
                    <div className="flex justify-between text-sm text-red-600">
                      <span>Physical ({formatPercent(result.physical_depreciation_percent)})</span>
                      <span>({formatCurrency(result.physical_depreciation)})</span>
                    </div>
                    {parseFloat(result.functional_obsolescence) > 0 && (
                      <div className="flex justify-between text-sm text-red-600">
                        <span>Functional</span>
                        <span>({formatCurrency(result.functional_obsolescence)})</span>
                      </div>
                    )}
                    {parseFloat(result.external_obsolescence) > 0 && (
                      <div className="flex justify-between text-sm text-red-600">
                        <span>External ({formatPercent(result.external_obsolescence_percent)})</span>
                        <span>({formatCurrency(result.external_obsolescence)})</span>
                      </div>
                    )}
                    <div className="flex justify-between text-sm font-medium text-red-700 border-t pt-1 mt-1">
                      <span>Total Depreciation ({formatPercent(result.total_depreciation_percent)})</span>
                      <span>({formatCurrency(result.total_depreciation)})</span>
                    </div>
                  </div>

                  {/* Final */}
                  <div className="border-t pt-2 mt-2">
                    <div className="flex justify-between text-sm">
                      <span>Depreciated Improvements</span>
                      <span>{formatCurrency(result.depreciated_improvements)}</span>
                    </div>
                    <div className="flex justify-between text-sm font-bold text-emerald-700 mt-2">
                      <span>Total Property Value</span>
                      <span>{formatCurrency(result.property_value)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Formula */}
              <div className="bg-amber-50 rounded-lg p-4">
                <div className="flex items-center gap-2 text-amber-700 text-sm mb-2">
                  <Info className="h-4 w-4" />
                  <span className="font-medium">Cost Approach Formula</span>
                </div>
                <p className="text-sm text-amber-600">
                  Value = Land + (RCN - Depreciation) = {formatCurrency(result.land_value)} + {formatCurrency(result.depreciated_improvements)}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-slate-400">
              <Hammer className="h-16 w-16 mb-4 opacity-50" />
              <p className="text-sm">Enter inputs and click Calculate</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default CostApproachCalculator;
