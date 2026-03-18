import React from 'react';

function Pulse({ className = '' }) {
  return <div className={`animate-pulse bg-gray-200 rounded ${className}`} />;
}

/** KPI card skeleton — shows 1 animated placeholder card */
export function KpiCardSkeleton() {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <Pulse className="h-3 w-24" />
      <Pulse className="h-7 w-32" />
      <Pulse className="h-2 w-16" />
    </div>
  );
}

/** Table skeleton — shows N rows of animated bars */
export function TableSkeleton({ rows = 5, cols = 4 }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="flex gap-4 px-4 py-3 border-b border-gray-100 bg-gray-50">
        {Array.from({ length: cols }).map((_, i) => (
          <Pulse key={i} className="h-3 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex gap-4 px-4 py-3 border-b border-gray-50 last:border-0">
          {Array.from({ length: cols }).map((_, c) => (
            <Pulse key={c} className="h-3 flex-1" style={{ width: `${60 + Math.random() * 40}%` }} />
          ))}
        </div>
      ))}
    </div>
  );
}

/** Chart skeleton — animated placeholder for Recharts area */
export function ChartSkeleton({ height = 200 }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <Pulse className="h-3 w-40 mb-4" />
      <Pulse className="rounded-md" style={{ height }} />
    </div>
  );
}

/**
 * Full page loading skeleton — combines KPI cards + chart + table.
 * Drop this into any page while data is loading.
 *
 * Usage:
 *   if (isLoading) return <PageSkeleton />;
 */
export default function PageSkeleton({ kpiCount = 4, tableRows = 6 }) {
  return (
    <div className="space-y-6 p-6 animate-in fade-in duration-200">
      {/* KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: kpiCount }).map((_, i) => (
          <KpiCardSkeleton key={i} />
        ))}
      </div>
      {/* Chart */}
      <ChartSkeleton height={240} />
      {/* Table */}
      <TableSkeleton rows={tableRows} />
    </div>
  );
}
