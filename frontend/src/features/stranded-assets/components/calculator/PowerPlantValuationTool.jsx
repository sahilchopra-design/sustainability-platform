import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Button } from '../../../../components/ui/button';
import { Badge } from '../../../../components/ui/badge';
import { 
  Factory, Calculator, TrendingDown, Zap, Wrench,
  CheckCircle, ArrowRight, DollarSign
} from 'lucide-react';
import { 
  usePowerPlants, 
  useScenarios, 
  usePowerPlantValuation 
} from '../../hooks/useStrandedAssets';

const TECHNOLOGY_COLORS = {
  coal: { bg: 'bg-slate-100', text: 'text-slate-700', icon: '⚫' },
  gas_ccgt: { bg: 'bg-blue-100', text: 'text-blue-700', icon: '🔵' },
  gas_ocgt: { bg: 'bg-sky-100', text: 'text-sky-700', icon: '💨' },
  nuclear: { bg: 'bg-purple-100', text: 'text-purple-700', icon: '☢️' },
  hydro: { bg: 'bg-cyan-100', text: 'text-cyan-700', icon: '💧' },
  wind_onshore: { bg: 'bg-emerald-100', text: 'text-emerald-700', icon: '🌬️' },
  wind_offshore: { bg: 'bg-teal-100', text: 'text-teal-700', icon: '🌊' },
  solar_pv: { bg: 'bg-yellow-100', text: 'text-yellow-700', icon: '☀️' },
};

const RISK_BADGE_COLORS = {
  low: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

const formatCurrency = (value) => {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toFixed(0)}`;
};

export function PowerPlantValuationTool() {
  const { data: plantsData, loading: plantsLoading } = usePowerPlants();
  const { data: scenarios, loading: scenariosLoading } = useScenarios();
  const { data: results, loading: calculating, calculate, error } = usePowerPlantValuation();

  const [selectedPlants, setSelectedPlants] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState('');
  const [targetYears, setTargetYears] = useState([2030, 2040]);
  const [discountRate, setDiscountRate] = useState(6);
  const [includeRepurposing, setIncludeRepurposing] = useState(true);
  const [technologyFilter, setTechnologyFilter] = useState('');

  const plants = plantsData?.items || [];
  const filteredPlants = technologyFilter 
    ? plants.filter(p => p.technology_type === technologyFilter)
    : plants;

  const handlePlantToggle = (id) => {
    setSelectedPlants(prev => 
      prev.includes(id) 
        ? prev.filter(p => p !== id)
        : [...prev, id]
    );
  };

  const handleCalculate = async () => {
    if (selectedPlants.length === 0 || !selectedScenario) return;
    
    await calculate({
      plant_ids: selectedPlants,
      scenario_id: selectedScenario,
      target_years: targetYears,
      discount_rate: discountRate / 100,
      include_repurposing: includeRepurposing,
    });
  };

  const uniqueTechnologies = [...new Set(plants.map(p => p.technology_type))];

  return (
    <div className="space-y-6" data-testid="power-plant-valuation-tool">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Factory className="h-5 w-5" />
              Power Plant Valuation Tool
            </CardTitle>
            <CardDescription>
              Analyze power plant NPV under climate transition scenarios
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Technology Filter */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Filter by Technology
              </label>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setTechnologyFilter('')}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    !technologyFilter
                      ? 'bg-amber-500 text-white'
                      : 'bg-slate-100 hover:bg-slate-200'
                  }`}
                >
                  All
                </button>
                {uniqueTechnologies.map(tech => {
                  const colors = TECHNOLOGY_COLORS[tech] || { bg: 'bg-slate-100', text: 'text-slate-700' };
                  return (
                    <button
                      key={tech}
                      onClick={() => setTechnologyFilter(tech)}
                      className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                        technologyFilter === tech
                          ? 'bg-amber-500 text-white'
                          : `${colors.bg} ${colors.text} hover:opacity-80`
                      }`}
                    >
                      {tech.replace('_', ' ').toUpperCase()}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Plant Selection */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Select Power Plants ({selectedPlants.length} selected)
              </label>
              <div className="space-y-2 max-h-48 overflow-y-auto border rounded-lg p-2">
                {plantsLoading ? (
                  <div className="flex items-center justify-center h-20">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-amber-500"></div>
                  </div>
                ) : filteredPlants.map((plant) => {
                  const colors = TECHNOLOGY_COLORS[plant.technology_type] || { bg: 'bg-slate-100', text: 'text-slate-700', icon: '⚡' };
                  return (
                    <label 
                      key={plant.id}
                      className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                        selectedPlants.includes(plant.id)
                          ? 'bg-amber-50 dark:bg-amber-900/20 border border-amber-200'
                          : 'hover:bg-slate-50 dark:hover:bg-slate-800'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedPlants.includes(plant.id)}
                        onChange={() => handlePlantToggle(plant.id)}
                        className="rounded border-slate-300"
                      />
                      <div className="flex-1">
                        <p className="font-medium text-sm">{plant.plant_name}</p>
                        <p className="text-xs text-slate-500">
                          {plant.capacity_mw} MW • {plant.country_code}
                        </p>
                      </div>
                      <Badge className={`${colors.bg} ${colors.text}`}>
                        {colors.icon} {plant.technology_type.replace('_', ' ')}
                      </Badge>
                    </label>
                  );
                })}
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
                    onClick={() => setTargetYears(prev => 
                      prev.includes(year)
                        ? prev.filter(y => y !== year)
                        : [...prev, year].sort()
                    )}
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

            {/* Options */}
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium mb-2">
                  Discount Rate: {discountRate}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="15"
                  step="0.5"
                  value={discountRate}
                  onChange={(e) => setDiscountRate(parseFloat(e.target.value))}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeRepurposing}
                  onChange={(e) => setIncludeRepurposing(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <span className="text-sm">Include Repurposing Options</span>
              </label>
            </div>

            <Button 
              onClick={handleCalculate}
              disabled={selectedPlants.length === 0 || !selectedScenario || calculating}
              className="w-full bg-amber-600 hover:bg-amber-700"
            >
              {calculating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Calculating...
                </>
              ) : (
                <>
                  <Calculator className="h-4 w-4 mr-2" />
                  Run Valuation
                </>
              )}
            </Button>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
                {error}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingDown className="h-5 w-5" />
              Valuation Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            {calculating ? (
              <div className="flex flex-col items-center justify-center h-64">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-amber-500 mb-4"></div>
                <p className="text-slate-500">Analyzing power plants...</p>
              </div>
            ) : results?.results?.length > 0 ? (
              <div className="space-y-6">
                {/* Summary */}
                <div className="p-4 bg-slate-50 dark:bg-slate-800 rounded-lg">
                  <p className="text-sm text-slate-500 mb-1">Scenario: {results.scenario_name}</p>
                  <div className="grid grid-cols-3 gap-4 mt-3">
                    <div>
                      <p className="text-xs text-slate-500">Plants Analyzed</p>
                      <p className="text-xl font-bold">{results.portfolio_summary?.total_plants_analyzed}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Total Capacity</p>
                      <p className="text-xl font-bold">{results.portfolio_summary?.total_capacity_mw?.toLocaleString()} MW</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Avg NPV Impact</p>
                      <p className={`text-xl font-bold ${
                        results.portfolio_summary?.avg_npv_impact_percent < 0 
                          ? 'text-red-600' 
                          : 'text-emerald-600'
                      }`}>
                        {results.portfolio_summary?.avg_npv_impact_percent?.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>

                {/* Individual Results */}
                <div className="space-y-4 max-h-[400px] overflow-y-auto">
                  {results.results.map((result) => {
                    const colors = TECHNOLOGY_COLORS[result.technology_type] || { bg: 'bg-slate-100', text: 'text-slate-700' };
                    return (
                      <div 
                        key={result.plant_id}
                        className="border rounded-lg p-4"
                        data-testid="valuation-result"
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div>
                            <h4 className="font-medium">{result.plant_name}</h4>
                            <p className="text-xs text-slate-500">
                              {result.capacity_mw} MW • {result.remaining_life_years}y remaining
                            </p>
                          </div>
                          <div className="flex items-center gap-2">
                            <Badge className={`${colors.bg} ${colors.text}`}>
                              {result.technology_type.replace('_', ' ')}
                            </Badge>
                            <Badge className={RISK_BADGE_COLORS[result.risk_category]}>
                              {result.risk_category}
                            </Badge>
                          </div>
                        </div>

                        {/* NPV Comparison */}
                        <div className="grid grid-cols-3 gap-2 mb-4">
                          <div className="bg-slate-50 dark:bg-slate-800 p-2 rounded text-center">
                            <p className="text-xs text-slate-500">Baseline NPV</p>
                            <p className="font-bold text-sm">{formatCurrency(result.baseline_npv_usd)}</p>
                          </div>
                          <div className="flex items-center justify-center">
                            <ArrowRight className={`h-5 w-5 ${
                              result.npv_impact_percent < 0 ? 'text-red-500' : 'text-emerald-500'
                            }`} />
                          </div>
                          <div className={`p-2 rounded text-center ${
                            result.npv_impact_percent < 0 
                              ? 'bg-red-50 dark:bg-red-900/20' 
                              : 'bg-emerald-50 dark:bg-emerald-900/20'
                          }`}>
                            <p className="text-xs text-slate-500">Scenario NPV</p>
                            <p className={`font-bold text-sm ${
                              result.npv_impact_percent < 0 ? 'text-red-600' : 'text-emerald-600'
                            }`}>
                              {formatCurrency(result.scenario_npv_usd)}
                            </p>
                          </div>
                        </div>

                        {/* Optimal Retirement */}
                        {result.optimal_retirement_year && (
                          <div className="flex items-center gap-2 p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg mb-4">
                            <Zap className="h-5 w-5 text-orange-500" />
                            <div className="flex-1">
                              <p className="text-xs text-slate-500">Optimal Retirement</p>
                              <p className="font-bold text-orange-600">{result.optimal_retirement_year}</p>
                            </div>
                          </div>
                        )}

                        {/* Repurposing Options */}
                        {result.repurposing_options?.length > 0 && (
                          <div className="mb-4">
                            <p className="text-xs font-medium text-slate-500 mb-2">Repurposing Options</p>
                            <div className="grid grid-cols-2 gap-2">
                              {result.repurposing_options.slice(0, 4).map((option, i) => (
                                <div 
                                  key={i}
                                  className="p-2 border rounded-lg text-xs"
                                >
                                  <div className="flex items-center gap-1 mb-1">
                                    <Wrench className="h-3 w-3" />
                                    <span className="font-medium capitalize">{option.option_type}</span>
                                  </div>
                                  <p className="text-slate-500">
                                    Cost: {formatCurrency(option.capital_cost_usd)}
                                  </p>
                                  <p className="text-slate-500">
                                    Feasibility: {(option.feasibility_score * 100).toFixed(0)}%
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Recommendation */}
                        <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                          <CheckCircle className="h-4 w-4 text-blue-500 mt-0.5" />
                          <p className="text-sm">{result.recommended_action}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                <Factory className="h-12 w-12 mb-4" />
                <p className="text-center">
                  Select power plants and a scenario to run valuation
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default PowerPlantValuationTool;
