/**
 * GlobalDemoBanner.jsx
 *
 * Sprint 1 — GAP-003: Seed Data Masking
 *
 * A persistent amber banner rendered once at the layout level (above <main>)
 * on EVERY page of the platform.  Communicates clearly that figures are
 * illustrative seed data until live data sources are connected.
 *
 * Behaviour:
 *  - Session-level dismissal via sessionStorage key 'sp_global_demo_dismissed'
 *    (dismissing once per browser session keeps it out of the way during demos)
 *  - Shows current isFallback state from dashboardStore (orange pulse dot
 *    when API is unreachable and synthetic fallback data is active)
 *  - Links directly to /data-intake to guide users toward connecting real data
 *  - Renders the active persona badge + institution type from PersonaContext
 *  - Shows a keyboard shortcut hint: press D to dismiss
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle, X, Database, Wifi, WifiOff, ArrowRight, RefreshCw,
} from 'lucide-react';
import { useDashboardStore } from '../../store/dashboardStore';

// Try persona context — may not be available on every render path
let _usePersona = null;
try {
  // eslint-disable-next-line global-require
  _usePersona = require('../../context/PersonaContext').usePersona;
} catch {}

const STORAGE_KEY = 'sp_global_demo_dismissed';

export default function GlobalDemoBanner() {
  const [dismissed, setDismissed] = useState(
    () => sessionStorage.getItem(STORAGE_KEY) === '1',
  );
  const navigate = useNavigate();

  // Pull isFallback from dashboardStore (non-blocking)
  const isFallback = useDashboardStore(s => s.isFallback ?? false);
  const apiReachable = useDashboardStore(s => s.apiReachable ?? false);

  // Try persona context
  let persona = null;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    if (_usePersona) persona = _usePersona()?.persona;
  } catch {}

  // Keyboard shortcut: press D to dismiss
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'd' && !e.ctrlKey && !e.metaKey && !e.altKey
          && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        setDismissed(true);
        sessionStorage.setItem(STORAGE_KEY, '1');
      }
    },
    [],
  );

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  if (dismissed) return null;

  const handleDismiss = () => {
    sessionStorage.setItem(STORAGE_KEY, '1');
    setDismissed(true);
  };

  return (
    <div
      className="bg-amber-50 border-b-2 border-amber-300 px-3 py-2 flex items-center gap-2.5 flex-wrap shrink-0"
      role="alert"
      aria-label="Demo mode notice"
    >
      {/* Icon */}
      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />

      {/* DEMO MODE badge */}
      <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-400 text-white
        text-[9px] font-extrabold tracking-widest uppercase border border-amber-500 shrink-0">
        <Database className="w-2.5 h-2.5" />
        DEMO MODE
      </span>

      {/* Main message */}
      <span className="flex-1 min-w-0 text-xs text-amber-800 font-medium">
        All figures are&nbsp;
        <strong className="font-bold text-amber-900">illustrative seed data</strong>
        &nbsp;generated from persona defaults — not live client data.
        {isFallback && (
          <span className="ml-2 inline-flex items-center gap-1 text-orange-700 font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
            API offline — synthetic fallback active.
          </span>
        )}
      </span>

      {/* API status dot */}
      <div className="flex items-center gap-1 shrink-0">
        {apiReachable ? (
          <span className="inline-flex items-center gap-1 text-[10px] text-emerald-600 font-semibold">
            <Wifi className="w-3 h-3" />
            <span className="hidden sm:inline">API connected</span>
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-[10px] text-amber-700 font-semibold">
            <WifiOff className="w-3 h-3" />
            <span className="hidden sm:inline">API offline</span>
          </span>
        )}
      </div>

      {/* Active persona pill */}
      {persona && (
        <div className="hidden md:flex items-center gap-1.5 shrink-0 border-l border-amber-300 pl-2.5">
          <span className="text-sm leading-none">{persona.logo}</span>
          <div className="leading-none">
            <div className="text-[10px] font-bold text-gray-700">{persona.institution}</div>
            <div className="text-[9px] text-gray-500">{persona.institutionType}</div>
          </div>
        </div>
      )}

      {/* Connect data link */}
      <button
        onClick={() => navigate('/data-intake')}
        className="hidden sm:inline-flex items-center gap-1 text-[10px] font-bold text-amber-700
          bg-amber-100 hover:bg-amber-200 border border-amber-300 px-2 py-1 rounded-full
          transition-colors shrink-0"
        aria-label="Go to Data Intake to connect live data"
      >
        Connect data <ArrowRight className="w-2.5 h-2.5" />
      </button>

      {/* Keyboard hint + dismiss */}
      <div className="flex items-center gap-1.5 shrink-0">
        <span className="hidden lg:inline text-[9px] text-amber-500 font-mono">press D to hide</span>
        <button
          onClick={handleDismiss}
          className="p-1 rounded hover:bg-amber-200 text-amber-600 transition-colors"
          aria-label="Dismiss demo mode notice"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
