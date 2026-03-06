import React, { useEffect, useState } from 'react';

const API = 'http://localhost:8001/api/v1/data-intake/steel-borrowers';

// CO2 intensities (tCO2/tCS) — worldsteel averages
const CO2_BF_BOF = 2.32;
const CO2_EAF = 0.67;
const CO2_DRI = 1.43;

const empty = {
  borrower_id: '', borrower_name: '', country_iso2: '',
  crude_steel_production_mt: '', bf_bof_share_pct: 0, eaf_share_pct: 0, dri_share_pct: 0,
  sbti_committed: false, data_year: new Date().getFullYear() - 1, notes: '',
};

export default function SteelBorrowersEntry() {
  const [borrowers, setBorrowers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);

  const fetchBorrowers = () => {
    setLoading(true);
    fetch(API).then(r => r.json())
      .then(d => { setBorrowers(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  };

  useEffect(() => { fetchBorrowers(); }, []);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const blended = (
    (form.bf_bof_share_pct / 100) * CO2_BF_BOF +
    (form.eaf_share_pct / 100) * CO2_EAF +
    (form.dri_share_pct / 100) * CO2_DRI
  ).toFixed(3);

  const totalShare = parseFloat(form.bf_bof_share_pct) + parseFloat(form.eaf_share_pct) + parseFloat(form.dri_share_pct);
  const totalCo2Estimate = form.crude_steel_production_mt
    ? (parseFloat(blended) * parseFloat(form.crude_steel_production_mt)).toFixed(0)
    : null;

  const selectBorrower = (b) => {
    setSelected(b.borrower_id);
    setForm({
      borrower_id: b.borrower_id,
      borrower_name: b.borrower_name || '',
      country_iso2: b.country_iso2 || '',
      crude_steel_production_mt: b.crude_steel_production_mt || '',
      bf_bof_share_pct: parseFloat(b.bf_bof_share_pct) || 0,
      eaf_share_pct: parseFloat(b.eaf_share_pct) || 0,
      dri_share_pct: parseFloat(b.dri_share_pct) || 0,
      sbti_committed: b.sbti_committed || false,
      data_year: b.data_year || new Date().getFullYear() - 1,
      notes: b.notes || '',
    });
    setSaved(false);
    setError(null);
  };

  const newBorrower = () => { setSelected(null); setForm(empty); setSaved(false); setError(null); };

  const handleSave = async () => {
    setSaving(true); setError(null);
    try {
      const payload = {
        ...form,
        crude_steel_production_mt: form.crude_steel_production_mt === '' ? null : parseFloat(form.crude_steel_production_mt),
        bf_bof_share_pct: parseFloat(form.bf_bof_share_pct),
        eaf_share_pct: parseFloat(form.eaf_share_pct),
        dri_share_pct: parseFloat(form.dri_share_pct),
        data_year: parseInt(form.data_year),
      };
      const res = await fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Save failed');
      setSaved(true);
      fetchBorrowers();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this borrower?')) return;
    await fetch(`${API}/${id}`, { method: 'DELETE' });
    fetchBorrowers();
    if (selected === id) { setSelected(null); setForm(empty); }
  };

  const Slider = ({ label, field, color }) => (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-sm text-gray-300">{label}</span>
        <span className={`text-sm font-bold ${color}`}>{form[field]}%</span>
      </div>
      <input type="range" min={0} max={100} step={1} value={form[field]}
        onChange={e => set(field, parseFloat(e.target.value))}
        className="w-full accent-blue-500" />
    </div>
  );

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-gray-100">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Steel Borrowers</h1>
        <p className="text-gray-400 text-sm mt-1">
          Production route blend and CO2 intensity per steel borrower. Blended intensity = weighted average of BF-BOF, EAF, DRI.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: borrower list */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          <div className="p-3 border-b border-gray-700 flex items-center justify-between">
            <span className="text-sm font-semibold text-gray-300">Borrowers ({borrowers.length})</span>
            <button onClick={newBorrower}
              className="text-xs px-2 py-1 bg-blue-700 hover:bg-blue-600 text-white rounded">
              + New
            </button>
          </div>
          {loading ? (
            <div className="p-4 text-gray-500 text-sm">Loading...</div>
          ) : (
            <div className="divide-y divide-gray-700 max-h-[60vh] overflow-y-auto">
              {borrowers.map(b => (
                <div key={b.borrower_id}
                  onClick={() => selectBorrower(b)}
                  className={`p-3 cursor-pointer hover:bg-gray-700 ${selected === b.borrower_id ? 'bg-blue-900/30 border-l-2 border-blue-500' : ''}`}
                >
                  <div className="font-medium text-sm text-white">{b.borrower_name || b.borrower_id}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-400">{b.country_iso2}</span>
                    <span className="text-xs text-blue-300 font-mono">
                      {parseFloat(b.blended_co2_intensity_tco2_tcs || 0).toFixed(2)} tCO2/tCS
                    </span>
                    {b.sbti_committed && (
                      <span className="text-xs bg-green-900 text-green-300 px-1.5 rounded">SBTi</span>
                    )}
                  </div>
                </div>
              ))}
              {borrowers.length === 0 && (
                <div className="p-4 text-gray-500 text-sm text-center">No borrowers yet</div>
              )}
            </div>
          )}
        </div>

        {/* Right: form */}
        <div className="lg:col-span-2 space-y-5">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Borrower ID *">
              <input value={form.borrower_id} onChange={e => set('borrower_id', e.target.value)}
                disabled={!!selected}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white text-sm disabled:opacity-60" />
            </Field>
            <Field label="Name">
              <input value={form.borrower_name} onChange={e => set('borrower_name', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white text-sm" />
            </Field>
            <Field label="Country (ISO2)">
              <input value={form.country_iso2} onChange={e => set('country_iso2', e.target.value.toUpperCase())}
                maxLength={2} className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white text-sm" />
            </Field>
            <Field label="Crude Steel Production (Mt/yr)">
              <input type="number" value={form.crude_steel_production_mt} onChange={e => set('crude_steel_production_mt', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white text-sm" />
            </Field>
            <Field label="Data Year">
              <select value={form.data_year} onChange={e => set('data_year', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white text-sm">
                {[2024, 2023, 2022, 2021, 2020].map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </Field>
            <div className="flex items-center gap-3 pt-5">
              <input type="checkbox" id="sbti" checked={form.sbti_committed}
                onChange={e => set('sbti_committed', e.target.checked)} className="w-4 h-4 accent-green-500" />
              <label htmlFor="sbti" className="text-sm text-gray-300">SBTi Committed</label>
            </div>
          </div>

          {/* Production route sliders */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 space-y-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-gray-300">Production Route Mix</span>
              <span className={`text-xs font-mono ${totalShare > 100.1 ? 'text-red-400' : 'text-gray-400'}`}>
                Sum: {totalShare.toFixed(1)}%
              </span>
            </div>
            <Slider label="BF-BOF (Blast Furnace)" field="bf_bof_share_pct" color="text-orange-400" />
            <Slider label="EAF (Electric Arc Furnace)" field="eaf_share_pct" color="text-blue-400" />
            <Slider label="DRI (Direct Reduced Iron)" field="dri_share_pct" color="text-purple-400" />

            {totalShare > 100.1 && (
              <div className="text-xs text-red-400">Share sum exceeds 100% — adjust sliders before saving.</div>
            )}
          </div>

          {/* Computed metrics */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <div className="text-xl font-bold text-blue-300">{blended}</div>
              <div className="text-xs text-gray-400 mt-1">Blended CO2 Intensity (tCO2/tCS)</div>
            </div>
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <div className="text-xl font-bold text-white">
                {totalCo2Estimate ? Number(totalCo2Estimate).toLocaleString() : '—'}
              </div>
              <div className="text-xs text-gray-400 mt-1">Estimated Total CO2 (tCO2e/yr)</div>
            </div>
          </div>

          {/* CO2 by reference table */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
            <div className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Reference Intensities (worldsteel)</div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              {[['BF-BOF', CO2_BF_BOF, 'text-orange-400'], ['EAF', CO2_EAF, 'text-blue-400'], ['DRI', CO2_DRI, 'text-purple-400']].map(([r, v, c]) => (
                <div key={r} className="text-center">
                  <div className={`font-bold text-base ${c}`}>{v}</div>
                  <div className="text-gray-500">{r} (tCO2/tCS)</div>
                </div>
              ))}
            </div>
          </div>

          <Field label="Notes">
            <textarea value={form.notes} onChange={e => set('notes', e.target.value)} rows={2}
              className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white text-sm" />
          </Field>

          {error && <div className="p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">{error}</div>}
          {saved && <div className="p-3 bg-green-900/30 border border-green-700 rounded text-green-300 text-sm">Saved successfully.</div>}

          <div className="flex gap-3">
            <button onClick={handleSave} disabled={saving || !form.borrower_id || totalShare > 100.1}
              className="px-5 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-sm text-white rounded">
              {saving ? 'Saving...' : selected ? 'Update' : 'Save'}
            </button>
            {selected && (
              <button onClick={() => handleDelete(form.borrower_id)}
                className="px-5 py-2 bg-red-800 hover:bg-red-700 text-sm text-white rounded">
                Delete
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-400 mb-1">{label}</label>
      {children}
    </div>
  );
}
