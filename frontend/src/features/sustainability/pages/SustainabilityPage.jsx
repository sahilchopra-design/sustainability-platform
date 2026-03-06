/**
 * Sustainability Frameworks Page
 * Main page with tabs for different sustainability assessment tools
 */
import React, { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Badge } from '../../../components/ui/badge';
import {
  LayoutDashboard, Award, Leaf, Building2, DollarSign,
  Globe, BarChart3, CheckCircle
} from 'lucide-react';

import { SustainabilityDashboard } from '../components/SustainabilityDashboard';
import { GRESBCalculator } from '../components/GRESBCalculator';
import { LEEDCalculator } from '../components/LEEDCalculator';
import { BREEAMCalculator } from '../components/BREEAMCalculator';
import { ValueImpactCalculator } from '../components/ValueImpactCalculator';

export default function SustainabilityPage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-white/[0.02]">
      {/* Header */}
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-100 rounded-lg">
            <Leaf className="h-6 w-6 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Sustainability Frameworks</h1>
            <p className="text-sm text-white/40">
              Analyze green certification value impact: GRESB, LEED, BREEAM, and more
            </p>
          </div>
        </div>

        {/* Framework Badges */}
        <div className="flex gap-2 mt-4">
          <Badge variant="outline" className="bg-violet-50 text-violet-700 border-violet-200">
            <Award className="h-3 w-3 mr-1" />
            GRESB
          </Badge>
          <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/20">
            <Leaf className="h-3 w-3 mr-1" />
            LEED
          </Badge>
          <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/20">
            <Building2 className="h-3 w-3 mr-1" />
            BREEAM
          </Badge>
          <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/20">
            <CheckCircle className="h-3 w-3 mr-1" />
            Energy Star
          </Badge>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-6 bg-[#0d1424] border border-white/[0.06]">
            <TabsTrigger
              value="dashboard"
              className="flex items-center gap-2 data-[state=active]:bg-white/[0.06]"
              data-testid="tab-sustainability-dashboard"
            >
              <LayoutDashboard className="h-4 w-4" />
              <span className="hidden md:inline">Dashboard</span>
            </TabsTrigger>
            <TabsTrigger
              value="gresb"
              className="flex items-center gap-2 data-[state=active]:bg-violet-50 data-[state=active]:text-violet-700"
              data-testid="tab-gresb"
            >
              <Award className="h-4 w-4" />
              <span className="hidden md:inline">GRESB</span>
            </TabsTrigger>
            <TabsTrigger
              value="leed"
              className="flex items-center gap-2 data-[state=active]:bg-green-500/10 data-[state=active]:text-green-400"
              data-testid="tab-leed"
            >
              <Leaf className="h-4 w-4" />
              <span className="hidden md:inline">LEED</span>
            </TabsTrigger>
            <TabsTrigger
              value="breeam"
              className="flex items-center gap-2 data-[state=active]:bg-blue-500/10 data-[state=active]:text-blue-300"
              data-testid="tab-breeam"
            >
              <Building2 className="h-4 w-4" />
              <span className="hidden md:inline">BREEAM</span>
            </TabsTrigger>
            <TabsTrigger
              value="value-impact"
              className="flex items-center gap-2 data-[state=active]:bg-emerald-500/10 data-[state=active]:text-emerald-400"
              data-testid="tab-value-impact"
            >
              <DollarSign className="h-4 w-4" />
              <span className="hidden md:inline">Value Impact</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="mt-0">
            <SustainabilityDashboard />
          </TabsContent>

          <TabsContent value="gresb" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                <div className="p-1.5 bg-violet-100 rounded">
                  <Award className="h-4 w-4 text-violet-600" />
                </div>
                GRESB Assessment Calculator
              </h2>
              <p className="text-sm text-white/60 mt-1">
                Global Real Estate Sustainability Benchmark for portfolio-level ESG performance evaluation
              </p>
            </div>
            <GRESBCalculator />
          </TabsContent>

          <TabsContent value="leed" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                <div className="p-1.5 bg-green-100 rounded">
                  <Leaf className="h-4 w-4 text-green-400" />
                </div>
                LEED Certification Calculator
              </h2>
              <p className="text-sm text-white/60 mt-1">
                Leadership in Energy and Environmental Design - the most widely used green building rating system
              </p>
            </div>
            <LEEDCalculator />
          </TabsContent>

          <TabsContent value="breeam" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                <div className="p-1.5 bg-blue-100 rounded">
                  <Building2 className="h-4 w-4 text-blue-300" />
                </div>
                BREEAM Certification Calculator
              </h2>
              <p className="text-sm text-white/60 mt-1">
                Building Research Establishment Environmental Assessment Method - the world's leading sustainability assessment for buildings with LEED comparison
              </p>
            </div>
            <BREEAMCalculator />
          </TabsContent>

          <TabsContent value="value-impact" className="mt-0">
            <div className="mb-4">
              <h2 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                <div className="p-1.5 bg-emerald-100 rounded">
                  <DollarSign className="h-4 w-4 text-emerald-400" />
                </div>
                Value Impact Analysis
              </h2>
              <p className="text-sm text-white/60 mt-1">
                Calculate rent/value premiums and ROI for green certifications based on research data
              </p>
            </div>
            <ValueImpactCalculator />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
