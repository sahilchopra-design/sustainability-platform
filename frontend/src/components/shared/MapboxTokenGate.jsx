/**
 * MapboxTokenGate
 *
 * Wraps any map component. If a valid Mapbox token is available (from env or
 * localStorage) it renders children and injects the token via the `tokenProp`
 * callback. If no token exists it renders an inline prompt that lets the user
 * paste their public access token and saves it to localStorage.
 *
 * Usage:
 *   <MapboxTokenGate height="500px">
 *     {(token) => <MyMapComponent accessToken={token} />}
 *   </MapboxTokenGate>
 *
 * Or as a wrapper when the child reads from mapboxgl.accessToken directly:
 *   <MapboxTokenGate height="500px" onToken={(t) => { mapboxgl.accessToken = t; }}>
 *     <MyMap />
 *   </MapboxTokenGate>
 */

import React, { useState } from 'react';
import { Map, Key, ExternalLink, RotateCcw, Eye, EyeOff } from 'lucide-react';
import { useMapboxToken } from '../../hooks/useMapboxToken';

export function MapboxTokenGate({ children, height = '400px', className = '' }) {
  const { token, setToken, clearToken } = useMapboxToken();
  const [input, setInput] = useState('');
  const [showInput, setShowInput] = useState(false);
  const [showToken, setShowToken] = useState(false);
  const [error, setError] = useState('');

  const handleSave = () => {
    const trimmed = input.trim();
    if (!trimmed) {
      setError('Token cannot be empty.');
      return;
    }
    if (!trimmed.startsWith('pk.')) {
      setError('Mapbox public tokens start with "pk.". Check you copied the full token.');
      return;
    }
    setError('');
    setToken(trimmed);
    setInput('');
    setShowInput(false);
  };

  // Token is present — render map content
  if (token) {
    return (
      <div className={`relative ${className}`}>
        {typeof children === 'function' ? children(token) : children}

        {/* Small "change token" button in corner */}
        <button
          onClick={() => { clearToken(); setShowInput(true); }}
          title="Change Mapbox token"
          className="absolute bottom-2 right-2 z-10 flex items-center gap-1 px-2 py-1 text-xs
                     bg-black/60 hover:bg-black/80 text-white/60 hover:text-white rounded
                     backdrop-blur transition-colors"
        >
          <Key className="h-3 w-3" />
          API key
        </button>
      </div>
    );
  }

  // No token — show prompt
  return (
    <div
      className={`flex flex-col items-center justify-center bg-[#0d1424] border border-white/[0.06] rounded-lg ${className}`}
      style={{ minHeight: height }}
    >
      <div className="w-full max-w-md px-6 py-8 text-center space-y-5">
        {/* Icon */}
        <div className="flex justify-center">
          <div className="p-4 bg-blue-500/10 rounded-full">
            <Map className="h-8 w-8 text-blue-400" />
          </div>
        </div>

        <div>
          <h3 className="text-base font-semibold text-white">Mapbox API Key Required</h3>
          <p className="mt-1 text-sm text-white/50">
            Enter your Mapbox public access token to enable the map view.
          </p>
        </div>

        {/* Input */}
        <div className="space-y-2 text-left">
          <label className="block text-xs font-medium text-white/60">
            Public access token
          </label>
          <div className="relative">
            <input
              type={showToken ? 'text' : 'password'}
              value={input}
              onChange={(e) => { setInput(e.target.value); setError(''); }}
              onKeyDown={(e) => e.key === 'Enter' && handleSave()}
              placeholder="pk.eyJ1IjoiYW5..."
              className="w-full bg-white/[0.05] border border-white/[0.12] rounded-md px-3 py-2 pr-10
                         text-sm text-white placeholder:text-white/25
                         focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/30
                         font-mono"
            />
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70 transition-colors"
              title={showToken ? 'Hide token' : 'Show token'}
            >
              {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {error && (
            <p className="text-xs text-red-400">{error}</p>
          )}
        </div>

        <button
          onClick={handleSave}
          disabled={!input.trim()}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/30
                     disabled:cursor-not-allowed text-white text-sm font-medium rounded-md
                     transition-colors"
        >
          Save & Load Map
        </button>

        <p className="text-xs text-white/30 leading-relaxed">
          Token is saved in your browser only and never sent to any server.{' '}
          <a
            href="https://account.mapbox.com/access-tokens/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 inline-flex items-center gap-0.5"
          >
            Get a free token
            <ExternalLink className="h-3 w-3 ml-0.5" />
          </a>
        </p>
      </div>
    </div>
  );
}

/**
 * Convenience: wraps a component that needs mapboxgl.accessToken set before mounting.
 * Sets the token on mapboxgl then renders children.
 */
export function withMapboxToken(mapboxgl) {
  return function TokenWrapper({ children, height, className }) {
    return (
      <MapboxTokenGate height={height} className={className}>
        {(token) => {
          mapboxgl.accessToken = token;
          return children;
        }}
      </MapboxTokenGate>
    );
  };
}

export default MapboxTokenGate;
