/**
 * GRESB Assessment Calculator Component
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Badge } from '../../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Slider } from '../../../components/ui/slider';
import { useGRESBAssessment, useGRESBBenchmarks } from '../hooks/useSustainability';
import { Calculator, Star, TrendingUp, Target, AlertCircle, Award, BarChart3 } from 'lucide-react';

const regions = [
  { value: 'north_america', label: 'North America' },
  { value: 'europe', label: 'Europe' },
  { value: 'asia_pacific', label: 'Asia Pacific' },
  { value: 'middle_east', label: 'Middle East' },
  { value: 'latin_america', label: 'Latin America' },
];

const starRatingColors = {
  '5_star': 'bg-violet-500',
  '4_star': 'bg-blue-500',
  '3_star': 'bg-emerald-500',
  '2_star': 'bg-amber-500',
  '1_star': 'bg-white/[0.08]',
};

const formatCurrency = (value) => {
  if (!value) return '$0';
  const num = parseFloat(value);
  if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
  return `$${num.toFixed(0)}`;
};

export function GRESBCalculator() {
  const [formData, setFormData] = useState({
    portfolio_name: '',
    entity_type: 'standing_investments',
    region: 'north_america',
    total_aum: '',
    num_assets: '',
    component_scores: {
      management: 15,
      policy: 6,
      risk_management: 7,
      stakeholder_engagement: 7,
      performance_indicators: 15,
    },
  });
  const [result, setResult] = useState(null);

  const mutation = useGRESBAssessment();
  const { data: benchmarks } = useGRESBBenchmarks(formData.region);

  const handleComponentChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      component_scores: {
        ...prev.component_scores,
        [field]: value[0],
      },
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const payload = {
      ...formData,
      total_aum: parseFloat(formData.total_aum) || 0,
      num_assets: parseInt(formData.num_assets) || 1,
    };
    mutation.mutate(payload, {
      onSuccess: (data) => setResult(data),
    });
  };

  const totalScore =
    formData.component_scores.management +
    formData.component_scores.policy +
    formData.component_scores.risk_management +
    formData.component_scores.stakeholder_engagement +
    formData.component_scores.performance_indicators;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Calculator className="h-4 w-4 text-violet-600" />
            GRESB Assessment Input
          </CardTitle>
          <CardDescription>
            Enter your portfolio details and component scores to calculate GRESB rating
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="portfolio_name">Portfolio Name</Label>
                <Input
                  id="portfolio_name"
                  data-testid="gresb-portfolio-name"
                  value={formData.portfolio_name}
                  onChange={(e) => setFormData((p) => ({ ...p, portfolio_name: e.target.value }))}
                  placeholder="Core Real Estate Fund"
                />
              </div>
              <div>
                <Label htmlFor="region">Region</Label>
                <Select
                  value={formData.region}
                  onValueChange={(v) => setFormData((p) => ({ ...p, region: v }))}
                >
                  <SelectTrigger data-testid="gresb-region">
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

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="total_aum">Total AUM ($)</Label>
                <Input
                  id="total_aum"
                  type="number"
                  data-testid="gresb-aum"
                  value={formData.total_aum}
                  onChange={(e) => setFormData((p) => ({ ...p, total_aum: e.target.value }))}
                  placeholder="2500000000"
                />
              </div>
              <div>
                <Label htmlFor="num_assets">Number of Assets</Label>
                <Input
                  id="num_assets"
                  type="number"
                  data-testid="gresb-num-assets"
                  value={formData.num_assets}
                  onChange={(e) => setFormData((p) => ({ ...p, num_assets: e.target.value }))}
                  placeholder="25"
                />
              </div>
            </div>

            {/* Component Scores */}
            <div className="space-y-4 pt-4 border-t">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-medium">Component Scores</Label>
                <Badge variant="outline" className="bg-violet-50 text-violet-700">
                  Total: {totalScore}/100
                </Badge>
              </div>

              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-white/60">Management (max 30)</span>
                    <span className="font-medium">{formData.component_scores.management}</span>
                  </div>
                  <Slider
                    value={[formData.component_scores.management]}
                    onValueChange={(v) => handleComponentChange('management', v)}
                    max={30}
                    step={1}
                    className="w-full"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-white/60">Policy (max 12)</span>
                    <span className="font-medium">{formData.component_scores.policy}</span>
                  </div>
                  <Slider
                    value={[formData.component_scores.policy]}
                    onValueChange={(v) => handleComponentChange('policy', v)}
                    max={12}
                    step={1}
                  />
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-white/60">Risk Management (max 14)</span>
                    <span className="font-medium">{formData.component_scores.risk_management}</span>
                  </div>
                  <Slider
                    value={[formData.component_scores.risk_management]}
                    onValueChange={(v) => handleComponentChange('risk_management', v)}
                    max={14}
                    step={1}
                  />
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-white/60">Stakeholder Engagement (max 14)</span>
                    <span className="font-medium">{formData.component_scores.stakeholder_engagement}</span>
                  </div>
                  <Slider
                    value={[formData.component_scores.stakeholder_engagement]}
                    onValueChange={(v) => handleComponentChange('stakeholder_engagement', v)}
                    max={14}
                    step={1}
                  />
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-white/60">Performance Indicators (max 30)</span>
                    <span className="font-medium">{formData.component_scores.performance_indicators}</span>
                  </div>
                  <Slider
                    value={[formData.component_scores.performance_indicators]}
                    onValueChange={(v) => handleComponentChange('performance_indicators', v)}
                    max={30}
                    step={1}
                  />
                </div>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full bg-violet-600 hover:bg-violet-700"
              disabled={mutation.isPending || !formData.portfolio_name || !formData.total_aum}
              data-testid="gresb-calculate-btn"
            >
              {mutation.isPending ? 'Calculating...' : 'Calculate GRESB Assessment'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      <div className="space-y-4">
        {result && (
          <>
            {/* Star Rating */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Star className="h-4 w-4 text-amber-500" />
                  GRESB Rating Result
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-6">
                  <div className="text-center">
                    <div className="flex items-center gap-1 mb-1">
                      {[1, 2, 3, 4, 5].map((star) => (
                        <Star
                          key={star}
                          className={`h-8 w-8 ${
                            parseInt(result.star_rating?.charAt(0)) >= star
                              ? 'fill-amber-400 text-amber-400'
                              : 'text-white/15'
                          }`}
                        />
                      ))}
                    </div>
                    <Badge className={`${starRatingColors[result.star_rating] || 'bg-white/[0.08]'} text-white`}>
                      {result.star_rating?.replace('_', ' ').toUpperCase()}
                    </Badge>
                  </div>
                  <div className="flex-1">
                    <div className="text-4xl font-bold text-white/90">{result.total_score}</div>
                    <div className="text-sm text-white/40">out of 100 points</div>
                    {result.score_to_next_star && (
                      <div className="text-xs text-violet-600 mt-1">
                        {result.score_to_next_star} points to next star
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Benchmark Comparison */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-blue-300" />
                  Benchmark Comparison
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-white/60">Percentile Rank</span>
                    <Badge variant="outline" className="bg-blue-500/10 text-blue-300">
                      {result.percentile_rank}th percentile
                    </Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-white/60">Peer Group Average</span>
                    <span className="font-medium">{result.benchmark?.peer_avg_score}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-white/60">Top Quartile Threshold</span>
                    <span className="font-medium text-emerald-400">{result.benchmark?.top_quartile_threshold}</span>
                  </div>
                  <div className="w-full h-2 bg-white/[0.06] rounded-full mt-2 relative">
                    <div
                      className="absolute h-full bg-violet-500 rounded-full"
                      style={{ width: `${result.total_score}%` }}
                    />
                    <div
                      className="absolute w-0.5 h-4 bg-emerald-500 -top-1"
                      style={{ left: `${result.benchmark?.top_quartile_threshold}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Value Impact */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-emerald-400" />
                  Estimated Value Impact
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-emerald-500/10 rounded-lg">
                    <div className="text-xs text-emerald-400 mb-1">Value Premium</div>
                    <div className="text-xl font-bold text-emerald-400">
                      +{result.estimated_value_premium_percent}%
                    </div>
                  </div>
                  <div className="p-3 bg-blue-500/10 rounded-lg">
                    <div className="text-xs text-blue-300 mb-1">Rent Premium</div>
                    <div className="text-xl font-bold text-blue-300">
                      +{result.estimated_rent_premium_percent}%
                    </div>
                  </div>
                  <div className="col-span-2 p-3 bg-violet-50 rounded-lg">
                    <div className="text-xs text-violet-600 mb-1">Estimated Value Impact</div>
                    <div className="text-2xl font-bold text-violet-700">
                      {formatCurrency(result.estimated_value_impact)}
                    </div>
                  </div>
                  <div className="col-span-2 text-xs text-white/40">
                    Cap rate compression: {result.cap_rate_compression_bps} bps
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recommendations */}
            {result.improvement_recommendations?.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Target className="h-4 w-4 text-amber-400" />
                    Improvement Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {result.improvement_recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm">
                        <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
                        <span className="text-white/70">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </>
        )}

        {!result && (
          <Card className="border-dashed">
            <CardContent className="py-12 text-center text-white/40">
              <Award className="h-12 w-12 mx-auto mb-4 text-white/20" />
              <p>Enter portfolio details and component scores to calculate GRESB assessment</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
