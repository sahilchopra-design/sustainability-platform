import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';
import { getPortfolios, runAnalysis } from '../utils/api';

const SCENARIOS = ['Orderly', 'Disorderly', 'Hot house world'];
const HORIZONS = [2030, 2040, 2050];

function Analysis() {
  const location = useLocation();
  const navigate = useNavigate();
  const preselectedPortfolioId = location.state?.portfolioId;

  const [selectedPortfolio, setSelectedPortfolio] = useState(preselectedPortfolioId || '');
  const [selectedScenarios, setSelectedScenarios] = useState(SCENARIOS);
  const [selectedHorizons, setSelectedHorizons] = useState(HORIZONS);

  const { data: portfoliosData, isLoading } = useQuery({
    queryKey: ['portfolios'],
    queryFn: async () => {
      const res = await getPortfolios();
      return res.data;
    },
  });

  const runMutation = useMutation({
    mutationFn: runAnalysis,
    onSuccess: (response) => {
      navigate(`/results/${response.data.id}`);
    },
  });

  const portfolios = portfoliosData?.portfolios || [];

  const handleToggleScenario = (scenario) => {
    if (selectedScenarios.includes(scenario)) {
      setSelectedScenarios(selectedScenarios.filter((s) => s !== scenario));
    } else {
      setSelectedScenarios([...selectedScenarios, scenario]);
    }
  };

  const handleToggleHorizon = (horizon) => {
    if (selectedHorizons.includes(horizon)) {
      setSelectedHorizons(selectedHorizons.filter((h) => h !== horizon));
    } else {
      setSelectedHorizons([...selectedHorizons, horizon]);
    }
  };

  const handleRunAnalysis = () => {
    if (!selectedPortfolio) {
      alert('Please select a portfolio');
      return;
    }
    if (selectedScenarios.length === 0) {
      alert('Please select at least one scenario');
      return;
    }
    if (selectedHorizons.length === 0) {
      alert('Please select at least one time horizon');
      return;
    }

    runMutation.mutate({
      portfolio_id: selectedPortfolio,
      scenarios: selectedScenarios,
      horizons: selectedHorizons,
    });
  };

  return (
    <div className="p-8" data-testid="analysis-page">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-foreground">Run Scenario Analysis</h1>
        <p className="text-muted-foreground mt-2">
          Analyze portfolio climate risk under NGFS scenarios
        </p>
      </div>

      <div className="max-w-3xl">
        {/* Portfolio Selection */}
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-foreground mb-4">1. Select Portfolio</h2>
          {isLoading ? (
            <div className="text-muted-foreground">Loading portfolios...</div>
          ) : portfolios.length === 0 ? (
            <div className="text-muted-foreground">No portfolios available. Create one first.</div>
          ) : (
            <select
              value={selectedPortfolio}
              onChange={(e) => setSelectedPortfolio(e.target.value)}
              className="w-full px-4 py-3 bg-background border border-input rounded-lg text-foreground"
              data-testid="portfolio-select"
            >
              <option value="">-- Choose Portfolio --</option>
              {portfolios.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.num_assets} assets, ${(p.total_exposure / 1e6).toFixed(1)}M exposure)
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Scenario Selection */}
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-foreground mb-4">2. Select Scenarios</h2>
          <div className="space-y-3">
            {SCENARIOS.map((scenario) => (
              <label
                key={scenario}
                className="flex items-center gap-3 p-3 border border-border rounded-lg cursor-pointer hover:bg-muted transition-colors"
                data-testid={`scenario-option-${scenario}`}
              >
                <input
                  type="checkbox"
                  checked={selectedScenarios.includes(scenario)}
                  onChange={() => handleToggleScenario(scenario)}
                  className="w-5 h-5"
                />
                <div className="flex-1">
                  <div className="font-medium text-foreground">{scenario}</div>
                  <div className="text-sm text-muted-foreground">
                    {scenario === 'Orderly' &&
                      'Net zero by 2050 with immediate policy action'}
                    {scenario === 'Disorderly' &&
                      'Delayed transition with sudden policy shifts'}
                    {scenario === 'Hot house world' &&
                      'Current policies continue, warming exceeds 2°C'}
                  </div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Horizon Selection */}
        <div className="bg-card border border-border rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-foreground mb-4">3. Select Time Horizons</h2>
          <div className="flex gap-4">
            {HORIZONS.map((horizon) => (
              <label
                key={horizon}
                className="flex-1 flex items-center justify-center gap-2 p-4 border border-border rounded-lg cursor-pointer hover:bg-muted transition-colors"
                data-testid={`horizon-option-${horizon}`}
              >
                <input
                  type="checkbox"
                  checked={selectedHorizons.includes(horizon)}
                  onChange={() => handleToggleHorizon(horizon)}
                  className="w-5 h-5"
                />
                <span className="font-medium text-foreground">{horizon}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Run Button */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h2 className="text-lg font-semibold text-foreground mb-4">4. Run Analysis</h2>
          <button
            onClick={handleRunAnalysis}
            disabled={runMutation.isPending || !selectedPortfolio}
            className="w-full px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 font-medium"
            data-testid="run-analysis-submit"
          >
            {runMutation.isPending ? 'Running Analysis...' : 'Run Scenario Analysis'}
          </button>
          {runMutation.isError && (
            <div className="mt-4 p-4 bg-destructive/10 border border-destructive rounded-lg text-destructive" data-testid="analysis-error">
              Error: {runMutation.error.message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Analysis;
