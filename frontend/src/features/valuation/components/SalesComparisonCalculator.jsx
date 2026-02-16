/**
 * Sales Comparison Calculator
 * Market Approach using comparable sales
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Badge } from '../../../components/ui/badge';
import { 
  Calculator, DollarSign, Scale, Building2,
  RefreshCw, Info, Plus, Trash2, ArrowRight
} from 'lucide-react';
import { useSalesComparison } from '../../hooks/useValuation';

const formatCurrency = (value, compact = false) => {
  if (!value) return '$0';
  const num = parseFloat(value);
  if (compact && Math.abs(num) >= 1000000) {
    return `$${(num / 1000000).toFixed(2)}M`;
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
};

const formatPercent = (value) => {
  if (!value) return '0%';
  return `${(parseFloat(value) * 100).toFixed(2)}%`;
};

const QUALITY_OPTIONS = [
  { value: 'class_a', label: 'Class A' },
  { value: 'class_b', label: 'Class B' },
  { value: 'class_c', label: 'Class C' },
];

const CONDITION_OPTIONS = [
  { value: 'excellent', label: 'Excellent' },
  { value: 'good', label: 'Good' },
  { value: 'fair', label: 'Fair' },
  { value: 'poor', label: 'Poor' },
];

const LOCATION_OPTIONS = [
  { value: 'cbd_prime', label: 'CBD Prime' },
  { value: 'cbd', label: 'CBD' },
  { value: 'urban', label: 'Urban' },
  { value: 'suburban', label: 'Suburban' },
  { value: 'rural', label: 'Rural' },
];

export function SalesComparisonCalculator() {
  const { mutate: calculate, isPending, data: result, reset } = useSalesComparison();
  
  const [subject, setSubject] = useState({
    size_sf: 100000,
    year_built: 2015,
    quality: 'class_a',
    condition: 'good',
    location: 'urban',
  });

  const [comparables, setComparables] = useState([
    {
      id: crypto.randomUUID(),
      sale_price: 42500000,
      sale_date: '2024-08-15',
      size_sf: 95000,
      year_built: 2012,
      quality: 'class_a',
      condition: 'good',
      location: 'urban',
    },
    {
      id: crypto.randomUUID(),
      sale_price: 51000000,
      sale_date: '2024-06-20',
      size_sf: 110000,
      year_built: 2018,
      quality: 'class_a',
      condition: 'excellent',
      location: 'urban',
    },
  ]);

  const [appreciationRate, setAppreciationRate] = useState(0.5);

  const handleSubjectChange = (field, value) => {
    setSubject(prev => ({ ...prev, [field]: value }));
  };

  const addComparable = () => {
    setComparables(prev => [...prev, {
      id: crypto.randomUUID(),
      sale_price: 0,
      sale_date: new Date().toISOString().split('T')[0],
      size_sf: 100000,
      year_built: 2015,
      quality: 'class_b',
      condition: 'good',
      location: 'urban',
    }]);
  };

  const updateComparable = (id, field, value) => {
    setComparables(prev => prev.map(c => 
      c.id === id ? { ...c, [field]: value } : c
    ));
  };

  const removeComparable = (id) => {
    setComparables(prev => prev.filter(c => c.id !== id));
  };

  const handleCalculate = () => {
    calculate({
      subject_property: {
        size_sf: parseFloat(subject.size_sf),
        year_built: parseInt(subject.year_built),
        quality: subject.quality,
        condition: subject.condition,
        location: subject.location,
      },
      comparables: comparables.filter(c => c.sale_price > 0).map(c => ({
        id: c.id,
        sale_price: parseFloat(c.sale_price),
        sale_date: c.sale_date,
        size_sf: parseFloat(c.size_sf),
        year_built: parseInt(c.year_built),
        quality: c.quality,
        condition: c.condition,
        location: c.location,
      })),
      market_appreciation_rate: parseFloat(appreciationRate) / 100,
    });
  };

  const handleReset = () => {
    reset();
    setSubject({
      size_sf: 100000,
      year_built: 2015,
      quality: 'class_a',
      condition: 'good',
      location: 'urban',
    });
    setComparables([]);
    setAppreciationRate(0.5);
  };

  return (
    <div className="space-y-6">
      {/* Subject Property */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-emerald-500" />
            Subject Property
          </CardTitle>
          <CardDescription>
            Property being valued
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="space-y-2">
              <Label>Size (SF)</Label>
              <Input
                type="number"
                value={subject.size_sf}
                onChange={(e) => handleSubjectChange('size_sf', e.target.value)}
                data-testid="input-subject-size"
              />
            </div>
            <div className="space-y-2">
              <Label>Year Built</Label>
              <Input
                type="number"
                value={subject.year_built}
                onChange={(e) => handleSubjectChange('year_built', e.target.value)}
                data-testid="input-subject-year"
              />
            </div>
            <div className="space-y-2">
              <Label>Quality</Label>
              <Select value={subject.quality} onValueChange={(v) => handleSubjectChange('quality', v)}>
                <SelectTrigger data-testid="select-subject-quality">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {QUALITY_OPTIONS.map(q => (
                    <SelectItem key={q.value} value={q.value}>{q.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Condition</Label>
              <Select value={subject.condition} onValueChange={(v) => handleSubjectChange('condition', v)}>
                <SelectTrigger data-testid="select-subject-condition">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CONDITION_OPTIONS.map(c => (
                    <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Location</Label>
              <Select value={subject.location} onValueChange={(v) => handleSubjectChange('location', v)}>
                <SelectTrigger data-testid="select-subject-location">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LOCATION_OPTIONS.map(l => (
                    <SelectItem key={l.value} value={l.value}>{l.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Comparables */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Scale className="h-5 w-5 text-blue-500" />
              Comparable Sales
            </span>
            <Button size="sm" onClick={addComparable} data-testid="btn-add-comparable">
              <Plus className="h-4 w-4 mr-1" /> Add Comparable
            </Button>
          </CardTitle>
          <CardDescription>
            Recent sales used for comparison
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {comparables.length === 0 ? (
            <p className="text-center py-8 text-slate-500">
              No comparables added. Click "Add Comparable" to begin.
            </p>
          ) : (
            comparables.map((comp, idx) => (
              <div key={comp.id} className="bg-slate-50 rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <Badge variant="outline">Comparable {idx + 1}</Badge>
                  <Button 
                    size="sm" 
                    variant="ghost" 
                    onClick={() => removeComparable(comp.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Sale Price ($)</Label>
                    <Input
                      type="number"
                      value={comp.sale_price}
                      onChange={(e) => updateComparable(comp.id, 'sale_price', e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Sale Date</Label>
                    <Input
                      type="date"
                      value={comp.sale_date}
                      onChange={(e) => updateComparable(comp.id, 'sale_date', e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Size (SF)</Label>
                    <Input
                      type="number"
                      value={comp.size_sf}
                      onChange={(e) => updateComparable(comp.id, 'size_sf', e.target.value)}
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Year Built</Label>
                    <Input
                      type="number"
                      value={comp.year_built}
                      onChange={(e) => updateComparable(comp.id, 'year_built', e.target.value)}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Quality</Label>
                    <Select value={comp.quality} onValueChange={(v) => updateComparable(comp.id, 'quality', v)}>
                      <SelectTrigger className="h-9">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {QUALITY_OPTIONS.map(q => (
                          <SelectItem key={q.value} value={q.value}>{q.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Condition</Label>
                    <Select value={comp.condition} onValueChange={(v) => updateComparable(comp.id, 'condition', v)}>
                      <SelectTrigger className="h-9">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {CONDITION_OPTIONS.map(c => (
                          <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Location</Label>
                    <Select value={comp.location} onValueChange={(v) => updateComparable(comp.id, 'location', v)}>
                      <SelectTrigger className="h-9">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {LOCATION_OPTIONS.map(l => (
                          <SelectItem key={l.value} value={l.value}>{l.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            ))
          )}

          {/* Market Appreciation & Calculate */}
          <div className="flex items-end gap-4 pt-4 border-t">
            <div className="space-y-2 w-48">
              <Label>Market Appreciation (%/month)</Label>
              <Input
                type="number"
                step="0.1"
                value={appreciationRate}
                onChange={(e) => setAppreciationRate(e.target.value)}
                data-testid="input-appreciation-rate"
              />
            </div>
            <Button 
              onClick={handleCalculate} 
              disabled={isPending || comparables.length === 0}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700"
              data-testid="btn-calculate-sales"
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

      {/* Results */}
      {result && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Value Summary */}
          <Card className="ring-2 ring-emerald-200">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-emerald-500" />
                Reconciled Value
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-lg p-6 text-center">
                <p className="text-sm text-emerald-600 font-medium mb-1">Property Value</p>
                <p className="text-4xl font-bold text-emerald-900">
                  {formatCurrency(result.reconciled_value)}
                </p>
                <p className="text-sm text-emerald-700 mt-2">
                  {formatCurrency(result.value_per_sf)} / SF
                </p>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">Confidence Level</span>
                  <Badge 
                    className={
                      result.confidence_level === 'high' 
                        ? 'bg-emerald-100 text-emerald-800'
                        : result.confidence_level === 'medium'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-red-100 text-red-800'
                    }
                  >
                    {result.confidence_level?.toUpperCase()}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-slate-600">95% Confidence Range</span>
                  <span className="text-sm font-medium">
                    {formatCurrency(result.confidence_range_low, true)} - {formatCurrency(result.confidence_range_high, true)}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-500">Mean Price</p>
                  <p className="text-lg font-semibold">{formatCurrency(result.mean_adjusted_price, true)}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-500">Median Price</p>
                  <p className="text-lg font-semibold">{formatCurrency(result.median_adjusted_price, true)}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-500">Avg Gross Adj</p>
                  <p className="text-lg font-semibold">{formatPercent(result.avg_gross_adjustment_percent)}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-slate-500">Avg Net Adj</p>
                  <p className="text-lg font-semibold">{formatPercent(result.avg_net_adjustment_percent)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Adjusted Comparables */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Scale className="h-5 w-5 text-blue-500" />
                Adjusted Comparables
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {result.adjusted_comparables?.map((comp, idx) => (
                <div key={comp.comp_id} className="bg-slate-50 rounded-lg p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline">Comp {idx + 1}</Badge>
                    <span className="text-xs text-slate-500">
                      {comp.days_since_sale} days ago
                    </span>
                  </div>
                  
                  <div className="flex items-center justify-between text-sm">
                    <span>Original Price:</span>
                    <span className="font-medium">{formatCurrency(comp.original_sale_price, true)}</span>
                  </div>

                  <div className="space-y-1">
                    {comp.adjustments?.map((adj, i) => (
                      <div key={i} className="flex justify-between text-xs">
                        <span className="text-slate-600 capitalize">{adj.type}:</span>
                        <span className={parseFloat(adj.amount) >= 0 ? 'text-emerald-600' : 'text-red-600'}>
                          {parseFloat(adj.amount) >= 0 ? '+' : ''}{formatCurrency(adj.amount, true)}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center justify-between text-sm border-t pt-2">
                    <span className="font-medium">Adjusted Price:</span>
                    <span className="font-bold text-emerald-700">
                      {formatCurrency(comp.adjusted_price, true)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">Per SF:</span>
                    <span>{formatCurrency(comp.adjusted_price_per_sf)}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default SalesComparisonCalculator;
