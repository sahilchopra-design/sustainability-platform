/**
 * Real Estate Valuation Page
 * Main page with tabs for different valuation approaches
 */
import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Badge } from '../../../components/ui/badge';
import { 
  LayoutDashboard, TrendingUp, LineChart, Hammer, Scale, 
  Calculator, Building2, DollarSign
} from 'lucide-react';

import { ValuationDashboard } from '../components/ValuationDashboard';
import { DirectCapCalculator } from '../components/DirectCapCalculator';
import { DCFCalculator } from '../components/DCFCalculator';
import { CostApproachCalculator } from '../components/CostApproachCalculator';
import { SalesComparisonCalculator } from '../components/SalesComparisonCalculator';

export default function ValuationPage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-100 rounded-lg">
            <Building2 className="h-6 w-6 text-emerald-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Real Estate Valuation Engine</h1>
            <p className="text-sm text-slate-500">
              Professional-grade property valuations using Income, Cost, and Sales Comparison approaches
            </p>
          </div>
        </div>
        
        {/* Approach Badges */}
        <div className="flex gap-2 mt-4">
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            <TrendingUp className="h-3 w-3 mr-1" />
            Income Approach
          </Badge>
          <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
            <Hammer className="h-3 w-3 mr-1" />
            Cost Approach
          </Badge>
          <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
            <Scale className="h-3 w-3 mr-1" />
            Sales Comparison
          </Badge>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-6 bg-white border border-slate-200">
            <TabsTrigger 
              value="dashboard" 
              className="flex items-center gap-2 data-[state=active]:bg-slate-100"
              data-testid="tab-dashboard"
            >
              <LayoutDashboard className="h-4 w-4" />
              <span className="hidden md:inline">Dashboard</span>
            </TabsTrigger>
            <TabsTrigger 
              value="direct-cap" 
              className="flex items-center gap-2 data-[state=active]:bg-blue-50 data-[state=active]:text-blue-700"
              data-testid="tab-direct-cap"
            >
              <TrendingUp className="h-4 w-4" />
              <span className="hidden md:inline">Direct Cap</span>
            </TabsTrigger>
            <TabsTrigger 
              value="dcf" 
              className="flex items-center gap-2 data-[state=active]:bg-violet-50 data-[state=active]:text-violet-700"
              data-testid="tab-dcf"
            >
              <LineChart className="h-4 w-4" />
              <span className="hidden md:inline">DCF</span>
            </TabsTrigger>
            <TabsTrigger 
              value="cost" 
              className="flex items-center gap-2 data-[state=active]:bg-amber-50 data-[state=active]:text-amber-700"
              data-testid="tab-cost"
            >
              <Hammer className="h-4 w-4" />
              <span className="hidden md:inline">Cost</span>
            </TabsTrigger>
            <TabsTrigger 
              value="sales" 
              className="flex items-center gap-2 data-[state=active]:bg-emerald-50 data-[state=active]:text-emerald-700"
              data-testid="tab-sales"
            >
              <Scale className="h-4 w-4" />
              <span className="hidden md:inline">Sales Comp</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="mt-0">
            <ValuationDashboard />
          </TabsContent>

          <TabsContent value="direct-cap" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <div className="p-1.5 bg-blue-100 rounded">
                  <TrendingUp className="h-4 w-4 text-blue-600" />
                </div>
                Direct Capitalization Method
              </h2>
              <p className="text-sm text-slate-600 mt-1">
                Value = NOI / Cap Rate. Best for stabilized income-producing properties with predictable cash flows.
              </p>
            </div>
            <DirectCapCalculator />
          </TabsContent>

          <TabsContent value="dcf" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <div className="p-1.5 bg-violet-100 rounded">
                  <LineChart className="h-4 w-4 text-violet-600" />
                </div>
                Discounted Cash Flow Analysis
              </h2>
              <p className="text-sm text-slate-600 mt-1">
                Multi-year projection of cash flows discounted to present value. Best for properties with changing income streams.
              </p>
            </div>
            <DCFCalculator />
          </TabsContent>

          <TabsContent value="cost" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <div className="p-1.5 bg-amber-100 rounded">
                  <Hammer className="h-4 w-4 text-amber-600" />
                </div>
                Replacement Cost Method
              </h2>
              <p className="text-sm text-slate-600 mt-1">
                Value = Land + (RCN - Depreciation). Best for special-purpose properties and newer construction.
              </p>
            </div>
            <CostApproachCalculator />
          </TabsContent>

          <TabsContent value="sales" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <div className="p-1.5 bg-emerald-100 rounded">
                  <Scale className="h-4 w-4 text-emerald-600" />
                </div>
                Sales Comparison Approach
              </h2>
              <p className="text-sm text-slate-600 mt-1">
                Adjusts recent comparable sales to estimate subject value. Best when sufficient market data is available.
              </p>
            </div>
            <SalesComparisonCalculator />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
