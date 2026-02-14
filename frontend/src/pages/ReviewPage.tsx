import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Download, CheckCircle2 } from 'lucide-react';
import { ColumnMappingWizard } from '../components/upload/ColumnMappingWizard';
import { DataPreviewTable, DataRow } from '../components/upload/DataPreviewTable';
import { ValidationResultsPanel, ValidationSummary } from '../components/upload/ValidationResultsPanel';
import { UploadProgressTracker, UploadStep } from '../components/upload/UploadProgressTracker';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { useColumnMapping } from '../hooks/useColumnMapping';
import axios from 'axios';
import { toast } from 'sonner';
import { UploadPreview, ValidationError } from '../types/upload';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function ReviewPage() {
  const { portfolioId, uploadId } = useParams<{ portfolioId: string; uploadId: string }>();
  const navigate = useNavigate();

  // State
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [validationSummary, setValidationSummary] = useState<ValidationSummary | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [currentStep, setCurrentStep] = useState<UploadStep>('mapping');
  const [processing, setProcessing] = useState(false);

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [selectedRows, setSelectedRows] = useState<number[]>([]);

  // Column mapping hook
  const {
    mapping,
    suggestions,
    requiredFields,
    updateMapping,
    applyAutoMapping,
    clearMapping,
    completeMapping,
    saveAsTemplate,
  } = useColumnMapping({
    uploadId: uploadId || '',
    fileColumns: preview?.columns || [],
    onMappingComplete: async (mapping) => {
      await handleValidate(mapping);
    },
  });

  // Load preview data
  useEffect(() => {
    const loadPreview = async () => {
      if (!portfolioId || !uploadId) return;

      setLoading(true);
      try {
        const response = await axios.get<UploadPreview>(
          `${BACKEND_URL}/api/v1/portfolios/${portfolioId}/uploads/${uploadId}/preview`
        );
        setPreview(response.data);

        // Auto-apply mapping if exists
        if (response.data.mapping) {
          Object.entries(response.data.mapping).forEach(([field, column]) => {
            updateMapping(field, column as string);
          });
        }
      } catch (err: any) {
        toast.error('Failed to Load Preview', {
          description: err.response?.data?.detail || 'Could not load upload preview',
        });
      } finally {
        setLoading(false);
      }
    };

    loadPreview();
  }, [portfolioId, uploadId]);

  // Validate data with mapping
  const handleValidate = async (mappingConfig: any) => {
    if (!portfolioId || !uploadId) return;

    setCurrentStep('validating');
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/v1/portfolios/${portfolioId}/uploads/${uploadId}/validate`,
        { mapping: mappingConfig }
      );

      setValidationSummary({
        total: response.data.total_rows,
        valid: response.data.valid_rows,
        warnings: response.data.warning_count || 0,
        errors: response.data.error_count || 0,
      });

      setValidationErrors(response.data.validation_errors || []);
      setCurrentStep('mapping'); // Stay on mapping step for now

      toast.success('Validation Complete', {
        description: `${response.data.valid_rows} of ${response.data.total_rows} rows are valid`,
      });
    } catch (err: any) {
      toast.error('Validation Failed', {
        description: err.response?.data?.detail || 'Could not validate data',
      });
      setCurrentStep('failed');
    }
  };

  // Process and import data
  const handleImport = async () => {
    if (!portfolioId || !uploadId) return;

    setProcessing(true);
    setCurrentStep('processing');

    try {
      await axios.post(
        `${BACKEND_URL}/api/v1/portfolios/${portfolioId}/uploads/${uploadId}/process`,
        {
          mapping,
          options: {
            skip_invalid: true,
            auto_enrich: true,
          },
        }
      );

      setCurrentStep('completed');
      toast.success('Import Complete', {
        description: 'Holdings have been successfully imported into the portfolio',
        duration: 7000,
      });

      // Navigate back to portfolio after delay
      setTimeout(() => {
        navigate(`/portfolios/${portfolioId}`);
      }, 2000);
    } catch (err: any) {
      setCurrentStep('failed');
      toast.error('Import Failed', {
        description: err.response?.data?.detail || 'Could not import holdings',
      });
    } finally {
      setProcessing(false);
    }
  };

  // Fix validation error inline
  const handleFixError = async (error: ValidationError, newValue: string) => {
    // TODO: Implement inline error fix via API
    console.log('Fix error:', error, 'New value:', newValue);
    toast.info('Error Fix', {
      description: 'Inline error fixing coming soon',
    });
  };

  // Handle cell edit in preview table
  const handleCellEdit = (rowId: number, column: string, newValue: any) => {
    // TODO: Implement cell edit via API
    console.log('Edit cell:', rowId, column, newValue);
  };

  // Convert preview rows to DataRow format
  const getPreviewData = (): DataRow[] => {
    if (!preview) return [];

    return preview.preview_rows.map((row, index) => ({
      _rowId: index + 1,
      _status: 'valid', // TODO: Get actual status from validation results
      ...row,
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading upload data...</p>
        </div>
      </div>
    );
  }

  if (!preview) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Alert variant="destructive" className="max-w-lg">
          <AlertDescription>Failed to load upload data. Please try again.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background" data-testid="review-page">
      {/* Hero band */}
      <div
        className="relative border-b border-border"
        style={{
          background:
            'radial-gradient(1200px 600px at 12% 20%, hsla(199,89%,56%,0.18), transparent 55%), radial-gradient(900px 500px at 78% 30%, hsla(158,64%,38%,0.12), transparent 60%), linear-gradient(180deg, hsla(210,20%,98%,1), hsla(210,20%,98%,0.0))',
        }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-start justify-between">
            <div>
              <Button
                variant="ghost"
                size="sm"
                className="mb-3 -ml-2"
                onClick={() => navigate(`/portfolios/${portfolioId}/upload`)}
                data-testid="back-to-upload-button"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Upload
              </Button>
              <h1
                className="text-4xl sm:text-5xl font-semibold tracking-tight text-foreground"
                data-testid="review-page-title"
              >
                Review & Import
              </h1>
              <p className="text-base md:text-lg text-muted-foreground mt-2">
                Map columns, validate data, and import holdings
              </p>
              <p className="text-sm text-muted-foreground mt-1 font-mono">
                Upload ID: {uploadId?.slice(-8)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-3 space-y-6">
            <Tabs defaultValue="mapping" className="w-full">
              <TabsList className="grid w-full grid-cols-3" data-testid="review-tabs">
                <TabsTrigger value="mapping" data-testid="tab-mapping">
                  1. Column Mapping
                </TabsTrigger>
                <TabsTrigger value="validation" disabled={!validationSummary} data-testid="tab-validation">
                  2. Validation
                </TabsTrigger>
                <TabsTrigger value="preview" data-testid="tab-preview">
                  3. Preview
                </TabsTrigger>
              </TabsList>

              <TabsContent value="mapping" className="mt-6">
                <ColumnMappingWizard
                  fileColumns={preview.columns}
                  requiredFields={requiredFields}
                  mapping={mapping}
                  suggestions={suggestions}
                  onMappingChange={updateMapping}
                  onAutoMap={applyAutoMapping}
                  onClear={clearMapping}
                  onComplete={completeMapping}
                  onSaveTemplate={saveAsTemplate}
                />
              </TabsContent>

              <TabsContent value="validation" className="mt-6">
                {validationSummary && (
                  <ValidationResultsPanel
                    summary={validationSummary}
                    errors={validationErrors}
                    onFixError={handleFixError}
                  />
                )}
              </TabsContent>

              <TabsContent value="preview" className="mt-6">
                <DataPreviewTable
                  data={getPreviewData()}
                  columns={preview.columns}
                  totalRows={preview.total_rows}
                  page={page}
                  pageSize={pageSize}
                  onPageChange={setPage}
                  onPageSizeChange={setPageSize}
                  onCellEdit={handleCellEdit}
                  onRowSelect={setSelectedRows}
                  selectedRows={selectedRows}
                />
              </TabsContent>
            </Tabs>

            {/* Import Actions */}
            {validationSummary && (
              <div className="flex items-center justify-between p-6 border border-border rounded-xl bg-card">
                <div>
                  <p className="text-sm font-medium">
                    Ready to import {validationSummary.valid} valid holdings
                  </p>
                  {validationSummary.errors > 0 && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {validationSummary.errors} rows with errors will be skipped
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => navigate(`/portfolios/${portfolioId}`)}
                    disabled={processing}
                    data-testid="cancel-import-button"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleImport}
                    disabled={processing || validationSummary.valid === 0}
                    data-testid="import-button"
                  >
                    {processing ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Importing...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="h-4 w-4 mr-2" />
                        Import Holdings
                      </>
                    )}
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Progress Tracker */}
          <div>
            <UploadProgressTracker currentStep={currentStep} />
          </div>
        </div>
      </div>
    </div>
  );
}