import { useState, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { UploadStatus } from '../types/upload';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
const ALLOWED_TYPES = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];

export interface UseFileUploadOptions {
  portfolioId: string;
  onUploadComplete?: (uploadId: string) => void;
  onError?: (error: string) => void;
}

export const useFileUpload = ({ portfolioId, onUploadComplete, onError }: UseFileUploadOptions) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback((file: File): { valid: boolean; error?: string } => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return { valid: false, error: `File size exceeds ${MAX_FILE_SIZE / (1024 * 1024)}MB limit` };
    }

    // Check file type
    if (!ALLOWED_TYPES.includes(file.type) && !file.name.match(/\.(csv|xlsx|xls)$/i)) {
      return { valid: false, error: 'File type not supported. Please upload CSV or Excel files.' };
    }

    return { valid: true };
  }, []);

  const selectFile = useCallback((selectedFile: File) => {
    const validation = validateFile(selectedFile);
    
    if (!validation.valid) {
      setError(validation.error!);
      toast.error('Invalid File', {
        description: validation.error,
        duration: 5000,
      });
      return false;
    }

    setFile(selectedFile);
    setError(null);
    return true;
  }, [validateFile]);

  const uploadFile = useCallback(async () => {
    if (!file) {
      setError('No file selected');
      return;
    }

    setUploading(true);
    setProgress(0);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post<UploadStatus>(
        `${BACKEND_URL}/api/v1/portfolios/${portfolioId}/upload`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setProgress(percentCompleted);
            }
          },
        }
      );

      setUploadStatus(response.data);
      toast.success('Upload Complete', {
        description: `${file.name} uploaded successfully. ${response.data.total_rows} rows detected.`,
        duration: 5000,
      });

      if (onUploadComplete) {
        onUploadComplete(response.data.upload_id);
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Upload failed';
      setError(errorMsg);
      toast.error('Upload Failed', {
        description: errorMsg,
        duration: 7000,
      });
      
      if (onError) {
        onError(errorMsg);
      }
    } finally {
      setUploading(false);
    }
  }, [file, portfolioId, onUploadComplete, onError]);

  const reset = useCallback(() => {
    setFile(null);
    setUploading(false);
    setProgress(0);
    setUploadStatus(null);
    setError(null);
  }, []);

  const cancelUpload = useCallback(() => {
    // TODO: Implement axios cancel token
    reset();
    toast.info('Upload Cancelled');
  }, [reset]);

  return {
    file,
    uploading,
    progress,
    uploadStatus,
    error,
    selectFile,
    uploadFile,
    reset,
    cancelUpload,
    validateFile,
  };
};