/**
 * ActivityGuide Component
 * Step-by-step wizard that guides users through selecting an economic activity,
 * understanding input requirements, and calculating carbon credits.
 *
 * Steps:
 *  1. Who are you? (user type)
 *  2. What sector? (filter by sector)
 *  3. Select your activity (card browser with search)
 *  4. Input Guide (fill parameters with data source help)
 *  5. Calculate (run methodology, show results)
 */

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import InputHelper from './InputHelper';

const API_BASE =
  process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const CDM_API = `${API_BASE}/api/v1/cdm-tools`;

// ---- Icons / badges ---------------------------------------------------

const SECTOR_ICONS = {
  Energy: '\u26A1',
  Waste: '\u267B',
  Forestry: '\uD83C\uDF33',
  Agriculture: '\uD83C\uDF3E',
  Industrial: '\uD83C\uDFED',
  Transport: '\uD83D\uDE8C',
  Buildings: '\uD83C\uDFE2',
  'Buildings & Household': '\uD83C\uDFE0',
  Financial: '\uD83D\uDCB0',
  Upstream: '\uD83D\uDD17',
  Downstream: '\uD83D\uDCE6',
  'Cross-Sector': '\uD83D\uDD04',
  Mining: '\u26CF',
  Textiles: '\uD83E\uDDF5',
  'Food & Beverage': '\uD83C\uDF5E',
  Healthcare: '\u2695',
  'Real Estate': '\uD83C\uDFD7',
  Technology: '\uD83D\uDCBB',
  'Blue Carbon': '\uD83C\uDF0A',
  Household: '\uD83C\uDFE0',
};

const SCALE_COLORS = {
  Large: '#3498db',
  Small: '#27ae60',
  Micro: '#e67e22',
};

const USER_TYPES = [
  { label: 'Corporate', desc: 'Large corporations, MNCs' },
  { label: 'MSME', desc: 'Micro, small and medium enterprises' },
  { label: 'Financial Institution', desc: 'Banks, funds, insurers' },
  { label: 'Energy Company', desc: 'Utilities, IPPs, developers' },
  { label: 'Municipality', desc: 'Cities, local government' },
  { label: 'NGO', desc: 'Non-profits, foundations' },
];

// ---- Styles -----------------------------------------------------------

const card = {
  background: '#fff',
  borderRadius: 10,
  border: '1px solid #e0e0e0',
  padding: 20,
  cursor: 'pointer',
  transition: 'all 0.2s',
};

const cardHover = {
  ...card,
  borderColor: '#3498db',
  boxShadow: '0 4px 12px rgba(52,152,219,0.15)',
};

const stepHeader = {
  fontSize: 22,
  fontWeight: 700,
  color: '#1a1a2e',
  marginBottom: 4,
};

const stepSub = {
  fontSize: 14,
  color: '#666',
  marginBottom: 24,
};

const btnPrimary = {
  padding: '10px 24px',
  background: '#3498db',
  color: '#fff',
  border: 'none',
  borderRadius: 8,
  fontSize: 14,
  fontWeight: 600,
  cursor: 'pointer',
};

const btnOutline = {
  padding: '10px 24px',
  background: 'transparent',
  color: '#3498db',
  border: '1px solid #3498db',
  borderRadius: 8,
  fontSize: 14,
  fontWeight: 600,
  cursor: 'pointer',
};

// =======================================================================
// Component
// =======================================================================

const ActivityGuide = () => {
  const [step, setStep] = useState(1);
  const [userType, setUserType] = useState(null);
  const [selectedSector, setSelectedSector] = useState(null);
  const [activities, setActivities] = useState([]);
  const [filteredActivities, setFilteredActivities] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedActivity, setSelectedActivity] = useState(null);
  const [activityDetail, setActivityDetail] = useState(null);
  const [inputValues, setInputValues] = useState({});
  const [calculating, setCalculating] = useState(false);
  const [calcResult, setCalcResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sectors, setSectors] = useState([]);
  const [hoverCard, setHoverCard] = useState(null);

  // -- Fetch all activities on mount ---
  useEffect(() => {
    const fetchActivities = async () => {
      try {
        setLoading(true);
        const res = await axios.get(`${CDM_API}/activities`);
        const data = res.data.activities || [];
        setActivities(data);
        // Extract unique sectors
        const secs = [...new Set(data.map((a) => a.sector))].sort();
        setSectors(secs);
      } catch (err) {
        console.error('Failed to load activities:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchActivities();
  }, []);

  // -- Filter when user type, sector, or search changes ---
  useEffect(() => {
    let filtered = [...activities];
    if (userType) {
      filtered = filtered.filter((a) =>
        a.user_types?.some((ut) => ut.toLowerCase() === userType.toLowerCase())
      );
    }
    if (selectedSector) {
      filtered = filtered.filter(
        (a) => a.sector?.toLowerCase() === selectedSector.toLowerCase()
      );
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (a) =>
          a.name?.toLowerCase().includes(q) ||
          a.sector?.toLowerCase().includes(q)
      );
    }
    setFilteredActivities(filtered);
  }, [activities, userType, selectedSector, searchQuery]);

  // -- Fetch activity detail ---
  const loadActivityDetail = useCallback(async (activityId) => {
    try {
      setLoading(true);
      const res = await axios.get(`${CDM_API}/activities/${activityId}`);
      setActivityDetail(res.data);
      // Pre-populate example values
      const defaults = {};
      (res.data.inputs_guide || []).forEach((ig) => {
        if (ig.example_value !== undefined && ig.example_value !== null) {
          defaults[ig.parameter] = ig.example_value;
        }
      });
      setInputValues(defaults);
    } catch (err) {
      console.error('Failed to load activity detail:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // -- Handle input change ---
  const handleInputChange = (param, value) => {
    setInputValues((prev) => ({ ...prev, [param]: value }));
  };

  // -- Calculate ---
  const handleCalculate = async () => {
    if (!activityDetail) return;
    setCalculating(true);
    setCalcResult(null);
    try {
      const methodology =
        activityDetail.recommended_methodology ||
        activityDetail.applicable_methodologies?.[0];
      if (!methodology) {
        setCalcResult({ error: 'No methodology mapped for this activity' });
        return;
      }
      // Build inputs dict — convert string values to numbers
      const numericInputs = {};
      Object.entries(inputValues).forEach(([k, v]) => {
        numericInputs[k] = v !== '' ? Number(v) : undefined;
      });
      numericInputs.use_cdm_tools = true;

      const res = await axios.post(
        `${API_BASE}/api/v1/carbon/methodologies/${methodology}/calculate`,
        numericInputs
      );
      setCalcResult(res.data);
    } catch (err) {
      // Try direct methodology engine endpoint
      try {
        const methodology =
          activityDetail.recommended_methodology ||
          activityDetail.applicable_methodologies?.[0];
        const numericInputs = {};
        Object.entries(inputValues).forEach(([k, v]) => {
          numericInputs[k] = v !== '' ? Number(v) : undefined;
        });
        const res = await axios.post(
          `${API_BASE}/api/v1/carbon/calculate`,
          { methodology_code: methodology, inputs: numericInputs }
        );
        setCalcResult(res.data);
      } catch (err2) {
        setCalcResult({
          error: err2.response?.data?.detail || err2.message,
        });
      }
    } finally {
      setCalculating(false);
    }
  };

  // -- Sector count ---
  const sectorCount = (sec) =>
    activities.filter(
      (a) =>
        a.sector === sec &&
        (!userType ||
          a.user_types?.some(
            (ut) => ut.toLowerCase() === userType.toLowerCase()
          ))
    ).length;

  // =====================================================================
  // RENDER
  // =====================================================================

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: 24 }}>
      {/* Progress bar */}
      <div
        style={{
          display: 'flex',
          gap: 4,
          marginBottom: 32,
        }}
      >
        {[1, 2, 3, 4, 5].map((s) => (
          <div
            key={s}
            style={{
              flex: 1,
              height: 4,
              borderRadius: 2,
              background: s <= step ? '#3498db' : '#e0e0e0',
              transition: 'background 0.3s',
            }}
          />
        ))}
      </div>

      {/* Step labels */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          marginBottom: 32,
          fontSize: 12,
          color: '#999',
        }}
      >
        {['User Type', 'Sector', 'Activity', 'Inputs', 'Results'].map(
          (l, i) => (
            <span
              key={l}
              style={{
                color: i + 1 <= step ? '#3498db' : '#bbb',
                fontWeight: i + 1 === step ? 700 : 400,
                cursor: i + 1 < step ? 'pointer' : 'default',
              }}
              onClick={() => i + 1 < step && setStep(i + 1)}
            >
              {l}
            </span>
          )
        )}
      </div>

      {/* ========== STEP 1: User Type ========== */}
      {step === 1 && (
        <div>
          <div style={stepHeader}>Who are you?</div>
          <p style={stepSub}>
            Select your organization type to see relevant carbon credit
            activities.
          </p>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280, 1fr))',
              gap: 16,
            }}
          >
            {USER_TYPES.map((ut) => (
              <div
                key={ut.label}
                style={hoverCard === ut.label ? cardHover : card}
                onMouseEnter={() => setHoverCard(ut.label)}
                onMouseLeave={() => setHoverCard(null)}
                onClick={() => {
                  setUserType(ut.label);
                  setStep(2);
                }}
              >
                <div
                  style={{ fontSize: 16, fontWeight: 600, color: '#1a1a2e' }}
                >
                  {ut.label}
                </div>
                <div style={{ fontSize: 13, color: '#666', marginTop: 4 }}>
                  {ut.desc}
                </div>
                <div
                  style={{
                    fontSize: 12,
                    color: '#3498db',
                    marginTop: 8,
                    fontWeight: 500,
                  }}
                >
                  {activities.filter((a) =>
                    a.user_types?.some(
                      (u) => u.toLowerCase() === ut.label.toLowerCase()
                    )
                  ).length}{' '}
                  activities
                </div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 16 }}>
            <button
              style={btnOutline}
              onClick={() => {
                setUserType(null);
                setStep(2);
              }}
            >
              Skip - Show all activities
            </button>
          </div>
        </div>
      )}

      {/* ========== STEP 2: Sector ========== */}
      {step === 2 && (
        <div>
          <div style={stepHeader}>What sector?</div>
          <p style={stepSub}>
            Choose a sector to narrow down activities
            {userType && ` for ${userType}`}.
          </p>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
              gap: 12,
            }}
          >
            {sectors.map((sec) => {
              const count = sectorCount(sec);
              if (count === 0) return null;
              return (
                <div
                  key={sec}
                  style={{
                    ...(hoverCard === sec ? cardHover : card),
                    textAlign: 'center',
                  }}
                  onMouseEnter={() => setHoverCard(sec)}
                  onMouseLeave={() => setHoverCard(null)}
                  onClick={() => {
                    setSelectedSector(sec);
                    setStep(3);
                  }}
                >
                  <div style={{ fontSize: 28, marginBottom: 4 }}>
                    {SECTOR_ICONS[sec] || '\uD83D\uDD27'}
                  </div>
                  <div
                    style={{ fontWeight: 600, fontSize: 14, color: '#1a1a2e' }}
                  >
                    {sec}
                  </div>
                  <div style={{ fontSize: 12, color: '#3498db', marginTop: 4 }}>
                    {count} activities
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
            <button style={btnOutline} onClick={() => setStep(1)}>
              Back
            </button>
            <button
              style={btnOutline}
              onClick={() => {
                setSelectedSector(null);
                setStep(3);
              }}
            >
              Skip - Show all sectors
            </button>
          </div>
        </div>
      )}

      {/* ========== STEP 3: Activity Selection ========== */}
      {step === 3 && (
        <div>
          <div style={stepHeader}>Select your activity</div>
          <p style={stepSub}>
            {filteredActivities.length} activities found
            {userType && ` for ${userType}`}
            {selectedSector && ` in ${selectedSector}`}.
          </p>

          {/* Search bar */}
          <input
            type="text"
            placeholder="Search activities..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 16px',
              borderRadius: 8,
              border: '1px solid #ccc',
              fontSize: 14,
              marginBottom: 16,
              boxSizing: 'border-box',
            }}
          />

          {/* Activity cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: 12,
              maxHeight: 480,
              overflowY: 'auto',
            }}
          >
            {filteredActivities.map((a) => (
              <div
                key={a.id}
                style={hoverCard === a.id ? cardHover : card}
                onMouseEnter={() => setHoverCard(a.id)}
                onMouseLeave={() => setHoverCard(null)}
                onClick={() => {
                  setSelectedActivity(a);
                  loadActivityDetail(a.id);
                  setStep(4);
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                  }}
                >
                  <div
                    style={{
                      fontWeight: 600,
                      fontSize: 14,
                      color: '#1a1a2e',
                      flex: 1,
                    }}
                  >
                    {a.name}
                  </div>
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: 4,
                      background: SCALE_COLORS[a.scale] || '#999',
                      color: '#fff',
                      fontSize: 10,
                      fontWeight: 700,
                      marginLeft: 8,
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {a.scale}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 12,
                    color: '#666',
                    marginTop: 4,
                  }}
                >
                  {SECTOR_ICONS[a.sector] || ''} {a.sector}
                  {a.value_chain_position &&
                    a.value_chain_position !== 'core' && (
                      <span style={{ marginLeft: 8, color: '#e67e22' }}>
                        [{a.value_chain_position}]
                      </span>
                    )}
                </div>
                {a.typical_credit_range && (
                  <div
                    style={{
                      fontSize: 11,
                      color: '#27ae60',
                      marginTop: 6,
                      fontWeight: 500,
                    }}
                  >
                    {a.typical_credit_range.min?.toLocaleString()} -{' '}
                    {a.typical_credit_range.max?.toLocaleString()}{' '}
                    {a.typical_credit_range.unit}
                  </div>
                )}
                {a.recommended_methodology && (
                  <div
                    style={{
                      fontSize: 11,
                      color: '#3498db',
                      marginTop: 4,
                    }}
                  >
                    Methodology: {a.recommended_methodology}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div style={{ marginTop: 16 }}>
            <button style={btnOutline} onClick={() => setStep(2)}>
              Back
            </button>
          </div>
        </div>
      )}

      {/* ========== STEP 4: Input Guide ========== */}
      {step === 4 && (
        <div>
          <div style={stepHeader}>
            {activityDetail?.name || selectedActivity?.name}
          </div>
          <p style={stepSub}>
            Fill in the parameters below. Each field includes data sourcing
            guidance.
          </p>

          {loading ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
              Loading activity details...
            </div>
          ) : activityDetail ? (
            <>
              {/* Activity metadata */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 1fr',
                  gap: 12,
                  marginBottom: 24,
                }}
              >
                <div style={{ ...card, cursor: 'default' }}>
                  <div style={{ fontSize: 11, color: '#999' }}>
                    Recommended Methodology
                  </div>
                  <div
                    style={{
                      fontSize: 16,
                      fontWeight: 700,
                      color: '#3498db',
                    }}
                  >
                    {activityDetail.recommended_methodology || 'N/A'}
                  </div>
                </div>
                <div style={{ ...card, cursor: 'default' }}>
                  <div style={{ fontSize: 11, color: '#999' }}>
                    Typical Credits
                  </div>
                  <div
                    style={{
                      fontSize: 16,
                      fontWeight: 700,
                      color: '#27ae60',
                    }}
                  >
                    {activityDetail.typical_credit_range?.min?.toLocaleString()}{' '}
                    -{' '}
                    {activityDetail.typical_credit_range?.max?.toLocaleString()}{' '}
                    {activityDetail.typical_credit_range?.unit}
                  </div>
                </div>
                <div style={{ ...card, cursor: 'default' }}>
                  <div style={{ fontSize: 11, color: '#999' }}>
                    CDM Tools Needed
                  </div>
                  <div
                    style={{
                      fontSize: 14,
                      fontWeight: 600,
                      color: '#1a1a2e',
                    }}
                  >
                    {activityDetail.cdm_tools_needed?.join(', ') || 'None'}
                  </div>
                </div>
              </div>

              {/* Regulatory notes */}
              {activityDetail.regulatory_notes && (
                <div
                  style={{
                    padding: 12,
                    background: '#eaf2f8',
                    borderRadius: 8,
                    fontSize: 13,
                    color: '#2c3e50',
                    marginBottom: 20,
                    borderLeft: '4px solid #3498db',
                  }}
                >
                  {activityDetail.regulatory_notes}
                </div>
              )}

              {/* Input fields */}
              {(activityDetail.inputs_guide || []).map((ig) => (
                <InputHelper
                  key={ig.parameter}
                  parameter={ig.parameter}
                  label={ig.label}
                  description={ig.description}
                  unit={ig.unit}
                  typicalRange={ig.typical_range}
                  exampleValue={ig.example_value}
                  dataSources={ig.data_sources}
                  required={ig.required}
                  tooltip={ig.tooltip}
                  value={inputValues[ig.parameter]}
                  onChange={handleInputChange}
                />
              ))}

              {/* Real world examples */}
              {activityDetail.real_world_examples?.length > 0 && (
                <div style={{ marginTop: 16, marginBottom: 16 }}>
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color: '#1a1a2e',
                      marginBottom: 8,
                    }}
                  >
                    Real-World Examples
                  </div>
                  {activityDetail.real_world_examples.map((ex, i) => (
                    <div
                      key={i}
                      style={{
                        fontSize: 12,
                        color: '#555',
                        padding: '4px 0',
                      }}
                    >
                      {ex.project} - {ex.credits?.toLocaleString()} tCO2e (
                      {ex.year})
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
                <button style={btnOutline} onClick={() => setStep(3)}>
                  Back
                </button>
                <button
                  style={btnPrimary}
                  onClick={() => {
                    handleCalculate();
                    setStep(5);
                  }}
                >
                  Calculate Carbon Credits
                </button>
              </div>
            </>
          ) : (
            <div style={{ color: '#e74c3c' }}>
              Failed to load activity detail.
            </div>
          )}
        </div>
      )}

      {/* ========== STEP 5: Results ========== */}
      {step === 5 && (
        <div>
          <div style={stepHeader}>Calculation Results</div>
          <p style={stepSub}>
            {activityDetail?.name || selectedActivity?.name} -{' '}
            {activityDetail?.recommended_methodology}
          </p>

          {calculating ? (
            <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>
              <div style={{ fontSize: 24, marginBottom: 12 }}>
                Calculating...
              </div>
              <div style={{ fontSize: 13 }}>
                Running methodology engine with CDM tool chain
              </div>
            </div>
          ) : calcResult ? (
            calcResult.error ? (
              <div
                style={{
                  padding: 20,
                  background: '#fdecea',
                  borderRadius: 8,
                  color: '#c0392b',
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: 8 }}>
                  Calculation Error
                </div>
                {calcResult.error}
              </div>
            ) : (
              <>
                {/* Key result */}
                <div
                  style={{
                    textAlign: 'center',
                    padding: 32,
                    background: 'linear-gradient(135deg, #e8f8f0, #eaf2f8)',
                    borderRadius: 12,
                    marginBottom: 24,
                  }}
                >
                  <div style={{ fontSize: 13, color: '#666', marginBottom: 8 }}>
                    Estimated Emission Reductions
                  </div>
                  <div
                    style={{
                      fontSize: 48,
                      fontWeight: 800,
                      color: '#27ae60',
                    }}
                  >
                    {(
                      calcResult.emission_reductions ||
                      calcResult.net_emission_reductions ||
                      0
                    ).toLocaleString()}
                  </div>
                  <div style={{ fontSize: 16, color: '#666' }}>
                    tCO2e per year
                  </div>
                </div>

                {/* Detailed breakdown */}
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                    gap: 12,
                    marginBottom: 24,
                  }}
                >
                  {[
                    {
                      label: 'Methodology',
                      value: calcResult.methodology,
                      color: '#3498db',
                    },
                    {
                      label: 'Baseline Emissions',
                      value: calcResult.baseline_emissions?.toLocaleString(),
                      unit: 'tCO2e',
                      color: '#e74c3c',
                    },
                    {
                      label: 'Project Emissions',
                      value: calcResult.project_emissions?.toLocaleString(),
                      unit: 'tCO2e',
                      color: '#e67e22',
                    },
                    {
                      label: 'Leakage',
                      value: calcResult.leakage?.toLocaleString(),
                      unit: 'tCO2e',
                      color: '#f39c12',
                    },
                  ]
                    .filter((item) => item.value !== undefined)
                    .map((item) => (
                      <div
                        key={item.label}
                        style={{ ...card, cursor: 'default' }}
                      >
                        <div style={{ fontSize: 11, color: '#999' }}>
                          {item.label}
                        </div>
                        <div
                          style={{
                            fontSize: 18,
                            fontWeight: 700,
                            color: item.color,
                          }}
                        >
                          {item.value} {item.unit || ''}
                        </div>
                      </div>
                    ))}
                </div>

                {/* CDM Tools used */}
                {calcResult.cdm_tools_used && (
                  <div style={{ marginBottom: 20 }}>
                    <div
                      style={{
                        fontSize: 14,
                        fontWeight: 600,
                        color: '#1a1a2e',
                        marginBottom: 8,
                      }}
                    >
                      CDM Tools Used
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {calcResult.cdm_tools_used.map((t) => (
                        <span
                          key={t}
                          style={{
                            padding: '4px 10px',
                            background: '#eaf2f8',
                            borderRadius: 4,
                            fontSize: 12,
                            color: '#3498db',
                            fontWeight: 500,
                          }}
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Grid EF source */}
                {calcResult.grid_ef_source && (
                  <div
                    style={{
                      fontSize: 12,
                      color: '#27ae60',
                      padding: 8,
                      background: '#e8f8f0',
                      borderRadius: 6,
                      marginBottom: 16,
                    }}
                  >
                    Grid emission factor: {calcResult.grid_ef_source}
                  </div>
                )}

                {/* Full result JSON toggle */}
                <details style={{ marginTop: 16 }}>
                  <summary
                    style={{
                      cursor: 'pointer',
                      fontSize: 13,
                      color: '#3498db',
                    }}
                  >
                    View full calculation output
                  </summary>
                  <pre
                    style={{
                      background: '#f8f9fa',
                      padding: 16,
                      borderRadius: 8,
                      fontSize: 12,
                      overflow: 'auto',
                      maxHeight: 300,
                    }}
                  >
                    {JSON.stringify(calcResult, null, 2)}
                  </pre>
                </details>
              </>
            )
          ) : (
            <div style={{ color: '#999', padding: 40, textAlign: 'center' }}>
              No results yet. Click Calculate to start.
            </div>
          )}

          <div style={{ display: 'flex', gap: 12, marginTop: 24 }}>
            <button style={btnOutline} onClick={() => setStep(4)}>
              Back to Inputs
            </button>
            <button
              style={btnOutline}
              onClick={() => {
                setStep(1);
                setCalcResult(null);
                setSelectedActivity(null);
                setActivityDetail(null);
                setInputValues({});
              }}
            >
              Start Over
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActivityGuide;
