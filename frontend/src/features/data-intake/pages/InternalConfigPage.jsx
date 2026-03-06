import React, { useCallback, useEffect, useState } from 'react';

const API = 'http://localhost:8001/api/v1/data-intake/internal-config';

const GROUP_LABELS = {
  emissions: 'Emissions',
  reporting: 'Reporting',
  thresholds: 'Thresholds',
  integration: 'Integration',
};

export default function InternalConfigPage() {
  const [config, setConfig] = useState([]);
  const [dirty, setDirty] = useState({});  // { key: newValue }
  const [saving, setSaving] = useState({});
  const [saved, setSaved] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchConfig = useCallback(() => {
    setLoading(true);
    fetch(API).then(r => r.json())
      .then(d => { setConfig(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  useEffect(() => { fetchConfig(); }, [fetchConfig]);

  const handleChange = (key, value) => {
    setDirty(d => ({ ...d, [key]: value }));
    setSaved(s => ({ ...s, [key]: false }));
  };

  const handleSave = async (key) => {
    setSaving(s => ({ ...s, [key]: true }));
    try {
      const res = await fetch(`${API}/${key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config_value: dirty[key] }),
      });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail); }
      setSaved(s => ({ ...s, [key]: true }));
      setDirty(d => { const n = { ...d }; delete n[key]; return n; });
      fetchConfig();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(s => ({ ...s, [key]: false }));
    }
  };

  const getValue = (item) => dirty[item.config_key] !== undefined ? dirty[item.config_key] : (item.config_value || '');
  const isDirty = (key) => dirty[key] !== undefined;

  // Group by config_group
  const groups = {};
  config.forEach(item => {
    const g = item.config_group || 'other';
    if (!groups[g]) groups[g] = [];
    groups[g].push(item);
  });

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-gray-100">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Internal Configuration</h1>
        <p className="text-gray-400 text-sm mt-1">
          Platform-wide settings for emissions accounting, reporting parameters, and integration defaults.
        </p>
      </div>

      {error && <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">{error}</div>}

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-20 bg-gray-800 rounded-lg animate-pulse" />)}
        </div>
      ) : (
        <div className="space-y-8">
          {Object.entries(groups).map(([group, items]) => (
            <div key={group}>
              <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
                {GROUP_LABELS[group] || group}
              </h2>
              <div className="space-y-3">
                {items.map(item => (
                  <div key={item.config_key}
                    className={`bg-gray-800 border rounded-lg p-4 transition-colors ${
                      isDirty(item.config_key) ? 'border-blue-500' : 'border-gray-700'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-white text-sm">{item.display_name}</span>
                          <span className="font-mono text-xs text-gray-500">{item.config_key}</span>
                          <span className="text-xs bg-gray-700 text-gray-400 px-1.5 py-0.5 rounded">{item.data_type}</span>
                        </div>
                        {item.description && (
                          <p className="text-xs text-gray-400 mb-3">{item.description}</p>
                        )}
                        <ConfigInput item={item} value={getValue(item)} onChange={v => handleChange(item.config_key, v)} />
                      </div>
                      <div className="flex flex-col items-end gap-2 shrink-0 pt-1">
                        {saved[item.config_key] && !isDirty(item.config_key) && (
                          <span className="text-xs text-green-400">Saved</span>
                        )}
                        {isDirty(item.config_key) && (
                          <button
                            onClick={() => handleSave(item.config_key)}
                            disabled={saving[item.config_key]}
                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-xs text-white rounded"
                          >
                            {saving[item.config_key] ? 'Saving...' : 'Save'}
                          </button>
                        )}
                        {item.updated_at && (
                          <span className="text-xs text-gray-600">
                            {new Date(item.updated_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
          {config.length === 0 && (
            <div className="text-center py-12 text-gray-500">No configuration keys found.</div>
          )}
        </div>
      )}
    </div>
  );
}

function ConfigInput({ item, value, onChange }) {
  if (item.data_type === 'boolean') {
    return (
      <div className="flex items-center gap-2">
        <input type="checkbox" checked={value === 'true' || value === true}
          onChange={e => onChange(e.target.checked ? 'true' : 'false')}
          className="w-4 h-4 accent-blue-500" />
        <span className="text-sm text-gray-300">{value === 'true' ? 'Enabled' : 'Disabled'}</span>
      </div>
    );
  }
  if (item.data_type === 'number') {
    return (
      <input type="number" value={value}
        onChange={e => onChange(e.target.value)}
        className="bg-gray-700 border border-gray-600 rounded px-3 py-1.5 text-white text-sm w-40
          focus:outline-none focus:border-blue-500" />
    );
  }
  return (
    <input type="text" value={value}
      onChange={e => onChange(e.target.value)}
      className="bg-gray-700 border border-gray-600 rounded px-3 py-1.5 text-white text-sm w-64
        focus:outline-none focus:border-blue-500" />
  );
}
