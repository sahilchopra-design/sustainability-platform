/**
 * PersonaTemplatesPage.jsx
 * ─────────────────────────────────────────────────────────────────────────────
 * Three-tab page:
 *   1. Download Templates  — per-module CSV / JSON pre-filled with persona seeds
 *   2. Bulk Upload         — drag-and-drop CSV → parse → preview → apply
 *   3. Lineage Map         — Persona × Module × DB table × API endpoint matrix
 */

import React, { useState, useRef, useCallback } from 'react';
import {
  Download, Upload, GitBranch, FileText, FileSpreadsheet,
  Database, Layers, CheckCircle, AlertCircle, X, ChevronRight,
  Search, Filter, Table2, ArrowRight, Info, RefreshCw,
} from 'lucide-react';
import {
  MODULE_SCHEMAS,
  downloadCsvTemplate,
  downloadJsonTemplate,
  parseCsvUpload,
} from '../../../data/templateUtils';
import {
  MODULE_REGISTRY,
  getPersonaModuleMatrix,
  getDbTableIndex,
  getPersonaLineage,
  CATEGORY_COLOURS,
} from '../../../data/personaLineageMap';

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const TABS = [
  { id: 'download',  label: 'Download Templates', icon: Download },
  { id: 'upload',    label: 'Bulk Upload',         icon: Upload },
  { id: 'lineage',   label: 'Lineage Map',         icon: GitBranch },
];

const CATEGORY_BG = {
  Analytics:  'bg-blue-900/40 text-blue-300 border-blue-700/40',
  Risk:       'bg-red-900/40 text-red-300 border-red-700/40',
  Emissions:  'bg-orange-900/40 text-orange-300 border-orange-700/40',
  Regulatory: 'bg-purple-900/40 text-purple-300 border-purple-700/40',
  Nature:     'bg-green-900/40 text-green-300 border-green-700/40',
  Energy:     'bg-yellow-900/40 text-yellow-300 border-yellow-700/40',
  ESG:        'bg-emerald-900/40 text-emerald-300 border-emerald-700/40',
  Other:      'bg-gray-700/60 text-gray-300 border-gray-600/40',
};

function catBadge(category) {
  const cls = CATEGORY_BG[category] || CATEGORY_BG.Other;
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${cls}`}>
      {category}
    </span>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 1: Download Templates
// ─────────────────────────────────────────────────────────────────────────────

const ALL_SCHEMA_CATEGORIES = [...new Set(
  Object.keys(MODULE_SCHEMAS).map(k => {
    const reg = MODULE_REGISTRY[k];
    return reg ? reg.category : 'Other';
  })
)];

function DownloadTemplatesTab() {
  const [search, setSearch] = useState('');
  const [filterCat, setFilterCat] = useState('All');
  const [downloading, setDownloading] = useState({});

  const handleDownload = async (moduleKey, format) => {
    const key = `${moduleKey}-${format}`;
    setDownloading(p => ({ ...p, [key]: true }));
    try {
      if (format === 'csv') downloadCsvTemplate(moduleKey);
      else downloadJsonTemplate(moduleKey);
    } finally {
      setTimeout(() => setDownloading(p => ({ ...p, [key]: false })), 600);
    }
  };

  const filtered = Object.entries(MODULE_SCHEMAS).filter(([key, schema]) => {
    const reg = MODULE_REGISTRY[key];
    const cat = reg ? reg.category : 'Other';
    const matchSearch = !search ||
      schema.label.toLowerCase().includes(search.toLowerCase()) ||
      key.includes(search.toLowerCase());
    const matchCat = filterCat === 'All' || cat === filterCat;
    return matchSearch && matchCat;
  });

  const categories = ['All', ...ALL_SCHEMA_CATEGORIES];

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search modules…"
            className="w-full pl-9 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-emerald-500"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {categories.map(c => (
            <button
              key={c}
              onClick={() => setFilterCat(c)}
              className={`text-xs px-3 py-1.5 rounded-full border font-medium transition-all ${
                filterCat === c
                  ? 'bg-emerald-600 border-emerald-500 text-white'
                  : 'bg-gray-800 border-gray-600 text-gray-400 hover:border-gray-400'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Info banner */}
      <div className="flex items-start gap-3 bg-blue-950/40 border border-blue-800/40 rounded-lg p-4 text-sm text-blue-300">
        <Info className="h-4 w-4 mt-0.5 flex-shrink-0" />
        <span>
          Templates are pre-filled with seed data for every persona that uses each module.
          Download CSV to bulk-upload via the <strong>Bulk Upload</strong> tab, or JSON for
          API-driven ingestion. Each template includes a comment row explaining field constraints.
        </span>
      </div>

      {/* Module grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered.map(([key, schema]) => {
          const reg = MODULE_REGISTRY[key];
          const cat = reg ? reg.category : 'Other';
          const dlCsv = downloading[`${key}-csv`];
          const dlJson = downloading[`${key}-json`];

          return (
            <div key={key} className="bg-gray-800 border border-gray-700 rounded-xl p-5 flex flex-col gap-3 hover:border-gray-600 transition-colors">
              {/* Header */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-100 text-sm leading-tight">{schema.label}</h3>
                  <p className="text-xs text-gray-400 mt-1 line-clamp-2">{schema.description}</p>
                </div>
                {catBadge(cat)}
              </div>

              {/* Stats row */}
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-gray-900/60 rounded-lg py-2">
                  <div className="text-sm font-bold text-emerald-400">{schema.fields.length}</div>
                  <div className="text-[10px] text-gray-500">Fields</div>
                </div>
                <div className="bg-gray-900/60 rounded-lg py-2">
                  <div className="text-sm font-bold text-blue-400">{schema.dbTables.length}</div>
                  <div className="text-[10px] text-gray-500">DB Tables</div>
                </div>
                <div className="bg-gray-900/60 rounded-lg py-2">
                  <div className="text-xs font-bold text-purple-400 truncate px-1">{schema.migration}</div>
                  <div className="text-[10px] text-gray-500">Migration</div>
                </div>
              </div>

              {/* DB tables */}
              <div className="flex flex-wrap gap-1">
                {schema.dbTables.map(t => (
                  <span key={t} className="text-[10px] bg-gray-900 border border-gray-700 text-gray-400 px-2 py-0.5 rounded-full font-mono">
                    {t}
                  </span>
                ))}
              </div>

              {/* API endpoint */}
              <div className="text-[10px] font-mono text-gray-500 bg-gray-900/60 rounded px-2 py-1 truncate">
                {schema.apiEndpoint}
              </div>

              {/* Download buttons */}
              <div className="flex gap-2 mt-auto pt-1">
                <button
                  onClick={() => handleDownload(key, 'csv')}
                  disabled={dlCsv}
                  className="flex-1 flex items-center justify-center gap-2 text-xs font-medium bg-emerald-800/50 hover:bg-emerald-700/60 border border-emerald-700/60 text-emerald-300 rounded-lg py-2 transition-all disabled:opacity-60"
                >
                  {dlCsv
                    ? <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    : <FileSpreadsheet className="h-3.5 w-3.5" />}
                  CSV
                </button>
                <button
                  onClick={() => handleDownload(key, 'json')}
                  disabled={dlJson}
                  className="flex-1 flex items-center justify-center gap-2 text-xs font-medium bg-blue-800/50 hover:bg-blue-700/60 border border-blue-700/60 text-blue-300 rounded-lg py-2 transition-all disabled:opacity-60"
                >
                  {dlJson
                    ? <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    : <FileText className="h-3.5 w-3.5" />}
                  JSON
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-16 text-gray-500 text-sm">
          No modules match your filter. Try clearing the search or category.
        </div>
      )}

      {/* Summary footer */}
      <div className="text-xs text-gray-600 border-t border-gray-800 pt-4">
        Showing {filtered.length} of {Object.keys(MODULE_SCHEMAS).length} module templates ·
        Total fields across all modules: {Object.values(MODULE_SCHEMAS).reduce((s, m) => s + m.fields.length, 0)}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 2: Bulk Upload
// ─────────────────────────────────────────────────────────────────────────────

function BulkUploadTab() {
  const [selectedModule, setSelectedModule] = useState('climate_risk');
  const [dragOver, setDragOver] = useState(false);
  const [parseResult, setParseResult] = useState(null);   // { headers, rows, errors }
  const [fileName, setFileName] = useState(null);
  const fileRef = useRef();

  const schema = MODULE_SCHEMAS[selectedModule];

  const processFile = useCallback((file) => {
    setFileName(file.name);
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const result = parseCsvUpload(text);
      setParseResult(result);
    };
    reader.readAsText(file);
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.csv')) processFile(file);
  }, [processFile]);

  const onFileChange = (e) => {
    const file = e.target.files[0];
    if (file) processFile(file);
  };

  const clearUpload = () => {
    setParseResult(null);
    setFileName(null);
    if (fileRef.current) fileRef.current.value = '';
  };

  const expectedHeaders = schema ? schema.fields.map(f => f.key) : [];

  return (
    <div className="space-y-6">
      {/* Module selector */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold text-gray-200">1. Select target module</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
          {Object.entries(MODULE_SCHEMAS).map(([key, s]) => (
            <button
              key={key}
              onClick={() => { setSelectedModule(key); clearUpload(); }}
              className={`text-left text-xs px-3 py-2 rounded-lg border transition-all ${
                selectedModule === key
                  ? 'bg-emerald-700/40 border-emerald-500 text-emerald-300'
                  : 'bg-gray-900/60 border-gray-700 text-gray-400 hover:border-gray-500'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
        {schema && (
          <div className="text-xs text-gray-500 flex gap-4">
            <span className="flex items-center gap-1">
              <Database className="h-3 w-3" /> {schema.dbTables.join(', ')}
            </span>
            <span>API: <code className="text-gray-400">{schema.apiEndpoint}</code></span>
          </div>
        )}
      </div>

      {/* Expected schema */}
      {schema && (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 space-y-3">
          <h3 className="text-sm font-semibold text-gray-200">2. Expected CSV schema — {schema.label}</h3>
          <div className="overflow-x-auto">
            <table className="text-xs w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left pb-2 text-gray-400 font-medium pr-4">Column Key</th>
                  <th className="text-left pb-2 text-gray-400 font-medium pr-4">Label</th>
                  <th className="text-left pb-2 text-gray-400 font-medium pr-4">Type</th>
                  <th className="text-left pb-2 text-gray-400 font-medium">Default / Options</th>
                </tr>
              </thead>
              <tbody>
                {schema.fields.map(f => (
                  <tr key={f.key} className="border-b border-gray-800 hover:bg-gray-900/30">
                    <td className="py-1.5 pr-4 font-mono text-emerald-400">{f.key}</td>
                    <td className="py-1.5 pr-4 text-gray-300">{f.label}</td>
                    <td className="py-1.5 pr-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        f.type === 'enum'    ? 'bg-purple-900/50 text-purple-300' :
                        f.type === 'number'  ? 'bg-blue-900/50 text-blue-300' :
                        f.type === 'boolean' ? 'bg-yellow-900/50 text-yellow-300' :
                                               'bg-gray-700 text-gray-300'
                      }`}>{f.type}</span>
                    </td>
                    <td className="py-1.5 text-gray-500">
                      {f.options ? f.options.join(' | ') : (f.default || '—')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex gap-2 pt-1">
            <button
              onClick={() => downloadCsvTemplate(selectedModule)}
              className="text-xs flex items-center gap-1.5 bg-emerald-800/40 hover:bg-emerald-700/50 border border-emerald-700/50 text-emerald-300 px-3 py-1.5 rounded-lg transition-all"
            >
              <FileSpreadsheet className="h-3.5 w-3.5" /> Download template CSV
            </button>
            <button
              onClick={() => downloadJsonTemplate(selectedModule)}
              className="text-xs flex items-center gap-1.5 bg-blue-800/40 hover:bg-blue-700/50 border border-blue-700/50 text-blue-300 px-3 py-1.5 rounded-lg transition-all"
            >
              <FileText className="h-3.5 w-3.5" /> Download template JSON
            </button>
          </div>
        </div>
      )}

      {/* Drop zone */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold text-gray-200">3. Upload filled CSV</h3>

        {!parseResult ? (
          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
            onClick={() => fileRef.current?.click()}
            className={`relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
              dragOver
                ? 'border-emerald-500 bg-emerald-950/30'
                : 'border-gray-600 hover:border-gray-500 hover:bg-gray-900/40'
            }`}
          >
            <Upload className="h-8 w-8 mx-auto text-gray-500 mb-3" />
            <p className="text-sm font-medium text-gray-300">Drop your CSV here or click to browse</p>
            <p className="text-xs text-gray-500 mt-1">Accepts .csv files · Max 5 MB</p>
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              onChange={onFileChange}
              className="hidden"
            />
          </div>
        ) : (
          <div className="space-y-4">
            {/* File badge */}
            <div className="flex items-center justify-between bg-gray-900/60 rounded-lg px-4 py-3">
              <div className="flex items-center gap-3">
                <FileSpreadsheet className="h-5 w-5 text-emerald-400" />
                <div>
                  <div className="text-sm font-medium text-gray-200">{fileName}</div>
                  <div className="text-xs text-gray-500">
                    {parseResult.rows.length} data rows · {parseResult.headers.length} columns
                    {parseResult.errors.length > 0 && (
                      <span className="ml-2 text-red-400">{parseResult.errors.length} error(s)</span>
                    )}
                  </div>
                </div>
              </div>
              <button onClick={clearUpload} className="text-gray-500 hover:text-gray-300">
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Column mapping check */}
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Column Mapping</h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                {expectedHeaders.map(h => {
                  const found = parseResult.headers.includes(h);
                  return (
                    <div key={h} className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded ${
                      found ? 'bg-emerald-950/40 text-emerald-400' : 'bg-red-950/40 text-red-400'
                    }`}>
                      {found
                        ? <CheckCircle className="h-3 w-3 flex-shrink-0" />
                        : <AlertCircle className="h-3 w-3 flex-shrink-0" />}
                      <span className="font-mono truncate">{h}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Parse errors */}
            {parseResult.errors.length > 0 && (
              <div className="bg-red-950/30 border border-red-800/40 rounded-lg p-3 space-y-1">
                <div className="text-xs font-semibold text-red-400 flex items-center gap-2">
                  <AlertCircle className="h-3.5 w-3.5" /> Parse warnings
                </div>
                {parseResult.errors.map((e, i) => (
                  <div key={i} className="text-xs text-red-300 ml-5">{e}</div>
                ))}
              </div>
            )}

            {/* Data preview */}
            {parseResult.rows.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                  Data Preview (first {Math.min(10, parseResult.rows.length)} rows)
                </h4>
                <div className="overflow-x-auto rounded-lg border border-gray-700">
                  <table className="text-xs w-full">
                    <thead className="bg-gray-900/80">
                      <tr>
                        <th className="px-3 py-2 text-left text-gray-500 font-medium">#</th>
                        {parseResult.headers.map(h => (
                          <th key={h} className="px-3 py-2 text-left text-gray-400 font-medium font-mono whitespace-nowrap">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {parseResult.rows.slice(0, 10).map((row, i) => (
                        <tr key={i} className={i % 2 === 0 ? 'bg-gray-800' : 'bg-gray-800/50'}>
                          <td className="px-3 py-1.5 text-gray-600">{i + 1}</td>
                          {parseResult.headers.map(h => (
                            <td key={h} className="px-3 py-1.5 text-gray-300 whitespace-nowrap max-w-[180px] truncate">
                              {row[h] ?? ''}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Apply button */}
                <div className="flex items-center gap-3 pt-2">
                  <button className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-all">
                    <CheckCircle className="h-4 w-4" />
                    Apply {parseResult.rows.length} rows to {schema?.label}
                  </button>
                  <span className="text-xs text-gray-500">
                    Data will be staged in persona context — no DB write in demo mode.
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab 3: Lineage Map
// ─────────────────────────────────────────────────────────────────────────────

const LINEAGE_VIEWS = ['Matrix', 'DB Tables', 'Persona Chain'];

function LineageTab() {
  const [view, setView] = useState('Matrix');
  const [selectedPersona, setSelectedPersona] = useState(null);
  const [searchTbl, setSearchTbl] = useState('');

  const matrix    = getPersonaModuleMatrix();
  const dbIndex   = getDbTableIndex();
  const allModKeys = Object.keys(MODULE_REGISTRY);
  const rawLineage = selectedPersona ? getPersonaLineage(selectedPersona) : null;
  // getPersonaLineage returns { persona, moduleChains }
  const personaLineage = rawLineage
    ? { ...rawLineage.persona, modules: rawLineage.moduleChains }
    : null;

  return (
    <div className="space-y-5">
      {/* View switcher */}
      <div className="flex gap-2 border-b border-gray-700 pb-4">
        {LINEAGE_VIEWS.map(v => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`text-sm px-4 py-2 rounded-lg font-medium transition-all ${
              view === v
                ? 'bg-emerald-700/50 text-emerald-300 border border-emerald-600/50'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
            }`}
          >
            {v}
          </button>
        ))}
      </div>

      {/* ── MATRIX VIEW ── */}
      {view === 'Matrix' && (
        <div className="space-y-4">
          <p className="text-xs text-gray-500">
            Each row is a persona. Coloured cells indicate the persona uses that module.
            Hover a cell to see the module category. {matrix.length} personas × {allModKeys.length} modules.
          </p>
          <div className="overflow-x-auto rounded-xl border border-gray-700">
            <table className="text-[11px] w-full">
              <thead className="bg-gray-900 sticky top-0">
                <tr>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium whitespace-nowrap min-w-[200px] border-r border-gray-700">
                    Persona
                  </th>
                  {allModKeys.map(k => {
                    const reg = MODULE_REGISTRY[k];
                    const colObj = CATEGORY_COLOURS?.[reg?.category];
                    const colCls = colObj?.text || 'text-gray-400';
                    return (
                      <th
                        key={k}
                        className="px-2 py-3 text-center font-medium border-r border-gray-800 last:border-0"
                        title={reg?.label || k}
                      >
                        <div className={colCls} style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', whiteSpace: 'nowrap', maxHeight: 90, overflow: 'hidden', fontSize: 10 }}>
                          {reg?.label?.replace(/\s/g, '\u00A0') || k}
                        </div>
                      </th>
                    );
                  })}
                  <th className="px-3 py-3 text-gray-400 font-medium text-center whitespace-nowrap">
                    Total
                  </th>
                </tr>
              </thead>
              <tbody>
                {matrix.map((p, i) => {
                  const activeSet = new Set(p.activeModules);
                  return (
                    <tr key={p.personaId} className={i % 2 === 0 ? 'bg-gray-800' : 'bg-gray-800/40'}>
                      <td className="px-4 py-2 border-r border-gray-700 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className="text-base">{p.logo}</span>
                          <div>
                            <div className="font-medium text-gray-200 text-[11px] leading-tight">{p.personaName}</div>
                            <div className="text-[9px] text-gray-500">{p.institution}</div>
                          </div>
                        </div>
                      </td>
                      {allModKeys.map(k => {
                        const reg = MODULE_REGISTRY[k];
                        const active = activeSet.has(k);
                        const catKey = reg?.category || 'Other';
                        const dotColour =
                          catKey === 'Analytics'  ? 'bg-blue-500' :
                          catKey === 'Risk'        ? 'bg-red-500' :
                          catKey === 'Emissions'   ? 'bg-orange-500' :
                          catKey === 'Regulatory'  ? 'bg-purple-500' :
                          catKey === 'Nature'      ? 'bg-green-500' :
                          catKey === 'Energy'      ? 'bg-yellow-500' :
                          catKey === 'ESG'         ? 'bg-emerald-500' :
                                                     'bg-gray-500';
                        return (
                          <td
                            key={k}
                            className="px-1 py-2 text-center border-r border-gray-800 last:border-0"
                            title={active ? `${p.personaName} uses ${reg?.label || k}` : `Not used`}
                          >
                            {active && (
                              <div className={`h-2.5 w-2.5 rounded-full mx-auto ${dotColour} opacity-90`} />
                            )}
                          </td>
                        );
                      })}
                      <td className="px-3 py-2 text-center">
                        <span className="text-[11px] font-bold text-emerald-400">{p.moduleCount}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Legend */}
          <div className="flex flex-wrap gap-3 text-[10px] text-gray-500">
            {Object.entries({
              Analytics: 'bg-blue-500', Risk: 'bg-red-500', Emissions: 'bg-orange-500',
              Regulatory: 'bg-purple-500', Nature: 'bg-green-500', Energy: 'bg-yellow-500',
              ESG: 'bg-emerald-500',
            }).map(([label, cls]) => (
              <span key={label} className="flex items-center gap-1.5">
                <span className={`h-2 w-2 rounded-full ${cls}`} />
                {label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ── DB TABLES VIEW ── */}
      {view === 'DB Tables' && (
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" />
              <input
                value={searchTbl}
                onChange={e => setSearchTbl(e.target.value)}
                placeholder="Filter tables…"
                className="w-full pl-8 pr-4 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-emerald-500"
              />
            </div>
            <span className="text-xs text-gray-500">{dbIndex.length} tables total</span>
          </div>

          <div className="overflow-x-auto rounded-xl border border-gray-700">
            <table className="text-xs w-full">
              <thead className="bg-gray-900">
                <tr>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">DB Table</th>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Migration</th>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Category</th>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Modules</th>
                  <th className="text-left px-4 py-3 text-gray-400 font-medium">Personas</th>
                </tr>
              </thead>
              <tbody>
                {dbIndex
                  .filter(row => !searchTbl || row.table.includes(searchTbl.toLowerCase()))
                  .map((row, i) => (
                    <tr key={row.table} className={i % 2 === 0 ? 'bg-gray-800' : 'bg-gray-800/40'}>
                      <td className="px-4 py-2.5 font-mono text-emerald-400 whitespace-nowrap">{row.table}</td>
                      <td className="px-4 py-2.5 text-gray-400 whitespace-nowrap">{row.migration}</td>
                      <td className="px-4 py-2.5">
                        {catBadge(row.category)}
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex flex-wrap gap-1">
                          {row.modules.map(m => (
                            <span key={m} className="text-[10px] bg-gray-900 border border-gray-700 text-gray-400 px-2 py-0.5 rounded-full">
                              {MODULE_REGISTRY[m]?.label || m}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-gray-400">{row.personas.length} persona(s)</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── PERSONA CHAIN VIEW ── */}
      {view === 'Persona Chain' && (
        <div className="space-y-5">
          {/* Persona selector */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {matrix.map(p => (
              <button
                key={p.personaId}
                onClick={() => setSelectedPersona(p.personaId)}
                className={`text-left text-xs px-3 py-2.5 rounded-xl border transition-all ${
                  selectedPersona === p.personaId
                    ? 'bg-emerald-700/40 border-emerald-500 text-emerald-300'
                    : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-500'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span>{p.logo}</span>
                  <div className="min-w-0">
                    <div className="font-semibold text-[11px] truncate">{(p.personaName || p.personaId).split(',')[0]}</div>
                    <div className="text-[9px] text-gray-500 truncate">{p.institution}</div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          {/* Lineage chain */}
          {personaLineage && (
            <div className="space-y-4">
              {/* Persona header */}
              <div className="bg-gray-800 border border-gray-700 rounded-xl p-5">
                <div className="flex items-center gap-4">
                  <span className="text-3xl">{personaLineage.logo}</span>
                  <div>
                    <h3 className="text-base font-bold text-gray-100">{personaLineage.name}</h3>
                    <p className="text-sm text-gray-400">{personaLineage.institution}</p>
                    <p className="text-xs text-gray-500 mt-0.5 italic">{personaLineage.tagline}</p>
                  </div>
                  <div className="ml-auto text-center">
                    <div className="text-2xl font-bold text-emerald-400">{personaLineage.modules.length}</div>
                    <div className="text-xs text-gray-500">Active Modules</div>
                  </div>
                </div>
              </div>

              {/* Module lineage cards */}
              <div className="space-y-3">
                {personaLineage.modules.map((mod, idx) => (
                  <div key={mod.moduleKey} className="bg-gray-800 border border-gray-700 rounded-xl overflow-hidden">
                    {/* Module header */}
                    <div className="flex items-center gap-3 px-5 py-3 bg-gray-900/60 border-b border-gray-700">
                      <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-900/60 text-emerald-400 text-xs font-bold">
                        {idx + 1}
                      </div>
                      <div className="flex-1">
                        <span className="font-semibold text-sm text-gray-200">{mod.moduleLabel}</span>
                      </div>
                      {catBadge(mod.category)}
                    </div>

                    {/* Lineage chain */}
                    <div className="flex items-start gap-0 overflow-x-auto p-4">
                      {/* Fields */}
                      <div className="flex-shrink-0 min-w-[150px]">
                        <div className="text-[10px] text-gray-500 uppercase font-semibold mb-2">Input Fields</div>
                        <div className="space-y-1">
                          {(mod.sampleFields || []).slice(0, 5).map(f => (
                            <div key={f} className="text-[10px] font-mono text-gray-400 bg-gray-900/60 px-2 py-0.5 rounded">{f}</div>
                          ))}
                          {(mod.sampleFields || []).length > 5 && (
                            <div className="text-[10px] text-gray-600">+{mod.sampleFields.length - 5} more</div>
                          )}
                        </div>
                      </div>

                      <ArrowRight className="flex-shrink-0 h-4 w-4 text-gray-600 mx-3 mt-5" />

                      {/* API */}
                      <div className="flex-shrink-0 min-w-[180px]">
                        <div className="text-[10px] text-gray-500 uppercase font-semibold mb-2">API Endpoint</div>
                        <div className="text-[10px] font-mono text-blue-400 bg-blue-950/30 border border-blue-900/40 px-2 py-1 rounded">
                          POST {mod.apiEndpoint}
                        </div>
                        <div className="text-[10px] text-gray-500 mt-1">
                          Route: <span className="text-gray-400">{mod.route}</span>
                        </div>
                      </div>

                      <ArrowRight className="flex-shrink-0 h-4 w-4 text-gray-600 mx-3 mt-5" />

                      {/* DB Tables */}
                      <div className="flex-shrink-0 min-w-[200px]">
                        <div className="text-[10px] text-gray-500 uppercase font-semibold mb-2">DB Tables</div>
                        <div className="space-y-1">
                          {mod.dbTables.map(t => (
                            <div key={t} className="flex items-center gap-1.5 text-[10px]">
                              <Database className="h-3 w-3 text-emerald-600 flex-shrink-0" />
                              <span className="font-mono text-emerald-400">{t}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <ArrowRight className="flex-shrink-0 h-4 w-4 text-gray-600 mx-3 mt-5" />

                      {/* Migration */}
                      <div className="flex-shrink-0">
                        <div className="text-[10px] text-gray-500 uppercase font-semibold mb-2">Migration</div>
                        <div className="text-[10px] font-mono text-purple-400 bg-purple-950/30 border border-purple-900/40 px-2 py-1 rounded">
                          {mod.migration}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!selectedPersona && (
            <div className="text-center py-16 text-gray-500 text-sm">
              Select a persona above to see their full module → API → DB lineage chain.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

export default function PersonaTemplatesPage() {
  const [activeTab, setActiveTab] = useState('download');

  return (
    <div className="p-6 bg-gray-900 min-h-screen text-gray-100 space-y-6">
      {/* Page header */}
      <div className="border-b border-gray-800 pb-5">
        <div className="flex items-center gap-3 mb-2">
          <div className="h-9 w-9 rounded-xl bg-emerald-900/60 flex items-center justify-center">
            <Layers className="h-5 w-5 text-emerald-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-100">Persona & Module Templates</h1>
            <p className="text-sm text-gray-400">
              Download pre-filled input templates · Bulk upload via CSV · Explore persona → module → DB lineage
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="flex flex-wrap gap-4 mt-4">
          {[
            { label: 'Personas', value: getPersonaModuleMatrix().length, colour: 'text-blue-400' },
            { label: 'Modules with templates', value: Object.keys(MODULE_SCHEMAS).length, colour: 'text-emerald-400' },
            { label: 'Total modules in registry', value: Object.keys(MODULE_REGISTRY).length, colour: 'text-purple-400' },
            { label: 'DB tables mapped', value: getDbTableIndex().length, colour: 'text-orange-400' },
          ].map(s => (
            <div key={s.label} className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 flex items-center gap-2">
              <span className={`text-lg font-bold ${s.colour}`}>{s.value}</span>
              <span className="text-xs text-gray-500">{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-gray-800 rounded-xl p-1 w-fit">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 text-sm font-medium px-5 py-2.5 rounded-lg transition-all ${
              activeTab === id
                ? 'bg-emerald-700 text-white shadow-sm'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'download' && <DownloadTemplatesTab />}
        {activeTab === 'upload'   && <BulkUploadTab />}
        {activeTab === 'lineage'  && <LineageTab />}
      </div>
    </div>
  );
}
