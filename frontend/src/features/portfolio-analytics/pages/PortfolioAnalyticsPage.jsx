/**
 * Portfolio Analytics Page
 * Main page with tabs for dashboard, holdings, reports, and scenario comparison
 */
import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Badge } from '../../../components/ui/badge';
import {
  LayoutDashboard, Building2, FileText, GitCompare, PieChart, Briefcase
} from 'lucide-react';

import { PortfolioSelector } from '../components/PortfolioSelector';
import { PortfolioDashboard } from '../components/PortfolioDashboard';
import { HoldingsTable } from '../components/HoldingsTable';
import { ReportGenerator } from '../components/ReportGenerator';
import { ScenarioComparison } from '../components/ScenarioComparison';
import { 
  usePortfolios, 
  useDashboard, 
  useHoldings 
} from '../hooks/usePortfolioAnalytics';

export default function PortfolioAnalyticsPage() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedPortfolioId, setSelectedPortfolioId] = useState(null);
  
  // Fetch portfolios
  const { data: portfolios, isLoading: portfoliosLoading } = usePortfolios();
  
  // Fetch dashboard data for selected portfolio
  const { data: dashboard, isLoading: dashboardLoading } = useDashboard(selectedPortfolioId);
  
  // Fetch holdings for selected portfolio
  const { data: holdings, isLoading: holdingsLoading } = useHoldings(selectedPortfolioId);
  
  // Auto-select first portfolio if none selected
  React.useEffect(() => {
    if (portfolios?.items?.length > 0 && !selectedPortfolioId) {
      setSelectedPortfolioId(portfolios.items[0].id);
    }
  }, [portfolios, selectedPortfolioId]);
  
  const selectedPortfolio = portfolios?.items?.find(p => p.id === selectedPortfolioId);
  
  return (
    <div className="min-h-screen bg-slate-50" data-testid="portfolio-analytics-page">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-100 rounded-lg">
            <PieChart className="h-6 w-6 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Portfolio Analytics</h1>
            <p className="text-sm text-slate-500">
              Consolidate property valuations into portfolio-level analytics and reports
            </p>
          </div>
        </div>
        
        {/* Feature Badges */}
        <div className="flex gap-2 mt-4">
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            <LayoutDashboard className="h-3 w-3 mr-1" />
            Executive Dashboard
          </Badge>
          <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
            <GitCompare className="h-3 w-3 mr-1" />
            Scenario Comparison
          </Badge>
          <Badge variant="outline" className="bg-violet-50 text-violet-700 border-violet-200">
            <FileText className="h-3 w-3 mr-1" />
            Multi-Format Reports
          </Badge>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - Portfolio Selector */}
          <div className="lg:col-span-1">
            <PortfolioSelector
              portfolios={portfolios}
              selectedId={selectedPortfolioId}
              onSelect={setSelectedPortfolioId}
              isLoading={portfoliosLoading}
            />
          </div>
          
          {/* Main Content Area */}
          <div className="lg:col-span-3">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-4 mb-6 bg-white border border-slate-200">
                <TabsTrigger
                  value="dashboard"
                  className="flex items-center gap-2 data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700"
                  data-testid="tab-dashboard"
                >
                  <LayoutDashboard className="h-4 w-4" />
                  <span className="hidden md:inline">Dashboard</span>
                </TabsTrigger>
                <TabsTrigger
                  value="holdings"
                  className="flex items-center gap-2 data-[state=active]:bg-blue-50 data-[state=active]:text-blue-700"
                  data-testid="tab-holdings"
                >
                  <Building2 className="h-4 w-4" />
                  <span className="hidden md:inline">Holdings</span>
                </TabsTrigger>
                <TabsTrigger
                  value="scenarios"
                  className="flex items-center gap-2 data-[state=active]:bg-violet-50 data-[state=active]:text-violet-700"
                  data-testid="tab-scenarios"
                >
                  <GitCompare className="h-4 w-4" />
                  <span className="hidden md:inline">Scenarios</span>
                </TabsTrigger>
                <TabsTrigger
                  value="reports"
                  className="flex items-center gap-2 data-[state=active]:bg-emerald-50 data-[state=active]:text-emerald-700"
                  data-testid="tab-reports"
                >
                  <FileText className="h-4 w-4" />
                  <span className="hidden md:inline">Reports</span>
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="dashboard" className="mt-0">
                <PortfolioDashboard 
                  dashboard={dashboard} 
                  isLoading={dashboardLoading && selectedPortfolioId} 
                />
              </TabsContent>
              
              <TabsContent value="holdings" className="mt-0">
                <HoldingsTable 
                  holdings={holdings} 
                  isLoading={holdingsLoading && selectedPortfolioId} 
                />
              </TabsContent>
              
              <TabsContent value="scenarios" className="mt-0">
                <ScenarioComparison portfolioId={selectedPortfolioId} />
              </TabsContent>
              
              <TabsContent value="reports" className="mt-0">
                <ReportGenerator 
                  portfolioId={selectedPortfolioId}
                  portfolioName={selectedPortfolio?.name}
                />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
}
