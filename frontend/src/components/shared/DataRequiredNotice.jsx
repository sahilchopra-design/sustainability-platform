/**
 * DataRequiredNotice — Reusable empty/error state for modules that need data
 * Shows a clear message when data is missing, plus guidance on what to provide.
 */
import React from 'react';
import { AlertCircle, Database, ArrowRight, RefreshCw } from 'lucide-react';

/**
 * @param {object}  props
 * @param {string}  props.title       — e.g. "No Holdings Data"
 * @param {string}  props.message     — Primary explanation
 * @param {Array}   props.requirements — Bullet list of data requirements
 * @param {string}  [props.severity]  — 'info' | 'warning' | 'error' (default info)
 * @param {object}  [props.icon]      — Lucide icon component override
 * @param {function} [props.onRetry]  — Show retry button if provided
 * @param {string}  [props.retryLabel] — e.g. "Recalculate"
 * @param {string}  [props.testId]
 */
export function DataRequiredNotice({
  title = 'Data Not Available',
  message,
  requirements = [],
  severity = 'info',
  icon: IconOverride,
  onRetry,
  retryLabel = 'Retry',
  testId,
}) {
  const palettes = {
    info: {
      border: 'border-blue-200',
      bg: 'bg-blue-50',
      iconColor: 'text-blue-400',
      titleColor: 'text-blue-700',
      textColor: 'text-blue-600',
      bulletColor: 'text-blue-400',
      btnBg: 'bg-blue-100 hover:bg-blue-200 text-blue-700',
    },
    warning: {
      border: 'border-amber-200',
      bg: 'bg-amber-50',
      iconColor: 'text-amber-400',
      titleColor: 'text-amber-700',
      textColor: 'text-amber-600',
      bulletColor: 'text-amber-400',
      btnBg: 'bg-amber-100 hover:bg-amber-200 text-amber-700',
    },
    error: {
      border: 'border-red-200',
      bg: 'bg-red-50',
      iconColor: 'text-red-400',
      titleColor: 'text-red-700',
      textColor: 'text-red-600',
      bulletColor: 'text-red-400',
      btnBg: 'bg-red-100 hover:bg-red-200 text-red-700',
    },
  };

  const p = palettes[severity] || palettes.info;
  const Icon = IconOverride || (severity === 'error' ? AlertCircle : Database);

  return (
    <div
      className={`rounded-xl border ${p.border} ${p.bg} p-5`}
      data-testid={testId || 'data-required-notice'}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex-shrink-0">
          <Icon className={`h-5 w-5 ${p.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className={`text-sm font-semibold ${p.titleColor} mb-1`}>{title}</h4>
          {message && (
            <p className={`text-xs ${p.textColor} mb-2 leading-relaxed`}>{message}</p>
          )}

          {requirements.length > 0 && (
            <div className="mt-2">
              <p className={`text-[10px] font-semibold uppercase tracking-wider ${p.textColor} opacity-70 mb-1.5`}>
                Required Data
              </p>
              <ul className="space-y-1">
                {requirements.map((req, i) => (
                  <li key={i} className={`text-xs ${p.textColor} flex items-start gap-1.5`}>
                    <ArrowRight className={`h-3 w-3 mt-0.5 flex-shrink-0 ${p.bulletColor}`} />
                    <span>{req}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {onRetry && (
            <button
              onClick={onRetry}
              className={`mt-3 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${p.btnBg}`}
            >
              <RefreshCw className="h-3 w-3" />
              {retryLabel}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
