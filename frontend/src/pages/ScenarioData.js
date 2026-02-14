import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getScenarioData, refreshScenarioData } from '../utils/api';

function ScenarioData() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['scenarioData'],
    queryFn: async () => {
      const res = await getScenarioData();
      return res.data;
    },
  });

  const refreshMutation = useMutation({
    mutationFn: () => refreshScenarioData(true),
    onSuccess: () => {
      queryClient.invalidateQueries(['scenarioData']);
    },
  });

  return (
    <div className="p-8" data-testid="scenario-data-page">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-foreground">NGFS Scenario Data</h1>
        <p className="text-muted-foreground mt-2">
          Climate scenario data from the Network for Greening the Financial System
        </p>
      </div>

      {isLoading ? (
        <div className="text-muted-foreground">Loading scenario data...</div>
      ) : (
        <div>
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-card border border-border rounded-xl p-6">
              <div className="text-sm text-muted-foreground mb-2">Total Records</div>
              <div className="text-3xl font-semibold text-foreground">{data.total_records}</div>
            </div>
            <div className="bg-card border border-border rounded-xl p-6">
              <div className="text-sm text-muted-foreground mb-2">Scenarios</div>
              <div className="text-3xl font-semibold text-foreground">{data.scenarios.length}</div>
            </div>
            <div className="bg-card border border-border rounded-xl p-6">
              <div className="text-sm text-muted-foreground mb-2">Variables</div>
              <div className="text-3xl font-semibold text-foreground">{data.variables.length}</div>
            </div>
            <div className="bg-card border border-border rounded-xl p-6">
              <div className="text-sm text-muted-foreground mb-2">Regions</div>
              <div className="text-3xl font-semibold text-foreground">{data.regions.length}</div>
            </div>
          </div>

          {/* Scenarios */}
          <div className="bg-card border border-border rounded-xl p-6 mb-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">Available Scenarios</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {data.scenarios.map((scenario) => (
                <div key={scenario} className="p-4 border border-border rounded-lg">
                  <div className="font-medium text-foreground">{scenario}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Variables */}
          <div className="bg-card border border-border rounded-xl p-6 mb-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">Climate Variables</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data.variables.map((variable) => (
                <div key={variable} className="p-3 border border-border rounded-lg">
                  <div className="text-sm text-foreground">{variable}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Regions */}
          <div className="bg-card border border-border rounded-xl p-6 mb-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">Geographic Regions</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              {data.regions.map((region) => (
                <div key={region} className="p-3 border border-border rounded-lg">
                  <div className="text-sm text-foreground">{region}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Time Horizons */}
          <div className="bg-card border border-border rounded-xl p-6 mb-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">Time Horizons</h2>
            <div className="flex gap-4">
              {data.years.map((year) => (
                <div key={year} className="px-6 py-3 border border-border rounded-lg">
                  <div className="font-medium text-foreground">{year}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Refresh Button */}
          <div className="bg-card border border-border rounded-xl p-6">
            <h2 className="text-xl font-semibold text-foreground mb-4">Data Management</h2>
            <p className="text-muted-foreground mb-4">
              Refresh scenario data from NGFS sources. This will overwrite existing data.
            </p>
            <button
              onClick={() => refreshMutation.mutate()}
              disabled={refreshMutation.isPending}
              className="px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
              data-testid="refresh-scenario-data-button"
            >
              {refreshMutation.isPending ? 'Refreshing...' : 'Refresh Scenario Data'}
            </button>
            {refreshMutation.isSuccess && (
              <div className="mt-4 p-4 bg-success/10 border border-success rounded-lg text-success">
                Scenario data refreshed successfully!
              </div>
            )}
            {refreshMutation.isError && (
              <div className="mt-4 p-4 bg-destructive/10 border border-destructive rounded-lg text-destructive">
                Error: {refreshMutation.error.message}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ScenarioData;
