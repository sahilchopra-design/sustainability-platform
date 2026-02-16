/**
 * Sustainability Dashboard Component
 * Displays KPIs and certification overview
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { useSustainabilityDashboard, useCertifications } from '../hooks/useSustainability';
import { Award, Building2, TrendingUp, AlertTriangle, Leaf, DollarSign, CheckCircle2 } from 'lucide-react';

const formatCurrency = (value) => {
  if (!value) return '$0';
  const num = parseFloat(value);
  if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
  if (num >= 1e3) return `$${(num / 1e3).toFixed(0)}K`;
  return `$${num.toFixed(0)}`;
};

const certTypeLabels = {
  leed: 'LEED',
  breeam: 'BREEAM',
  gresb: 'GRESB',
  energy_star: 'Energy Star',
  well: 'WELL',
};

const certLevelColors = {
  platinum: 'bg-violet-100 text-violet-700',
  gold: 'bg-amber-100 text-amber-700',
  silver: 'bg-slate-100 text-slate-600',
  certified: 'bg-green-100 text-green-700',
  outstanding: 'bg-violet-100 text-violet-700',
  excellent: 'bg-blue-100 text-blue-700',
  very_good: 'bg-emerald-100 text-emerald-700',
  good: 'bg-green-100 text-green-700',
  pass: 'bg-slate-100 text-slate-600',
  '5_star': 'bg-violet-100 text-violet-700',
  '4_star': 'bg-blue-100 text-blue-700',
  '3_star': 'bg-emerald-100 text-emerald-700',
  '2_star': 'bg-amber-100 text-amber-700',
  '1_star': 'bg-slate-100 text-slate-600',
};

export function SustainabilityDashboard() {
  const { data: dashboard, isLoading: dashLoading } = useSustainabilityDashboard();
  const { data: certData, isLoading: certLoading } = useCertifications({});

  if (dashLoading || certLoading) {
    return (
      <div className="p-6 text-center text-slate-500">Loading dashboard...</div>
    );
  }

  const kpis = dashboard || {};
  const certifications = certData?.items || [];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card data-testid="kpi-certified-count">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Certified Properties</p>
                <p className="text-2xl font-bold text-slate-900">{kpis.total_certified_properties || 0}</p>
                <p className="text-xs text-emerald-600 mt-1">
                  {kpis.certification_coverage_percent || 0}% coverage
                </p>
              </div>
              <div className="p-3 bg-emerald-100 rounded-lg">
                <CheckCircle2 className="h-6 w-6 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card data-testid="kpi-certified-value">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Certified AUM</p>
                <p className="text-2xl font-bold text-slate-900">
                  {formatCurrency(kpis.total_certified_value)}
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  +{kpis.avg_value_premium_captured || 0}% premium captured
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <DollarSign className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card data-testid="kpi-potential-uplift">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Potential Uplift</p>
                <p className="text-2xl font-bold text-slate-900">
                  {formatCurrency(kpis.potential_value_uplift)}
                </p>
                <p className="text-xs text-amber-600 mt-1">
                  {kpis.total_uncertified_properties || 0} uncertified assets
                </p>
              </div>
              <div className="p-3 bg-amber-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card data-testid="kpi-avg-scores">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Avg GRESB Score</p>
                <p className="text-2xl font-bold text-slate-900">
                  {kpis.avg_gresb_score || '-'}
                </p>
                <div className="flex gap-2 mt-1">
                  {kpis.avg_leed_points && (
                    <span className="text-xs text-slate-500">LEED: {kpis.avg_leed_points}pts</span>
                  )}
                </div>
              </div>
              <div className="p-3 bg-violet-100 rounded-lg">
                <Award className="h-6 w-6 text-violet-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Certification Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Leaf className="h-4 w-4 text-emerald-600" />
              Certifications by Type
            </CardTitle>
            <CardDescription>Distribution of certification frameworks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(kpis.by_certification_type || {}).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="bg-slate-50">
                      {certTypeLabels[type] || type.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-32 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{
                          width: `${(count / (kpis.total_certified_properties || 1)) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-sm font-medium text-slate-700 w-8 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Award className="h-4 w-4 text-violet-600" />
              Certifications by Level
            </CardTitle>
            <CardDescription>Performance tier breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {Object.entries(kpis.by_level || {}).map(([level, count]) => (
                <Badge
                  key={level}
                  variant="outline"
                  className={`${certLevelColors[level] || 'bg-slate-100 text-slate-700'}`}
                >
                  {level.replace('_', ' ')} ({count})
                </Badge>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Certifications This Year</span>
                <span className="font-medium text-emerald-600">+{kpis.certifications_this_year || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm mt-2">
                <span className="text-slate-500">Expiring Soon</span>
                <span className="font-medium text-amber-600">{kpis.certifications_expiring_soon || 0}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Certifications Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Building2 className="h-4 w-4 text-slate-600" />
            Certified Properties
          </CardTitle>
          <CardDescription>Properties with active sustainability certifications</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="certifications-table">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-3 px-2 font-medium text-slate-600">Property</th>
                  <th className="text-left py-3 px-2 font-medium text-slate-600">Certification</th>
                  <th className="text-left py-3 px-2 font-medium text-slate-600">Level</th>
                  <th className="text-right py-3 px-2 font-medium text-slate-600">Score</th>
                  <th className="text-right py-3 px-2 font-medium text-slate-600">Value Premium</th>
                  <th className="text-right py-3 px-2 font-medium text-slate-600">Impact</th>
                </tr>
              </thead>
              <tbody>
                {certifications.map((cert, idx) => (
                  <tr key={cert.id || idx} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-2">
                      <div className="font-medium text-slate-800">{cert.property_name}</div>
                      <div className="text-xs text-slate-500 capitalize">{cert.property_sector}</div>
                    </td>
                    <td className="py-3 px-2">
                      <Badge variant="outline" className="bg-slate-50">
                        {certTypeLabels[cert.certification_type] || cert.certification_type?.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="py-3 px-2">
                      <Badge
                        className={`${certLevelColors[cert.certification_level] || 'bg-slate-100 text-slate-700'}`}
                      >
                        {(cert.certification_level || '').replace('_', ' ')}
                      </Badge>
                    </td>
                    <td className="py-3 px-2 text-right font-medium">
                      {cert.score || '-'}
                    </td>
                    <td className="py-3 px-2 text-right text-emerald-600 font-medium">
                      +{cert.value_premium_percent || 0}%
                    </td>
                    <td className="py-3 px-2 text-right font-medium text-slate-800">
                      {formatCurrency(cert.estimated_value_impact)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
