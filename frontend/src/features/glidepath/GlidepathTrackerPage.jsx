/**
 * GlidepathTrackerPage — Sector NZBA / CRREM trajectory tracking.
 * Route: /glidepath-tracker
 * Sprint 4 — WHOOP for Sustainability platform.
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// ─────────────────────────────────────────────────────────
// RAG colour mapping
// ─────────────────────────────────────────────────────────
const RAG_COLOURS = {
  GREEN: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30', dot: '#10b981' },
  AMBER: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30', dot: '#f59e0b' },
  RED: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30', dot: '#ef4444' },
  GREY: { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/20', dot: '#6b7280' },
};

const RAGBadge = ({ rag, label }) => {
  const c = RAG_COLOURS[rag] || RAG_COLOURS.GREY;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border ${c.bg} ${c.text} ${c.border}`}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: c.dot }} />
      {label || rag}
    </span>
  );
};

const SectionTitle = ({ children }) => (
  <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">{children}</h3>
);

// ─────────────────────────────────────────────────────────
// Sector Glidepath Chart (actual vs NZBA vs IEA NZE)
// ─────────────────────────────────────────────────────────
const SectorGlidepathChart = ({ dataPoints, sector }) => {
  const chartData = (dataPoints || []).map(dp => ({
    year: dp.year,
    actual: dp.actual_waci ?? undefined,
    nzba: dp.nzba_target,
    iea: dp.iea_nze_reference,
  }));

  return (
    <div data-testid={`glidepath-chart-${sector}`}>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <defs>
            <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#22d3ee" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="year" tick={{ fill: '#9ca3af', fontSize: 11 }} />
          <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={v => `${v}`} />
          <Tooltip
            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 8 }}
            labelStyle={{ color: '#e5e7eb' }}
            formatter={(v, name) => [
              v == null ? 'No data' : `${Number(v).toFixed(1)} tCO₂e/MEUR`,
              name === 'actual' ? 'Actual WACI' : name === 'nzba' ? 'NZBA Target' : 'IEA NZE Reference',
            ]}
          />
          <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 11 }} />
          {/* Actual trajectory */}
          <Area type="monotone" dataKey="actual" fill="url(#actualGrad)" stroke="#22d3ee" strokeWidth={2.5}
            dot={{ fill: '#22d3ee', r: 3 }} connectNulls={false} name="Actual WACI" />
          {/* NZBA target */}
          <Line type="monotone" dataKey="nzba" stroke="#10b981" strokeWidth={2} dot={false}
            strokeDasharray="6 3" name="NZBA Target" />
          {/* IEA NZE */}
          <Line type="monotone" dataKey="iea" stroke="#ffffff" strokeWidth={1.5} dot={false}
            strokeDasharray="3 3" strokeOpacity={0.4} name="IEA NZE Reference" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// RAG Status Grid
// ─────────────────────────────────────────────────────────
const GlidepathStatusGrid = ({ grid, sectors, years }) => {
  if (!grid || grid.length === 0) return (
    <div className="text-sm text-gray-500 p-4">No data available. Run PCAF calculation to populate glidepath data.</div>
  );

  return (
    <div data-testid="glidepath-status-grid" className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/10">
            <th className="text-left py-2 text-xs text-gray-400 font-medium pr-4">Sector</th>
            {years.map(yr => (
              <th key={yr} className="text-center py-2 text-xs text-gray-400 font-medium px-2">{yr}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sectors.map(sector => {
            const sectorRows = grid.filter(r => r.sector === sector);
            return (
              <tr key={sector} className="border-b border-white/5 hover:bg-white/3">
                <td className="py-2 pr-4 text-gray-300 font-medium">{sector}</td>
                {years.map(yr => {
                  const cell = sectorRows.find(r => r.year === yr);
                  const c = RAG_COLOURS[cell?.rag || 'GREY'];
                  return (
                    <td key={yr} className="py-2 px-2 text-center">
                      <span className={`inline-block w-6 h-6 rounded-full ${c.bg} border ${c.border}`}
                        title={cell?.actual ? `Actual: ${cell.actual?.toFixed(0)} | Target: ${cell.target?.toFixed(0)}` : 'No data'} />
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      {/* Legend */}
      <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
        {Object.entries(RAG_COLOURS).map(([rag, c]) => (
          <div key={rag} className="flex items-center gap-1.5">
            <span className={`w-3 h-3 rounded-full ${c.bg} border ${c.border}`} />
            <span className={c.text}>{rag}</span>
          </div>
        ))}
        <span className="ml-2">— On or below glidepath target</span>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────
const ALL_SECTORS = ['Power', 'Oil & Gas', 'Steel', 'Shipping', 'Real Estate', 'Aviation', 'Cement'];
const GRID_YEARS = [2025, 2030, 2035, 2040, 2045, 2050];

export default function GlidepathTrackerPage() {
  const [selectedSectors, setSelectedSectors] = useState(['Power', 'Steel', 'Shipping']);
  const [activeSector, setActiveSector] = useState('Power');
  const [portfolioId, setPortfolioId] = useState('');
  const [glidepathData, setGlidepathData] = useState(null);
  const [statusGrid, setStatusGrid] = useState(null);
  const [loading, setLoading] = useState(false);
  const [nzbaRef, setNzbaRef] = useState(null);
  const [portfolios, setPortfolios] = useState([]);

  // Fetch portfolios for dropdown
  useEffect(() => {
    axios.get(`${API}/api/v1/portfolios-pg`)
      .then(res => {
        const items = res.data?.portfolios || res.data || [];
        setPortfolios(items);
        if (items.length > 0 && !portfolioId) setPortfolioId(items[0].id);
      })
      .catch(() => {});
  }, []);

  // Fetch NZBA reference for active sector
  useEffect(() => {
    if (!activeSector) return;
    axios.get(`${API}/api/v1/glidepath/nzba/${encodeURIComponent(activeSector)}`)
      .then(res => setNzbaRef(res.data))
      .catch(() => setNzbaRef(null));
  }, [activeSector]);

  const handleFetchGlidepath = useCallback(async () => {
    if (!portfolioId || !activeSector) return;
    setLoading(true);
    try {
      const [gpRes, gridRes] = await Promise.all([
        axios.get(`${API}/api/v1/glidepath/sector/${encodeURIComponent(activeSector)}?portfolio_id=${portfolioId}`),
        axios.get(`${API}/api/v1/glidepath/portfolio/${portfolioId}/status-grid?sectors=${encodeURIComponent(selectedSectors.join(','))}`),
      ]);
      setGlidepathData(gpRes.data);
      setStatusGrid(gridRes.data);
    } catch (err) {
      console.error('Glidepath fetch failed', err);
    } finally {
      setLoading(false);
    }
  }, [portfolioId, activeSector, selectedSectors]);

  const toggleSector = (sector) => {
    setSelectedSectors(prev =>
      prev.includes(sector) ? prev.filter(s => s !== sector) : [...prev, sector]
    );
  };

  // Build chart data from NZBA reference even without actual data
  const chartDataPoints = glidepathData?.data_points || (nzbaRef?.glidepath?.map(g => ({
    year: g.year,
    actual_waci: null,
    nzba_target: g.value,
    iea_nze_reference: g.value * 0.90,
    rag_status: 'GREY',
    deviation_pct: null,
  })) || []);

  return (
    <div className="min-h-screen p-6 space-y-6" style={{ background: 'hsl(222, 35%, 7%)' }}>
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
          Glidepath Tracker
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          NZBA / IEA NZE sector trajectories vs actual portfolio WACI — {new Date().getFullYear()} data
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-end gap-4">
        {/* Portfolio selector */}
        <div>
          <label className="block text-xs text-gray-400 mb-1">Portfolio</label>
          <select
            value={portfolioId}
            onChange={e => setPortfolioId(e.target.value)}
            className="bg-white/5 border border-white/15 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500/60"
            data-testid="glidepath-portfolio-select"
          >
            {portfolios.length === 0 && <option value="">Select portfolio...</option>}
            {portfolios.map(p => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>
        </div>

        {/* Sector selector chips */}
        <div>
          <label className="block text-xs text-gray-400 mb-1">Sectors in grid</label>
          <div className="flex flex-wrap gap-1.5" data-testid="glidepath-sector-selector">
            {ALL_SECTORS.map(s => (
              <button
                key={s}
                onClick={() => toggleSector(s)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors border ${
                  selectedSectors.includes(s)
                    ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40'
                    : 'bg-white/5 text-gray-400 border-white/10 hover:border-white/20'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleFetchGlidepath}
          disabled={loading || !portfolioId}
          className="px-5 py-2 rounded-lg text-sm font-semibold text-white disabled:opacity-40"
          style={{ background: 'linear-gradient(135deg, hsl(199,89%,40%), hsl(199,89%,30%))' }}
          data-testid="glidepath-fetch-btn"
        >
          {loading ? 'Loading...' : 'Load Glidepath Data'}
        </button>
      </div>

      {/* Data Hub status banner */}
      <div className="flex items-center gap-3 bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
        <div className="w-2 h-2 rounded-full bg-blue-400" />
        <span className="text-xs text-blue-300">
          Showing NZBA 2021 / IEA WEO 2023 reference glidepaths (fallback).
          Actual portfolio WACI populates after running a PCAF calculation.
          Connect Data Hub (port 8002) for live sector benchmarks.
        </span>
      </div>

      {/* Sector chart tabs */}
      <div className="rounded-xl border border-white/10 p-5" style={{ background: 'hsl(222,35%,9%)' }}>
        {/* Sector tabs */}
        <div className="flex gap-1 mb-5 border-b border-white/10">
          {selectedSectors.map(s => (
            <button
              key={s}
              onClick={() => setActiveSector(s)}
              className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${
                activeSector === s
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {s}
              {glidepathData?.sector === s && (
                <RAGBadge rag={glidepathData.current_rag} label={glidepathData.current_rag} />
              )}
            </button>
          ))}
        </div>

        {/* Chart */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-base font-semibold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
                {activeSector} — WACI Trajectory (tCO₂e / MEUR)
              </h3>
              {nzbaRef && (
                <p className="text-xs text-gray-500 mt-0.5">Source: {nzbaRef.source}</p>
              )}
            </div>
            {glidepathData?.current_rag && <RAGBadge rag={glidepathData.current_rag} label={`${glidepathData.current_rag} — Current Status`} />}
          </div>
          <SectorGlidepathChart dataPoints={chartDataPoints} sector={activeSector} />
        </div>

        {/* Chart legend note */}
        <div className="flex items-center gap-6 text-xs text-gray-500 mt-3">
          <div className="flex items-center gap-2"><span className="w-4 h-0.5 bg-cyan-400 inline-block" />Actual WACI (portfolio)</div>
          <div className="flex items-center gap-2"><span className="w-4 h-0.5 border-t-2 border-dashed border-emerald-400 inline-block" />NZBA Target</div>
          <div className="flex items-center gap-2"><span className="w-4 h-0.5 border-t border-dashed border-gray-400 inline-block opacity-40" />IEA NZE Reference</div>
        </div>
      </div>

      {/* Status Grid */}
      <div className="rounded-xl border border-white/10 p-5" style={{ background: 'hsl(222,35%,9%)' }}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
            Portfolio Glidepath Status — Sector × Year
          </h3>
          <span className="text-xs text-gray-500">vs NZBA sector targets</span>
        </div>
        <GlidepathStatusGrid
          grid={statusGrid?.grid || []}
          sectors={selectedSectors}
          years={GRID_YEARS}
        />
      </div>

      {/* NZBA reference table */}
      {nzbaRef && (
        <div className="rounded-xl border border-white/10 p-5" style={{ background: 'hsl(222,35%,9%)' }}>
          <SectionTitle>{activeSector} — NZBA Reference Values</SectionTitle>
          <div className="grid grid-cols-3 md:grid-cols-7 gap-3">
            {nzbaRef.glidepath.filter(g => [2025, 2030, 2035, 2040, 2045, 2050].includes(g.year)).map(g => (
              <div key={g.year} className="text-center">
                <div className="text-xs text-gray-500">{g.year}</div>
                <div className="text-lg font-bold text-white" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{g.value.toFixed(0)}</div>
                <div className="text-xs text-gray-600">tCO₂e/MEUR</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
