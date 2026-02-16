/**
 * Value Impact Calculator Component
 * Calculates the financial impact of green certifications
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Badge } from '../../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { useValueImpact } from '../hooks/useSustainability';
import { Calculator, DollarSign, TrendingUp, BookOpen, Building2, Leaf } from 'lucide-react';

const certTypes = [
  { value: 'leed', label: 'LEED' },
  { value: 'breeam', label: 'BREEAM' },
  { value: 'energy_star', label: 'Energy Star' },
  { value: 'gresb', label: 'GRESB' },
  { value: 'well', label: 'WELL' },
];

const leedLevels = [
  { value: 'certified', label: 'Certified' },
  { value: 'silver', label: 'Silver' },
  { value: 'gold', label: 'Gold' },
  { value: 'platinum', label: 'Platinum' },
];

const breeamLevels = [
  { value: 'pass', label: 'Pass' },
  { value: 'good', label: 'Good' },
  { value: 'very_good', label: 'Very Good' },
  { value: 'excellent', label: 'Excellent' },
  { value: 'outstanding', label: 'Outstanding' },
];

const sectors = [
  { value: 'office', label: 'Office' },
  { value: 'retail', label: 'Retail' },
  { value: 'industrial', label: 'Industrial' },
  { value: 'multifamily', label: 'Multifamily' },
  { value: 'hotel', label: 'Hotel' },
];

const regions = [
  { value: 'north_america', label: 'North America' },
  { value: 'europe', label: 'Europe' },
  { value: 'asia_pacific', label: 'Asia Pacific' },
];

const formatCurrency = (value) => {
  if (!value) return '$0';
  const num = parseFloat(value);
  if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
  if (num >= 1e3) return `$${(num / 1e3).toFixed(0)}K`;
  return `$${num.toFixed(0)}`;
};

export function ValueImpactCalculator() {
  const [formData, setFormData] = useState({
    certification_type: 'leed',
    certification_level: 'gold',
    property_sector: 'office',
    region: 'north_america',
    current_value: '',
    current_noi: '',
    gross_floor_area_sf: '',
    current_rent_psf: '',
  });
  const [result, setResult] = useState(null);

  const mutation = useValueImpact();

  const getLevelsForCertType = () => {
    switch (formData.certification_type) {
      case 'leed':
        return leedLevels;
      case 'breeam':
        return breeamLevels;
      case 'energy_star':
        return [{ value: 'certified', label: 'Certified' }];
      case 'gresb':
        return [
          { value: '1_star', label: '1 Star' },
          { value: '2_star', label: '2 Star' },
          { value: '3_star', label: '3 Star' },
          { value: '4_star', label: '4 Star' },
          { value: '5_star', label: '5 Star' },
        ];
      case 'well':
        return [
          { value: 'silver', label: 'Silver' },
          { value: 'gold', label: 'Gold' },
          { value: 'platinum', label: 'Platinum' },
        ];
      default:
        return leedLevels;
    }
  };

  const handleCertTypeChange = (value) => {
    const levels = getLevelsForCertType();
    setFormData((p) => ({
      ...p,
      certification_type: value,
      certification_level: value === 'leed' ? 'gold' : value === 'breeam' ? 'very_good' : levels[0]?.value || 'certified',
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      ...formData,
      current_value: parseFloat(formData.current_value) || 0,
      current_noi: formData.current_noi ? parseFloat(formData.current_noi) : undefined,
      gross_floor_area_sf: formData.gross_floor_area_sf ? parseFloat(formData.gross_floor_area_sf) : undefined,
      current_rent_psf: formData.current_rent_psf ? parseFloat(formData.current_rent_psf) : undefined,
    };
    mutation.mutate(payload, {
      onSuccess: (data) => setResult(data),
    });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Calculator className="h-4 w-4 text-blue-600" />
            Value Impact Analysis
          </CardTitle>
          <CardDescription>
            Calculate the financial impact of obtaining a green certification
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Certification Type</Label>
                <Select
                  value={formData.certification_type}
                  onValueChange={handleCertTypeChange}
                >
                  <SelectTrigger data-testid="value-cert-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {certTypes.map((c) => (
                      <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Certification Level</Label>
                <Select
                  value={formData.certification_level}
                  onValueChange={(v) => setFormData((p) => ({ ...p, certification_level: v }))}
                >
                  <SelectTrigger data-testid="value-cert-level">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {getLevelsForCertType().map((l) => (
                      <SelectItem key={l.value} value={l.value}>{l.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Property Sector</Label>
                <Select
                  value={formData.property_sector}
                  onValueChange={(v) => setFormData((p) => ({ ...p, property_sector: v }))}
                >
                  <SelectTrigger data-testid="value-sector">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {sectors.map((s) => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Region</Label>
                <Select
                  value={formData.region}
                  onValueChange={(v) => setFormData((p) => ({ ...p, region: v }))}
                >
                  <SelectTrigger data-testid="value-region">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {regions.map((r) => (
                      <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="pt-4 border-t">
              <Label className="text-sm font-medium">Property Financials</Label>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="current_value">Current Value ($)</Label>
                <Input
                  id="current_value"
                  type="number"
                  data-testid="value-current-value"
                  value={formData.current_value}
                  onChange={(e) => setFormData((p) => ({ ...p, current_value: e.target.value }))}
                  placeholder="100000000"
                />
              </div>
              <div>
                <Label htmlFor="current_noi">Current NOI ($)</Label>
                <Input
                  id="current_noi"
                  type="number"
                  data-testid="value-noi"
                  value={formData.current_noi}
                  onChange={(e) => setFormData((p) => ({ ...p, current_noi: e.target.value }))}
                  placeholder="5000000"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="gfa_sf">Gross Floor Area (SF)</Label>
                <Input
                  id="gfa_sf"
                  type="number"
                  data-testid="value-gfa"
                  value={formData.gross_floor_area_sf}
                  onChange={(e) => setFormData((p) => ({ ...p, gross_floor_area_sf: e.target.value }))}
                  placeholder="450000"
                />
              </div>
              <div>
                <Label htmlFor="rent_psf">Current Rent ($/SF)</Label>
                <Input
                  id="rent_psf"
                  type="number"
                  data-testid="value-rent"
                  value={formData.current_rent_psf}
                  onChange={(e) => setFormData((p) => ({ ...p, current_rent_psf: e.target.value }))}
                  placeholder="65"
                />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700"
              disabled={mutation.isPending || !formData.current_value}
              data-testid="value-calculate-btn"
            >
              {mutation.isPending ? 'Calculating...' : 'Calculate Value Impact'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-4">
        {result && (
          <>
            {/* Main Impact */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-emerald-600" />
                  Estimated Value Impact
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center mb-4">
                  <div className="text-4xl font-bold text-emerald-600">
                    {formatCurrency(result.estimated_value_increase)}
                  </div>
                  <div className="text-sm text-slate-500">
                    Estimated value uplift from{' '}
                    <Badge variant="outline" className="ml-1">
                      {result.certification_type?.toUpperCase()} {result.certification_level?.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="p-3 bg-emerald-50 rounded-lg text-center">
                    <div className="text-xs text-emerald-600 mb-1">Value Premium</div>
                    <div className="text-xl font-bold text-emerald-700">
                      +{parseFloat(result.value_premium_percent || 0).toFixed(1)}%
                    </div>
                    <div className="text-[10px] text-emerald-500 mt-1">
                      Range: {parseFloat(result.value_premium_range?.low || 0).toFixed(1)}% - {parseFloat(result.value_premium_range?.high || 0).toFixed(1)}%
                    </div>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg text-center">
                    <div className="text-xs text-blue-600 mb-1">Rent Premium</div>
                    <div className="text-xl font-bold text-blue-700">
                      +{parseFloat(result.rent_premium_percent || 0).toFixed(1)}%
                    </div>
                    <div className="text-[10px] text-blue-500 mt-1">
                      Range: {parseFloat(result.rent_premium_range?.low || 0).toFixed(1)}% - {parseFloat(result.rent_premium_range?.high || 0).toFixed(1)}%
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Additional Metrics */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-violet-600" />
                  Financial Benefits
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {result.estimated_rent_premium_psf && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-600">Rent Premium per SF</span>
                      <span className="font-medium text-emerald-600">
                        +${parseFloat(result.estimated_rent_premium_psf).toFixed(2)}/SF
                      </span>
                    </div>
                  )}
                  {result.estimated_annual_rent_increase && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-600">Annual Rent Increase</span>
                      <span className="font-medium text-emerald-600">
                        {formatCurrency(result.estimated_annual_rent_increase)}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">Cap Rate Compression</span>
                    <span className="font-medium text-violet-600">
                      {result.cap_rate_compression_bps} bps
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">Operating Cost Savings</span>
                    <span className="font-medium text-blue-600">
                      {parseFloat(result.estimated_operating_cost_savings_percent || 0).toFixed(1)}%
                    </span>
                  </div>
                  {result.estimated_annual_cost_savings && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-600">Annual Cost Savings</span>
                      <span className="font-medium text-emerald-600">
                        {formatCurrency(result.estimated_annual_cost_savings)}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">Regional Adjustment</span>
                    <span className="font-medium">
                      {parseFloat(result.regional_adjustment || 1).toFixed(2)}x
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Sources */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-slate-600" />
                  Research Sources
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-slate-600">Data Reliability</span>
                  <Badge
                    variant="outline"
                    className={
                      result.data_reliability === 'high'
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-amber-50 text-amber-700'
                    }
                  >
                    {result.data_reliability}
                  </Badge>
                </div>
                <ul className="space-y-1 text-xs text-slate-600">
                  {(result.source_studies || []).slice(0, 4).map((source, idx) => (
                    <li key={idx} className="flex items-start gap-1">
                      <span className="text-slate-400">•</span>
                      {source}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </>
        )}

        {!result && (
          <Card className="border-dashed">
            <CardContent className="py-12 text-center text-slate-500">
              <Building2 className="h-12 w-12 mx-auto mb-4 text-slate-300" />
              <p>Select certification type and enter property financials to estimate value impact</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
