/**
 * InputHelper Component
 * Reusable component for each input parameter in the Activity Guide.
 * Shows label, description, unit, range indicator, data source popover,
 * and validates input against typical range.
 */

import React, { useState, useRef } from 'react';

const InputHelper = ({
  parameter,
  label,
  description,
  unit = '',
  typicalRange,
  exampleValue,
  dataSources = [],
  required = true,
  tooltip = '',
  value,
  onChange,
}) => {
  const [showSources, setShowSources] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const sourceRef = useRef(null);

  const isOutOfRange =
    value !== '' &&
    value !== undefined &&
    typicalRange &&
    (Number(value) < typicalRange.min || Number(value) > typicalRange.max);

  const rangePercent =
    typicalRange && value !== '' && value !== undefined
      ? Math.min(
          100,
          Math.max(
            0,
            ((Number(value) - typicalRange.min) /
              (typicalRange.max - typicalRange.min)) *
              100
          )
        )
      : null;

  return (
    <div
      style={{
        marginBottom: 16,
        padding: 16,
        background: '#f8f9fa',
        borderRadius: 8,
        border: isOutOfRange ? '1px solid #e74c3c' : '1px solid #e0e0e0',
      }}
    >
      {/* Label row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 6,
        }}
      >
        <label
          style={{
            fontWeight: 600,
            fontSize: 14,
            color: '#1a1a2e',
          }}
        >
          {label}
          {required && (
            <span style={{ color: '#e74c3c', marginLeft: 4 }}>*</span>
          )}
          {unit && (
            <span
              style={{
                fontWeight: 400,
                fontSize: 12,
                color: '#666',
                marginLeft: 8,
              }}
            >
              ({unit})
            </span>
          )}
        </label>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {/* Tooltip icon */}
          {tooltip && (
            <div
              style={{ position: 'relative' }}
              onMouseEnter={() => setShowTooltip(true)}
              onMouseLeave={() => setShowTooltip(false)}
            >
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 20,
                  height: 20,
                  borderRadius: '50%',
                  background: '#3498db',
                  color: '#111',
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: 'help',
                }}
              >
                i
              </span>
              {showTooltip && (
                <div
                  style={{
                    position: 'absolute',
                    right: 0,
                    top: 24,
                    width: 260,
                    padding: 10,
                    background: '#1a1a2e',
                    color: '#111',
                    borderRadius: 6,
                    fontSize: 12,
                    zIndex: 100,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                  }}
                >
                  {tooltip}
                </div>
              )}
            </div>
          )}

          {/* Data sources button */}
          {dataSources.length > 0 && (
            <div style={{ position: 'relative' }} ref={sourceRef}>
              <button
                type="button"
                onClick={() => setShowSources(!showSources)}
                style={{
                  padding: '2px 8px',
                  borderRadius: 4,
                  border: '1px solid #3498db',
                  background: showSources ? '#3498db' : 'transparent',
                  color: showSources ? '#fff' : '#3498db',
                  fontSize: 11,
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
              >
                Where to find
              </button>
              {showSources && (
                <div
                  style={{
                    position: 'absolute',
                    right: 0,
                    top: 28,
                    width: 300,
                    padding: 12,
                    background: '#fff',
                    borderRadius: 8,
                    border: '1px solid #e0e0e0',
                    zIndex: 100,
                    boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
                  }}
                >
                  <div
                    style={{
                      fontWeight: 600,
                      fontSize: 12,
                      color: '#1a1a2e',
                      marginBottom: 8,
                    }}
                  >
                    Data Sources
                  </div>
                  <ul
                    style={{
                      margin: 0,
                      padding: '0 0 0 16px',
                      fontSize: 12,
                      color: '#555',
                    }}
                  >
                    {dataSources.map((src, i) => (
                      <li key={i} style={{ marginBottom: 4 }}>
                        {src}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Description */}
      <p
        style={{
          margin: '0 0 8px 0',
          fontSize: 12,
          color: '#666',
          lineHeight: 1.4,
        }}
      >
        {description}
      </p>

      {/* Input + Use Default */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input
          type="number"
          value={value ?? ''}
          onChange={(e) => onChange(parameter, e.target.value)}
          placeholder={exampleValue !== undefined ? `e.g. ${exampleValue}` : ''}
          style={{
            flex: 1,
            padding: '8px 12px',
            borderRadius: 6,
            border: isOutOfRange
              ? '1px solid #e74c3c'
              : '1px solid #ccc',
            fontSize: 14,
            outline: 'none',
          }}
        />
        {exampleValue !== undefined && (
          <button
            type="button"
            onClick={() => onChange(parameter, exampleValue)}
            style={{
              padding: '8px 12px',
              borderRadius: 6,
              border: '1px solid #27ae60',
              background: '#e8f8f0',
              color: '#27ae60',
              fontSize: 12,
              cursor: 'pointer',
              fontWeight: 600,
              whiteSpace: 'nowrap',
            }}
          >
            Use Default
          </button>
        )}
      </div>

      {/* Range indicator */}
      {typicalRange && (
        <div style={{ marginTop: 8 }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: 11,
              color: '#999',
              marginBottom: 4,
            }}
          >
            <span>
              {typicalRange.min.toLocaleString()} {unit}
            </span>
            <span>
              {typicalRange.max.toLocaleString()} {unit}
            </span>
          </div>
          <div
            style={{
              height: 4,
              background: '#e0e0e0',
              borderRadius: 2,
              position: 'relative',
            }}
          >
            {rangePercent !== null && (
              <div
                style={{
                  position: 'absolute',
                  left: `${rangePercent}%`,
                  top: -3,
                  width: 10,
                  height: 10,
                  borderRadius: '50%',
                  background: isOutOfRange ? '#e74c3c' : '#3498db',
                  transform: 'translateX(-50%)',
                }}
              />
            )}
          </div>
        </div>
      )}

      {/* Out of range warning */}
      {isOutOfRange && (
        <div
          style={{
            marginTop: 6,
            fontSize: 11,
            color: '#e74c3c',
            fontWeight: 500,
          }}
        >
          Value is outside the typical range ({typicalRange.min.toLocaleString()}{' '}
          - {typicalRange.max.toLocaleString()} {unit}). Please verify.
        </div>
      )}
    </div>
  );
};

export default InputHelper;
