import React, { useCallback, useEffect, useRef, useState } from 'react';

const API = 'http://localhost:8001/api/v1/data-intake/shipping-fleet';

const CII_STYLE = {
  A: 'bg-green-700 text-green-100',
  B: 'bg-green-900 text-green-300',
  C: 'bg-yellow-900 text-yellow-300',
  D: 'bg-orange-900 text-orange-300',
  E: 'bg-red-900 text-red-300',
};

export default function ShippingFleetUpload() {
  const [vessels, setVessels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [filter, setFilter] = useState('');
  const [ciiFilter, setCiiFilter] = useState('');
  const [error, setError] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const fileRef = useRef();

  const fetchVessels = useCallback(() => {
    setLoading(true);
    fetch(API).then(r => r.json())
      .then(d => { setVessels(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  useEffect(() => { fetchVessels(); }, [fetchVessels]);

  const handleFile = async (file) => {
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    setUploading(true); setError(null); setUploadResult(null);
    try {
      const res = await fetch(`${API}/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      setUploadResult(data);
      fetchVessels();
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => window.open(`${API}/template`, '_blank');

  const filtered = vessels.filter(v => {
    const matchText = !filter || [v.vessel_name, v.vessel_imo, v.vessel_type, v.flag_state]
      .some(f => (f || '').toLowerCase().includes(filter.toLowerCase()));
    const matchCii = !ciiFilter || v.cii_rating === ciiFilter;
    return matchText && matchCii;
  });

  const totalCo2 = vessels.reduce((s, v) => s + (parseFloat(v.annual_co2_tco2e) || 0), 0);
  const ciiDist = ['A','B','C','D','E'].map(r => ({ r, n: vessels.filter(v => v.cii_rating === r).length }));

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-gray-100">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Shipping Fleet Upload</h1>
          <p className="text-gray-400 text-sm mt-1">Vessel-level CII ratings and CO2 emissions for Poseidon Principles alignment.</p>
        </div>
        <button onClick={downloadTemplate}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-sm text-white rounded border border-gray-600">
          Download Template
        </button>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Vessels', value: vessels.length },
          { label: 'Total CO2 (tCO2e/yr)', value: totalCo2 > 0 ? (totalCo2 / 1000).toFixed(1) + ' kt' : '—' },
          ...ciiDist.filter(d => d.n > 0).slice(0, 2).map(d => ({
            label: `CII ${d.r}`, value: d.n,
          })),
        ].map(k => (
          <div key={k.label} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
            <div className="text-xl font-bold text-white">{k.value}</div>
            <div className="text-xs text-gray-400 mt-1">{k.label}</div>
          </div>
        ))}
      </div>

      {/* CII distribution */}
      <div className="flex gap-2 mb-6">
        {ciiDist.map(d => (
          <div key={d.r} className={`flex items-center gap-1.5 px-3 py-1.5 rounded ${CII_STYLE[d.r] || 'bg-gray-700 text-gray-400'}`}>
            <span className="font-bold">{d.r}</span>
            <span className="text-sm">{d.n}</span>
          </div>
        ))}
      </div>

      {/* Upload zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]); }}
        onClick={() => fileRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer mb-6 transition-colors ${
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
            <p className="text-gray-500 text-xs mt-1">Required: vessel_imo, vessel_type, annual_co2_tco2e, cii_rating</p>
          </>
        )}
      </div>

      {uploadResult && (
        <div className="mb-4 p-3 bg-green-900/30 border border-green-700 rounded text-green-300 text-sm">
          Upserted {uploadResult.upserted} vessels.
        </div>
      )}
      {error && <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">{error}</div>}

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <input type="text" placeholder="Filter by name, IMO, type, flag..." value={filter}
          onChange={e => setFilter(e.target.value)}
          className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white" />
        <select value={ciiFilter} onChange={e => setCiiFilter(e.target.value)}
          className="bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white">
          <option value="">All CII</option>
          {['A','B','C','D','E'].map(r => <option key={r} value={r}>CII {r}</option>)}
        </select>
        <span className="text-xs text-gray-400 self-center">{filtered.length} vessels</span>
      </div>

      {loading ? (
        <div className="text-gray-400 text-sm">Loading...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400 text-left">
                {['IMO', 'Name', 'Type', 'Flag', 'DWT (t)', 'Propulsion', 'CO2 (tCO2e)', 'CII', 'EEXI', 'Year'].map(h => (
                  <th key={h} className="pb-2 pr-3 font-medium text-xs whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {filtered.slice(0, 500).map(v => (
                <tr key={v.id} className="hover:bg-gray-800">
                  <td className="py-1.5 pr-3 font-mono text-xs text-gray-300">{v.vessel_imo}</td>
                  <td className="py-1.5 pr-3 text-white text-xs">{v.vessel_name}</td>
                  <td className="py-1.5 pr-3 text-gray-400 text-xs">{v.vessel_type}</td>
                  <td className="py-1.5 pr-3 text-gray-400 text-xs">{v.flag_state}</td>
                  <td className="py-1.5 pr-3 text-white text-xs">{v.dwt_tonnes ? Number(v.dwt_tonnes).toLocaleString() : '—'}</td>
                  <td className="py-1.5 pr-3 text-gray-400 text-xs">{v.propulsion_type}</td>
                  <td className="py-1.5 pr-3 text-white text-xs">{v.annual_co2_tco2e ? Number(v.annual_co2_tco2e).toLocaleString() : '—'}</td>
                  <td className="py-1.5 pr-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-bold ${CII_STYLE[v.cii_rating] || 'bg-gray-700 text-gray-400'}`}>
                      {v.cii_rating || '—'}
                    </span>
                  </td>
                  <td className="py-1.5 pr-3 text-gray-400 text-xs">{v.eexi_value || '—'}</td>
                  <td className="py-1.5 pr-3 text-gray-400 text-xs">{v.data_year}</td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={10} className="py-8 text-center text-gray-500">No vessels found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
