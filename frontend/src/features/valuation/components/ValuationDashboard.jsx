/**
 * Real Estate Valuation Dashboard
 * Displays portfolio summary and key metrics
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { 
  Building2, DollarSign, TrendingUp, Calculator, 
  BarChart3, PieChart, Home, Factory
} from 'lucide-react';
import { useDashboardKPIs, useProperties } from '../../hooks/useValuation';

const formatCurrency = (value, compact = false) => {
  if (!value) return '$0';
  const num = parseFloat(value);
  if (compact && num >= 1000000000) {
    return `$${(num / 1000000000).toFixed(2)}B`;
  } else if (compact && num >= 1000000) {
    return `$${(num / 1000000).toFixed(1)}M`;
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num);
};

const formatPercent = (value) => {
  if (!value) return '0%';
  return `${(parseFloat(value) * 100).toFixed(2)}%`;
};

const PropertyTypeIcon = ({ type }) => {
  const icons = {
    office: Building2,
    retail: Home,
    industrial: Factory,
    multifamily: Building2,
    hotel: Building2,
  };
  const Icon = icons[type] || Building2;
  return <Icon className="h-4 w-4" />;
};

export function ValuationDashboard() {
  const { data: kpis, isLoading: kpisLoading } = useDashboardKPIs();
  const { data: propertiesData, isLoading: propsLoading } = useProperties();

  if (kpisLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  const properties = propertiesData?.items || [];

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-emerald-50 to-white border-emerald-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2 text-emerald-700">
              <DollarSign className="h-4 w-4" />
              Portfolio Value
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-emerald-900">
              {formatCurrency(kpis?.total_portfolio_value, true)}
            </p>
            <p className="text-xs text-emerald-600">
              {kpis?.total_properties || 0} properties tracked
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-white border-blue-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2 text-blue-700">
              <TrendingUp className="h-4 w-4" />
              Avg Cap Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-blue-900">
              {formatPercent(kpis?.avg_cap_rate)}
            </p>
            <p className="text-xs text-blue-600">
              Portfolio weighted average
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-violet-50 to-white border-violet-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2 text-violet-700">
              <BarChart3 className="h-4 w-4" />
              Avg Value/SF
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-violet-900">
              ${parseFloat(kpis?.avg_value_per_sf || 0).toFixed(0)}
            </p>
            <p className="text-xs text-violet-600">
              Per square foot
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-50 to-white border-amber-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2 text-amber-700">
              <Calculator className="h-4 w-4" />
              Total Valuations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-amber-900">
              {kpis?.total_valuations || 0}
            </p>
            <p className="text-xs text-amber-600">
              Across all approaches
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Property Type Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5 text-slate-500" />
              Properties by Type
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(kpis?.properties_by_type || {}).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <PropertyTypeIcon type={type} />
                    <span className="capitalize text-sm font-medium">
                      {type.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-32 bg-slate-100 rounded-full h-2">
                      <div 
                        className="bg-emerald-500 h-2 rounded-full" 
                        style={{ 
                          width: `${(count / (kpis?.total_properties || 1)) * 100}%` 
                        }}
                      />
                    </div>
                    <span className="text-sm text-slate-600 w-8 text-right">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5 text-slate-500" />
              Valuations by Method
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(kpis?.valuations_by_method || {}).map(([method, count]) => {
                const colors = {
                  direct_capitalization: 'bg-blue-500',
                  dcf: 'bg-violet-500',
                  cost: 'bg-amber-500',
                  sales_comparison: 'bg-emerald-500',
                };
                return (
                  <div key={method} className="flex items-center justify-between">
                    <span className="capitalize text-sm font-medium">
                      {method.replace('_', ' ')}
                    </span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-slate-100 rounded-full h-2">
                        <div 
                          className={`${colors[method] || 'bg-slate-500'} h-2 rounded-full`} 
                          style={{ 
                            width: `${(count / (kpis?.total_valuations || 1)) * 100}%` 
                          }}
                        />
                      </div>
                      <span className="text-sm text-slate-600 w-8 text-right">{count}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Property List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-slate-500" />
            Property Portfolio
          </CardTitle>
        </CardHeader>
        <CardContent>
          {propsLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-slate-500"></div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-2 text-sm font-medium text-slate-600">Property</th>
                    <th className="text-left py-3 px-2 text-sm font-medium text-slate-600">Type</th>
                    <th className="text-left py-3 px-2 text-sm font-medium text-slate-600">Location</th>
                    <th className="text-right py-3 px-2 text-sm font-medium text-slate-600">Size (SF)</th>
                    <th className="text-right py-3 px-2 text-sm font-medium text-slate-600">Market Value</th>
                    <th className="text-right py-3 px-2 text-sm font-medium text-slate-600">Cap Rate</th>
                    <th className="text-center py-3 px-2 text-sm font-medium text-slate-600">Quality</th>
                  </tr>
                </thead>
                <tbody>
                  {properties.map((property) => (
                    <tr 
                      key={property.id} 
                      className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-2">
                        <div className="font-medium text-sm">{property.property_name}</div>
                        <div className="text-xs text-slate-500">{property.address}</div>
                      </td>
                      <td className="py-3 px-2">
                        <Badge variant="outline" className="capitalize">
                          {property.property_type?.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td className="py-3 px-2 text-sm text-slate-600">
                        {property.city}, {property.state_province}
                      </td>
                      <td className="py-3 px-2 text-sm text-right">
                        {parseFloat(property.rentable_area_sf || 0).toLocaleString()}
                      </td>
                      <td className="py-3 px-2 text-sm text-right font-medium">
                        {formatCurrency(property.market_value, true)}
                      </td>
                      <td className="py-3 px-2 text-sm text-right">
                        {formatPercent(property.cap_rate)}
                      </td>
                      <td className="py-3 px-2 text-center">
                        <Badge 
                          className={
                            property.quality_rating === 'class_a' 
                              ? 'bg-emerald-100 text-emerald-800' 
                              : property.quality_rating === 'class_b'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-slate-100 text-slate-800'
                          }
                        >
                          {property.quality_rating?.replace('class_', 'Class ').toUpperCase()}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default ValuationDashboard;
