/**
 * EU Regulatory Compliance Hub
 * Tabbed interface for 4 EU regulatory engines:
 *   1. EU Taxonomy Alignment (Reg (EU) 2020/852)
 *   2. EUDR Compliance (Reg (EU) 2023/1115)
 *   3. CSDDD Due Diligence (Dir (EU) 2024/1760)
 *   4. Climate Transition Plan (TPT / GFANZ / IIGCC / CSDDD Art 22 / ESRS E1)
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import {
  Landmark, TreePine, Scale, ArrowUpRight, ChevronDown, ChevronRight,
  AlertTriangle, CheckCircle2, XCircle, Loader2, Info, Search,
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";

/* ── Palette ───────────────────────────────────────────────────────────────── */
const OBJ_COLORS = ['#10b981', '#06b6d4', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899'];
const RADAR_COLORS = ['#06b6d4', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'];
const PIE_COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

/* ── Shared UI ─────────────────────────────────────────────────────────────── */
function Card({ title, subtitle, badge, children, className = '' }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            {title && <h2 className="text-sm font-semibold text-gray-900">{title}</h2>}
            {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {badge && <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-700 border border-gray-200">{badge}</span>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}

function StatCard({ label, value, sub, color = 'text-gray-900' }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
      <p className="text-xs text-gray-500 font-medium mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 1 }) : value}</p>
      {sub && <p className="text-[11px] text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

function Badge({ label, color = 'bg-gray-50 text-gray-500' }) {
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>{label}</span>;
}

function Spinner() {
  return <div className="flex items-center justify-center py-16"><Loader2 className="w-7 h-7 text-gray-700 animate-spin" /></div>;
}

function Collapsible({ title, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-xl">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-5 py-3 text-xs font-semibold text-gray-700 hover:text-gray-900 transition">
        {title}
        {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      {open && <div className="px-5 pb-4">{children}</div>}
    </div>
  );
}

function TabPill({ tabs, active, onChange }) {
  return (
    <div className="inline-flex bg-[#f0f0f0] rounded-lg p-1 border border-gray-200 flex-wrap gap-0.5">
      {tabs.map(t => (
        <button key={t.id} onClick={() => onChange(t.id)}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${
            active === t.id ? 'bg-gray-100 text-gray-700 border border-gray-300' : 'text-gray-500 hover:text-gray-600'
          }`}>
          {t.icon}{t.label}
        </button>
      ))}
    </div>
  );
}

function InputField({ label, value, onChange, type = 'text', placeholder = '', className = '' }) {
  return (
    <div className={className}>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
        className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm bg-[#f5f6f8] text-gray-700 focus:outline-none focus:ring-1 focus:ring-black/50" />
    </div>
  );
}

function SelectField({ label, value, onChange, options, className = '' }) {
  return (
    <div className={className}>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      <select value={value} onChange={e => onChange(e.target.value)}
        className="w-full border border-gray-200 rounded px-2 py-1.5 text-sm bg-[#f5f6f8] text-gray-700 focus:outline-none">
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

function SubmitBtn({ onClick, loading, label }) {
  return (
    <button onClick={onClick} disabled={loading}
      className="bg-[#164E8A] hover:bg-[#12407A] disabled:opacity-50 text-[#ffffff] text-sm font-semibold px-8 py-2.5 rounded-lg shadow transition-colors flex items-center gap-2">
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}{label}
    </button>
  );
}

function ErrorBox({ message }) {
  if (!message) return null;
  return (
    <div className="flex items-start gap-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
      <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
      <p className="text-xs text-red-400">{message}</p>
    </div>
  );
}

const ratingBadge = (score) => {
  if (score >= 75) return <Badge label="Compliant" color="bg-emerald-500/10 text-emerald-400" />;
  if (score >= 50) return <Badge label="Partial" color="bg-amber-500/10 text-amber-400" />;
  return <Badge label="Non-Compliant" color="bg-red-500/10 text-red-400" />;
};

/* ═══════════════════════════════════════════════════════════════════════════
   TAB 1 — EU TAXONOMY ALIGNMENT
   ═══════════════════════════════════════════════════════════════════════════ */
function TaxonomyTab() {
  const [objectives, setObjectives] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Form state
  const [naceCode, setNaceCode] = useState('');
  const [activityName, setActivityName] = useState('');
  const [sector, setSector] = useState('');
  const [objective, setObjective] = useState('CCM');
  const [entityName, setEntityName] = useState('');
  const [reportingYear, setReportingYear] = useState('2025');
  const [turnover, setTurnover] = useState('');
  const [capex, setCapex] = useState('');
  const [opex, setOpex] = useState('');

  const fetchRef = useCallback(async () => {
    try {
      const [objRes, actRes] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/eu-taxonomy/ref/objectives`),
        axios.get(`${API_BASE}/api/v1/eu-taxonomy/ref/activities`),
      ]);
      setObjectives(objRes.data?.objectives || objRes.data || []);
      setActivities(actRes.data?.activities || actRes.data || []);
    } catch { /* reference data may not be available */ }
  }, []);

  useEffect(() => { fetchRef(); }, [fetchRef]);

  const filteredActivities = activities.filter(a =>
    (a.nace_code || a.code || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (a.activity_name || a.name || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const assessEntity = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/eu-taxonomy/assess-entity`, {
        entity_name: entityName || 'Demo Entity',
        reporting_year: parseInt(reportingYear),
        activities: [{ nace_code: naceCode, activity_name: activityName, sector, objective, sc_evidence: {}, dnsh_responses: {}, safeguards_data: {} }],
        total_turnover_eur: parseFloat(turnover) || 0,
        total_capex_eur: parseFloat(capex) || 0,
        total_opex_eur: parseFloat(opex) || 0,
      });
      setResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || err.message); }
    setLoading(false);
  };

  const objBreakdown = result?.objective_breakdown || result?.objectives_breakdown || [];
  const objData = Array.isArray(objBreakdown) ? objBreakdown : Object.entries(objBreakdown).map(([k, v]) => ({ objective: k, ...(typeof v === 'object' ? v : { alignment: v }) }));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="Regulation (EU) 2020/852" color="bg-emerald-400/10 text-emerald-400" />
        <Badge label="6 Environmental Objectives" color="bg-blue-400/10 text-blue-300" />
        <Badge label="GAR / BTAR Ratios" color="bg-purple-400/10 text-purple-300" />
      </div>

      <Collapsible title="Reference: Environmental Objectives & NACE Activities">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-4">
          {['CCM - Climate Change Mitigation', 'CCA - Climate Change Adaptation', 'WTR - Water & Marine Resources',
            'CE - Circular Economy', 'POL - Pollution Prevention', 'BIO - Biodiversity & Ecosystems'].map((o, i) => (
            <div key={i} className="p-2 rounded-lg text-xs text-gray-600" style={{ backgroundColor: `${OBJ_COLORS[i]}15` }}>{o}</div>
          ))}
        </div>
        {activities.length > 0 && (
          <div>
            <div className="relative mb-2">
              <Search className="absolute left-2 top-2 w-3.5 h-3.5 text-gray-500" />
              <input value={searchTerm} onChange={e => setSearchTerm(e.target.value)} placeholder="Search NACE activities..."
                className="w-full pl-7 pr-3 py-1.5 border border-gray-200 rounded text-xs bg-[#f5f6f8] text-gray-600 focus:outline-none" />
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1">
              {filteredActivities.slice(0, 30).map((a, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-gray-500 p-1.5 rounded hover:bg-gray-50 cursor-pointer"
                  onClick={() => { setNaceCode(a.nace_code || a.code || ''); setActivityName(a.activity_name || a.name || ''); setSector(a.sector || ''); }}>
                  <span className="font-mono text-gray-700">{a.nace_code || a.code}</span>
                  <span>{a.activity_name || a.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </Collapsible>

      <Card title="Entity Taxonomy Assessment" subtitle="Assess EU Taxonomy alignment for an entity across turnover, CapEx, and OpEx KPIs.">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <InputField label="Entity Name" value={entityName} onChange={setEntityName} placeholder="e.g. Acme Corp" />
          <InputField label="NACE Code" value={naceCode} onChange={setNaceCode} placeholder="e.g. D35.11" />
          <InputField label="Activity Name" value={activityName} onChange={setActivityName} placeholder="e.g. Electricity generation from wind" />
          <SelectField label="Primary Objective" value={objective} onChange={setObjective}
            options={[{ value: 'CCM', label: 'CCM - Climate Mitigation' }, { value: 'CCA', label: 'CCA - Climate Adaptation' }, { value: 'WTR', label: 'WTR - Water' }, { value: 'CE', label: 'CE - Circular Economy' }, { value: 'POL', label: 'POL - Pollution' }, { value: 'BIO', label: 'BIO - Biodiversity' }]} />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <InputField label="Reporting Year" value={reportingYear} onChange={setReportingYear} type="number" />
          <InputField label="Total Turnover (EUR)" value={turnover} onChange={setTurnover} type="number" placeholder="e.g. 500000000" />
          <InputField label="Total CapEx (EUR)" value={capex} onChange={setCapex} type="number" placeholder="e.g. 120000000" />
          <InputField label="Total OpEx (EUR)" value={opex} onChange={setOpex} type="number" placeholder="e.g. 80000000" />
        </div>
        <ErrorBox message={error} />
        <div className="flex justify-end mt-4"><SubmitBtn onClick={assessEntity} loading={loading} label="Assess Taxonomy Alignment" /></div>
      </Card>

      <Collapsible title="Reference: DNSH Matrix & Minimum Safeguards">
        <div className="space-y-3">
          <p className="text-xs text-gray-500">Art 17 requires that Taxonomy-aligned activities Do No Significant Harm to the other 5 objectives. Art 18 requires compliance with minimum safeguards (OECD, UNGP, ILO).</p>
          <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
            {['CCM - Mitigation', 'CCA - Adaptation', 'WTR - Water', 'CE - Circular', 'POL - Pollution', 'BIO - Biodiversity'].map((o, i) => (
              <div key={i} className="p-2 rounded-lg text-[10px] text-center border border-gray-200" style={{ backgroundColor: `${OBJ_COLORS[i]}10` }}>
                <p className="font-semibold text-gray-600">{o.split(' - ')[0]}</p>
                <p className="text-gray-500">{o.split(' - ')[1]}</p>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-gray-500 mt-2">
            <div className="p-2 bg-gray-50 rounded"><span className="text-gray-600 font-semibold">OECD:</span> MNE Guidelines Ch IV (Human Rights)</div>
            <div className="p-2 bg-gray-50 rounded"><span className="text-gray-600 font-semibold">UNGP:</span> UN Guiding Principles on Business & Human Rights</div>
            <div className="p-2 bg-gray-50 rounded"><span className="text-gray-600 font-semibold">ILO:</span> 8 Core Conventions (forced labour, child labour, discrimination)</div>
            <div className="p-2 bg-gray-50 rounded"><span className="text-gray-600 font-semibold">Int'l Bill:</span> International Bill of Human Rights</div>
          </div>
        </div>
      </Collapsible>

      <Collapsible title="Reference: Financial KPIs (EBA ITS)">
        <div className="grid grid-cols-3 gap-3 text-xs text-gray-500">
          <div className="p-3 bg-emerald-500/[0.04] border border-emerald-500/10 rounded-lg">
            <p className="font-semibold text-emerald-400 mb-1">Turnover KPI</p>
            <p>Net turnover from Taxonomy-aligned activities / Total net turnover</p>
          </div>
          <div className="p-3 bg-blue-500/[0.04] border border-blue-500/10 rounded-lg">
            <p className="font-semibold text-blue-300 mb-1">CapEx KPI</p>
            <p>Capital expenditure on Taxonomy-aligned activities / Total CapEx</p>
          </div>
          <div className="p-3 bg-purple-500/[0.04] border border-purple-500/10 rounded-lg">
            <p className="font-semibold text-purple-300 mb-1">OpEx KPI</p>
            <p>Operating expenditure on Taxonomy-aligned activities / Total OpEx</p>
          </div>
        </div>
      </Collapsible>

      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <StatCard label="Turnover Alignment" value={`${(result.turnover_alignment_pct ?? result.turnover_aligned_pct ?? 0).toFixed(1)}%`} color="text-emerald-400" sub="of total turnover" />
            <StatCard label="CapEx Alignment" value={`${(result.capex_alignment_pct ?? result.capex_aligned_pct ?? 0).toFixed(1)}%`} color="text-blue-300" sub="of total CapEx" />
            <StatCard label="OpEx Alignment" value={`${(result.opex_alignment_pct ?? result.opex_aligned_pct ?? 0).toFixed(1)}%`} color="text-purple-300" sub="of total OpEx" />
            <StatCard label="GAR" value={`${(result.gar ?? 0).toFixed(2)}`} color="text-gray-700" sub="Green Asset Ratio" />
            <StatCard label="BTAR" value={`${(result.btar ?? 0).toFixed(2)}`} color="text-amber-400" sub="Banking Taxonomy Alignment" />
          </div>

          {(result.transitional_share != null || result.enabling_share != null) && (
            <div className="grid grid-cols-2 gap-4">
              <StatCard label="Transitional Share" value={`${(result.transitional_share ?? 0).toFixed(1)}%`} color="text-amber-400" sub="Art 10(2) transitional activities" />
              <StatCard label="Enabling Share" value={`${(result.enabling_share ?? 0).toFixed(1)}%`} color="text-emerald-400" sub="Art 16 enabling activities" />
            </div>
          )}

          {objData.length > 0 && (
            <Card title="Objective Breakdown">
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={objData} dataKey="alignment" nameKey="objective" cx="50%" cy="50%" outerRadius={80} label={({ objective, alignment }) => `${objective}: ${alignment}%`}>
                    {objData.map((_, i) => <Cell key={i} fill={OBJ_COLORS[i % OBJ_COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #ffffff10', borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            </Card>
          )}

          {(result.eligible_vs_aligned || result.comparison) && (
            <Card title="Eligible vs Aligned Activities">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={[{ name: 'Turnover', eligible: result.eligible_vs_aligned?.turnover_eligible ?? 0, aligned: result.eligible_vs_aligned?.turnover_aligned ?? 0 },
                  { name: 'CapEx', eligible: result.eligible_vs_aligned?.capex_eligible ?? 0, aligned: result.eligible_vs_aligned?.capex_aligned ?? 0 },
                  { name: 'OpEx', eligible: result.eligible_vs_aligned?.opex_eligible ?? 0, aligned: result.eligible_vs_aligned?.opex_aligned ?? 0 }]}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#ffffff60' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#ffffff60' }} tickFormatter={v => `${v}%`} />
                  <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #ffffff10', borderRadius: 8 }} />
                  <Legend wrapperStyle={{ fontSize: 10 }} />
                  <Bar dataKey="eligible" name="Eligible" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="aligned" name="Aligned" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TAB 2 — EUDR COMPLIANCE
   ═══════════════════════════════════════════════════════════════════════════ */
function EudrTab() {
  const [commodities, setCommodities] = useState([]);
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [screenResult, setScreenResult] = useState(null);
  const [ddResult, setDdResult] = useState(null);

  // Screening form
  const [commodity, setCommodity] = useState('coffee');
  const [hsCodes, setHsCodes] = useState('');
  const [originCountry, setOriginCountry] = useState('');
  const [volumeTonnes, setVolumeTonnes] = useState('');
  // DD form
  const [operatorName, setOperatorName] = useState('');
  const [ddCommodities, setDdCommodities] = useState('coffee');
  const [supplyCountries, setSupplyCountries] = useState('');
  const [certifications, setCertifications] = useState('');

  const fetchRef = useCallback(async () => {
    try {
      const [comRes, ctryRes] = await Promise.all([
        axios.get(`${API_BASE}/api/v1/eudr/ref/commodities`),
        axios.get(`${API_BASE}/api/v1/eudr/ref/country-benchmarks`),
      ]);
      setCommodities(comRes.data?.commodities || comRes.data || []);
      setCountries(ctryRes.data?.countries || ctryRes.data || []);
    } catch { /* ref may not be live */ }
  }, []);

  useEffect(() => { fetchRef(); }, [fetchRef]);

  const screenCommodity = async () => {
    setLoading(true); setError(''); setScreenResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/eudr/commodity-screening`, {
        commodity, hs_codes: hsCodes ? hsCodes.split(',').map(s => s.trim()) : [],
        origin_country: originCountry, volume_tonnes: parseFloat(volumeTonnes) || 0,
      });
      setScreenResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || err.message); }
    setLoading(false);
  };

  const runDueDiligence = async () => {
    setLoading(true); setError(''); setDdResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/eudr/due-diligence`, {
        operator_name: operatorName || 'Demo Operator',
        commodities: ddCommodities.split(',').map(s => s.trim()),
        supply_chain_countries: supplyCountries ? supplyCountries.split(',').map(s => s.trim()) : [],
        certifications: certifications ? certifications.split(',').map(s => s.trim()) : [],
        geolocation_data: {},
      });
      setDdResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || err.message); }
    setLoading(false);
  };

  const riskColor = (tier) => {
    if (tier === 'low') return 'bg-emerald-500/10 text-emerald-400';
    if (tier === 'standard') return 'bg-amber-500/10 text-amber-400';
    if (tier === 'high') return 'bg-red-500/10 text-red-400';
    return 'bg-gray-50 text-gray-500';
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="EU 2023/1115 (EUDR)" color="bg-emerald-400/10 text-emerald-400" />
        <Badge label="7 Forest-Risk Commodities" color="bg-blue-400/10 text-blue-300" />
        <Badge label="Art 8-11 DDS" color="bg-gray-50 text-gray-800" />
      </div>

      <Collapsible title="Reference: Commodities & Country Benchmarks">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs font-semibold text-gray-600 mb-2">Annex I Commodities</p>
            <div className="space-y-1">
              {(commodities.length ? commodities : ['Cattle', 'Cocoa', 'Coffee', 'Oil Palm', 'Rubber', 'Soy', 'Wood']).map((c, i) => (
                <div key={i} className="text-xs text-gray-500 p-1.5 bg-gray-50 rounded">{typeof c === 'string' ? c : c.name || c.commodity}</div>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-600 mb-2">Country Tiers (sample)</p>
            <div className="space-y-1 max-h-40 overflow-y-auto">
              {(Array.isArray(countries) ? countries.slice(0, 15) : []).map((c, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-gray-500">
                  <Badge label={c.risk_tier || c.tier || 'std'} color={riskColor(c.risk_tier || c.tier)} />
                  <span>{c.country || c.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Collapsible>

      <Collapsible title="Reference: HS Codes & Enforcement Timeline">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs font-semibold text-gray-600 mb-2">Key HS/CN Code Ranges</p>
            <div className="space-y-1 text-xs text-gray-500">
              {[
                { code: 'HS 0201-0206', desc: 'Cattle: Fresh/frozen/offal meat' },
                { code: 'HS 1801-1806', desc: 'Cocoa: Beans, paste, butter, chocolate' },
                { code: 'HS 0901, 2101', desc: 'Coffee: Beans, extracts, concentrates' },
                { code: 'HS 1511, 1513', desc: 'Palm Oil: Crude/refined, palm kernel' },
                { code: 'HS 4001-4017', desc: 'Rubber: Natural, synthetic, articles' },
                { code: 'HS 1201, 1507', desc: 'Soy: Beans, oil, oilcake' },
                { code: 'HS 4401-4421', desc: 'Wood: Fuel, charcoal, sawn, panels' },
              ].map((h, i) => (
                <div key={i} className="flex gap-2 p-1.5 bg-gray-50 rounded">
                  <span className="font-mono text-gray-500 shrink-0">{h.code}</span>
                  <span>{h.desc}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-600 mb-2">Enforcement Timeline</p>
            <div className="space-y-2 text-xs text-gray-500">
              <div className="p-2 bg-emerald-500/[0.04] border border-emerald-500/10 rounded-lg">
                <p className="text-emerald-400 font-semibold">29 Jun 2023</p>
                <p>Regulation entered into force</p>
              </div>
              <div className="p-2 bg-blue-500/[0.04] border border-blue-500/10 rounded-lg">
                <p className="text-blue-300 font-semibold">30 Dec 2024</p>
                <p>EC country benchmarking list published</p>
              </div>
              <div className="p-2 bg-amber-500/[0.04] border border-amber-500/10 rounded-lg">
                <p className="text-amber-400 font-semibold">30 Dec 2025</p>
                <p>Large operators / traders compliance deadline</p>
              </div>
              <div className="p-2 bg-purple-500/[0.04] border border-purple-500/10 rounded-lg">
                <p className="text-purple-300 font-semibold">30 Jun 2026</p>
                <p>SME traders extended deadline (Del. Reg. 2024/2955)</p>
              </div>
            </div>
          </div>
        </div>
      </Collapsible>

      <Card title="Commodity Screening" subtitle="Screen a commodity lot against EUDR eligibility criteria (Art 3).">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <SelectField label="Commodity" value={commodity} onChange={setCommodity}
            options={['cattle','cocoa','coffee','oil_palm','rubber','soy','wood'].map(c => ({ value: c, label: c.replace('_', ' ') }))} />
          <InputField label="HS Codes (comma-sep)" value={hsCodes} onChange={setHsCodes} placeholder="e.g. 0901, 2101" />
          <InputField label="Origin Country" value={originCountry} onChange={setOriginCountry} placeholder="e.g. Brazil" />
          <InputField label="Volume (tonnes)" value={volumeTonnes} onChange={setVolumeTonnes} type="number" placeholder="e.g. 5000" />
        </div>
        <ErrorBox message={error} />
        <div className="flex justify-end mt-2"><SubmitBtn onClick={screenCommodity} loading={loading} label="Screen Commodity" /></div>
      </Card>

      {screenResult && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Risk Tier" value={screenResult.risk_tier || screenResult.country_risk || 'N/A'} color={screenResult.risk_tier === 'low' ? 'text-emerald-400' : screenResult.risk_tier === 'high' ? 'text-red-400' : 'text-amber-400'} />
          <StatCard label="Eligible" value={screenResult.eligible ? 'Yes' : 'No'} color={screenResult.eligible ? 'text-emerald-400' : 'text-red-400'} />
          <StatCard label="Traceability Score" value={`${(screenResult.traceability_score ?? 0).toFixed(0)}%`} color="text-gray-700" />
          <StatCard label="DDS Required" value={screenResult.dds_required ? 'Yes' : 'Simplified'} color="text-amber-400" />
        </div>
      )}

      <Card title="Due Diligence Assessment" subtitle="Full EUDR due diligence assessment for an operator (Art 8-11).">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <InputField label="Operator Name" value={operatorName} onChange={setOperatorName} placeholder="e.g. Global Trade Co" />
          <InputField label="Commodities (comma-sep)" value={ddCommodities} onChange={setDdCommodities} placeholder="e.g. coffee, cocoa" />
          <InputField label="Supply Chain Countries" value={supplyCountries} onChange={setSupplyCountries} placeholder="e.g. Brazil, Colombia" />
          <InputField label="Certifications" value={certifications} onChange={setCertifications} placeholder="e.g. FSC, RSPO" />
        </div>
        <div className="flex justify-end mt-2"><SubmitBtn onClick={runDueDiligence} loading={loading} label="Run Due Diligence" /></div>
      </Card>

      {ddResult && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="DD Completeness" value={`${(ddResult.completeness_pct ?? ddResult.dd_completeness ?? 0).toFixed(0)}%`} color="text-gray-700" />
            <StatCard label="DDS Ready" value={ddResult.dds_ready ? 'Yes' : 'No'} color={ddResult.dds_ready ? 'text-emerald-400' : 'text-red-400'} />
            <StatCard label="Compliance Gaps" value={ddResult.gaps?.length ?? ddResult.compliance_gaps?.length ?? 0} color="text-amber-400" />
            <StatCard label="Risk Level" value={ddResult.overall_risk || 'Standard'} color="text-purple-300" />
          </div>
          {(ddResult.gaps || ddResult.compliance_gaps || []).length > 0 && (
            <Card title="Compliance Gaps">
              <div className="space-y-2">
                {(ddResult.gaps || ddResult.compliance_gaps || []).map((g, i) => (
                  <div key={i} className="flex items-start gap-2 p-2.5 border border-amber-500/20 bg-amber-500/[0.06] rounded-lg">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
                    <span className="text-xs text-gray-600">{typeof g === 'string' ? g : g.description || g.gap || g.label}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TAB 3 — CSDDD DUE DILIGENCE
   ═══════════════════════════════════════════════════════════════════════════ */
function CsdddTab() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [scopeResult, setScopeResult] = useState(null);
  const [ddResult, setDdResult] = useState(null);
  const [adverseImpacts, setAdverseImpacts] = useState([]);

  // Scope form
  const [entityName, setEntityName] = useState('');
  const [isEu, setIsEu] = useState(true);
  const [employees, setEmployees] = useState('');
  const [turnoverEur, setTurnoverEur] = useState('');
  const [sectorInput, setSectorInput] = useState('');
  // DD form
  const [ddEntityName, setDdEntityName] = useState('');
  const [obligations, setObligations] = useState({ policy: 70, identification: 60, prevention: 55, remediation: 50, remediation_provided: 45, stakeholder: 65, grievance: 40, monitoring: 60, reporting: 55 });

  const fetchRef = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/v1/csddd/ref/adverse-impacts`);
      setAdverseImpacts(res.data?.categories || res.data || []);
    } catch { /* ref optional */ }
  }, []);

  useEffect(() => { fetchRef(); }, [fetchRef]);

  const assessScope = async () => {
    setLoading(true); setError(''); setScopeResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/csddd/scope-assessment`, {
        entity_name: entityName || 'Demo Entity', is_eu_entity: isEu,
        employees: parseInt(employees) || 0, turnover_eur: parseFloat(turnoverEur) || 0,
        sector: sectorInput || 'general',
      });
      setScopeResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || err.message); }
    setLoading(false);
  };

  const assessDD = async () => {
    setLoading(true); setError(''); setDdResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/csddd/dd-compliance`, {
        entity_name: ddEntityName || 'Demo Entity',
        obligations_data: obligations,
        adverse_impacts_identified: [], value_chain_data: {},
      });
      setDdResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || err.message); }
    setLoading(false);
  };

  const oblKeys = Object.keys(obligations);
  const radarData = oblKeys.map(k => ({ obligation: k.replace(/_/g, ' '), score: obligations[k], fullMark: 100 }));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="Directive (EU) 2024/1760" color="bg-purple-400/10 text-purple-300" />
        <Badge label="Art 2 Scope" color="bg-blue-400/10 text-blue-300" />
        <Badge label="18 Adverse Impact Categories" color="bg-amber-400/10 text-amber-400" />
        <Badge label="5% Turnover Penalty" color="bg-red-400/10 text-red-400" />
      </div>

      <Collapsible title="Reference: Adverse Impact Categories & Penalties">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs font-semibold text-gray-600 mb-2">Human Rights (HR-01 to HR-10)</p>
            <div className="space-y-1 text-xs text-gray-500">
              {['Forced labour', 'Child labour', 'Unsafe working conditions', 'Freedom of association', 'Discrimination',
                'Inadequate wages', 'Land & resource rights', 'Privacy violations', 'Cultural heritage', 'Adequate standard of living'].map((h, i) => (
                <div key={i} className="p-1 bg-gray-50 rounded">HR-{String(i+1).padStart(2,'0')}: {h}</div>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-600 mb-2">Environmental (ENV-01 to ENV-08)</p>
            <div className="space-y-1 text-xs text-gray-500">
              {['GHG emissions', 'Deforestation', 'Water pollution', 'Air pollution', 'Soil degradation',
                'Biodiversity loss', 'Waste management', 'Hazardous substances'].map((e, i) => (
                <div key={i} className="p-1 bg-gray-50 rounded">ENV-{String(i+1).padStart(2,'0')}: {e}</div>
              ))}
            </div>
            <div className="mt-3 p-2 bg-red-500/[0.06] border border-red-500/10 rounded-lg">
              <p className="text-xs font-semibold text-red-400">Max Penalty: 5% worldwide turnover</p>
              <p className="text-[10px] text-gray-500">Art 30-33 + Art 22 civil liability (5-year limitation)</p>
            </div>
          </div>
        </div>
      </Collapsible>

      <Collapsible title="Reference: Scope Thresholds & Phase-In Groups">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-gray-500">
            <thead><tr className="border-b border-gray-200">
              <th className="text-left py-2 px-2 text-gray-600">Group</th>
              <th className="text-left py-2 px-2 text-gray-600">Type</th>
              <th className="text-left py-2 px-2 text-gray-600">Employees</th>
              <th className="text-left py-2 px-2 text-gray-600">Turnover</th>
              <th className="text-left py-2 px-2 text-gray-600">Effective</th>
            </tr></thead>
            <tbody>
              {[
                { group: 'Group 1', type: 'EU', emp: '>5,000', turnover: '>EUR 1.5bn', eff: '26 Jul 2027' },
                { group: 'Group 2', type: 'EU', emp: '>3,000', turnover: '>EUR 900m', eff: '26 Jul 2028' },
                { group: 'Group 3', type: 'EU', emp: '>1,000', turnover: '>EUR 450m', eff: '26 Jul 2029' },
                { group: 'Non-EU 1', type: 'Non-EU', emp: '-', turnover: '>EUR 1.5bn in EU', eff: '26 Jul 2027' },
                { group: 'Non-EU 2', type: 'Non-EU', emp: '-', turnover: '>EUR 900m in EU', eff: '26 Jul 2028' },
                { group: 'Non-EU 3', type: 'Non-EU', emp: '-', turnover: '>EUR 450m in EU', eff: '26 Jul 2029' },
              ].map((r, i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="py-1.5 px-2 font-semibold text-gray-700">{r.group}</td>
                  <td className="py-1.5 px-2">{r.type}</td>
                  <td className="py-1.5 px-2">{r.emp}</td>
                  <td className="py-1.5 px-2">{r.turnover}</td>
                  <td className="py-1.5 px-2 text-gray-700">{r.eff}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Collapsible>

      <Collapsible title="Reference: High-Risk Sectors (NACE Codes)">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-gray-500">
          {[
            { sector: 'Textiles & Leather', nace: 'C13-C15' },
            { sector: 'Agriculture & Forestry', nace: 'A01-A02' },
            { sector: 'Food & Beverage', nace: 'C10-C12' },
            { sector: 'Mining & Metals', nace: 'B05-B08, C24' },
            { sector: 'Construction', nace: 'F41-F43' },
            { sector: 'Wholesale Trade', nace: 'G46' },
            { sector: 'Extraction of Crude', nace: 'B06' },
            { sector: 'Financial Services', nace: 'K64-K66' },
          ].map((s, i) => (
            <div key={i} className="p-2 bg-gray-50 border border-gray-200 rounded-lg">
              <p className="text-gray-600 font-semibold">{s.sector}</p>
              <p className="font-mono text-[10px] text-amber-400/60">{s.nace}</p>
            </div>
          ))}
        </div>
      </Collapsible>

      <Card title="Scope Assessment (Art 2)" subtitle="Determine if the entity falls within CSDDD scope based on employees and turnover thresholds.">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
          <InputField label="Entity Name" value={entityName} onChange={setEntityName} placeholder="e.g. Acme GmbH" />
          <SelectField label="EU Entity?" value={isEu ? 'true' : 'false'} onChange={v => setIsEu(v === 'true')}
            options={[{ value: 'true', label: 'Yes - EU entity' }, { value: 'false', label: 'No - Non-EU entity' }]} />
          <InputField label="Employees" value={employees} onChange={setEmployees} type="number" placeholder="e.g. 1200" />
          <InputField label="Turnover (EUR)" value={turnoverEur} onChange={setTurnoverEur} type="number" placeholder="e.g. 300000000" />
          <InputField label="Sector" value={sectorInput} onChange={setSectorInput} placeholder="e.g. textiles" />
        </div>
        <ErrorBox message={error} />
        <div className="flex justify-end mt-2"><SubmitBtn onClick={assessScope} loading={loading} label="Assess Scope" /></div>
      </Card>

      {scopeResult && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="In Scope" value={scopeResult.in_scope ? 'Yes' : 'No'} color={scopeResult.in_scope ? 'text-emerald-400' : 'text-gray-500'} />
          <StatCard label="Scope Group" value={scopeResult.group || scopeResult.scope_group || 'N/A'} color="text-purple-300" sub={scopeResult.phase_in_date || ''} />
          <StatCard label="High-Risk Sector" value={scopeResult.high_risk_sector ? 'Yes' : 'No'} color={scopeResult.high_risk_sector ? 'text-amber-400' : 'text-gray-500'} />
          <StatCard label="Phase-In Year" value={scopeResult.phase_in_year || scopeResult.effective_year || 'TBD'} color="text-gray-700" />
        </div>
      )}

      <Card title="DD Compliance Assessment (Art 5-13)" subtitle="Score 9 due diligence obligations to compute overall compliance.">
        <div className="grid grid-cols-3 md:grid-cols-5 gap-3 mb-4">
          {oblKeys.map(k => (
            <div key={k}>
              <label className="block text-[10px] text-gray-500 mb-1 capitalize">{k.replace(/_/g, ' ')}</label>
              <input type="number" min="0" max="100" value={obligations[k]}
                onChange={e => setObligations(prev => ({ ...prev, [k]: Math.min(100, Math.max(0, parseInt(e.target.value) || 0)) }))}
                className="w-full border border-gray-200 rounded px-2 py-1 text-xs bg-[#f5f6f8] text-gray-700 focus:outline-none" />
            </div>
          ))}
        </div>
        <InputField label="Entity Name" value={ddEntityName} onChange={setDdEntityName} placeholder="e.g. Acme GmbH" className="mb-4 max-w-xs" />
        <div className="flex justify-end"><SubmitBtn onClick={assessDD} loading={loading} label="Assess DD Compliance" /></div>
      </Card>

      {ddResult && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl border border-gray-200 p-5 text-center">
              <p className="text-xs text-gray-500 mb-1">DD Score</p>
              <p className={`text-3xl font-bold ${(ddResult.overall_score ?? 0) >= 75 ? 'text-emerald-400' : (ddResult.overall_score ?? 0) >= 50 ? 'text-amber-400' : 'text-red-400'}`}>
                {(ddResult.overall_score ?? 0).toFixed(0)}
              </p>
              {ratingBadge(ddResult.overall_score ?? 0)}
            </div>
            <StatCard label="Compliance Rating" value={ddResult.rating || ddResult.compliance_rating || 'N/A'} color="text-gray-700" />
            <StatCard label="Penalty Exposure" value={ddResult.penalty_exposure || ddResult.max_penalty || 'N/A'} color="text-red-400" sub="Art 30-33 max 5% turnover" />
            <StatCard label="EUDR Overlap" value={ddResult.eudr_overlap ? 'Flagged' : 'None'} color={ddResult.eudr_overlap ? 'text-amber-400' : 'text-gray-500'} />
          </div>

          <Card title="Obligation Breakdown (Radar)">
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#ffffff10" />
                <PolarAngleAxis dataKey="obligation" tick={{ fontSize: 9, fill: '#ffffff60' }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 8, fill: '#ffffff40' }} />
                <Radar name="Score" dataKey="score" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          </Card>

          {(ddResult.adverse_impacts || ddResult.impacts || []).length > 0 && (
            <Card title="Adverse Impact Heatmap">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {(ddResult.adverse_impacts || ddResult.impacts || []).map((imp, i) => (
                  <div key={i} className={`p-2 rounded-lg text-xs ${(imp.severity || imp.risk || 'low') === 'high' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : (imp.severity || imp.risk) === 'medium' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-gray-50 text-gray-500 border border-gray-200'}`}>
                    <p className="font-semibold">{imp.category || imp.id}</p>
                    <p className="text-[10px] mt-0.5">{imp.description || imp.label || ''}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   TAB 4 — CLIMATE TRANSITION PLAN
   ═══════════════════════════════════════════════════════════════════════════ */
function TransitionPlanTab() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [pathwayResult, setPathwayResult] = useState(null);
  const [frameworks, setFrameworks] = useState([]);

  // Assessment form
  const [entityName, setEntityName] = useState('');
  const [sector, setSector] = useState('');
  const [reportingYear, setReportingYear] = useState('2025');
  const [tptScore, setTptScore] = useState(60);
  const [gfanzScore, setGfanzScore] = useState(55);
  const [iigccScore, setIigccScore] = useState(50);
  const [csdddArt22Score, setCsdddArt22Score] = useState(45);
  const [esrsE1Score, setEsrsE1Score] = useState(65);
  // Pathway form
  const [pathSector, setPathSector] = useState('power');
  const [currentIntensity, setCurrentIntensity] = useState('');
  const [targetIntensity, setTargetIntensity] = useState('');
  const [targetYear, setTargetYear] = useState('2030');

  const fetchRef = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/v1/transition-plan/ref/cross-framework-mapping`);
      setFrameworks(res.data?.mappings || res.data || []);
    } catch { /* ref optional */ }
  }, []);

  useEffect(() => { fetchRef(); }, [fetchRef]);

  const assess = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/transition-plan/assess`, {
        entity_name: entityName || 'Demo Entity', sector: sector || 'power', reporting_year: parseInt(reportingYear),
        tpt_data: { score: tptScore }, gfanz_data: { score: gfanzScore }, iigcc_data: { score: iigccScore },
        csddd_art22_data: { score: csdddArt22Score }, esrs_e1_data: { score: esrsE1Score }, cdp_c4_data: {},
      });
      setResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || err.message); }
    setLoading(false);
  };

  const assessPathway = async () => {
    setLoading(true); setError(''); setPathwayResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/transition-plan/assess-sector-pathway`, {
        entity_name: entityName || 'Demo Entity', sector: pathSector,
        current_intensity: parseFloat(currentIntensity) || 0,
        target_intensity: parseFloat(targetIntensity) || 0,
        target_year: parseInt(targetYear),
      });
      setPathwayResult(res.data);
    } catch (err) { setError(err.response?.data?.detail || err.message); }
    setLoading(false);
  };

  const dimensions = result?.dimensions || result?.dimension_scores || [];
  const dimData = Array.isArray(dimensions) ? dimensions : Object.entries(dimensions).map(([k, v]) => ({ dimension: k, score: typeof v === 'object' ? v.score : v, fullMark: 100 }));

  const gapList = result?.gaps || result?.inter_framework_gaps || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="TPT Framework" color="bg-blue-400/10 text-blue-300" />
        <Badge label="GFANZ" color="bg-emerald-400/10 text-emerald-400" />
        <Badge label="IIGCC Net Zero" color="bg-purple-400/10 text-purple-300" />
        <Badge label="CSDDD Art 22" color="bg-amber-400/10 text-amber-400" />
        <Badge label="ESRS E1" color="bg-gray-50 text-gray-800" />
      </div>

      <Collapsible title="Reference: Cross-Framework Mapping">
        {frameworks.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-gray-500">
              <thead><tr className="border-b border-gray-200">
                <th className="text-left py-1.5 px-2 text-gray-600">Dimension</th>
                <th className="text-left py-1.5 px-2 text-gray-600">TPT</th>
                <th className="text-left py-1.5 px-2 text-gray-600">GFANZ</th>
                <th className="text-left py-1.5 px-2 text-gray-600">ESRS E1</th>
              </tr></thead>
              <tbody>
                {frameworks.slice(0, 10).map((f, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="py-1.5 px-2 text-gray-700">{f.dimension || f.name}</td>
                    <td className="py-1.5 px-2">{f.tpt || '-'}</td>
                    <td className="py-1.5 px-2">{f.gfanz || '-'}</td>
                    <td className="py-1.5 px-2">{f.esrs_e1 || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid grid-cols-5 gap-2 text-xs text-gray-500">
            {['Target Credibility', 'Implementation Maturity', 'Governance', 'Financial Commitment', 'Transparency'].map((d, i) => (
              <div key={i} className="p-2 rounded-lg bg-gray-50 text-center">{d}</div>
            ))}
          </div>
        )}
      </Collapsible>

      <Card title="Transition Plan Assessment" subtitle="Multi-framework assessment across TPT, GFANZ, IIGCC, CSDDD Art 22, and ESRS E1.">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <InputField label="Entity Name" value={entityName} onChange={setEntityName} placeholder="e.g. Acme Energy" />
          <InputField label="Sector" value={sector} onChange={setSector} placeholder="e.g. power" />
          <InputField label="Reporting Year" value={reportingYear} onChange={setReportingYear} type="number" />
          <div />
        </div>
        <p className="text-xs font-semibold text-gray-600 mb-2">Framework Scores (0-100)</p>
        <div className="grid grid-cols-5 gap-3 mb-4">
          {[['TPT', tptScore, setTptScore], ['GFANZ', gfanzScore, setGfanzScore], ['IIGCC', iigccScore, setIigccScore],
            ['CSDDD Art 22', csdddArt22Score, setCsdddArt22Score], ['ESRS E1', esrsE1Score, setEsrsE1Score]].map(([label, val, setter]) => (
            <div key={label}>
              <label className="block text-[10px] text-gray-500 mb-1">{label}</label>
              <input type="number" min="0" max="100" value={val}
                onChange={e => setter(Math.min(100, Math.max(0, parseInt(e.target.value) || 0)))}
                className="w-full border border-gray-200 rounded px-2 py-1 text-xs bg-[#f5f6f8] text-gray-700 focus:outline-none" />
            </div>
          ))}
        </div>
        <ErrorBox message={error} />
        <div className="flex justify-end mt-2"><SubmitBtn onClick={assess} loading={loading} label="Assess Transition Plan" /></div>
      </Card>

      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-black/20 to-purple-500/20 border border-black/10 rounded-xl p-5 text-center">
              <p className="text-xs text-gray-500 mb-1">Overall Score</p>
              <p className="text-3xl font-bold text-gray-900">{(result.overall_score ?? 0).toFixed(0)}</p>
              {ratingBadge(result.overall_score ?? 0)}
            </div>
            <StatCard label="Rating" value={result.rating || result.overall_rating || 'N/A'} color="text-gray-700" />
            <StatCard label="Framework Coverage" value={`${(result.framework_coverage ?? result.completeness ?? 0).toFixed(0)}%`} color="text-purple-300" sub="of assessed frameworks" />
            <StatCard label="Improvement Items" value={(gapList.length)} color="text-amber-400" sub="inter-framework gaps" />
          </div>

          {dimData.length > 0 && (
            <Card title="5-Dimension Radar">
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={dimData}>
                  <PolarGrid stroke="#ffffff10" />
                  <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 9, fill: '#ffffff60' }} />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 8, fill: '#ffffff40' }} />
                  <Radar name="Score" dataKey="score" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.25} />
                </RadarChart>
              </ResponsiveContainer>
            </Card>
          )}

          {(result.framework_completeness || result.framework_scores) && (
            <Card title="Framework Completeness">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={Object.entries(result.framework_completeness || result.framework_scores || {}).map(([k, v]) => ({ framework: k, completeness: typeof v === 'object' ? v.completeness || v.score : v }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis dataKey="framework" tick={{ fontSize: 9, fill: '#ffffff60' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#ffffff60' }} tickFormatter={v => `${v}%`} />
                  <Tooltip contentStyle={{ background: '#ffffff', border: '1px solid #ffffff10', borderRadius: 8 }} />
                  <Bar dataKey="completeness" name="Completeness" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                    {Object.entries(result.framework_completeness || result.framework_scores || {}).map((_, i) => (
                      <Cell key={i} fill={RADAR_COLORS[i % RADAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}

          {gapList.length > 0 && (
            <Card title="Inter-Framework Gaps & Improvement Roadmap">
              <div className="space-y-2">
                {gapList.map((g, i) => (
                  <div key={i} className="flex items-start gap-2 p-2.5 border border-amber-500/20 bg-amber-500/[0.06] rounded-lg">
                    <Info className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
                    <div className="flex-1">
                      <p className="text-xs text-gray-700 font-medium">{typeof g === 'string' ? g : g.gap || g.description}</p>
                      {g.recommendation && <p className="text-[10px] text-gray-500 mt-0.5">{g.recommendation}</p>}
                    </div>
                    {g.framework && <Badge label={g.framework} color="bg-gray-50 text-gray-500" />}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      <Card title="Targets Assessment" subtitle="Assess individual reduction targets against SBTi criteria and Paris alignment.">
        <div className="space-y-3 mb-4">
          {[
            { type: 'Scope 1+2', year: 2030, base_year: 2019, reduction_pct: 42, science_based: true, sbti_validated: true },
            { type: 'Scope 3', year: 2030, base_year: 2019, reduction_pct: 25, science_based: true, sbti_validated: false },
          ].map((t, i) => (
            <div key={i} className="grid grid-cols-6 gap-2 items-center p-3 bg-[#f5f6f8] border border-gray-200 rounded-lg">
              <div className="text-xs text-gray-600 font-medium">{t.type}</div>
              <div className="text-xs text-gray-500">Target: {t.year}</div>
              <div className="text-xs text-gray-500">Base: {t.base_year}</div>
              <div className="text-xs text-gray-700">{t.reduction_pct}% reduction</div>
              <div>{t.science_based ? <Badge label="Science-based" color="bg-emerald-500/10 text-emerald-400" /> : <Badge label="Not SBT" color="bg-gray-50 text-gray-500" />}</div>
              <div>{t.sbti_validated ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <XCircle className="w-4 h-4 text-gray-400" />}</div>
            </div>
          ))}
        </div>
        <p className="text-[10px] text-gray-500">Targets are evaluated against SBTi criteria. POST /assess-targets sends an array of target objects.</p>
      </Card>

      <Card title="Sector Pathway Alignment" subtitle="Compare entity decarbonisation trajectory against the sector benchmark.">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
          <SelectField label="Sector" value={pathSector} onChange={setPathSector}
            options={['power', 'steel', 'cement', 'aviation', 'shipping', 'automotive', 'oil_gas', 'real_estate'].map(s => ({ value: s, label: s.replace('_', ' ') }))} />
          <InputField label="Current Intensity (tCO2/unit)" value={currentIntensity} onChange={setCurrentIntensity} type="number" placeholder="e.g. 0.45" />
          <InputField label="Target Intensity" value={targetIntensity} onChange={setTargetIntensity} type="number" placeholder="e.g. 0.12" />
          <InputField label="Target Year" value={targetYear} onChange={setTargetYear} type="number" placeholder="e.g. 2030" />
          <div className="flex items-end"><SubmitBtn onClick={assessPathway} loading={loading} label="Assess Pathway" /></div>
        </div>
      </Card>

      {pathwayResult && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Pathway Aligned" value={pathwayResult.aligned ? 'Yes' : 'No'} color={pathwayResult.aligned ? 'text-emerald-400' : 'text-red-400'} />
          <StatCard label="Gap to Benchmark" value={`${(pathwayResult.gap_to_benchmark ?? pathwayResult.intensity_gap ?? 0).toFixed(2)}`} color="text-amber-400" sub="tCO2/unit" />
          <StatCard label="Reduction Required" value={`${(pathwayResult.reduction_required_pct ?? 0).toFixed(0)}%`} color="text-gray-700" />
          <StatCard label="Benchmark (2030)" value={`${(pathwayResult.benchmark_2030 ?? pathwayResult.sector_benchmark ?? 0).toFixed(2)}`} color="text-purple-300" sub="tCO2/unit" />
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════
   MAIN HUB COMPONENT
   ═══════════════════════════════════════════════════════════════════════════ */
const TABS = [
  { id: 'taxonomy', label: 'EU Taxonomy', icon: <Landmark className="w-3.5 h-3.5" /> },
  { id: 'eudr', label: 'EUDR', icon: <TreePine className="w-3.5 h-3.5" /> },
  { id: 'csddd', label: 'CSDDD', icon: <Scale className="w-3.5 h-3.5" /> },
  { id: 'transition', label: 'Transition Plan', icon: <ArrowUpRight className="w-3.5 h-3.5" /> },
];

export default function EURegulatoryHubPage() {
  const [activeTab, setActiveTab] = useState('taxonomy');

  return (
    <div className="min-h-screen bg-white text-gray-700 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Landmark className="w-5 h-5 text-gray-700" />
            EU Regulatory Compliance Hub
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            Unified assessment interface for EU Taxonomy, EUDR, CSDDD, and Climate Transition Plan frameworks
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge label="EU 2020/852" color="bg-emerald-400/10 text-emerald-400" />
          <Badge label="EU 2023/1115" color="bg-blue-400/10 text-blue-300" />
          <Badge label="EU 2024/1760" color="bg-purple-400/10 text-purple-300" />
        </div>
      </div>

      {/* Tab Navigation */}
      <TabPill tabs={TABS} active={activeTab} onChange={setActiveTab} />

      {/* Tab Content */}
      <div>
        {activeTab === 'taxonomy' && <TaxonomyTab />}
        {activeTab === 'eudr' && <EudrTab />}
        {activeTab === 'csddd' && <CsdddTab />}
        {activeTab === 'transition' && <TransitionPlanTab />}
      </div>

      {/* Shared Methodology Footer */}
      <Card title="Methodology & Legal Basis" className="border-gray-100">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs text-gray-500">
          <div><span className="font-semibold text-gray-700">EU Taxonomy:</span> Regulation (EU) 2020/852 + Delegated Acts 2021/2139, 2023/2486</div>
          <div><span className="font-semibold text-gray-700">EUDR:</span> Regulation (EU) 2023/1115 — 7 forest-risk commodities, DDS per Art 8-11</div>
          <div><span className="font-semibold text-gray-700">CSDDD:</span> Directive (EU) 2024/1760 — corporate due diligence, Art 2 scope, Art 22 climate plan</div>
          <div><span className="font-semibold text-gray-700">Transition Plan:</span> TPT Framework + GFANZ + IIGCC Net Zero + ESRS E1 + CDP C4</div>
          <div><span className="font-semibold text-gray-700">GAR/BTAR:</span> EBA ITS 2022/2453 — Green Asset Ratio, Banking Book Taxonomy Alignment</div>
          <div><span className="font-semibold text-gray-700">DNSH:</span> Art 17 — Do No Significant Harm to other 5 environmental objectives</div>
          <div><span className="font-semibold text-gray-700">Safeguards:</span> Art 18 — OECD Guidelines, UN Guiding Principles, ILO conventions</div>
          <div><span className="font-semibold text-gray-700">Penalties:</span> CSDDD Art 30-33 max 5% turnover; EUDR Art 25 proportionate sanctions</div>
        </div>
      </Card>
    </div>
  );
}
