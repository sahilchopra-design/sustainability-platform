// Type definitions for upload system

export interface UploadStatus {
  upload_id: string;
  status: 'uploaded' | 'validating' | 'mapping' | 'processing' | 'completed' | 'failed';
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  processed_rows: number;
  mapping_config?: Record<string, string>;
  validation_results?: ValidationSummary;
  error_message?: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface ValidationSummary {
  total_errors: number;
  total_warnings: number;
  is_valid: boolean;
  error_types: Record<string, number>;
  affected_rows: number;
}

export interface ValidationError {
  row_number?: number;
  column_name?: string;
  error_type: string;
  error_message: string;
  severity: 'error' | 'warning' | 'info';
  original_value?: string;
}

export interface UploadPreview {
  upload_id: string;
  filename: string;
  total_rows: number;
  preview_rows: Array<Record<string, any>>;
  columns: string[];
  mapping?: Record<string, string>;
  statistics?: {
    total_exposure: number;
    currency_distribution: Record<string, number>;
    sector_distribution: Record<string, number>;
    rating_distribution: Record<string, number>;
  };
}

export interface MappingTemplate {
  id: string;
  name: string;
  description?: string;
  mapping_config: Record<string, string>;
  file_format: string;
  usage_count: number;
  created_at: string;
  updated_at: string;
}

export interface ProcessOptions {
  skip_invalid: boolean;
  auto_enrich: boolean;
}
