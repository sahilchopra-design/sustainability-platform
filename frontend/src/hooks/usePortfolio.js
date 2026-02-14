import { useState, useEffect, useCallback } from 'react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export function usePortfolio(portfolioId) {
  const [portfolio, setPortfolio] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPortfolio = useCallback(async () => {
    if (!portfolioId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch(`${API_URL}/api/portfolios/${portfolioId}`);
      if (!res.ok) throw new Error('Failed to fetch portfolio');
      const data = await res.json();
      setPortfolio(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [portfolioId]);

  useEffect(() => {
    fetchPortfolio();
  }, [fetchPortfolio]);

  return { portfolio, loading, error, refetch: fetchPortfolio };
}

export function usePortfolios() {
  const [portfolios, setPortfolios] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchPortfolios = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch(`${API_URL}/api/portfolios`);
      if (!res.ok) throw new Error('Failed to fetch portfolios');
      const data = await res.json();
      setPortfolios(data.portfolios || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPortfolios();
  }, [fetchPortfolios]);

  const createPortfolio = async (name, description) => {
    try {
      const res = await fetch(`${API_URL}/api/portfolios`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description }),
      });
      if (!res.ok) throw new Error('Failed to create portfolio');
      const data = await res.json();
      await fetchPortfolios();
      return data;
    } catch (err) {
      throw err;
    }
  };

  const deletePortfolio = async (id) => {
    try {
      const res = await fetch(`${API_URL}/api/portfolios/${id}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Failed to delete portfolio');
      await fetchPortfolios();
    } catch (err) {
      throw err;
    }
  };

  return { 
    portfolios, 
    loading, 
    error, 
    refetch: fetchPortfolios,
    createPortfolio,
    deletePortfolio,
  };
}

export function usePortfolioMetrics(portfolioId) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const calculateMetrics = useCallback(async () => {
    if (!portfolioId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch(`${API_URL}/api/portfolios/${portfolioId}`);
      if (!res.ok) throw new Error('Failed to fetch portfolio');
      const data = await res.json();
      
      const assets = data.assets || [];
      const totalExposure = assets.reduce((sum, a) => sum + (a.exposure || 0), 0);
      const totalMarketValue = assets.reduce((sum, a) => sum + (a.market_value || 0), 0);
      const avgPD = assets.length > 0 
        ? assets.reduce((sum, a) => sum + (a.base_pd || 0), 0) / assets.length 
        : 0;
      const avgLGD = assets.length > 0 
        ? assets.reduce((sum, a) => sum + (a.base_lgd || 0), 0) / assets.length 
        : 0;
      const expectedLoss = totalExposure * avgPD * avgLGD;
      
      // Sector breakdown
      const sectorBreakdown = {};
      assets.forEach(asset => {
        const sector = asset.company?.sector || 'Unknown';
        sectorBreakdown[sector] = (sectorBreakdown[sector] || 0) + (asset.exposure || 0);
      });

      // Geographic breakdown (using country from company if available)
      const geoBreakdown = {};
      assets.forEach(asset => {
        const country = asset.company?.country || 'Unknown';
        geoBreakdown[country] = (geoBreakdown[country] || 0) + (asset.exposure || 0);
      });

      // Rating breakdown
      const ratingBreakdown = {};
      assets.forEach(asset => {
        const rating = asset.rating || 'NR';
        ratingBreakdown[rating] = (ratingBreakdown[rating] || 0) + (asset.exposure || 0);
      });

      setMetrics({
        totalExposure,
        totalMarketValue,
        expectedLoss,
        avgPD: avgPD * 100,
        avgLGD: avgLGD * 100,
        numAssets: assets.length,
        sectorBreakdown,
        geoBreakdown,
        ratingBreakdown,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [portfolioId]);

  useEffect(() => {
    calculateMetrics();
  }, [calculateMetrics]);

  return { metrics, loading, error, refetch: calculateMetrics };
}
