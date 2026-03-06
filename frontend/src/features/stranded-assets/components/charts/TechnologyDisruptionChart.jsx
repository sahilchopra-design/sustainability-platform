import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../../components/ui/card';
import { Badge } from '../../../../components/ui/badge';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, Area, AreaChart, ReferenceLine
} from 'recharts';
import { TrendingUp, Zap, Fuel, Flame, Battery, Car, Home } from 'lucide-react';
import { useTechnologyDisruption } from '../../hooks/useStrandedAssets';

const METRIC_CONFIG = {
  ev: {
    label: 'EV Adoption',
    description: 'Electric vehicle sales share by region',
    icon: Car,
    color: '#3b82f6',
    unit: '%'
  },
  heat_pump: {
    label: 'Heat Pump Adoption',
    description: 'Heat pump installations displacing gas heating',
    icon: Home,
    color: '#10b981',
    unit: '%'
  },
  hydrogen: {
    label: 'Green Hydrogen Cost',
    description: 'Levelized cost of green hydrogen production',
    icon: Zap,
    color: '#8b5cf6',
    unit: '$/kg'
  },
  battery: {
    label: 'Battery Cost',
    description: 'Lithium-ion battery pack cost trajectory',
    icon: Battery,
    color: '#f59e0b',
    unit: '$/kWh'
  }
};

const REGION_OPTIONS = [
  { value: 'global', label: 'Global' },
  { value: 'europe', label: 'Europe' },
  { value: 'china', label: 'China' },
  { value: 'us', label: 'United States' },
  { value: 'india', label: 'India' },
];

export function TechnologyDisruptionChart() {
  const [selectedMetric, setSelectedMetric] = useState('ev');
  const [selectedRegion, setSelectedRegion] = useState('global');
  const [selectedYear, setSelectedYear] = useState(2035);

  const { data, loading, error } = useTechnologyDisruption(selectedMetric, { 
    region: selectedRegion,
    year: selectedYear 
  });

  const config = METRIC_CONFIG[selectedMetric];
  const Icon = config?.icon || TrendingUp;

  const chartData = useMemo(() => {
    if (!data?.chart_data) return [];
    return data.chart_data.map(item => ({
      ...item,
      value: parseFloat(item.value)
    }));
  }, [data]);

  return (
    <div className="space-y-6" data-testid="technology-disruption-chart">
      {/* Metric Selector */}
      <div className="flex flex-wrap gap-3">
        {Object.entries(METRIC_CONFIG).map(([key, cfg]) => {
          const MetricIcon = cfg.icon;
          return (
            <button
              key={key}
              onClick={() => setSelectedMetric(key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                selectedMetric === key
                  ? 'bg-amber-500 text-white shadow-lg scale-105'
                  : 'bg-white/[0.06] dark:bg-[#111827] hover:bg-white/[0.08] dark:hover:bg-[#1a2234]'
              }`}
            >
              <MetricIcon className="h-4 w-4" />
              {cfg.label}
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg" style={{ backgroundColor: `${config?.color}20` }}>
                  <Icon className="h-5 w-5" style={{ color: config?.color }} />
                </div>
                <div>
                  <CardTitle>{config?.label}</CardTitle>
                  <CardDescription>{config?.description}</CardDescription>
                </div>
              </div>
              <select
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value)}
                className="border rounded-lg px-3 py-1.5 text-sm bg-[#0d1424] dark:bg-[#111827]"
              >
                {REGION_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-64 text-red-500">
                Error loading data: {error}
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id={`gradient-${selectedMetric}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={config?.color} stopOpacity={0.3}/>
                      <stop offset="95%" stopColor={config?.color} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="year" 
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                  />
                  <YAxis 
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    tickFormatter={(val) => `${val}${config?.unit === '%' ? '%' : ''}`}
                  />
                  <Tooltip 
                    formatter={(value) => [`${value.toFixed(1)}${config?.unit}`, config?.label]}
                    labelFormatter={(label) => `Year: ${label}`}
                    contentStyle={{ 
                      borderRadius: '8px', 
                      border: '1px solid #e5e7eb',
                      boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)'
                    }}
                  />
                  <ReferenceLine 
                    x={2030} 
                    stroke="#f59e0b" 
                    strokeDasharray="5 5" 
                    label={{ value: '2030', position: 'top', fill: '#f59e0b', fontSize: 10 }}
                  />
                  <ReferenceLine 
                    x={2050} 
                    stroke="#10b981" 
                    strokeDasharray="5 5"
                    label={{ value: '2050', position: 'top', fill: '#10b981', fontSize: 10 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="value"
                    stroke={config?.color}
                    strokeWidth={3}
                    fill={`url(#gradient-${selectedMetric})`}
                    dot={false}
                    activeDot={{ r: 6, stroke: config?.color, strokeWidth: 2, fill: 'white' }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Key Metrics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Key Projections</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading ? (
              <div className="flex items-center justify-center h-48">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-amber-500"></div>
              </div>
            ) : (
              <>
                {/* Current Value */}
                <div className="p-4 bg-white/[0.02] dark:bg-[#111827] rounded-lg">
                  <p className="text-xs text-white/40 mb-1">Current ({data?.current_year})</p>
                  <p className="text-2xl font-bold" style={{ color: config?.color }}>
                    {parseFloat(data?.current_value || 0).toFixed(1)}{config?.unit}
                  </p>
                </div>

                {/* 2030 Projection */}
                <div className="p-4 bg-amber-500/10 dark:bg-amber-900/20 rounded-lg border border-amber-500/20 dark:border-amber-800">
                  <p className="text-xs text-white/40 mb-1">2030 Projection</p>
                  <p className="text-2xl font-bold text-amber-400">
                    {parseFloat(data?.projected_2030 || 0).toFixed(1)}{config?.unit}
                  </p>
                </div>

                {/* 2040 Projection */}
                <div className="p-4 bg-blue-500/10 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-xs text-white/40 mb-1">2040 Projection</p>
                  <p className="text-2xl font-bold text-blue-300">
                    {parseFloat(data?.projected_2040 || 0).toFixed(1)}{config?.unit}
                  </p>
                </div>

                {/* 2050 Projection */}
                <div className="p-4 bg-emerald-500/10 dark:bg-emerald-900/20 rounded-lg border border-emerald-500/20 dark:border-emerald-800">
                  <p className="text-xs text-white/40 mb-1">2050 Projection</p>
                  <p className="text-2xl font-bold text-emerald-400">
                    {parseFloat(data?.projected_2050 || 0).toFixed(1)}{config?.unit}
                  </p>
                </div>

                {/* CAGR */}
                {data?.growth_rate_cagr && (
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <span className="text-sm text-white/40">CAGR</span>
                    <Badge className={parseFloat(data.growth_rate_cagr) > 0 ? 'bg-emerald-100 text-emerald-400' : 'bg-red-100 text-red-400'}>
                      {parseFloat(data.growth_rate_cagr) > 0 ? '+' : ''}{parseFloat(data.growth_rate_cagr).toFixed(1)}%
                    </Badge>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Data Table */}
      {chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Projection Data</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-3 font-medium text-white/40">Year</th>
                    {chartData.map(item => (
                      <th key={item.year} className="text-center py-2 px-3 font-medium text-white/40">
                        {item.year}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="py-2 px-3 font-medium">{config?.label}</td>
                    {chartData.map(item => (
                      <td key={item.year} className="text-center py-2 px-3">
                        {item.value.toFixed(1)}{config?.unit}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default TechnologyDisruptionChart;
