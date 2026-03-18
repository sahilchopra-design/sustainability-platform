/**
 * DemoBanner.jsx
 *
 * Persistent amber banner shown on pages using simulated demo data.
 * Now includes:
 *  - Active persona badge (institution · role)
 *  - PersonaSwitcher dropdown (switch to any of 12 institution/role personas)
 *  - Per-session dismissal via sessionStorage
 */
import React, { useState } from 'react';
import { AlertTriangle, X, Database } from 'lucide-react';
import PersonaSwitcher from './PersonaSwitcher';
import { usePersona } from '../../context/PersonaContext';

const ROLE_COLOURS = {
  'Investment Lead':                  'bg-blue-100 text-blue-700 border-blue-200',
  'Analytics Lead':                   'bg-purple-100 text-purple-700 border-purple-200',
  'Sustainability & Regulatory Lead': 'bg-emerald-100 text-emerald-700 border-emerald-200',
};

export default function DemoBanner({ message, docsHref }) {
  const storageKey = `demo_banner_dismissed_${window.location.pathname}`;
  const [dismissed, setDismissed] = useState(
    () => sessionStorage.getItem(storageKey) === '1'
  );

  // Try to consume persona context — may not be available on every page
  let persona = null;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const ctx = usePersona();
    persona = ctx?.persona;
  } catch {}

  if (dismissed) return null;

  const handleDismiss = () => {
    sessionStorage.setItem(storageKey, '1');
    setDismissed(true);
  };

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-3 py-2 flex items-center gap-2.5 flex-wrap">
      <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />

      {/* Message */}
      <div className="flex-1 min-w-0 text-xs text-amber-800">
        <span className="font-bold uppercase tracking-wide text-amber-700 mr-1.5">Demo Data</span>
        {message || 'Simulated inputs based on the active persona below — not live client data.'}
        {docsHref && (
          <a href={docsHref} target="_blank" rel="noopener noreferrer"
            className="ml-2 underline font-semibold text-amber-700 hover:text-amber-900">
            How to connect your data →
          </a>
        )}
      </div>

      {/* Active persona pill */}
      {persona && (
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="text-sm leading-none">{persona.logo}</span>
          <div className="flex flex-col leading-none">
            <span className="text-[10px] font-bold text-gray-700">{persona.institution}</span>
            <span className="text-[9px] text-gray-500">{persona.institutionType}</span>
          </div>
          <span className={`hidden sm:inline-flex items-center px-1.5 py-0.5 rounded border text-[8px] font-bold
            ${ROLE_COLOURS[persona.role] || 'bg-gray-100 text-gray-600 border-gray-200'}`}>
            {persona.role}
          </span>
        </div>
      )}

      {/* Persona switcher */}
      {persona && <PersonaSwitcher compact />}

      {/* SAMPLE badge + dismiss */}
      <div className="flex items-center gap-1.5 shrink-0">
        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 text-amber-700
          text-[10px] font-bold border border-amber-300">
          <Database className="w-2.5 h-2.5" /> SAMPLE
        </span>
        <button
          onClick={handleDismiss}
          className="p-1 rounded hover:bg-amber-100 text-amber-600 transition-colors"
          aria-label="Dismiss demo data notice"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
