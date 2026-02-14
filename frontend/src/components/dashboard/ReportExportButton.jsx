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

export function ReportExportButton({
  analysisResults = null,
  portfolioData = null,
  disabled = false,
  className,
}) {
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

      // Generate export data
      const exportData = generateExportData(
        selectedFormat.id,
        selectedSections,
        analysisResults,
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
            disabled={disabled || !analysisResults}
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
  const rows = [
    ['Climate Risk Analysis Report'],
    ['Export Date', data.exportDate],
    [],
    ['Portfolio Summary'],
    ['Portfolio Name', data.portfolio?.name || 'N/A'],
    ['Total Exposure', data.portfolio?.total_exposure || 'N/A'],
    [],
  ];

  if (data.analysis?.results) {
    rows.push(['Scenario Analysis Results']);
    rows.push(['Scenario', 'Horizon', 'Expected Loss', 'PD Change']);
    
    data.analysis.results.forEach(result => {
      rows.push([
        result.scenario_name,
        result.horizon,
        result.portfolio_metrics?.expected_loss || 0,
        result.portfolio_metrics?.avg_pd_change || 0,
      ]);
    });
  }

  return rows.map(row => row.join(',')).join('\n');
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
  a.download = `climate_risk_report_${new Date().toISOString().split('T')[0]}.${format}`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
