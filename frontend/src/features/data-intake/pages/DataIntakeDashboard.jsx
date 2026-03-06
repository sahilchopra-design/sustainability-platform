import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const API = 'http://localhost:8001/api/v1/data-intake';

const PRIORITY_COLORS = { P0: 'text-red-400', P1: 'text-yellow-400' };
const STATUS_COLORS = {
  active: 'bg-green-900 text-green-300',
  configured: 'bg-green-900 text-green-300',
  empty: 'bg-gray-700 text-gray-400',
};

export default function DataIntakeDashboard() {
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API}/status`)
      .then(r => r.json())
      .then(d => { setModules(d.modules || []); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  const p0 = modules.filter(m => m.priority === 'P0');
  const p1 = modules.filter(m => m.priority === 'P1');
  const totalRecords = modules.reduce((s, m) => s + (m.count || 0), 0);

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-gray-100">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Data Intake</h1>
        <p className="text-gray-400 mt-1 text-sm">
          Client proprietary data — loan books, counterparty emissions, real assets, fleet, and platform configuration.
        </p>
      </div>

      {/* Summary bar */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Total Records', value: totalRecords.toLocaleString() },
          { label: 'Modules Active', value: modules.filter(m => m.status === 'active' || m.status === 'configured').length },
          { label: 'Modules Empty', value: modules.filter(m => m.status === 'empty').length },
        ].map(k => (
          <div key={k.label} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">{loading ? '—' : k.value}</div>
            <div className="text-xs text-gray-400 mt-1">{k.label}</div>
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-6 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">{error}</div>
      )}

      {/* P0 Modules */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3">
          P0 — Required for PCAF Financed Emissions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {loading
            ? [1, 2].map(i => <div key={i} className="h-28 bg-gray-800 rounded-lg animate-pulse" />)
            : p0.map(m => <ModuleCard key={m.id} module={m} />)
          }
        </div>
      </div>

      {/* P1 Modules */}
      <div>
        <h2 className="text-sm font-semibold text-yellow-400 uppercase tracking-wider mb-3">
          P1 — Sector-specific &amp; Configuration
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading
            ? [1, 2, 3, 4, 5].map(i => <div key={i} className="h-28 bg-gray-800 rounded-lg animate-pulse" />)
            : p1.map(m => <ModuleCard key={m.id} module={m} />)
          }
        </div>
      </div>
    </div>
  );
}

function ModuleCard({ module: m }) {
  return (
    <Link to={m.route} className="block">
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-5 hover:border-blue-500 transition-colors">
        <div className="flex items-start justify-between mb-3">
          <span className="font-semibold text-white">{m.label}</span>
          <span className={`text-xs font-mono px-2 py-0.5 rounded ${STATUS_COLORS[m.status] || STATUS_COLORS.empty}`}>
            {m.status}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-white">{m.count.toLocaleString()}</span>
          <span className="text-xs text-gray-400">{m.unit}</span>
        </div>
        <div className="mt-3 flex items-center justify-between">
          <span className={`text-xs font-mono ${PRIORITY_COLORS[m.priority]}`}>{m.priority}</span>
          <span className="text-xs text-blue-400 hover:text-blue-300">Open →</span>
        </div>
      </div>
    </Link>
  );
}
