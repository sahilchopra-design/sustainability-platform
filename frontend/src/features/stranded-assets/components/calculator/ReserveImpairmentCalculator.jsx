import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Button } from '../../../../components/ui/button';
import { Badge } from '../../../../components/ui/badge';
import { 
  Calculator, Target, TrendingDown, AlertTriangle, 
  CheckCircle, ChevronRight, BarChart3
} from 'lucide-react';
import { 
  useReserves, 
  useScenarios, 
  useReserveImpairment 
} from '../../hooks/useStrandedAssets';

const RISK_BADGE_COLORS = {
  low: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  critical: 'bg-red-100 text-red-700 border-red-200',
};

const formatCurrency = (value) => {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toFixed(0)}`;
};

export function ReserveImpairmentCalculator() {
  const { data: reservesData, loading: reservesLoading } = useReserves();
  const { data: scenarios, loading: scenariosLoading } = useScenarios();
  const { data: results, loading: calculating, calculate, error } = useReserveImpairment();

  const [selectedReserves, setSelectedReserves] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState('');
  const [targetYears, setTargetYears] = useState([2030, 2040, 2050]);
  const [discountRate, setDiscountRate] = useState(8);

  const reserves = reservesData?.items || [];

  const handleReserveToggle = (id) => {
    setSelectedReserves(prev => 
      prev.includes(id) 
        ? prev.filter(r => r !== id)
        : [...prev, id]
    );
  };

  const handleYearToggle = (year) => {
    setTargetYears(prev => 
      prev.includes(year)
        ? prev.filter(y => y !== year)
        : [...prev, year].sort()
    );
  };

  const handleCalculate = async () => {
    if (selectedReserves.length === 0 || !selectedScenario) return;
    
    await calculate({
      reserve_ids: selectedReserves,
      scenario_id: selectedScenario,
      target_years: targetYears,
      discount_rate: discountRate / 100,
    });
  };

  return (
    <div className="space-y-6" data-testid="reserve-impairment-calculator">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5" />
              Reserve Impairment Calculator
            </CardTitle>
            <CardDescription>
              Analyze fossil fuel reserves under climate transition scenarios
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Reserve Selection */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Select Reserves ({selectedReserves.length} selected)
              </label>
              <div className="space-y-2 max-h-48 overflow-y-auto border rounded-lg p-2">
                {reservesLoading ? (
                  <div className="flex items-center justify-center h-20">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-amber-500"></div>
                  </div>
                ) : reserves.map((reserve) => (
                  <label 
                    key={reserve.id}
                    className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                      selectedReserves.includes(reserve.id)
                        ? 'bg-amber-50 dark:bg-amber-900/20 border border-amber-200'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-800'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedReserves.includes(reserve.id)}
                      onChange={() => handleReserveToggle(reserve.id)}
                      className="rounded border-slate-300"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{reserve.asset_name}</p>
                      <p className="text-xs text-slate-500">
                        {reserve.reserve_type.toUpperCase()} • {reserve.proven_reserves_mmBOE} mmBOE
                      </p>
                    </div>
                    <Badge variant="outline" className="capitalize">
                      {reserve.reserve_type}
                    </Badge>
                  </label>
                ))}
              </div>
            </div>

            {/* Scenario Selection */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Climate Scenario
              </label>
              <select
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 bg-white dark:bg-slate-800"
                data-testid="scenario-select"
              >
                <option value="">Select a scenario...</option>
                {scenariosLoading ? (
                  <option disabled>Loading...</option>
                ) : scenarios.map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Target Years */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Target Years
              </label>
              <div className="flex flex-wrap gap-2">
                {[2030, 2035, 2040, 2045, 2050].map((year) => (
                  <button
                    key={year}
                    onClick={() => handleYearToggle(year)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      targetYears.includes(year)
                        ? 'bg-amber-500 text-white'
                        : 'bg-slate-100 dark:bg-slate-800 hover:bg-slate-200'
                    }`}
                  >
                    {year}
                  </button>
                ))}
              </div>
            </div>

            {/* Discount Rate */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Discount Rate: {discountRate}%
              </label>
              <input
                type="range"
                min="0"
                max="20"
                step="0.5"
                value={discountRate}
                onChange={(e) => setDiscountRate(parseFloat(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-slate-500 mt-1">
                <span>0%</span>
                <span>20%</span>
              </div>
            </div>

            <Button 
              onClick={handleCalculate}
              disabled={selectedReserves.length === 0 || !selectedScenario || calculating}
              className="w-full bg-amber-600 hover:bg-amber-700"
              data-testid="calculate-button"
            >
              {calculating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Calculating...
                </>
              ) : (
                <>
                  <Calculator className="h-4 w-4 mr-2" />
                  Calculate Impairment
                </>
              )}
            </Button>

            {error && (
              <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 rounded-lg text-red-600 text-sm">
                {error}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Calculation Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            {calculating ? (
              <div className="flex flex-col items-center justify-center h-64">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-amber-500 mb-4"></div>
                <p className="text-slate-500">Analyzing reserves...</p>
              </div>
            ) : results?.results?.length > 0 ? (
              <div className="space-y-6">
                {/* Summary */}
                <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-500 mb-1">Scenario: {results.scenario_name}</p>
                  <div className="grid grid-cols-2 gap-4 mt-3">
                    <div>
                      <p className="text-xs text-slate-500">Total Stranded Value</p>
                      <p className="text-xl font-bold text-red-600">
                        {formatCurrency(results.portfolio_summary?.total_stranded_value_usd || 0)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Avg Risk Score</p>
                      <p className="text-xl font-bold">
                        {((results.portfolio_summary?.avg_risk_score || 0) * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                </div>

                {/* Individual Results */}
                <div className="space-y-4">
                  {results.results.map((result) => (
                    <div 
                      key={result.reserve_id}
                      className="border rounded-lg p-4"
                      data-testid="impairment-result"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h4 className="font-medium">{result.asset_name}</h4>
                          <p className="text-xs text-slate-500 uppercase">
                            {result.reserve_type} • {result.total_reserves_mmBOE} mmBOE
                          </p>
                        </div>
                        <Badge className={RISK_BADGE_COLORS[result.risk_category]}>
                          {result.risk_category.toUpperCase()}
                        </Badge>
                      </div>

                      {/* Risk Score Gauge */}
                      <div className="flex items-center gap-4 mb-4">
                        <div className="relative w-16 h-16">
                          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                            <circle
                              cx="18"
                              cy="18"
                              r="15.9155"
                              fill="none"
                              stroke="#e5e7eb"
                              strokeWidth="3"
                            />
                            <circle
                              cx="18"
                              cy="18"
                              r="15.9155"
                              fill="none"
                              stroke={
                                result.stranding_risk_score >= 0.75 ? '#ef4444' :
                                result.stranding_risk_score >= 0.5 ? '#f97316' :
                                result.stranding_risk_score >= 0.25 ? '#eab308' : '#22c55e'
                              }
                              strokeWidth="3"
                              strokeDasharray={`${result.stranding_risk_score * 100} 100`}
                              strokeLinecap="round"
                            />
                          </svg>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <span className="text-sm font-bold">
                              {(result.stranding_risk_score * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                        <div className="flex-1 grid grid-cols-2 gap-2">
                          <div className="bg-red-50 dark:bg-red-900/20 p-2 rounded">
                            <p className="text-xs text-slate-500">Stranded</p>
                            <p className="font-bold text-red-600">{result.total_stranded_percent}%</p>
                          </div>
                          <div className="bg-orange-50 dark:bg-orange-900/20 p-2 rounded">
                            <p className="text-xs text-slate-500">NPV Impact</p>
                            <p className="font-bold text-orange-600">{result.npv_impact_percent}%</p>
                          </div>
                        </div>
                      </div>

                      {/* Stranded Value */}
                      <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg mb-4">
                        <TrendingDown className="h-5 w-5 text-red-500" />
                        <div className="flex-1">
                          <p className="text-xs text-slate-500">Stranded Value</p>
                          <p className="font-bold text-red-600">
                            {formatCurrency(result.total_stranded_value_usd)}
                          </p>
                        </div>
                      </div>

                      {/* Recommendations */}
                      <div>
                        <p className="text-xs font-medium text-slate-500 mb-2">Recommendations</p>
                        <ul className="space-y-1">
                          {result.recommendations.map((rec, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs">
                              <CheckCircle className="h-3 w-3 text-emerald-500 mt-0.5 flex-shrink-0" />
                              <span>{rec}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                <Target className="h-12 w-12 mb-4" />
                <p className="text-center">
                  Select reserves and a scenario, then click Calculate to analyze impairment
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default ReserveImpairmentCalculator;
