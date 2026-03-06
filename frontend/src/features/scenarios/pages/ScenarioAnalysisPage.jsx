/**
 * Scenario Analysis Page
 * Main page with tabs for scenario builder, sensitivity analysis, and what-if analysis
 */
import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Badge } from '../../../components/ui/badge';
import { Card, CardContent } from '../../../components/ui/card';
import {
  Calculator, BarChart3, Zap, GitCompare, TrendingUp, LayoutDashboard
} from 'lucide-react';

import { ScenarioBuilder } from '../components/ScenarioBuilder';
import { SensitivityAnalysis } from '../components/SensitivityAnalysis';
import { WhatIfAnalysis } from '../components/WhatIfAnalysis';
import { ScenarioComparison } from '../components/ScenarioComparison';
import { useScenarioDashboard } from '../hooks/useScenarios';

function DashboardOverview() {
  const { data: dashboard, isLoading } = useScenarioDashboard();

  if (isLoading) {
    return <div className="p-6 text-center text-white/40">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/40">Scenarios Created</p>
                <p className="text-2xl font-bold text-white">{dashboard?.total_scenarios || 0}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <Calculator className="h-6 w-6 text-blue-300" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/40">Analyses Run</p>
                <p className="text-2xl font-bold text-white">{dashboard?.total_analyses || 0}</p>
              </div>
              <div className="p-3 bg-violet-100 rounded-lg">
                <BarChart3 className="h-6 w-6 text-violet-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/40">Avg Value Swing</p>
                <p className="text-2xl font-bold text-white">
                  ±{parseFloat(dashboard?.avg_value_swing_pct || 0).toFixed(1)}%
                </p>
              </div>
              <div className="p-3 bg-amber-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-amber-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-white/40">Top Variable</p>
                <p className="text-lg font-bold text-white">
                  {dashboard?.most_impactful_variables?.[0]?.variable || 'Cap Rate'}
                </p>
              </div>
              <div className="p-3 bg-emerald-100 rounded-lg">
                <Zap className="h-6 w-6 text-emerald-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Most Impactful Variables */}
      <Card>
        <CardContent className="pt-6">
          <h3 className="text-sm font-semibold text-white/70 mb-4">Most Impactful Variables</h3>
          <div className="space-y-3">
            {(dashboard?.most_impactful_variables || []).map((v, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-violet-500 to-blue-500 flex items-center justify-center text-white text-sm font-bold">
                    {idx + 1}
                  </div>
                  <span className="font-medium text-white/70">{v.variable}</span>
                </div>
                <div className="flex items-center gap-4">
                  <Badge className="bg-red-100 text-red-400">
                    {parseFloat(v.low_impact).toFixed(1)}%
                  </Badge>
                  <Badge className="bg-emerald-100 text-emerald-400">
                    +{parseFloat(v.high_impact).toFixed(1)}%
                  </Badge>
                  <Badge variant="outline" className="bg-violet-50 text-violet-700">
                    Swing: {parseFloat(v.swing).toFixed(1)}%
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Scenarios */}
      {dashboard?.recent_scenarios?.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-sm font-semibold text-white/70 mb-4">Recent Scenarios</h3>
            <div className="space-y-2">
              {dashboard.recent_scenarios.map((s, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-white/[0.02] rounded-lg">
                  <div>
                    <div className="font-medium text-white/70">{s.scenario_name}</div>
                    <div className="text-xs text-white/40">{s.description || 'No description'}</div>
                  </div>
                  <Badge className={
                    parseFloat(s.value_change_pct) > 0 
                      ? 'bg-emerald-100 text-emerald-400' 
                      : 'bg-red-100 text-red-400'
                  }>
                    {parseFloat(s.value_change_pct) > 0 ? '+' : ''}{parseFloat(s.value_change_pct).toFixed(1)}%
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function ScenarioAnalysisPage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-white/[0.02]">
      {/* Header */}
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Calculator className="h-6 w-6 text-blue-300" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Scenario Analysis</h1>
            <p className="text-sm text-white/40">
              Interactive scenario builder, sensitivity analysis, and what-if modeling
            </p>
          </div>
        </div>

        {/* Feature Badges */}
        <div className="flex gap-2 mt-4">
          <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/20">
            <Calculator className="h-3 w-3 mr-1" />
            Scenario Builder
          </Badge>
          <Badge variant="outline" className="bg-violet-50 text-violet-700 border-violet-200">
            <BarChart3 className="h-3 w-3 mr-1" />
            Sensitivity Analysis
          </Badge>
          <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/20">
            <Zap className="h-3 w-3 mr-1" />
            What-If Analysis
          </Badge>
          <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
            <GitCompare className="h-3 w-3 mr-1" />
            Scenario Comparison
          </Badge>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-6 bg-[#0d1424] border border-white/[0.06]">
            <TabsTrigger
              value="dashboard"
              className="flex items-center gap-2 data-[state=active]:bg-white/[0.06]"
              data-testid="tab-scenario-dashboard"
            >
              <LayoutDashboard className="h-4 w-4" />
              <span className="hidden md:inline">Dashboard</span>
            </TabsTrigger>
            <TabsTrigger
              value="builder"
              className="flex items-center gap-2 data-[state=active]:bg-blue-500/10 data-[state=active]:text-blue-300"
              data-testid="tab-scenario-builder"
            >
              <Calculator className="h-4 w-4" />
              <span className="hidden md:inline">Builder</span>
            </TabsTrigger>
            <TabsTrigger
              value="sensitivity"
              className="flex items-center gap-2 data-[state=active]:bg-violet-50 data-[state=active]:text-violet-700"
              data-testid="tab-sensitivity"
            >
              <BarChart3 className="h-4 w-4" />
              <span className="hidden md:inline">Sensitivity</span>
            </TabsTrigger>
            <TabsTrigger
              value="whatif"
              className="flex items-center gap-2 data-[state=active]:bg-amber-500/10 data-[state=active]:text-amber-400"
              data-testid="tab-whatif"
            >
              <Zap className="h-4 w-4" />
              <span className="hidden md:inline">What-If</span>
            </TabsTrigger>
            <TabsTrigger
              value="compare"
              className="flex items-center gap-2 data-[state=active]:bg-emerald-500/10 data-[state=active]:text-emerald-400"
              data-testid="tab-compare"
            >
              <GitCompare className="h-4 w-4" />
              <span className="hidden md:inline">Compare</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="mt-0">
            <DashboardOverview />
          </TabsContent>

          <TabsContent value="builder" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                <div className="p-1.5 bg-blue-100 rounded">
                  <Calculator className="h-4 w-4 text-blue-300" />
                </div>
                Scenario Builder
              </h2>
              <p className="text-sm text-white/60 mt-1">
                Create custom scenarios by modifying key valuation parameters
              </p>
            </div>
            <ScenarioBuilder />
          </TabsContent>

          <TabsContent value="sensitivity" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                <div className="p-1.5 bg-violet-100 rounded">
                  <BarChart3 className="h-4 w-4 text-violet-600" />
                </div>
                Sensitivity Analysis
              </h2>
              <p className="text-sm text-white/60 mt-1">
                Analyze how changes in key variables affect property valuation
              </p>
            </div>
            <SensitivityAnalysis />
          </TabsContent>

          <TabsContent value="whatif" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                <div className="p-1.5 bg-amber-100 rounded">
                  <Zap className="h-4 w-4 text-amber-400" />
                </div>
                What-If Analysis
              </h2>
              <p className="text-sm text-white/60 mt-1">
                See how parameter changes affect valuation with cascading effects
              </p>
            </div>
            <WhatIfAnalysis />
          </TabsContent>

          <TabsContent value="compare" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                <div className="p-1.5 bg-emerald-100 rounded">
                  <GitCompare className="h-4 w-4 text-emerald-400" />
                </div>
                Scenario Comparison
              </h2>
              <p className="text-sm text-white/60 mt-1">
                Compare multiple scenarios side by side
              </p>
            </div>
            <ScenarioComparison />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
