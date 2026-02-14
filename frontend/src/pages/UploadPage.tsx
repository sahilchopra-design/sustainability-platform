import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Upload, FileText } from 'lucide-react';
import { FileUploadZone } from '../components/upload/FileUploadZone';
import { UploadProgressTracker, UploadStep } from '../components/upload/UploadProgressTracker';
import { ImportHistoryList } from '../components/upload/ImportHistoryList';
import { Button } from '../components/ui/button';
import { useFileUpload } from '../hooks/useFileUpload';
import axios from 'axios';
import { UploadStatus } from '../types/upload';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function UploadPage() {
  const { portfolioId } = useParams<{ portfolioId: string }>();
  const navigate = useNavigate();
  const [history, setHistory] = useState<UploadStatus[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [currentUploadId, setCurrentUploadId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<UploadStep>('uploaded');

  const {
    file,
    uploading,
    progress,
    uploadStatus,
    error,
    selectFile,
    uploadFile,
    reset,
    cancelUpload,
  } = useFileUpload({
    portfolioId: portfolioId || 'default',
    onUploadComplete: (uploadId) => {
      setCurrentUploadId(uploadId);
      setCurrentStep('uploaded');
      // Navigate to review page after upload
      setTimeout(() => {
        navigate(`/portfolios/${portfolioId}/upload/${uploadId}/review`);
      }, 1500);
    },
    onError: (err) => {
      setCurrentStep('failed');
    },
  });

  // Load upload history
  useEffect(() => {
    const loadHistory = async () => {
      if (!portfolioId) return;
      
      setLoadingHistory(true);
      try {
        const response = await axios.get<UploadStatus[]>(
          `${BACKEND_URL}/api/v1/portfolios/${portfolioId}/uploads`
        );
        setHistory(response.data);
      } catch (err) {
        console.error('Failed to load upload history:', err);
      } finally {
        setLoadingHistory(false);
      }
    };

    loadHistory();
  }, [portfolioId]);

  const handleViewUpload = (uploadId: string) => {
    navigate(`/portfolios/${portfolioId}/upload/${uploadId}/review`);
  };

  const handleRetryUpload = async (uploadId: string) => {
    // TODO: Implement retry logic
    console.log('Retry upload:', uploadId);
  };

  const handleDeleteUpload = async (uploadId: string) => {
    // TODO: Implement delete logic
    console.log('Delete upload:', uploadId);
  };

  return (
    <div className="min-h-screen bg-background" data-testid="upload-page">
      {/* Hero band with subtle gradient */}
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
              <h1
                className="text-4xl sm:text-5xl font-semibold tracking-tight text-foreground"
                data-testid="upload-page-title"
              >
                Upload Portfolio Holdings
              </h1>
              <p className="text-base md:text-lg text-muted-foreground mt-2">
                Import holdings from CSV or Excel files with automatic validation
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/portfolios/${portfolioId}`)}
              data-testid="back-to-portfolio-button"
            >
              Back to Portfolio
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Upload Zone */}
          <div className="lg:col-span-2 space-y-6">
            <FileUploadZone
              file={file}
              uploading={uploading}
              progress={progress}
              error={error}
              onFileSelect={selectFile}
              onUpload={uploadFile}
              onCancel={cancelUpload}
              onReset={reset}
            />

            {/* Instructions Card */}
            {!file && (
              <div className="border border-border rounded-xl p-6 bg-card">
                <div className="flex items-start gap-4">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <FileText className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-sm font-semibold mb-2">File Requirements</h3>
                    <ul className="text-sm text-muted-foreground space-y-1.5">
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-0.5">•</span>
                        <span>Supported formats: CSV, XLSX, XLS</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-0.5">•</span>
                        <span>Maximum file size: 50MB</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-0.5">•</span>
                        <span>
                          Required columns: Counterparty Name, Exposure Amount
                        </span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-primary mt-0.5">•</span>
                        <span>
                          Optional columns: Currency, Sector, Rating, LEI, ISIN, Country
                        </span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Progress & History */}
          <div className="space-y-6">
            {(uploading || uploadStatus) && (
              <UploadProgressTracker
                currentStep={currentStep}
                error={error}
              />
            )}

            <ImportHistoryList
              uploads={history}
              onView={handleViewUpload}
              onRetry={handleRetryUpload}
              onDelete={handleDeleteUpload}
            />
          </div>
        </div>
      </div>
    </div>
  );
}