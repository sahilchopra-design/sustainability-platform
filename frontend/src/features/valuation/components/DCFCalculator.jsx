/**
 * DCF (Discounted Cash Flow) Calculator
 * Income Approach using projected cash flows
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Badge } from '../../../components/ui/badge';
import { 
  Calculator, DollarSign, TrendingUp, LineChart,
  RefreshCw, Info, ChevronRight
} from 'lucide-react';
import { useDCF } from '../hooks/useValuation';

const formatCurrency = (value, compact = false) => {
  if (!value) return '$0';
  const num = parseFloat(value);
  if (compact && Math.abs(num) >= 1000000) {
    return `$${(num / 1000000).toFixed(2)}M`;
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
};

const formatPercent = (value) => {
  if (!value) return '0%';
  return `${(parseFloat(value) * 100).toFixed(2)}%`;
};

export function DCFCalculator() {
  const { mutate: calculate, isPending, data: result, reset } = useDCF();
  
  const [inputs, setInputs] = useState({
    projection_years: 10,
    current_noi: 2500000,
    revenue_growth_rate: 3,
    expense_growth_rate: 2,
    inflation_rate: 2,
    discount_rate: 8,
    terminal_cap_rate: 6.5,
    terminal_growth_rate: 2,
    equity_investment: 12000000,
    debt_service: 1500000,
    selling_costs_percent: 3,
  });

  const handleChange = (field, value) => {
    setInputs(prev => ({ ...prev, [field]: value }));
  };

  const handleCalculate = () => {
    calculate({
      projection_years: parseInt(inputs.projection_years),
      current_noi: parseFloat(inputs.current_noi),
      revenue_growth_rate: parseFloat(inputs.revenue_growth_rate) / 100,
      expense_growth_rate: parseFloat(inputs.expense_growth_rate) / 100,
      inflation_rate: parseFloat(inputs.inflation_rate) / 100,
      discount_rate: parseFloat(inputs.discount_rate) / 100,
      terminal_cap_rate: parseFloat(inputs.terminal_cap_rate) / 100,
      terminal_growth_rate: parseFloat(inputs.terminal_growth_rate) / 100,
      equity_investment: parseFloat(inputs.equity_investment),
      debt_service: parseFloat(inputs.debt_service),
      selling_costs_percent: parseFloat(inputs.selling_costs_percent) / 100,
    });
  };

  const handleReset = () => {
    reset();
    setInputs({
      projection_years: 10,
      current_noi: 2500000,
      revenue_growth_rate: 3,
      expense_growth_rate: 2,
      inflation_rate: 2,
      discount_rate: 8,
      terminal_cap_rate: 6.5,
      terminal_growth_rate: 2,
      equity_investment: 12000000,
      debt_service: 1500000,
      selling_costs_percent: 3,
    });
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <LineChart className="h-5 w-5 text-violet-500" />
              DCF Analysis Inputs
            </CardTitle>
            <CardDescription>
              Multi-year cash flow projection parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Projection Period */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Projection Years</Label>
                <Input
                  type="number"
                  min="1"
                  max="30"
                  value={inputs.projection_years}
                  onChange={(e) => handleChange('projection_years', e.target.value)}
                  data-testid="input-projection-years"
                />
              </div>
              <div className="space-y-2">
                <Label>Current NOI ($)</Label>
                <Input
                  type="number"
                  value={inputs.current_noi}
                  onChange={(e) => handleChange('current_noi', e.target.value)}
                  data-testid="input-current-noi"
                />
              </div>
            </div>

            {/* Growth Rates */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-slate-700 border-b pb-2">
                Growth Assumptions
              </h4>
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-2">
                  <Label className="text-xs">Revenue Growth (%)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={inputs.revenue_growth_rate}
                    onChange={(e) => handleChange('revenue_growth_rate', e.target.value)}
                    data-testid="input-revenue-growth"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Expense Growth (%)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={inputs.expense_growth_rate}
                    onChange={(e) => handleChange('expense_growth_rate', e.target.value)}
                    data-testid="input-expense-growth"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Inflation (%)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={inputs.inflation_rate}
                    onChange={(e) => handleChange('inflation_rate', e.target.value)}
                    data-testid="input-inflation"
                  />
                </div>
              </div>
            </div>

            {/* Discount & Terminal */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-slate-700 border-b pb-2">
                Discount & Exit Assumptions
              </h4>
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-2">
                  <Label className="text-xs">Discount Rate (%)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={inputs.discount_rate}
                    onChange={(e) => handleChange('discount_rate', e.target.value)}
                    data-testid="input-discount-rate"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Terminal Cap (%)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={inputs.terminal_cap_rate}
                    onChange={(e) => handleChange('terminal_cap_rate', e.target.value)}
                    data-testid="input-terminal-cap"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Terminal Growth (%)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={inputs.terminal_growth_rate}
                    onChange={(e) => handleChange('terminal_growth_rate', e.target.value)}
                    data-testid="input-terminal-growth"
                  />
                </div>
              </div>
            </div>

            {/* Capital Structure */}
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-slate-700 border-b pb-2">
                Capital Structure
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Equity Investment ($)</Label>
                  <Input
                    type="number"
                    value={inputs.equity_investment}
                    onChange={(e) => handleChange('equity_investment', e.target.value)}
                    data-testid="input-equity-investment"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Annual Debt Service ($)</Label>
                  <Input
                    type="number"
                    value={inputs.debt_service}
                    onChange={(e) => handleChange('debt_service', e.target.value)}
                    data-testid="input-debt-service"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Selling Costs (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={inputs.selling_costs_percent}
                  onChange={(e) => handleChange('selling_costs_percent', e.target.value)}
                  data-testid="input-selling-costs"
                />
              </div>
            </div>

            {/* Buttons */}
            <div className="flex gap-3 pt-4">
              <Button 
                onClick={handleCalculate} 
                disabled={isPending}
                className="flex-1 bg-violet-600 hover:bg-violet-700"
                data-testid="btn-calculate-dcf"
              >
                {isPending ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Calculator className="h-4 w-4 mr-2" />
                )}
                Run DCF Analysis
              </Button>
              <Button variant="outline" onClick={handleReset}>
                Reset
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Key Results */}
        <Card className={result ? 'ring-2 ring-violet-200' : ''}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-emerald-500" />
              Investment Returns
            </CardTitle>
            <CardDescription>
              Key metrics from DCF analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            {result ? (
              <div className="space-y-6">
                {/* NPV */}
                <div className="bg-gradient-to-br from-violet-50 to-violet-100 rounded-lg p-6 text-center">
                  <p className="text-sm text-violet-600 font-medium mb-1">Net Present Value (NPV)</p>
                  <p className="text-4xl font-bold text-violet-900">
                    {formatCurrency(result.npv)}
                  </p>
                </div>

                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-emerald-50 rounded-lg p-4 text-center">
                    <p className="text-xs text-emerald-600 font-medium">IRR</p>
                    <p className="text-2xl font-bold text-emerald-900">
                      {formatPercent(result.irr)}
                    </p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <p className="text-xs text-blue-600 font-medium">Equity Multiple</p>
                    <p className="text-2xl font-bold text-blue-900">
                      {parseFloat(result.equity_multiple).toFixed(2)}x
                    </p>
                  </div>
                  <div className="bg-amber-50 rounded-lg p-4 text-center">
                    <p className="text-xs text-amber-600 font-medium">Cash-on-Cash (Yr 1)</p>
                    <p className="text-2xl font-bold text-amber-900">
                      {formatPercent(result.cash_on_cash_year1)}
                    </p>
                  </div>
                  <div className="bg-slate-50 rounded-lg p-4 text-center">
                    <p className="text-xs text-slate-600 font-medium">Avg Cash-on-Cash</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {formatPercent(result.average_cash_on_cash)}
                    </p>
                  </div>
                </div>

                {/* Terminal Value */}
                <div className="bg-slate-50 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-slate-600">Terminal Value</span>
                    <span className="font-semibold">{formatCurrency(result.terminal_value)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">PV of Terminal Value</span>
                    <span className="font-semibold">{formatCurrency(result.terminal_value_present)}</span>
                  </div>
                </div>

                {/* Payback */}
                {result.payback_period_years && (
                  <div className="bg-green-50 rounded-lg p-4 flex items-center justify-between">
                    <span className="text-sm text-green-700">Payback Period</span>
                    <Badge className="bg-green-100 text-green-800">
                      {result.payback_period_years} years
                    </Badge>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-slate-400">
                <LineChart className="h-16 w-16 mb-4 opacity-50" />
                <p className="text-sm">Enter inputs and click Run DCF Analysis</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Cash Flow Table */}
      {result && result.cash_flows && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-slate-500" />
              Projected Cash Flows
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-2 px-3 font-medium text-slate-600">Year</th>
                    <th className="text-right py-2 px-3 font-medium text-slate-600">Revenue</th>
                    <th className="text-right py-2 px-3 font-medium text-slate-600">Expenses</th>
                    <th className="text-right py-2 px-3 font-medium text-slate-600">NOI</th>
                    <th className="text-right py-2 px-3 font-medium text-slate-600">Debt Service</th>
                    <th className="text-right py-2 px-3 font-medium text-slate-600">CFADS</th>
                    <th className="text-right py-2 px-3 font-medium text-slate-600">Cumulative</th>
                  </tr>
                </thead>
                <tbody>
                  {result.cash_flows.map((cf) => (
                    <tr key={cf.year} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-2 px-3 font-medium">Year {cf.year}</td>
                      <td className="py-2 px-3 text-right">{formatCurrency(cf.revenue, true)}</td>
                      <td className="py-2 px-3 text-right text-red-600">({formatCurrency(cf.expenses, true)})</td>
                      <td className="py-2 px-3 text-right font-medium">{formatCurrency(cf.noi, true)}</td>
                      <td className="py-2 px-3 text-right text-red-600">({formatCurrency(cf.debt_service, true)})</td>
                      <td className="py-2 px-3 text-right font-medium text-emerald-600">{formatCurrency(cf.cfads, true)}</td>
                      <td className="py-2 px-3 text-right">{formatCurrency(cf.cumulative_cash_flow, true)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Sensitivity Analysis */}
      {result && result.sensitivity_cap_rate && Object.keys(result.sensitivity_cap_rate).length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Sensitivity: Terminal Cap Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(result.sensitivity_cap_rate).map(([rate, value]) => (
                  <div key={rate} className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">{(parseFloat(rate) * 100).toFixed(1)}%</span>
                    <span className="font-medium">{formatCurrency(value)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Sensitivity: Discount Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(result.sensitivity_discount_rate).map(([rate, value]) => (
                  <div key={rate} className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">{(parseFloat(rate) * 100).toFixed(1)}%</span>
                    <span className="font-medium">{formatCurrency(value)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

export default DCFCalculator;
