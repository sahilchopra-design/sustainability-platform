/**
 * PersonaSwitcher.jsx
 *
 * Compact dropdown that lets users switch between the 12 demo personas.
 * Groups personas by sector. Displays role badge + institution name.
 *
 * Used inside the DemoBanner and can be placed anywhere in the header.
 */
import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Users } from 'lucide-react';
import { usePersona } from '../../context/PersonaContext';

const ROLE_COLOURS = {
  'Investment Lead':                  'bg-blue-100 text-blue-700',
  'Analytics Lead':                   'bg-purple-100 text-purple-700',
  'Sustainability & Regulatory Lead': 'bg-emerald-100 text-emerald-700',
};

const SECTOR_BORDER = {
  Finance:         'border-blue-200',
  Energy:          'border-sky-200',
  'Supply Chain':  'border-violet-200',
  Manufacturing:   'border-amber-200',
};

export default function PersonaSwitcher({ compact = false }) {
  const { persona, setPersonaId, ALL_PERSONAS, SECTORS } = usePersona();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const grouped = SECTORS.map(sector => ({
    sector,
    personas: ALL_PERSONAS.filter(p => p.sector === sector),
  }));

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(o => !o)}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-gray-300
          bg-white hover:bg-gray-50 text-xs font-medium text-gray-700 transition-colors shadow-sm"
      >
        <span className="text-sm leading-none">{persona.logo}</span>
        {!compact && (
          <span className="max-w-[140px] truncate hidden sm:block">
            {persona.institution}
          </span>
        )}
        <span className={`hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold
          ${ROLE_COLOURS[persona.role] || 'bg-gray-100 text-gray-600'}`}>
          {persona.role.split(' ')[0]}
        </span>
        <ChevronDown className={`w-3 h-3 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 mt-1.5 w-80 bg-white rounded-xl shadow-xl border border-gray-200 z-50
          max-h-[480px] overflow-y-auto">
          <div className="p-3 border-b border-gray-100">
            <p className="text-[10px] font-bold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
              <Users className="w-3 h-3" /> Persona Â· Institution Â· Role
            </p>
            <p className="text-[10px] text-gray-400 mt-0.5">
              Switching populates all calculators with realistic data for this user type.
            </p>
          </div>

          {grouped.map(({ sector, personas }) => (
            <div key={sector}>
              <p className="px-3 pt-2.5 pb-1 text-[9px] font-extrabold uppercase tracking-widest text-gray-400">
                {sector}
              </p>
              {personas.map(p => {
                const active = p.id === persona.id;
                return (
                  <button
                    key={p.id}
                    onClick={() => { setPersonaId(p.id); setOpen(false); }}
                    className={`w-full text-left px-3 py-2 flex items-start gap-2.5 hover:bg-gray-50 transition-colors
                      border-l-2 ${active ? SECTOR_BORDER[sector] : 'border-transparent'}`}
                  >
                    <span className="text-base leading-none mt-0.5 shrink-0">{p.logo}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className={`text-[10px] font-semibold ${active ? 'text-gray-900' : 'text-gray-700'}`}>
                          {p.institution}
                        </span>
                        <span className={`inline-flex items-center px-1.5 py-px rounded text-[8px] font-bold
                          ${ROLE_COLOURS[p.role] || 'bg-gray-100 text-gray-600'}`}>
                          {p.role}
                        </span>
                        {active && (
                          <span className="inline-flex items-center px-1.5 py-px rounded text-[8px] font-bold
                            bg-black text-white">ACTIVE</span>
                        )}
                      </div>
                      <p className="text-[10px] text-gray-500 mt-0.5 truncate">{p.name}</p>
                      <p className="text-[9px] text-gray-400 mt-0.5 truncate">{p.tagline}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          ))}

          <div className="p-2.5 border-t border-gray-100 bg-gray-50 rounded-b-xl">
            <p className="text-[9px] text-gray-400 text-center">
              All data is simulated. No real institution data is used.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
