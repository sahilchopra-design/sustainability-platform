import React, { useEffect, useState } from 'react';

const API = 'http://localhost:8001/api/v1/data-intake/counterparty';
const STEPS = ['Find Entity', 'Reporting Year', 'Data Source', 'Enter Emissions', 'Evidence', 'Confirm'];

const DQS_OPTIONS = [
  { value: 'direct_measurement', label: 'Direct Measurement', dqs: 1, desc: 'Metered / sensor data' },
  { value: 'audited_report',     label: 'Audited Report',     dqs: 2, desc: 'Third-party assured disclosure' },
  { value: 'self_reported',      label: 'Self-Reported',      dqs: 3, desc: 'Company-reported without assurance' },
  { value: 'sector_average',     label: 'Sector Average',     dqs: 4, desc: 'Industry proxy / PCAF factor' },
  { value: 'estimated',          label: 'Estimated',          dqs: 5, desc: 'Internal modelled estimate' },
];

const DQS_COLORS = { 1: 'text-green-400', 2: 'text-green-300', 3: 'text-yellow-400', 4: 'text-orange-400', 5: 'text-red-400' };

const empty = {
  counterparty_id: '', counterparty_name: '', reporting_year: new Date().getFullYear() - 1,
  scope1_tco2e: '', scope2_market_tco2e: '', scope2_location_tco2e: '',
  scope3_total_tco2e: '', scope3_cat1_purchased_goods: '',
  scope3_cat11_use_of_sold_products: '', scope3_cat15_investments: '',
  data_source_type: 'self_reported', evidence_url: '', assurance_level: 'none', notes: '',
};

export default function CounterpartyEmissionsWizard() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(empty);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);
  const [view, setView] = useState('list'); // 'list' | 'wizard'

  const fetchRecords = () => {
    setLoading(true);
    fetch(API).then(r => r.json())
      .then(d => { setRecords(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  };

  useEffect(() => { fetchRecords(); }, []);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const reset = () => { setForm(empty); setStep(0); setSaved(false); setError(null); };

  const handleSave = async () => {
    setSaving(true); setError(null);
    try {
      const payload = { ...form };
      Object.keys(payload).forEach(k => {
        if (['scope1_tco2e','scope2_market_tco2e','scope2_location_tco2e',
             'scope3_total_tco2e','scope3_cat1_purchased_goods',
             'scope3_cat11_use_of_sold_products','scope3_cat15_investments'].includes(k)) {
          payload[k] = payload[k] === '' ? null : parseFloat(payload[k]);
        }
      });
      payload.reporting_year = parseInt(payload.reporting_year);
      const res = await fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Save failed'); }
      setSaved(true);
      fetchRecords();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this record?')) return;
    await fetch(`${API}/${id}`, { method: 'DELETE' });
    fetchRecords();
  };

  const selectedDqs = DQS_OPTIONS.find(d => d.value === form.data_source_type);

  if (view === 'list') {
    return (
      <div className="p-6 bg-gray-900 min-h-screen text-gray-100">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Counterparty Emissions</h1>
            <p className="text-gray-400 text-sm mt-1">
              Scope 1/2/3 emissions per counterparty with PCAF Data Quality Score.
            </p>
          </div>
          <button
            onClick={() => { reset(); setView('wizard'); }}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-sm text-white rounded"
          >
            + Add Counterparty
          </button>
        </div>

        {error && <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">{error}</div>}

        {loading ? (
          <div className="text-gray-400 text-sm">Loading...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  {['Counterparty ID', 'Name', 'Year', 'Scope 1', 'Scope 2 (mkt)', 'Scope 3', 'DQS', 'Source', 'Assurance'].map(h => (
                    <th key={h} className="pb-2 pr-4 font-medium text-xs">{h}</th>
                  ))}
                  <th className="pb-2 font-medium text-xs">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {records.map(r => (
                  <tr key={r.id} className="hover:bg-gray-800">
                    <td className="py-2 pr-4 font-mono text-xs text-gray-300">{r.counterparty_id}</td>
                    <td className="py-2 pr-4 text-white text-xs">{r.counterparty_name || '—'}</td>
                    <td className="py-2 pr-4 text-gray-300 text-xs">{r.reporting_year}</td>
                    <td className="py-2 pr-4 text-white text-xs">{r.scope1_tco2e != null ? Number(r.scope1_tco2e).toLocaleString() : '—'}</td>
                    <td className="py-2 pr-4 text-white text-xs">{r.scope2_market_tco2e != null ? Number(r.scope2_market_tco2e).toLocaleString() : '—'}</td>
                    <td className="py-2 pr-4 text-white text-xs">{r.scope3_total_tco2e != null ? Number(r.scope3_total_tco2e).toLocaleString() : '—'}</td>
                    <td className={`py-2 pr-4 font-bold text-xs ${DQS_COLORS[r.pcaf_dqs] || 'text-gray-400'}`}>{r.pcaf_dqs}</td>
                    <td className="py-2 pr-4 text-gray-400 text-xs">{r.data_source_type}</td>
                    <td className="py-2 pr-4 text-gray-400 text-xs">{r.assurance_level}</td>
                    <td className="py-2">
                      <button onClick={() => handleDelete(r.id)} className="text-red-400 hover:text-red-300 text-xs">Delete</button>
                    </td>
                  </tr>
                ))}
                {records.length === 0 && (
                  <tr><td colSpan={10} className="py-8 text-center text-gray-500">No counterparty emissions recorded yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  }

  // Wizard view
  return (
    <div className="p-6 bg-gray-900 min-h-screen text-gray-100">
      <div className="mb-6 flex items-center gap-4">
        <button onClick={() => setView('list')} className="text-gray-400 hover:text-white text-sm">← Back</button>
        <h1 className="text-xl font-bold text-white">Add Counterparty Emissions</h1>
      </div>

      {/* Step indicator */}
      <div className="flex gap-1 mb-8">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center flex-1">
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
              i < step ? 'bg-green-600 text-white' : i === step ? 'bg-blue-600 text-white' : 'bg-gray-700 text-gray-400'
            }`}>{i < step ? '✓' : i + 1}</div>
            <div className={`text-xs ml-1.5 hidden sm:block ${i === step ? 'text-white' : 'text-gray-500'}`}>{s}</div>
            {i < STEPS.length - 1 && <div className={`flex-1 h-px mx-2 ${i < step ? 'bg-green-600' : 'bg-gray-700'}`} />}
          </div>
        ))}
      </div>

      <div className="max-w-xl">
        {/* Step 0: Entity */}
        {step === 0 && (
          <div className="space-y-4">
            <Field label="Counterparty ID *" hint="e.g. LEI, internal ID">
              <input value={form.counterparty_id} onChange={e => set('counterparty_id', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" placeholder="CP001" />
            </Field>
            <Field label="Counterparty Name">
              <input value={form.counterparty_name} onChange={e => set('counterparty_name', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" placeholder="Acme Corp" />
            </Field>
          </div>
        )}

        {/* Step 1: Year */}
        {step === 1 && (
          <Field label="Reporting Year *">
            <select value={form.reporting_year} onChange={e => set('reporting_year', e.target.value)}
              className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white">
              {[2024, 2023, 2022, 2021, 2020, 2019].map(y => <option key={y} value={y}>{y}</option>)}
            </select>
          </Field>
        )}

        {/* Step 2: Data source / DQS */}
        {step === 2 && (
          <div className="space-y-3">
            <label className="text-sm font-medium text-gray-300">Data Source Type</label>
            {DQS_OPTIONS.map(opt => (
              <label key={opt.value} className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer ${
                form.data_source_type === opt.value ? 'border-blue-500 bg-blue-900/20' : 'border-gray-700 hover:border-gray-600'
              }`}>
                <input type="radio" name="dqs" value={opt.value}
                  checked={form.data_source_type === opt.value}
                  onChange={() => set('data_source_type', opt.value)} className="mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-white font-medium text-sm">{opt.label}</span>
                    <span className={`text-xs font-mono font-bold ${DQS_COLORS[opt.dqs]}`}>DQS {opt.dqs}</span>
                  </div>
                  <div className="text-xs text-gray-400">{opt.desc}</div>
                </div>
              </label>
            ))}
          </div>
        )}

        {/* Step 3: Emissions */}
        {step === 3 && (
          <div className="space-y-4">
            {[
              ['scope1_tco2e', 'Scope 1 (tCO2e)'],
              ['scope2_market_tco2e', 'Scope 2 Market-based (tCO2e)'],
              ['scope2_location_tco2e', 'Scope 2 Location-based (tCO2e)'],
              ['scope3_total_tco2e', 'Scope 3 Total (tCO2e)'],
              ['scope3_cat1_purchased_goods', 'Scope 3 Cat.1 Purchased Goods'],
              ['scope3_cat11_use_of_sold_products', 'Scope 3 Cat.11 Use of Sold Products'],
              ['scope3_cat15_investments', 'Scope 3 Cat.15 Investments'],
            ].map(([k, label]) => (
              <Field key={k} label={label}>
                <input type="number" value={form[k]} onChange={e => set(k, e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white"
                  placeholder="Leave blank if not available" />
              </Field>
            ))}
          </div>
        )}

        {/* Step 4: Evidence */}
        {step === 4 && (
          <div className="space-y-4">
            <Field label="Evidence URL">
              <input value={form.evidence_url} onChange={e => set('evidence_url', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="https://..." />
            </Field>
            <Field label="Assurance Level">
              <select value={form.assurance_level} onChange={e => set('assurance_level', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white">
                {['none', 'limited', 'reasonable'].map(a => <option key={a} value={a}>{a}</option>)}
              </select>
            </Field>
            <Field label="Notes">
              <textarea value={form.notes} onChange={e => set('notes', e.target.value)} rows={3}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
          </div>
        )}

        {/* Step 5: Confirm */}
        {step === 5 && (
          <div className="space-y-3">
            {saved ? (
              <div className="p-4 bg-green-900/30 border border-green-700 rounded text-green-300">
                Record saved successfully.
                <button onClick={() => { reset(); setView('list'); }} className="ml-4 text-sm underline">View All Records</button>
                <button onClick={reset} className="ml-4 text-sm underline">Add Another</button>
              </div>
            ) : (
              <>
                <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 text-sm space-y-2">
                  <Row label="Counterparty" value={`${form.counterparty_id} — ${form.counterparty_name || 'unnamed'}`} />
                  <Row label="Year" value={form.reporting_year} />
                  <Row label="DQS" value={`${selectedDqs?.dqs} — ${selectedDqs?.label}`} />
                  <Row label="Scope 1" value={form.scope1_tco2e ? `${Number(form.scope1_tco2e).toLocaleString()} tCO2e` : '—'} />
                  <Row label="Scope 2 (market)" value={form.scope2_market_tco2e ? `${Number(form.scope2_market_tco2e).toLocaleString()} tCO2e` : '—'} />
                  <Row label="Scope 3 Total" value={form.scope3_total_tco2e ? `${Number(form.scope3_total_tco2e).toLocaleString()} tCO2e` : '—'} />
                  <Row label="Assurance" value={form.assurance_level} />
                </div>
                {error && <div className="p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">{error}</div>}
              </>
            )}
          </div>
        )}

        {/* Navigation */}
        {!saved && (
          <div className="flex justify-between mt-8">
            <button
              onClick={() => step > 0 ? setStep(s => s - 1) : setView('list')}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-sm text-white rounded"
            >
              {step === 0 ? 'Cancel' : 'Back'}
            </button>
            {step < STEPS.length - 1 ? (
              <button
                onClick={() => setStep(s => s + 1)}
                disabled={step === 0 && !form.counterparty_id.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-sm text-white rounded"
              >
                Next
              </button>
            ) : (
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-40 text-sm text-white rounded"
              >
                {saving ? 'Saving...' : 'Save Record'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Field({ label, hint, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1">
        {label} {hint && <span className="text-gray-500 font-normal text-xs">({hint})</span>}
      </label>
      {children}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-400">{label}</span>
      <span className="text-white font-medium">{value}</span>
    </div>
  );
}
