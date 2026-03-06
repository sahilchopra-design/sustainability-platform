/**
 * Direct Capitalization Calculator
 * Income Approach using NOI / Cap Rate
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Badge } from '../../../components/ui/badge';
import { 
  Calculator, DollarSign, TrendingUp, Building2,
  ArrowRight, RefreshCw, Info
} from 'lucide-react';
import { useDirectCapitalization } from '../hooks/useValuation';

const formatCurrency = (value) => {
  if (!value) return '$0';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(parseFloat(value));
};

const formatPercent = (value) => {
  if (!value) return '0%';
  return `${(parseFloat(value) * 100).toFixed(2)}%`;
};

export function DirectCapCalculator() {
  const { mutate: calculate, isPending, data: result, reset } = useDirectCapitalization();
  
  const [inputs, setInputs] = useState({
    rentable_area_sf: 100000,
    market_rent_per_sf: 35,
    other_income: 50000,
    vacancy_rate: 5,
    collection_loss_rate: 2,
    operating_expense_ratio: 35,
    cap_rate: 6.5,
  });

  const handleChange = (field, value) => {
    setInputs(prev => ({ ...prev, [field]: value }));
  };

  const handleCalculate = () => {
    calculate({
      rentable_area_sf: parseFloat(inputs.rentable_area_sf),
      market_rent_per_sf: parseFloat(inputs.market_rent_per_sf),
      other_income: parseFloat(inputs.other_income),
      vacancy_rate: parseFloat(inputs.vacancy_rate) / 100,
      collection_loss_rate: parseFloat(inputs.collection_loss_rate) / 100,
      operating_expense_ratio: parseFloat(inputs.operating_expense_ratio) / 100,
      cap_rate: parseFloat(inputs.cap_rate) / 100,
    });
  };

  const handleReset = () => {
    reset();
    setInputs({
      rentable_area_sf: 100000,
      market_rent_per_sf: 35,
      other_income: 50000,
      vacancy_rate: 5,
      collection_loss_rate: 2,
      operating_expense_ratio: 35,
      cap_rate: 6.5,
    });
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Input Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5 text-blue-500" />
            Direct Capitalization Inputs
          </CardTitle>
          <CardDescription>
            Enter property income and expense parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Property Size & Rent */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white/70 border-b pb-2">
              Gross Income
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="rentable_area_sf">Rentable Area (SF)</Label>
                <Input
                  id="rentable_area_sf"
                  type="number"
                  value={inputs.rentable_area_sf}
                  onChange={(e) => handleChange('rentable_area_sf', e.target.value)}
                  data-testid="input-rentable-area"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="market_rent_per_sf">Market Rent ($/SF)</Label>
                <Input
                  id="market_rent_per_sf"
                  type="number"
                  step="0.01"
                  value={inputs.market_rent_per_sf}
                  onChange={(e) => handleChange('market_rent_per_sf', e.target.value)}
                  data-testid="input-market-rent"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="other_income">Other Income ($)</Label>
              <Input
                id="other_income"
                type="number"
                value={inputs.other_income}
                onChange={(e) => handleChange('other_income', e.target.value)}
                data-testid="input-other-income"
              />
              <p className="text-xs text-white/40">Parking, storage, laundry, etc.</p>
            </div>
          </div>

          {/* Vacancy & Collection Loss */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white/70 border-b pb-2">
              Vacancy & Losses
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="vacancy_rate">Vacancy Rate (%)</Label>
                <Input
                  id="vacancy_rate"
                  type="number"
                  step="0.1"
                  value={inputs.vacancy_rate}
                  onChange={(e) => handleChange('vacancy_rate', e.target.value)}
                  data-testid="input-vacancy-rate"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="collection_loss_rate">Collection Loss (%)</Label>
                <Input
                  id="collection_loss_rate"
                  type="number"
                  step="0.1"
                  value={inputs.collection_loss_rate}
                  onChange={(e) => handleChange('collection_loss_rate', e.target.value)}
                  data-testid="input-collection-loss"
                />
              </div>
            </div>
          </div>

          {/* Operating Expenses */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white/70 border-b pb-2">
              Operating Expenses
            </h4>
            <div className="space-y-2">
              <Label htmlFor="operating_expense_ratio">Expense Ratio (%)</Label>
              <Input
                id="operating_expense_ratio"
                type="number"
                step="0.1"
                value={inputs.operating_expense_ratio}
                onChange={(e) => handleChange('operating_expense_ratio', e.target.value)}
                data-testid="input-expense-ratio"
              />
              <p className="text-xs text-white/40">
                Includes taxes, insurance, maintenance, management
              </p>
            </div>
          </div>

          {/* Cap Rate */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-white/70 border-b pb-2">
              Capitalization Rate
            </h4>
            <div className="space-y-2">
              <Label htmlFor="cap_rate">Cap Rate (%)</Label>
              <Input
                id="cap_rate"
                type="number"
                step="0.1"
                value={inputs.cap_rate}
                onChange={(e) => handleChange('cap_rate', e.target.value)}
                data-testid="input-cap-rate"
              />
            </div>
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <Button 
              onClick={handleCalculate} 
              disabled={isPending}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
              data-testid="btn-calculate-direct-cap"
            >
              {isPending ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Calculator className="h-4 w-4 mr-2" />
              )}
              Calculate Value
            </Button>
            <Button 
              variant="outline" 
              onClick={handleReset}
              data-testid="btn-reset-direct-cap"
            >
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      <Card className={result ? 'ring-2 ring-blue-200' : ''}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5 text-emerald-500" />
            Valuation Results
          </CardTitle>
          <CardDescription>
            Property value using direct capitalization
          </CardDescription>
        </CardHeader>
        <CardContent>
          {result ? (
            <div className="space-y-6">
              {/* Final Value */}
              <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-lg p-6 text-center">
                <p className="text-sm text-emerald-400 font-medium mb-1">Property Value</p>
                <p className="text-4xl font-bold text-emerald-900">
                  {formatCurrency(result.property_value)}
                </p>
                <p className="text-sm text-emerald-400 mt-2">
                  {formatCurrency(result.value_per_sf)} / SF
                </p>
              </div>

              {/* Income Breakdown */}
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-white/70 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  Income Statement
                </h4>
                <div className="bg-white/[0.02] rounded-lg p-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Potential Gross Income (PGI)</span>
                    <span className="font-medium">{formatCurrency(result.pgi)}</span>
                  </div>
                  <div className="flex justify-between text-sm text-red-400">
                    <span>Less: Vacancy Loss</span>
                    <span>({formatCurrency(result.vacancy_loss)})</span>
                  </div>
                  <div className="flex justify-between text-sm text-red-400">
                    <span>Less: Collection Loss</span>
                    <span>({formatCurrency(result.collection_loss)})</span>
                  </div>
                  <div className="flex justify-between text-sm font-medium border-t pt-2">
                    <span>Effective Gross Income (EGI)</span>
                    <span>{formatCurrency(result.egi)}</span>
                  </div>
                  <div className="flex justify-between text-sm text-red-400">
                    <span>Less: Operating Expenses</span>
                    <span>({formatCurrency(result.operating_expenses)})</span>
                  </div>
                  <div className="flex justify-between text-sm font-bold border-t pt-2 text-emerald-400">
                    <span>Net Operating Income (NOI)</span>
                    <span>{formatCurrency(result.noi)}</span>
                  </div>
                </div>
              </div>

              {/* Key Metrics */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-white/[0.02] rounded-lg p-3 text-center">
                  <p className="text-xs text-white/40">Expense Ratio</p>
                  <p className="text-lg font-semibold">{formatPercent(result.expense_ratio)}</p>
                </div>
                <div className="bg-white/[0.02] rounded-lg p-3 text-center">
                  <p className="text-xs text-white/40">GIM</p>
                  <p className="text-lg font-semibold">{parseFloat(result.gross_income_multiplier).toFixed(2)}x</p>
                </div>
                <div className="bg-white/[0.02] rounded-lg p-3 text-center">
                  <p className="text-xs text-white/40">NIM</p>
                  <p className="text-lg font-semibold">{parseFloat(result.net_income_multiplier).toFixed(2)}x</p>
                </div>
              </div>

              {/* Formula */}
              <div className="bg-blue-500/10 rounded-lg p-4">
                <div className="flex items-center gap-2 text-blue-300 text-sm mb-2">
                  <Info className="h-4 w-4" />
                  <span className="font-medium">Direct Capitalization Formula</span>
                </div>
                <p className="text-sm text-blue-300">
                  Value = NOI / Cap Rate = {formatCurrency(result.noi)} / {formatPercent(result.cap_rate)} = {formatCurrency(result.property_value)}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-white/30">
              <Building2 className="h-16 w-16 mb-4 opacity-50" />
              <p className="text-sm">Enter inputs and click Calculate</p>
              <p className="text-xs mt-1">Results will appear here</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default DirectCapCalculator;
