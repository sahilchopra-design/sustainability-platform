/**
 * AlertFeed
 *
 * Chronological alert list from platform_alerts table.
 * Each alert shows severity badge, title, message, timestamp,
 * and a one-click navigation link to the relevant module.
 *
 * Props:
 *   alerts      array    from /api/v1/portfolio-health/{id}/alerts
 *   onMarkRead  fn(id)   called when user marks an alert as read
 *   onMarkAll   fn()     mark all read
 *   loading     bool
 */
import React from 'react';
import { useNavigate } from 'react-router-dom';

const SEVERITY_CONFIG = {
  critical: {
    label: 'Critical',
    colour: '#ef4444',
    bg: 'rgba(239,68,68,0.10)',
    border: 'rgba(239,68,68,0.25)',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0zM12 9v4M12 17h.01"/>
      </svg>
    ),
  },
  warning: {
    label: 'Warning',
    colour: '#f59e0b',
    bg: 'rgba(245,158,11,0.08)',
    border: 'rgba(245,158,11,0.20)',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10"/><path d="M12 8v4M12 16h.01"/>
      </svg>
    ),
  },
  info: {
    label: 'Info',
    colour: '#38bdf8',
    bg: 'rgba(56,189,248,0.06)',
    border: 'rgba(56,189,248,0.15)',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
      </svg>
    ),
  },
};

function timeAgo(isoString) {
  if (!isoString) return '';
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function AlertFeed({ alerts = [], onMarkRead, onMarkAll, loading = false }) {
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-16 rounded-lg bg-white/5 animate-pulse" />
        ))}
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-white/30">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mb-3 opacity-40">
          <path d="M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3"/>
        </svg>
        <p className="text-sm">No alerts — portfolio is on track</p>
      </div>
    );
  }

  return (
    <div data-testid="alert-feed">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-white/40 font-medium uppercase tracking-wider">
          {alerts.filter(a => !a.is_read).length} unread
        </span>
        {onMarkAll && alerts.some(a => !a.is_read) && (
          <button
            onClick={onMarkAll}
            className="text-xs text-[#38bdf8] hover:opacity-80 transition-opacity"
          >
            Mark all read
          </button>
        )}
      </div>

      {/* Alert list */}
      <div className="space-y-2">
        {alerts.map(alert => {
          const cfg = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.info;
          return (
            <div
              key={alert.id}
              className="rounded-lg p-3 border transition-all duration-150 cursor-pointer group"
              style={{
                background: alert.is_read ? 'rgba(255,255,255,0.03)' : cfg.bg,
                borderColor: alert.is_read ? 'rgba(255,255,255,0.08)' : cfg.border,
                opacity: alert.is_read ? 0.65 : 1,
              }}
              onClick={() => {
                if (onMarkRead && !alert.is_read) onMarkRead(alert.id);
                if (alert.module_link) navigate(alert.module_link);
              }}
              data-testid={`alert-item-${alert.alert_type}`}
            >
              <div className="flex items-start gap-2.5">
                {/* Severity icon */}
                <span style={{ color: cfg.colour }} className="mt-0.5 flex-shrink-0">
                  {cfg.icon}
                </span>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs font-semibold text-white leading-snug truncate">
                      {alert.title}
                    </p>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {/* Unread dot */}
                      {!alert.is_read && (
                        <span
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ background: cfg.colour }}
                        />
                      )}
                      <span className="text-[10px] text-white/30 tabular-nums">
                        {timeAgo(alert.created_at)}
                      </span>
                    </div>
                  </div>
                  <p className="text-[11px] text-white/50 leading-relaxed mt-0.5 line-clamp-2">
                    {alert.message}
                  </p>
                </div>
              </div>

              {/* Module link hint */}
              {alert.module_link && (
                <p className="text-[10px] mt-1.5 pl-[22px]" style={{ color: cfg.colour }}>
                  View in {alert.module_link.replace('/', '').replace(/-/g, ' ')} →
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
