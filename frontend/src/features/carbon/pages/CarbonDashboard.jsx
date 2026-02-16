/**
 * CarbonDashboard Page
 * Main dashboard for carbon credits management
 */

import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Leaf, TrendingUp, Shield, DollarSign, 
  Plus, RefreshCw, FileText, Settings,
  ChevronDown, Calculator
} from 'lucide-react';

import { Button } from '../../../components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../../components/ui/dialog';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Skeleton } from '../../../components/ui/skeleton';

import { MetricCard } from '../components/dashboard/MetricCard';
import { CreditsChart } from '../components/dashboard/CreditsChart';
import { RiskHeatMap } from '../components/dashboard/RiskHeatMap';
import { ProjectTable } from '../components/dashboard/ProjectTable';
import { GeographicMap } from '../components/dashboard/GeographicMap';
import { ScenarioTabs } from '../components/scenarios/ScenarioTabs';
import { RiskSliders } from '../components/scenarios/RiskSliders';
import MethodologyCalculator from '../components/calculator/MethodologyCalculator';
import { ExportButton } from '../../../components/shared/ExportButton';
import { exportCarbonCalculation } from '../../../lib/exportUtils';

import { 
  useCarbonPortfolios, 
  useCarbonPortfolioDashboard,
  useCarbonScenarios,
  useCreateCarbonPortfolio,
  useCreateCarbonProject,
  useCalculateCarbonCredits
} from '../api/queries';

import {
  loadPortfolioDashboard,
  setActiveScenario,
  setScenarios
} from '../store/carbonSlice';

import {
  selectPortfolioDashboard,
  selectDashboardLoading,
  selectScenarios,
  selectActiveScenarioId
} from '../store/selectors';

export default function CarbonDashboard() {
  const dispatch = useDispatch();
  
  // Local state
  const [selectedPortfolioId, setSelectedPortfolioId] = useState(null);
  const [showNewPortfolio, setShowNewPortfolio] = useState(false);
  const [showNewProject, setShowNewProject] = useState(false);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [newProject, setNewProject] = useState({
    name: '',
    project_type: 'RENEWABLE_ENERGY',
    standard: 'VCS',
    country_code: 'US',
    annual_credits: 10000
  });
  const [scenarioParams, setScenarioParams] = useState({
    permanence_risk_pct: 10,
    delivery_risk_pct: 5,
    regulatory_risk_pct: 5,
    market_risk_pct: 10,
    base_carbon_price_usd: 15,
    price_growth_rate_pct: 5,
    discount_rate_pct: 8
  });

  // Queries
  const { data: portfolios = [], isLoading: portfoliosLoading } = useCarbonPortfolios();
  const { data: dashboard, isLoading: dashboardLoading, refetch: refetchDashboard } = 
    useCarbonPortfolioDashboard(selectedPortfolioId);
  const { data: scenarios = [] } = useCarbonScenarios(selectedPortfolioId);
  
  // Mutations
  const createPortfolio = useCreateCarbonPortfolio();
  const createProject = useCreateCarbonProject();
  const calculate = useCalculateCarbonCredits();

  // Redux state
  const activeScenarioId = useSelector(selectActiveScenarioId);

  // Set first portfolio as selected
  useEffect(() => {
    if (portfolios.length > 0 && !selectedPortfolioId) {
      setSelectedPortfolioId(portfolios[0].id);
    }
  }, [portfolios, selectedPortfolioId]);

  // Set scenarios in store
  useEffect(() => {
    if (scenarios.length > 0) {
      dispatch(setScenarios(scenarios));
      if (!activeScenarioId) {
        dispatch(setActiveScenario(scenarios[0].id));
      }
    }
  }, [scenarios, dispatch, activeScenarioId]);

  // Handle portfolio creation
  const handleCreatePortfolio = async () => {
    if (!newPortfolioName.trim()) return;
    
    try {
      const result = await createPortfolio.mutateAsync({
        name: newPortfolioName,
        description: ''
      });
      setSelectedPortfolioId(result.id);
      setShowNewPortfolio(false);
      setNewPortfolioName('');
    } catch (error) {
      console.error('Failed to create portfolio:', error);
    }
  };

  // Handle project creation
  const handleCreateProject = async () => {
    if (!newProject.name.trim() || !selectedPortfolioId) return;
    
    try {
      await createProject.mutateAsync({
        ...newProject,
        portfolio_id: selectedPortfolioId
      });
      setShowNewProject(false);
      setNewProject({
        name: '',
        project_type: 'RENEWABLE_ENERGY',
        standard: 'VCS',
        country_code: 'US',
        annual_credits: 10000
      });
      refetchDashboard();
    } catch (error) {
      console.error('Failed to create project:', error);
    }
  };

  // Handle calculation
  const handleRunCalculation = async () => {
    if (!selectedPortfolioId) return;
    
    try {
      await calculate.mutateAsync({
        portfolio_id: selectedPortfolioId,
        scenario_id: activeScenarioId,
        calculation_type: 'standard'
      });
      refetchDashboard();
    } catch (error) {
      console.error('Calculation failed:', error);
    }
  };

  // Format numbers
  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
    return num.toLocaleString();
  };

  const formatCurrency = (num) => {
    if (!num) return '$0';
    if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `$${(num / 1000).toFixed(0)}k`;
    return `$${num.toLocaleString()}`;
  };
  
  // Handle export
  const handleExport = async (format) => {
    const selectedPortfolio = portfolios.find(p => p.id === selectedPortfolioId);
    await exportCarbonCalculation({
      portfolio_name: selectedPortfolio?.name || 'Unknown Portfolio',
      total_credits: dashboard?.total_credits || 0,
      portfolio_value_usd: dashboard?.portfolio_value_usd || 0,
      at_risk_credits: dashboard?.at_risk_credits || 0,
      net_expected_value_usd: dashboard?.net_expected_value_usd || 0,
      credits_by_type: dashboard?.credits_by_type || {},
      projects: dashboard?.projects || [],
    }, format);
  };

  return (
    <div className="p-6 space-y-6" data-testid="carbon-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Carbon Credits</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage your carbon credit portfolio and track performance
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Portfolio Selector */}
          <Select 
            value={selectedPortfolioId || ''} 
            onValueChange={setSelectedPortfolioId}
          >
            <SelectTrigger className="w-[220px]" data-testid="portfolio-selector">
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
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowNewPortfolio(true)}
            data-testid="new-portfolio-btn"
          >
            <Plus className="w-4 h-4 mr-1" />
            New Portfolio
          </Button>
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => refetchDashboard()}
            disabled={dashboardLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${dashboardLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          
          <Button 
            size="sm"
            onClick={handleRunCalculation}
            disabled={!selectedPortfolioId || calculate.isPending}
            data-testid="run-calculation-btn"
          >
            {calculate.isPending ? 'Calculating...' : 'Run Calculation'}
          </Button>
        </div>
      </div>

      {/* Loading State */}
      {(portfoliosLoading || dashboardLoading) && !dashboard && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      )}

      {/* No Portfolio Selected */}
      {!selectedPortfolioId && !portfoliosLoading && (
        <div className="text-center py-16 bg-white rounded-xl border border-slate-200">
          <Leaf className="w-12 h-12 mx-auto text-slate-300 mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">
            No Portfolio Selected
          </h3>
          <p className="text-sm text-slate-500 mb-4">
            Create or select a portfolio to view your carbon credits dashboard
          </p>
          <Button onClick={() => setShowNewPortfolio(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Portfolio
          </Button>
        </div>
      )}

      {/* Dashboard Content */}
      {selectedPortfolioId && dashboard && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Total Annual Credits"
              value={formatNumber(dashboard.summary?.total_annual_credits)}
              unit="tCO2e"
              trend="up"
              trendValue="+12%"
              icon={Leaf}
            />
            <MetricCard
              title="Risk-Adjusted Credits"
              value={formatNumber(dashboard.summary?.total_risk_adjusted_credits)}
              unit="tCO2e"
              trend="neutral"
              icon={Shield}
            />
            <MetricCard
              title="Quality Score"
              value={dashboard.summary?.portfolio_quality_score?.toFixed(1) || '0'}
              unit={`/ 5 (${dashboard.summary?.portfolio_quality_rating || 'N/A'})`}
              trend="up"
              trendValue="+0.3"
              icon={TrendingUp}
            />
            <MetricCard
              title="10-Year NPV"
              value={formatCurrency(dashboard.summary?.portfolio_npv_10yr_usd)}
              trend="up"
              trendValue="+8%"
              icon={DollarSign}
            />
          </div>

          {/* Main Content Tabs */}
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="calculator" data-testid="calculator-tab">
                <Calculator className="w-4 h-4 mr-1" />
                Calculator
              </TabsTrigger>
              <TabsTrigger value="projects">Projects</TabsTrigger>
              <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
              <TabsTrigger value="map">Map</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-6">
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Credits Chart */}
                <div className="lg:col-span-2">
                  <CreditsChart 
                    data={dashboard.yearly_projections || []} 
                    height={350}
                  />
                </div>
                
                {/* Risk Heat Map */}
                <div>
                  <RiskHeatMap risks={dashboard.risk_heat_map || []} />
                </div>
              </div>

              {/* Project Summary Table */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-slate-900">Projects</h3>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={() => setShowNewProject(true)}
                    data-testid="add-project-btn"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Add Project
                  </Button>
                </div>
                <ProjectTable 
                  projects={dashboard.projects || []}
                  onView={(p) => console.log('View project:', p)}
                  onEdit={(p) => console.log('Edit project:', p)}
                  onDelete={(p) => console.log('Delete project:', p)}
                />
              </div>
            </TabsContent>

            {/* Calculator Tab */}
            <TabsContent value="calculator" className="space-y-6">
              <MethodologyCalculator />
            </TabsContent>

            {/* Projects Tab */}
            <TabsContent value="projects" className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">All Projects</h3>
                <Button onClick={() => setShowNewProject(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Project
                </Button>
              </div>
              <ProjectTable 
                projects={dashboard.projects || []}
                onView={(p) => console.log('View project:', p)}
                onEdit={(p) => console.log('Edit project:', p)}
                onDelete={(p) => console.log('Delete project:', p)}
              />
            </TabsContent>

            {/* Scenarios Tab */}
            <TabsContent value="scenarios" className="space-y-6">
              <ScenarioTabs
                scenarios={scenarios}
                activeScenarioId={activeScenarioId}
                onSelect={(id) => dispatch(setActiveScenario(id))}
                onCreate={() => console.log('Create scenario')}
                onDuplicate={(id) => console.log('Duplicate scenario:', id)}
                onDelete={(id) => console.log('Delete scenario:', id)}
              />
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <RiskSliders
                  values={scenarioParams}
                  onChange={setScenarioParams}
                />
                
                <div className="space-y-6">
                  <CreditsChart 
                    data={dashboard.yearly_projections || []} 
                    height={300}
                    title="Scenario Projections"
                  />
                </div>
              </div>
            </TabsContent>

            {/* Map Tab */}
            <TabsContent value="map" className="space-y-6">
              <GeographicMap
                projects={dashboard.projects || []}
                geoDistribution={dashboard.geographic_distribution || []}
                height={500}
                onProjectClick={(p) => console.log('Clicked project:', p)}
              />
            </TabsContent>
          </Tabs>
        </>
      )}

      {/* New Portfolio Dialog */}
      <Dialog open={showNewPortfolio} onOpenChange={setShowNewPortfolio}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Portfolio</DialogTitle>
            <DialogDescription>
              Create a new carbon credits portfolio to manage your projects.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="portfolio-name">Portfolio Name</Label>
              <Input
                id="portfolio-name"
                value={newPortfolioName}
                onChange={(e) => setNewPortfolioName(e.target.value)}
                placeholder="e.g., European Renewables"
                data-testid="portfolio-name-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewPortfolio(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreatePortfolio}
              disabled={!newPortfolioName.trim() || createPortfolio.isPending}
              data-testid="create-portfolio-submit"
            >
              {createPortfolio.isPending ? 'Creating...' : 'Create Portfolio'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* New Project Dialog */}
      <Dialog open={showNewProject} onOpenChange={setShowNewProject}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add New Project</DialogTitle>
            <DialogDescription>
              Add a carbon credit project to your portfolio.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="project-name">Project Name</Label>
              <Input
                id="project-name"
                value={newProject.name}
                onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                placeholder="e.g., Solar Farm A"
                data-testid="project-name-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Project Type</Label>
                <Select 
                  value={newProject.project_type}
                  onValueChange={(v) => setNewProject({ ...newProject, project_type: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="RENEWABLE_ENERGY">Renewable Energy</SelectItem>
                    <SelectItem value="FOREST_CONSERVATION">Forest Conservation</SelectItem>
                    <SelectItem value="AFFORESTATION">Afforestation</SelectItem>
                    <SelectItem value="METHANE_CAPTURE">Methane Capture</SelectItem>
                    <SelectItem value="COOKSTOVES">Cookstoves</SelectItem>
                    <SelectItem value="BLUE_CARBON">Blue Carbon</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Standard</Label>
                <Select 
                  value={newProject.standard}
                  onValueChange={(v) => setNewProject({ ...newProject, standard: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="VCS">VCS</SelectItem>
                    <SelectItem value="GOLD_STANDARD">Gold Standard</SelectItem>
                    <SelectItem value="ACR">ACR</SelectItem>
                    <SelectItem value="CAR">CAR</SelectItem>
                    <SelectItem value="CDM">CDM</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Country</Label>
                <Select 
                  value={newProject.country_code}
                  onValueChange={(v) => setNewProject({ ...newProject, country_code: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
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
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="annual-credits">Annual Credits (tCO2e)</Label>
                <Input
                  id="annual-credits"
                  type="number"
                  value={newProject.annual_credits}
                  onChange={(e) => setNewProject({ ...newProject, annual_credits: parseInt(e.target.value) || 0 })}
                  data-testid="annual-credits-input"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewProject(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateProject}
              disabled={!newProject.name.trim() || createProject.isPending}
              data-testid="create-project-submit"
            >
              {createProject.isPending ? 'Adding...' : 'Add Project'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
