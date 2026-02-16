import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { 
  Fuel, Factory, Building2, AlertTriangle, TrendingDown, 
  DollarSign, BarChart3, Target, Zap
} from 'lucide-react';
import { useDashboardKPIs, useCriticalAssets, useMapData } from '../../hooks/useStrandedAssets';
import { AssetMapViewer } from '../../../../components/shared/AssetMapViewer';
import { ExportButton } from '../../../../components/shared/ExportButton';
import { exportStrandedAssets } from '../../../../lib/exportUtils';

const RISK_COLORS = {
  low: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200' },
  medium: { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200' },
  high: { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
  critical: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
};

const formatCurrency = (value) => {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  return `$${value.toFixed(0)}`;
};

export function StrandedAssetDashboard() {
  const { data: kpis, loading: kpisLoading } = useDashboardKPIs();
  const { data: criticalData, loading: criticalLoading } = useCriticalAssets({ risk_threshold: 'high' });
  const { data: mapData, loading: mapLoading } = useMapData();

  if (kpisLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  const riskDistribution = kpis?.assets_by_risk_category || {};
  
  const handleExport = async (format) => {
    await exportStrandedAssets({
      total_exposure_usd: kpis?.total_exposure_usd || 0,
      stranded_value_at_risk_usd: kpis?.stranded_value_at_risk_usd || 0,
      assets_by_risk_category: riskDistribution,
      total_assets: kpis?.total_assets || 0,
      avg_stranding_year: kpis?.avg_stranding_year || 0,
      critical_assets: criticalData?.assets || [],
    }, format);
  };

  return (
    <div className="space-y-6" data-testid="stranded-asset-dashboard">
      {/* Header with Export Button */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-800">Stranded Asset Overview</h2>
        <ExportButton 
          onExport={handleExport}
          label="Export Analysis"
          disabled={kpisLoading}
          data-testid="stranded-asset-export-btn"
        />
      </div>
      
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Exposure */}
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Total Exposure</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {formatCurrency(parseFloat(kpis?.total_exposure_usd || 0))}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {kpis?.total_assets || 0} assets tracked
                </p>
              </div>
              <div className="p-3 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
                <DollarSign className="h-6 w-6 text-amber-600 dark:text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Stranded Value at Risk */}
        <Card className="border-l-4 border-l-red-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Value at Risk</p>
                <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {formatCurrency(parseFloat(kpis?.stranded_value_at_risk_usd || 0))}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {((parseFloat(kpis?.stranded_value_at_risk_usd || 0) / parseFloat(kpis?.total_exposure_usd || 1)) * 100).toFixed(1)}% of exposure
                </p>
              </div>
              <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-lg">
                <TrendingDown className="h-6 w-6 text-red-600 dark:text-red-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* High Risk Assets */}
        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">High Risk Assets</p>
                <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                  {(kpis?.high_risk_assets || 0) + (kpis?.critical_risk_assets || 0)}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  {kpis?.critical_risk_assets || 0} critical
                </p>
              </div>
              <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <AlertTriangle className="h-6 w-6 text-orange-600 dark:text-orange-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Avg Risk Score */}
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Avg Risk Score</p>
                <p className="text-2xl font-bold text-slate-900 dark:text-white">
                  {(parseFloat(kpis?.avg_stranding_risk_score || 0) * 100).toFixed(0)}%
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Portfolio weighted
                </p>
              </div>
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Target className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Asset Type Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Fuel className="h-4 w-4 text-blue-500" />
              Fossil Fuel Reserves
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{kpis?.total_reserves_count || 0}</p>
            <p className="text-xs text-slate-500">Oil, Gas, Coal reserves</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Factory className="h-4 w-4 text-emerald-500" />
              Power Plants
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{kpis?.total_plants_count || 0}</p>
            <p className="text-xs text-slate-500">Coal, Gas, Nuclear facilities</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Building2 className="h-4 w-4 text-purple-500" />
              Infrastructure
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{kpis?.total_infrastructure_count || 0}</p>
            <p className="text-xs text-slate-500">Pipelines, Terminals, Refineries</p>
          </CardContent>
        </Card>
      </div>

      {/* Asset Map Visualization */}
      <div className="w-full">
        {mapLoading ? (
          <Card>
            <CardContent className="flex items-center justify-center h-[500px]">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
            </CardContent>
          </Card>
        ) : (
          <AssetMapViewer
            assets={mapData?.assets || []}
            title="Stranded Asset Map"
            subtitle="Geographic distribution of assets by risk level"
            height="500px"
            initialCenter={[0, 25]}
            initialZoom={1.8}
            showFilters={true}
            showLegend={true}
            module="stranded-assets"
          />
        )}
      </div>

      {/* Risk Distribution & Critical Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Risk Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(RISK_COLORS).map(([level, colors]) => {
                const count = riskDistribution[level] || 0;
                const total = Object.values(riskDistribution).reduce((a, b) => a + b, 0) || 1;
                const percentage = (count / total) * 100;
                
                return (
                  <div key={level} className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="capitalize font-medium">{level} Risk</span>
                      <span className="text-slate-500">{count} assets ({percentage.toFixed(0)}%)</span>
                    </div>
                    <div className="h-3 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${colors.bg} ${colors.border} border-r-2`}
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Critical Alerts */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              Critical Asset Alerts
              {criticalData?.total > 0 && (
                <Badge variant="destructive" className="ml-2">
                  {criticalData.total}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {criticalLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-red-500"></div>
              </div>
            ) : criticalData?.alerts?.length > 0 ? (
              <div className="space-y-3 max-h-[280px] overflow-y-auto">
                {criticalData.alerts.slice(0, 5).map((alert) => (
                  <div
                    key={alert.alert_id}
                    className={`p-3 rounded-lg border ${
                      alert.risk_level === 'critical' 
                        ? 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800' 
                        : 'bg-orange-50 border-orange-200 dark:bg-orange-900/20 dark:border-orange-800'
                    }`}
                    data-testid="critical-alert-item"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-slate-900 dark:text-white">
                          {alert.asset_name}
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {alert.counterparty_name} • {alert.asset_type}
                        </p>
                        <p className="text-xs text-slate-600 dark:text-slate-300 mt-2">
                          {alert.alert_trigger}
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge 
                          variant={alert.risk_level === 'critical' ? 'destructive' : 'default'}
                          className="mb-1"
                        >
                          {(parseFloat(alert.stranding_risk_score) * 100).toFixed(0)}%
                        </Badge>
                        <p className="text-sm font-bold text-red-600 dark:text-red-400">
                          {formatCurrency(parseFloat(alert.estimated_impact_usd))}
                        </p>
                        <p className="text-xs text-slate-500">
                          {alert.time_to_stranding_years}y to stranding
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-32 text-slate-400">
                <Zap className="h-8 w-8 mb-2" />
                <p>No critical alerts</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default StrandedAssetDashboard;
