/**
 * LEAP Results Visualization Component
 * Charts and visualizations for LEAP assessment results
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { Progress } from '../../../../components/ui/progress';
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import { 
  MapPin, Search, FileCheck, FileText, CheckCircle, 
  AlertTriangle, TrendingUp, Leaf, Target, Shield
} from 'lucide-react';

const RISK_COLORS = ['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444'];
const STEP_COLORS = {
  locate: '#3b82f6',
  evaluate: '#8b5cf6',
  assess: '#f59e0b',
  prepare: '#10b981',
};

const getRiskBadgeClass = (rating) => {
  const ratings = {
    'Low': 'bg-green-100 text-green-300',
    'Low-Medium': 'bg-lime-100 text-lime-800',
    'Medium': 'bg-yellow-100 text-yellow-800',
    'Medium-High': 'bg-orange-100 text-orange-300',
    'High': 'bg-red-100 text-red-300',
    'Very High': 'bg-red-200 text-red-900',
  };
  return ratings[rating] || 'bg-white/[0.06] text-white/90';
};

export function LEAPResultsVisualization({ result }) {
  if (!result) return null;

  // Prepare radar chart data for LEAP scores
  const radarData = [
    { step: 'Locate', score: result.locate_score || 0, fullMark: 5 },
    { step: 'Evaluate', score: result.evaluate_score || 0, fullMark: 5 },
    { step: 'Assess', score: result.assess_score || 0, fullMark: 5 },
    { step: 'Prepare', score: result.prepare_score || 0, fullMark: 5 },
  ];

  // Bar chart data for scenario comparison
  const scenarioData = result.scenario_results?.map(s => ({
    name: s.scenario_name?.replace('TNFD ', '').replace('NCORE ', '') || 'Unknown',
    overall: s.overall_score || 0,
    locate: s.locate_score || 0,
    evaluate: s.evaluate_score || 0,
    assess: s.assess_score || 0,
    prepare: s.prepare_score || 0,
  })) || [];

  // Risk distribution pie chart
  const riskDistribution = [
    { name: 'Low', value: result.risk_breakdown?.low || 20 },
    { name: 'Medium', value: result.risk_breakdown?.medium || 30 },
    { name: 'High', value: result.risk_breakdown?.high || 35 },
    { name: 'Critical', value: result.risk_breakdown?.critical || 15 },
  ];

  // Overall score
  const overallScore = result.overall_risk_score || result.overall_score || 
    ((result.locate_score || 0) + (result.evaluate_score || 0) + 
     (result.assess_score || 0) + (result.prepare_score || 0)) / 4;

  return (
    <div className="space-y-6" data-testid="leap-results-visualization">
      {/* Overall Summary */}
      <Card className="bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border-emerald-500/20">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {/* Overall Score */}
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-[#0d1424] shadow-lg mb-3">
                <span className="text-3xl font-bold text-emerald-400">
                  {overallScore.toFixed(1)}
                </span>
              </div>
              <p className="text-sm font-medium text-white/60">Overall Score</p>
              <Badge className={getRiskBadgeClass(result.overall_risk_rating)}>
                {result.overall_risk_rating || 'Medium'}
              </Badge>
            </div>

            {/* LEAP Step Scores */}
            {[
              { key: 'locate', label: 'Locate', icon: MapPin, color: STEP_COLORS.locate },
              { key: 'evaluate', label: 'Evaluate', icon: Search, color: STEP_COLORS.evaluate },
              { key: 'assess', label: 'Assess', icon: FileCheck, color: STEP_COLORS.assess },
              { key: 'prepare', label: 'Prepare', icon: FileText, color: STEP_COLORS.prepare },
            ].map(step => {
              const StepIcon = step.icon;
              const score = result[`${step.key}_score`] || 0;
              return (
                <div key={step.key} className="text-center">
                  <div 
                    className="inline-flex items-center justify-center w-12 h-12 rounded-full mb-2"
                    style={{ backgroundColor: `${step.color}20` }}
                  >
                    <StepIcon className="h-5 w-5" style={{ color: step.color }} />
                  </div>
                  <p className="text-2xl font-bold" style={{ color: step.color }}>
                    {score.toFixed(1)}
                  </p>
                  <p className="text-xs text-white/40">{step.label}</p>
                  <Progress 
                    value={(score / 5) * 100} 
                    className="h-1.5 mt-2"
                    style={{ '--progress-background': step.color }}
                  />
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="h-4 w-4 text-emerald-400" />
              LEAP Score Profile
            </CardTitle>
            <CardDescription>Assessment scores across LEAP steps</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis 
                  dataKey="step" 
                  tick={{ fontSize: 12, fill: '#64748b' }}
                />
                <PolarRadiusAxis 
                  angle={30} 
                  domain={[0, 5]} 
                  tick={{ fontSize: 10 }}
                />
                <Radar
                  name="Score"
                  dataKey="score"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.4}
                  strokeWidth={2}
                />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Risk Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Shield className="h-4 w-4 text-amber-400" />
              Risk Distribution
            </CardTitle>
            <CardDescription>Nature-related risk breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={riskDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {riskDistribution.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={RISK_COLORS[index % RISK_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => [`${value}%`, 'Proportion']}
                />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Scenario Comparison */}
      {scenarioData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-300" />
              Scenario Comparison
            </CardTitle>
            <CardDescription>Risk scores across different climate/nature scenarios</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={scenarioData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" domain={[0, 5]} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11 }} />
                <Tooltip 
                  formatter={(value) => [value.toFixed(2), '']}
                  contentStyle={{ fontSize: 12 }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="locate" name="Locate" fill={STEP_COLORS.locate} stackId="a" />
                <Bar dataKey="evaluate" name="Evaluate" fill={STEP_COLORS.evaluate} stackId="a" />
                <Bar dataKey="assess" name="Assess" fill={STEP_COLORS.assess} stackId="a" />
                <Bar dataKey="prepare" name="Prepare" fill={STEP_COLORS.prepare} stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      {result.recommendations && result.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Leaf className="h-4 w-4 text-emerald-400" />
              Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {result.recommendations.map((rec, idx) => (
                <div 
                  key={idx}
                  className="flex items-start gap-3 p-3 bg-white/[0.02] dark:bg-[#111827] rounded-lg"
                >
                  <CheckCircle className="h-5 w-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-white/90 dark:text-white/15">
                      {rec.title || rec}
                    </p>
                    {rec.description && (
                      <p className="text-xs text-white/40 mt-1">{rec.description}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default LEAPResultsVisualization;
