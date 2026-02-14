// Custom hook for file upload operations
import { useState, useCallback } from 'react';
import { useToast } from '@/hooks/use-toast';
import type { UploadStatus, UploadPreview, ValidationError } from '@/types/upload';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

export const useFileUpload = (portfolioId: string) => {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus | null>(null);
  const [preview, setPreview] = useState<UploadPreview | null>(null);
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const { toast } = useToast();

  // Upload file
  const uploadFile = useCallback(async (file: File) => {
    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(
        `${API_BASE_URL}/api/v1/uploads?portfolio_id=${portfolioId}`,
        {
          method: 'POST',
          body: formData,
        }
      );
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }
      
      const data = await response.json();
      setUploadStatus(data);
      
      toast({
        title: 'File uploaded successfully',
        description: `${data.total_rows} rows detected`,
      });
      
      return data.upload_id;
    } catch (error) {
      toast({
        title: 'Upload failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
      throw error;
    } finally {
      setUploading(false);
    }
  }, [portfolioId, toast]);

  // Get upload status
  const fetchStatus = useCallback(async (uploadId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/uploads/${uploadId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch status');
      }
      
      const data = await response.json();
      setUploadStatus(data);
      return data;
    } catch (error) {
      console.error('Failed to fetch status:', error);
      throw error;
    }
  }, []);

  // Get preview
  const fetchPreview = useCallback(async (uploadId: string, maxRows: number = 100) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/uploads/${uploadId}/preview?max_rows=${maxRows}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch preview');
      }
      
      const data = await response.json();
      setPreview(data);
      return data;
    } catch (error) {
      console.error('Failed to fetch preview:', error);
      throw error;
    }
  }, []);

  // Get validation errors
  const fetchErrors = useCallback(async (uploadId: string) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/uploads/${uploadId}/errors`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch errors');
      }
      
      const data = await response.json();
      setErrors(data);
      return data;
    } catch (error) {
      console.error('Failed to fetch errors:', error);
      throw error;
    }
  }, []);

  // Update mapping
  const updateMapping = useCallback(async (
    uploadId: string,
    mapping: Record<string, string>
  ) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/uploads/${uploadId}/mapping`,
        {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mapping }),
        }
      );
      
      if (!response.ok) {
        throw new Error('Failed to update mapping');
      }
      
      const data = await response.json();
      setUploadStatus(data);
      
      toast({
        title: 'Mapping updated',
        description: 'Column mapping has been saved',
      });
      
      return data;
    } catch (error) {
      toast({
        title: 'Failed to update mapping',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
      throw error;
    }
  }, [toast]);

  // Process upload
  const processUpload = useCallback(async (
    uploadId: string,
    options: { skip_invalid?: boolean; auto_enrich?: boolean } = {}
  ) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/uploads/${uploadId}/process`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            skip_invalid: options.skip_invalid ?? false,
            auto_enrich: options.auto_enrich ?? true,
          }),
        }
      );
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Processing failed');
      }
      
      const data = await response.json();
      setUploadStatus(data);
      
      toast({
        title: 'Processing started',
        description: 'Your file is being processed in the background',
      });
      
      return data;
    } catch (error) {
      toast({
        title: 'Processing failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
      throw error;
    }
  }, [toast]);

  return {
    uploading,
    uploadStatus,
    preview,
    errors,
    uploadFile,
    fetchStatus,
    fetchPreview,
    fetchErrors,
    updateMapping,
    processUpload,
  };
};
