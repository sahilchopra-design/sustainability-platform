/**
 * Portfolio Selector Component
 * Dropdown to select a portfolio for analysis
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Badge } from '../../../components/ui/badge';
import { Skeleton } from '../../../components/ui/skeleton';
import { Briefcase, Building2, DollarSign, TrendingUp } from 'lucide-react';

const STRATEGY_COLORS = {
  core: 'bg-blue-500/10 text-blue-300',
  core_plus: 'bg-violet-50 text-violet-700',
  value_add: 'bg-amber-500/10 text-amber-400',
  opportunistic: 'bg-red-500/10 text-red-400',
  debt: 'bg-gray-50 text-gray-700',
};

const TYPE_COLORS = {
  fund: 'bg-emerald-500/10 text-emerald-400',
  reit: 'bg-cyan-50 text-cyan-700',
  separate_account: 'bg-purple-500/10 text-purple-300',
  index: 'bg-gray-50 text-gray-800',
  pension: 'bg-orange-500/10 text-orange-400',
  insurance: 'bg-pink-50 text-pink-700',
};

function formatCurrency(value) {
  const num = parseFloat(value);
  if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
  if (num >= 1e6) return `$${(num / 1e6).toFixed(0)}M`;
  return `$${num.toLocaleString()}`;
}

export function PortfolioSelector({ 
  portfolios, 
  selectedId, 
  onSelect, 
  isLoading,
  showDetails = true 
}) {
  const selectedPortfolio = portfolios?.items?.find(p => p.id === selectedId);
  
  if (isLoading) {
    return (
      <Card className="bg-white" data-testid="portfolio-selector-loading">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <Briefcase className="h-4 w-4" />
            Select Portfolio
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-10 w-full mb-4" />
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card className="bg-white" data-testid="portfolio-selector">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <Briefcase className="h-4 w-4 text-blue-500" />
          Select Portfolio
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Select value={selectedId || ''} onValueChange={onSelect}>
          <SelectTrigger className="w-full" data-testid="portfolio-select-trigger">
            <SelectValue placeholder="Choose a portfolio..." />
          </SelectTrigger>
          <SelectContent>
            {portfolios?.items?.map((portfolio) => (
              <SelectItem key={portfolio.id} value={portfolio.id} data-testid={`portfolio-option-${portfolio.id}`}>
                <div className="flex items-center gap-2">
                  <span>{portfolio.name}</span>
                  <span className="text-xs text-gray-500">
                    ({portfolio.total_properties} properties)
                  </span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        {showDetails && selectedPortfolio && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg space-y-3" data-testid="portfolio-details">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-medium text-gray-900">{selectedPortfolio.name}</h3>
                <p className="text-xs text-gray-500 mt-0.5">{selectedPortfolio.description}</p>
              </div>
              <div className="flex gap-1">
                <Badge 
                  variant="outline" 
                  className={TYPE_COLORS[selectedPortfolio.portfolio_type] || 'bg-gray-50'}
                >
                  {selectedPortfolio.portfolio_type?.replace('_', ' ')}
                </Badge>
                {selectedPortfolio.investment_strategy && (
                  <Badge 
                    variant="outline" 
                    className={STRATEGY_COLORS[selectedPortfolio.investment_strategy] || 'bg-gray-50'}
                  >
                    {selectedPortfolio.investment_strategy?.replace('_', ' ')}
                  </Badge>
                )}
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-2 pt-2 border-t border-gray-200">
              <div className="text-center">
                <Building2 className="h-4 w-4 mx-auto text-gray-500" />
                <p className="text-lg font-semibold text-gray-900">{selectedPortfolio.total_properties}</p>
                <p className="text-[10px] text-gray-500">Properties</p>
              </div>
              <div className="text-center">
                <DollarSign className="h-4 w-4 mx-auto text-gray-500" />
                <p className="text-lg font-semibold text-gray-900">
                  {formatCurrency(selectedPortfolio.total_value || 0)}
                </p>
                <p className="text-[10px] text-gray-500">Total Value</p>
              </div>
              <div className="text-center">
                <TrendingUp className="h-4 w-4 mx-auto text-gray-500" />
                <p className="text-lg font-semibold text-gray-900">
                  {selectedPortfolio.target_return ? `${selectedPortfolio.target_return}%` : '-'}
                </p>
                <p className="text-[10px] text-gray-500">Target Return</p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
