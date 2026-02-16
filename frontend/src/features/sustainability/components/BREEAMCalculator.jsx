/**
 * BREEAM Certification Calculator with LEED Comparison
 * Building Research Establishment Environmental Assessment Method
 * 
 * BREEAM Schemes: New Construction, In-Use, Refurbishment, Infrastructure
 * Rating Levels: Pass (30%), Good (45%), Very Good (55%), Excellent (70%), Outstanding (85%)
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Slider } from '../../../components/ui/slider';
import { Badge } from '../../../components/ui/badge';
import { Progress } from '../../../components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs';
import {
  Building2, Calculator, ArrowRight, TrendingUp, Award, BarChart3,
  Leaf, Zap, Droplet, Recycle, TreePine, CloudRain, Factory, 
  Heart, Users, AlertCircle, CheckCircle2, ArrowUpDown, Scale,
  Download, FileText, FileSpreadsheet
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend,
  Cell
} from 'recharts';
import { useBREEAMCalculator, useLEEDCalculator, useExportAssessment } from '../hooks/useSustainability';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../../../components/ui/dropdown-menu';

// BREEAM Category configurations
const BREEAM_CATEGORIES = [
  { key: 'management', label: 'Management', icon: Users, weight: 12, color: '#8b5cf6' },
  { key: 'health_wellbeing', label: 'Health & Wellbeing', icon: Heart, weight: 15, color: '#ec4899' },
  { key: 'energy', label: 'Energy', icon: Zap, weight: 19, color: '#f59e0b' },
  { key: 'transport', label: 'Transport', icon: Factory, weight: 8, color: '#6366f1' },
  { key: 'water', label: 'Water', icon: Droplet, weight: 6, color: '#0ea5e9' },
  { key: 'materials', label: 'Materials', icon: Building2, weight: 12.5, color: '#64748b' },
  { key: 'waste', label: 'Waste', icon: Recycle, weight: 7.5, color: '#22c55e' },
  { key: 'land_use_ecology', label: 'Land Use & Ecology', icon: TreePine, weight: 10, color: '#10b981' },
  { key: 'pollution', label: 'Pollution', icon: CloudRain, weight: 10, color: '#ef4444' },
  { key: 'innovation', label: 'Innovation', icon: Award, weight: 10, color: '#a855f7' },
];

// BREEAM Rating levels
const BREEAM_RATINGS = {
  outstanding: { min: 85, color: '#1e40af', bg: 'bg-blue-900', label: 'Outstanding' },
  excellent: { min: 70, color: '#059669', bg: 'bg-emerald-600', label: 'Excellent' },
  very_good: { min: 55, color: '#16a34a', bg: 'bg-green-500', label: 'Very Good' },
  good: { min: 45, color: '#ca8a04', bg: 'bg-yellow-500', label: 'Good' },
  pass: { min: 30, color: '#d97706', bg: 'bg-amber-500', label: 'Pass' },
  unclassified: { min: 0, color: '#6b7280', bg: 'bg-gray-400', label: 'Unclassified' },
};

// LEED to BREEAM mapping for comparison
const LEED_CATEGORIES = [
  { key: 'energy_atmosphere', label: 'Energy & Atmosphere', maxPoints: 33 },
  { key: 'location_transportation', label: 'Location & Transportation', maxPoints: 16 },
  { key: 'indoor_environmental_quality', label: 'Indoor Environmental Quality', maxPoints: 16 },
  { key: 'materials_resources', label: 'Materials & Resources', maxPoints: 13 },
  { key: 'water_efficiency', label: 'Water Efficiency', maxPoints: 11 },
  { key: 'sustainable_sites', label: 'Sustainable Sites', maxPoints: 10 },
  { key: 'innovation', label: 'Innovation', maxPoints: 6 },
  { key: 'regional_priority', label: 'Regional Priority', maxPoints: 4 },
  { key: 'integrative_process', label: 'Integrative Process', maxPoints: 1 },
];

const getRatingFromScore = (score) => {
  if (score >= 85) return BREEAM_RATINGS.outstanding;
  if (score >= 70) return BREEAM_RATINGS.excellent;
  if (score >= 55) return BREEAM_RATINGS.very_good;
  if (score >= 45) return BREEAM_RATINGS.good;
  if (score >= 30) return BREEAM_RATINGS.pass;
  return BREEAM_RATINGS.unclassified;
};

const formatCurrency = (value) => {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value?.toFixed(0) || 0}`;
};

export function BREEAMCalculator() {
  const [activeTab, setActiveTab] = useState('calculator');
  
  // Form state
  const [propertyName, setPropertyName] = useState('');
  const [propertySector, setPropertySector] = useState('office');
  const [region, setRegion] = useState('europe');
  const [breeamScheme, setBreeamScheme] = useState('new_construction');
  const [floorArea, setFloorArea] = useState('');
  const [propertyValue, setPropertyValue] = useState('');
  const [yearBuilt, setYearBuilt] = useState('');
  
  // Category scores (0-100)
  const [categoryScores, setCategoryScores] = useState({
    management: 50,
    health_wellbeing: 50,
    energy: 50,
    transport: 50,
    water: 50,
    materials: 50,
    waste: 50,
    land_use_ecology: 50,
    pollution: 50,
    innovation: 50,
  });

  // LEED comparison scores
  const [leedScores, setLeedScores] = useState({
    energy_atmosphere: 15,
    location_transportation: 8,
    indoor_environmental_quality: 8,
    materials_resources: 6,
    water_efficiency: 5,
    sustainable_sites: 5,
    innovation: 3,
    regional_priority: 2,
    integrative_process: 1,
  });
  
  const { mutate: calculateBREEAM, data: breeamResult, isPending: isBreeamLoading } = useBREEAMCalculator();
  const { mutate: calculateLEED, data: leedResult, isPending: isLeedLoading } = useLEEDCalculator();
  const { mutate: exportAssessment, isPending: isExporting } = useExportAssessment();
  
  // Export handler
  const handleExport = (format) => {
    if (!breeamResult) return;
    
    exportAssessment({
      data: {
        ...breeamResult,
        property_name: propertyName || 'BREEAM Assessment',
        property_sector: propertySector,
        region: region,
        breeam_scheme: breeamScheme,
      },
      format,
      assessmentType: 'breeam',
    });
  };
  
  // Calculate weighted score locally for preview
  const calculateWeightedScore = () => {
    let weighted = 0;
    BREEAM_CATEGORIES.forEach(cat => {
      weighted += (categoryScores[cat.key] * cat.weight) / 100;
    });
    return weighted;
  };
  
  const previewScore = calculateWeightedScore();
  const previewRating = getRatingFromScore(previewScore);
  
  // Calculate LEED total for preview
  const leedTotalPoints = Object.values(leedScores).reduce((a, b) => a + b, 0);
  const getLEEDLevel = (points) => {
    if (points >= 80) return { label: 'Platinum', color: '#94a3b8' };
    if (points >= 60) return { label: 'Gold', color: '#fbbf24' };
    if (points >= 50) return { label: 'Silver', color: '#9ca3af' };
    return { label: 'Certified', color: '#22c55e' };
  };
  const leedLevel = getLEEDLevel(leedTotalPoints);
  
  const handleCalculate = () => {
    const breeamPayload = {
      property_name: propertyName || 'Sample Property',
      property_sector: propertySector,
      region: region,
      breeam_scheme: breeamScheme,
      category_scores: categoryScores,
      weights: {
        management: 0.12,
        health_wellbeing: 0.15,
        energy: 0.19,
        transport: 0.08,
        water: 0.06,
        materials: 0.125,
        waste: 0.075,
        land_use_ecology: 0.10,
        pollution: 0.10,
        innovation: 0.10,
      },
      gross_floor_area_m2: parseFloat(floorArea) || 5000,
      year_built: parseInt(yearBuilt) || 2020,
      current_value: parseFloat(propertyValue) || 50000000,
    };
    
    calculateBREEAM(breeamPayload);
  };

  const handleCompare = () => {
    // Calculate BREEAM
    handleCalculate();
    
    // Calculate LEED
    const leedPayload = {
      property_name: propertyName || 'Sample Property',
      property_sector: propertySector,
      region: region,
      leed_version: 'v4.1',
      project_type: 'bd+c',
      category_scores: leedScores,
      gross_floor_area_m2: parseFloat(floorArea) || 5000,
      year_built: parseInt(yearBuilt) || 2020,
      current_value: parseFloat(propertyValue) || 50000000,
    };
    
    calculateLEED(leedPayload);
  };

  const updateCategoryScore = (key, value) => {
    setCategoryScores(prev => ({ ...prev, [key]: value[0] }));
  };

  const updateLeedScore = (key, value) => {
    setLeedScores(prev => ({ ...prev, [key]: parseInt(value) || 0 }));
  };

  // Prepare chart data for category comparison
  const radarData = BREEAM_CATEGORIES.filter(c => c.key !== 'innovation').map(cat => ({
    category: cat.label.split(' ')[0],
    score: categoryScores[cat.key],
    benchmark: 55, // Very Good threshold
  }));

  // Bar chart data for weighted scores
  const barData = BREEAM_CATEGORIES.map(cat => ({
    name: cat.label.split('&')[0].trim().slice(0, 8),
    score: (categoryScores[cat.key] * cat.weight / 100),
    weight: cat.weight,
    fill: cat.color,
  }));

  return (
    <div className="space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2 bg-white border border-slate-200">
          <TabsTrigger
            value="calculator"
            className="flex items-center gap-2 data-[state=active]:bg-blue-50 data-[state=active]:text-blue-700"
            data-testid="breeam-calculator-tab"
          >
            <Calculator className="h-4 w-4" />
            BREEAM Calculator
          </TabsTrigger>
          <TabsTrigger
            value="comparison"
            className="flex items-center gap-2 data-[state=active]:bg-violet-50 data-[state=active]:text-violet-700"
            data-testid="breeam-leed-comparison-tab"
          >
            <Scale className="h-4 w-4" />
            BREEAM vs LEED
          </TabsTrigger>
        </TabsList>

        {/* BREEAM Calculator Tab */}
        <TabsContent value="calculator" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Form */}
            <Card className="lg:col-span-2">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Building2 className="h-5 w-5 text-blue-600" />
                  Property Details & Category Scores
                </CardTitle>
                <CardDescription>
                  Enter property information and BREEAM category scores (0-100 per category)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Property Details */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="propertyName">Property Name</Label>
                    <Input
                      id="propertyName"
                      placeholder="Enter property name"
                      value={propertyName}
                      onChange={(e) => setPropertyName(e.target.value)}
                      data-testid="breeam-property-name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Property Sector</Label>
                    <Select value={propertySector} onValueChange={setPropertySector}>
                      <SelectTrigger data-testid="breeam-sector-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="office">Office</SelectItem>
                        <SelectItem value="retail">Retail</SelectItem>
                        <SelectItem value="industrial">Industrial</SelectItem>
                        <SelectItem value="multifamily">Multifamily</SelectItem>
                        <SelectItem value="hotel">Hotel</SelectItem>
                        <SelectItem value="healthcare">Healthcare</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>BREEAM Scheme</Label>
                    <Select value={breeamScheme} onValueChange={setBreeamScheme}>
                      <SelectTrigger data-testid="breeam-scheme-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="new_construction">New Construction</SelectItem>
                        <SelectItem value="in_use">In-Use</SelectItem>
                        <SelectItem value="refurbishment">Refurbishment</SelectItem>
                        <SelectItem value="infrastructure">Infrastructure</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <Label>Region</Label>
                    <Select value={region} onValueChange={setRegion}>
                      <SelectTrigger data-testid="breeam-region-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="europe">Europe</SelectItem>
                        <SelectItem value="north_america">North America</SelectItem>
                        <SelectItem value="asia_pacific">Asia Pacific</SelectItem>
                        <SelectItem value="middle_east">Middle East</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Floor Area (m²)</Label>
                    <Input
                      type="number"
                      placeholder="5000"
                      value={floorArea}
                      onChange={(e) => setFloorArea(e.target.value)}
                      data-testid="breeam-floor-area"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Property Value ($)</Label>
                    <Input
                      type="number"
                      placeholder="50000000"
                      value={propertyValue}
                      onChange={(e) => setPropertyValue(e.target.value)}
                      data-testid="breeam-property-value"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Year Built</Label>
                    <Input
                      type="number"
                      placeholder="2020"
                      value={yearBuilt}
                      onChange={(e) => setYearBuilt(e.target.value)}
                      data-testid="breeam-year-built"
                    />
                  </div>
                </div>

                {/* Category Scores */}
                <div className="border-t pt-4">
                  <h3 className="font-medium text-slate-800 mb-4 flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Category Scores (0-100)
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                    {BREEAM_CATEGORIES.map(cat => {
                      const Icon = cat.icon;
                      return (
                        <div key={cat.key} className="space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Icon className="h-4 w-4" style={{ color: cat.color }} />
                              <Label className="text-sm">{cat.label}</Label>
                              <Badge variant="outline" className="text-xs">
                                {cat.weight}%
                              </Badge>
                            </div>
                            <span className="text-sm font-medium" style={{ color: cat.color }}>
                              {categoryScores[cat.key]}
                            </span>
                          </div>
                          <Slider
                            value={[categoryScores[cat.key]]}
                            onValueChange={(val) => updateCategoryScore(cat.key, val)}
                            max={100}
                            step={1}
                            className="w-full"
                            data-testid={`breeam-slider-${cat.key}`}
                          />
                        </div>
                      );
                    })}
                  </div>
                </div>

                <Button
                  onClick={handleCalculate}
                  disabled={isBreeamLoading}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  data-testid="breeam-calculate-btn"
                >
                  {isBreeamLoading ? 'Calculating...' : 'Calculate BREEAM Assessment'}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </CardContent>
            </Card>

            {/* Preview & Results Panel */}
            <div className="space-y-4">
              {/* Live Preview */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Award className="h-4 w-4 text-blue-600" />
                    Live Score Preview
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center space-y-3">
                    <div className="text-4xl font-bold" style={{ color: previewRating.color }}>
                      {previewScore.toFixed(1)}%
                    </div>
                    <Badge 
                      className={`${previewRating.bg} text-white text-sm px-3 py-1`}
                      data-testid="breeam-preview-rating"
                    >
                      {previewRating.label}
                    </Badge>
                    <Progress 
                      value={previewScore} 
                      className="h-2"
                    />
                    <div className="flex justify-between text-xs text-slate-500">
                      <span>Pass 30%</span>
                      <span>Outstanding 85%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Rating Scale */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">BREEAM Rating Scale</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Object.entries(BREEAM_RATINGS).filter(([k]) => k !== 'unclassified').map(([key, val]) => (
                      <div key={key} className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-3 h-3 rounded-full" 
                            style={{ backgroundColor: val.color }}
                          />
                          <span>{val.label}</span>
                        </div>
                        <span className="text-slate-500">≥{val.min}%</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Results Section */}
          {breeamResult && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
              {/* Assessment Result */}
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      Assessment Result
                    </CardTitle>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={isExporting}
                          data-testid="export-breeam-btn"
                        >
                          <Download className="h-4 w-4 mr-1" />
                          {isExporting ? 'Exporting...' : 'Export'}
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleExport('pdf')}>
                          <FileText className="h-4 w-4 mr-2" />
                          Export as PDF
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleExport('excel')}>
                          <FileSpreadsheet className="h-4 w-4 mr-2" />
                          Export as Excel
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-blue-50 p-4 rounded-lg text-center">
                      <div className="text-3xl font-bold text-blue-700">
                        {parseFloat(breeamResult.weighted_score || previewScore).toFixed(1)}%
                      </div>
                      <div className="text-sm text-slate-600">Weighted Score</div>
                    </div>
                    <div className="bg-emerald-50 p-4 rounded-lg text-center">
                      <Badge className={`${getRatingFromScore(parseFloat(breeamResult.weighted_score) || previewScore).bg} text-white`}>
                        {breeamResult.rating?.replace('_', ' ').toUpperCase() || previewRating.label}
                      </Badge>
                      <div className="text-sm text-slate-600 mt-2">Rating Level</div>
                    </div>
                  </div>

                  {breeamResult.points_to_next_level && (
                    <div className="bg-amber-50 border border-amber-200 p-3 rounded-lg">
                      <div className="flex items-center gap-2 text-amber-700">
                        <TrendingUp className="h-4 w-4" />
                        <span className="text-sm font-medium">
                          {parseFloat(breeamResult.points_to_next_level).toFixed(1)} points to next level
                        </span>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div>
                      <div className="text-sm text-slate-500">Rent Premium</div>
                      <div className="text-lg font-semibold text-emerald-600">
                        +{parseFloat(breeamResult.estimated_rent_premium_percent || 7.5).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-500">Value Premium</div>
                      <div className="text-lg font-semibold text-emerald-600">
                        +{parseFloat(breeamResult.estimated_value_premium_percent || 12.8).toFixed(1)}%
                      </div>
                    </div>
                    {breeamResult.estimated_value_impact && (
                      <div className="col-span-2">
                        <div className="text-sm text-slate-500">Estimated Value Impact</div>
                        <div className="text-xl font-bold text-blue-600">
                          {formatCurrency(breeamResult.estimated_value_impact)}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Category Performance Chart */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Category Performance vs Benchmark</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={280}>
                    <RadarChart data={radarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="category" tick={{ fontSize: 10 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} />
                      <Radar
                        name="Your Score"
                        dataKey="score"
                        stroke="#3b82f6"
                        fill="#3b82f6"
                        fillOpacity={0.5}
                      />
                      <Radar
                        name="Very Good Threshold"
                        dataKey="benchmark"
                        stroke="#22c55e"
                        fill="none"
                        strokeDasharray="5 5"
                      />
                      <Legend />
                    </RadarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Weighted Score Breakdown */}
              <Card className="lg:col-span-2">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Weighted Score Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={barData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" domain={[0, 20]} />
                      <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 11 }} />
                      <Tooltip
                        formatter={(value, name, props) => [
                          `${value.toFixed(2)} (${props.payload.weight}% weight)`,
                          'Weighted Score'
                        ]}
                      />
                      <Bar dataKey="score" radius={[0, 4, 4, 0]}>
                        {barData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Improvement Priorities */}
              {breeamResult.improvement_priorities && breeamResult.improvement_priorities.length > 0 && (
                <Card className="lg:col-span-2">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <AlertCircle className="h-4 w-4 text-amber-500" />
                      Improvement Priorities
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {breeamResult.improvement_priorities.map((item, idx) => (
                        <div
                          key={idx}
                          className={`p-3 rounded-lg border ${
                            item.priority === 'high' 
                              ? 'bg-red-50 border-red-200' 
                              : 'bg-amber-50 border-amber-200'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <span className="font-medium text-sm">{item.category}</span>
                            <Badge variant="outline" className={
                              item.priority === 'high' ? 'text-red-600' : 'text-amber-600'
                            }>
                              {item.priority}
                            </Badge>
                          </div>
                          <div className="text-xs text-slate-600">
                            Current: {item.current_score} → Target: {item.target_score}
                          </div>
                          <div className="text-xs text-emerald-600 font-medium">
                            +{item.potential_weighted_gain?.toFixed(1)} weighted points
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </TabsContent>

        {/* BREEAM vs LEED Comparison Tab */}
        <TabsContent value="comparison" className="mt-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* BREEAM Input */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-blue-600" />
                    BREEAM Categories
                  </CardTitle>
                  <Badge variant="outline" className="bg-blue-50 text-blue-700">
                    Score: {previewScore.toFixed(1)}%
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {BREEAM_CATEGORIES.slice(0, 6).map(cat => {
                    const Icon = cat.icon;
                    return (
                      <div key={cat.key} className="flex items-center gap-3">
                        <Icon className="h-4 w-4 flex-shrink-0" style={{ color: cat.color }} />
                        <div className="flex-1">
                          <div className="flex justify-between text-sm mb-1">
                            <span>{cat.label}</span>
                            <span className="font-medium">{categoryScores[cat.key]}</span>
                          </div>
                          <Slider
                            value={[categoryScores[cat.key]]}
                            onValueChange={(val) => updateCategoryScore(cat.key, val)}
                            max={100}
                            step={1}
                            className="w-full"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* LEED Input */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Leaf className="h-5 w-5 text-green-600" />
                    LEED Categories
                  </CardTitle>
                  <Badge variant="outline" className="bg-green-50 text-green-700">
                    Points: {leedTotalPoints}/110
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {LEED_CATEGORIES.slice(0, 6).map(cat => (
                    <div key={cat.key} className="flex items-center gap-3">
                      <Leaf className="h-4 w-4 flex-shrink-0 text-green-500" />
                      <div className="flex-1">
                        <div className="flex justify-between text-sm mb-1">
                          <span className="truncate">{cat.label}</span>
                          <span className="font-medium">{leedScores[cat.key]}/{cat.maxPoints}</span>
                        </div>
                        <Input
                          type="number"
                          min={0}
                          max={cat.maxPoints}
                          value={leedScores[cat.key]}
                          onChange={(e) => updateLeedScore(cat.key, e.target.value)}
                          className="h-8"
                          data-testid={`leed-input-${cat.key}`}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="mt-4">
            <Button
              onClick={handleCompare}
              disabled={isBreeamLoading || isLeedLoading}
              className="w-full bg-violet-600 hover:bg-violet-700"
              data-testid="compare-certifications-btn"
            >
              {isBreeamLoading || isLeedLoading ? 'Calculating...' : 'Compare Certifications'}
              <ArrowUpDown className="ml-2 h-4 w-4" />
            </Button>
          </div>

          {/* Comparison Results */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            {/* Side-by-Side Comparison */}
            <Card className="lg:col-span-2">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Side-by-Side Comparison</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {/* BREEAM Column */}
                  <div className="space-y-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <Building2 className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-blue-700">
                        {(breeamResult?.weighted_score || previewScore).toFixed(1)}%
                      </div>
                      <Badge className={`${previewRating.bg} text-white mt-2`}>
                        {breeamResult?.rating?.replace('_', ' ').toUpperCase() || previewRating.label}
                      </Badge>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Rent Premium</span>
                        <span className="font-medium text-emerald-600">
                          +{(breeamResult?.estimated_rent_premium_percent || 7.5).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Value Premium</span>
                        <span className="font-medium text-emerald-600">
                          +{(breeamResult?.estimated_value_premium_percent || 12.8).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Market Focus</span>
                        <span className="font-medium">Europe, UK</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Categories</span>
                        <span className="font-medium">10</span>
                      </div>
                    </div>
                  </div>

                  {/* LEED Column */}
                  <div className="space-y-4">
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <Leaf className="h-8 w-8 text-green-600 mx-auto mb-2" />
                      <div className="text-2xl font-bold text-green-700">
                        {leedResult?.total_points || leedTotalPoints}/110
                      </div>
                      <Badge 
                        className="text-white mt-2"
                        style={{ backgroundColor: leedLevel.color }}
                      >
                        {leedResult?.certification_level?.toUpperCase() || leedLevel.label.toUpperCase()}
                      </Badge>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Rent Premium</span>
                        <span className="font-medium text-emerald-600">
                          +{(leedResult?.estimated_rent_premium_percent || 9.0).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Value Premium</span>
                        <span className="font-medium text-emerald-600">
                          +{(leedResult?.estimated_value_premium_percent || 15.3).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Market Focus</span>
                        <span className="font-medium">Americas, Global</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Categories</span>
                        <span className="font-medium">9</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recommendation */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Award className="h-4 w-4 text-violet-600" />
                  Recommendation
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className={`p-4 rounded-lg ${region === 'europe' ? 'bg-blue-50 border border-blue-200' : 'bg-green-50 border border-green-200'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {region === 'europe' ? (
                      <Building2 className="h-5 w-5 text-blue-600" />
                    ) : (
                      <Leaf className="h-5 w-5 text-green-600" />
                    )}
                    <span className="font-semibold">
                      {region === 'europe' ? 'BREEAM Recommended' : 'LEED Recommended'}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600">
                    {region === 'europe' 
                      ? 'For European markets, BREEAM has stronger recognition and typically commands higher premiums.'
                      : 'For North American markets, LEED is the dominant certification with highest market recognition.'
                    }
                  </p>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="font-medium text-slate-700">Key Differences:</div>
                  <ul className="space-y-1 text-slate-600">
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                      <span>BREEAM: Percentage-based scoring (0-100%)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span>LEED: Points-based system (0-110 points)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="h-4 w-4 text-violet-500 mt-0.5 flex-shrink-0" />
                      <span>Both provide similar value premiums</span>
                    </li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default BREEAMCalculator;
