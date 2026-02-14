import { useState, useEffect, useCallback } from 'react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function useScenarios() {
  const [scenarios, setScenarios] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchScenarios = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [scenariosRes, templatesRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/scenarios`),
        fetch(`${API_URL}/api/v1/scenarios/templates`),
      ]);
      
      const scenariosData = await scenariosRes.json();
      const templatesData = await templatesRes.json();
      
      setScenarios(scenariosData || []);
      setTemplates(templatesData || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchScenarios();
  }, [fetchScenarios]);

  return { scenarios, templates, loading, error, refetch: fetchScenarios };
}

export function useScenarioAnalysis() {
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const runAnalysis = useCallback(async (portfolioId, scenarios, horizons) => {
    if (!portfolioId) {
      setError('Please select a portfolio');
      return null;
    }
    
    if (!scenarios || scenarios.length === 0) {
      setError('Please select at least one scenario');
      return null;
    }

    setRunning(true);
    setProgress(0);
    setError(null);

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 15, 90));
      }, 400);

      const res = await fetch(`${API_URL}/api/analysis/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portfolio_id: portfolioId,
          scenarios: scenarios,
          horizons: horizons || [2030, 2040, 2050],
        }),
      });

      clearInterval(progressInterval);

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      const data = await res.json();
      setResults(data);
      setProgress(100);
      
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setRunning(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setResults(null);
    setProgress(0);
    setError(null);
  }, []);

  return {
    running,
    progress,
    results,
    error,
    runAnalysis,
    clearResults,
  };
}

export function useAnalysisRuns(portfolioId) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchRuns = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const url = portfolioId 
        ? `${API_URL}/api/analysis/runs?portfolio_id=${portfolioId}`
        : `${API_URL}/api/analysis/runs`;
      
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch analysis runs');
      const data = await res.json();
      setRuns(data.runs || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [portfolioId]);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  const getRunDetails = useCallback(async (runId) => {
    try {
      const res = await fetch(`${API_URL}/api/analysis/runs/${runId}`);
      if (!res.ok) throw new Error('Failed to fetch run details');
      return await res.json();
    } catch (err) {
      throw err;
    }
  }, []);

  const deleteRun = useCallback(async (runId) => {
    try {
      const res = await fetch(`${API_URL}/api/analysis/runs/${runId}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to delete run');
      await fetchRuns();
    } catch (err) {
      throw err;
    }
  }, [fetchRuns]);

  return { runs, loading, error, refetch: fetchRuns, getRunDetails, deleteRun };
}
