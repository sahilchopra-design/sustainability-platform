import React, { useCallback, useRef } from 'react';
import { Upload, FileText, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription } from '../ui/alert';
import { cn } from '../../lib/utils';

export interface FileUploadZoneProps {
  file: File | null;
  uploading: boolean;
  progress: number;
  error: string | null;
  onFileSelect: (file: File) => boolean;
  onUpload: () => void;
  onCancel: () => void;
  onReset: () => void;
}

export const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  file,
  uploading,
  progress,
  error,
  onFileSelect,
  onUpload,
  onCancel,
  onReset,
}) => {
  const [dragActive, setDragActive] = React.useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        onFileSelect(e.dataTransfer.files[0]);
      }
    },
    [onFileSelect]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      e.preventDefault();
      if (e.target.files && e.target.files[0]) {
        onFileSelect(e.target.files[0]);
      }
    },
    [onFileSelect]
  );

  const handleButtonClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="w-full" data-testid="file-upload-zone">
      {error && (
        <Alert variant="destructive" className="mb-4" data-testid="upload-error-alert">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!file ? (
        <div
          className={cn(
            'relative flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-xl transition-colors cursor-pointer',
            dragActive
              ? 'border-primary bg-primary/5'
              : 'border-border bg-card hover:border-primary/50 hover:bg-accent/5'
          )}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={handleButtonClick}
          data-testid="upload-dropzone"
        >
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".csv,.xlsx,.xls"
            onChange={handleChange}
            data-testid="upload-file-input"
          />
          <Upload className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-base font-medium text-foreground mb-1">
            Drag and drop your file here
          </p>
          <p className="text-sm text-muted-foreground mb-4">or click to browse</p>
          <Button variant="secondary" size="sm" data-testid="upload-browse-button">
            Browse Files
          </Button>
          <p className="text-xs text-muted-foreground mt-4">
            Supports CSV, XLSX, XLS • Max 50MB
          </p>
        </div>
      ) : (
        <div className="border border-border rounded-xl p-6 bg-card" data-testid="upload-file-selected">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-lg bg-primary/10">
              <FileText className="h-6 w-6 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-medium text-foreground truncate" data-testid="upload-file-name">
                  {file.name}
                </p>
                {!uploading && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={onReset}
                    data-testid="upload-remove-file-button"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
              <p className="text-xs text-muted-foreground" data-testid="upload-file-size">
                {formatFileSize(file.size)}
              </p>

              {uploading && (
                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Uploading...</span>
                    <span className="font-medium tabular-nums" data-testid="upload-progress-percent">
                      {progress}%
                    </span>
                  </div>
                  <Progress value={progress} className="h-2" data-testid="upload-progress-bar" />
                </div>
              )}

              {!uploading && progress === 100 && (
                <div className="mt-3 flex items-center gap-2 text-sm text-[hsl(var(--success))]">
                  <CheckCircle2 className="h-4 w-4" />
                  <span>Upload complete</span>
                </div>
              )}
            </div>
          </div>

          {!uploading && progress === 0 && (
            <div className="flex gap-2 mt-6">
              <Button
                onClick={onUpload}
                className="flex-1"
                data-testid="upload-start-button"
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload File
              </Button>
              <Button variant="outline" onClick={onReset} data-testid="upload-cancel-button">
                Cancel
              </Button>
            </div>
          )}

          {uploading && (
            <div className="mt-6">
              <Button
                variant="outline"
                onClick={onCancel}
                className="w-full"
                data-testid="upload-cancel-upload-button"
              >
                Cancel Upload
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};