/**
 * CreditsChart Component
 * Line chart showing carbon credits over time
 */

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

export const CreditsChart = ({
  data = [],
  height = 300,
  title = 'Annual Credits Over Time'
}) => {
  const formatNumber = (value) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `${(value / 1000).toFixed(0)}k`;
    return value;
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-slate-200 rounded-lg shadow-lg p-3">
          <p className="font-semibold text-slate-900 mb-2">{label}</p>
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center gap-2 text-sm">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-slate-600">{entry.name}:</span>
              <span className="font-medium text-slate-900">
                {entry.value?.toLocaleString()} tCO2e
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6" data-testid="credits-chart">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">
        {title}
      </h3>
      
      {data.length === 0 ? (
        <div className="flex items-center justify-center h-[300px] text-slate-400">
          No projection data available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
            <XAxis
              dataKey="year"
              stroke="#64748B"
              fontSize={12}
              tickLine={false}
            />
            <YAxis
              stroke="#64748B"
              fontSize={12}
              tickLine={false}
              tickFormatter={formatNumber}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ paddingTop: '20px' }} />
            
            <Line
              type="monotone"
              dataKey="base_case"
              name="Base Case"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="optimistic"
              name="Optimistic"
              stroke="#10B981"
              strokeWidth={2}
              dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
              strokeDasharray="5 5"
            />
            <Line
              type="monotone"
              dataKey="pessimistic"
              name="Pessimistic"
              stroke="#F59E0B"
              strokeWidth={2}
              dot={{ fill: '#F59E0B', strokeWidth: 2, r: 4 }}
              strokeDasharray="5 5"
            />
            <Line
              type="monotone"
              dataKey="risk_adjusted"
              name="Risk Adjusted"
              stroke="#8B5CF6"
              strokeWidth={2}
              dot={{ fill: '#8B5CF6', strokeWidth: 2, r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default CreditsChart;
