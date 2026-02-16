import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../../components/ui/select';
import { Progress } from '../../../../components/ui/progress';
import { Leaf, Building2, Layers, ArrowRight, Info } from 'lucide-react';
import { natureRiskApi } from '../../api/natureRiskApi';

const DEPENDENCY_COLORS = {
  5: 'bg-red-500',
  4: 'bg-orange-500',
  3: 'bg-yellow-500',
  2: 'bg-blue-400',
  1: 'bg-green-400'
};

const DEPENDENCY_LABELS = {
  5: 'Very High',
  4: 'High',
  3: 'Medium',
  2: 'Low',
  1: 'Very Low'
};

export function ENCOREExplorer() {
  const [sectors, setSectors] = useState([]);
  const [ecosystemServices, setEcosystemServices] = useState([]);
  const [selectedSector, setSelectedSector] = useState(null);
  const [dependencies, setDependencies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [sectorsData, servicesData] = await Promise.all([
        natureRiskApi.getENCORESectors(),
        natureRiskApi.getEcosystemServices()
      ]);
      setSectors(sectorsData);
      setEcosystemServices(servicesData);
    } catch (err) {
      console.error('Error loading ENCORE data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDependencies = async (sectorCode) => {
    try {
      setLoading(true);
      const data = await natureRiskApi.getENCOREDependencies(sectorCode);
      setDependencies(data);
    } catch (err) {
      console.error('Error loading dependencies:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSectorChange = (sectorCode) => {
    const sector = sectors.find(s => s.code === sectorCode);
    setSelectedSector(sector);
    loadDependencies(sectorCode);
  };

  // Group dependencies by ecosystem service
  const groupedDependencies = dependencies.reduce((acc, dep) => {
    const service = dep.ecosystem_service;
    if (!acc[service]) {
      acc[service] = [];
    }
    acc[service].push(dep);
    return acc;
  }, {});

  // Calculate average score per service
  const serviceScores = Object.entries(groupedDependencies).map(([service, deps]) => {
    const avgScore = deps.reduce((sum, d) => sum + (d.dependency_score || 0), 0) / deps.length;
    return { service, avgScore, count: deps.length };
  }).sort((a, b) => b.avgScore - a.avgScore);

  return (
    <div className="space-y-6" data-testid="encore-explorer">
      {/* Header */}
      <Card className="bg-white dark:bg-slate-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Leaf className="h-5 w-5 text-emerald-600" />
            ENCORE Dependency Explorer
          </CardTitle>
          <CardDescription>
            Explore ecosystem service dependencies by sector using ENCORE database
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Select Sector</label>
              <Select onValueChange={handleSectorChange}>
                <SelectTrigger className="w-full md:w-[300px]">
                  <SelectValue placeholder="Choose a sector to explore" />
                </SelectTrigger>
                <SelectContent>
                  {sectors.map(sector => (
                    <SelectItem key={sector.code} value={sector.code}>
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-slate-400" />
                        {sector.name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedSector && (
              <div className="flex gap-2">
                <Badge variant="outline" className="h-9 flex items-center gap-2">
                  <Layers className="h-4 w-4" />
                  {dependencies.length} dependencies
                </Badge>
                <Badge variant="outline" className="h-9 flex items-center gap-2">
                  {Object.keys(groupedDependencies).length} services
                </Badge>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Ecosystem Services Overview */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {ecosystemServices.slice(0, 5).map(service => (
          <Card key={service.id} className="bg-white dark:bg-slate-800">
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-xs font-medium truncate">{service.name}</span>
              </div>
              <p className="text-xs text-slate-500">{service.category}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {loading ? (
        <Card className="bg-white dark:bg-slate-800">
          <CardContent className="py-12 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto"></div>
            <p className="text-slate-500 mt-2">Loading ENCORE data...</p>
          </CardContent>
        </Card>
      ) : selectedSector ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Service Scores */}
          <Card className="bg-white dark:bg-slate-800">
            <CardHeader>
              <CardTitle className="text-lg">Ecosystem Service Dependencies</CardTitle>
              <CardDescription>
                {selectedSector.name} sector dependency ratings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {serviceScores.map(({ service, avgScore, count }) => (
                  <div key={service} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium capitalize">
                          {service.replace('_', ' ')}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {count} {count === 1 ? 'subsector' : 'subsectors'}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded ${DEPENDENCY_COLORS[Math.round(avgScore)]} text-white`}>
                          {DEPENDENCY_LABELS[Math.round(avgScore)] || 'N/A'}
                        </span>
                        <span className="text-sm font-mono">{avgScore.toFixed(1)}</span>
                      </div>
                    </div>
                    <Progress 
                      value={avgScore * 20} 
                      className="h-2"
                    />
                  </div>
                ))}

                {serviceScores.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    No dependency data available for this sector
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Detailed Dependencies */}
          <Card className="bg-white dark:bg-slate-800">
            <CardHeader>
              <CardTitle className="text-lg">Dependency Details</CardTitle>
              <CardDescription>
                Breakdown by subsector and ecosystem service
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-[400px] overflow-y-auto">
                {dependencies.map((dep, index) => (
                  <div 
                    key={index}
                    className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">{dep.subsector_name}</span>
                      <Badge className={`${DEPENDENCY_COLORS[dep.dependency_score]} text-white`}>
                        {dep.dependency_score}/5
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <span>{dep.ecosystem_service.replace('_', ' ')}</span>
                      <ArrowRight className="h-3 w-3" />
                      <span className="capitalize">{dep.dependency_type}</span>
                    </div>
                    {dep.dependency_description && (
                      <p className="text-xs text-slate-500 mt-2 italic">
                        {dep.dependency_description}
                      </p>
                    )}
                  </div>
                ))}

                {dependencies.length === 0 && (
                  <div className="text-center py-8 text-slate-500">
                    Select a sector to view dependencies
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      ) : (
        <Card className="bg-white dark:bg-slate-800">
          <CardContent className="py-12 text-center text-slate-500">
            <Leaf className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Select a sector to explore its ecosystem dependencies</p>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card className="bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-emerald-600 mt-0.5" />
            <div>
              <p className="font-medium text-emerald-800 dark:text-emerald-200">About ENCORE</p>
              <p className="text-sm text-emerald-700 dark:text-emerald-300 mt-1">
                ENCORE (Exploring Natural Capital Opportunities, Risks and Exposure) is a tool 
                developed by the Natural Capital Finance Alliance to help financial institutions 
                understand how their portfolios depend on nature. Dependency scores range from 
                1 (Very Low) to 5 (Very High).
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
