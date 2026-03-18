import React from 'react';

/**
 * Empty state placeholder for pages with no data.
 *
 * Usage:
 *   <EmptyState
 *     title="No portfolios yet"
 *     description="Upload your first portfolio to get started with climate risk analysis."
 *     actionLabel="Upload Portfolio"
 *     onAction={() => navigate('/data-intake/portfolio')}
 *   />
 */
export default function EmptyState({
  icon,
  title = 'No data yet',
  description = '',
  actionLabel,
  onAction,
  secondaryLabel,
  onSecondary,
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {/* Icon */}
      <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
        {icon || (
          <svg className="w-7 h-7 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
          </svg>
        )}
      </div>

      {/* Title */}
      <h3 className="text-base font-semibold text-gray-800 mb-1">{title}</h3>

      {/* Description */}
      {description && (
        <p className="text-sm text-gray-500 max-w-sm mb-6">{description}</p>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        {actionLabel && onAction && (
          <button
            onClick={onAction}
            className="px-4 py-2 text-sm font-medium text-white bg-emerald-600 rounded-md hover:bg-emerald-700 transition-colors"
          >
            {actionLabel}
          </button>
        )}
        {secondaryLabel && onSecondary && (
          <button
            onClick={onSecondary}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            {secondaryLabel}
          </button>
        )}
      </div>
    </div>
  );
}
