/**
 * LEED Assessment Calculator Component
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Badge } from '../../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Slider } from '../../../components/ui/slider';
import { useLEEDAssessment } from '../hooks/useSustainability';
import { Calculator, Award, TrendingUp, Target, CheckCircle2, Leaf } from 'lucide-react';

const sectors = [
  { value: 'office', label: 'Office' },
  { value: 'retail', label: 'Retail' },
  { value: 'industrial', label: 'Industrial' },
  { value: 'multifamily', label: 'Multifamily' },
  { value: 'hotel', label: 'Hotel' },
  { value: 'healthcare', label: 'Healthcare' },
];

const regions = [
  { value: 'north_america', label: 'North America' },
  { value: 'europe', label: 'Europe' },
  { value: 'asia_pacific', label: 'Asia Pacific' },
];

const levelColors = {
  platinum: 'bg-violet-500',
  gold: 'bg-amber-500',
  silver: 'bg-slate-400',
  certified: 'bg-green-500',
};

const categoryConfig = [
  { key: 'integrative_process', label: 'Integrative Process', max: 1 },
  { key: 'location_transportation', label: 'Location & Transportation', max: 16 },
  { key: 'sustainable_sites', label: 'Sustainable Sites', max: 10 },
  { key: 'water_efficiency', label: 'Water Efficiency', max: 11 },
  { key: 'energy_atmosphere', label: 'Energy & Atmosphere', max: 33 },
  { key: 'materials_resources', label: 'Materials & Resources', max: 13 },
  { key: 'indoor_environmental_quality', label: 'Indoor Environmental Quality', max: 16 },
  { key: 'innovation', label: 'Innovation', max: 6 },
  { key: 'regional_priority', label: 'Regional Priority', max: 4 },
];

const formatCurrency = (value) => {
  if (!value) return '$0';
  const num = parseFloat(value);
  if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
  return `$${num.toFixed(0)}`;
};

export function LEEDCalculator() {
  const [formData, setFormData] = useState({
    property_name: '',
    property_sector: 'office',
    region: 'north_america',
    leed_version: 'v4.1',
    gross_floor_area_m2: '',
    current_value: '',
    category_scores: {
      integrative_process: 0,
      location_transportation: 8,
      sustainable_sites: 5,
      water_efficiency: 6,
      energy_atmosphere: 15,
      materials_resources: 6,
      indoor_environmental_quality: 8,
      innovation: 3,
      regional_priority: 2,
    },
  });
  const [result, setResult] = useState(null);

  const mutation = useLEEDAssessment();

  const handleCategoryChange = (key, value) => {
    setFormData((prev) => ({
      ...prev,
      category_scores: {
        ...prev.category_scores,
        [key]: value[0],
      },
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      ...formData,
      gross_floor_area_m2: parseFloat(formData.gross_floor_area_m2) || 10000,
      current_value: formData.current_value ? parseFloat(formData.current_value) : undefined,
    };
    mutation.mutate(payload, {
      onSuccess: (data) => setResult(data),
    });
  };

  const totalPoints = Object.values(formData.category_scores).reduce((a, b) => a + b, 0);

  const getCertLevel = (points) => {
    if (points >= 80) return 'Platinum';
    if (points >= 60) return 'Gold';
    if (points >= 50) return 'Silver';
    if (points >= 40) return 'Certified';
    return 'Not Certified';
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Calculator className="h-4 w-4 text-green-600" />
            LEED Assessment Input
          </CardTitle>
          <CardDescription>
            Enter property details and category scores to estimate LEED certification
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="property_name">Property Name</Label>
                <Input
                  id="property_name"
                  data-testid="leed-property-name"
                  value={formData.property_name}
                  onChange={(e) => setFormData((p) => ({ ...p, property_name: e.target.value }))}
                  placeholder="Downtown Office Tower"
                />
              </div>
              <div>
                <Label htmlFor="sector">Property Sector</Label>
                <Select
                  value={formData.property_sector}
                  onValueChange={(v) => setFormData((p) => ({ ...p, property_sector: v }))}
                >
                  <SelectTrigger data-testid="leed-sector">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {sectors.map((s) => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="gfa">Gross Floor Area (m²)</Label>
                <Input
                  id="gfa"
                  type="number"
                  data-testid="leed-gfa"
                  value={formData.gross_floor_area_m2}
                  onChange={(e) => setFormData((p) => ({ ...p, gross_floor_area_m2: e.target.value }))}
                  placeholder="50000"
                />
              </div>
              <div>
                <Label htmlFor="current_value">Current Value ($)</Label>
                <Input
                  id="current_value"
                  type="number"
                  data-testid="leed-value"
                  value={formData.current_value}
                  onChange={(e) => setFormData((p) => ({ ...p, current_value: e.target.value }))}
                  placeholder="100000000"
                />
              </div>
            </div>

            {/* Category Scores */}
            <div className="space-y-3 pt-4 border-t">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">Category Scores</Label>
                <div className="flex items-center gap-2">
                  <Badge
                    className={`${levelColors[getCertLevel(totalPoints).toLowerCase()] || 'bg-slate-300'} text-white`}
                  >
                    {getCertLevel(totalPoints)}
                  </Badge>
                  <span className="text-sm font-medium">{totalPoints}/110</span>
                </div>
              </div>

              <div className="space-y-3 max-h-64 overflow-y-auto pr-2">
                {categoryConfig.map((cat) => (
                  <div key={cat.key}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-600">{cat.label}</span>
                      <span className="font-medium">
                        {formData.category_scores[cat.key]}/{cat.max}
                      </span>
                    </div>
                    <Slider
                      value={[formData.category_scores[cat.key]]}
                      onValueChange={(v) => handleCategoryChange(cat.key, v)}
                      max={cat.max}
                      step={1}
                    />
                  </div>
                ))}
              </div>
            </div>

            <Button
              type="submit"
              className="w-full bg-green-600 hover:bg-green-700"
              disabled={mutation.isPending || !formData.property_name}
              data-testid="leed-calculate-btn"
            >
              {mutation.isPending ? 'Calculating...' : 'Calculate LEED Assessment'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-4">
        {result && (
          <>
            {/* Certification Level */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Leaf className="h-4 w-4 text-green-600" />
                  LEED Certification Result
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <div
                      className={`w-20 h-20 rounded-full ${
                        levelColors[result.certification_level] || 'bg-slate-300'
                      } flex items-center justify-center mb-2`}
                    >
                      <Award className="h-10 w-10 text-white" />
                    </div>
                    <Badge className={`${levelColors[result.certification_level] || 'bg-slate-400'} text-white`}>
                      {(result.certification_level || '').toUpperCase()}
                    </Badge>
                  </div>
                  <div className="flex-1">
                    <div className="text-4xl font-bold text-slate-800">{result.total_points}</div>
                    <div className="text-sm text-slate-500">out of 110 points</div>
                    {result.points_to_next_level && (
                      <div className="text-xs text-green-600 mt-1">
                        {result.points_to_next_level} points to next level
                      </div>
                    )}
                    <div className="text-xs text-slate-500 mt-1">
                      {result.percentile_in_market}th percentile in market
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Value Impact */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-emerald-600" />
                  Estimated Value Impact
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-emerald-50 rounded-lg">
                    <div className="text-xs text-emerald-600 mb-1">Value Premium</div>
                    <div className="text-xl font-bold text-emerald-700">
                      +{parseFloat(result.estimated_value_premium_percent || 0).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <div className="text-xs text-blue-600 mb-1">Rent Premium</div>
                    <div className="text-xl font-bold text-blue-700">
                      +{parseFloat(result.estimated_rent_premium_percent || 0).toFixed(1)}%
                    </div>
                  </div>
                  {result.estimated_value_impact && (
                    <div className="col-span-2 p-3 bg-green-50 rounded-lg">
                      <div className="text-xs text-green-600 mb-1">Estimated Value Impact</div>
                      <div className="text-2xl font-bold text-green-700">
                        {formatCurrency(result.estimated_value_impact)}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Category Performance */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Target className="h-4 w-4 text-blue-600" />
                  Category Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs text-slate-500 mb-1">Strongest Categories</div>
                    <div className="flex flex-wrap gap-1">
                      {(result.strongest_categories || []).map((cat) => (
                        <Badge key={cat} variant="outline" className="bg-emerald-50 text-emerald-700 text-xs">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          {cat.replace(/_/g, ' ')}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  {result.weakest_categories?.length > 0 && (
                    <div>
                      <div className="text-xs text-slate-500 mb-1">Areas for Improvement</div>
                      <div className="flex flex-wrap gap-1">
                        {result.weakest_categories.map((cat) => (
                          <Badge key={cat} variant="outline" className="bg-amber-50 text-amber-700 text-xs">
                            {cat.replace(/_/g, ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {Object.keys(result.improvement_potential || {}).length > 0 && (
                    <div className="pt-2 border-t">
                      <div className="text-xs text-slate-500 mb-2">Improvement Potential</div>
                      {Object.entries(result.improvement_potential).slice(0, 3).map(([cat, points]) => (
                        <div key={cat} className="flex justify-between text-xs mb-1">
                          <span className="text-slate-600">{cat.replace(/_/g, ' ')}</span>
                          <span className="text-green-600 font-medium">+{points} pts possible</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {!result && (
          <Card className="border-dashed">
            <CardContent className="py-12 text-center text-slate-500">
              <Leaf className="h-12 w-12 mx-auto mb-4 text-slate-300" />
              <p>Enter property details and category scores to calculate LEED assessment</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
