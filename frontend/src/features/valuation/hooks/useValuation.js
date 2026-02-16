/**
 * React Query hooks for Real Estate Valuation
 */
import { useQuery, useMutation } from '@tanstack/react-query';
import * as valuationApi from '../api/valuationApi';

// ============ Dashboard ============

export const useDashboardKPIs = () => {
  return useQuery({
    queryKey: ['valuation', 'dashboard'],
    queryFn: valuationApi.getDashboardKPIs,
    staleTime: 30000,
  });
};

// ============ Properties ============

export const useProperties = (params = {}) => {
  return useQuery({
    queryKey: ['valuation', 'properties', params],
    queryFn: () => valuationApi.listProperties(params),
    staleTime: 30000,
  });
};

export const useProperty = (propertyId) => {
  return useQuery({
    queryKey: ['valuation', 'property', propertyId],
    queryFn: () => valuationApi.getProperty(propertyId),
    enabled: !!propertyId,
    staleTime: 30000,
  });
};

// ============ Income Approach ============

export const useDirectCapitalization = () => {
  return useMutation({
    mutationFn: valuationApi.calculateDirectCapitalization,
  });
};

export const useDCF = () => {
  return useMutation({
    mutationFn: valuationApi.calculateDCF,
  });
};

// ============ Cost Approach ============

export const useReplacementCost = () => {
  return useMutation({
    mutationFn: valuationApi.calculateReplacementCost,
  });
};

export const useConstructionCosts = (params = {}) => {
  return useQuery({
    queryKey: ['valuation', 'construction-costs', params],
    queryFn: () => valuationApi.getConstructionCosts(params),
    staleTime: 60000,
  });
};

export const useLocationFactors = () => {
  return useQuery({
    queryKey: ['valuation', 'location-factors'],
    queryFn: valuationApi.getLocationFactors,
    staleTime: 60000,
  });
};

// ============ Sales Comparison ============

export const useSalesComparison = () => {
  return useMutation({
    mutationFn: valuationApi.calculateSalesComparison,
  });
};

export const useComparables = (params = {}) => {
  return useQuery({
    queryKey: ['valuation', 'comparables', params],
    queryFn: () => valuationApi.listComparables(params),
    staleTime: 30000,
  });
};

// ============ Comprehensive Valuation ============

export const useComprehensiveValuation = () => {
  return useMutation({
    mutationFn: valuationApi.runComprehensiveValuation,
  });
};

// ============ Market Data ============

export const useMarketCapRates = (params = {}) => {
  return useQuery({
    queryKey: ['valuation', 'cap-rates', params],
    queryFn: () => valuationApi.getMarketCapRates(params),
    staleTime: 60000,
  });
};

export const useMapData = (params = {}) => {
  return useQuery({
    queryKey: ['valuation', 'map-data', params],
    queryFn: () => valuationApi.getMapData(params),
    staleTime: 30000,
  });
};
