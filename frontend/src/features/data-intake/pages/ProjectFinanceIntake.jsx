import React, { useEffect, useState } from 'react';

const API = 'http://localhost:8001/api/v1/data-intake/project-finance';

const STEPS = [
  'Project Details', 'Capacity & CapEx', 'Financing Structure',
  'Revenue & Costs', 'Carbon Credits', 'Risk Classification', 'Review & Save',
];

const PROJECT_TYPES = ['solar','wind','hydro','storage','ccs','waste_to_energy','biomass','geothermal','other'];
const EP_CATS = [
  { v: 'A', label: 'Category A', desc: 'Significant adverse social or environmental impacts' },
  { v: 'B', label: 'Category B', desc: 'Limited adverse social or environmental impacts' },
  { v: 'C', label: 'Category C', desc: 'Minimal or no social or environmental impacts' },
];

const empty = {
  project_name: '', project_type: 'solar', country_iso2: '',
  capacity_mw: '', total_capex_musd: '', debt_musd: '', equity_musd: '',
  annual_revenue_musd: '', annual_opex_musd: '', annual_debt_service_musd: '',
  project_life_yrs: 25, capacity_factor_pct: '', discount_rate_pct: 8.0,
  include_carbon_credits: false, carbon_credit_price_usd: '', annual_co2_avoided_tco2e: '',
  equator_principles_category: 'B', paris_alignment_status: 'under_review', notes: '',
};

export default function ProjectFinanceIntake() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(empty);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [view, setView] = useState('list');

  const fetchProjects = () => {
    setLoading(true);
    fetch(API).then(r => r.json())
      .then(d => { setProjects(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  };

  useEffect(() => { fetchProjects(); }, []);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));
  const n = (v) => v === '' ? null : parseFloat(v);

  const handleSave = async () => {
    setSaving(true); setError(null);
    try {
      const payload = {
        ...form,
        capacity_mw: n(form.capacity_mw),
        total_capex_musd: n(form.total_capex_musd),
        debt_musd: n(form.debt_musd),
        equity_musd: n(form.equity_musd),
        annual_revenue_musd: n(form.annual_revenue_musd),
        annual_opex_musd: n(form.annual_opex_musd),
        annual_debt_service_musd: n(form.annual_debt_service_musd),
        project_life_yrs: parseInt(form.project_life_yrs),
        capacity_factor_pct: n(form.capacity_factor_pct),
        discount_rate_pct: n(form.discount_rate_pct),
        carbon_credit_price_usd: n(form.carbon_credit_price_usd),
        annual_co2_avoided_tco2e: n(form.annual_co2_avoided_tco2e),
      };
      const res = await fetch(API, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Save failed');
      setResult(data);
      fetchProjects();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this project?')) return;
    await fetch(`${API}/${id}`, { method: 'DELETE' });
    fetchProjects();
  };

  const resetWizard = () => { setForm(empty); setStep(0); setResult(null); setError(null); };

  // List view
  if (view === 'list') {
    return (
      <div className="p-6 bg-gray-900 min-h-screen text-gray-100">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Project Finance</h1>
            <p className="text-gray-400 text-sm mt-1">
              Renewable energy and green infrastructure project assessments with DSCR, LCOE and equity IRR.
            </p>
          </div>
          <button onClick={() => { resetWizard(); setView('wizard'); }}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-sm text-white rounded">
            + New Project
          </button>
        </div>

        {error && <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">{error}</div>}

        {loading ? <div className="text-gray-400 text-sm">Loading...</div> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 text-left">
                  {['Ref', 'Name', 'Type', 'Country', 'MW', 'CapEx (M$)', 'DSCR', 'LCOE ($/MWh)', 'IRR %', 'Paris', 'Status'].map(h => (
                    <th key={h} className="pb-2 pr-3 font-medium text-xs whitespace-nowrap">{h}</th>
                  ))}
                  <th className="pb-2 text-xs">Del</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {projects.map(p => (
                  <tr key={p.id} className="hover:bg-gray-800">
                    <td className="py-1.5 pr-3 font-mono text-xs text-gray-400">{p.project_ref}</td>
                    <td className="py-1.5 pr-3 text-white text-xs">{p.project_name}</td>
                    <td className="py-1.5 pr-3 text-gray-400 text-xs">{p.project_type}</td>
                    <td className="py-1.5 pr-3 text-gray-400 text-xs">{p.country_iso2}</td>
                    <td className="py-1.5 pr-3 text-white text-xs">{p.capacity_mw || '—'}</td>
                    <td className="py-1.5 pr-3 text-white text-xs">{p.total_capex_musd || '—'}</td>
                    <td className={`py-1.5 pr-3 text-xs font-medium ${
                      p.preliminary_dscr >= 1.3 ? 'text-green-400' : p.preliminary_dscr >= 1.0 ? 'text-yellow-400' : 'text-red-400'
                    }`}>{p.preliminary_dscr ? Number(p.preliminary_dscr).toFixed(2) : '—'}</td>
                    <td className="py-1.5 pr-3 text-white text-xs">{p.preliminary_lcoe_usd_mwh ? Number(p.preliminary_lcoe_usd_mwh).toFixed(1) : '—'}</td>
                    <td className="py-1.5 pr-3 text-white text-xs">{p.preliminary_equity_irr_pct ? `${Number(p.preliminary_equity_irr_pct).toFixed(1)}%` : '—'}</td>
                    <td className="py-1.5 pr-3">
                      <span className={`px-1.5 py-0.5 rounded text-xs ${
                        p.paris_alignment_status === 'aligned' ? 'bg-green-900 text-green-300'
                        : p.paris_alignment_status === 'misaligned' ? 'bg-red-900 text-red-300'
                        : 'bg-gray-700 text-gray-400'
                      }`}>{p.paris_alignment_status}</span>
                    </td>
                    <td className="py-1.5 pr-3">
                      <span className={`px-1.5 py-0.5 rounded text-xs ${
                        p.status === 'approved' ? 'bg-green-900 text-green-300'
                        : p.status === 'draft' ? 'bg-gray-700 text-gray-400'
                        : 'bg-blue-900 text-blue-300'
                      }`}>{p.status}</span>
                    </td>
                    <td className="py-1.5">
                      <button onClick={() => handleDelete(p.id)} className="text-red-400 hover:text-red-300 text-xs">✕</button>
                    </td>
                  </tr>
                ))}
                {projects.length === 0 && (
                  <tr><td colSpan={12} className="py-8 text-center text-gray-500">No projects yet</td></tr>
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
        <h1 className="text-xl font-bold text-white">New Project Finance Record</h1>
      </div>

      {/* Steps */}
      <div className="flex gap-1 mb-8 overflow-x-auto pb-1">
        {STEPS.map((s, i) => (
          <div key={s} className="flex items-center shrink-0">
            <button onClick={() => !result && setStep(i)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs ${
                i === step ? 'bg-blue-600 text-white' : i < step ? 'bg-gray-700 text-green-400' : 'bg-gray-800 text-gray-500'
              }`}>
              <span className="font-bold">{i < step ? '✓' : i + 1}</span>
              <span className="hidden sm:inline">{s}</span>
            </button>
            {i < STEPS.length - 1 && <div className={`w-4 h-px mx-1 ${i < step ? 'bg-green-600' : 'bg-gray-700'}`} />}
          </div>
        ))}
      </div>

      <div className="max-w-2xl">
        {/* Step 0: Project Details */}
        {step === 0 && (
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <Field label="Project Name *">
                <input value={form.project_name} onChange={e => set('project_name', e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
              </Field>
            </div>
            <Field label="Project Type">
              <select value={form.project_type} onChange={e => set('project_type', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white">
                {PROJECT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </Field>
            <Field label="Country (ISO2)">
              <input value={form.country_iso2} onChange={e => set('country_iso2', e.target.value.toUpperCase())} maxLength={2}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
            <Field label="Project Life (years)">
              <input type="number" value={form.project_life_yrs} onChange={e => set('project_life_yrs', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
            <Field label="Discount Rate (%)">
              <input type="number" step="0.5" value={form.discount_rate_pct} onChange={e => set('discount_rate_pct', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
          </div>
        )}

        {/* Step 1: Capacity & CapEx */}
        {step === 1 && (
          <div className="grid grid-cols-2 gap-4">
            <Field label="Capacity (MW)">
              <input type="number" value={form.capacity_mw} onChange={e => set('capacity_mw', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
            <Field label="Capacity Factor (%)">
              <input type="number" step="0.1" value={form.capacity_factor_pct} onChange={e => set('capacity_factor_pct', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
            <div className="col-span-2">
              <Field label="Total CapEx (M USD)">
                <input type="number" value={form.total_capex_musd} onChange={e => set('total_capex_musd', e.target.value)}
                  className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
              </Field>
            </div>
          </div>
        )}

        {/* Step 2: Financing */}
        {step === 2 && (
          <div className="grid grid-cols-2 gap-4">
            <Field label="Debt (M USD)">
              <input type="number" value={form.debt_musd} onChange={e => set('debt_musd', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
            <Field label="Equity (M USD)">
              <input type="number" value={form.equity_musd} onChange={e => set('equity_musd', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
            <Field label="Annual Debt Service (M USD)">
              <input type="number" value={form.annual_debt_service_musd} onChange={e => set('annual_debt_service_musd', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
            {form.debt_musd && form.total_capex_musd && (
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 flex flex-col justify-center">
                <div className="text-lg font-bold text-white">
                  {(parseFloat(form.debt_musd) / parseFloat(form.total_capex_musd) * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-400">Debt/CapEx ratio</div>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Revenue & Costs */}
        {step === 3 && (
          <div className="grid grid-cols-2 gap-4">
            <Field label="Annual Revenue (M USD)">
              <input type="number" value={form.annual_revenue_musd} onChange={e => set('annual_revenue_musd', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
            <Field label="Annual OpEx (M USD)">
              <input type="number" value={form.annual_opex_musd} onChange={e => set('annual_opex_musd', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
            {form.annual_revenue_musd && form.annual_opex_musd && (
              <div className="col-span-2 bg-gray-800 border border-gray-700 rounded-lg p-3">
                <div className="text-lg font-bold text-white">
                  {(parseFloat(form.annual_revenue_musd) - parseFloat(form.annual_opex_musd)).toFixed(2)} M USD
                </div>
                <div className="text-xs text-gray-400">Preliminary EBITDA/yr</div>
              </div>
            )}
          </div>
        )}

        {/* Step 4: Carbon Credits */}
        {step === 4 && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-3 bg-gray-800 border border-gray-700 rounded-lg">
              <input type="checkbox" id="cc" checked={form.include_carbon_credits}
                onChange={e => set('include_carbon_credits', e.target.checked)} className="w-4 h-4 accent-green-500" />
              <label htmlFor="cc" className="text-sm text-white">Include carbon credit revenue</label>
            </div>
            {form.include_carbon_credits && (
              <div className="grid grid-cols-2 gap-4">
                <Field label="Carbon Credit Price (USD/tCO2)">
                  <input type="number" value={form.carbon_credit_price_usd} onChange={e => set('carbon_credit_price_usd', e.target.value)}
                    className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
                </Field>
                <Field label="Annual CO2 Avoided (tCO2e)">
                  <input type="number" value={form.annual_co2_avoided_tco2e} onChange={e => set('annual_co2_avoided_tco2e', e.target.value)}
                    className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
                </Field>
                {form.carbon_credit_price_usd && form.annual_co2_avoided_tco2e && (
                  <div className="col-span-2 bg-gray-800 border border-gray-700 rounded-lg p-3">
                    <div className="text-lg font-bold text-green-400">
                      {(parseFloat(form.carbon_credit_price_usd) * parseFloat(form.annual_co2_avoided_tco2e) / 1_000_000).toFixed(2)} M USD/yr
                    </div>
                    <div className="text-xs text-gray-400">Carbon credit revenue estimate</div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Step 5: Risk Classification */}
        {step === 5 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Equator Principles Category</label>
              {EP_CATS.map(c => (
                <label key={c.v} className={`flex items-start gap-3 p-3 rounded-lg border mb-2 cursor-pointer ${
                  form.equator_principles_category === c.v ? 'border-blue-500 bg-blue-900/20' : 'border-gray-700 hover:border-gray-600'
                }`}>
                  <input type="radio" name="ep" value={c.v} checked={form.equator_principles_category === c.v}
                    onChange={() => set('equator_principles_category', c.v)} className="mt-0.5" />
                  <div>
                    <div className="text-white font-medium text-sm">{c.label}</div>
                    <div className="text-xs text-gray-400">{c.desc}</div>
                  </div>
                </label>
              ))}
            </div>
            <Field label="Paris Alignment Status">
              <select value={form.paris_alignment_status} onChange={e => set('paris_alignment_status', e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white">
                {['aligned', 'misaligned', 'under_review'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </Field>
            <Field label="Notes">
              <textarea value={form.notes} onChange={e => set('notes', e.target.value)} rows={3}
                className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-2 text-white" />
            </Field>
          </div>
        )}

        {/* Step 6: Review & Save */}
        {step === 6 && (
          <div>
            {result ? (
              <div className="space-y-4">
                <div className="p-4 bg-green-900/30 border border-green-700 rounded text-green-300">
                  Project saved: <strong>{result.project_ref}</strong>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { label: 'DSCR', value: result.preliminary_dscr ? Number(result.preliminary_dscr).toFixed(2) : '—', ok: result.preliminary_dscr >= 1.3 },
                    { label: 'LCOE ($/MWh)', value: result.preliminary_lcoe_usd_mwh ? Number(result.preliminary_lcoe_usd_mwh).toFixed(1) : '—', ok: true },
                    { label: 'Equity IRR', value: result.preliminary_equity_irr_pct ? `${Number(result.preliminary_equity_irr_pct).toFixed(1)}%` : '—', ok: result.preliminary_equity_irr_pct > 8 },
                  ].map(m => (
                    <div key={m.label} className="bg-gray-800 border border-gray-700 rounded-lg p-3 text-center">
                      <div className={`text-xl font-bold ${m.ok ? 'text-white' : 'text-yellow-400'}`}>{m.value}</div>
                      <div className="text-xs text-gray-400 mt-1">{m.label}</div>
                    </div>
                  ))}
                </div>
                <button onClick={() => { resetWizard(); setView('list'); }}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-sm text-white rounded">
                  View All Projects
                </button>
              </div>
            ) : (
              <>
                <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 text-sm space-y-2 mb-4">
                  {[
                    ['Project', form.project_name],
                    ['Type', form.project_type],
                    ['Country', form.country_iso2],
                    ['Capacity', form.capacity_mw ? `${form.capacity_mw} MW` : '—'],
                    ['CapEx', form.total_capex_musd ? `$${form.total_capex_musd}M` : '—'],
                    ['EP Category', form.equator_principles_category],
                    ['Paris', form.paris_alignment_status],
                    ['Carbon Credits', form.include_carbon_credits ? 'Yes' : 'No'],
                  ].map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-gray-400">{k}</span>
                      <span className="text-white font-medium">{v}</span>
                    </div>
                  ))}
                </div>
                {error && <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded text-red-300 text-sm">{error}</div>}
              </>
            )}
          </div>
        )}

        {/* Nav */}
        {!result && (
          <div className="flex justify-between mt-8">
            <button
              onClick={() => step > 0 ? setStep(s => s - 1) : setView('list')}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-sm text-white rounded">
              {step === 0 ? 'Cancel' : 'Back'}
            </button>
            {step < STEPS.length - 1 ? (
              <button onClick={() => setStep(s => s + 1)} disabled={step === 0 && !form.project_name}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-sm text-white rounded">
                Next
              </button>
            ) : (
              <button onClick={handleSave} disabled={saving}
                className="px-4 py-2 bg-green-600 hover:bg-green-500 disabled:opacity-40 text-sm text-white rounded">
                {saving ? 'Computing & Saving...' : 'Save Project'}
              </button>
            )}
          </div>
        )}
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
