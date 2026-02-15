/**
 * React Query hooks for Carbon API
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchPortfolios,
  fetchPortfolio,
  fetchPortfolioDashboard,
  createPortfolio,
  updatePortfolio,
  deletePortfolio,
  fetchProjects,
  createProject,
  updateProject,
  deleteProject,
  fetchScenarios,
  createScenario,
  deleteScenario,
  calculateCarbonCredits,
  fetchMethodologies,
  generateReport
} from './carbonApi';

// ============ Portfolio Queries ============

export const useCarbonPortfolios = (params) => {
  return useQuery({
    queryKey: ['carbon-portfolios', params],
    queryFn: () => fetchPortfolios(params),
    staleTime: 5 * 60 * 1000
  });
};

export const useCarbonPortfolio = (portfolioId) => {
  return useQuery({
    queryKey: ['carbon-portfolio', portfolioId],
    queryFn: () => fetchPortfolio(portfolioId),
    enabled: !!portfolioId,
    staleTime: 2 * 60 * 1000
  });
};

export const useCarbonPortfolioDashboard = (portfolioId) => {
  return useQuery({
    queryKey: ['carbon-portfolio-dashboard', portfolioId],
    queryFn: () => fetchPortfolioDashboard(portfolioId),
    enabled: !!portfolioId,
    staleTime: 2 * 60 * 1000
  });
};

export const useCreateCarbonPortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: createPortfolio,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['carbon-portfolios'] });
    }
  });
};

export const useUpdateCarbonPortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }) => updatePortfolio(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['carbon-portfolios'] });
      queryClient.invalidateQueries({ queryKey: ['carbon-portfolio', id] });
    }
  });
};

export const useDeleteCarbonPortfolio = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: deletePortfolio,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['carbon-portfolios'] });
    }
  });
};

// ============ Project Queries ============

export const useCarbonProjects = (params) => {
  return useQuery({
    queryKey: ['carbon-projects', params],
    queryFn: () => fetchProjects(params),
    staleTime: 5 * 60 * 1000
  });
};

export const useCreateCarbonProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: createProject,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['carbon-projects'] });
      queryClient.invalidateQueries({ queryKey: ['carbon-portfolio-dashboard', variables.portfolio_id] });
    }
  });
};

export const useUpdateCarbonProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }) => updateProject(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['carbon-projects'] });
    }
  });
};

export const useDeleteCarbonProject = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['carbon-projects'] });
    }
  });
};

// ============ Scenario Queries ============

export const useCarbonScenarios = (portfolioId) => {
  return useQuery({
    queryKey: ['carbon-scenarios', portfolioId],
    queryFn: () => fetchScenarios(portfolioId),
    enabled: !!portfolioId,
    staleTime: 5 * 60 * 1000
  });
};

export const useCreateCarbonScenario = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ portfolioId, data }) => createScenario(portfolioId, data),
    onSuccess: (_, { portfolioId }) => {
      queryClient.invalidateQueries({ queryKey: ['carbon-scenarios', portfolioId] });
    }
  });
};

export const useDeleteCarbonScenario = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ portfolioId, scenarioId }) => deleteScenario(portfolioId, scenarioId),
    onSuccess: (_, { portfolioId }) => {
      queryClient.invalidateQueries({ queryKey: ['carbon-scenarios', portfolioId] });
    }
  });
};

// ============ Calculation Queries ============

export const useCalculateCarbonCredits = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: calculateCarbonCredits,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['carbon-portfolio-dashboard', variables.portfolio_id] });
    }
  });
};

// ============ Methodology Queries ============

export const useCarbonMethodologies = (params) => {
  return useQuery({
    queryKey: ['carbon-methodologies', params],
    queryFn: () => fetchMethodologies(params),
    staleTime: 60 * 60 * 1000
  });
};

// ============ Report Queries ============

export const useGenerateCarbonReport = () => {
  return useMutation({
    mutationFn: generateReport
  });
};
