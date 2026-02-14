// Custom hook for column mapping
import { useState, useCallback } from 'react';
import type { MappingTemplate } from '@/types/upload';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '';

export const useColumnMapping = () => {
  const [templates, setTemplates] = useState<MappingTemplate[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch mapping templates
  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/uploads/templates`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch templates');
      }
      
      const data = await response.json();
      setTemplates(data);
      return data;
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  // Save mapping template
  const saveTemplate = useCallback(async (
    name: string,
    description: string,
    mapping: Record<string, string>,
    fileFormat: string
  ) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/uploads/templates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          description,
          mapping_config: mapping,
          file_format: fileFormat,
        }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to save template');
      }
      
      const data = await response.json();
      setTemplates(prev => [data, ...prev]);
      return data;
    } catch (error) {
      console.error('Failed to save template:', error);
      throw error;
    }
  }, []);

  // Calculate confidence score for auto-mapping
  const getConfidenceScore = useCallback((
    uploadedColumn: string,
    standardField: string
  ): number => {
    const normalizedUpload = uploadedColumn.toLowerCase().replace(/[_\s]/g, '');
    const normalizedStandard = standardField.toLowerCase().replace(/[_\s]/g, '');
    
    // Exact match
    if (normalizedUpload === normalizedStandard) return 100;
    
    // Contains match
    if (normalizedUpload.includes(normalizedStandard) || 
        normalizedStandard.includes(normalizedUpload)) {
      return 85;
    }
    
    // Partial match (Levenshtein-like)
    const maxLen = Math.max(normalizedUpload.length, normalizedStandard.length);
    const distance = levenshteinDistance(normalizedUpload, normalizedStandard);
    const similarity = ((maxLen - distance) / maxLen) * 100;
    
    return Math.round(similarity);
  }, []);

  return {
    templates,
    loading,
    fetchTemplates,
    saveTemplate,
    getConfidenceScore,
  };
};

// Levenshtein distance helper
function levenshteinDistance(str1: string, str2: string): number {
  const matrix: number[][] = [];
  
  for (let i = 0; i <= str2.length; i++) {
    matrix[i] = [i];
  }
  
  for (let j = 0; j <= str1.length; j++) {
    matrix[0][j] = j;
  }
  
  for (let i = 1; i <= str2.length; i++) {
    for (let j = 1; j <= str1.length; j++) {
      if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }
  
  return matrix[str2.length][str1.length];
}
