import React, { useCallback, useEffect, useRef, useState } from 'react';

const API = 'http://localhost:8001/api/v1/data-intake/portfolio';
const TABS = ['Upload History', 'View Rows', 'Manual Entry'];

const CII_COLORS = { A: 'text-green-400', B: 'text-green-300', C: 'text-yellow-400', D: 'text-orange-400', E: 'text-red-400' };

export default function LoanPortfolioUpload() {
  const [tab, setTab] = useState(0);
  const [uploads, setUploads] = useState([]);
  const [rows, setRows] = useState([]);
  const [selectedUpload, setSelectedUpload] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [uploadName, setUploadName] = useState('');
  const [error, setError] = useState(null);
  const fileRef = useRef();

  const fetchUploads = useCallback(() => {
    setLoading(true);
    fetch(API)
      .then(r => r.json())
      .then(d => { setUploads(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  useEffect(() => { if (tab === 0) fetchUploads(); }, [tab, fetchUploads]);

  const fetchRows = useCallback((uploadId) => {
    setLoading(true);
    fetch(`${API}/${uploadId}/rows`)
      .then(r => r.json())
      .then(d => { setRows(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  useEffect(() => {
    if (tab === 1 && selectedUpload) fetchRows(selectedUpload);
  }, [tab, selectedUpload, fetchRows]);

  const handleFile = async (file) => {
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    form.append('upload_name', uploadName || file.name);
    setUploading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/upload`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      fetchUploads();
      setTab(0);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    window.open(`${API}/template`, '_blank');
  };

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-gray-100">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Loan Portfolio Upload</h1>
          <p className="text-gray-400 text-sm mt-1">
            Upload CSV files containing counterparty loan data for PCAF financed emissions.
          </p>
        </div>
        <button
          onClick={downloadTemplate}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-sm text-white rounded border border-gray-600"
        >
          Download Template
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">{error}</div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-gray-700 mb-6">
        {TABS.map((t, i) => (
          <button
            key={t}
            onClick={() => setTab(i)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === i
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Upload History */}
      {tab === 0 && (
        <div>
          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => {
              e.preventDefault();
              setDragOver(false);
              handleFile(e.dataTransfer.files[0]);
            }}
            onClick={() => fileRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer mb-6 transition-colors ${
              dragOver ? 'border-blue-400 bg-blue-900/20' : 'border-gray-600 hover:border-gray-500'
            }`}
          >
            <input ref={fileRef} type="file" accept=".csv" className="hidden"
              onChange={e => handleFile(e.target.files[0])} />
            {uploading ? (
              <p className="text-blue-400">Uploading...</p>
            ) : (
              <>
                <p className="text-gray-300 font-medium">Drop CSV file here or click to browse</p>
                <p className="text-gray-500 text-sm mt-1">
                  Required columns: counterparty_id, outstanding_amount, sector_gics, pcaf_dqs
                </p>
              </>
            )}
          </div>

          <div className="mb-4 flex gap-3 items-center">
            <input
              type="text"
              placeholder="Upload name (optional)"
              value={uploadName}
              onChange={e => setUploadName(e.target.value)}
              className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
            />
          </div>

          {loading ? (
            <div className="text-gray-400 text-sm">Loading...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700 text-gray-400 text-left">
                    {['ID', 'Name', 'Filename', 'Status', 'Rows', 'Valid', 'Errors', 'Uploaded'].map(h => (
                      <th key={h} className="pb-2 pr-4 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {uploads.map(u => (
                    <tr key={u.id}
                      className="hover:bg-gray-800 cursor-pointer"
                      onClick={() => { setSelectedUpload(u.id); setTab(1); }}
                    >
                      <td className="py-2 pr-4 text-gray-400">{u.id}</td>
                      <td className="py-2 pr-4 text-white">{u.upload_name}</td>
                      <td className="py-2 pr-4 text-gray-400 text-xs">{u.filename}</td>
                      <td className="py-2 pr-4">
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          u.status === 'complete' ? 'bg-green-900 text-green-300'
                          : u.status === 'failed' ? 'bg-red-900 text-red-300'
                          : 'bg-yellow-900 text-yellow-300'
                        }`}>{u.status}</span>
                      </td>
                      <td className="py-2 pr-4 text-white">{u.total_rows}</td>
                      <td className="py-2 pr-4 text-green-400">{u.valid_rows}</td>
                      <td className="py-2 pr-4 text-red-400">{u.error_rows}</td>
                      <td className="py-2 pr-4 text-gray-400 text-xs">
                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                      </td>
                    </tr>
                  ))}
                  {uploads.length === 0 && (
                    <tr><td colSpan={8} className="py-8 text-center text-gray-500">No uploads yet</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* View Rows */}
      {tab === 1 && (
        <div>
          {!selectedUpload ? (
            <div className="text-gray-400 p-8 text-center">Select an upload from the Upload History tab</div>
          ) : loading ? (
            <div className="text-gray-400 text-sm">Loading rows...</div>
          ) : (
            <div className="overflow-x-auto">
              <p className="text-gray-400 text-sm mb-3">Showing rows for upload #{selectedUpload} ({rows.length} rows)</p>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700 text-gray-400 text-left">
                    {['Counterparty', 'Name', 'Type', 'Amount', 'CCY', 'Sector', 'Country', 'Stage', 'DQS', 'Valid'].map(h => (
                      <th key={h} className="pb-2 pr-3 font-medium text-xs whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {rows.map(r => (
                    <tr key={r.id} className={r.is_valid ? '' : 'bg-red-900/10'}>
                      <td className="py-1.5 pr-3 text-gray-300 font-mono text-xs">{r.counterparty_id}</td>
                      <td className="py-1.5 pr-3 text-white text-xs">{r.counterparty_name}</td>
                      <td className="py-1.5 pr-3 text-gray-400 text-xs">{r.instrument_type}</td>
                      <td className="py-1.5 pr-3 text-white text-xs">{Number(r.outstanding_amount || 0).toLocaleString()}</td>
                      <td className="py-1.5 pr-3 text-gray-400 text-xs">{r.currency}</td>
                      <td className="py-1.5 pr-3 text-gray-400 text-xs">{r.sector_gics}</td>
                      <td className="py-1.5 pr-3 text-gray-400 text-xs">{r.country_iso2}</td>
                      <td className="py-1.5 pr-3 text-gray-400 text-xs">{r.stage_ifrs9}</td>
                      <td className="py-1.5 pr-3 text-gray-300 text-xs">{r.pcaf_dqs}</td>
                      <td className="py-1.5 pr-3">
                        <span className={`text-xs ${r.is_valid ? 'text-green-400' : 'text-red-400'}`}>
                          {r.is_valid ? 'Y' : 'N'}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {rows.length === 0 && (
                    <tr><td colSpan={10} className="py-6 text-center text-gray-500">No rows</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Manual Entry */}
      {tab === 2 && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-sm">Manual row entry is available via the CSV upload.</p>
          <p className="text-xs mt-2">Download the template, fill it in, and upload it above.</p>
          <button
            onClick={downloadTemplate}
            className="mt-4 px-4 py-2 bg-blue-700 hover:bg-blue-600 text-sm text-white rounded"
          >
            Download CSV Template
          </button>
        </div>
      )}
    </div>
  );
}
