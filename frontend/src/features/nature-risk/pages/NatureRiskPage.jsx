import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import { Badge } from '../../../components/ui/badge';
import { Leaf, Droplets, TreePine, Building2, BarChart3, Target, FileText, Compass } from 'lucide-react';
import { NatureRiskDashboard } from '../components/dashboard/NatureRiskDashboard';
import { PortfolioNatureRisk } from '../components/portfolio/PortfolioNatureRisk';
import { WaterRiskAnalysis } from '../components/water/WaterRiskAnalysis';
import { BiodiversityOverlaps } from '../components/biodiversity/BiodiversityOverlaps';
import { ENCOREExplorer } from '../components/dashboard/ENCOREExplorer';
import { GBFAlignment } from '../components/dashboard/GBFAlignment';
import { LEAPAssessmentWizard } from '../components/leap/LEAPAssessmentWizard';

export default function NatureRiskPage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-white/[0.02] dark:bg-[#0d1424]">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
              <Leaf className="h-6 w-6 text-emerald-400 dark:text-emerald-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white dark:text-white">
                Nature Risk Module
              </h1>
              <p className="text-white/60 dark:text-white/30">
                TNFD LEAP Assessment & Portfolio Nature Risk Analysis
              </p>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/20">
              TNFD Framework
            </Badge>
            <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/20">
              ENCORE Database
            </Badge>
            <Badge variant="outline" className="bg-purple-500/10 text-purple-300 border-purple-500/20">
              GBF Aligned
            </Badge>
          </div>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-7 h-auto p-1 bg-white/[0.06] dark:bg-[#111827] rounded-lg">
            <TabsTrigger 
              value="dashboard" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-[#0d1424] dark:data-[state=active]:bg-[#1a2234]"
              data-testid="tab-dashboard"
            >
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">Dashboard</span>
            </TabsTrigger>
            <TabsTrigger 
              value="leap" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-[#0d1424] dark:data-[state=active]:bg-[#1a2234]"
              data-testid="tab-leap"
            >
              <Compass className="h-4 w-4" />
              <span className="hidden sm:inline">LEAP</span>
            </TabsTrigger>
            <TabsTrigger 
              value="portfolio" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-[#0d1424] dark:data-[state=active]:bg-[#1a2234]"
              data-testid="tab-portfolio"
            >
              <Building2 className="h-4 w-4" />
              <span className="hidden sm:inline">Portfolio</span>
            </TabsTrigger>
            <TabsTrigger 
              value="water" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-[#0d1424] dark:data-[state=active]:bg-[#1a2234]"
              data-testid="tab-water"
            >
              <Droplets className="h-4 w-4" />
              <span className="hidden sm:inline">Water Risk</span>
            </TabsTrigger>
            <TabsTrigger 
              value="biodiversity" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-[#0d1424] dark:data-[state=active]:bg-[#1a2234]"
              data-testid="tab-biodiversity"
            >
              <TreePine className="h-4 w-4" />
              <span className="hidden sm:inline">Biodiversity</span>
            </TabsTrigger>
            <TabsTrigger 
              value="encore" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-[#0d1424] dark:data-[state=active]:bg-[#1a2234]"
              data-testid="tab-encore"
            >
              <Leaf className="h-4 w-4" />
              <span className="hidden sm:inline">ENCORE</span>
            </TabsTrigger>
            <TabsTrigger 
              value="gbf" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-[#0d1424] dark:data-[state=active]:bg-[#1a2234]"
              data-testid="tab-gbf"
            >
              <Target className="h-4 w-4" />
              <span className="hidden sm:inline">GBF</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" data-testid="content-dashboard">
            <NatureRiskDashboard />
          </TabsContent>

          <TabsContent value="leap" data-testid="content-leap">
            <LEAPAssessmentWizard />
          </TabsContent>

          <TabsContent value="portfolio" data-testid="content-portfolio">
            <PortfolioNatureRisk />
          </TabsContent>

          <TabsContent value="water" data-testid="content-water">
            <WaterRiskAnalysis />
          </TabsContent>

          <TabsContent value="biodiversity" data-testid="content-biodiversity">
            <BiodiversityOverlaps />
          </TabsContent>

          <TabsContent value="encore" data-testid="content-encore">
            <ENCOREExplorer />
          </TabsContent>

          <TabsContent value="gbf" data-testid="content-gbf">
            <GBFAlignment />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
