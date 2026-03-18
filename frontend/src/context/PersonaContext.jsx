/**
 * PersonaContext.jsx
 *
 * Provides the active persona to every component in the tree.
 *
 * Hooks exported:
 *   usePersona()              → { persona, setPersonaId, ALL_PERSONAS, SECTORS, ROLES }
 *   usePersonaDefaults(mod)   → object of default inputs for that module, or {}
 *
 * Persistence: persona choice saved to localStorage so it survives page reload.
 */
import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';
import {
  ALL_PERSONAS,
  PERSONA_BY_ID,
  DEFAULT_PERSONA_ID,
  SECTORS,
  ROLES,
} from '../data/personaSeeds';

const STORAGE_KEY = 'sp_active_persona';

const PersonaContext = createContext(null);

export function PersonaProvider({ children }) {
  const [personaId, setPersonaIdState] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return (stored && PERSONA_BY_ID[stored]) ? stored : DEFAULT_PERSONA_ID;
    } catch {
      return DEFAULT_PERSONA_ID;
    }
  });

  const setPersonaId = useCallback((id) => {
    if (!PERSONA_BY_ID[id]) return;
    try { localStorage.setItem(STORAGE_KEY, id); } catch {}
    setPersonaIdState(id);
  }, []);

  const persona = PERSONA_BY_ID[personaId] || PERSONA_BY_ID[DEFAULT_PERSONA_ID];

  const value = useMemo(() => ({
    persona,
    personaId,
    setPersonaId,
    ALL_PERSONAS,
    SECTORS,
    ROLES,
  }), [persona, personaId, setPersonaId]);

  return (
    <PersonaContext.Provider value={value}>
      {children}
    </PersonaContext.Provider>
  );
}

const DEFAULT_CTX = {
  persona: PERSONA_BY_ID[DEFAULT_PERSONA_ID],
  personaId: DEFAULT_PERSONA_ID,
  setPersonaId: () => {},
  ALL_PERSONAS,
  SECTORS,
  ROLES,
};

/** Returns the full persona context object */
export function usePersona() {
  const ctx = useContext(PersonaContext);
  return ctx || DEFAULT_CTX;
}

/**
 * Returns the persona's defaults for a given module key.
 * Returns empty object if the module is not defined for this persona.
 *
 * @param {string} moduleName  e.g. 'banking_capital', 'carbon', 'supply_chain'
 */
export function usePersonaDefaults(moduleName) {
  const { persona } = usePersona();
  return (persona?.modules?.[moduleName]) || {};
}
