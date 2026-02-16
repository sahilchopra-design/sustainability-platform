/**
 * Reusable Export Button Component
 * Provides PDF and Excel export dropdown
 */

import React, { useState } from 'react';
import { Download, FileText, FileSpreadsheet, ChevronDown, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { toast } from 'sonner';

export function ExportButton({ 
  onExport, 
  label = "Export",
  disabled = false,
  className = "",
  size = "default",
  variant = "outline",
}) {
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState(null);

  const handleExport = async (format) => {
    setIsExporting(true);
    setExportFormat(format);
    
    try {
      await onExport(format);
      toast.success(`${format.toUpperCase()} export downloaded successfully`);
    } catch (error) {
      console.error('Export error:', error);
      toast.error(`Export failed: ${error.message || 'Unknown error'}`);
    } finally {
      setIsExporting(false);
      setExportFormat(null);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant={variant} 
          size={size} 
          disabled={disabled || isExporting}
          className={className}
          data-testid="export-dropdown-btn"
        >
          {isExporting ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Exporting...
            </>
          ) : (
            <>
              <Download className="h-4 w-4 mr-2" />
              {label}
              <ChevronDown className="h-4 w-4 ml-2" />
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem 
          onClick={() => handleExport('pdf')}
          disabled={isExporting}
          data-testid="export-pdf-option"
        >
          <FileText className="h-4 w-4 mr-2 text-red-500" />
          Export as PDF
          {isExporting && exportFormat === 'pdf' && (
            <Loader2 className="h-4 w-4 ml-2 animate-spin" />
          )}
        </DropdownMenuItem>
        <DropdownMenuItem 
          onClick={() => handleExport('excel')}
          disabled={isExporting}
          data-testid="export-excel-option"
        >
          <FileSpreadsheet className="h-4 w-4 mr-2 text-green-600" />
          Export as Excel
          {isExporting && exportFormat === 'excel' && (
            <Loader2 className="h-4 w-4 ml-2 animate-spin" />
          )}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default ExportButton;
