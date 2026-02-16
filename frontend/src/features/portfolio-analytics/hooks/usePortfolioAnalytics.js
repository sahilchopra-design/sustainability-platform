/**
 * React Query hooks for Portfolio Analytics
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../api/portfolioAnalyticsApi';

/**
 * Hook to fetch all portfolios
 */
export function usePortfolios(params = {}) {
  return useQuery({
    queryKey: ['portfolio-analytics', 'portfolios', params],
    queryFn: () => api.fetchPortfolios(params),
    staleTime: 30000,
  });
}

/**
 * Hook to fetch single portfolio
 */
export function usePortfolio(portfolioId) {
  return useQuery({
    queryKey: ['portfolio-analytics', 'portfolio', portfolioId],
    queryFn: () => api.fetchPortfolio(portfolioId),
    enabled: !!portfolioId,
    staleTime: 30000,
  });
}

/**
 * Hook to fetch portfolio holdings
 */
export function useHoldings(portfolioId) {
  return useQuery({
    queryKey: ['portfolio-analytics', 'holdings', portfolioId],
    queryFn: () => api.fetchHoldings(portfolioId),
    enabled: !!portfolioId,
    staleTime: 30000,
  });
}

/**
 * Hook to fetch portfolio analytics
 */
export function useAnalytics(portfolioId, params = {}) {
  return useQuery({
    queryKey: ['portfolio-analytics', 'analytics', portfolioId, params],
    queryFn: () => api.fetchAnalytics(portfolioId, params),
    enabled: !!portfolioId,
    staleTime: 60000,
  });
}

/**
 * Hook to fetch portfolio dashboard
 */
export function useDashboard(portfolioId, params = {}) {
  return useQuery({
    queryKey: ['portfolio-analytics', 'dashboard', portfolioId, params],
    queryFn: () => api.fetchDashboard(portfolioId, params),
    enabled: !!portfolioId,
    staleTime: 60000,
  });
}

/**
 * Hook to fetch enum values
 */
export function useEnums() {
  return useQuery({
    queryKey: ['portfolio-analytics', 'enums'],
    queryFn: api.fetchEnums,
    staleTime: Infinity,
  });
}

/**
 * Hook to create portfolio
 */
export function useCreatePortfolio() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.createPortfolio,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio-analytics', 'portfolios'] });
    },
  });
}

/**
 * Hook to update portfolio
 */
export function useUpdatePortfolio() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ portfolioId, data }) => api.updatePortfolio(portfolioId, data),
    onSuccess: (_, { portfolioId }) => {
      queryClient.invalidateQueries({ queryKey: ['portfolio-analytics', 'portfolios'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio-analytics', 'portfolio', portfolioId] });
    },
  });
}

/**
 * Hook to compare scenarios
 */
export function useCompareScenarios() {
  return useMutation({
    mutationFn: ({ portfolioId, data }) => api.compareScenarios(portfolioId, data),
  });
}

/**
 * Hook to generate report
 */
export function useGenerateReport() {
  return useMutation({
    mutationFn: ({ portfolioId, data }) => api.generateReport(portfolioId, data),
  });
}

/**
 * Hook to seed sample data
 */
export function useSeedSampleData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.seedSampleData,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio-analytics'] });
    },
  });
}
