import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const API = 'http://localhost:8001/api/v1/data-intake';

const PRIORITY_COLORS = { P0: 'text-red-400', P1: 'text-yellow-400' };
const STATUS_COLORS = {
  active: 'bg-green-900 text-green-300',
  configured: 'bg-green-900 text-green-300',
  empty: 'bg-gray-700 text-gray-400',
};
const CATEGORY_COLORS = {
  ESG: 'bg-emerald-900/60 text-emerald-300',
  Governance: 'bg-purple-900/60 text-purple-300',
  Energy: 'bg-amber-900/60 text-amber-300',
  'Real Estate': 'bg-cyan-900/60 text-cyan-300',
  Emissions: 'bg-rose-900/60 text-rose-300',
  Social: 'bg-blue-900/60 text-blue-300',
  Platform: 'bg-gray-700 text-gray-300',
};

export default function DataIntakeDashboard() {
  const [modules, setModules] = useState([]);
  const [dataHub, setDataHub] = useState([]);
  const [summary, setSummary] = useState(null);
  const [criBreakdown, setCriBreakdown] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API}/status`)
      .then(r => r.json())
      .then(d => {
        setModules(d.modules || []);
        setDataHub(d.data_hub || []);
        setSummary(d.summary || null);
        setCriBreakdown(d.country_risk_breakdown || []);
        setLoading(false);
      })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  const p0 = modules.filter(m => m.priority === 'P0');
  const p1 = modules.filter(m => m.priority === 'P1');

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-gray-100">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Data Intake & Reference Hub</h1>
        <p className="text-gray-400 mt-1 text-sm">
          Client proprietary data modules and reference data sources powering analytics.
        </p>
      </div>

      {/* Summary KPI bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        {[
          {
            label: 'Client Records',
            value: summary ? summary.total_client_records.toLocaleString() : '--',
            sub: summary ? `${summary.client_modules_active}/${summary.client_modules_total} modules` : '',
          },
          {
            label: 'Client Completion',
            value: summary ? `${summary.client_completion_pct}%` : '--',
            sub: summary ? `${summary.client_modules_active} active` : '',
            pct: summary?.client_completion_pct,
          },
          {
            label: 'Reference Records',
            value: summary ? summary.total_reference_records.toLocaleString() : '--',
            sub: summary ? `${summary.dh_sources_active}/${summary.dh_sources_total} sources` : '',
          },
          {
            label: 'Reference Coverage',
            value: summary ? `${summary.dh_completion_pct}%` : '--',
            sub: summary ? `${summary.dh_sources_active} active` : '',
            pct: summary?.dh_completion_pct,
          },
        ].map(k => (
          <div key={k.label} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">{loading ? '--' : k.value}</div>
            <div className="text-xs text-gray-400 mt-1">{k.label}</div>
            {k.pct !== undefined && !loading && (
              <div className="mt-2 w-full bg-gray-700 rounded-full h-1.5">
                <div
                  className={`h-1.5 rounded-full transition-all ${k.pct >= 80 ? 'bg-green-500' : k.pct >= 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${k.pct}%` }}
                />
              </div>
            )}
            {k.sub && !loading && <div className="text-xs text-gray-500 mt-1">{k.sub}</div>}
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-6 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">{error}</div>
      )}

      {/* P0 Client Modules */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3">
          P0 -- Required for PCAF Financed Emissions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {loading
            ? [1, 2].map(i => <div key={i} className="h-28 bg-gray-800 rounded-lg animate-pulse" />)
            : p0.map(m => <ModuleCard key={m.id} module={m} />)
          }
        </div>
      </div>

      {/* P1 Client Modules */}
      <div className="mb-8">
        <h2 className="text-sm font-semibold text-yellow-400 uppercase tracking-wider mb-3">
          P1 -- Sector-specific & Configuration
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading
            ? [1, 2, 3, 4, 5].map(i => <div key={i} className="h-28 bg-gray-800 rounded-lg animate-pulse" />)
            : p1.map(m => <ModuleCard key={m.id} module={m} />)
          }
        </div>
      </div>

      {/* Reference Data Hub */}
      <div className="mb-8">
        <div className="flex items-baseline gap-3 mb-3">
          <h2 className="text-sm font-semibold text-blue-400 uppercase tracking-wider">
            Reference Data Hub
          </h2>
          {summary && !loading && (
            <span className="text-xs text-gray-500">
              {summary.total_reference_records.toLocaleString()} total records across {summary.dh_sources_active} sources
            </span>
          )}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {loading
            ? [1, 2, 3, 4, 5, 6].map(i => <div key={i} className="h-24 bg-gray-800 rounded-lg animate-pulse" />)
            : dataHub.map(d => <DataHubCard key={d.id} source={d} />)
          }
        </div>
      </div>

      {/* Country Risk Breakdown */}
      {criBreakdown.length > 0 && !loading && (
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-purple-400 uppercase tracking-wider mb-3">
            Country Risk Indices Breakdown
          </h2>
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {criBreakdown.map(b => (
                <div key={b.index} className="text-center">
                  <div className="text-xl font-bold text-white">{b.count.toLocaleString()}</div>
                  <div className="text-xs text-gray-400 mt-1">{CRI_LABELS[b.index] || b.index}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const CRI_LABELS = {
  CPI: 'Transparency Intl CPI',
  FSI: 'Fragile States Index',
  FH_FIW: 'Freedom House FIW',
  UNDP_GII: 'UNDP Gender Inequality',
};

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
        {/* Completion indicator */}
        <div className="mt-2 w-full bg-gray-700 rounded-full h-1">
          <div
            className={`h-1 rounded-full transition-all ${m.status === 'empty' ? 'bg-gray-600' : 'bg-green-500'}`}
            style={{ width: m.status === 'empty' ? '0%' : '100%' }}
          />
        </div>
        <div className="mt-2 flex items-center justify-between">
          <span className={`text-xs font-mono ${PRIORITY_COLORS[m.priority]}`}>{m.priority}</span>
          <span className="text-xs text-blue-400 hover:text-blue-300">Open &rarr;</span>
        </div>
      </div>
    </Link>
  );
}

function DataHubCard({ source: d }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-colors">
      <div className="flex items-start justify-between mb-2">
        <span className="font-medium text-white text-sm">{d.label}</span>
        <span className={`text-xs px-2 py-0.5 rounded ${CATEGORY_COLORS[d.category] || CATEGORY_COLORS.Platform}`}>
          {d.category}
        </span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-xl font-bold text-white">{d.count.toLocaleString()}</span>
        <span className="text-xs text-gray-400">{d.unit}</span>
      </div>
      <div className="mt-2 flex items-center justify-between">
        <span className={`text-xs ${d.status === 'active' ? 'text-green-400' : 'text-gray-500'}`}>
          {d.status === 'active' ? 'Loaded' : 'No data'}
        </span>
        <span className="text-xs text-gray-500 font-mono">{d.table}</span>
      </div>
    </div>
  );
}
