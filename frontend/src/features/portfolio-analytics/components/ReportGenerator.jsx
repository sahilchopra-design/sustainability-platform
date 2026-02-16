/**
 * Report Generator Component
 * Generate various portfolio reports
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Button } from '../../../components/ui/button';
import { Badge } from '../../../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select';
import { Switch } from '../../../components/ui/switch';
import { Label } from '../../../components/ui/label';
import { Slider } from '../../../components/ui/slider';
import { Skeleton } from '../../../components/ui/skeleton';
import {
  FileText, Download, Loader2, CheckCircle, ChevronDown, ChevronUp,
  BarChart2, Leaf, AlertTriangle, TrendingUp, Users
} from 'lucide-react';
import { useGenerateReport } from '../hooks/usePortfolioAnalytics';

const REPORT_TYPES = [
  { 
    value: 'valuation', 
    label: 'Valuation Report',
    description: 'Detailed property valuations and methodology',
    icon: TrendingUp,
    color: 'bg-blue-100 text-blue-700',
  },
  { 
    value: 'climate_risk', 
    label: 'Climate Risk Report',
    description: 'Physical and transition risk assessment',
    icon: AlertTriangle,
    color: 'bg-amber-100 text-amber-700',
  },
  { 
    value: 'sustainability', 
    label: 'Sustainability Report',
    description: 'ESG metrics, certifications, improvement roadmap',
    icon: Leaf,
    color: 'bg-emerald-100 text-emerald-700',
  },
  { 
    value: 'tcfd', 
    label: 'TCFD Report',
    description: 'TCFD-aligned disclosure report',
    icon: FileText,
    color: 'bg-purple-100 text-purple-700',
  },
  { 
    value: 'investor', 
    label: 'Investor Report',
    description: 'Quarterly investor report with key metrics',
    icon: Users,
    color: 'bg-cyan-100 text-cyan-700',
  },
  { 
    value: 'executive', 
    label: 'Executive Summary',
    description: 'High-level dashboard for executives',
    icon: BarChart2,
    color: 'bg-slate-100 text-slate-700',
  },
];

export function ReportGenerator({ portfolioId, portfolioName }) {
  const [reportType, setReportType] = useState('valuation');
  const [timeHorizon, setTimeHorizon] = useState(10);
  const [includeCharts, setIncludeCharts] = useState(true);
  const [includeDetails, setIncludeDetails] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [generatedReport, setGeneratedReport] = useState(null);
  
  const { mutate: generateReport, isPending } = useGenerateReport();
  
  const selectedReportType = REPORT_TYPES.find(r => r.value === reportType);
  
  const handleGenerate = () => {
    setGeneratedReport(null);
    generateReport(
      {
        portfolioId,
        data: {
          report_type: reportType,
          format: 'json',
          time_horizon: timeHorizon,
          include_charts: includeCharts,
          include_property_details: includeDetails,
        },
      },
      {
        onSuccess: (data) => {
          setGeneratedReport(data);
        },
      }
    );
  };
  
  if (!portfolioId) {
    return (
      <Card className="bg-white" data-testid="report-generator-disabled">
        <CardContent className="py-12 text-center text-slate-500">
          <FileText className="h-12 w-12 mx-auto mb-4 text-slate-300" />
          <p>Select a portfolio to generate reports</p>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card className="bg-white" data-testid="report-generator">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-slate-700 flex items-center gap-2">
          <FileText className="h-4 w-4 text-blue-500" />
          Generate Report
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Report Type Selection */}
        <div>
          <Label className="text-xs text-slate-600 mb-2 block">Report Type</Label>
          <Select value={reportType} onValueChange={setReportType}>
            <SelectTrigger data-testid="report-type-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {REPORT_TYPES.map((type) => {
                const Icon = type.icon;
                return (
                  <SelectItem key={type.value} value={type.value}>
                    <div className="flex items-center gap-2">
                      <Icon className="h-4 w-4" />
                      <span>{type.label}</span>
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
          
          {selectedReportType && (
            <p className="text-xs text-slate-500 mt-2">{selectedReportType.description}</p>
          )}
        </div>
        
        {/* Advanced Options Toggle */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
        >
          {showAdvanced ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          Advanced Options
        </button>
        
        {showAdvanced && (
          <div className="space-y-4 p-3 bg-slate-50 rounded-lg">
            {/* Time Horizon */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="text-xs text-slate-600">Time Horizon</Label>
                <span className="text-xs font-medium text-slate-700">{timeHorizon} years</span>
              </div>
              <Slider
                value={[timeHorizon]}
                onValueChange={([v]) => setTimeHorizon(v)}
                min={1}
                max={30}
                step={1}
                className="w-full"
              />
            </div>
            
            {/* Include Charts */}
            <div className="flex items-center justify-between">
              <Label className="text-xs text-slate-600">Include Charts</Label>
              <Switch
                checked={includeCharts}
                onCheckedChange={setIncludeCharts}
              />
            </div>
            
            {/* Include Property Details */}
            <div className="flex items-center justify-between">
              <Label className="text-xs text-slate-600">Include Property Details</Label>
              <Switch
                checked={includeDetails}
                onCheckedChange={setIncludeDetails}
              />
            </div>
          </div>
        )}
        
        {/* Generate Button */}
        <Button 
          onClick={handleGenerate} 
          disabled={isPending}
          className="w-full"
          data-testid="generate-report-btn"
        >
          {isPending ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <FileText className="h-4 w-4 mr-2" />
              Generate {selectedReportType?.label}
            </>
          )}
        </Button>
        
        {/* Generated Report Preview */}
        {generatedReport && (
          <div className="mt-4 p-4 bg-emerald-50 rounded-lg border border-emerald-200" data-testid="report-generated">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle className="h-5 w-5 text-emerald-600" />
              <span className="font-medium text-emerald-800">Report Generated</span>
            </div>
            
            {/* Executive Summary */}
            {generatedReport.executive_summary && (
              <div className="space-y-2 text-sm">
                <p className="font-medium text-slate-700">Executive Summary</p>
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-white p-2 rounded">
                    <p className="text-xs text-slate-500">Portfolio</p>
                    <p className="font-medium">{generatedReport.executive_summary.portfolio_name}</p>
                  </div>
                  <div className="bg-white p-2 rounded">
                    <p className="text-xs text-slate-500">Properties</p>
                    <p className="font-medium">{generatedReport.executive_summary.property_count}</p>
                  </div>
                  <div className="bg-white p-2 rounded">
                    <p className="text-xs text-slate-500">Total Value</p>
                    <p className="font-medium">
                      ${(generatedReport.executive_summary.total_value / 1e6).toFixed(1)}M
                    </p>
                  </div>
                  <div className="bg-white p-2 rounded">
                    <p className="text-xs text-slate-500">Avg Risk Score</p>
                    <p className="font-medium">{generatedReport.executive_summary.avg_risk_score?.toFixed(1)}</p>
                  </div>
                </div>
                
                {/* Key Findings */}
                {generatedReport.executive_summary.key_findings?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs text-slate-500 mb-1">Key Findings</p>
                    <ul className="space-y-1">
                      {generatedReport.executive_summary.key_findings.map((finding, i) => (
                        <li key={i} className="text-xs text-slate-600 flex items-start gap-1">
                          <span className="text-emerald-500 mt-0.5">•</span>
                          {finding}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
