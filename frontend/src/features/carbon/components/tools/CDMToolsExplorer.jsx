/**
 * CDMToolsExplorer Component
 * Browsable explorer for all 43 UNFCCC CDM Methodological Tools.
 * Features:
 *   - Category-grouped accordion list of all tools
 *   - Per-tool detail panel with description, input schema, "Run Tool" form
 *   - Methodology dependency graph (select methodology -> see required tools)
 *   - Tool Chain Runner: select methodology -> fill inputs -> execute full chain
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';

// ---- Category metadata (icon + color) ----
const CATEGORY_META = {
  ADDITIONALITY: { icon: '\u2714', color: '#8e44ad', label: 'Additionality' },
  EMISSION_CALC: { icon: '\u2601', color: '#e74c3c', label: 'Emission Calculation' },
  BASELINE: { icon: '\u2500', color: '#2980b9', label: 'Baseline' },
  BASELINE_GRID: { icon: '\u26a1', color: '#f39c12', label: 'Grid Emission Factor' },
  TRANSPORT: { icon: '\ud83d\ude8c', color: '#16a085', label: 'Transport' },
  FINANCIAL: { icon: '\ud83d\udcb0', color: '#27ae60', label: 'Financial Analysis' },
  DEFAULTS: { icon: '\u2699', color: '#7f8c8d', label: 'Default Values' },
  AR_ADDITIONALITY: { icon: '\ud83c\udf33', color: '#2ecc71', label: 'A/R Additionality' },
  AR_MEASUREMENT: { icon: '\ud83d\udccf', color: '#1abc9c', label: 'A/R Measurement' },
  AR_EMISSION: { icon: '\ud83d\udd25', color: '#e67e22', label: 'A/R Emission' },
  AR_CARBON_STOCK: { icon: '\ud83c\udf3f', color: '#27ae60', label: 'A/R Carbon Stock' },
  AR_LEAKAGE: { icon: '\u2194', color: '#c0392b', label: 'A/R Leakage' },
  AR_ELIGIBILITY: { icon: '\ud83d\udcdc', color: '#34495e', label: 'A/R Eligibility' },
};

const getCategoryMeta = (cat) =>
  CATEGORY_META[cat] || { icon: '\u2022', color: '#95a5a6', label: cat };

// ---- Styles ----
const styles = {
  container: {
    maxWidth: 1200,
    margin: '0 auto',
    padding: 24,
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    color: '#1a1a2e',
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 700,
    margin: 0,
    color: '#1a1a2e',
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    margin: '4px 0 0 0',
  },
  tabBar: {
    display: 'flex',
    gap: 0,
    borderBottom: '2px solid #e0e0e0',
    marginBottom: 24,
  },
  tab: (active) => ({
    padding: '10px 20px',
    cursor: 'pointer',
    fontWeight: active ? 700 : 500,
    fontSize: 14,
    color: active ? '#2980b9' : '#666',
    borderBottom: active ? '2px solid #2980b9' : '2px solid transparent',
    marginBottom: -2,
    background: 'none',
    border: 'none',
    borderBottomWidth: 2,
    borderBottomStyle: 'solid',
    borderBottomColor: active ? '#2980b9' : 'transparent',
    transition: 'all 0.2s',
  }),
  searchBox: {
    width: '100%',
    padding: '10px 14px',
    borderRadius: 8,
    border: '1px solid #ddd',
    fontSize: 14,
    marginBottom: 16,
    outline: 'none',
    boxSizing: 'border-box',
  },
  categoryHeader: (color, expanded) => ({
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '12px 16px',
    background: expanded ? color + '11' : '#f8f9fa',
    borderRadius: 8,
    cursor: 'pointer',
    marginBottom: expanded ? 0 : 8,
    borderBottomLeftRadius: expanded ? 0 : 8,
    borderBottomRightRadius: expanded ? 0 : 8,
    border: `1px solid ${expanded ? color + '44' : '#e0e0e0'}`,
    borderBottom: expanded ? 'none' : undefined,
    transition: 'all 0.2s',
  }),
  categoryTitle: {
    fontWeight: 700,
    fontSize: 15,
  },
  categoryCount: {
    fontSize: 12,
    color: '#999',
    marginLeft: 8,
  },
  chevron: (expanded) => ({
    transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
    transition: 'transform 0.2s',
    fontSize: 14,
    color: '#999',
  }),
  toolList: (color) => ({
    padding: '0 0 8px 0',
    border: `1px solid ${color}44`,
    borderTop: 'none',
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
    marginBottom: 8,
    background: '#fff',
  }),
  toolRow: (selected) => ({
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '10px 16px',
    cursor: 'pointer',
    background: selected ? '#eaf2fa' : 'transparent',
    borderLeft: selected ? '3px solid #2980b9' : '3px solid transparent',
    transition: 'all 0.15s',
  }),
  toolCode: {
    fontWeight: 700,
    fontSize: 13,
    color: '#2980b9',
    minWidth: 80,
  },
  toolName: {
    flex: 1,
    fontSize: 13,
    marginLeft: 12,
    color: '#333',
  },
  badge: (color) => ({
    fontSize: 10,
    fontWeight: 700,
    padding: '2px 8px',
    borderRadius: 10,
    background: color + '22',
    color: color,
  }),
  detailPanel: {
    padding: 24,
    background: '#fff',
    border: '1px solid #e0e0e0',
    borderRadius: 12,
    marginTop: 16,
  },
  detailTitle: {
    fontSize: 20,
    fontWeight: 700,
    marginBottom: 4,
  },
  detailCode: {
    fontSize: 13,
    color: '#2980b9',
    fontWeight: 600,
    marginBottom: 12,
  },
  detailDescription: {
    fontSize: 14,
    color: '#555',
    lineHeight: 1.6,
    marginBottom: 16,
  },
  metaGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: 12,
    marginBottom: 20,
  },
  metaCard: {
    padding: 12,
    background: '#f8f9fa',
    borderRadius: 8,
    fontSize: 13,
  },
  metaLabel: {
    fontWeight: 600,
    fontSize: 11,
    color: '#999',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  metaValue: {
    fontWeight: 600,
    color: '#1a1a2e',
  },
  inputForm: {
    marginTop: 16,
    padding: 16,
    background: '#f8f9fa',
    borderRadius: 8,
    border: '1px solid #e0e0e0',
  },
  inputRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  inputLabel: {
    minWidth: 200,
    fontSize: 13,
    fontWeight: 600,
  },
  input: {
    flex: 1,
    padding: '8px 12px',
    borderRadius: 6,
    border: '1px solid #ccc',
    fontSize: 13,
  },
  button: (variant) => ({
    padding: '10px 20px',
    borderRadius: 8,
    border: 'none',
    fontWeight: 700,
    fontSize: 14,
    cursor: 'pointer',
    background: variant === 'primary' ? '#2980b9' : variant === 'success' ? '#27ae60' : '#e0e0e0',
    color: variant === 'primary' || variant === 'success' ? '#fff' : '#333',
  }),
  resultBox: {
    marginTop: 16,
    padding: 16,
    background: '#e8f8f0',
    borderRadius: 8,
    border: '1px solid #27ae6044',
  },
  errorBox: {
    marginTop: 16,
    padding: 16,
    background: '#fce4e4',
    borderRadius: 8,
    border: '1px solid #e74c3c44',
    color: '#c0392b',
    fontSize: 13,
  },
  chainCard: {
    padding: 16,
    background: '#fff',
    border: '1px solid #e0e0e0',
    borderRadius: 8,
    marginBottom: 12,
  },
  toolChip: (color) => ({
    display: 'inline-block',
    padding: '3px 10px',
    borderRadius: 12,
    fontSize: 11,
    fontWeight: 700,
    background: (color || '#2980b9') + '18',
    color: color || '#2980b9',
    marginRight: 6,
    marginBottom: 4,
  }),
  emptyState: {
    padding: 48,
    textAlign: 'center',
    color: '#999',
    fontSize: 14,
  },
};


// ===================== Sub-components =====================

/**
 * CategoryAccordion - expandable group of tools
 */
const CategoryAccordion = ({
  category,
  tools,
  expanded,
  onToggle,
  selectedTool,
  onSelectTool,
}) => {
  const meta = getCategoryMeta(category);
  return (
    <div>
      <div
        style={styles.categoryHeader(meta.color, expanded)}
        onClick={onToggle}
      >
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ marginRight: 8, fontSize: 18 }}>{meta.icon}</span>
          <span style={styles.categoryTitle}>{meta.label}</span>
          <span style={styles.categoryCount}>{tools.length} tools</span>
        </div>
        <span style={styles.chevron(expanded)}>{'\u25B6'}</span>
      </div>
      {expanded && (
        <div style={styles.toolList(meta.color)}>
          {tools.map((t) => (
            <div
              key={t.code}
              style={styles.toolRow(selectedTool === t.code)}
              onClick={() => onSelectTool(t.code)}
            >
              <span style={styles.toolCode}>{t.code}</span>
              <span style={styles.toolName}>{t.name}</span>
              <span style={styles.badge(meta.color)}>
                {t.version || 'v1'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};


/**
 * ToolDetailPanel - full detail + run form for a single tool
 */
const ToolDetailPanel = ({ toolCode, onClose }) => {
  const [detail, setDetail] = useState(null);
  const [defaults, setDefaults] = useState({});
  const [inputs, setInputs] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!toolCode) return;
    setResult(null);
    setError(null);
    // Fetch tool detail + defaults in parallel
    Promise.all([
      fetch(`${API_BASE}/api/v1/cdm-tools/${toolCode}`).then((r) => r.json()),
      fetch(`${API_BASE}/api/v1/cdm-tools/${toolCode}/defaults`).then((r) =>
        r.json()
      ),
    ])
      .then(([det, def]) => {
        setDetail(det);
        const defs = def.default_parameters || {};
        setDefaults(defs);
        setInputs({ ...defs });
      })
      .catch(() => {
        setDetail(null);
      });
  }, [toolCode]);

  const handleInputChange = (key, val) => {
    setInputs((prev) => ({ ...prev, [key]: val }));
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      // Parse numeric values
      const parsedInputs = {};
      Object.entries(inputs).forEach(([k, v]) => {
        const num = Number(v);
        parsedInputs[k] = isNaN(num) ? v : num;
      });

      const resp = await fetch(
        `${API_BASE}/api/v1/cdm-tools/${toolCode}/calculate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ inputs: parsedInputs }),
        }
      );
      const data = await resp.json();
      if (data.success) {
        setResult(data.result);
      } else {
        setError(data.error || 'Calculation failed');
      }
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  if (!detail) {
    return (
      <div style={styles.detailPanel}>
        <div style={{ color: '#999', fontSize: 14 }}>Loading tool detail...</div>
      </div>
    );
  }

  const meta = getCategoryMeta(detail.category);
  const inputFields = detail.input_schema
    ? Object.entries(detail.input_schema)
    : Object.keys(defaults).map((k) => [k, { type: 'number' }]);

  return (
    <div style={styles.detailPanel}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}
      >
        <div>
          <div style={styles.detailTitle}>{detail.name}</div>
          <div style={styles.detailCode}>
            {detail.code} &middot;{' '}
            <span style={styles.badge(meta.color)}>{meta.label}</span>
            {detail.version && (
              <span
                style={{
                  marginLeft: 8,
                  fontSize: 12,
                  color: '#999',
                }}
              >
                {detail.version}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            fontSize: 20,
            cursor: 'pointer',
            color: '#999',
          }}
        >
          {'\u2715'}
        </button>
      </div>

      <div style={styles.detailDescription}>
        {detail.description || 'No description available.'}
      </div>

      {/* Metadata grid */}
      <div style={styles.metaGrid}>
        {detail.unfccc_reference && (
          <div style={styles.metaCard}>
            <div style={styles.metaLabel}>UNFCCC Reference</div>
            <div style={styles.metaValue}>{detail.unfccc_reference}</div>
          </div>
        )}
        <div style={styles.metaCard}>
          <div style={styles.metaLabel}>Category</div>
          <div style={styles.metaValue}>{meta.label}</div>
        </div>
        <div style={styles.metaCard}>
          <div style={styles.metaLabel}>Status</div>
          <div style={styles.metaValue}>{detail.status || 'Active'}</div>
        </div>
        {detail.applicable_scopes && detail.applicable_scopes.length > 0 && (
          <div style={styles.metaCard}>
            <div style={styles.metaLabel}>Applicable Scopes</div>
            <div style={styles.metaValue}>
              {detail.applicable_scopes.join(', ')}
            </div>
          </div>
        )}
      </div>

      {/* Run Tool Form */}
      <div style={styles.inputForm}>
        <div
          style={{
            fontWeight: 700,
            fontSize: 15,
            marginBottom: 12,
            color: '#1a1a2e',
          }}
        >
          Run Tool
        </div>
        {inputFields.length === 0 ? (
          <div style={{ fontSize: 13, color: '#999', marginBottom: 12 }}>
            This tool uses default parameters. Click "Calculate" to run.
          </div>
        ) : (
          inputFields.map(([key, schema]) => (
            <div key={key} style={styles.inputRow}>
              <label style={styles.inputLabel}>
                {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
              </label>
              <input
                type={
                  schema && schema.type === 'string' ? 'text' : 'number'
                }
                value={inputs[key] ?? ''}
                onChange={(e) => handleInputChange(key, e.target.value)}
                placeholder={
                  defaults[key] !== undefined
                    ? `Default: ${defaults[key]}`
                    : ''
                }
                style={styles.input}
              />
            </div>
          ))
        )}

        <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
          <button
            style={styles.button('primary')}
            onClick={handleRun}
            disabled={loading}
          >
            {loading ? 'Calculating...' : 'Calculate'}
          </button>
          {Object.keys(defaults).length > 0 && (
            <button
              style={styles.button('default')}
              onClick={() => setInputs({ ...defaults })}
            >
              Reset to Defaults
            </button>
          )}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div style={styles.resultBox}>
          <div
            style={{ fontWeight: 700, fontSize: 15, marginBottom: 8 }}
          >
            Calculation Result
          </div>
          <div style={styles.metaGrid}>
            {Object.entries(result.outputs || {}).map(([k, v]) => (
              <div key={k} style={styles.metaCard}>
                <div style={styles.metaLabel}>{k.replace(/_/g, ' ')}</div>
                <div
                  style={{
                    ...styles.metaValue,
                    fontSize: 18,
                    color: '#27ae60',
                  }}
                >
                  {typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 4 }) : String(v)}
                </div>
              </div>
            ))}
          </div>
          {result.unit && (
            <div style={{ fontSize: 12, color: '#666', marginTop: 4 }}>
              Unit: {result.unit}
            </div>
          )}
          {result.methodology_notes && (
            <div
              style={{
                marginTop: 8,
                fontSize: 12,
                color: '#555',
                fontStyle: 'italic',
              }}
            >
              {result.methodology_notes}
            </div>
          )}
        </div>
      )}

      {error && (
        <div style={styles.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
};


/**
 * MethodologyDepGraph - shows tools required by a methodology
 */
const MethodologyDepGraph = () => {
  const [methodologyCode, setMethodologyCode] = useState('');
  const [mapping, setMapping] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const POPULAR_METHODOLOGIES = [
    'ACM0001', 'ACM0002', 'ACM0006', 'ACM0009',
    'AMS-I.D', 'AR-ACM0003', 'VM0048', 'TPDDTEC',
  ];

  const handleLookup = async (code) => {
    const target = code || methodologyCode;
    if (!target) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(
        `${API_BASE}/api/v1/cdm-tools/for-methodology/${target.toUpperCase()}`
      );
      if (!resp.ok) {
        throw new Error(`No tool mapping found for ${target}`);
      }
      setMapping(await resp.json());
    } catch (e) {
      setError(e.message);
      setMapping(null);
    }
    setLoading(false);
  };

  return (
    <div>
      <div
        style={{
          fontWeight: 700,
          fontSize: 16,
          marginBottom: 12,
        }}
      >
        Methodology Tool Dependencies
      </div>
      <p style={{ fontSize: 13, color: '#666', marginBottom: 16 }}>
        Select or enter a methodology code to see which CDM tools it requires.
      </p>

      {/* Quick picks */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
        {POPULAR_METHODOLOGIES.map((m) => (
          <button
            key={m}
            onClick={() => {
              setMethodologyCode(m);
              handleLookup(m);
            }}
            style={{
              ...styles.button('default'),
              padding: '6px 14px',
              fontSize: 12,
              fontWeight: 600,
              background: methodologyCode === m ? '#2980b9' : '#f0f0f0',
              color: methodologyCode === m ? '#fff' : '#333',
            }}
          >
            {m}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          type="text"
          value={methodologyCode}
          onChange={(e) => setMethodologyCode(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === 'Enter' && handleLookup()}
          placeholder="e.g. ACM0002"
          style={{ ...styles.searchBox, marginBottom: 0, flex: 1 }}
        />
        <button
          style={styles.button('primary')}
          onClick={() => handleLookup()}
          disabled={loading}
        >
          {loading ? 'Looking up...' : 'Lookup'}
        </button>
      </div>

      {error && <div style={styles.errorBox}>{error}</div>}

      {mapping && (
        <div style={styles.chainCard}>
          <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>
            {mapping.methodology_code}
          </div>
          <div style={{ fontSize: 13, color: '#666', marginBottom: 12 }}>
            {mapping.total_tools} CDM tool{mapping.total_tools !== 1 ? 's' : ''} required
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {(mapping.tools || []).map((t) => {
              const meta = getCategoryMeta(t.category);
              return (
                <span key={t.code} style={styles.toolChip(meta.color)}>
                  {meta.icon} {t.code}: {t.short_name || t.name}
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};


/**
 * ToolChainRunner - execute full chain for a methodology
 */
const ToolChainRunner = () => {
  const [methodologyCode, setMethodologyCode] = useState('ACM0002');
  const [toolInputs, setToolInputs] = useState('{}');
  const [chainResult, setChainResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showJson, setShowJson] = useState(false);

  const PRESETS = {
    ACM0002: {
      label: 'ACM0002: 50MW Wind Farm India',
      inputs: JSON.stringify(
        {
          TOOL07: { country_code: 'IN' },
          TOOL01: {
            project_type: 'Grid-connected renewable energy',
            investment_irr: 12,
            benchmark_irr: 15,
            barriers: ['Investment barrier', 'Technological barrier'],
          },
          TOOL05: {
            annual_electricity_mwh: 122640,
          },
        },
        null,
        2
      ),
    },
    ACM0001: {
      label: 'ACM0001: Landfill Gas Brazil',
      inputs: JSON.stringify(
        {
          TOOL04: {
            waste_categories: { food: 150000, paper: 100000, wood: 50000, textiles: 30000 },
            doc_values: { food: 0.15, paper: 0.4, wood: 0.43, textiles: 0.24 },
            docf: 0.5,
            mcf: 1.0,
            ox_factor: 0.1,
            methane_fraction: 0.5,
          },
          TOOL06: {
            methane_flow_rate_m3h: 500,
            operating_hours: 8000,
            flare_efficiency: 0.98,
          },
        },
        null,
        2
      ),
    },
    'AR-ACM0003': {
      label: 'AR-ACM0003: Teak Plantation Myanmar',
      inputs: JSON.stringify(
        {
          'AR-TOOL14': {
            species: [
              {
                name: 'Tectona grandis',
                a: 0.153,
                b: 2.382,
                c: 0,
                wood_density: 0.55,
                count_per_hectare: 1100,
                avg_dbh_cm: 15,
                avg_height_m: 12,
              },
            ],
            area_hectares: 2000,
            root_to_shoot_ratio: 0.27,
            carbon_fraction: 0.47,
          },
          'AR-TOOL19': {
            land_type: 'Degraded grassland',
            years_since_deforestation: 25,
            canopy_cover_percent: 8,
            country: 'Myanmar',
          },
        },
        null,
        2
      ),
    },
  };

  const handlePreset = (key) => {
    setMethodologyCode(key);
    setToolInputs(PRESETS[key].inputs);
    setChainResult(null);
    setError(null);
  };

  const handleRunChain = async () => {
    setLoading(true);
    setError(null);
    setChainResult(null);
    try {
      let parsedInputs = {};
      try {
        parsedInputs = JSON.parse(toolInputs);
      } catch {
        throw new Error('Invalid JSON in tool inputs');
      }

      const resp = await fetch(
        `${API_BASE}/api/v1/cdm-tools/chain/${methodologyCode}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tool_inputs: parsedInputs }),
        }
      );
      const data = await resp.json();
      if (resp.ok) {
        setChainResult(data);
      } else {
        setError(data.detail || 'Chain execution failed');
      }
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  return (
    <div>
      <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>
        Tool Chain Runner
      </div>
      <p style={{ fontSize: 13, color: '#666', marginBottom: 16 }}>
        Execute the complete CDM tool chain for a methodology. Select a preset
        or enter your own methodology code and tool inputs.
      </p>

      {/* Presets */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
        {Object.entries(PRESETS).map(([key, preset]) => (
          <button
            key={key}
            onClick={() => handlePreset(key)}
            style={{
              ...styles.button('default'),
              fontSize: 12,
              padding: '8px 14px',
              background: methodologyCode === key ? '#2980b9' : '#f0f0f0',
              color: methodologyCode === key ? '#fff' : '#333',
            }}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {/* Methodology code input */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input
          type="text"
          value={methodologyCode}
          onChange={(e) => setMethodologyCode(e.target.value.toUpperCase())}
          placeholder="Methodology code"
          style={{ ...styles.searchBox, marginBottom: 0, flex: 1, maxWidth: 200 }}
        />
      </div>

      {/* Tool inputs textarea */}
      <div style={{ marginBottom: 12 }}>
        <label
          style={{
            display: 'block',
            fontWeight: 600,
            fontSize: 13,
            marginBottom: 4,
          }}
        >
          Tool Inputs (JSON)
        </label>
        <textarea
          value={toolInputs}
          onChange={(e) => setToolInputs(e.target.value)}
          rows={12}
          style={{
            width: '100%',
            padding: 12,
            borderRadius: 8,
            border: '1px solid #ccc',
            fontFamily: 'monospace',
            fontSize: 12,
            resize: 'vertical',
            boxSizing: 'border-box',
          }}
        />
      </div>

      <button
        style={styles.button('success')}
        onClick={handleRunChain}
        disabled={loading}
      >
        {loading ? 'Executing Chain...' : 'Execute Tool Chain'}
      </button>

      {error && <div style={styles.errorBox}>{error}</div>}

      {chainResult && (
        <div style={{ marginTop: 16 }}>
          {/* Summary bar */}
          <div
            style={{
              display: 'flex',
              gap: 16,
              marginBottom: 16,
              flexWrap: 'wrap',
            }}
          >
            <div
              style={{
                ...styles.metaCard,
                flex: 1,
                minWidth: 160,
                textAlign: 'center',
                background: chainResult.success ? '#e8f8f0' : '#fce4e4',
              }}
            >
              <div style={styles.metaLabel}>Status</div>
              <div
                style={{
                  fontWeight: 700,
                  fontSize: 18,
                  color: chainResult.success ? '#27ae60' : '#e74c3c',
                }}
              >
                {chainResult.success ? 'Success' : 'Partial Failure'}
              </div>
            </div>
            <div style={{ ...styles.metaCard, flex: 1, minWidth: 160, textAlign: 'center' }}>
              <div style={styles.metaLabel}>Tools Executed</div>
              <div style={{ fontWeight: 700, fontSize: 18, color: '#2980b9' }}>
                {chainResult.tools_executed}
              </div>
            </div>
            <div style={{ ...styles.metaCard, flex: 1, minWidth: 160, textAlign: 'center' }}>
              <div style={styles.metaLabel}>Tools Failed</div>
              <div
                style={{
                  fontWeight: 700,
                  fontSize: 18,
                  color: chainResult.tools_failed > 0 ? '#e74c3c' : '#27ae60',
                }}
              >
                {chainResult.tools_failed}
              </div>
            </div>
          </div>

          {/* Aggregated outputs */}
          {chainResult.aggregated_outputs && (
            <div style={styles.chainCard}>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>
                Aggregated Outputs
              </div>
              <div style={styles.metaGrid}>
                {Object.entries(chainResult.aggregated_outputs).map(([k, v]) => (
                  <div key={k} style={styles.metaCard}>
                    <div style={styles.metaLabel}>{k.replace(/_/g, ' ')}</div>
                    <div style={styles.metaValue}>
                      {typeof v === 'number'
                        ? v.toLocaleString(undefined, { maximumFractionDigits: 4 })
                        : typeof v === 'boolean'
                        ? v ? 'Yes' : 'No'
                        : String(v)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Per-tool results */}
          {(chainResult.results || []).length > 0 && (
            <div style={styles.chainCard}>
              <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 8 }}>
                Individual Tool Results
              </div>
              {chainResult.results.map((r, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: 12,
                    background: '#f8f9fa',
                    borderRadius: 6,
                    marginBottom: 8,
                    border: '1px solid #e0e0e0',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: 6,
                    }}
                  >
                    <span style={{ fontWeight: 700, fontSize: 13, color: '#2980b9' }}>
                      {r.tool_code}: {r.tool_name}
                    </span>
                    <span style={{ fontSize: 11, color: '#999' }}>{r.unit}</span>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {Object.entries(r.outputs || {}).map(([k, v]) => (
                      <span
                        key={k}
                        style={{
                          fontSize: 12,
                          padding: '2px 8px',
                          background: '#e8f8f0',
                          borderRadius: 4,
                        }}
                      >
                        <strong>{k}:</strong>{' '}
                        {typeof v === 'number' ? v.toLocaleString(undefined, { maximumFractionDigits: 4 }) : String(v)}
                      </span>
                    ))}
                  </div>
                  {r.methodology_notes && (
                    <div
                      style={{
                        marginTop: 4,
                        fontSize: 11,
                        color: '#666',
                        fontStyle: 'italic',
                      }}
                    >
                      {r.methodology_notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Errors */}
          {(chainResult.errors || []).length > 0 && (
            <div
              style={{
                ...styles.chainCard,
                border: '1px solid #e74c3c44',
                background: '#fce4e4',
              }}
            >
              <div
                style={{
                  fontWeight: 700,
                  fontSize: 14,
                  marginBottom: 8,
                  color: '#c0392b',
                }}
              >
                Errors
              </div>
              {chainResult.errors.map((err, i) => (
                <div key={i} style={{ fontSize: 12, marginBottom: 4, color: '#c0392b' }}>
                  {typeof err === 'object' ? JSON.stringify(err) : err}
                </div>
              ))}
            </div>
          )}

          {/* Raw JSON toggle */}
          <button
            style={{
              ...styles.button('default'),
              fontSize: 12,
              marginTop: 8,
            }}
            onClick={() => setShowJson(!showJson)}
          >
            {showJson ? 'Hide' : 'Show'} Raw JSON
          </button>
          {showJson && (
            <pre
              style={{
                marginTop: 8,
                padding: 12,
                background: '#1a1a2e',
                color: '#7bed9f',
                borderRadius: 8,
                fontSize: 11,
                overflow: 'auto',
                maxHeight: 400,
              }}
            >
              {JSON.stringify(chainResult, null, 2)}
            </pre>
          )}
        </div>
      )}
    </div>
  );
};


// ===================== Main Component =====================

const CDMToolsExplorer = () => {
  const [activeTab, setActiveTab] = useState('browse'); // browse | dependencies | chain
  const [tools, setTools] = useState([]);
  const [search, setSearch] = useState('');
  const [expandedCats, setExpandedCats] = useState({});
  const [selectedTool, setSelectedTool] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch all tools on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/cdm-tools/categories`)
      .then((r) => r.json())
      .then((data) => {
        const allTools = [];
        (data.categories || []).forEach((cat) => {
          (cat.tools || []).forEach((t) => allTools.push(t));
        });
        setTools(allTools);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Group tools by category + apply search filter
  const grouped = useMemo(() => {
    const filtered = search
      ? tools.filter(
          (t) =>
            t.code.toLowerCase().includes(search.toLowerCase()) ||
            t.name.toLowerCase().includes(search.toLowerCase()) ||
            (t.short_name || '').toLowerCase().includes(search.toLowerCase())
        )
      : tools;

    const groups = {};
    filtered.forEach((t) => {
      const cat = t.category || 'OTHER';
      if (!groups[cat]) groups[cat] = [];
      groups[cat].push(t);
    });
    return groups;
  }, [tools, search]);

  const toggleCategory = useCallback((cat) => {
    setExpandedCats((prev) => ({ ...prev, [cat]: !prev[cat] }));
  }, []);

  const handleSelectTool = useCallback((code) => {
    setSelectedTool((prev) => (prev === code ? null : code));
  }, []);

  const TABS = [
    { key: 'browse', label: 'Browse Tools' },
    { key: 'dependencies', label: 'Methodology Dependencies' },
    { key: 'chain', label: 'Tool Chain Runner' },
  ];

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>CDM Methodological Tools Explorer</h1>
        <p style={styles.subtitle}>
          Browse, explore, and execute all 43 UNFCCC CDM methodological tools
        </p>
      </div>

      {/* Tab bar */}
      <div style={styles.tabBar}>
        {TABS.map((t) => (
          <button
            key={t.key}
            style={styles.tab(activeTab === t.key)}
            onClick={() => {
              setActiveTab(t.key);
              setSelectedTool(null);
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Browse tab */}
      {activeTab === 'browse' && (
        <div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tools by code or name..."
            style={styles.searchBox}
          />

          {loading ? (
            <div style={styles.emptyState}>Loading CDM tools...</div>
          ) : Object.keys(grouped).length === 0 ? (
            <div style={styles.emptyState}>
              No tools match your search.
            </div>
          ) : (
            <>
              <div style={{ fontSize: 13, color: '#666', marginBottom: 12 }}>
                {tools.length} tools across {Object.keys(grouped).length}{' '}
                categories
                {search && (
                  <span>
                    {' '}
                    (showing{' '}
                    {Object.values(grouped).reduce((s, a) => s + a.length, 0)}{' '}
                    matching)
                  </span>
                )}
              </div>
              {Object.entries(grouped).map(([cat, catTools]) => (
                <CategoryAccordion
                  key={cat}
                  category={cat}
                  tools={catTools}
                  expanded={!!expandedCats[cat]}
                  onToggle={() => toggleCategory(cat)}
                  selectedTool={selectedTool}
                  onSelectTool={handleSelectTool}
                />
              ))}
            </>
          )}

          {/* Detail panel */}
          {selectedTool && (
            <ToolDetailPanel
              toolCode={selectedTool}
              onClose={() => setSelectedTool(null)}
            />
          )}
        </div>
      )}

      {/* Dependencies tab */}
      {activeTab === 'dependencies' && <MethodologyDepGraph />}

      {/* Chain runner tab */}
      {activeTab === 'chain' && <ToolChainRunner />}
    </div>
  );
};

export default CDMToolsExplorer;
