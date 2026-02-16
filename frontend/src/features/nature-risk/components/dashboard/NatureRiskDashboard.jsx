import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Progress } from '../../../components/ui/progress';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line 
} from 'recharts';
import { 
  Leaf, Droplets, TreePine, AlertTriangle, TrendingUp, 
  Building2, Target, Shield, CheckCircle 
} from 'lucide-react';
import { natureRiskApi } from '../../api/natureRiskApi';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

export function NatureRiskDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const data = await natureRiskApi.getDashboardSummary();
      setSummary(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center text-red-500 py-8">
        <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
        <p>Error loading dashboard: {error}</p>
      </div>
    );
  }

  const sectorData = summary?.sector_breakdown 
    ? Object.entries(summary.sector_breakdown).map(([name, data]) => ({
        name,
        count: data.count,
        avgRisk: data.avg_risk
      }))
    : [];

  const gbfData = summary?.gbf_alignment || { aligned_targets: 0, partial_targets: 0, not_aligned_targets: 0 };
  const gbfPieData = [
    { name: 'Aligned', value: gbfData.aligned_targets, color: '#10b981' },
    { name: 'Partial', value: gbfData.partial_targets, color: '#f59e0b' },
    { name: 'Not Aligned', value: gbfData.not_aligned_targets, color: '#ef4444' }
  ];

  return (
    <div className="space-y-6" data-testid="nature-risk-dashboard">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-white dark:bg-slate-800 border-l-4 border-l-emerald-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Total Assessments</p>
                <p className="text-3xl font-bold text-slate-900 dark:text-white" data-testid="total-assessments">
                  {summary?.total_assessments || 0}
                </p>
              </div>
              <div className="p-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-full">
                <Leaf className="h-6 w-6 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-slate-800 border-l-4 border-l-red-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">High Risk Entities</p>
                <p className="text-3xl font-bold text-red-600" data-testid="high-risk-entities">
                  {summary?.high_risk_entities || 0}
                </p>
              </div>
              <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-full">
                <AlertTriangle className="h-6 w-6 text-red-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-slate-800 border-l-4 border-l-blue-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Water Stress Locations</p>
                <p className="text-3xl font-bold text-blue-600" data-testid="water-stress-locations">
                  {summary?.water_risk_exposure?.high_stress_locations || 0}
                  <span className="text-lg text-slate-400">/{summary?.water_risk_exposure?.total_locations || 0}</span>
                </p>
              </div>
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                <Droplets className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white dark:bg-slate-800 border-l-4 border-l-purple-500">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Biodiversity Overlaps</p>
                <p className="text-3xl font-bold text-purple-600" data-testid="biodiversity-overlaps">
                  {(summary?.biodiversity_overlaps?.direct_overlaps || 0) + (summary?.biodiversity_overlaps?.buffer_overlaps || 0)}
                </p>
              </div>
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-full">
                <TreePine className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sector Risk Distribution */}
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-slate-600" />
              Sector Risk Distribution
            </CardTitle>
            <CardDescription>Average nature risk score by sector</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sectorData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 5]} />
                  <YAxis dataKey="name" type="category" width={100} />
                  <Tooltip formatter={(value) => value.toFixed(2)} />
                  <Bar dataKey="avgRisk" fill="#10b981" name="Avg Risk Score" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* GBF Alignment */}
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5 text-slate-600" />
              GBF Target Alignment
            </CardTitle>
            <CardDescription>Global Biodiversity Framework compliance status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] flex items-center">
              <ResponsiveContainer width="50%" height="100%">
                <PieChart>
                  <Pie
                    data={gbfPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {gbfPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex-1 space-y-3">
                {gbfPieData.map((item, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-sm text-slate-600 dark:text-slate-400">{item.name}</span>
                    </div>
                    <span className="font-semibold">{item.value}</span>
                  </div>
                ))}
                <div className="pt-2 border-t">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600 dark:text-slate-400">Total Targets</span>
                    <span className="font-semibold">{gbfData.total_targets || 23}</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Risk Trend */}
      <Card className="bg-white dark:bg-slate-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-slate-600" />
            Nature Risk Trend
          </CardTitle>
          <CardDescription>Monthly average risk score trend</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={summary?.trend_data || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis domain={[0, 5]} />
                <Tooltip formatter={(value) => value.toFixed(2)} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="risk_score" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  dot={{ fill: '#10b981' }}
                  name="Risk Score"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white cursor-pointer hover:from-emerald-600 hover:to-emerald-700 transition-all">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <Shield className="h-10 w-10 opacity-80" />
              <div>
                <h3 className="font-semibold text-lg">Run LEAP Assessment</h3>
                <p className="text-emerald-100 text-sm">Start a new TNFD LEAP assessment</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white cursor-pointer hover:from-blue-600 hover:to-blue-700 transition-all">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <Droplets className="h-10 w-10 opacity-80" />
              <div>
                <h3 className="font-semibold text-lg">Analyze Water Risk</h3>
                <p className="text-blue-100 text-sm">Assess water stress exposure</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white cursor-pointer hover:from-purple-600 hover:to-purple-700 transition-all">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <TreePine className="h-10 w-10 opacity-80" />
              <div>
                <h3 className="font-semibold text-lg">Check Biodiversity</h3>
                <p className="text-purple-100 text-sm">Analyze protected area overlaps</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
