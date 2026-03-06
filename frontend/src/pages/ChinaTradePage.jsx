/**
 * China Trade & Sustainability Platform
 * Route: /china-trade
 * Tabs: Exporter Intelligence | CBAM Exposure | Supplier Framework | China ESG & ETS | Trade Corridors | Carbon Marketplace | Connected Modules
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, ReferenceLine,
} from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || '';
const BASE = `${API}/api/v1/china-trade`;

// ─── Palette ────────────────────────────────────────────────────────────────
const C = {
  blue:   '#3b82f6',
  green:  '#22c55e',
  amber:  '#f59e0b',
  red:    '#ef4444',
  purple: '#a855f7',
  cyan:   '#06b6d4',
  indigo: '#6366f1',
  rose:   '#f43f5e',
  slate:  '#94a3b8',
};
const PIE_COLORS = [C.blue, C.green, C.amber, C.red, C.purple, C.cyan, C.indigo, C.rose];

// ─── Atoms ──────────────────────────────────────────────────────────────────
function Card({ children, className = '' }) {
  return (
    <div className={`bg-[#0e1829] border border-white/[0.07] rounded-xl p-5 ${className}`}>
      {children}
    </div>
  );
}

function SectionTitle({ children }) {
  return <h3 className="text-sm font-semibold text-white/60 uppercase tracking-widest mb-4">{children}</h3>;
}

function Stat({ label, value, sub, color = 'text-white' }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs text-white/40 uppercase tracking-wide">{label}</span>
      <span className={`text-2xl font-bold ${color}`}>{value}</span>
      {sub && <span className="text-xs text-white/40">{sub}</span>}
    </div>
  );
}

function Badge({ children, color = 'blue' }) {
  const map = {
    blue:   'bg-blue-500/15 text-blue-400 border-blue-500/20',
    green:  'bg-green-500/15 text-green-400 border-green-500/20',
    amber:  'bg-amber-500/15 text-amber-400 border-amber-500/20',
    red:    'bg-red-500/15 text-red-400 border-red-500/20',
    purple: 'bg-purple-500/15 text-purple-400 border-purple-500/20',
    cyan:   'bg-cyan-500/15 text-cyan-400 border-cyan-500/20',
    slate:  'bg-slate-500/15 text-slate-400 border-slate-500/20',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold border ${map[color] || map.blue}`}>
      {children}
    </span>
  );
}

function Spinner() {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

function Empty({ msg = 'No data available' }) {
  return <div className="text-center py-12 text-white/30 text-sm">{msg}</div>;
}

function TT({ active, payload, label, unit = '' }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0e1829] border border-white/[0.07] rounded-lg p-3 text-xs shadow-xl">
      {label && <p className="text-white/50 mb-2">{label}</p>}
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || '#fff' }}>
          {p.name}: <span className="font-bold">{typeof p.value === 'number' ? p.value.toLocaleString() : p.value}{unit}</span>
        </p>
      ))}
    </div>
  );
}

function ReadinessBand({ score }) {
  const band =
    score >= 80 ? { label: 'Leader',      color: 'green'  } :
    score >= 60 ? { label: 'Advanced',    color: 'blue'   } :
    score >= 40 ? { label: 'Developing',  color: 'amber'  } :
                  { label: 'Emerging',    color: 'red'    };
  return <Badge color={band.color}>{band.label}</Badge>;
}

// ─── Custom fetch hook ───────────────────────────────────────────────────────
function useFetch(url, deps = []) {
  const [data, setData]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!url) { setLoading(false); return; }
    setLoading(true);
    setError(null);
    fetch(url)
      .then(r => { if (!r.ok) throw new Error(r.statusText); return r.json(); })
      .then(d  => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading, error };
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 1 — Exporter Intelligence
// ═══════════════════════════════════════════════════════════════════════════════
function ExporterTab() {
  const [query, setQuery]   = useState('');
  const [sector, setSector] = useState('');
  const [minScore, setMin]  = useState(0);
  const [results, setResults] = useState(null);
  const [searching, setSearching] = useState(false);

  const { data: summary, loading: sumLoading } = useFetch(`${BASE}/exporters/cbam-readiness-summary`, []);

  const search = useCallback(() => {
    setSearching(true);
    const params = new URLSearchParams({ limit: 20 });
    if (query)   params.set('query', query);
    if (sector)  params.set('sector', sector);
    if (minScore > 0) params.set('min_cbam_readiness', minScore);
    fetch(`${BASE}/exporters/search?${params}`)
      .then(r => r.json())
      .then(d => { setResults(d); setSearching(false); })
      .catch(() => setSearching(false));
  }, [query, sector, minScore]);

  // auto-search on mount
  useEffect(() => { search(); }, []); // eslint-disable-line

  const bandData = summary ? Object.entries(summary.band_distribution || {}).map(([name, value]) => ({ name, value })) : [];
  const exporters = results?.exporters || [];

  return (
    <div className="space-y-6">
      {/* Summary strip */}
      {sumLoading ? <Spinner /> : summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card><Stat label="Total Exporters" value={summary.total_exporters ?? '—'} /></Card>
          <Card><Stat label="CBAM Applicable" value={summary.cbam_applicable ?? '—'} color="text-amber-400" /></Card>
          <Card><Stat label="Avg CBAM Readiness" value={`${summary.avg_cbam_readiness ?? '—'}`} sub="/ 100" color="text-blue-400" /></Card>
          <Card><Stat label="Avg Carbon Intensity" value={summary.avg_embedded_carbon_tco2_per_tonne ? `${summary.avg_embedded_carbon_tco2_per_tonne.toFixed(2)}` : '—'} sub="tCO₂ / tonne" color="text-red-400" /></Card>
        </div>
      )}

      {/* Readiness distribution chart */}
      {bandData.length > 0 && (
        <Card>
          <SectionTitle>CBAM Readiness Band Distribution</SectionTitle>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={bandData} margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <Tooltip content={<TT />} />
              <Bar dataKey="value" name="Companies" radius={[4, 4, 0, 0]}>
                {bandData.map((entry, i) => {
                  const color = entry.name === 'Leader' ? C.green : entry.name === 'Advanced' ? C.blue : entry.name === 'Developing' ? C.amber : C.red;
                  return <Cell key={i} fill={color} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Search filters */}
      <Card>
        <SectionTitle>Search Exporters</SectionTitle>
        <div className="flex flex-wrap gap-3 mb-4">
          <input
            className="flex-1 min-w-[200px] bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50"
            placeholder="Company name or keyword…"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && search()}
          />
          <select
            className="bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50"
            value={sector}
            onChange={e => setSector(e.target.value)}
          >
            <option value="">All Sectors</option>
            {['Steel', 'Aluminium', 'Cement', 'Chemicals', 'Energy', 'EV & Battery', 'Solar', 'Mining'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <div className="flex items-center gap-2">
            <span className="text-xs text-white/40">Min CBAM Score:</span>
            <input
              type="range" min={0} max={100} step={10}
              value={minScore}
              onChange={e => setMin(Number(e.target.value))}
              className="w-24 accent-blue-500"
            />
            <span className="text-xs text-blue-400 w-8">{minScore}</span>
          </div>
          <button
            onClick={search}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg transition-colors"
          >
            Search
          </button>
        </div>

        {searching ? <Spinner /> : exporters.length === 0 ? <Empty /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-white/40 border-b border-white/[0.07]">
                  <th className="text-left pb-2 pr-4">Company</th>
                  <th className="text-left pb-2 pr-4">Sector</th>
                  <th className="text-right pb-2 pr-4">CBAM Readiness</th>
                  <th className="text-right pb-2 pr-4">Carbon Intensity</th>
                  <th className="text-right pb-2 pr-4">vs EU Benchmark</th>
                  <th className="text-center pb-2 pr-4">CBAM</th>
                  <th className="text-left pb-2">Key Markets</th>
                </tr>
              </thead>
              <tbody>
                {exporters.map((e, i) => (
                  <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="py-2 pr-4">
                      <div className="font-semibold text-white">{e.entity_name}</div>
                      <div className="text-white/30">{e.entity_name_zh}</div>
                    </td>
                    <td className="py-2 pr-4 text-white/60">{e.sector}</td>
                    <td className="py-2 pr-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${e.cbam_readiness_score}%`,
                              backgroundColor: e.cbam_readiness_score >= 80 ? C.green : e.cbam_readiness_score >= 60 ? C.blue : e.cbam_readiness_score >= 40 ? C.amber : C.red,
                            }}
                          />
                        </div>
                        <span className="text-white font-bold">{e.cbam_readiness_score}</span>
                      </div>
                      <div className="mt-0.5 flex justify-end"><ReadinessBand score={e.cbam_readiness_score} /></div>
                    </td>
                    <td className="py-2 pr-4 text-right text-white">{e.avg_embedded_carbon_tco2_per_tonne?.toFixed(3)} tCO₂/t</td>
                    <td className="py-2 pr-4 text-right">
                      <span className={e.vs_eu_benchmark_pct > 0 ? 'text-red-400' : 'text-green-400'}>
                        {e.vs_eu_benchmark_pct > 0 ? '+' : ''}{e.vs_eu_benchmark_pct?.toFixed(1)}%
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-center">
                      {e.cbam_applicable ? <Badge color="amber">CBAM</Badge> : <Badge color="slate">N/A</Badge>}
                    </td>
                    <td className="py-2 text-white/50">{(e.key_export_markets || []).join(', ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 2 — CBAM Exposure Calculator (Auto-Fill)
// ═══════════════════════════════════════════════════════════════════════════════
function CBAMTab() {
  const [entityName, setEntityName] = useState('');
  const [hsCode, setHsCode]         = useState('');
  const [volume, setVolume]         = useState('');
  const [etsPriceEur, setEtsPrice]  = useState('65.0');
  const [autoFill, setAutoFill]     = useState(null);
  const [calc, setCalc]             = useState(null);
  const [loading, setLoading]       = useState(false);
  const [calcLoading, setCalcLoading] = useState(false);

  const { data: benchmarks } = useFetch(`${BASE}/cbam/hs-benchmarks`, []);

  const doAutoFill = () => {
    if (!entityName || !hsCode) return;
    setLoading(true);
    fetch(`${BASE}/cbam/supplier-lookup?entity_name=${encodeURIComponent(entityName)}&hs_code=${encodeURIComponent(hsCode)}`)
      .then(r => r.json())
      .then(d => { setAutoFill(d); setLoading(false); })
      .catch(() => setLoading(false));
  };

  const doCalculate = () => {
    if (!entityName || !hsCode || !volume) return;
    setCalcLoading(true);
    fetch(`${BASE}/cbam/calculate-liability`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entity_name: entityName,
        hs_code: hsCode,
        export_volume_tonnes: Number(volume),
        eu_ets_price_eur: Number(etsPriceEur),
      }),
    })
      .then(r => r.json())
      .then(d => { setCalc(d); setCalcLoading(false); })
      .catch(() => setCalcLoading(false));
  };

  const af = autoFill?.cbam_auto_fill;

  const waterfallData = calc ? [
    { name: 'Gross CBAM', value: calc.gross_cbam_liability_eur ?? 0 },
    { name: 'CETS Deduction', value: -(calc.cets_deduction_eur ?? 0) },
    { name: 'Net CBAM', value: calc.net_cbam_liability_eur ?? 0 },
  ] : [];

  return (
    <div className="space-y-6">
      {/* Input panel */}
      <Card>
        <SectionTitle>CBAM Liability Calculator — Auto-Fill from China Trade Data</SectionTitle>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-xs text-white/40 block mb-1">Supplier / Exporter Name</label>
            <input
              className="w-full bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50"
              placeholder="e.g. China Baowu Steel Group"
              value={entityName}
              onChange={e => setEntityName(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">HS-4 Code (CBAM Annex I)</label>
            <input
              className="w-full bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50"
              placeholder="e.g. 7208 (Steel) / 7601 (Aluminium)"
              value={hsCode}
              onChange={e => setHsCode(e.target.value)}
            />
          </div>
        </div>
        <button
          onClick={doAutoFill}
          disabled={loading || !entityName || !hsCode}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white text-sm font-semibold rounded-lg transition-colors mr-3"
        >
          {loading ? 'Fetching…' : 'Auto-Fill from China Trade Data'}
        </button>
      </Card>

      {/* Auto-fill results */}
      {af && (
        <Card className="border-blue-500/20">
          <SectionTitle>Auto-Fill Results — {autoFill.entity_name} / HS {autoFill.hs_code}</SectionTitle>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div>
              <span className="text-xs text-white/40 block">Embedded Carbon</span>
              <span className="text-lg font-bold text-white">{af.embedded_carbon_tco2_per_tonne} tCO₂/t</span>
            </div>
            <div>
              <span className="text-xs text-white/40 block">EU Benchmark</span>
              <span className="text-lg font-bold text-white">{af.eu_benchmark_tco2_per_tonne} tCO₂/t</span>
            </div>
            <div>
              <span className="text-xs text-white/40 block">Carbon Surplus vs Benchmark</span>
              <span className={`text-lg font-bold ${af.carbon_surplus_tco2_per_tonne > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {af.carbon_surplus_tco2_per_tonne > 0 ? '+' : ''}{af.carbon_surplus_tco2_per_tonne} tCO₂/t
              </span>
            </div>
            <div>
              <span className="text-xs text-white/40 block">CETS Price</span>
              <span className="text-lg font-bold text-amber-400">¥{af.cets_price_cny} / €{af.cets_price_eur}</span>
            </div>
          </div>
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 text-xs text-blue-300">
            <strong>Regulatory note:</strong> {af.art9_deductible
              ? `CETS carbon cost is deductible from CBAM obligation under EU CBAM Reg. 2023/956 Art. 9 (actual verified emissions approach).`
              : `This entity's CETS coverage does not qualify for Art. 9 CBAM deduction under current phase.`}
          </div>
        </Card>
      )}

      {/* Calculate section */}
      <Card>
        <SectionTitle>Calculate Net CBAM Liability</SectionTitle>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="text-xs text-white/40 block mb-1">Export Volume (tonnes)</label>
            <input
              type="number"
              className="w-full bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50"
              placeholder="e.g. 50000"
              value={volume}
              onChange={e => setVolume(e.target.value)}
            />
          </div>
          <div>
            <label className="text-xs text-white/40 block mb-1">EU ETS Price (€/tCO₂)</label>
            <input
              type="number"
              className="w-full bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50"
              value={etsPriceEur}
              onChange={e => setEtsPrice(e.target.value)}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={doCalculate}
              disabled={calcLoading || !entityName || !hsCode || !volume}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-sm font-semibold rounded-lg transition-colors"
            >
              {calcLoading ? 'Calculating…' : 'Calculate CBAM Liability'}
            </button>
          </div>
        </div>

        {calc && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-[#060c18] rounded-lg p-3">
                  <span className="text-xs text-white/40 block">Gross CBAM Liability</span>
                  <span className="text-xl font-bold text-white">€{(calc.gross_cbam_liability_eur || 0).toLocaleString()}</span>
                </div>
                <div className="bg-[#060c18] rounded-lg p-3">
                  <span className="text-xs text-white/40 block">CETS Art.9 Deduction</span>
                  <span className="text-xl font-bold text-green-400">-€{(calc.cets_deduction_eur || 0).toLocaleString()}</span>
                </div>
                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 col-span-2">
                  <span className="text-xs text-white/40 block">Net CBAM Obligation</span>
                  <span className="text-2xl font-bold text-blue-400">€{(calc.net_cbam_liability_eur || 0).toLocaleString()}</span>
                  <span className="text-xs text-white/30 block mt-0.5">€/tonne: {calc.cbam_per_tonne_eur?.toFixed(2)} · Total tCO₂: {calc.total_embedded_tco2?.toFixed(0)}</span>
                </div>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={waterfallData} margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip content={<TT unit=" €" />} />
                <Bar dataKey="value" name="EUR" radius={[4, 4, 0, 0]}>
                  {waterfallData.map((entry, i) => (
                    <Cell key={i} fill={entry.value < 0 ? C.green : i === 2 ? C.blue : C.amber} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      {/* HS Benchmark table */}
      {benchmarks && (
        <Card>
          <SectionTitle>EU CBAM Annex I — HS-4 Benchmark Reference Table</SectionTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-white/40 border-b border-white/[0.07]">
                  <th className="text-left pb-2 pr-4">HS-4</th>
                  <th className="text-left pb-2 pr-4">Description</th>
                  <th className="text-left pb-2 pr-4">Sector</th>
                  <th className="text-right pb-2 pr-4">EU Benchmark (tCO₂/t)</th>
                  <th className="text-center pb-2">CBAM Annex I</th>
                </tr>
              </thead>
              <tbody>
                {(benchmarks.benchmarks || []).map((b, i) => (
                  <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="py-2 pr-4 font-mono text-blue-400">{b.hs_code}</td>
                    <td className="py-2 pr-4 text-white/80">{b.description}</td>
                    <td className="py-2 pr-4"><Badge color="slate">{b.sector}</Badge></td>
                    <td className="py-2 pr-4 text-right font-bold text-white">{b.eu_benchmark_tco2_per_tonne}</td>
                    <td className="py-2 text-center"><Badge color="amber">CBAM</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {benchmarks.cets_reference && (
            <div className="mt-3 flex gap-4 text-xs text-white/40">
              <span>CETS spot: <strong className="text-amber-400">¥{benchmarks.cets_reference.spot_cny}</strong></span>
              <span>EUR equiv: <strong className="text-amber-400">€{benchmarks.cets_reference.spot_eur}</strong></span>
              <span>EU ETS ref: <strong className="text-blue-400">€{benchmarks.cets_reference.eu_ets_reference_eur}</strong></span>
              <span>Arbitrage: <strong className="text-red-400">€{benchmarks.cets_reference.arbitrage_eur_per_tco2}/tCO₂</strong></span>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 3 — Supplier Framework
// ═══════════════════════════════════════════════════════════════════════════════
function SupplierTab() {
  const [framework, setFramework]   = useState('');
  const [category, setCategory]     = useState('');
  const [maxIntensity, setMaxInt]   = useState('');
  const [requireCert, setReqCert]   = useState(false);
  const [ranked, setRanked]         = useState(null);

  const { data: reqs, loading: reqLoading } = useFetch(
    `${BASE}/suppliers/requirements${framework || category ? `?${new URLSearchParams({ ...(framework && { framework }), ...(category && { product_category: category }) })}` : ''}`,
    [framework, category],
  );

  const rankSuppliers = () => {
    const params = new URLSearchParams();
    if (category)     params.set('product_category', category);
    if (maxIntensity) params.set('max_intensity', maxIntensity);
    if (requireCert)  params.set('require_certified', 'true');
    fetch(`${BASE}/suppliers/rank?${params}`)
      .then(r => r.json())
      .then(setRanked);
  };

  const requirements = reqs?.requirements || [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Importer requirements */}
        <Card>
          <SectionTitle>Importer Decarbonisation Requirements</SectionTitle>
          <div className="flex gap-3 mb-4">
            <select
              className="flex-1 bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
              value={framework}
              onChange={e => setFramework(e.target.value)}
            >
              <option value="">All Frameworks</option>
              {['CBAM', 'CSDDD', 'SBTi', 'CDP', 'RE100'].map(f => <option key={f} value={f}>{f}</option>)}
            </select>
            <select
              className="flex-1 bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
              value={category}
              onChange={e => setCategory(e.target.value)}
            >
              <option value="">All Categories</option>
              {['Steel', 'Aluminium', 'Components', 'Chemicals', 'Energy', 'Cement'].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          {reqLoading ? <Spinner /> : requirements.length === 0 ? <Empty /> : (
            <div className="space-y-3">
              {requirements.map((r, i) => (
                <div key={i} className="bg-[#060c18] rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-semibold text-sm text-white">{r.importer_name}</span>
                    <div className="flex gap-1.5">
                      <Badge color="blue">{r.framework}</Badge>
                      {r.cbam_art9_eligible && <Badge color="amber">Art.9</Badge>}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-white/40">Max Intensity</span>
                      <span className="block font-bold text-white">{r.max_carbon_intensity_tco2_per_tonne} tCO₂/t</span>
                    </div>
                    <div>
                      <span className="text-white/40">Category</span>
                      <span className="block text-white/80">{r.product_category}</span>
                    </div>
                    <div>
                      <span className="text-white/40">Target Year</span>
                      <span className="block text-white/80">{r.target_year}</span>
                    </div>
                    <div>
                      <span className="text-white/40">Certifications</span>
                      <span className="block text-white/80">{(r.required_certifications || []).join(', ')}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Supplier ranking */}
        <Card>
          <SectionTitle>Supplier Ranking Tool</SectionTitle>
          <div className="space-y-3 mb-4">
            <div>
              <label className="text-xs text-white/40 block mb-1">Max Carbon Intensity (tCO₂/t)</label>
              <input
                type="number"
                className="w-full bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500/50"
                placeholder="e.g. 2.0"
                value={maxIntensity}
                onChange={e => setMaxInt(e.target.value)}
              />
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={requireCert}
                onChange={e => setReqCert(e.target.checked)}
                className="accent-blue-500"
              />
              <span className="text-sm text-white/60">Require certified products only</span>
            </label>
            <button
              onClick={rankSuppliers}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg transition-colors"
            >
              Rank Suppliers
            </button>
          </div>

          {ranked && (
            ranked.suppliers?.length === 0 ? <Empty msg="No suppliers match criteria" /> : (
              <div className="space-y-2">
                {(ranked.suppliers || []).map((s, i) => (
                  <div key={i} className="flex items-center justify-between bg-[#060c18] rounded-lg px-3 py-2.5">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-bold text-white/30 w-5">#{i + 1}</span>
                      <div>
                        <div className="text-sm font-semibold text-white">{s.entity_name}</div>
                        <div className="text-xs text-white/40">{s.sector}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-white">{s.avg_embedded_carbon_tco2_per_tonne?.toFixed(3)} tCO₂/t</div>
                      <ReadinessBand score={s.cbam_readiness_score} />
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </Card>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 4 — China ESG & ETS
// ═══════════════════════════════════════════════════════════════════════════════
function ESGETSTab() {
  const [sector, setSector] = useState('');
  const [esgTier, setEsgTier] = useState('');

  const { data: dashboard, loading: dashLoading } = useFetch(
    `${BASE}/esg-ets/dashboard${sector || esgTier ? `?${new URLSearchParams({ ...(sector && { sector }), ...(esgTier && { esg_tier: esgTier }) })}` : ''}`,
    [sector, esgTier],
  );
  const { data: ndc }     = useFetch(`${BASE}/esg-ets/ndc-alignment`, []);
  const { data: cetsPrice } = useFetch(`${BASE}/esg-ets/cets-price`, []);
  const { data: ets }     = useFetch(`${BASE}/esg-ets/ets-positions`, []);

  const priceHistory = cetsPrice?.history || [];
  const ndcData      = ndc?.pathways || [];
  const tierDist     = dashboard?.tier_distribution
    ? Object.entries(dashboard.tier_distribution).map(([name, value]) => ({ name, value }))
    : [];
  const entities     = dashboard?.entities || [];

  return (
    <div className="space-y-6">
      {/* CETS price chart */}
      {priceHistory.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="md:col-span-2">
            <SectionTitle>CETS Price History (CNY / tCO₂)</SectionTitle>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={priceHistory} margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="year" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} unit=" ¥" />
                <Tooltip content={<TT unit=" ¥" />} />
                <Line type="monotone" dataKey="avg_price_cny" name="Avg Price (CNY)" stroke={C.amber} strokeWidth={2.5} dot={{ r: 4, fill: C.amber }} />
              </LineChart>
            </ResponsiveContainer>
            {cetsPrice?.current && (
              <div className="mt-3 flex gap-6 text-xs text-white/50">
                <span>Spot: <strong className="text-amber-400">¥{cetsPrice.current.spot_cny}</strong></span>
                <span>EUR equiv: <strong className="text-amber-400">€{cetsPrice.current.spot_eur}</strong></span>
                <span>YTD: <strong className={cetsPrice.current.ytd_change_pct >= 0 ? 'text-green-400' : 'text-red-400'}>{cetsPrice.current.ytd_change_pct >= 0 ? '+' : ''}{cetsPrice.current.ytd_change_pct}%</strong></span>
                <span>Phase: <strong className="text-white">{cetsPrice.current.phase}</strong></span>
              </div>
            )}
          </Card>
          <Card>
            <SectionTitle>ESG Tier Distribution</SectionTitle>
            {tierDist.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={tierDist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                    {tierDist.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip content={<TT />} />
                </PieChart>
              </ResponsiveContainer>
            ) : <Spinner />}
          </Card>
        </div>
      )}

      {/* Filters + ESG table */}
      <Card>
        <div className="flex gap-3 mb-4">
          <select
            className="bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
            value={sector}
            onChange={e => setSector(e.target.value)}
          >
            <option value="">All Sectors</option>
            {['Power', 'Steel', 'Aluminium', 'Cement', 'Chemicals', 'Paper', 'Aviation', 'Oil & Gas'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select
            className="bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
            value={esgTier}
            onChange={e => setEsgTier(e.target.value)}
          >
            <option value="">All Tiers</option>
            {['Leader', 'Advanced', 'Developing', 'Emerging'].map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        <SectionTitle>SSE / SZSE 2024 ESG Disclosures</SectionTitle>
        {dashLoading ? <Spinner /> : entities.length === 0 ? <Empty /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-white/40 border-b border-white/[0.07]">
                  <th className="text-left pb-2 pr-3">Company</th>
                  <th className="text-left pb-2 pr-3">Sector</th>
                  <th className="text-left pb-2 pr-3">Tier</th>
                  <th className="text-right pb-2 pr-3">E Score</th>
                  <th className="text-right pb-2 pr-3">S Score</th>
                  <th className="text-right pb-2 pr-3">G Score</th>
                  <th className="text-right pb-2 pr-3">CETS Covered</th>
                  <th className="text-right pb-2">Carbon Intensity</th>
                </tr>
              </thead>
              <tbody>
                {entities.map((e, i) => (
                  <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="py-2 pr-3 font-semibold text-white">{e.entity_name}</td>
                    <td className="py-2 pr-3 text-white/60">{e.sector}</td>
                    <td className="py-2 pr-3"><ReadinessBand score={e.esg_tier === 'Leader' ? 90 : e.esg_tier === 'Advanced' ? 70 : e.esg_tier === 'Developing' ? 50 : 20} /></td>
                    <td className="py-2 pr-3 text-right text-green-400 font-bold">{e.environmental_score}</td>
                    <td className="py-2 pr-3 text-right text-blue-400 font-bold">{e.social_score}</td>
                    <td className="py-2 pr-3 text-right text-purple-400 font-bold">{e.governance_score}</td>
                    <td className="py-2 pr-3 text-right text-white">{e.cets_covered ? <Badge color="amber">CETS</Badge> : <Badge color="slate">No</Badge>}</td>
                    <td className="py-2 text-right text-white">{e.carbon_intensity_tco2_per_revenue ? `${e.carbon_intensity_tco2_per_revenue.toFixed(3)} tCO₂/¥mn` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* NDC Pathways */}
      {ndcData.length > 0 && (
        <Card>
          <SectionTitle>China NDC Pathways — 2030 Peak / 2060 Neutrality</SectionTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-white/40 border-b border-white/[0.07]">
                  <th className="text-left pb-2 pr-4">Sector</th>
                  <th className="text-right pb-2 pr-4">2025 Baseline (MtCO₂)</th>
                  <th className="text-right pb-2 pr-4">2030 Target</th>
                  <th className="text-right pb-2 pr-4">2050 Target</th>
                  <th className="text-right pb-2 pr-4">Reduction %</th>
                  <th className="text-left pb-2">Key Metric</th>
                </tr>
              </thead>
              <tbody>
                {ndcData.map((p, i) => (
                  <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="py-2 pr-4 font-semibold text-white">{p.sector}</td>
                    <td className="py-2 pr-4 text-right text-white/70">{p.baseline_emissions_mtco2?.toLocaleString()}</td>
                    <td className="py-2 pr-4 text-right text-amber-400">{p.target_2030_mtco2?.toLocaleString()}</td>
                    <td className="py-2 pr-4 text-right text-green-400">{p.target_2050_mtco2?.toLocaleString()}</td>
                    <td className="py-2 pr-4 text-right text-red-400 font-bold">{p.reduction_pct_2030}%</td>
                    <td className="py-2 text-white/50 text-xs">{p.key_metric}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ETS positions */}
      {ets?.positions?.length > 0 && (
        <Card>
          <SectionTitle>CETS Phase 2 Coverage — Sector Positions</SectionTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-white/40 border-b border-white/[0.07]">
                  <th className="text-left pb-2 pr-4">Sector</th>
                  <th className="text-right pb-2 pr-4">Installations</th>
                  <th className="text-right pb-2 pr-4">Annual Emissions (MtCO₂)</th>
                  <th className="text-right pb-2 pr-4">Free Allocation %</th>
                  <th className="text-right pb-2 pr-4">Carbon Cost (¥mn)</th>
                  <th className="text-center pb-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {ets.positions.map((p, i) => (
                  <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="py-2 pr-4 font-semibold text-white">{p.sector}</td>
                    <td className="py-2 pr-4 text-right text-white">{p.covered_installations?.toLocaleString()}</td>
                    <td className="py-2 pr-4 text-right text-white">{p.annual_emissions_mtco2?.toFixed(2)}</td>
                    <td className="py-2 pr-4 text-right text-amber-400">{p.free_allocation_pct}%</td>
                    <td className="py-2 pr-4 text-right text-white">{p.total_carbon_cost_cny_mn?.toLocaleString()}</td>
                    <td className="py-2 text-center">
                      <Badge color={p.compliance_status === 'Surplus' ? 'green' : p.compliance_status === 'Deficit' ? 'red' : 'amber'}>
                        {p.compliance_status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 5 — Trade Corridors
// ═══════════════════════════════════════════════════════════════════════════════
function CorridorsTab() {
  const [plSector, setPlSector] = useState('Steel');
  const { data: corridors, loading: corrLoading } = useFetch(`${BASE}/corridors`, []);
  const { data: plImpact, loading: plLoading }    = useFetch(`${BASE}/corridors/pl-impact/${plSector}`, [plSector]);

  const allCorridors = corridors?.corridors || [];
  const top3         = allCorridors.slice(0, 3);
  const plData       = plImpact?.scenarios || [];

  return (
    <div className="space-y-6">
      {/* Top corridor cards */}
      {corrLoading ? <Spinner /> : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {top3.map((c, i) => (
            <Card key={i} className="border-blue-500/10">
              <div className="flex items-center justify-between mb-3">
                <span className="font-bold text-white">{c.corridor_name}</span>
                {c.cbam_applicable && <Badge color="amber">CBAM</Badge>}
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-white/40">Trade Value</span>
                  <span className="font-bold text-white">${c.trade_value_usd_bn?.toLocaleString()}bn</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/40">Annual CBAM Liability (est.)</span>
                  <span className="font-bold text-amber-400">€{c.annual_cbam_liability_est_eur_mn?.toLocaleString()}mn</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/40">CETS Arbitrage</span>
                  <span className="font-bold text-red-400">€{c.arbitrage_eur_per_tco2}/tCO₂</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-white/40">Top Sectors</span>
                  <span className="text-white/70">{(c.top_sectors || []).join(', ')}</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Full corridor table */}
      {allCorridors.length > 0 && (
        <Card>
          <SectionTitle>All Trade Corridors</SectionTitle>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-white/40 border-b border-white/[0.07]">
                  <th className="text-left pb-2 pr-4">Corridor</th>
                  <th className="text-right pb-2 pr-4">Trade Value (USD bn)</th>
                  <th className="text-right pb-2 pr-4">CBAM Liability (€mn est.)</th>
                  <th className="text-right pb-2 pr-4">Arbitrage (€/tCO₂)</th>
                  <th className="text-left pb-2 pr-4">Dominant Sector</th>
                  <th className="text-center pb-2">CBAM</th>
                </tr>
              </thead>
              <tbody>
                {allCorridors.map((c, i) => (
                  <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="py-2 pr-4 font-semibold text-white">{c.corridor_name}</td>
                    <td className="py-2 pr-4 text-right text-white">${c.trade_value_usd_bn?.toLocaleString()}</td>
                    <td className="py-2 pr-4 text-right text-amber-400">€{c.annual_cbam_liability_est_eur_mn?.toLocaleString()}</td>
                    <td className="py-2 pr-4 text-right text-red-400 font-bold">€{c.arbitrage_eur_per_tco2}</td>
                    <td className="py-2 pr-4 text-white/60">{c.dominant_cbam_sector}</td>
                    <td className="py-2 text-center">{c.cbam_applicable ? <Badge color="amber">CBAM</Badge> : <Badge color="slate">N/A</Badge>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* P&L impact by sector */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <SectionTitle>P&L Impact — EU ETS Price Scenarios</SectionTitle>
          <select
            className="bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white focus:outline-none"
            value={plSector}
            onChange={e => setPlSector(e.target.value)}
          >
            {['Steel', 'Aluminium', 'Cement', 'Chemicals', 'Fertiliser'].map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        {plLoading ? <Spinner /> : plData.length === 0 ? <Empty /> : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={plData} margin={{ top: 0, right: 10, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="eu_ets_price_eur" tick={{ fill: '#94a3b8', fontSize: 11 }} unit="€" />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <Tooltip content={<TT />} />
                <Legend wrapperStyle={{ color: '#94a3b8', fontSize: 11 }} />
                <Bar dataKey="cbam_liability_eur_per_tonne" name="CBAM (€/t)" fill={C.amber} radius={[3, 3, 0, 0]} />
                <Bar dataKey="cets_deduction_eur_per_tonne" name="CETS Deduction (€/t)" fill={C.green} radius={[3, 3, 0, 0]} />
                <Bar dataKey="net_impact_eur_per_tonne" name="Net Impact (€/t)" fill={C.red} radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-white/40 border-b border-white/[0.07]">
                    <th className="text-right pb-2 pr-3">EU ETS</th>
                    <th className="text-right pb-2 pr-3">Gross CBAM</th>
                    <th className="text-right pb-2 pr-3">CETS Ded.</th>
                    <th className="text-right pb-2">Net (€/t)</th>
                  </tr>
                </thead>
                <tbody>
                  {plData.map((p, i) => (
                    <tr key={i} className="border-b border-white/[0.03]">
                      <td className="py-1.5 pr-3 text-right text-white">€{p.eu_ets_price_eur}</td>
                      <td className="py-1.5 pr-3 text-right text-amber-400">€{p.cbam_liability_eur_per_tonne?.toFixed(2)}</td>
                      <td className="py-1.5 pr-3 text-right text-green-400">€{p.cets_deduction_eur_per_tonne?.toFixed(2)}</td>
                      <td className="py-1.5 text-right text-red-400 font-bold">€{p.net_impact_eur_per_tonne?.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// TAB 6 — Carbon Marketplace
// ═══════════════════════════════════════════════════════════════════════════════
function MarketplaceTab() {
  const [listingType, setListingType] = useState('');
  const [standard, setStandard]       = useState('');
  const [mktSector, setMktSector]     = useState('');

  const { data: prices, loading: priceLoading } = useFetch(`${BASE}/marketplace/price-discovery`, []);
  const { data: stats }  = useFetch(`${BASE}/marketplace/stats`, []);

  const [listings, setListings]   = useState(null);
  const [listLoading, setListLoading] = useState(false);

  const fetchListings = useCallback(() => {
    setListLoading(true);
    const params = new URLSearchParams({ limit: 20 });
    if (listingType) params.set('listing_type', listingType);
    if (standard)    params.set('standard', standard);
    if (mktSector)   params.set('sector', mktSector);
    fetch(`${BASE}/marketplace/listings?${params}`)
      .then(r => r.json())
      .then(d => { setListings(d); setListLoading(false); })
      .catch(() => setListLoading(false));
  }, [listingType, standard, mktSector]);

  useEffect(() => { fetchListings(); }, []); // eslint-disable-line

  const priceRows = prices?.benchmarks || [];
  const activeListings = listings?.listings || [];

  return (
    <div className="space-y-6">
      {/* Stats strip */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card><Stat label="Total Listings" value={stats.total_listings ?? '—'} /></Card>
          <Card><Stat label="Total Volume (tCO₂)" value={stats.total_volume_tco2 ? stats.total_volume_tco2.toLocaleString() : '—'} color="text-blue-400" /></Card>
          <Card><Stat label="Total Value (USD)" value={stats.total_value_usd ? `$${stats.total_value_usd.toLocaleString()}` : '—'} color="text-green-400" /></Card>
          <Card><Stat label="Avg Price (USD/tCO₂)" value={stats.avg_price_usd_per_tco2 ? `$${stats.avg_price_usd_per_tco2.toFixed(2)}` : '—'} color="text-amber-400" /></Card>
        </div>
      )}

      {/* Price benchmark table */}
      <Card>
        <SectionTitle>Carbon Market Price Benchmarks</SectionTitle>
        {priceLoading ? <Spinner /> : priceRows.length === 0 ? <Empty /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="text-white/40 border-b border-white/[0.07]">
                  <th className="text-left pb-2 pr-4">Standard</th>
                  <th className="text-right pb-2 pr-4">Spot (USD/tCO₂)</th>
                  <th className="text-right pb-2 pr-4">1Y Forward</th>
                  <th className="text-right pb-2 pr-4">Spread</th>
                  <th className="text-right pb-2 pr-4">vs EU ETS Discount</th>
                  <th className="text-left pb-2">Exchange</th>
                </tr>
              </thead>
              <tbody>
                {priceRows.map((p, i) => (
                  <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="py-2 pr-4">
                      <div className="font-bold text-white">{p.standard}</div>
                      <div className="text-white/30">{p.description}</div>
                    </td>
                    <td className="py-2 pr-4 text-right font-bold text-green-400">${p.spot_usd?.toFixed(2)}</td>
                    <td className="py-2 pr-4 text-right text-white">${p.forward_1y_usd?.toFixed(2)}</td>
                    <td className="py-2 pr-4 text-right text-blue-400">
                      {p.contango_pct != null ? `${p.contango_pct > 0 ? '+' : ''}${p.contango_pct?.toFixed(1)}%` : '—'}
                    </td>
                    <td className="py-2 pr-4 text-right text-amber-400">
                      {p.vs_eu_ets_discount_pct != null ? `${p.vs_eu_ets_discount_pct?.toFixed(1)}%` : '—'}
                    </td>
                    <td className="py-2 text-white/50">{p.exchange}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Active listings */}
      <Card>
        <div className="flex items-center justify-between mb-4">
          <SectionTitle>Active Listings</SectionTitle>
          <div className="flex gap-2">
            <select
              className="bg-[#060c18] border border-white/[0.07] rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none"
              value={listingType}
              onChange={e => setListingType(e.target.value)}
            >
              <option value="">All Types</option>
              {['Allowance', 'Offset', 'Certificate'].map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <select
              className="bg-[#060c18] border border-white/[0.07] rounded-lg px-2 py-1.5 text-xs text-white focus:outline-none"
              value={standard}
              onChange={e => setStandard(e.target.value)}
            >
              <option value="">All Standards</option>
              {['CETS', 'CCER', 'VCS', 'Gold_Standard', 'CDM', 'EU_ETS'].map(s => <option key={s} value={s}>{s}</option>)}
            </select>
            <button
              onClick={fetchListings}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-lg transition-colors"
            >
              Filter
            </button>
          </div>
        </div>

        {listLoading ? <Spinner /> : activeListings.length === 0 ? <Empty /> : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {activeListings.map((l, i) => (
              <div key={i} className="bg-[#060c18] rounded-lg p-4 border border-white/[0.05] hover:border-white/[0.1] transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="font-semibold text-sm text-white">{l.seller_name}</div>
                    <div className="text-xs text-white/40">{l.project_name}</div>
                  </div>
                  <div className="flex gap-1.5">
                    <Badge color={l.listing_type === 'Allowance' ? 'blue' : l.listing_type === 'Offset' ? 'green' : 'purple'}>
                      {l.listing_type}
                    </Badge>
                    <Badge color="slate">{l.standard}</Badge>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div>
                    <span className="text-white/40 block">Price</span>
                    <span className="font-bold text-green-400">${l.price_usd_per_tco2?.toFixed(2)}/t</span>
                  </div>
                  <div>
                    <span className="text-white/40 block">Volume</span>
                    <span className="font-bold text-white">{l.volume_tco2?.toLocaleString()} tCO₂</span>
                  </div>
                  <div>
                    <span className="text-white/40 block">Vintage</span>
                    <span className="font-bold text-white">{l.vintage_year}</span>
                  </div>
                </div>
                {(l.co_benefits || []).length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {l.co_benefits.map((b, j) => (
                      <Badge key={j} color="cyan">{b}</Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN PAGE
// ═══════════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════════
// TAB 7 — Connected Modules
// ═══════════════════════════════════════════════════════════════════════════════
function ConnectedModulesTab() {
  const [entityName, setEntityName] = useState('');
  const [hub, setHub]   = useState(null);
  const [hubLoading, setHubLoading] = useState(false);
  const [hubError, setHubError] = useState(null);

  const { data: scope3 }    = useFetch(`${BASE}/cross-module/scope3-cat1`, []);
  const { data: eclData }   = useFetch(`${BASE}/cross-module/ecl-cbam-overlay`, []);
  const { data: ngfsData }  = useFetch(`${BASE}/cross-module/scenario-cets-ngfs`, []);
  const { data: portData }  = useFetch(`${BASE}/cross-module/portfolio-cbam`, []);

  const fetchHub = () => {
    if (!entityName.trim()) return;
    setHubLoading(true);
    setHubError(null);
    setHub(null);
    fetch(`${BASE}/cross-module/entity-hub/${encodeURIComponent(entityName.trim())}`)
      .then(r => r.json())
      .then(d => { setHub(d); setHubLoading(false); })
      .catch(() => { setHubError('Lookup failed'); setHubLoading(false); });
  };

  const MODULE_CARDS = [
    {
      title: 'CBAM Calculator',
      href: '/cbam',
      badgeLabel: 'AUTO-FILL',
      badgeColor: 'amber',
      description: 'China Trade data auto-fills embedded carbon, EU benchmark, and CETS Art.9 deduction into the CBAM Calculator.',
      dataPoint: eclData ? `CETS €${eclData.cets_price_eur}/tCO2 · Arbitrage €${eclData.cbam_arbitrage_eur}/tCO2` : 'Loading…',
    },
    {
      title: 'Supply Chain (Scope 3 Cat 1)',
      href: '/supply-chain',
      badgeLabel: 'CAT 1 EF',
      badgeColor: 'green',
      description: 'CETS-verified emission factors from Chinese exporters available in the Scope 3 Calculator purchased-goods panel.',
      dataPoint: scope3 ? `${scope3.total_factors} emission factor records · ${scope3.ghg_protocol_category}` : 'Loading…',
    },
    {
      title: 'Financial Risk (IFRS 9 ECL)',
      href: '/financial-risk',
      badgeLabel: 'CREDIT RISK',
      badgeColor: 'red',
      description: 'CBAM readiness scores mapped to IFRS 9 PD/LGD uplift bands. China CBAM Credit Risk section in Financial Risk.',
      dataPoint: eclData ? `${eclData.total_entities_assessed} entities assessed across ${eclData.risk_bands?.length} risk bands` : 'Loading…',
    },
    {
      title: 'Regulatory (CSRD / SFDR / ISSB)',
      href: '/regulatory',
      badgeLabel: 'CHINA ESG',
      badgeColor: 'blue',
      description: 'SSE/SZSE 2024 mandatory ESG disclosures mapped to CSRD ESRS E1, SFDR PAI, and ISSB S2. Available in Regulatory → China ESG Intelligence tab.',
      dataPoint: 'SSE/SZSE 2024 · 5 CSRD cross-standard mappings · 4 key gap findings',
    },
    {
      title: 'Scenario Analysis (NGFS × CETS)',
      href: '/scenario-analysis',
      badgeLabel: 'NGFS',
      badgeColor: 'purple',
      description: 'CETS price trajectories under NGFS v4 scenarios (Net Zero 2050, Delayed Transition, Below 2°C, Current Policies) for China transition risk.',
      dataPoint: ngfsData ? `${ngfsData.scenarios?.length} NGFS scenarios · 2030 NDC peak · 2060 neutrality` : 'Loading…',
    },
    {
      title: 'Portfolio Analytics (CBAM Roll-up)',
      href: '/portfolio',
      badgeLabel: 'PORTFOLIO',
      badgeColor: 'cyan',
      description: 'Sector-level CBAM gross/net liability aggregation across China-exposed portfolios. Art.9 CETS deduction roll-up.',
      dataPoint: portData
        ? `Gross €${((portData.total_gross_cbam_liability_eur || 0) / 1e6).toFixed(1)}mn · Net €${((portData.total_net_cbam_liability_eur || 0) / 1e6).toFixed(1)}mn · ${portData.sector_breakdown?.length || 0} sectors`
        : 'Loading…',
    },
    {
      title: 'Asia Regulatory',
      href: '/asia-regulatory',
      badgeLabel: 'PBoC · HKMA',
      badgeColor: 'cyan',
      description: 'PBoC Green Finance, HKMA Taxonomy, SEBI BRSR, and other Asia-Pacific regulatory frameworks. Shares CETS data with China Trade.',
      dataPoint: 'PBoC Green Finance · HKMA Taxonomy · SEBI BRSR · JFSA · MAS',
    },
    {
      title: 'CSRD Reports',
      href: '/csrd',
      badgeLabel: 'PDF PIPELINE',
      badgeColor: 'slate',
      description: 'Processed annual reports from Chinese-exposed EU companies (Ørsted, RWE, ENGIE, EDP). China Trade ESG data cross-references ESRS E1 gaps.',
      dataPoint: '8 EU reports processed · 82 KPI values · 120 gaps tracked',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <SectionTitle>Connected Modules — China Trade Platform Integration Map</SectionTitle>
        <p className="text-sm text-white/40 -mt-3 mb-4">
          China Trade data is available across all platform modules. Use the entity hub below to view a unified cross-module card for any Chinese exporter.
        </p>
      </div>

      {/* Entity Hub Lookup */}
      <Card className="border-blue-500/20">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-bold text-white">Cross-Module Entity Hub</h3>
            <p className="text-xs text-white/40 mt-0.5">Unified data card for any Chinese exporter across all modules</p>
          </div>
          <Badge color="amber">ALL MODULES</Badge>
        </div>
        <div className="flex gap-3 mb-4">
          <input
            className="flex-1 bg-[#060c18] border border-white/[0.07] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            placeholder="e.g., China Baowu Steel Group"
            value={entityName}
            onChange={e => setEntityName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && fetchHub()}
          />
          <button
            onClick={fetchHub}
            disabled={hubLoading || !entityName.trim()}
            className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {hubLoading ? 'Loading…' : 'Look Up'}
          </button>
        </div>

        {hubError && <div className="text-sm text-red-400 py-2">{hubError}</div>}

        {hub && !hub.error && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-[#060c18] rounded-lg p-3">
                <p className="text-[10px] text-white/40 mb-1">Sector</p>
                <p className="text-sm font-bold text-white">{hub.sector}</p>
              </div>
              <div className="bg-[#060c18] rounded-lg p-3">
                <p className="text-[10px] text-white/40 mb-1">CBAM Readiness</p>
                <p className="text-xl font-bold text-blue-400">{hub.cbam_readiness_score}</p>
              </div>
              <div className="bg-[#060c18] rounded-lg p-3">
                <p className="text-[10px] text-white/40 mb-1">ESG Tier</p>
                <ReadinessBand score={hub.cbam_readiness_score} />
              </div>
              <div className="bg-[#060c18] rounded-lg p-3">
                <p className="text-[10px] text-white/40 mb-1">ETS Registered</p>
                <p className={`text-sm font-bold ${hub.ets_registered ? 'text-green-400' : 'text-amber-400'}`}>
                  {hub.ets_registered ? 'Yes' : 'No'}
                </p>
              </div>
            </div>

            {hub.cbam_liability?.net_cbam_liability_eur != null && (
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-[#060c18] rounded-lg p-3">
                  <p className="text-[10px] text-white/40 mb-1">Gross CBAM Liability</p>
                  <p className="text-sm font-bold text-white">
                    €{((hub.cbam_liability.gross_cbam_liability_eur || 0) / 1000).toFixed(0)}k
                  </p>
                </div>
                <div className="bg-[#060c18] rounded-lg p-3">
                  <p className="text-[10px] text-white/40 mb-1">CETS Art.9 Deduction</p>
                  <p className="text-sm font-bold text-green-400">
                    -€{((hub.cbam_liability.cets_deduction_eur || 0) / 1000).toFixed(0)}k
                  </p>
                </div>
                <div className="bg-[#060c18] rounded-lg p-3">
                  <p className="text-[10px] text-white/40 mb-1">Net CBAM Liability</p>
                  <p className="text-sm font-bold text-amber-400">
                    €{((hub.cbam_liability.net_cbam_liability_eur || 0) / 1000).toFixed(0)}k
                  </p>
                </div>
              </div>
            )}

            <div className="flex flex-wrap gap-2 pt-1">
              {Object.entries(hub.module_links || {}).map(([mod, href]) => (
                <a key={mod} href={href}
                  className="text-[10px] px-3 py-1 rounded border border-blue-500/20 bg-blue-500/5 text-blue-400 hover:bg-blue-500/10 hover:border-blue-500/40 transition-colors capitalize">
                  {mod.replace(/_/g, ' ')} →
                </a>
              ))}
            </div>
          </div>
        )}

        {hub?.error && (
          <div className="text-sm text-amber-400 py-2 flex items-center gap-2">
            <span className="text-amber-500">⚠</span> {hub.error}
          </div>
        )}
      </Card>

      {/* Module Integration Cards */}
      <div>
        <SectionTitle>Active Integrations</SectionTitle>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {MODULE_CARDS.map((m, i) => (
            <a key={i} href={m.href}
              className="block bg-[#0e1829] border border-white/[0.07] hover:border-white/[0.15] rounded-xl p-5 transition-all group">
              <div className="flex items-start justify-between mb-2">
                <h4 className="text-sm font-bold text-white group-hover:text-blue-300 transition-colors">{m.title}</h4>
                <Badge color={m.badgeColor}>{m.badgeLabel}</Badge>
              </div>
              <p className="text-xs text-white/50 mb-3 leading-relaxed">{m.description}</p>
              <p className="text-[10px] text-white/30 font-mono border-t border-white/[0.04] pt-2">{m.dataPoint}</p>
            </a>
          ))}
        </div>
      </div>

      {/* Cross-module data summary cards */}
      <div>
        <SectionTitle>Live Cross-Module Data</SectionTitle>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

          {/* Scope 3 Cat 1 summary */}
          {scope3 && (
            <Card>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold text-white/70 uppercase tracking-wide">Scope 3 Cat 1 EFs</h4>
                <Badge color="green">SUPPLY CHAIN</Badge>
              </div>
              <p className="text-2xl font-bold text-white mb-1">{scope3.total_factors}</p>
              <p className="text-xs text-white/40 mb-3">emission factor records</p>
              {(scope3.factors || []).slice(0, 4).map((f, i) => (
                <div key={i} className="flex justify-between text-xs py-1 border-b border-white/[0.03]">
                  <span className="text-white/50">{f.product || f.product_name}</span>
                  <span className="font-bold text-white">{Number(f.ef_tco2_t || f.embedded_carbon_tco2_per_tonne || 0).toFixed(2)} tCO2/t</span>
                </div>
              ))}
              <a href="/supply-chain" className="text-[10px] text-blue-400 hover:underline mt-2 block">
                View in Supply Chain →
              </a>
            </Card>
          )}

          {/* Portfolio CBAM */}
          {portData && (
            <Card>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold text-white/70 uppercase tracking-wide">Portfolio CBAM Exposure</h4>
                <Badge color="cyan">PORTFOLIO</Badge>
              </div>
              <p className="text-2xl font-bold text-amber-400 mb-1">
                €{((portData.total_net_cbam_liability_eur || 0) / 1e6).toFixed(1)}mn
              </p>
              <p className="text-xs text-white/40 mb-3">net liability (after Art.9)</p>
              {(portData.sector_breakdown || []).slice(0, 4).map((s, i) => (
                <div key={i} className="flex justify-between text-xs py-1 border-b border-white/[0.03]">
                  <span className="text-white/50">{s.sector}</span>
                  <span className="font-bold text-amber-400">
                    €{((s.net_liability_eur || 0) / 1000).toFixed(0)}k
                  </span>
                </div>
              ))}
              <a href="/portfolio" className="text-[10px] text-blue-400 hover:underline mt-2 block">
                View in Portfolio Analytics →
              </a>
            </Card>
          )}

          {/* NGFS scenario */}
          {ngfsData && (
            <Card>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-xs font-bold text-white/70 uppercase tracking-wide">NGFS × CETS Scenarios</h4>
                <Badge color="purple">SCENARIOS</Badge>
              </div>
              <p className="text-2xl font-bold text-white mb-1">¥{ngfsData.base_case_price_cny}</p>
              <p className="text-xs text-white/40 mb-3">CETS spot · 2026-03-05</p>
              {(ngfsData.scenarios || []).map((s, i) => (
                <div key={i} className="flex justify-between text-xs py-1 border-b border-white/[0.03]">
                  <span className="text-white/50 truncate">{s.ngfs_scenario}</span>
                  <span className="font-bold text-white ml-2">¥{s.cets_2030_cny} (2030)</span>
                </div>
              ))}
              <a href="/scenario-analysis" className="text-[10px] text-blue-400 hover:underline mt-2 block">
                View in Scenario Analysis →
              </a>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

const TABS = [
  { id: 'exporters',   label: 'Exporter Intelligence', badge: 'CBAM READY'   },
  { id: 'cbam',        label: 'CBAM Exposure',          badge: 'AUTO-FILL'   },
  { id: 'suppliers',   label: 'Supplier Framework',     badge: 'CSDDD'       },
  { id: 'esg-ets',     label: 'China ESG & ETS',        badge: 'CETS · NDC'  },
  { id: 'corridors',   label: 'Trade Corridors',        badge: 'P&L IMPACT'  },
  { id: 'marketplace', label: 'Carbon Marketplace',     badge: 'LIVE PRICES' },
  { id: 'connected',   label: 'Connected Modules',      badge: 'ALL MODULES' },
];

export default function ChinaTradePage() {
  const [activeTab, setActiveTab] = useState('exporters');
  const { data: summary } = useFetch(`${BASE}/summary`, []);

  return (
    <div className="min-h-screen bg-[#060c18] text-white px-6 py-8">

      {/* Page header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-2xl font-bold text-white">China Trade &amp; Sustainability Platform</h1>
          <Badge color="amber">CBAM</Badge>
          <Badge color="blue">CETS</Badge>
          <Badge color="green">ESG</Badge>
        </div>
        <p className="text-sm text-white/40">
          Exporter intelligence · CBAM auto-fill · Supplier framework · China ESG &amp; ETS · Trade corridors · Carbon marketplace
        </p>
      </div>

      {/* Header stats strip */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          <Card className="border-amber-500/15">
            <Stat
              label="CBAM Arbitrage"
              value={`€${summary.cbam_arbitrage_eur_per_tco2 ?? 52.84}`}
              sub="per tCO₂ vs EU ETS"
              color="text-amber-400"
            />
          </Card>
          <Card className="border-amber-500/10">
            <Stat
              label="CETS Spot Price"
              value={`¥${summary.cets_spot_price_cny ?? 95}`}
              sub={`≈ €${summary.cets_spot_price_eur ?? 12.16}`}
              color="text-amber-400"
            />
          </Card>
          <Card>
            <Stat
              label="CN→EU CBAM Liability"
              value={`€${summary.china_eu_cbam_liability_est_eur_mn?.toLocaleString() ?? '4,280'}mn`}
              sub="est. 2025 annual"
              color="text-red-400"
            />
          </Card>
          <Card>
            <Stat
              label="CBAM-Ready Exporters"
              value={`${summary.cbam_ready_exporters ?? '—'} / ${summary.total_exporters ?? '—'}`}
              sub="score ≥ 60"
              color="text-blue-400"
            />
          </Card>
          <Card>
            <Stat
              label="Active Carbon Listings"
              value={summary.active_listings ?? '—'}
              sub="CETS · CCER · VCS"
              color="text-green-400"
            />
          </Card>
        </div>
      )}

      {/* Tab strip */}
      <div className="flex overflow-x-auto gap-1 mb-6 bg-[#0e1829] rounded-xl p-1 border border-white/[0.07]">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
              activeTab === t.id
                ? 'bg-blue-600 text-white'
                : 'text-white/50 hover:text-white hover:bg-white/[0.05]'
            }`}
          >
            {t.label}
            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
              activeTab === t.id ? 'bg-white/20 text-white' : 'bg-white/10 text-white/40'
            }`}>
              {t.badge}
            </span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'exporters'   && <ExporterTab />}
        {activeTab === 'cbam'        && <CBAMTab />}
        {activeTab === 'suppliers'   && <SupplierTab />}
        {activeTab === 'esg-ets'     && <ESGETSTab />}
        {activeTab === 'corridors'   && <CorridorsTab />}
        {activeTab === 'marketplace' && <MarketplaceTab />}
        {activeTab === 'connected'   && <ConnectedModulesTab />}
      </div>
    </div>
  );
}
