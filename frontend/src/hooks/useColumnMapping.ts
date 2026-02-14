import { useState, useCallback, useMemo } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { MappingTemplate } from '../types/upload';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Required fields for portfolio holdings
const REQUIRED_FIELDS = [
  { key: 'counterparty_name', label: 'Counterparty Name', required: true },
  { key: 'exposure', label: 'Exposure Amount', required: true },
  { key: 'currency', label: 'Currency', required: false },
  { key: 'sector', label: 'Sector', required: false },
  { key: 'rating', label: 'Credit Rating', required: false },
  { key: 'lei', label: 'LEI Code', required: false },
  { key: 'isin', label: 'ISIN', required: false },
  { key: 'country', label: 'Country', required: false },
];

export interface ColumnMapping {
  [systemField: string]: string; // system field -> file column name
}

export interface MappingSuggestion {
  systemField: string;
  suggestedColumn: string;
  confidence: number; // 0-100
}

export interface UseColumnMappingOptions {
  uploadId: string;
  fileColumns: string[];
  onMappingComplete?: (mapping: ColumnMapping) => void;
}

export const useColumnMapping = ({ uploadId, fileColumns, onMappingComplete }: UseColumnMappingOptions) => {
  const [mapping, setMapping] = useState<ColumnMapping>({});
  const [templates, setTemplates] = useState<MappingTemplate[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  // Auto-suggest mappings based on column names
  const suggestions = useMemo<MappingSuggestion[]>(() => {
    const results: MappingSuggestion[] = [];

    REQUIRED_FIELDS.forEach((field) => {
      let bestMatch = '';
      let maxConfidence = 0;

      fileColumns.forEach((col) => {
        const colLower = col.toLowerCase().trim();
        const fieldLower = field.key.toLowerCase();
        const labelLower = field.label.toLowerCase();

        let confidence = 0;

        // Exact match
        if (colLower === fieldLower || colLower === labelLower) {
          confidence = 100;
        }
        // Contains match
        else if (colLower.includes(fieldLower) || fieldLower.includes(colLower)) {
          confidence = 80;
        }
        // Partial word match
        else if (colLower.includes(fieldLower.split('_')[0])) {
          confidence = 60;
        }
        // Synonym/common variations
        else {
          const synonyms: Record<string, string[]> = {
            counterparty_name: ['name', 'company', 'entity', 'borrower', 'obligor'],
            exposure: ['amount', 'value', 'balance', 'ead', 'outstanding'],
            currency: ['ccy', 'curr'],
            sector: ['industry', 'vertical'],
            rating: ['grade', 'score'],
            lei: ['legal entity identifier'],
          };

          if (synonyms[field.key]) {
            synonyms[field.key].forEach((syn) => {
              if (colLower.includes(syn)) {
                confidence = Math.max(confidence, 50);
              }
            });
          }
        }

        if (confidence > maxConfidence) {
          maxConfidence = confidence;
          bestMatch = col;
        }
      });

      if (maxConfidence > 40) {
        results.push({
          systemField: field.key,
          suggestedColumn: bestMatch,
          confidence: maxConfidence,
        });
      }
    });

    return results;
  }, [fileColumns]);

  // Apply auto-suggestions
  const applyAutoMapping = useCallback(() => {
    const autoMapping: ColumnMapping = {};
    suggestions.forEach((suggestion) => {
      if (suggestion.confidence >= 60) {
        autoMapping[suggestion.systemField] = suggestion.suggestedColumn;
      }
    });
    setMapping(autoMapping);
    toast.success('Auto-Mapping Applied', {
      description: `${Object.keys(autoMapping).length} fields mapped automatically`,
    });
  }, [suggestions]);

  // Update a single mapping
  const updateMapping = useCallback((systemField: string, fileColumn: string | null) => {
    setMapping((prev) => {
      const newMapping = { ...prev };
      if (fileColumn) {
        newMapping[systemField] = fileColumn;
      } else {
        delete newMapping[systemField];
      }
      return newMapping;
    });
  }, []);

  // Clear all mappings
  const clearMapping = useCallback(() => {
    setMapping({});
  }, []);

  // Validate mapping completeness
  const validateMapping = useCallback((): { valid: boolean; errors: string[] } => {
    const errors: string[] = [];

    REQUIRED_FIELDS.forEach((field) => {
      if (field.required && !mapping[field.key]) {
        errors.push(`${field.label} is required but not mapped`);
      }
    });

    return {
      valid: errors.length === 0,
      errors,
    };
  }, [mapping]);

  // Save mapping as template
  const saveAsTemplate = useCallback(async (name: string, description?: string) => {
    const validation = validateMapping();
    if (!validation.valid) {
      toast.error('Invalid Mapping', {
        description: 'Please complete all required field mappings before saving',
      });
      return;
    }

    try {
      await axios.post(`${BACKEND_URL}/api/v1/mapping-templates`, {
        name,
        description,
        mapping_config: mapping,
        file_format: 'csv', // Infer from upload
      });

      toast.success('Template Saved', {
        description: `Mapping template "${name}" saved successfully`,
      });
    } catch (err: any) {
      toast.error('Save Failed', {
        description: err.response?.data?.detail || 'Could not save template',
      });
    }
  }, [mapping, validateMapping]);

  // Load templates
  const loadTemplates = useCallback(async () => {
    setLoadingTemplates(true);
    try {
      const response = await axios.get<MappingTemplate[]>(`${BACKEND_URL}/api/v1/mapping-templates`);
      setTemplates(response.data);
    } catch (err: any) {
      toast.error('Load Failed', {
        description: 'Could not load mapping templates',
      });
    } finally {
      setLoadingTemplates(false);
    }
  }, []);

  // Apply a saved template
  const applyTemplate = useCallback((template: MappingTemplate) => {
    setMapping(template.mapping_config);
    toast.success('Template Applied', {
      description: `Using mapping template: ${template.name}`,
    });
  }, []);

  // Complete mapping (trigger validation and callback)
  const completeMapping = useCallback(() => {
    const validation = validateMapping();
    if (!validation.valid) {
      toast.error('Incomplete Mapping', {
        description: validation.errors[0],
      });
      return false;
    }

    if (onMappingComplete) {
      onMappingComplete(mapping);
    }
    return true;
  }, [mapping, validateMapping, onMappingComplete]);

  return {
    mapping,
    suggestions,
    templates,
    loadingTemplates,
    requiredFields: REQUIRED_FIELDS,
    updateMapping,
    applyAutoMapping,
    clearMapping,
    validateMapping,
    saveAsTemplate,
    loadTemplates,
    applyTemplate,
    completeMapping,
  };
};