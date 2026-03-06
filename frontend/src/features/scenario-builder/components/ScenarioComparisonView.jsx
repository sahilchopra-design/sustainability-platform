/**
 * ScenarioComparisonView — side-by-side comparison of 2–3 scenarios.
 * Shows parameter diffs and metric comparison chart.
 */
import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { SCENARIO_TEMPLATES, NGFS_FAMILY_META, ALL_PARAMETERS, buildScenarioParams } from '../data/ngfsData';

const COMPARE_COLORS = ['#22d3ee', '#f59e0b', '#a78bfa'];

// ─── Helpers ─────────────────────────────────────────────────────────────────

function buildCompareScenario(template) {
  return {
    id:         template.id,
    name:       template.name,
    ngfsFamily: template.ngfsFamily || 'Orderly',
    category:   template.category,
    parameters: buildScenarioParams(template),
  };
}

// ─── Parameter diff table ────────────────────────────────────────────────────

function ParamDiffTable({ scenarios }) {
  const SHOW_PARAMS = ['carbon_price_usd', 'temperature_rise_c', 'renewable_share_pct', 'policy_stringency', 'gdp_growth_pct', 'credit_spread_bps'];

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[11px]" data-testid="param-diff-table">
        <thead>
          <tr className="border-b border-white/8">
            <th className="text-left text-white/35 font-normal pb-2 pr-3 w-36">Parameter</th>
            {scenarios.map((s, i) => (
              <th key={s.id} className="text-right pb-2 px-2 font-medium" style={{ color: COMPARE_COLORS[i] }}>
                {s.name.length > 20 ? s.name.slice(0, 18) + '…' : s.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {SHOW_PARAMS.map(paramId => {
            const paramDef = ALL_PARAMETERS.find(p => p.id === paramId);
            if (!paramDef) return null;

            const values = scenarios.map(s => {
              const p = s.parameters.find(pp => pp.id === paramId);
              return p?.value ?? null;
            });

            const minVal = Math.min(...values.filter(v => v != null));
            const maxVal = Math.max(...values.filter(v => v != null));
            const hasVariance = maxVal - minVal > 0.001;

            return (
              <tr key={paramId} className="border-b border-white/5">
                <td className="py-1.5 pr-3">
                  <div className="text-white/60">{paramDef.label}</div>
                  <div className="text-[9px] text-white/25">{paramDef.unit}</div>
                </td>
                {values.map((val, i) => {
                  const isMin = hasVariance && val === minVal;
                  const isMax = hasVariance && val === maxVal;
                  return (
                    <td key={i} className="text-right py-1.5 px-2">
                      <span className={`font-mono ${
                        isMax ? 'text-amber-400 font-semibold' :
                        isMin ? 'text-emerald-400/80' : 'text-white/65'
                      }`}>
                        {val?.toFixed(2) ?? '—'}
                      </span>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ─── Metric comparison chart ──────────────────────────────────────────────────

function MetricComparisonChart({ scenarios }) {
  const metrics = [
    { key: 'carbon_price_usd',   label: 'Carbon Price',  unit: '$/tCO2e' },
    { key: 'temperature_rise_c', label: 'Temp Rise',     unit: '°C'      },
    { key: 'policy_stringency',  label: 'Policy',        unit: 'Index'   },
    { key: 'renewable_share_pct',label: 'Renewables',    unit: '%'       },
  ];

  const chartData = metrics.map(m => {
    const row = { metric: m.label, unit: m.unit };
    scenarios.forEach((s, i) => {
      const p = s.parameters.find(pp => pp.id === m.key);
      row[`s${i}`] = p?.value ?? 0;
    });
    return row;
  });

  return (
    <div style={{ height: 200 }} data-testid="metric-comparison-chart">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="metric" tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: 'rgba(255,255,255,0.2)', fontSize: 9 }} axisLine={false} tickLine={false} width={30} />
          <Tooltip
            contentStyle={{ background: '#0d1526', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 11 }}
            labelStyle={{ color: 'rgba(255,255,255,0.6)' }}
          />
          <Legend
            wrapperStyle={{ fontSize: 10, color: 'rgba(255,255,255,0.4)' }}
            formatter={(value, entry) => scenarios[parseInt(value.replace('s', ''))]?.name?.slice(0, 20) || value}
          />
          {scenarios.map((s, i) => (
            <Bar key={`s${i}`} dataKey={`s${i}`} name={`s${i}`} fill={COMPARE_COLORS[i]} opacity={0.8} radius={[2,2,0,0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── Main component ────────────────────────────────────────────────────────────

export function ScenarioComparisonView({ currentScenario }) {
  const [selectedIds, setSelectedIds] = useState([]);
  const [tab, setTab] = useState('params'); // 'params' | 'chart'

  // Templates available to compare against
  const comparableTemplates = SCENARIO_TEMPLATES.filter(t =>
    !selectedIds.includes(t.id)
  );

  const toggleTemplate = (id) => {
    setSelectedIds(prev => {
      if (prev.includes(id)) return prev.filter(x => x !== id);
      if (prev.length >= 2) return [...prev.slice(1), id]; // max 2 others
      return [...prev, id];
    });
  };

  // Build comparison scenarios: current + selected templates
  const comparisonScenarios = [
    { ...currentScenario, name: currentScenario.name || 'Your Scenario' },
    ...selectedIds.map(id => {
      const tpl = SCENARIO_TEMPLATES.find(t => t.id === id);
      return tpl ? buildCompareScenario(tpl) : null;
    }).filter(Boolean),
  ];

  return (
    <div className="flex flex-col gap-4" data-testid="scenario-comparison-view">
      {/* Selector */}
      <div>
        <p className="text-[11px] text-white/40 mb-2">Compare with (up to 2 templates):</p>
        <div className="flex flex-wrap gap-1.5">
          {SCENARIO_TEMPLATES.map((tpl, i) => {
            const isSelected = selectedIds.includes(tpl.id);
            const meta = NGFS_FAMILY_META[tpl.ngfsFamily] || {};
            const colorIdx = selectedIds.indexOf(tpl.id);
            return (
              <button
                key={tpl.id}
                onClick={() => toggleTemplate(tpl.id)}
                className={`text-[10px] px-2 py-1 rounded border transition-colors ${
                  isSelected
                    ? 'border-white/20 text-white/80 font-semibold'
                    : 'border-white/8 text-white/35 hover:border-white/16 hover:text-white/55'
                }`}
                style={isSelected ? { borderColor: COMPARE_COLORS[colorIdx + 1], color: COMPARE_COLORS[colorIdx + 1] } : {}}
              >
                {tpl.name.length > 24 ? tpl.name.slice(0, 22) + '…' : tpl.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* Legend */}
      {comparisonScenarios.length > 1 && (
        <div className="flex flex-wrap gap-3">
          {comparisonScenarios.map((s, i) => (
            <div key={s.id || i} className="flex items-center gap-1.5 text-[10px]">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COMPARE_COLORS[i] }} />
              <span style={{ color: COMPARE_COLORS[i] }}>{s.name?.slice(0, 24)}</span>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      {comparisonScenarios.length > 1 && (
        <>
          <div className="flex gap-1 border-b border-white/8 pb-0">
            {[['params', 'Parameters'], ['chart', 'Chart']].map(([key, lbl]) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`text-[11px] px-3 py-1.5 rounded-t border-b-2 transition-colors ${
                  tab === key
                    ? 'border-cyan-500 text-cyan-300'
                    : 'border-transparent text-white/40 hover:text-white/60'
                }`}
              >
                {lbl}
              </button>
            ))}
          </div>

          {tab === 'params' && <ParamDiffTable scenarios={comparisonScenarios} />}
          {tab === 'chart'  && <MetricComparisonChart scenarios={comparisonScenarios} />}
        </>
      )}

      {comparisonScenarios.length === 1 && (
        <div className="text-[12px] text-white/25 py-6 text-center">
          Select at least one template above to compare
        </div>
      )}
    </div>
  );
}

export default ScenarioComparisonView;
