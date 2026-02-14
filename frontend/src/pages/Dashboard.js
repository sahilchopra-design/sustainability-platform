import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getPortfolios, getAnalysisRuns } from '../utils/api';

function Dashboard() {
  const { data: portfoliosData, isLoading: loadingPortfolios } = useQuery({
    queryKey: ['portfolios'],
    queryFn: async () => {
      const res = await getPortfolios();
      return res.data;
    },
  });

  const { data: runsData, isLoading: loadingRuns } = useQuery({
    queryKey: ['analysisRuns'],
    queryFn: async () => {
      const res = await getAnalysisRuns();
      return res.data;
    },
  });

  const portfolios = portfoliosData?.portfolios || [];
  const runs = runsData?.runs || [];

  // Calculate stats
  const totalExposure = portfolios.reduce((sum, p) => sum + (p.total_exposure || 0), 0);
  const totalAssets = portfolios.reduce((sum, p) => sum + (p.num_assets || 0), 0);
  const recentRuns = runs.slice(0, 5);

  return (
    <div className="p-8" data-testid="dashboard-page">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mt-2">Climate Credit Risk Portfolio Overview</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-card border border-border rounded-xl p-6" data-testid="kpi-card-portfolios">
          <div className="text-sm text-muted-foreground mb-2">Total Portfolios</div>
          <div className="text-3xl font-semibold text-foreground">
            {loadingPortfolios ? '...' : portfolios.length}
          </div>
          <Link
            to="/portfolios"
            className="text-sm text-primary hover:underline mt-2 inline-block"
            data-testid="kpi-card-portfolios-link"
          >
            View all portfolios →
          </Link>
        </div>

        <div className="bg-card border border-border rounded-xl p-6" data-testid="kpi-card-exposure">
          <div className="text-sm text-muted-foreground mb-2">Total Exposure</div>
          <div className="text-3xl font-semibold text-foreground">
            {loadingPortfolios ? '...' : `$${(totalExposure / 1e6).toFixed(1)}M`}
          </div>
          <div className="text-sm text-muted-foreground mt-2">
            Across {totalAssets} assets
          </div>
        </div>

        <div className="bg-card border border-border rounded-xl p-6" data-testid="kpi-card-analyses">
          <div className="text-sm text-muted-foreground mb-2">Analyses Completed</div>
          <div className="text-3xl font-semibold text-foreground">
            {loadingRuns ? '...' : runs.length}
          </div>
          <Link
            to="/analysis"
            className="text-sm text-primary hover:underline mt-2 inline-block"
            data-testid="kpi-card-analyses-link"
          >
            Run new analysis →
          </Link>
        </div>
      </div>

      {/* Recent Analysis Runs */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">Recent Analysis Runs</h2>
        {loadingRuns ? (
          <div className="text-muted-foreground">Loading...</div>
        ) : recentRuns.length === 0 ? (
          <div className="text-muted-foreground" data-testid="no-analyses">
            No analyses yet. <Link to="/analysis" className="text-primary hover:underline">Run your first analysis</Link>
          </div>
        ) : (
          <div className="space-y-3" data-testid="recent-analyses-list">
            {recentRuns.map((run) => (
              <div
                key={run.id}
                className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted transition-colors"
                data-testid={`analysis-run-${run.id}`}
              >
                <div>
                  <div className="font-medium text-foreground">{run.portfolio_name}</div>
                  <div className="text-sm text-muted-foreground">
                    {run.scenarios.join(', ')} • {run.horizons.join(', ')}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-sm text-muted-foreground">
                    {new Date(run.created_at).toLocaleString()}
                  </div>
                  <Link
                    to={`/results/${run.id}`}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                    data-testid={`view-results-${run.id}`}
                  >
                    View Results
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
