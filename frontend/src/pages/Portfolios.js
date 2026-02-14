import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getPortfolios, createPortfolio, deletePortfolio } from '../utils/api';

function Portfolios() {
  const queryClient = useQueryClient();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [newPortfolioDescription, setNewPortfolioDescription] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['portfolios'],
    queryFn: async () => {
      const res = await getPortfolios();
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: createPortfolio,
    onSuccess: () => {
      queryClient.invalidateQueries(['portfolios']);
      setShowCreateForm(false);
      setNewPortfolioName('');
      setNewPortfolioDescription('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deletePortfolio,
    onSuccess: () => {
      queryClient.invalidateQueries(['portfolios']);
    },
  });

  const portfolios = data?.portfolios || [];

  const handleCreate = () => {
    if (newPortfolioName.trim()) {
      createMutation.mutate({
        name: newPortfolioName,
        description: newPortfolioDescription,
      });
    }
  };

  return (
    <div className="p-8" data-testid="portfolios-page">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-semibold text-foreground">Portfolios</h1>
          <p className="text-muted-foreground mt-2">Manage your climate risk portfolios</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          data-testid="create-portfolio-button"
        >
          {showCreateForm ? 'Cancel' : 'Create Portfolio'}
        </button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="bg-card border border-border rounded-xl p-6 mb-6" data-testid="create-portfolio-form">
          <h2 className="text-lg font-semibold text-foreground mb-4">New Portfolio</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Portfolio Name *
              </label>
              <input
                type="text"
                value={newPortfolioName}
                onChange={(e) => setNewPortfolioName(e.target.value)}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                placeholder="e.g., European Energy Portfolio"
                data-testid="portfolio-name-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Description
              </label>
              <textarea
                value={newPortfolioDescription}
                onChange={(e) => setNewPortfolioDescription(e.target.value)}
                className="w-full px-4 py-2 bg-background border border-input rounded-lg text-foreground"
                rows={3}
                placeholder="Describe the portfolio..."
                data-testid="portfolio-description-input"
              />
            </div>
            <button
              onClick={handleCreate}
              disabled={!newPortfolioName.trim() || createMutation.isPending}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
              data-testid="submit-portfolio-button"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Portfolio'}
            </button>
          </div>
        </div>
      )}

      {/* Portfolio List */}
      {isLoading ? (
        <div className="text-muted-foreground">Loading portfolios...</div>
      ) : portfolios.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-8 text-center" data-testid="no-portfolios">
          <p className="text-muted-foreground mb-4">No portfolios yet</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Create Your First Portfolio
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="portfolios-grid">
          {portfolios.map((portfolio) => (
            <div
              key={portfolio.id}
              className="bg-card border border-border rounded-xl p-6 hover:shadow-lg transition-shadow"
              data-testid={`portfolio-card-${portfolio.id}`}
            >
              <Link to={`/portfolios/${portfolio.id}`}>
                <h3 className="text-lg font-semibold text-foreground mb-2 hover:text-primary transition-colors">
                  {portfolio.name}
                </h3>
              </Link>
              {portfolio.description && (
                <p className="text-sm text-muted-foreground mb-4">{portfolio.description}</p>
              )}
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Assets:</span>
                  <span className="font-medium text-foreground">{portfolio.num_assets}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Exposure:</span>
                  <span className="font-medium text-foreground">
                    ${(portfolio.total_exposure / 1e6).toFixed(1)}M
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Created:</span>
                  <span className="text-muted-foreground">
                    {new Date(portfolio.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <div className="flex gap-2">
                <Link
                  to={`/portfolios/${portfolio.id}`}
                  className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-center"
                  data-testid={`view-portfolio-${portfolio.id}`}
                >
                  View Details
                </Link>
                <button
                  onClick={() => {
                    if (window.confirm('Are you sure you want to delete this portfolio?')) {
                      deleteMutation.mutate(portfolio.id);
                    }
                  }}
                  className="px-4 py-2 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors"
                  data-testid={`delete-portfolio-${portfolio.id}`}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Portfolios;
