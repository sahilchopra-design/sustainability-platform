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
  gold: 'bg-amber-100 text-amber-400',
  silver: 'bg-white/[0.06] text-white/60',
  certified: 'bg-green-100 text-green-400',
  outstanding: 'bg-violet-100 text-violet-700',
  excellent: 'bg-blue-100 text-blue-300',
  very_good: 'bg-emerald-100 text-emerald-400',
  good: 'bg-green-100 text-green-400',
  pass: 'bg-white/[0.06] text-white/60',
  '5_star': 'bg-violet-100 text-violet-700',
  '4_star': 'bg-blue-100 text-blue-300',
  '3_star': 'bg-emerald-100 text-emerald-400',
  '2_star': 'bg-amber-100 text-amber-400',
  '1_star': 'bg-white/[0.06] text-white/60',
};

export function SustainabilityDashboard() {
  const { data: dashboard, isLoading: dashLoading } = useSustainabilityDashboard();
  const { data: certData, isLoading: certLoading } = useCertifications({});

  if (dashLoading || certLoading) {
    return (
      <div className="p-6 text-center text-white/40">Loading dashboard...</div>
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
                <p className="text-sm text-white/40">Certified Properties</p>
                <p className="text-2xl font-bold text-white">{kpis.total_certified_properties || 0}</p>
                <p className="text-xs text-emerald-400 mt-1">
                  {kpis.certification_coverage_percent || 0}% coverage
                </p>
              </div>
              <div className="p-3 bg-emerald-100 rounded-lg">
                <CheckCircle2 className="h-6 w-6 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card data-testid="kpi-certified-value">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/40">Certified AUM</p>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(kpis.total_certified_value)}
                </p>
                <p className="text-xs text-blue-300 mt-1">
                  +{kpis.avg_value_premium_captured || 0}% premium captured
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <DollarSign className="h-6 w-6 text-blue-300" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card data-testid="kpi-potential-uplift">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/40">Potential Uplift</p>
                <p className="text-2xl font-bold text-white">
                  {formatCurrency(kpis.potential_value_uplift)}
                </p>
                <p className="text-xs text-amber-400 mt-1">
                  {kpis.total_uncertified_properties || 0} uncertified assets
                </p>
              </div>
              <div className="p-3 bg-amber-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card data-testid="kpi-avg-scores">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/40">Avg GRESB Score</p>
                <p className="text-2xl font-bold text-white">
                  {kpis.avg_gresb_score || '-'}
                </p>
                <div className="flex gap-2 mt-1">
                  {kpis.avg_leed_points && (
                    <span className="text-xs text-white/40">LEED: {kpis.avg_leed_points}pts</span>
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
              <Leaf className="h-4 w-4 text-emerald-400" />
              Certifications by Type
            </CardTitle>
            <CardDescription>Distribution of certification frameworks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(kpis.by_certification_type || {}).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="bg-white/[0.02]">
                      {certTypeLabels[type] || type.toUpperCase()}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="w-32 h-2 bg-white/[0.06] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{
                          width: `${(count / (kpis.total_certified_properties || 1)) * 100}%`,
                        }}
                      />
                    </div>
                    <span className="text-sm font-medium text-white/70 w-8 text-right">{count}</span>
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
                  className={`${certLevelColors[level] || 'bg-white/[0.06] text-white/70'}`}
                >
                  {level.replace('_', ' ')} ({count})
                </Badge>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-white/[0.04]">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/40">Certifications This Year</span>
                <span className="font-medium text-emerald-400">+{kpis.certifications_this_year || 0}</span>
              </div>
              <div className="flex items-center justify-between text-sm mt-2">
                <span className="text-white/40">Expiring Soon</span>
                <span className="font-medium text-amber-400">{kpis.certifications_expiring_soon || 0}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Certifications Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Building2 className="h-4 w-4 text-white/60" />
            Certified Properties
          </CardTitle>
          <CardDescription>Properties with active sustainability certifications</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" data-testid="certifications-table">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="text-left py-3 px-2 font-medium text-white/60">Property</th>
                  <th className="text-left py-3 px-2 font-medium text-white/60">Certification</th>
                  <th className="text-left py-3 px-2 font-medium text-white/60">Level</th>
                  <th className="text-right py-3 px-2 font-medium text-white/60">Score</th>
                  <th className="text-right py-3 px-2 font-medium text-white/60">Value Premium</th>
                  <th className="text-right py-3 px-2 font-medium text-white/60">Impact</th>
                </tr>
              </thead>
              <tbody>
                {certifications.map((cert, idx) => (
                  <tr key={cert.id || idx} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                    <td className="py-3 px-2">
                      <div className="font-medium text-white/90">{cert.property_name}</div>
                      <div className="text-xs text-white/40 capitalize">{cert.property_sector}</div>
                    </td>
                    <td className="py-3 px-2">
                      <Badge variant="outline" className="bg-white/[0.02]">
                        {certTypeLabels[cert.certification_type] || cert.certification_type?.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="py-3 px-2">
                      <Badge
                        className={`${certLevelColors[cert.certification_level] || 'bg-white/[0.06] text-white/70'}`}
                      >
                        {(cert.certification_level || '').replace('_', ' ')}
                      </Badge>
                    </td>
                    <td className="py-3 px-2 text-right font-medium">
                      {cert.score || '-'}
                    </td>
                    <td className="py-3 px-2 text-right text-emerald-400 font-medium">
                      +{cert.value_premium_percent || 0}%
                    </td>
                    <td className="py-3 px-2 text-right font-medium text-white/90">
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
