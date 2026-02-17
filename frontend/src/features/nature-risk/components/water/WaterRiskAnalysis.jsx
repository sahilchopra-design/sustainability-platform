import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Button } from '../../../../components/ui/button';
import { Badge } from '../../../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../../components/ui/tabs';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, BarChart, Bar 
} from 'recharts';
import { 
  Droplets, MapPin, AlertTriangle, TrendingUp, 
  ThermometerSun, CloudRain, Filter, Map, List 
} from 'lucide-react';
import { natureRiskApi } from '../../api/natureRiskApi';
import { WaterRiskMap } from './WaterRiskMap';

const getRiskColor = (value) => {
  if (value >= 4) return 'text-red-600 bg-red-50';
  if (value >= 3) return 'text-orange-600 bg-orange-50';
  if (value >= 2) return 'text-yellow-600 bg-yellow-50';
  return 'text-green-600 bg-green-50';
};

const getRiskLevel = (value) => {
  if (value >= 4) return 'Extremely High';
  if (value >= 3) return 'High';
  if (value >= 2) return 'Medium';
  if (value >= 1) return 'Low-Medium';
  return 'Low';
};

export function WaterRiskAnalysis() {
  const [locations, setLocations] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [countryFilter, setCountryFilter] = useState('');

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      const [locationsData, scenariosData] = await Promise.all([
        natureRiskApi.getWaterRiskLocations(),
        natureRiskApi.getScenarios()
      ]);
      setLocations(locationsData);
      setScenarios(scenariosData);
      if (scenariosData.length > 0) {
        setSelectedScenario(scenariosData[0].id);
      }
    } catch (err) {
      console.error('Error loading data:', err);
    }
  };

  const analyzeLocation = async (locationId) => {
    if (!selectedScenario) return;
    
    try {
      setLoading(true);
      const result = await natureRiskApi.getWaterRiskReport(locationId, selectedScenario);
      setAnalysisResult(result);
      setSelectedLocation(locations.find(l => l.id === locationId));
    } catch (err) {
      console.error('Error analyzing location:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredLocations = countryFilter
    ? locations.filter(l => l.country_code === countryFilter)
    : locations;

  const countries = [...new Set(locations.map(l => l.country_code))].sort();

  const projectionData = analysisResult ? [
    { year: 'Baseline', stress: analysisResult.indicators?.water_stress || 0 },
    { year: '2030', stress: analysisResult.projected_risk_scores?.[2030] || 0 },
    { year: '2040', stress: analysisResult.projected_risk_scores?.[2040] || 0 },
    { year: '2050', stress: analysisResult.projected_risk_scores?.[2050] || 0 }
  ] : [];

  const indicatorData = analysisResult?.indicators ? [
    { name: 'Water Stress', value: analysisResult.indicators.water_stress },
    { name: 'Groundwater', value: analysisResult.indicators.groundwater_decline },
    { name: 'Drought Risk', value: analysisResult.indicators.drought_risk },
    { name: 'Flood Risk', value: analysisResult.indicators.flood_risk },
    { name: 'Seasonal Var.', value: analysisResult.indicators.seasonal_variability }
  ] : [];

  return (
    <div className="space-y-6" data-testid="water-risk-analysis">
      {/* Header */}
      <Card className="bg-white dark:bg-slate-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Droplets className="h-5 w-5 text-blue-600" />
            Water Risk Analysis
          </CardTitle>
          <CardDescription>
            Analyze water stress and risk projections using WRI Aqueduct data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Filter by Country</label>
              <Select value={countryFilter || 'all'} onValueChange={(v) => setCountryFilter(v === 'all' ? '' : v)}>
                <SelectTrigger>
                  <SelectValue placeholder="All Countries" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Countries</SelectItem>
                  {countries.map(code => (
                    <SelectItem key={code} value={code}>{code}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Scenario</label>
              <Select value={selectedScenario || 'none'} onValueChange={(v) => setSelectedScenario(v === 'none' ? null : v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select scenario" />
                </SelectTrigger>
                <SelectContent>
                  {scenarios.map(s => (
                    <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Badge variant="outline" className="h-10 flex items-center gap-2">
                <Filter className="h-4 w-4" />
                {filteredLocations.length} locations
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Locations List */}
        <Card className="bg-white dark:bg-slate-800 lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Locations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {filteredLocations.map(location => (
                <div
                  key={location.id}
                  className={`p-3 rounded-lg cursor-pointer transition-all ${
                    selectedLocation?.id === location.id
                      ? 'bg-blue-50 dark:bg-blue-900/30 border-2 border-blue-500'
                      : 'bg-slate-50 dark:bg-slate-700/50 hover:bg-slate-100 dark:hover:bg-slate-700'
                  }`}
                  onClick={() => analyzeLocation(location.id)}
                  data-testid={`location-${location.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-slate-400" />
                      <span className="font-medium text-sm">{location.location_name}</span>
                    </div>
                    <Badge className={getRiskColor(location.baseline_water_stress)}>
                      {location.baseline_water_stress?.toFixed(1)}
                    </Badge>
                  </div>
                  <div className="text-xs text-slate-500 mt-1 ml-6">
                    {location.country_code} • {location.basin_name}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Analysis Results */}
        <div className="lg:col-span-2 space-y-6">
          {loading ? (
            <Card className="bg-white dark:bg-slate-800">
              <CardContent className="py-12 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-slate-500 mt-2">Analyzing water risk...</p>
              </CardContent>
            </Card>
          ) : analysisResult ? (
            <>
              {/* Summary Cards */}
              <div className="grid grid-cols-3 gap-4">
                <Card className="bg-white dark:bg-slate-800">
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-2 text-slate-500 mb-1">
                      <Droplets className="h-4 w-4" />
                      <span className="text-xs">Baseline Risk</span>
                    </div>
                    <p className={`text-2xl font-bold ${getRiskColor(analysisResult.baseline_risk_score).split(' ')[0]}`}>
                      {analysisResult.baseline_risk_score?.toFixed(2)}
                    </p>
                    <p className="text-xs text-slate-500">{getRiskLevel(analysisResult.baseline_risk_score)}</p>
                  </CardContent>
                </Card>

                <Card className="bg-white dark:bg-slate-800">
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-2 text-slate-500 mb-1">
                      <TrendingUp className="h-4 w-4" />
                      <span className="text-xs">2050 Projection</span>
                    </div>
                    <p className={`text-2xl font-bold ${getRiskColor(analysisResult.projected_risk_scores?.[2050] || 0).split(' ')[0]}`}>
                      {analysisResult.projected_risk_scores?.[2050]?.toFixed(2) || 'N/A'}
                    </p>
                    <p className="text-xs text-slate-500">{getRiskLevel(analysisResult.projected_risk_scores?.[2050])}</p>
                  </CardContent>
                </Card>

                <Card className="bg-white dark:bg-slate-800">
                  <CardContent className="pt-6">
                    <div className="flex items-center gap-2 text-slate-500 mb-1">
                      <AlertTriangle className="h-4 w-4" />
                      <span className="text-xs">Key Risks</span>
                    </div>
                    <p className="text-2xl font-bold text-orange-600">
                      {analysisResult.key_risk_factors?.length || 0}
                    </p>
                    <p className="text-xs text-slate-500">Risk factors identified</p>
                  </CardContent>
                </Card>
              </div>

              {/* Projection Chart */}
              <Card className="bg-white dark:bg-slate-800">
                <CardHeader>
                  <CardTitle className="text-lg">Water Stress Projections</CardTitle>
                  <CardDescription>
                    {selectedLocation?.location_name} under selected scenario
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-[250px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={projectionData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="year" />
                        <YAxis domain={[0, 5]} />
                        <Tooltip formatter={(value) => value.toFixed(2)} />
                        <Line 
                          type="monotone" 
                          dataKey="stress" 
                          stroke="#3b82f6" 
                          strokeWidth={2}
                          dot={{ fill: '#3b82f6', r: 5 }}
                          name="Water Stress"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Risk Thresholds Legend */}
                  <div className="grid grid-cols-4 gap-2 mt-4 text-center text-xs">
                    <div className="p-2 bg-green-50 dark:bg-green-900/20 rounded">
                      <p className="font-medium text-green-700">Low</p>
                      <p className="text-green-600">0-1</p>
                    </div>
                    <div className="p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded">
                      <p className="font-medium text-yellow-700">Medium</p>
                      <p className="text-yellow-600">1-2</p>
                    </div>
                    <div className="p-2 bg-orange-50 dark:bg-orange-900/20 rounded">
                      <p className="font-medium text-orange-700">High</p>
                      <p className="text-orange-600">2-4</p>
                    </div>
                    <div className="p-2 bg-red-50 dark:bg-red-900/20 rounded">
                      <p className="font-medium text-red-700">Extreme</p>
                      <p className="text-red-600">4-5</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Indicators */}
              <Card className="bg-white dark:bg-slate-800">
                <CardHeader>
                  <CardTitle className="text-lg">Risk Indicators</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-[200px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={indicatorData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" domain={[0, 5]} />
                        <YAxis dataKey="name" type="category" width={100} />
                        <Tooltip formatter={(value) => value.toFixed(2)} />
                        <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              {/* Recommendations */}
              {analysisResult.recommendations?.length > 0 && (
                <Card className="bg-white dark:bg-slate-800">
                  <CardHeader>
                    <CardTitle className="text-lg">Recommendations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {analysisResult.recommendations.map((rec, index) => (
                        <li key={index} className="flex items-start gap-2 text-sm">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card className="bg-white dark:bg-slate-800">
              <CardContent className="py-12 text-center text-slate-500">
                <Droplets className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a location to view water risk analysis</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
