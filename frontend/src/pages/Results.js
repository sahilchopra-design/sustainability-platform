import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { getAnalysisRun } from '../utils/api';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const SCENARIO_COLORS = {
  Orderly: 'hsl(158, 64%, 28%)',
  Disorderly: 'hsl(30, 90%, 52%)',
  'Hot house world': 'hsl(0, 72%, 45%)',
};

function Results() {
  const { runId } = useParams();

  const { data, isLoading } = useQuery({
    queryKey: ['analysisRun', runId],
    queryFn: async () => {
      const res = await getAnalysisRun(runId);
      return res.data;
    },
  });

  if (isLoading) {
    return <div className="p-8">Loading results...</div>;
  }

  const run = data;
  const results = run?.results || [];

  // Prepare chart data
  const expectedLossData = run.horizons.map((horizon) => {
    const point = { horizon: horizon.toString() };
    run.scenarios.forEach((scenario) => {
      const result = results.find((r) => r.scenario === scenario && r.horizon === horizon);
      point[scenario] = result ? result.expected_loss_pct : 0;
    });
    return point;
  });

  const riskAdjustedReturnData = run.horizons.map((horizon) => {
    const point = { horizon: horizon.toString() };
    run.scenarios.forEach((scenario) => {
      const result = results.find((r) => r.scenario === scenario && r.horizon === horizon);
      point[scenario] = result ? result.risk_adjusted_return : 0;
    });
    return point;
  });

  // Sector breakdown for latest horizon
  const latestHorizon = run.horizons[run.horizons.length - 1];

  return (
    <div className="p-8" data-testid="results-page">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
          <Link to="/" className="hover:text-foreground">Dashboard</Link>
          <span>/</span>
          <span>Analysis Results</span>
        </div>
        <h1 className="text-3xl font-semibold text-foreground">Scenario Analysis Results</h1>
        <div className="flex items-center gap-4 mt-2 text-muted-foreground">
          <span>{run.portfolio_name}</span>
          <span>•</span>
          <span>{new Date(run.created_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Scenario Summary */}
      <div className="bg-card border border-border rounded-xl p-6 mb-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">Scenarios Analyzed</h2>
        <div className="flex gap-4">
          {run.scenarios.map((scenario) => (
            <div
              key={scenario}
              className="px-4 py-2 border border-border rounded-lg"
              style={{ borderColor: SCENARIO_COLORS[scenario] }}
            >
              <span className="font-medium" style={{ color: SCENARIO_COLORS[scenario] }}>
                {scenario}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Expected Loss Chart */}
      <div className="bg-card border border-border rounded-xl p-6 mb-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">Expected Loss by Scenario</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={expectedLossData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="horizon" stroke="hsl(var(--muted-foreground))" />
            <YAxis stroke="hsl(var(--muted-foreground))" label={{ value: 'Expected Loss (%)', angle: -90, position: 'insideLeft' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
              }}
            />
            <Legend />
            {run.scenarios.map((scenario) => (
              <Line
                key={scenario}
                type="monotone"
                dataKey={scenario}
                stroke={SCENARIO_COLORS[scenario]}
                strokeWidth={2}
                dot={{ r: 5 }}
                data-testid={`expected-loss-line-${scenario}`}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Risk-Adjusted Return Chart */}
      <div className="bg-card border border-border rounded-xl p-6 mb-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">
          Risk-Adjusted Return by Scenario
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={riskAdjustedReturnData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis dataKey="horizon" stroke="hsl(var(--muted-foreground))" />
            <YAxis stroke="hsl(var(--muted-foreground))" label={{ value: 'Return (%)', angle: -90, position: 'insideLeft' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
              }}
            />
            <Legend />
            {run.scenarios.map((scenario) => (
              <Bar key={scenario} dataKey={scenario} fill={SCENARIO_COLORS[scenario]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed Metrics Table */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">Detailed Metrics</h2>
        <div className="overflow-x-auto">
          <table className="w-full" data-testid="results-table">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Scenario</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-foreground">Horizon</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-foreground">Expected Loss</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-foreground">RAR (%)</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-foreground">Avg PD Change</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-foreground">VaR 95</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-foreground">HHI</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-foreground">Migrations</th>
              </tr>
            </thead>
            <tbody>
              {results.map((result, idx) => (
                <tr key={idx} className="border-b border-border hover:bg-muted" data-testid={`result-row-${idx}`}>
                  <td className="py-3 px-4 text-sm font-medium" style={{ color: SCENARIO_COLORS[result.scenario] }}>
                    {result.scenario}
                  </td>
                  <td className="py-3 px-4 text-sm text-foreground text-center">{result.horizon}</td>
                  <td className="py-3 px-4 text-sm text-foreground text-right">
                    ${(result.expected_loss / 1e6).toFixed(2)}M ({result.expected_loss_pct.toFixed(2)}%)
                  </td>
                  <td className="py-3 px-4 text-sm text-foreground text-right">
                    {result.risk_adjusted_return.toFixed(2)}%
                  </td>
                  <td className="py-3 px-4 text-sm text-foreground text-right">
                    {result.avg_pd_change_pct >= 0 ? '+' : ''}{result.avg_pd_change_pct.toFixed(1)}%
                  </td>
                  <td className="py-3 px-4 text-sm text-foreground text-right">
                    ${(result.var_95 / 1e6).toFixed(2)}M
                  </td>
                  <td className="py-3 px-4 text-sm text-foreground text-right">
                    {result.concentration_hhi.toFixed(0)}
                  </td>
                  <td className="py-3 px-4 text-sm text-foreground text-center">
                    <div className="flex gap-2 justify-center text-xs">
                      <span className="text-destructive">↓{result.rating_migrations.downgrades}</span>
                      <span className="text-muted-foreground">=</span>
                      <span className="text-muted-foreground">{result.rating_migrations.stable}</span>
                      <span className="text-muted-foreground">=</span>
                      <span className="text-success">↑{result.rating_migrations.upgrades}</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-6 flex gap-4">
        <Link
          to="/portfolios"
          className="px-6 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/90 transition-colors"
          data-testid="back-to-portfolios"
        >
          Back to Portfolios
        </Link>
        <Link
          to="/analysis"
          className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          data-testid="run-new-analysis"
        >
          Run New Analysis
        </Link>
      </div>
    </div>
  );
}

export default Results;
