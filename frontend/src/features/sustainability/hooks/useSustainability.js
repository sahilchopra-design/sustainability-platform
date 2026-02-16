/**
 * React hooks for Sustainability Frameworks
 */
import { useQuery, useMutation } from '@tanstack/react-query';
import * as api from '../api/sustainabilityApi';

// Dashboard
export function useSustainabilityDashboard() {
  return useQuery({
    queryKey: ['sustainability', 'dashboard'],
    queryFn: () => api.getDashboard().then((r) => r.data),
  });
}

// Certifications
export function useCertifications(params) {
  return useQuery({
    queryKey: ['sustainability', 'certifications', params],
    queryFn: () => api.getCertifications(params).then((r) => r.data),
  });
}

export function useCertification(id) {
  return useQuery({
    queryKey: ['sustainability', 'certification', id],
    queryFn: () => api.getCertification(id).then((r) => r.data),
    enabled: !!id,
  });
}

// GRESB Assessment
export function useGRESBAssessment() {
  return useMutation({
    mutationFn: (data) => api.calculateGRESB(data).then((r) => r.data),
  });
}

export function useGRESBBenchmarks(region) {
  return useQuery({
    queryKey: ['sustainability', 'gresb', 'benchmarks', region],
    queryFn: () => api.getGRESBBenchmarks(region).then((r) => r.data),
  });
}

// LEED Assessment
export function useLEEDAssessment() {
  return useMutation({
    mutationFn: (data) => api.calculateLEED(data).then((r) => r.data),
  });
}

export function useLEEDThresholds() {
  return useQuery({
    queryKey: ['sustainability', 'leed', 'thresholds'],
    queryFn: () => api.getLEEDThresholds().then((r) => r.data),
  });
}

// BREEAM Assessment
export function useBREEAMAssessment() {
  return useMutation({
    mutationFn: (data) => api.calculateBREEAM(data).then((r) => r.data),
  });
}

// Alias for BREEAMCalculator component
export function useBREEAMCalculator() {
  return useMutation({
    mutationFn: (data) => api.calculateBREEAM(data).then((r) => r.data),
  });
}

// Alias for LEED calculator in comparison
export function useLEEDCalculator() {
  return useMutation({
    mutationFn: (data) => api.calculateLEED(data).then((r) => r.data),
  });
}

export function useBREEAMWeights() {
  return useQuery({
    queryKey: ['sustainability', 'breeam', 'weights'],
    queryFn: () => api.getBREEAMWeights().then((r) => r.data),
  });
}

// Value Impact
export function useValueImpact() {
  return useMutation({
    mutationFn: (data) => api.calculateValueImpact(data).then((r) => r.data),
  });
}

export function useBenchmarks(params) {
  return useQuery({
    queryKey: ['sustainability', 'benchmarks', params],
    queryFn: () => api.getBenchmarks(params).then((r) => r.data),
  });
}

// Portfolio Analysis
export function usePortfolioAnalysis() {
  return useMutation({
    mutationFn: (data) => api.analyzePortfolio(data).then((r) => r.data),
  });
}

// Comparison Tool
export function useCertificationComparison() {
  return useMutation({
    mutationFn: (data) => api.compareCertifications(data).then((r) => r.data),
  });
}

// Enums
export function useEnums() {
  return useQuery({
    queryKey: ['sustainability', 'enums'],
    queryFn: () => api.getEnums().then((r) => r.data),
    staleTime: Infinity,
  });
}
