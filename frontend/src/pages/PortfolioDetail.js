import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPortfolio, addAssetToPortfolio, removeAssetFromPortfolio } from '../utils/api';

const SECTORS = [
  'Power Generation',
  'Oil & Gas',
  'Metals & Mining',
  'Automotive',
  'Airlines',
  'Real Estate',
];

const ASSET_TYPES = ['Bond', 'Loan', 'Equity'];

function PortfolioDetail() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [showAddForm, setShowAddForm] = useState(false);
  const [newAsset, setNewAsset] = useState({
    asset_type: 'Bond',
    company_name: '',
    company_sector: SECTORS[0],
    company_subsector: '',
    exposure: '',
    market_value: '',
    base_pd: '',
    base_lgd: '',
    rating: 'BBB',
    maturity_years: '5',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['portfolio', id],
    queryFn: async () => {
      const res = await getPortfolio(id);
      return res.data;
    },
  });

  const addAssetMutation = useMutation({
    mutationFn: ({ portfolioId, asset }) => addAssetToPortfolio(portfolioId, asset),
    onSuccess: () => {
      queryClient.invalidateQueries(['portfolio', id]);
      setShowAddForm(false);
      resetForm();
    },
  });

  const removeAssetMutation = useMutation({
    mutationFn: ({ portfolioId, assetId }) => removeAssetFromPortfolio(portfolioId, assetId),
    onSuccess: () => {
      queryClient.invalidateQueries(['portfolio', id]);
    },
  });

  const resetForm = () => {
    setNewAsset({
      asset_type: 'Bond',
      company_name: '',
      company_sector: SECTORS[0],
      company_subsector: '',
      exposure: '',
      market_value: '',
      base_pd: '',
      base_lgd: '',
      rating: 'BBB',
      maturity_years: '5',
    });
  };

  const handleAddAsset = () => {
    const asset = {
      id: `asset_${Date.now()}`,
      asset_type: newAsset.asset_type,
      company: {
        name: newAsset.company_name,
        sector: newAsset.company_sector,
        subsector: newAsset.company_subsector || null,
      },
      exposure: parseFloat(newAsset.exposure),
      market_value: parseFloat(newAsset.market_value),
      base_pd: parseFloat(newAsset.base_pd),
      base_lgd: parseFloat(newAsset.base_lgd),
      rating: newAsset.rating,
      maturity_years: parseInt(newAsset.maturity_years),
    };

    addAssetMutation.mutate({ portfolioId: id, asset });
  };

  if (isLoading) {
    return <div className="p-8">Loading...</div>;
  }

  const portfolio = data;
  const assets = portfolio?.assets || [];

  return (
    <div className="p-8" data-testid="portfolio-detail-page">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
          <Link to="/portfolios" className="hover:text-foreground">Portfolios</Link>
          <span>/</span>
          <span>{portfolio?.name}</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-foreground">{portfolio?.name}</h1>
            {portfolio?.description && (
              <p className="text-muted-foreground mt-2">{portfolio.description}</p>
            )}
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => setShowAddForm(!showAddForm)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              data-testid="add-asset-button"
            >
              {showAddForm ? 'Cancel' : 'Add Asset'}
            </button>
            <Link
              to="/analysis"
              state={{ portfolioId: id }}
              className="px-4 py-2 bg-accent text-accent-foreground rounded-lg hover:bg-accent/90 transition-colors"
              data-testid="run-analysis-button"
            >
              Run Analysis
            </Link>
          </div>
        </div>
      </div>

      {/* Portfolio Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="text-sm text-muted-foreground">Total Assets</div>
          <div className="text-2xl font-semibold text-foreground mt-1">{assets.length}</div>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="text-sm text-muted-foreground">Total Exposure</div>
          <div className="text-2xl font-semibold text-foreground mt-1">
            ${(portfolio?.total_exposure / 1e6).toFixed(1)}M
          </div>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="text-sm text-muted-foreground">Avg Base PD</div>
          <div className="text-2xl font-semibold text-foreground mt-1">
            {assets.length > 0
              ? (assets.reduce((sum, a) => sum + a.base_pd, 0) / assets.length).toFixed(3)
              : '0.000'}
          </div>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="text-sm text-muted-foreground">Avg Base LGD</div>
          <div className="text-2xl font-semibold text-foreground mt-1">
            {assets.length > 0
              ? (assets.reduce((sum, a) => sum + a.base_lgd, 0) / assets.length).toFixed(3)
              : '0.000'}
          </div>
        </div>
      </div>

      {/* Add Asset Form */}
      {showAddForm && (
        <div className="bg-card border border-border rounded-xl p-6 mb-6" data-testid="add-asset-form">
          <h2 className="text-lg font-semibold text-foreground mb-4">Add New Asset</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Asset Type</label>
              <select
                value={newAsset.asset_type}
                onChange={(e) => setNewAsset({ ...newAsset, asset_type: e.target.value })}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                data-testid="asset-type-select"
              >
                {ASSET_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Company Name</label>
              <input
                type="text"
                value={newAsset.company_name}
                onChange={(e) => setNewAsset({ ...newAsset, company_name: e.target.value })}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                data-testid="company-name-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Sector</label>
              <select
                value={newAsset.company_sector}
                onChange={(e) => setNewAsset({ ...newAsset, company_sector: e.target.value })}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                data-testid="sector-select"
              >
                {SECTORS.map((sector) => (
                  <option key={sector} value={sector}>
                    {sector}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Subsector</label>
              <input
                type="text"
                value={newAsset.company_subsector}
                onChange={(e) => setNewAsset({ ...newAsset, company_subsector: e.target.value })}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                data-testid="subsector-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Exposure ($)</label>
              <input
                type="number"
                value={newAsset.exposure}
                onChange={(e) => setNewAsset({ ...newAsset, exposure: e.target.value })}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                data-testid="exposure-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Market Value ($)</label>
              <input
                type="number"
                value={newAsset.market_value}
                onChange={(e) => setNewAsset({ ...newAsset, market_value: e.target.value })}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                data-testid="market-value-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Base PD</label>
              <input
                type="number"
                step="0.001"
                value={newAsset.base_pd}
                onChange={(e) => setNewAsset({ ...newAsset, base_pd: e.target.value })}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                data-testid="base-pd-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Base LGD</label>
              <input
                type="number"
                step="0.01"
                value={newAsset.base_lgd}
                onChange={(e) => setNewAsset({ ...newAsset, base_lgd: e.target.value })}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                data-testid="base-lgd-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Rating</label>
              <input
                type="text"
                value={newAsset.rating}
                onChange={(e) => setNewAsset({ ...newAsset, rating: e.target.value })}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                data-testid="rating-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Maturity (years)</label>
              <input
                type="number"
                value={newAsset.maturity_years}
                onChange={(e) => setNewAsset({ ...newAsset, maturity_years: e.target.value })}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                data-testid="maturity-input"
              />
            </div>
          </div>
          <button
            onClick={handleAddAsset}
            disabled={addAssetMutation.isPending}
            className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
            data-testid="submit-asset-button"
          >
            {addAssetMutation.isPending ? 'Adding...' : 'Add Asset'}
          </button>
        </div>
      )}

      {/* Assets Table */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">Assets ({assets.length})</h2>
        {assets.length === 0 ? (
          <div className="text-muted-foreground text-center py-8" data-testid="no-assets">
            No assets in this portfolio. Add your first asset to get started.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full" data-testid="assets-table">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Type</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Company</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Sector</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-foreground">Exposure</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-foreground">Market Value</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-foreground">Base PD</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-foreground">Base LGD</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-foreground">Rating</th>
                  <th className="text-center py-3 px-4 text-sm font-medium text-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {assets.map((asset) => (
                  <tr key={asset.id} className="border-b border-border hover:bg-muted" data-testid={`asset-row-${asset.id}`}>
                    <td className="py-3 px-4 text-sm text-foreground">{asset.asset_type}</td>
                    <td className="py-3 px-4 text-sm text-foreground">
                      <div>{asset.company.name}</div>
                      {asset.company.subsector && (
                        <div className="text-xs text-muted-foreground">{asset.company.subsector}</div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-sm text-foreground">{asset.company.sector}</td>
                    <td className="py-3 px-4 text-sm text-foreground text-right">
                      ${(asset.exposure / 1e6).toFixed(2)}M
                    </td>
                    <td className="py-3 px-4 text-sm text-foreground text-right">
                      ${(asset.market_value / 1e6).toFixed(2)}M
                    </td>
                    <td className="py-3 px-4 text-sm text-foreground text-right">
                      {(asset.base_pd * 100).toFixed(2)}%
                    </td>
                    <td className="py-3 px-4 text-sm text-foreground text-right">
                      {(asset.base_lgd * 100).toFixed(1)}%
                    </td>
                    <td className="py-3 px-4 text-sm text-foreground text-center">
                      <span className="px-2 py-1 bg-muted text-foreground rounded text-xs font-medium">
                        {asset.rating}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => {
                          if (window.confirm('Remove this asset from the portfolio?')) {
                            removeAssetMutation.mutate({ portfolioId: id, assetId: asset.id });
                          }
                        }}
                        className="text-destructive hover:underline text-sm"
                        data-testid={`remove-asset-${asset.id}`}
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default PortfolioDetail;
