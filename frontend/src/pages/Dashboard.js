import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { toast } from 'sonner';
import { LayoutDashboard, TrendingUp } from 'lucide-react';

import {
  PortfolioSelector,
  ScenarioSelector,
  PortfolioMetricsCard,
  ExposureBreakdownChart,
  ScenarioComparisonChart,
  HeatmapVisualization,
  CounterpartyTable,
  AnalysisRunButton,
  ReportExportButton,
} from '../components/dashboard';

import { useDashboardStore } from '../store/dashboardStore';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function Dashboard() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  
  // Use Zustand store for state management
  const {
    selectedPortfolio,
    selectPortfolio,
    selectedScenarios,
    setSelectedScenarios,
    selectedHorizons,
    setSelectedHorizons,
    metrics,
    metricsLoading,
    holdings,
    holdingsLoading,
    analysisRunning,
    analysisProgress,
    analysisResults,
    analysisError,
    runAnalysis,
  } = useDashboardStore();

  // Handle analysis run
  const handleRunAnalysis = useCallback(async () => {
    const result = await runAnalysis();
    if (result) {
      setActiveTab('results');
      return result;
    }
  }, [runAnalysis]);

  // Calculate summary stats from analysis results
  const summaryStats = analysisResults?.results ? {
    worstCaseScenario: analysisResults.results.reduce((worst, r) => {
      const rLoss = r.portfolio_metrics?.expected_loss || r.expected_loss || 0;
      const worstLoss = worst?.portfolio_metrics?.expected_loss || worst?.expected_loss || 0;
      return rLoss > worstLoss ? r : worst;
    }, null),
    avgImpact: analysisResults.results.reduce((sum, r) => 
      sum + (r.portfolio_metrics?.expected_loss || r.expected_loss || 0), 0
    ) / analysisResults.results.length,
  } : null;

  // Helper to get scenario name from result
  const getScenarioName = (result) => result?.scenario_name || result?.scenario || 'N/A';

  return (
    <div className="p-6 space-y-6" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground tracking-tight font-['Space_Grotesk'] flex items-center gap-2">
            <LayoutDashboard className="h-6 w-6" />
            Portfolio Scenario Analysis
          </h1>
          <p className="text-muted-foreground mt-1">
            Analyze climate risk impact on your credit portfolios
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <ReportExportButton 
            analysisResults={analysisResults} 
            portfolioData={selectedPortfolio}
            disabled={!analysisResults}
          />
        </div>
      </div>

      {/* Selection Controls */}
      <Card data-testid="analysis-controls">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Portfolio Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Portfolio</label>
              <PortfolioSelector
                selectedPortfolio={selectedPortfolio}
                onSelect={selectPortfolio}
                className="w-full"
              />
            </div>

            {/* Scenario Selection */}
            <div className="md:col-span-2">
              <ScenarioSelector
                selectedScenarios={selectedScenarios}
                selectedHorizons={selectedHorizons}
                onScenariosChange={setSelectedScenarios}
                onHorizonsChange={setSelectedHorizons}
              />
            </div>
          </div>

          <Separator className="my-6" />

          {/* Run Analysis Button */}
          <div className="max-w-sm mx-auto">
            <AnalysisRunButton
              onRun={handleRunAnalysis}
              running={analysisRunning}
              progress={analysisProgress}
              error={analysisError}
              disabled={!selectedPortfolio || selectedScenarios.length === 0}
              portfolioName={selectedPortfolio?.name}
              scenarioCount={selectedScenarios.length}
            />
          </div>
        </CardContent>
      </Card>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList data-testid="dashboard-tabs">
          <TabsTrigger value="overview" data-testid="tab-overview">
            Portfolio Overview
          </TabsTrigger>
          <TabsTrigger value="results" data-testid="tab-results" disabled={!analysisResults}>
            Analysis Results
            {analysisResults && (
              <Badge variant="secondary" className="ml-2 text-xs">New</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="holdings" data-testid="tab-holdings" disabled={!selectedPortfolio}>
            Holdings
          </TabsTrigger>
        </TabsList>

        {/* Portfolio Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          {/* Metrics Cards */}
          <PortfolioMetricsCard 
            metrics={metrics} 
            loading={metricsLoading}
          />

          {/* Charts Row */}
          {selectedPortfolio && metrics && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ExposureBreakdownChart
                sectorBreakdown={metrics.sectorBreakdown}
                geoBreakdown={metrics.geoBreakdown}
                ratingBreakdown={metrics.ratingBreakdown}
                loading={metricsLoading}
                onDrillDown={(type, value) => {
                  toast.info(`Drill down: ${type} - ${value}`);
                }}
              />
              <HeatmapVisualization
                data={metrics}
                loading={metricsLoading}
                title="Sector × Geography Heatmap"
                description="Concentration risk matrix"
              />
            </div>
          )}

          {/* Empty State */}
          {!selectedPortfolio && (
            <Card>
              <CardContent className="py-16 text-center">
                <TrendingUp className="h-16 w-16 mx-auto text-muted-foreground opacity-30 mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">Select a Portfolio</h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Choose a portfolio from the dropdown above to view its metrics, 
                  exposure breakdown, and run scenario analysis.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Analysis Results Tab */}
        <TabsContent value="results" className="space-y-6 mt-6">
          {analysisResults ? (
            <>
              {/* Summary Cards */}
              {summaryStats && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <p className="text-xs text-muted-foreground mb-1">Scenarios Analyzed</p>
                      <p className="text-2xl font-semibold tabular-nums">
                        {analysisResults.results?.length || 0}
                      </p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <p className="text-xs text-muted-foreground mb-1">Worst Case Scenario</p>
                      <p className="text-lg font-semibold">
                        {getScenarioName(summaryStats.worstCaseScenario)}
                      </p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <p className="text-xs text-muted-foreground mb-1">Avg. Expected Loss Impact</p>
                      <p className="text-2xl font-semibold tabular-nums text-destructive">
                        ${(summaryStats.avgImpact / 1e6).toFixed(2)}M
                      </p>
                    </CardContent>
                  </Card>
                </div>
              )}

              {/* Comparison Chart */}
              <ScenarioComparisonChart
                analysisResults={analysisResults}
                loading={false}
              />
            </>
          ) : (
            <Card>
              <CardContent className="py-16 text-center">
                <TrendingUp className="h-16 w-16 mx-auto text-muted-foreground opacity-30 mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No Analysis Results</h3>
                <p className="text-muted-foreground">
                  Run a scenario analysis to see results here.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Holdings Tab */}
        <TabsContent value="holdings" className="mt-6">
          <CounterpartyTable
            holdings={holdings}
            loading={holdingsLoading}
            onExport={() => toast.success('Holdings exported')}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default Dashboard;
