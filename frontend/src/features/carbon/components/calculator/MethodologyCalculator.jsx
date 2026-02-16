/**
 * MethodologyCalculator Component
 * Interactive form for calculating carbon credits using different methodologies
 */

import React, { useState, useEffect } from 'react';
import { 
  Calculator, Leaf, Factory, Trees, Wheat, Building2, 
  Car, Home, Droplets, Mountain, ChevronDown, Info, RefreshCw,
  Save, Check, X
} from 'lucide-react';

import { Button } from '../../../../components/ui/button';
import { Input } from '../../../../components/ui/input';
import { Label } from '../../../../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../../components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../../components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../../../../components/ui/tabs';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../../../../components/ui/tooltip';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../../../components/ui/dialog';
import { Skeleton } from '../../../../components/ui/skeleton';
import { saveCalculationAsProject, fetchPortfolios } from '../../api/carbonApi';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Sector icons mapping
const SECTOR_ICONS = {
  ENERGY: Factory,
  WASTE: Droplets,
  FORESTRY: Trees,
  AGRICULTURE: Wheat,
  INDUSTRIAL: Factory,
  TRANSPORT: Car,
  BUILDINGS: Building2,
  HOUSEHOLD: Home,
  MINING: Mountain,
  BLUE_CARBON: Droplets,
};

// Default inputs for each methodology
const DEFAULT_INPUTS = {
  'ACM0002': {
    installed_capacity_mw: 150,
    capacity_factor: 0.28,
    grid_emission_factor: 0.45,
    operating_margin_weight: 0.75,
    build_margin_weight: 0.25,
    uncertainty_factor: 0.05
  },
  'ACM0001': {
    waste_quantity: 500000,
    methane_generation_potential: 100,
    capture_efficiency: 0.75,
    destruction_efficiency: 0.995,
    methane_gwp: 28,
    n2o_gwp: 265
  },
  'AR-ACM0003': {
    start_year: 2024,
    crediting_period_years: 30,
    risk_buffer_percentage: 0.20,
    species: [
      { name: 'Mahogany', area_hectares: 400, max_biomass_per_hectare: 300, growth_rate: 0.15 },
      { name: 'Teak', area_hectares: 350, max_biomass_per_hectare: 250, growth_rate: 0.20 }
    ]
  },
  'VM0048': {
    forest_area: 10000,
    baseline_deforestation_rate: 0.02,
    project_deforestation_rate: 0.005,
    carbon_stock_per_hectare: 150,
    buffer_percentage: 0.25
  },
  'TPDDTEC': {
    stove_count: 10000,
    baseline_fuel_consumption: 2.5,
    project_fuel_consumption: 1.5,
    fuel_ncv: 15.0,
    fuel_emission_factor: 112.0
  },
  'AMS-II.D': {
    building_area: 10000,
    baseline_energy_intensity: 150,
    project_energy_intensity: 100,
    grid_emission_factor: 0.45
  },
  'VM0022': {
    crop_area: 5000,
    baseline_nitrogen: 150,
    project_nitrogen: 100,
    n2o_emission_factor: 0.01,
    n2o_gwp: 265
  },
  'VM0033': {
    area_hectares: 500,
    soil_carbon_density: 150,
    biomass_carbon_density: 20,
    risk_buffer: 0.25
  }
};

// Input field configurations for each methodology
const INPUT_CONFIGS = {
  'ACM0002': [
    { key: 'installed_capacity_mw', label: 'Installed Capacity', unit: 'MW', type: 'number', step: 1 },
    { key: 'capacity_factor', label: 'Capacity Factor', unit: '', type: 'number', step: 0.01, min: 0, max: 1 },
    { key: 'grid_emission_factor', label: 'Grid Emission Factor', unit: 'tCO2/MWh', type: 'number', step: 0.01 },
    { key: 'operating_margin_weight', label: 'Operating Margin Weight', unit: '', type: 'number', step: 0.05, min: 0, max: 1 },
    { key: 'build_margin_weight', label: 'Build Margin Weight', unit: '', type: 'number', step: 0.05, min: 0, max: 1 },
    { key: 'uncertainty_factor', label: 'Uncertainty Factor', unit: '', type: 'number', step: 0.01, min: 0, max: 0.2 },
  ],
  'ACM0001': [
    { key: 'waste_quantity', label: 'Annual Waste Quantity', unit: 'tonnes', type: 'number', step: 1000 },
    { key: 'methane_generation_potential', label: 'Methane Generation Potential', unit: 'm³ CH4/tonne', type: 'number', step: 5 },
    { key: 'capture_efficiency', label: 'Capture Efficiency', unit: '', type: 'number', step: 0.05, min: 0, max: 1 },
    { key: 'destruction_efficiency', label: 'Destruction Efficiency', unit: '', type: 'number', step: 0.005, min: 0, max: 1 },
  ],
  'AR-ACM0003': [
    { key: 'start_year', label: 'Start Year', unit: '', type: 'number', step: 1 },
    { key: 'crediting_period_years', label: 'Crediting Period', unit: 'years', type: 'number', step: 1, min: 1, max: 60 },
    { key: 'risk_buffer_percentage', label: 'Risk Buffer', unit: '%', type: 'number', step: 0.05, min: 0, max: 0.5 },
  ],
  'VM0048': [
    { key: 'forest_area', label: 'Forest Area', unit: 'hectares', type: 'number', step: 100 },
    { key: 'baseline_deforestation_rate', label: 'Baseline Deforestation Rate', unit: '%/year', type: 'number', step: 0.005, min: 0, max: 0.1 },
    { key: 'project_deforestation_rate', label: 'Project Deforestation Rate', unit: '%/year', type: 'number', step: 0.001, min: 0, max: 0.1 },
    { key: 'carbon_stock_per_hectare', label: 'Carbon Stock', unit: 'tC/ha', type: 'number', step: 10 },
    { key: 'buffer_percentage', label: 'Buffer Percentage', unit: '%', type: 'number', step: 0.05, min: 0, max: 0.5 },
  ],
  'TPDDTEC': [
    { key: 'stove_count', label: 'Number of Cookstoves', unit: '', type: 'number', step: 100 },
    { key: 'baseline_fuel_consumption', label: 'Baseline Fuel Consumption', unit: 'tonnes/stove/year', type: 'number', step: 0.1 },
    { key: 'project_fuel_consumption', label: 'Project Fuel Consumption', unit: 'tonnes/stove/year', type: 'number', step: 0.1 },
    { key: 'fuel_ncv', label: 'Fuel NCV', unit: 'GJ/tonne', type: 'number', step: 0.5 },
    { key: 'fuel_emission_factor', label: 'Fuel Emission Factor', unit: 'kgCO2/GJ', type: 'number', step: 1 },
  ],
  'AMS-II.D': [
    { key: 'building_area', label: 'Building Area', unit: 'm²', type: 'number', step: 100 },
    { key: 'baseline_energy_intensity', label: 'Baseline Energy Intensity', unit: 'kWh/m²/year', type: 'number', step: 5 },
    { key: 'project_energy_intensity', label: 'Project Energy Intensity', unit: 'kWh/m²/year', type: 'number', step: 5 },
    { key: 'grid_emission_factor', label: 'Grid Emission Factor', unit: 'tCO2/MWh', type: 'number', step: 0.01 },
  ],
  'VM0022': [
    { key: 'crop_area', label: 'Crop Area', unit: 'hectares', type: 'number', step: 100 },
    { key: 'baseline_nitrogen', label: 'Baseline Nitrogen Application', unit: 'kg N/ha', type: 'number', step: 5 },
    { key: 'project_nitrogen', label: 'Project Nitrogen Application', unit: 'kg N/ha', type: 'number', step: 5 },
    { key: 'n2o_emission_factor', label: 'N2O Emission Factor', unit: '', type: 'number', step: 0.001 },
  ],
  'VM0033': [
    { key: 'area_hectares', label: 'Restoration Area', unit: 'hectares', type: 'number', step: 50 },
    { key: 'soil_carbon_density', label: 'Soil Carbon Density', unit: 'tC/ha', type: 'number', step: 10 },
    { key: 'biomass_carbon_density', label: 'Biomass Carbon Density', unit: 'tC/ha', type: 'number', step: 5 },
    { key: 'risk_buffer', label: 'Risk Buffer', unit: '%', type: 'number', step: 0.05, min: 0, max: 0.5 },
  ],
};

export default function MethodologyCalculator() {
  const [sectors, setSectors] = useState([]);
  const [methodologies, setMethodologies] = useState([]);
  const [selectedSector, setSelectedSector] = useState('ENERGY');
  const [selectedMethodology, setSelectedMethodology] = useState('');
  const [inputs, setInputs] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingMethodologies, setLoadingMethodologies] = useState(false);
  
  // Save as project state
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [portfolios, setPortfolios] = useState([]);
  const [loadingPortfolios, setLoadingPortfolios] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(null);
  const [saveFormData, setSaveFormData] = useState({
    portfolio_id: '',
    project_name: '',
    country_code: 'US'
  });

  // Fetch all methodologies on mount
  useEffect(() => {
    fetchMethodologiesBySector(selectedSector);
  }, [selectedSector]);
  
  // Fetch portfolios when save dialog opens
  useEffect(() => {
    if (showSaveDialog && portfolios.length === 0) {
      loadPortfolios();
    }
  }, [showSaveDialog]);
  
  const loadPortfolios = async () => {
    setLoadingPortfolios(true);
    try {
      const data = await fetchPortfolios();
      setPortfolios(data || []);
      if (data?.length > 0) {
        setSaveFormData(prev => ({ ...prev, portfolio_id: data[0].id }));
      }
    } catch (error) {
      console.error('Failed to fetch portfolios:', error);
    }
    setLoadingPortfolios(false);
  };

  const fetchMethodologiesBySector = async (sector) => {
    setLoadingMethodologies(true);
    try {
      const response = await fetch(`${API_URL}/api/v1/carbon/methodology-list/${sector}`);
      const data = await response.json();
      setMethodologies(data.methodologies || []);
      if (data.methodologies?.length > 0) {
        const firstMethod = data.methodologies[0].code;
        setSelectedMethodology(firstMethod);
        setInputs(DEFAULT_INPUTS[firstMethod] || {});
      }
    } catch (error) {
      console.error('Failed to fetch methodologies:', error);
    }
    setLoadingMethodologies(false);
  };

  const handleMethodologyChange = (code) => {
    setSelectedMethodology(code);
    setInputs(DEFAULT_INPUTS[code] || {});
    setResult(null);
  };

  const handleInputChange = (key, value) => {
    setInputs(prev => ({
      ...prev,
      [key]: parseFloat(value) || value
    }));
  };

  const handleCalculate = async () => {
    if (!selectedMethodology) return;
    
    setLoading(true);
    setSaveSuccess(false);
    setSaveError(null);
    try {
      const response = await fetch(
        `${API_URL}/api/v1/carbon/calculate/methodology?methodology_code=${selectedMethodology}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(inputs)
        }
      );
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Calculation failed:', error);
      setResult({ error: 'Calculation failed. Please try again.' });
    }
    setLoading(false);
  };

  const handleSaveAsProject = async () => {
    if (!result || !saveFormData.portfolio_id || !saveFormData.project_name.trim()) {
      setSaveError('Please fill in all required fields');
      return;
    }
    
    setSaving(true);
    setSaveError(null);
    
    try {
      await saveCalculationAsProject({
        portfolio_id: saveFormData.portfolio_id,
        project_name: saveFormData.project_name,
        methodology_code: selectedMethodology,
        annual_credits: result.emission_reductions,
        country_code: saveFormData.country_code,
        calculation_inputs: inputs,
        calculation_result: result
      });
      
      setSaveSuccess(true);
      setTimeout(() => {
        setShowSaveDialog(false);
        setSaveSuccess(false);
        setSaveFormData({ portfolio_id: portfolios[0]?.id || '', project_name: '', country_code: 'US' });
      }, 1500);
    } catch (error) {
      console.error('Failed to save project:', error);
      setSaveError(error.response?.data?.detail || 'Failed to save project. Please try again.');
    }
    setSaving(false);
  };

  const openSaveDialog = () => {
    // Pre-populate project name with methodology name
    const methodologyName = methodologies.find(m => m.code === selectedMethodology)?.name || selectedMethodology;
    setSaveFormData(prev => ({
      ...prev,
      project_name: `${methodologyName} Project`,
      portfolio_id: portfolios[0]?.id || prev.portfolio_id
    }));
    setShowSaveDialog(true);
    setSaveSuccess(false);
    setSaveError(null);
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString();
  };

  const SectorIcon = SECTOR_ICONS[selectedSector] || Factory;

  return (
    <div className="space-y-6" data-testid="methodology-calculator">
      <Card className="bg-white border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="w-5 h-5 text-emerald-600" />
            Methodology Calculator
          </CardTitle>
          <CardDescription>
            Calculate carbon credits using 40+ certified methodologies (CDM, VCS, Gold Standard, CAR, ACR, GCC)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Sector Selection Tabs */}
          <Tabs value={selectedSector} onValueChange={setSelectedSector} className="w-full">
            <TabsList className="grid grid-cols-5 lg:grid-cols-10 gap-1 h-auto mb-6">
              {['ENERGY', 'FORESTRY', 'WASTE', 'AGRICULTURE', 'INDUSTRIAL', 'TRANSPORT', 'BUILDINGS', 'HOUSEHOLD', 'MINING', 'BLUE_CARBON'].map((sector) => {
                const Icon = SECTOR_ICONS[sector] || Factory;
                return (
                  <TabsTrigger 
                    key={sector} 
                    value={sector}
                    className="flex flex-col items-center gap-1 py-2 px-2 text-xs"
                    data-testid={`sector-tab-${sector.toLowerCase()}`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="hidden md:inline">{sector.replace('_', ' ')}</span>
                  </TabsTrigger>
                );
              })}
            </TabsList>

            {/* Methodology Selection */}
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <Label>Select Methodology</Label>
                  <Select 
                    value={selectedMethodology} 
                    onValueChange={handleMethodologyChange}
                    disabled={loadingMethodologies}
                  >
                    <SelectTrigger className="mt-1" data-testid="methodology-select">
                      <SelectValue placeholder="Select a methodology" />
                    </SelectTrigger>
                    <SelectContent>
                      {methodologies.map((m) => (
                        <SelectItem key={m.code} value={m.code}>
                          <span className="font-medium">{m.code}</span>
                          <span className="text-slate-500 ml-2">- {m.name}</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2 mt-6">
                  <span className="px-2 py-1 bg-slate-100 text-slate-600 text-xs rounded">
                    {methodologies.find(m => m.code === selectedMethodology)?.standard || '-'}
                  </span>
                  <span className="px-2 py-1 bg-emerald-100 text-emerald-600 text-xs rounded">
                    {methodologies.find(m => m.code === selectedMethodology)?.scale || 'Large'}
                  </span>
                </div>
              </div>

              {/* Input Fields */}
              {selectedMethodology && INPUT_CONFIGS[selectedMethodology] && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
                  {INPUT_CONFIGS[selectedMethodology].map((config) => (
                    <div key={config.key} className="space-y-1">
                      <Label className="flex items-center gap-1 text-sm">
                        {config.label}
                        {config.unit && (
                          <span className="text-slate-400 text-xs">({config.unit})</span>
                        )}
                      </Label>
                      <Input
                        type={config.type}
                        step={config.step}
                        min={config.min}
                        max={config.max}
                        value={inputs[config.key] ?? ''}
                        onChange={(e) => handleInputChange(config.key, e.target.value)}
                        className="text-sm"
                        data-testid={`input-${config.key}`}
                      />
                    </div>
                  ))}
                </div>
              )}

              {/* Generic inputs for methodologies without specific configs */}
              {selectedMethodology && !INPUT_CONFIGS[selectedMethodology] && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                  <p className="text-amber-700 text-sm">
                    This methodology uses default inputs. Click calculate to see the result.
                  </p>
                </div>
              )}

              {/* Calculate Button */}
              <div className="flex items-center gap-4 mt-6">
                <Button 
                  onClick={handleCalculate}
                  disabled={loading || !selectedMethodology}
                  className="bg-emerald-600 hover:bg-emerald-700"
                  data-testid="calculate-btn"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Calculating...
                    </>
                  ) : (
                    <>
                      <Calculator className="w-4 h-4 mr-2" />
                      Calculate Credits
                    </>
                  )}
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => setInputs(DEFAULT_INPUTS[selectedMethodology] || {})}
                  disabled={!selectedMethodology}
                >
                  Reset to Defaults
                </Button>
              </div>
            </div>
          </Tabs>
        </CardContent>
      </Card>

      {/* Results Card */}
      {result && (
        <Card className="bg-white border-slate-200" data-testid="calculation-result">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-emerald-700">
                  <Leaf className="w-5 h-5" />
                  Calculation Results
                </CardTitle>
                <CardDescription>
                  {result.methodology} v{result.version} - {result.sector || selectedSector}
                </CardDescription>
              </div>
              {!result.error && (
                <Button
                  onClick={openSaveDialog}
                  className="bg-blue-600 hover:bg-blue-700"
                  data-testid="save-as-project-btn"
                >
                  <Save className="w-4 h-4 mr-2" />
                  Save as Project
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {result.error ? (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-700">{result.error}</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Main Result */}
                <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
                  <p className="text-sm text-emerald-600 mb-1">Annual Emission Reductions</p>
                  <p className="text-4xl font-bold text-emerald-700">
                    {formatNumber(result.emission_reductions)}
                  </p>
                  <p className="text-sm text-emerald-600 mt-1">{result.unit}</p>
                </div>

                {/* Detailed Breakdown */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {result.baseline_emissions !== undefined && (
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500">Baseline Emissions</p>
                      <p className="text-lg font-semibold text-slate-700">
                        {formatNumber(result.baseline_emissions)}
                      </p>
                      <p className="text-xs text-slate-400">{result.unit}</p>
                    </div>
                  )}
                  {result.project_emissions !== undefined && (
                    <div className="p-4 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500">Project Emissions</p>
                      <p className="text-lg font-semibold text-slate-700">
                        {formatNumber(result.project_emissions)}
                      </p>
                      <p className="text-xs text-slate-400">{result.unit}</p>
                    </div>
                  )}
                  {result.annual_generation_mwh !== undefined && (
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <p className="text-xs text-blue-500">Annual Generation</p>
                      <p className="text-lg font-semibold text-blue-700">
                        {formatNumber(result.annual_generation_mwh)}
                      </p>
                      <p className="text-xs text-blue-400">MWh</p>
                    </div>
                  )}
                  {result.total_credits !== undefined && (
                    <div className="p-4 bg-amber-50 rounded-lg">
                      <p className="text-xs text-amber-500">Total Credits (Lifetime)</p>
                      <p className="text-lg font-semibold text-amber-700">
                        {formatNumber(result.total_credits)}
                      </p>
                      <p className="text-xs text-amber-400">{result.unit}</p>
                    </div>
                  )}
                  {result.annual_credits_per_stove !== undefined && (
                    <div className="p-4 bg-purple-50 rounded-lg">
                      <p className="text-xs text-purple-500">Credits per Stove</p>
                      <p className="text-lg font-semibold text-purple-700">
                        {formatNumber(result.annual_credits_per_stove)}
                      </p>
                      <p className="text-xs text-purple-400">{result.unit}/stove</p>
                    </div>
                  )}
                </div>

                {/* Yearly Results for Forestry */}
                {result.yearly_results && result.yearly_results.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-700 mb-3">Yearly Projections</h4>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-slate-50">
                            <th className="px-3 py-2 text-left text-slate-600">Year</th>
                            <th className="px-3 py-2 text-right text-slate-600">CO2 Sequestered</th>
                            <th className="px-3 py-2 text-right text-slate-600">Risk Buffer</th>
                            <th className="px-3 py-2 text-right text-slate-600">Net Credits</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.yearly_results.slice(0, 10).map((yr, idx) => (
                            <tr key={idx} className="border-b border-slate-100">
                              <td className="px-3 py-2">{yr.year}</td>
                              <td className="px-3 py-2 text-right">{formatNumber(yr.co2_sequestered)}</td>
                              <td className="px-3 py-2 text-right text-red-600">-{formatNumber(yr.risk_buffer)}</td>
                              <td className="px-3 py-2 text-right font-medium text-emerald-600">{formatNumber(yr.net_credits)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {result.yearly_results.length > 10 && (
                        <p className="text-xs text-slate-400 mt-2">
                          Showing first 10 of {result.yearly_results.length} years
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Save as Project Dialog */}
      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Save Calculation as Project</DialogTitle>
            <DialogDescription>
              Add this calculation result to your carbon credits portfolio as a new project.
            </DialogDescription>
          </DialogHeader>
          
          {saveSuccess ? (
            <div className="py-8 text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Check className="w-8 h-8 text-emerald-600" />
              </div>
              <p className="text-lg font-semibold text-slate-900">Project Saved!</p>
              <p className="text-sm text-slate-500 mt-1">
                Your calculation has been added to the portfolio.
              </p>
            </div>
          ) : (
            <>
              <div className="space-y-4 py-4">
                {/* Portfolio Selection */}
                <div className="space-y-2">
                  <Label htmlFor="portfolio">Portfolio *</Label>
                  {loadingPortfolios ? (
                    <Skeleton className="h-10 w-full" />
                  ) : portfolios.length === 0 ? (
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                      <p className="text-sm text-amber-700">
                        No portfolios found. Please create a portfolio first.
                      </p>
                    </div>
                  ) : (
                    <Select
                      value={saveFormData.portfolio_id}
                      onValueChange={(v) => setSaveFormData(prev => ({ ...prev, portfolio_id: v }))}
                    >
                      <SelectTrigger data-testid="save-portfolio-select">
                        <SelectValue placeholder="Select portfolio" />
                      </SelectTrigger>
                      <SelectContent>
                        {portfolios.map((p) => (
                          <SelectItem key={p.id} value={p.id}>
                            {p.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>

                {/* Project Name */}
                <div className="space-y-2">
                  <Label htmlFor="project-name">Project Name *</Label>
                  <Input
                    id="project-name"
                    value={saveFormData.project_name}
                    onChange={(e) => setSaveFormData(prev => ({ ...prev, project_name: e.target.value }))}
                    placeholder="e.g., Solar Farm Brazil"
                    data-testid="save-project-name-input"
                  />
                </div>

                {/* Country */}
                <div className="space-y-2">
                  <Label htmlFor="country">Country</Label>
                  <Select
                    value={saveFormData.country_code}
                    onValueChange={(v) => setSaveFormData(prev => ({ ...prev, country_code: v }))}
                  >
                    <SelectTrigger data-testid="save-country-select">
                      <SelectValue placeholder="Select country" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="US">United States</SelectItem>
                      <SelectItem value="BR">Brazil</SelectItem>
                      <SelectItem value="IN">India</SelectItem>
                      <SelectItem value="CN">China</SelectItem>
                      <SelectItem value="ID">Indonesia</SelectItem>
                      <SelectItem value="KE">Kenya</SelectItem>
                      <SelectItem value="DE">Germany</SelectItem>
                      <SelectItem value="AU">Australia</SelectItem>
                      <SelectItem value="GB">United Kingdom</SelectItem>
                      <SelectItem value="FR">France</SelectItem>
                      <SelectItem value="JP">Japan</SelectItem>
                      <SelectItem value="MX">Mexico</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Calculation Summary */}
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs text-slate-500 mb-1">Calculation Summary</p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-slate-700">{selectedMethodology}</span>
                    <span className="text-sm font-bold text-emerald-600">
                      {formatNumber(result?.emission_reductions)} tCO2e/year
                    </span>
                  </div>
                </div>

                {/* Error Message */}
                {saveError && (
                  <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                    <X className="w-4 h-4 text-red-500" />
                    <p className="text-sm text-red-700">{saveError}</p>
                  </div>
                )}
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={() => setShowSaveDialog(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveAsProject}
                  disabled={saving || !saveFormData.portfolio_id || !saveFormData.project_name.trim()}
                  className="bg-emerald-600 hover:bg-emerald-700"
                  data-testid="save-project-submit-btn"
                >
                  {saving ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4 mr-2" />
                      Save Project
                    </>
                  )}
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
