import { useState, useEffect } from 'react';

const STORAGE_KEY = 'mapbox_access_token';
const ENV_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;

/**
 * Returns the active Mapbox token (env → localStorage → null)
 * and a setter that persists to localStorage.
 *
 * @returns {{ token: string|null, setToken: (t: string) => void, clearToken: () => void }}
 */
export function useMapboxToken() {
  const [token, setTokenState] = useState(() => {
    if (ENV_TOKEN) return ENV_TOKEN;
    try {
      return localStorage.getItem(STORAGE_KEY) || null;
    } catch {
      return null;
    }
  });

  // If env token changes at runtime (rare) stay in sync
  useEffect(() => {
    if (ENV_TOKEN && token !== ENV_TOKEN) {
      setTokenState(ENV_TOKEN);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const setToken = (t) => {
    const trimmed = t?.trim();
    if (!trimmed) return;
    try {
      localStorage.setItem(STORAGE_KEY, trimmed);
    } catch {
      // quota exceeded — best effort
    }
    setTokenState(trimmed);
  };

  const clearToken = () => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
    setTokenState(ENV_TOKEN || null);
  };

  return { token, setToken, clearToken };
}
