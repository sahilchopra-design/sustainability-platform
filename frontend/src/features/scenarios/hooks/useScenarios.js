/**
 * React hooks for Scenario Analysis
 */
import { useQuery, useMutation } from '@tanstack/react-query';
import * as api from '../api/scenarioApi';

// Dashboard
export function useScenarioDashboard() {
  return useQuery({
    queryKey: ['scenarios', 'dashboard'],
    queryFn: () => api.getScenarioDashboard().then((r) => r.data),
  });
}

// Scenario Builder
export function useBuildScenario() {
  return useMutation({
    mutationFn: (data) => api.buildScenario(data).then((r) => r.data),
  });
}

export function useScenarios(params) {
  return useQuery({
    queryKey: ['scenarios', 'list', params],
    queryFn: () => api.listScenarios(params).then((r) => r.data),
  });
}

export function useScenario(id) {
  return useQuery({
    queryKey: ['scenarios', id],
    queryFn: () => api.getScenario(id).then((r) => r.data),
    enabled: !!id,
  });
}

export function useCompareScenarios() {
  return useMutation({
    mutationFn: (data) => api.compareScenarios(data).then((r) => r.data),
  });
}

// Templates
export function useTemplates() {
  return useQuery({
    queryKey: ['scenarios', 'templates'],
    queryFn: () => api.getTemplates().then((r) => r.data),
  });
}

export function useApplyTemplate() {
  return useMutation({
    mutationFn: ({ propertyId, templateName }) => 
      api.applyTemplate(propertyId, templateName).then((r) => r.data),
  });
}

// Properties
export function useProperties() {
  return useQuery({
    queryKey: ['scenarios', 'properties'],
    queryFn: () => api.getProperties().then((r) => r.data),
  });
}

// Sensitivity Analysis
export function useSensitivityAnalysis() {
  return useMutation({
    mutationFn: (data) => api.analyzeSensitivity(data).then((r) => r.data),
  });
}

export function useTornadoChart() {
  return useMutation({
    mutationFn: (data) => api.generateTornado(data).then((r) => r.data),
  });
}

export function useSpiderChart() {
  return useMutation({
    mutationFn: (data) => api.generateSpider(data).then((r) => r.data),
  });
}

export function useSensitivityPresets() {
  return useQuery({
    queryKey: ['sensitivity', 'presets'],
    queryFn: () => api.getSensitivityPresets().then((r) => r.data),
  });
}

// What-If Analysis
export function useWhatIfAnalysis() {
  return useMutation({
    mutationFn: (data) => api.analyzeWhatIf(data).then((r) => r.data),
  });
}

export function useWhatIfParameters() {
  return useQuery({
    queryKey: ['whatif', 'parameters'],
    queryFn: () => api.getWhatIfParameters().then((r) => r.data),
  });
}
