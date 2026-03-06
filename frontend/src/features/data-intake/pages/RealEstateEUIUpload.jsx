import React, { useCallback, useEffect, useRef, useState } from 'react';

const API = 'http://localhost:8001/api/v1/data-intake/real-estate';

const COLUMNS = [
  'asset_ref', 'property_name', 'address_line1', 'city', 'country_iso2',
  'property_type', 'gross_floor_area_m2', 'eui_kwh_m2_yr',
  'crrem_pathway_2030', 'crrem_pathway_2050', 'stranding_year',
  'energy_star_score', 'gresb_score', 'data_year',
];

const EUI_BENCHMARKS = {
  office: { good: 120, poor: 250 },
  retail: { good: 150, poor: 300 },
  industrial: { good: 80, poor: 180 },
  residential: { good: 100, poor: 220 },
};

export default function RealEstateEUIUpload() {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [uploadBatch, setUploadBatch] = useState('');
  const [filter, setFilter] = useState('');
  const [error, setError] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const fileRef = useRef();

  const fetchAssets = useCallback(() => {
    setLoading(true);
    fetch(API).then(r => r.json())
      .then(d => { setAssets(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  useEffect(() => { fetchAssets(); }, [fetchAssets]);

  const handleFile = async (file) => {
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    if (uploadBatch) form.append('upload_batch', uploadBatch);
    setUploading(true); setError(null); setUploadResult(null);
    try {
      const res = await fetch(`${API}/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      setUploadResult(data);
      fetchAssets();
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => window.open(`${API}/template`, '_blank');

  const filtered = assets.filter(a =>
    !filter || [a.property_name, a.city, a.country_iso2, a.property_type, a.asset_ref]
      .some(v => (v || '').toLowerCase().includes(filter.toLowerCase()))
  );

  const avgEui = assets.length > 0
    ? (assets.reduce((s, a) => s + (parseFloat(a.eui_kwh_m2_yr) || 0), 0) / assets.length).toFixed(1)
    : null;

  const euiColor = (eui, type) => {
    const bench = EUI_BENCHMARKS[type] || EUI_BENCHMARKS.office;
    if (eui <= bench.good) return 'text-green-400';
    if (eui <= bench.poor) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-gray-100">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Real Estate EUI Upload</h1>
          <p className="text-gray-400 text-sm mt-1">Energy Use Intensity data with CRREM decarbonisation pathways.</p>
        </div>
        <button onClick={downloadTemplate}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-sm text-white rounded border border-gray-600">
          Download Template
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Upload panel */}
        <div>
          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); }}
            onClick={() => fileRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer mb-4 transition-colors ${
              dragOver ? 'border-blue-400 bg-blue-900/20' : 'border-gray-600 hover:border-gray-500'
            }`}
          >
            <input ref={fileRef} type="file" accept=".csv" className="hidden"
              onChange={e => handleFile(e.target.files[0])} />
            {uploading ? (
              <p className="text-blue-400">Processing...</p>
            ) : (
              <>
                <p className="text-gray-300 font-medium">Drop CSV or click to browse</p>
                <p className="text-gray-500 text-xs mt-1">Required: asset_ref, eui_kwh_m2_yr, property_type</p>
              </>
            )}
          </div>

          <input type="text" placeholder="Batch label (optional)"
            value={uploadBatch} onChange={e => setUploadBatch(e.target.value)}
            className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white mb-4" />

          {uploadResult && (
            <div className="p-3 bg-green-900/30 border border-green-700 rounded text-sm text-green-300">
              Inserted {uploadResult.inserted} assets.
              {uploadResult.flagged_high_eui > 0 && (
                <span className="text-yellow-300"> {uploadResult.flagged_high_eui} have EUI &gt; 800 kWh/m² (flagged).</span>
              )}
            </div>
          )}
          {error && <div className="p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">{error}</div>}

          {/* Required columns */}
          <div className="mt-4 bg-gray-800 border border-gray-700 rounded-lg p-4">
            <p className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Template Columns</p>
            <div className="grid grid-cols-2 gap-1">
              {COLUMNS.map(c => (
                <div key={c} className="text-xs font-mono text-gray-300 py-0.5">{c}</div>
              ))}
            </div>
          </div>
        </div>

        {/* KPI panel */}
        <div className="space-y-3">
          {[
            { label: 'Total Assets', value: assets.length },
            { label: 'Avg EUI (kWh/m²/yr)', value: avgEui || '—' },
            { label: 'High EUI (>250)', value: assets.filter(a => parseFloat(a.eui_kwh_m2_yr) > 250).length },
            { label: 'With Stranding Year', value: assets.filter(a => a.stranding_year).length },
          ].map(k => (
            <div key={k.label} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <div className="text-xl font-bold text-white">{k.value}</div>
              <div className="text-xs text-gray-400">{k.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Filter + table */}
      <div className="flex items-center gap-3 mb-4">
        <input type="text" placeholder="Filter by name, city, type..." value={filter}
          onChange={e => setFilter(e.target.value)}
          className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white" />
        <span className="text-xs text-gray-400">{filtered.length} assets</span>
      </div>

      {loading ? (
        <div className="text-gray-400 text-sm">Loading...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400 text-left">
                {['Ref', 'Name', 'City', 'Country', 'Type', 'GFA (m²)', 'EUI', 'CRREM 2030', 'CRREM 2050', 'Stranding', 'Year'].map(h => (
                  <th key={h} className="pb-2 pr-3 font-medium text-xs whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filtered.slice(0, 200).map(a => (
                <tr key={a.id} className="hover:bg-gray-800">
                  <td className="py-1.5 pr-3 font-mono text-xs text-gray-400">{a.asset_ref}</td>
                  <td className="py-1.5 pr-3 text-white text-xs">{a.property_name}</td>
                  <td className="py-1.5 pr-3 text-gray-400 text-xs">{a.city}</td>
                  <td className="py-1.5 pr-3 text-gray-400 text-xs">{a.country_iso2}</td>
                  <td className="py-1.5 pr-3 text-gray-400 text-xs">{a.property_type}</td>
                  <td className="py-1.5 pr-3 text-white text-xs">{a.gross_floor_area_m2 ? Number(a.gross_floor_area_m2).toLocaleString() : '—'}</td>
                  <td className={`py-1.5 pr-3 font-medium text-xs ${euiColor(parseFloat(a.eui_kwh_m2_yr), a.property_type)}`}>
                    {a.eui_kwh_m2_yr || '—'}
                  </td>
                  <td className="py-1.5 pr-3 text-gray-400 text-xs">{a.crrem_pathway_2030 || '—'}</td>
                  <td className="py-1.5 pr-3 text-gray-400 text-xs">{a.crrem_pathway_2050 || '—'}</td>
                  <td className={`py-1.5 pr-3 text-xs font-medium ${a.stranding_year && a.stranding_year <= 2035 ? 'text-red-400' : 'text-gray-400'}`}>
                    {a.stranding_year || '—'}
                  </td>
                  <td className="py-1.5 pr-3 text-gray-400 text-xs">{a.data_year}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={11} className="py-8 text-center text-gray-500">No assets found</td></tr>
              )}
            </tbody>
          </table>
          {filtered.length > 200 && (
            <p className="text-xs text-gray-500 mt-2 text-center">Showing first 200 of {filtered.length} assets</p>
          )}
        </div>
      )}
    </div>
  );
}
