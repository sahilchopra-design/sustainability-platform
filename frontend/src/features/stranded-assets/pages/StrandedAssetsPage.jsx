import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Badge } from '../../../components/ui/badge';
import { 
  Fuel, Factory, Building2, AlertTriangle, TrendingDown, 
  Calculator, BarChart3, Map, LineChart, Target
} from 'lucide-react';
import { StrandedAssetDashboard } from '../components/dashboard/StrandedAssetDashboard';
import { ReserveImpairmentCalculator } from '../components/calculator/ReserveImpairmentCalculator';
import { PowerPlantValuationTool } from '../components/calculator/PowerPlantValuationTool';
import { TechnologyDisruptionChart } from '../components/charts/TechnologyDisruptionChart';

export default function StrandedAssetsPage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-amber-100 dark:bg-amber-900/30 rounded-lg">
              <TrendingDown className="h-6 w-6 text-amber-600 dark:text-amber-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Stranded Asset Analysis
              </h1>
              <p className="text-slate-600 dark:text-slate-400">
                Climate transition risk assessment for energy assets
              </p>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
              IEA Scenarios
            </Badge>
            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
              NGFS Framework
            </Badge>
            <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
              NPV Analysis
            </Badge>
          </div>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 h-auto p-1 bg-slate-100 dark:bg-slate-800 rounded-lg">
            <TabsTrigger 
              value="dashboard" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700"
              data-testid="tab-dashboard"
            >
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">Dashboard</span>
            </TabsTrigger>
            <TabsTrigger 
              value="reserves" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700"
              data-testid="tab-reserves"
            >
              <Fuel className="h-4 w-4" />
              <span className="hidden sm:inline">Reserves</span>
            </TabsTrigger>
            <TabsTrigger 
              value="plants" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700"
              data-testid="tab-plants"
            >
              <Factory className="h-4 w-4" />
              <span className="hidden sm:inline">Power Plants</span>
            </TabsTrigger>
            <TabsTrigger 
              value="disruption" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700"
              data-testid="tab-disruption"
            >
              <LineChart className="h-4 w-4" />
              <span className="hidden sm:inline">Tech Disruption</span>
            </TabsTrigger>
            <TabsTrigger 
              value="alerts" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700"
              data-testid="tab-alerts"
            >
              <AlertTriangle className="h-4 w-4" />
              <span className="hidden sm:inline">Alerts</span>
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            <StrandedAssetDashboard />
          </TabsContent>

          {/* Reserve Impairment Tab */}
          <TabsContent value="reserves" className="space-y-6">
            <ReserveImpairmentCalculator />
          </TabsContent>

          {/* Power Plant Valuation Tab */}
          <TabsContent value="plants" className="space-y-6">
            <PowerPlantValuationTool />
          </TabsContent>

          {/* Technology Disruption Tab */}
          <TabsContent value="disruption" className="space-y-6">
            <TechnologyDisruptionChart />
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts" className="space-y-6">
            <CriticalAssetsPanel />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

// Critical Assets Panel Component
function CriticalAssetsPanel() {
  const [riskFilter, setRiskFilter] = useState('high');
  const [data, setData] = useState({ alerts: [], total: 0, critical_count: 0, high_count: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAlerts = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `${process.env.REACT_APP_BACKEND_URL}/api/v1/stranded-assets/critical-assets?risk_threshold=${riskFilter}`
        );
        const result = await response.json();
        setData(result);
      } catch (err) {
        console.error('Error fetching alerts:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchAlerts();
  }, [riskFilter]);

  const formatCurrency = (value) => {
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
    return `$${value.toFixed(0)}`;
  };

  return (
    <div className="space-y-6" data-testid="critical-assets-panel">
      {/* Filter */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-red-500" />
          <h2 className="text-lg font-semibold">Critical Asset Alerts</h2>
          <Badge variant="destructive">{data.total}</Badge>
        </div>
        <div className="flex gap-2">
          {['high', 'critical'].map((level) => (
            <button
              key={level}
              onClick={() => setRiskFilter(level)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${
                riskFilter === level
                  ? 'bg-red-500 text-white'
                  : 'bg-slate-100 dark:bg-slate-800 hover:bg-slate-200'
              }`}
            >
              {level} ({level === 'critical' ? data.critical_count : data.high_count})
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-l-4 border-l-red-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Critical Alerts</p>
                <p className="text-2xl font-bold text-red-600">{data.critical_count}</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">High Risk Alerts</p>
                <p className="text-2xl font-bold text-orange-600">{data.high_count}</p>
              </div>
              <Target className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Alerts</p>
                <p className="text-2xl font-bold">{data.total}</p>
              </div>
              <BarChart3 className="h-8 w-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alerts Table */}
      <Card>
        <CardHeader>
          <CardTitle>Alert Details</CardTitle>
          <CardDescription>Assets requiring immediate attention based on stranding risk</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
            </div>
          ) : data.alerts.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Asset</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Type</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Counterparty</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-slate-500">Risk</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-slate-500">Impact</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-slate-500">Time</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {data.alerts.map((alert) => (
                    <tr key={alert.alert_id} className="border-b hover:bg-slate-50 dark:hover:bg-slate-800">
                      <td className="py-3 px-4">
                        <p className="font-medium">{alert.asset_name}</p>
                        <p className="text-xs text-slate-500">{alert.alert_trigger}</p>
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className="capitalize">
                          {alert.asset_type.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-sm">{alert.counterparty_name}</td>
                      <td className="py-3 px-4 text-center">
                        <Badge 
                          className={alert.risk_level === 'critical' 
                            ? 'bg-red-100 text-red-700' 
                            : 'bg-orange-100 text-orange-700'
                          }
                        >
                          {(parseFloat(alert.stranding_risk_score) * 100).toFixed(0)}%
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-red-600">
                        {formatCurrency(parseFloat(alert.estimated_impact_usd))}
                      </td>
                      <td className="py-3 px-4 text-center text-sm">
                        {alert.time_to_stranding_years}y
                      </td>
                      <td className="py-3 px-4 text-sm text-blue-600">
                        {alert.recommended_action}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-48 text-slate-400">
              <AlertTriangle className="h-12 w-12 mb-4" />
              <p>No alerts matching the selected criteria</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
