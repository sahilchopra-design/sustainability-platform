import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../../components/ui/tabs';
import { Badge } from '../../../../components/ui/badge';
import { Leaf, Droplets, TreePine, Building2, BarChart3, Target, FileText } from 'lucide-react';
import { NatureRiskDashboard } from '../components/dashboard/NatureRiskDashboard';
import { PortfolioNatureRisk } from '../components/portfolio/PortfolioNatureRisk';
import { WaterRiskAnalysis } from '../components/water/WaterRiskAnalysis';
import { BiodiversityOverlaps } from '../components/biodiversity/BiodiversityOverlaps';
import { ENCOREExplorer } from '../components/dashboard/ENCOREExplorer';
import { GBFAlignment } from '../components/dashboard/GBFAlignment';

export default function NatureRiskPage() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg">
              <Leaf className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                Nature Risk Module
              </h1>
              <p className="text-slate-600 dark:text-slate-400">
                TNFD LEAP Assessment & Portfolio Nature Risk Analysis
              </p>
            </div>
          </div>
          <div className="flex gap-2 mt-3">
            <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
              TNFD Framework
            </Badge>
            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
              ENCORE Database
            </Badge>
            <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
              GBF Aligned
            </Badge>
          </div>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-6 h-auto p-1 bg-slate-100 dark:bg-slate-800 rounded-lg">
            <TabsTrigger 
              value="dashboard" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700"
              data-testid="tab-dashboard"
            >
              <BarChart3 className="h-4 w-4" />
              <span className="hidden sm:inline">Dashboard</span>
            </TabsTrigger>
            <TabsTrigger 
              value="portfolio" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700"
              data-testid="tab-portfolio"
            >
              <Building2 className="h-4 w-4" />
              <span className="hidden sm:inline">Portfolio</span>
            </TabsTrigger>
            <TabsTrigger 
              value="water" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700"
              data-testid="tab-water"
            >
              <Droplets className="h-4 w-4" />
              <span className="hidden sm:inline">Water Risk</span>
            </TabsTrigger>
            <TabsTrigger 
              value="biodiversity" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700"
              data-testid="tab-biodiversity"
            >
              <TreePine className="h-4 w-4" />
              <span className="hidden sm:inline">Biodiversity</span>
            </TabsTrigger>
            <TabsTrigger 
              value="encore" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700"
              data-testid="tab-encore"
            >
              <Leaf className="h-4 w-4" />
              <span className="hidden sm:inline">ENCORE</span>
            </TabsTrigger>
            <TabsTrigger 
              value="gbf" 
              className="flex items-center gap-2 py-2.5 data-[state=active]:bg-white dark:data-[state=active]:bg-slate-700"
              data-testid="tab-gbf"
            >
              <Target className="h-4 w-4" />
              <span className="hidden sm:inline">GBF</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" data-testid="content-dashboard">
            <NatureRiskDashboard />
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
