/**
 * NGFSDataBrowser — browse official NGFS Phase IV variables and trajectories.
 * Filter by family, region, variable. Click "Import" to bring trajectory into scenario.
 */
import React, { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { NGFS_VARIABLES, ALL_PARAMETERS, NGFS_FAMILY_META, buildTrajectory } from '../data/ngfsData';

const FAMILY_COLORS = {
  Orderly:           '#22d3ee',
  Disorderly:        '#f59e0b',
  'Hot house world': '#f87171',
};

const YEARS = [2025, 2030, 2035, 2040, 2045, 2050];

// ─── Trajectory preview chart ────────────────────────────────────────────────

function TrajectoryPreview({ paramId }) {
  const param = ALL_PARAMETERS.find(p => p.id === paramId);
  if (!param) return null;

  const chartData = YEARS.map(yr => {
    const row = { year: yr };
    ['Orderly', 'Disorderly', 'Hot house world'].forEach(fam => {
      row[fam] = param.trajectories?.[fam]?.[yr] ?? null;
    });
    return row;
  });

  return (
    <div style={{ height: 180 }} className="mt-2">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="year" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: 'rgba(255,255,255,0.2)', fontSize: 9 }} axisLine={false} tickLine={false} width={36}
            tickFormatter={v => v >= 1000 ? `${(v/1000).toFixed(1)}k` : v.toFixed(1)} />
          <Tooltip
            contentStyle={{ background: '#0d1526', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 10 }}
            labelStyle={{ color: 'rgba(255,255,255,0.5)' }}
          />
          <Legend wrapperStyle={{ fontSize: 9, color: 'rgba(255,255,255,0.35)' }} />
          {['Orderly', 'Disorderly', 'Hot house world'].map(fam => (
            <Line key={fam} dataKey={fam} stroke={FAMILY_COLORS[fam]} strokeWidth={1.8} dot={false}
              name={fam === 'Hot house world' ? 'Hot House' : fam} connectNulls />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Variable card ────────────────────────────────────────────────────────────

function VariableCard({ variable, isSelected, onSelect, onImport }) {
  const param = ALL_PARAMETERS.find(p => p.id === variable.paramId);
  const familyMeta = variable.family !== 'all' ? NGFS_FAMILY_META[variable.family] : null;

  return (
    <div
      className={`rounded-lg border p-3 cursor-pointer transition-all ${
        isSelected
          ? 'border-cyan-500/50 bg-cyan-500/8'
          : 'border-white/8 bg-[#0d1526] hover:border-white/16'
      }`}
      onClick={() => onSelect(variable)}
      data-testid={`ngfs-variable-${variable.id}`}
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <div>
          <h5 className="text-[12px] font-semibold text-white/85">{variable.name}</h5>
          <p className="text-[10px] text-white/35">{variable.unit}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {familyMeta ? (
            <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border ${familyMeta.bgClass} ${familyMeta.textClass} ${familyMeta.borderClass}`}>
              {variable.family === 'Hot house world' ? 'Hot House' : variable.family}
            </span>
          ) : (
            <span className="text-[9px] text-white/30 bg-white/5 px-1.5 py-0.5 rounded border border-white/10">
              All Scenarios
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between text-[9px] text-white/25 mt-2">
        <span>{variable.source}</span>
        <span>Updated {variable.lastUpdated}</span>
      </div>
    </div>
  );
}

// ─── Main component ────────────────────────────────────────────────────────────

export function NGFSDataBrowser({ onImportVariable }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [familyFilter, setFamilyFilter] = useState('all');
  const [selectedVariable, setSelectedVariable] = useState(null);

  const filtered = useMemo(() => {
    let list = NGFS_VARIABLES;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(v =>
        v.name.toLowerCase().includes(q) ||
        v.unit.toLowerCase().includes(q) ||
        v.source.toLowerCase().includes(q)
      );
    }
    if (familyFilter !== 'all') {
      list = list.filter(v => v.family === familyFilter || v.family === 'all');
    }
    return list;
  }, [searchQuery, familyFilter]);

  const selectedParam = selectedVariable
    ? ALL_PARAMETERS.find(p => p.id === selectedVariable.paramId)
    : null;

  return (
    <div className="flex flex-col gap-3" data-testid="ngfs-data-browser">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-[13px] font-semibold text-white/85">NGFS Phase IV Variables</h4>
          <p className="text-[10px] text-white/35">Official scenarios · REMIND-MAgPIE · GCAM · MAGICC</p>
        </div>
        <span className="text-[10px] text-white/30 bg-white/5 px-2 py-0.5 rounded">
          {filtered.length} variables
        </span>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <svg className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-white/25" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search variables..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-7 pr-3 py-1.5 text-[11px] bg-white/5 border border-white/10 rounded text-white/75 placeholder-white/20 focus:outline-none focus:border-cyan-500/40"
          />
        </div>
        <select
          value={familyFilter}
          onChange={e => setFamilyFilter(e.target.value)}
          className="text-[11px] bg-white/5 border border-white/10 rounded px-2 py-1.5 text-white/55 focus:outline-none"
        >
          <option value="all">All Families</option>
          <option value="Orderly">Orderly</option>
          <option value="Disorderly">Disorderly</option>
          <option value="Hot house world">Hot House World</option>
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Variable list */}
        <div className="space-y-2 overflow-y-auto" style={{ maxHeight: 420 }}>
          {filtered.map(v => (
            <VariableCard
              key={v.id}
              variable={v}
              isSelected={selectedVariable?.id === v.id}
              onSelect={setSelectedVariable}
              onImport={onImportVariable}
            />
          ))}
          {filtered.length === 0 && (
            <div className="text-center py-8 text-white/25 text-sm">No variables match your filters</div>
          )}
        </div>

        {/* Detail panel */}
        <div className="bg-[#0d1526] border border-white/8 rounded-lg p-3">
          {selectedVariable ? (
            <>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h5 className="text-[13px] font-semibold text-white/90">{selectedVariable.name}</h5>
                  <p className="text-[10px] text-white/40">{selectedVariable.unit} · {selectedVariable.region}</p>
                </div>
                {onImportVariable && selectedParam && (
                  <button
                    onClick={() => onImportVariable(selectedVariable.paramId, selectedVariable.family)}
                    className="text-[10px] font-semibold px-2.5 py-1 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/25 transition-colors"
                  >
                    Import to Scenario
                  </button>
                )}
              </div>

              {/* 2050 values by family */}
              {selectedParam && (
                <div className="grid grid-cols-3 gap-2 mb-3">
                  {['Orderly', 'Disorderly', 'Hot house world'].map(fam => {
                    const val2050 = selectedParam.trajectories?.[fam]?.[2050];
                    const meta = NGFS_FAMILY_META[fam];
                    return (
                      <div key={fam} className={`rounded p-2 border ${meta.bgClass} ${meta.borderClass}`}>
                        <div className={`text-[9px] font-semibold mb-0.5 ${meta.textClass}`}>
                          {fam === 'Hot house world' ? 'Hot House' : fam}
                        </div>
                        <div className="text-[13px] font-bold text-white/85">
                          {val2050?.toFixed(2) ?? '—'}
                        </div>
                        <div className="text-[9px] text-white/30">{selectedVariable.unit}</div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Trajectory chart */}
              {selectedVariable.paramId && (
                <TrajectoryPreview paramId={selectedVariable.paramId} />
              )}

              <div className="flex items-center justify-between text-[9px] text-white/25 mt-2 pt-2 border-t border-white/8">
                <span>Source: {selectedVariable.source}</span>
                <span>Last updated: {selectedVariable.lastUpdated}</span>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-white/20">
              <svg className="h-10 w-10 mb-2 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-[12px]">Select a variable</p>
              <p className="text-[10px]">to view trajectory data</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default NGFSDataBrowser;
