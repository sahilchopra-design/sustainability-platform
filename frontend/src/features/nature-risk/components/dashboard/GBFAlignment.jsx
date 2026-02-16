import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { Progress } from '../../../../components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../../components/ui/tabs';
import { 
  Target, CheckCircle, AlertCircle, XCircle, 
  ChevronRight, Globe, Shield, Info 
} from 'lucide-react';
import { natureRiskApi } from '../../api/natureRiskApi';

const ALIGNMENT_COLORS = {
  'aligned': 'text-green-600 bg-green-100',
  'partial': 'text-yellow-600 bg-yellow-100',
  'not_aligned': 'text-red-600 bg-red-100',
  'not_applicable': 'text-slate-500 bg-slate-100'
};

const ALIGNMENT_ICONS = {
  'aligned': CheckCircle,
  'partial': AlertCircle,
  'not_aligned': XCircle,
  'not_applicable': Shield
};

export function GBFAlignment() {
  const [targets, setTargets] = useState([]);
  const [alignmentData, setAlignmentData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState('all');

  useEffect(() => {
    loadGBFData();
  }, []);

  const loadGBFData = async () => {
    try {
      setLoading(true);
      const [targetsData, alignmentResults] = await Promise.all([
        natureRiskApi.getGBFTargets(),
        natureRiskApi.getGBFAlignment('portfolio', 'demo-portfolio', 2024)
      ]);
      setTargets(targetsData);
      setAlignmentData(alignmentResults);
    } catch (err) {
      console.error('Error loading GBF data:', err);
    } finally {
      setLoading(false);
    }
  };

  const categories = [...new Set(targets.map(t => t.category))];
  
  const filteredTargets = activeCategory === 'all' 
    ? targets 
    : targets.filter(t => t.category === activeCategory);

  // Calculate summary stats
  const alignmentSummary = {
    aligned: alignmentData.filter(a => a.alignment_status === 'aligned').length,
    partial: alignmentData.filter(a => a.alignment_status === 'partial').length,
    not_aligned: alignmentData.filter(a => a.alignment_status === 'not_aligned').length,
    total: targets.length
  };

  const overallScore = alignmentData.length > 0
    ? alignmentData.reduce((sum, a) => sum + (a.alignment_score || 0), 0) / alignmentData.length
    : 0;

  // Get alignment status for a target
  const getAlignmentForTarget = (targetNumber) => {
    return alignmentData.find(a => a.target_number === targetNumber);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="gbf-alignment">
      {/* Header */}
      <Card className="bg-white dark:bg-slate-800">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-purple-600" />
            Global Biodiversity Framework Alignment
          </CardTitle>
          <CardDescription>
            Track alignment with the Kunming-Montreal GBF targets
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-green-50 dark:bg-green-900/20 border-green-200">
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 mb-1">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  <span className="text-sm text-green-700">Aligned</span>
                </div>
                <p className="text-2xl font-bold text-green-700" data-testid="aligned-count">
                  {alignmentSummary.aligned}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200">
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 mb-1">
                  <AlertCircle className="h-4 w-4 text-yellow-600" />
                  <span className="text-sm text-yellow-700">Partial</span>
                </div>
                <p className="text-2xl font-bold text-yellow-700" data-testid="partial-count">
                  {alignmentSummary.partial}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-red-50 dark:bg-red-900/20 border-red-200">
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 mb-1">
                  <XCircle className="h-4 w-4 text-red-600" />
                  <span className="text-sm text-red-700">Not Aligned</span>
                </div>
                <p className="text-2xl font-bold text-red-700" data-testid="not-aligned-count">
                  {alignmentSummary.not_aligned}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-purple-50 dark:bg-purple-900/20 border-purple-200">
              <CardContent className="pt-4">
                <div className="flex items-center gap-2 mb-1">
                  <Target className="h-4 w-4 text-purple-600" />
                  <span className="text-sm text-purple-700">Overall Score</span>
                </div>
                <p className="text-2xl font-bold text-purple-700" data-testid="overall-score">
                  {overallScore.toFixed(0)}%
                </p>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* Category Tabs */}
      <Tabs value={activeCategory} onValueChange={setActiveCategory}>
        <TabsList className="w-full justify-start overflow-x-auto">
          <TabsTrigger value="all">All Targets</TabsTrigger>
          {categories.map(cat => (
            <TabsTrigger key={cat} value={cat}>
              {cat}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={activeCategory} className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredTargets.map(target => {
              const alignment = getAlignmentForTarget(target.number);
              const Icon = alignment 
                ? ALIGNMENT_ICONS[alignment.alignment_status] 
                : Shield;
              const colorClass = alignment 
                ? ALIGNMENT_COLORS[alignment.alignment_status] 
                : 'text-slate-500 bg-slate-100';

              return (
                <Card 
                  key={target.number}
                  className="bg-white dark:bg-slate-800 hover:shadow-lg transition-shadow"
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline" className="font-mono">
                            {target.number}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            {target.category}
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-700 dark:text-slate-300">
                          {target.description}
                        </p>
                        
                        {alignment && (
                          <div className="mt-3">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-xs text-slate-500">Alignment Score</span>
                              <span className="text-xs font-medium">{alignment.alignment_score}%</span>
                            </div>
                            <Progress value={alignment.alignment_score} className="h-2" />
                          </div>
                        )}
                      </div>
                      <div className={`p-2 rounded-full ${colorClass}`}>
                        <Icon className="h-5 w-5" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>
      </Tabs>

      {/* Information Panel */}
      <Card className="bg-purple-50 dark:bg-purple-900/20 border-purple-200">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Globe className="h-5 w-5 text-purple-600 mt-0.5" />
            <div>
              <p className="font-medium text-purple-800 dark:text-purple-200">
                Kunming-Montreal Global Biodiversity Framework
              </p>
              <p className="text-sm text-purple-700 dark:text-purple-300 mt-1">
                The GBF was adopted in December 2022 and sets out 23 action-oriented global targets 
                for urgent action over the decade to 2030. Target 15 specifically requires businesses 
                to regularly monitor, assess, and transparently disclose their risks, dependencies, 
                and impacts on biodiversity through their operations, supply and value chains.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alignment Details */}
      {alignmentData.length > 0 && (
        <Card className="bg-white dark:bg-slate-800">
          <CardHeader>
            <CardTitle className="text-lg">Your Alignment Progress</CardTitle>
            <CardDescription>
              Detailed status for tracked targets
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alignmentData.map((item, index) => {
                const Icon = ALIGNMENT_ICONS[item.alignment_status] || Shield;
                const colorClass = ALIGNMENT_COLORS[item.alignment_status] || 'text-slate-500 bg-slate-100';

                return (
                  <div 
                    key={index}
                    className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${colorClass}`}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{item.target_number}</p>
                        <p className="text-xs text-slate-500">{item.target_description}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">{item.alignment_score}%</p>
                      <Badge className={colorClass.replace('bg-', 'bg-opacity-50 ')}>
                        {item.alignment_status.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
