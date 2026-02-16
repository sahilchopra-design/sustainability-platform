/**
 * Portfolio Analytics Dashboard Component
 * Displays KPI cards, charts, and alerts for a selected portfolio
 */
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import { Badge } from '../../../components/ui/badge';
import { Skeleton } from '../../../components/ui/skeleton';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';
import {
  DollarSign, Building2, AlertTriangle, TrendingDown, AlertCircle,
  Leaf, Award, Percent, ArrowUp, ArrowDown
} from 'lucide-react';
import { ExportButton } from '../../../components/shared/ExportButton';
import { exportPortfolioAnalytics } from '../../../lib/exportUtils';

const COLORS = ['#0ea5e9', '#8b5cf6', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4'];

const ICON_MAP = {
  DollarSign: DollarSign,
  Building2: Building2,
  AlertTriangle: AlertTriangle,
  TrendingDown: TrendingDown,
  AlertCircle: AlertCircle,
  Leaf: Leaf,
  Award: Award,
  Percent: Percent,
};

const COLOR_MAP = {
  emerald: 'bg-emerald-100 text-emerald-700',
  blue: 'bg-blue-100 text-blue-700',
  red: 'bg-red-100 text-red-700',
  amber: 'bg-amber-100 text-amber-700',
  violet: 'bg-violet-100 text-violet-700',
};

function formatValue(value) {
  if (typeof value === 'number') {
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
    if (value % 1 !== 0) return value.toFixed(2);
    return value.toString();
  }
  return value;
}

function KPICard({ kpi }) {
  const Icon = ICON_MAP[kpi.icon] || DollarSign;
  const colorClass = COLOR_MAP[kpi.color] || 'bg-slate-100 text-slate-700';
  
  return (
    <Card className="bg-white hover:shadow-md transition-shadow" data-testid={`kpi-${kpi.id}`}>
      <CardContent className="pt-4 pb-3">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs text-slate-500 mb-1">{kpi.label}</p>
            <p className="text-xl font-bold text-slate-900">{formatValue(kpi.value)}</p>
            {kpi.change !== null && kpi.change !== undefined && (
              <div className="flex items-center gap-1 mt-1">
                {kpi.trend === 'up' ? (
                  <ArrowUp className="h-3 w-3 text-emerald-500" />
                ) : kpi.trend === 'down' ? (
                  <ArrowDown className="h-3 w-3 text-red-500" />
                ) : null}
                <span className={`text-xs ${kpi.trend === 'up' ? 'text-emerald-600' : kpi.trend === 'down' ? 'text-red-600' : 'text-slate-500'}`}>
                  {kpi.change > 0 ? '+' : ''}{kpi.change}% {kpi.change_period}
                </span>
              </div>
            )}
          </div>
          <div className={`p-2 rounded-lg ${colorClass}`}>
            <Icon className="h-4 w-4" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SectorAllocationChart({ data }) {
  if (!data || data.length === 0) return null;
  
  return (
    <Card className="bg-white" data-testid="chart-sector-allocation">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-slate-700">Sector Allocation</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={75}
                dataKey="value"
                nameKey="name"
                paddingAngle={2}
              >
                {data.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => `${value.toFixed(1)}%`}
                contentStyle={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '6px' }}
              />
              <Legend iconSize={8} wrapperStyle={{ fontSize: '11px' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

function GeographicChart({ data }) {
  if (!data || data.length === 0) return null;
  
  return (
    <Card className="bg-white" data-testid="chart-geographic">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-slate-700">Geographic Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tickFormatter={(v) => `$${v.toFixed(0)}M`} tick={{ fontSize: 10 }} />
              <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} width={70} />
              <Tooltip
                formatter={(value) => `$${value.toFixed(1)}M`}
                contentStyle={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '6px' }}
              />
              <Bar dataKey="value" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

function RiskDistributionChart({ data }) {
  if (!data || data.length === 0) return null;
  
  return (
    <Card className="bg-white" data-testid="chart-risk-distribution">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-slate-700">Risk Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[200px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 9 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '6px' }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {data.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

function AlertsList({ alerts }) {
  if (!alerts || alerts.length === 0) return null;
  
  const severityColors = {
    critical: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800',
  };
  
  const severityIcons = {
    critical: AlertCircle,
    warning: AlertTriangle,
    info: AlertCircle,
  };
  
  return (
    <Card className="bg-white" data-testid="alerts-list">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold text-slate-700 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          Alerts & Notifications
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {alerts.map((alert) => {
          const Icon = severityIcons[alert.severity] || AlertCircle;
          return (
            <div
              key={alert.id}
              className={`p-3 rounded-lg border ${severityColors[alert.severity] || severityColors.info}`}
            >
              <div className="flex items-start gap-2">
                <Icon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium text-sm">{alert.title}</p>
                  <p className="text-xs mt-0.5 opacity-80">{alert.message}</p>
                  {alert.action_required && (
                    <Badge variant="outline" className="mt-2 text-[10px]">Action Required</Badge>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

export function PortfolioDashboard({ dashboard, isLoading }) {
  if (isLoading) {
    return (
      <div className="space-y-6" data-testid="dashboard-loading">
        {/* KPI Skeleton */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-lg" />
          ))}
        </div>
        {/* Charts Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-64 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }
  
  if (!dashboard) {
    return (
      <Card className="bg-white">
        <CardContent className="py-12 text-center text-slate-500">
          <p>No dashboard data available. Select a portfolio to view analytics.</p>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <div className="space-y-6" data-testid="portfolio-dashboard">
      {/* Portfolio Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">{dashboard.portfolio_name}</h2>
          <p className="text-xs text-slate-500">
            Last updated: {new Date(dashboard.last_updated).toLocaleString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
            {dashboard.property_count} Properties
          </Badge>
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            AUM: ${(parseFloat(dashboard.total_aum) / 1e9).toFixed(2)}B
          </Badge>
          <ExportButton 
            onExport={(format) => exportPortfolioAnalytics(dashboard.portfolio_id, format, 'executive')}
            label="Export"
            data-testid="portfolio-export-btn"
          />
        </div>
      </div>
      
      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {dashboard.kpi_cards.map((kpi) => (
          <KPICard key={kpi.id} kpi={kpi} />
        ))}
      </div>
      
      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {dashboard.charts?.sector_allocation && (
          <SectorAllocationChart data={dashboard.charts.sector_allocation.data} />
        )}
        {dashboard.charts?.geographic_distribution && (
          <GeographicChart data={dashboard.charts.geographic_distribution.data} />
        )}
        {dashboard.charts?.risk_distribution && (
          <RiskDistributionChart data={dashboard.charts.risk_distribution.data} />
        )}
      </div>
      
      {/* Alerts */}
      {dashboard.alerts && dashboard.alerts.length > 0 && (
        <AlertsList alerts={dashboard.alerts} />
      )}
    </div>
  );
}
