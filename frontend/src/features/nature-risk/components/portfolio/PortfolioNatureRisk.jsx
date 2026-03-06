import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Button } from '../../../../components/ui/button';
import { Badge } from '../../../../components/ui/badge';
import { Progress } from '../../../../components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../../components/ui/select';
import { Checkbox } from '../../../../components/ui/checkbox';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, 
  PolarRadiusAxis, Radar 
} from 'recharts';
import { 
  Leaf, Building2, AlertTriangle, TrendingUp, DollarSign,
  ChevronRight, Shield, Target 
} from 'lucide-react';
import { natureRiskApi } from '../../api/natureRiskApi';

const getRiskBadgeColor = (rating) => {
  switch (rating) {
    case 'critical': return 'bg-red-600 text-white';
    case 'high': return 'bg-orange-500 text-white';
    case 'medium-high': return 'bg-yellow-500 text-white';
    case 'medium': return 'bg-blue-500 text-white';
    case 'medium-low': return 'bg-green-400 text-white';
    default: return 'bg-green-500 text-white';
  }
};

export function PortfolioNatureRisk() {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenarios, setSelectedScenarios] = useState([]);
  const [includeCollateral, setIncludeCollateral] = useState(true);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadScenarios();
  }, []);

  const loadScenarios = async () => {
    try {
      const data = await natureRiskApi.getScenarios();
      setScenarios(data);
      if (data.length > 0) {
        setSelectedScenarios([data[0].id]);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const runAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await natureRiskApi.analyzePortfolioNatureRisk({
        portfolio_id: 'demo-portfolio',
        scenario_ids: selectedScenarios,
        include_collateral_impact: includeCollateral
      });
      setAnalysisResults(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const leapScoresData = analysisResults?.aggregate_metrics ? [
    { name: 'Locate', score: analysisResults.aggregate_metrics.avg_locate_score },
    { name: 'Evaluate', score: analysisResults.aggregate_metrics.avg_evaluate_score },
    { name: 'Assess', score: analysisResults.aggregate_metrics.avg_assess_score },
    { name: 'Prepare', score: analysisResults.aggregate_metrics.avg_prepare_score }
  ] : [];

  const dependencyData = analysisResults?.aggregate_metrics?.dependency_breakdown
    ? Object.entries(analysisResults.aggregate_metrics.dependency_breakdown).map(([name, count]) => ({
        name: name.charAt(0).toUpperCase() + name.slice(1).replace('_', ' '),
        count
      }))
    : [];

  return (
    <div className="space-y-6" data-testid="portfolio-nature-risk">
      {/* Configuration Panel */}
      <Card className="bg-[#0d1424] dark:bg-[#111827]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Leaf className="h-5 w-5 text-emerald-400" />
            Portfolio Nature Risk Analysis
          </CardTitle>
          <CardDescription>
            Comprehensive analysis of nature-related risks across your portfolio
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Select Scenarios</label>
              <div className="border rounded-lg p-3 max-h-[150px] overflow-y-auto space-y-2">
                {scenarios.map((s) => (
                  <div key={s.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={s.id}
                      checked={selectedScenarios.includes(s.id)}
                      onCheckedChange={(checked) => {
                        setSelectedScenarios(prev =>
                          checked
                            ? [...prev, s.id]
                            : prev.filter(id => id !== s.id)
                        );
                      }}
                    />
                    <label htmlFor={s.id} className="text-sm cursor-pointer">
                      {s.name}
                      <Badge variant="outline" className="ml-2 text-xs">
                        {s.framework}
                      </Badge>
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="collateral"
                  checked={includeCollateral}
                  onCheckedChange={setIncludeCollateral}
                />
                <label htmlFor="collateral" className="text-sm">
                  Include collateral impact assessment
                </label>
              </div>

              <Button
                onClick={runAnalysis}
                disabled={selectedScenarios.length === 0 || loading}
                className="w-full bg-emerald-600 hover:bg-emerald-700"
                data-testid="run-analysis-btn"
              >
                {loading ? 'Analyzing...' : 'Run Portfolio Analysis'}
              </Button>
            </div>
          </div>

          {error && (
            <div className="text-red-500 text-sm flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {analysisResults && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-[#0d1424] dark:bg-[#111827]">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-white/40 mb-2">
                  <Building2 className="h-4 w-4" />
                  <span className="text-sm">Holdings Analyzed</span>
                </div>
                <p className="text-3xl font-bold" data-testid="holdings-count">
                  {analysisResults.holding_count}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-[#0d1424] dark:bg-[#111827]">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-white/40 mb-2">
                  <Target className="h-4 w-4" />
                  <span className="text-sm">Avg LEAP Score</span>
                </div>
                <p className="text-3xl font-bold text-emerald-400" data-testid="avg-leap-score">
                  {analysisResults.aggregate_metrics?.average_leap_score?.toFixed(2)}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-[#0d1424] dark:bg-[#111827]">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-white/40 mb-2">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="text-sm">High Risk Holdings</span>
                </div>
                <p className="text-3xl font-bold text-orange-400" data-testid="high-risk-count">
                  {analysisResults.aggregate_metrics?.high_risk_count || 0}
                </p>
              </CardContent>
            </Card>

            <Card className="bg-[#0d1424] dark:bg-[#111827]">
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-white/40 mb-2">
                  <DollarSign className="h-4 w-4" />
                  <span className="text-sm">Exposure at Risk</span>
                </div>
                <p className="text-3xl font-bold text-red-400" data-testid="exposure-at-risk">
                  ${(analysisResults.aggregate_metrics?.total_exposure_at_risk_usd / 1e6)?.toFixed(1)}M
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* LEAP Scores */}
            <Card className="bg-[#0d1424] dark:bg-[#111827]">
              <CardHeader>
                <CardTitle>LEAP Score Distribution</CardTitle>
                <CardDescription>Average scores across TNFD LEAP phases</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={leapScoresData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 5]} />
                      <Tooltip formatter={(value) => value.toFixed(2)} />
                      <Bar dataKey="score" fill="#10b981" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Dependencies Radar */}
            <Card className="bg-[#0d1424] dark:bg-[#111827]">
              <CardHeader>
                <CardTitle>Key Dependencies</CardTitle>
                <CardDescription>Portfolio dependency on ecosystem services</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[300px]">
                  {dependencyData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={dependencyData}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="name" tick={{ fontSize: 12 }} />
                        <PolarRadiusAxis angle={30} domain={[0, 'auto']} />
                        <Radar
                          name="Holdings Count"
                          dataKey="count"
                          stroke="#3b82f6"
                          fill="#3b82f6"
                          fillOpacity={0.3}
                        />
                        <Tooltip />
                      </RadarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-white/40">
                      No dependency data available
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Holdings Table */}
          <Card className="bg-[#0d1424] dark:bg-[#111827]">
            <CardHeader>
              <CardTitle>Holding Details</CardTitle>
              <CardDescription>Individual holding nature risk assessment</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {analysisResults.holding_results?.map((holding, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 bg-white/[0.02] dark:bg-[#0d1424]/50 rounded-lg hover:bg-white/[0.06] dark:hover:bg-[#1a2234] transition-colors"
                    data-testid={`holding-${index}`}
                  >
                    <div className="flex-1">
                      <p className="font-medium text-white dark:text-white">
                        {holding.entity_name}
                      </p>
                      <p className="text-sm text-white/40">
                        {holding.sector} • ${(holding.exposure_usd / 1e6).toFixed(1)}M exposure
                      </p>
                      <div className="flex gap-2 mt-2">
                        {holding.key_dependencies?.slice(0, 3).map((dep, i) => (
                          <Badge key={i} variant="outline" className="text-xs">
                            {dep}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className={getRiskBadgeColor(holding.risk_rating)}>
                        {holding.risk_rating}
                      </Badge>
                      <p className="text-sm text-white/40 mt-1">
                        LEAP: {holding.leap_scores?.overall?.toFixed(2)}
                      </p>
                      {holding.financial_impact?.estimated_impact_usd > 0 && (
                        <p className="text-xs text-red-500 mt-1">
                          ${(holding.financial_impact.estimated_impact_usd / 1e6).toFixed(2)}M at risk
                        </p>
                      )}
                    </div>
                    <ChevronRight className="h-5 w-5 text-white/30 ml-4" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
