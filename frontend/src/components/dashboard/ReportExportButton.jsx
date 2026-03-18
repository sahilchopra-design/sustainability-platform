import React, { useState } from 'react';
import { Button } from '../ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../ui/dropdown-menu';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../ui/dialog';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
import { Progress } from '../ui/progress';
import { Download, FileSpreadsheet, FileText, FileJson, Loader2, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '../../lib/utils';

const EXPORT_FORMATS = [
  { id: 'pdf', label: 'PDF Report', icon: FileText, description: 'Formatted report with charts' },
  { id: 'xlsx', label: 'Excel', icon: FileSpreadsheet, description: 'Spreadsheet with raw data' },
  { id: 'csv', label: 'CSV', icon: FileSpreadsheet, description: 'Simple comma-separated values' },
  { id: 'json', label: 'JSON', icon: FileJson, description: 'Structured data format' },
];

const EXPORT_SECTIONS = [
  { id: 'summary', label: 'Executive Summary', default: true },
  { id: 'metrics', label: 'Portfolio Metrics', default: true },
  { id: 'scenarios', label: 'Scenario Analysis Results', default: true },
  { id: 'holdings', label: 'Counterparty Holdings', default: true },
  { id: 'charts', label: 'Visualizations', default: true },
  { id: 'methodology', label: 'Methodology Notes', default: false },
];

// Seeded fallback used when no live analysis results are available (demo / offline mode)
function buildFallbackResults(portfolioData) {
  const portfolioName = portfolioData?.name || 'Demo Portfolio';
  const totalExposure = portfolioData?.total_exposure || 850_000_000;
  const scenarios = [
    { scenario_name: 'Net Zero 2050', horizon: 2030, el_pct: 0.031, pd_change: 0.18, cap_charge: 0.048 },
    { scenario_name: 'Net Zero 2050', horizon: 2050, el_pct: 0.019, pd_change: 0.09, cap_charge: 0.031 },
    { scenario_name: 'Below 2°C', horizon: 2030, el_pct: 0.044, pd_change: 0.27, cap_charge: 0.062 },
    { scenario_name: 'Below 2°C', horizon: 2050, el_pct: 0.029, pd_change: 0.14, cap_charge: 0.041 },
    { scenario_name: 'Delayed Transition', horizon: 2030, el_pct: 0.061, pd_change: 0.43, cap_charge: 0.089 },
    { scenario_name: 'Delayed Transition', horizon: 2050, el_pct: 0.082, pd_change: 0.58, cap_charge: 0.11 },
    { scenario_name: 'Current Policies', horizon: 2030, el_pct: 0.078, pd_change: 0.51, cap_charge: 0.104 },
    { scenario_name: 'Current Policies', horizon: 2050, el_pct: 0.134, pd_change: 0.94, cap_charge: 0.168 },
  ];
  return {
    portfolio_id: portfolioData?.id || 'demo',
    portfolio_name: portfolioName,
    total_exposure: totalExposure,
    run_date: new Date().toISOString(),
    results: scenarios.map(s => ({
      scenario_name: s.scenario_name,
      horizon: s.horizon,
      portfolio_metrics: {
        expected_loss: totalExposure * s.el_pct,
        avg_pd_change: s.pd_change,
        capital_charge: totalExposure * s.cap_charge,
      },
    })),
    sector_breakdown: {
      'Energy': totalExposure * 0.22,
      'Utilities': totalExposure * 0.18,
      'Industrials': totalExposure * 0.16,
      'Real Estate': totalExposure * 0.14,
      'Materials': totalExposure * 0.12,
      'Financials': totalExposure * 0.10,
      'Other': totalExposure * 0.08,
    },
    _fallback: true,
  };
}

export function ReportExportButton({
  analysisResults = null,
  portfolioData = null,
  disabled = false,
  className,
}) {
  const isFallback = !analysisResults;
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState(null);
  const [selectedSections, setSelectedSections] = useState(
    EXPORT_SECTIONS.filter(s => s.default).map(s => s.id)
  );
  const [exporting, setExporting] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);

  const handleFormatSelect = (format) => {
    setSelectedFormat(format);
    setDialogOpen(true);
  };

  const toggleSection = (sectionId) => {
    if (selectedSections.includes(sectionId)) {
      setSelectedSections(selectedSections.filter(id => id !== sectionId));
    } else {
      setSelectedSections([...selectedSections, sectionId]);
    }
  };

  const handleExport = async () => {
    if (!selectedFormat) return;

    setExporting(true);
    setExportProgress(0);

    try {
      // Simulate export progress
      for (let i = 0; i <= 100; i += 20) {
        await new Promise(resolve => setTimeout(resolve, 300));
        setExportProgress(i);
      }

      // Generate export data — use live results or seeded fallback for demo mode
      const resultsToExport = analysisResults || buildFallbackResults(portfolioData);
      const exportData = generateExportData(
        selectedFormat.id,
        selectedSections,
        resultsToExport,
        portfolioData
      );

      // Trigger download
      downloadFile(exportData, selectedFormat.id);

      toast.success(`${selectedFormat.label} exported successfully`);
      setDialogOpen(false);
    } catch (error) {
      toast.error('Export failed. Please try again.');
    } finally {
      setExporting(false);
      setExportProgress(0);
    }
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            variant="outline"
            disabled={disabled}
            className={className}
            data-testid="report-export-button"
          >
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-[200px]">
          {EXPORT_FORMATS.map((format) => {
            const Icon = format.icon;
            return (
              <DropdownMenuItem
                key={format.id}
                onClick={() => handleFormatSelect(format)}
                data-testid={`export-format-${format.id}`}
              >
                <Icon className="h-4 w-4 mr-2" />
                <div>
                  <p className="font-medium">{format.label}</p>
                  <p className="text-xs text-muted-foreground">{format.description}</p>
                </div>
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Export Configuration Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent data-testid="export-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedFormat?.icon && <selectedFormat.icon className="h-5 w-5" />}
              Export as {selectedFormat?.label}
            </DialogTitle>
            <DialogDescription>
              Select which sections to include in your report
              {isFallback && (
                <span className="block mt-1 text-amber-600 dark:text-amber-400 text-xs font-medium">
                  Using seeded demo data — run an analysis to export live results
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          <div className="py-4 space-y-4">
            {/* Section Selection */}
            <div className="space-y-3">
              {EXPORT_SECTIONS.map((section) => (
                <label
                  key={section.id}
                  className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted cursor-pointer"
                >
                  <Checkbox
                    checked={selectedSections.includes(section.id)}
                    onCheckedChange={() => toggleSection(section.id)}
                    data-testid={`export-section-${section.id}`}
                  />
                  <span className="text-sm">{section.label}</span>
                </label>
              ))}
            </div>

            {/* Export Progress */}
            {exporting && (
              <div className="space-y-2 pt-4 border-t">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Generating report...</span>
                  <span className="tabular-nums">{exportProgress}%</span>
                </div>
                <Progress value={exportProgress} />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)} disabled={exporting}>
              Cancel
            </Button>
            <Button 
              onClick={handleExport} 
              disabled={exporting || selectedSections.length === 0}
              data-testid="confirm-export-button"
            >
              {exporting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Helper functions
function generateExportData(format, sections, analysisResults, portfolioData) {
  const data = {
    exportDate: new Date().toISOString(),
    sections,
    portfolio: portfolioData,
    analysis: analysisResults,
  };

  switch (format) {
    case 'json':
      return JSON.stringify(data, null, 2);
    case 'csv':
      return generateCSV(data);
    case 'xlsx':
    case 'pdf':
    default:
      return JSON.stringify(data, null, 2);
  }
}

function generateCSV(data) {
  const analysis = data.analysis;
  const fmt = (n) => typeof n === 'number' ? n.toLocaleString('en-US', { maximumFractionDigits: 2 }) : (n || 'N/A');
  const rows = [
    ['Climate Risk Analysis Report'],
    ['Export Date', data.exportDate],
    analysis?._fallback ? ['Data Mode', 'Seeded Demo (backend offline)'] : ['Data Mode', 'Live Analysis'],
    [],
    ['Portfolio Summary'],
    ['Portfolio Name', analysis?.portfolio_name || data.portfolio?.name || 'N/A'],
    ['Total Exposure (EUR)', fmt(analysis?.total_exposure || data.portfolio?.total_exposure)],
    ['Run Date', analysis?.run_date || data.exportDate],
    [],
  ];

  if (analysis?.results?.length) {
    rows.push(['Scenario Analysis Results']);
    rows.push(['Scenario', 'Horizon', 'Expected Loss (EUR)', 'Avg PD Change', 'Capital Charge (EUR)']);
    analysis.results.forEach(result => {
      rows.push([
        result.scenario_name,
        result.horizon,
        fmt(result.portfolio_metrics?.expected_loss),
        fmt(result.portfolio_metrics?.avg_pd_change),
        fmt(result.portfolio_metrics?.capital_charge),
      ]);
    });
    rows.push([]);
  }

  if (analysis?.sector_breakdown) {
    rows.push(['Sector Breakdown']);
    rows.push(['Sector', 'Exposure (EUR)']);
    Object.entries(analysis.sector_breakdown).forEach(([sector, exposure]) => {
      rows.push([sector, fmt(exposure)]);
    });
  }

  return rows.map(row => row.map(v => `"${v}"`).join(',')).join('\n');
}

function downloadFile(content, format) {
  const mimeTypes = {
    json: 'application/json',
    csv: 'text/csv',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    pdf: 'application/pdf',
  };

  const blob = new Blob([content], { type: mimeTypes[format] || 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `sustainability_platform_report_${new Date().toISOString().split('T')[0]}.${format}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
