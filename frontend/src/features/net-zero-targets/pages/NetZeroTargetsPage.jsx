/**
 * NetZeroTargetsPage.jsx
 * Route: /net-zero-targets
 * Badge: NZ · SBTi · E33
 *
 * Tab 1 — Target Setup      POST /api/v1/net-zero-targets/assess
 * Tab 2 — Pathway           POST /api/v1/net-zero-targets/assess
 * Tab 3 — Temperature Score POST /api/v1/net-zero-targets/assess
 * Tab 4 — Framework Compliance
 * Tab 5 — Milestones
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  AreaChart, Area, PieChart, Pie, Cell, ScatterChart, Scatter, ReferenceLine,
} from 'recharts';

const rng = (seed) => { let s = seed; return () => { s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 0xffffffff; }; };

const Section = ({title,sub,children})=><div style={{background:'#fff',border:'1px solid #e5e7eb',borderRadius:8,padding:24,marginBottom:20}}><div style={{marginBottom:16}}><h3 style={{margin:0,fontWeight:700,fontSize:16}}>{title}</h3>{sub&&<p style={{margin:'4px 0 0',color:'#6b7280',fontSize:13}}>{sub}</p>}</div>{children}</div>;
const KpiCard = ({label,value,sub,color='#10b981'})=><div style={{flex:1,minWidth:160,background:'#f9fafb',border:'1px solid #e5e7eb',borderRadius:8,padding:16}}><div style={{fontSize:12,color:'#6b7280',marginBottom:4}}>{label}</div><div style={{fontSize:22,fontWeight:700,color}}>{value}</div>{sub&&<div style={{fontSize:11,color:'#9ca3af',marginTop:2}}>{sub}</div>}</div>;
const Row = ({children,gap=12})=><div style={{display:'flex',flexWrap:'wrap',gap}}>{children}</div>;
const Inp = ({label,...p})=><label style={{display:'flex',flexDirection:'column',gap:4,fontSize:13,color:'#374151'}}>{label}<input {...p} style={{padding:'6px 10px',border:'1px solid #d1d5db',borderRadius:6,fontSize:13,...p.style}}/></label>;
const Sel = ({label,options,...p})=><label style={{display:'flex',flexDirection:'column',gap:4,fontSize:13,color:'#374151'}}>{label}<select {...p} style={{padding:'6px 10px',border:'1px solid #d1d5db',borderRadius:6,fontSize:13,...p.style}}>{options.map(o=><option key={o.value??o} value={o.value??o}>{o.label??o}</option>)}</select></label>;
const Btn = ({children,...p})=><button {...p} style={{padding:'8px 18px',background:'#10b981',color:'#fff',border:'none',borderRadius:6,fontWeight:600,fontSize:13,cursor:'pointer',...p.style}}>{children}</button>;

const TABS = ['Target Setup','Pathway','Temperature Score','Framework Compliance','Milestones'];
const ENTITY_TYPES = [{value:'corporate',label:'Corporate'},{value:'bank',label:'Bank'},{value:'asset_manager',label:'Asset Manager'},{value:'asset_owner',label:'Asset Owner'}];
const FRAMEWORKS = [{value:'sbti',label:'SBTi'},{value:'nzba',label:'NZBA'},{value:'nzami',label:'NZAMI'},{value:'nzaoa',label:'NZAoA'}];
const SCOPE_LABELS = ['Scope 1','Scope 2','Scope 3'];
const TT = {backgroundColor:'#fff',border:'1px solid #e5e7eb',fontSize:11};
const YEARS = [2020,2025,2030,2035,2040,2045,2050];

function buildFallback(seed) {
  const r = rng(seed);
  const baseEmissions = 1000 + r()*4000;
  const tempScore = (1.4 + r()*2.0).toFixed(1);
  const frameworks = ['SBTi','NZBA','NZAMI','NZAoA'];
  const reductionPct = Math.round(42 + r()*28);
  const pathwayData = YEARS.map((yr,i) => {
    const required = Math.round(baseEmissions * Math.pow(0.93 - r()*0.03, i*5));
    const projected = Math.round(baseEmissions * Math.pow(0.95 - r()*0.02, i*5));
    return {year:yr, required, projected, gap: Math.max(0, projected - required)};
  });
  const milestones = [
    {year:2025,target:'Near-term SBTi submission',status:'In Progress',reduction:15},
    {year:2030,target:'42% absolute reduction vs 2020',status:'On Track',reduction:42},
    {year:2035,target:'Intermediate milestone check',status:'Planned',reduction:58},
    {year:2040,target:'75% decarbonisation achieved',status:'Planned',reduction:75},
    {year:2050,target:'Net zero — residual offsets only',status:'Planned',reduction:100},
  ];
  const fwCompliance = frameworks.map(fw => ({
    framework: fw,
    score: Math.round(40 + r()*55),
    status: r()>0.5?'Compliant':r()>0.3?'Partial':'Non-Compliant',
    gaps: Math.round(r()*6),
    key_req: r()>0.5?'Met':'Pending',
  }));
  const residualEmissions = [{name:'Removals (Bioenergy)',value:Math.round(50+r()*100)},{name:'Technical CDR',value:Math.round(30+r()*80)},{name:'Nature-based Solutions',value:Math.round(40+r()*90)},{name:'Unavoidable Residual',value:Math.round(20+r()*60)}];
  return {
    temperature_score: tempScore,
    pathway_gap_pct: Math.round(5+r()*35),
    sbti_status: r()>0.5?'Validated':r()>0.3?'Committed':'Not Started',
    near_term_reduction: reductionPct,
    pathway_data: pathwayData,
    milestones,
    fw_compliance: fwCompliance,
    residual_emissions: residualEmissions,
    scope_coverage: [true,true,r()>0.3],
    bvcm_summary: 'Beyond Value Chain Mitigation (BVCM) plan includes reforestation (200,000 ha by 2030), community-based clean cooking (1.5Mt CO2e/yr), and regenerative agriculture finance ($50M committed).',
    temp_comparison: [
      {framework:'Current Trajectory',temp:parseFloat(tempScore)+0.4},
      {framework:'Near-Term Target',temp:parseFloat(tempScore)},
      {framework:'Net Zero Target',temp:1.5},
      {framework:'Paris Agreement',temp:1.5},
      {framework:'Below 2°C',temp:1.9},
    ],
    fw_requirements: [
      {req:'Near-term science-based target',sbti:r()>0.3,nzba:r()>0.4,nzami:r()>0.4,nzaoa:r()>0.5},
      {req:'Long-term net zero commitment',sbti:r()>0.2,nzba:r()>0.3,nzami:r()>0.3,nzaoa:r()>0.3},
      {req:'Scope 3 coverage >67%',sbti:r()>0.4,nzba:r()>0.5,nzami:r()>0.5,nzaoa:r()>0.4},
      {req:'Annual progress reporting',sbti:r()>0.2,nzba:r()>0.2,nzami:r()>0.2,nzaoa:r()>0.2},
      {req:'Board-level climate governance',sbti:r()>0.3,nzba:r()>0.3,nzami:r()>0.3,nzaoa:r()>0.3},
    ],
  };
}

export default function NetZeroTargetsPage() {
  const [tab, setTab] = useState(0);
  const [form, setForm] = useState({entity_id:'CORP-042',entity_type:'corporate',framework:'sbti',base_year:'2020',net_zero_year:'2050',near_term_year:'2030',near_term_reduction:42});
  const [scopes, setScopes] = useState([true,true,true]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const upd = (k,v) => setForm(f=>({...f,[k]:v}));

  const run = async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/net-zero-targets/assess', {...form, scopes});
      setData(res.data);
    } catch {
      const seed = form.entity_id.split('').reduce((a,c)=>a+c.charCodeAt(0),0)||42;
      setData(buildFallback(seed));
    }
    setLoading(false);
  };

  useEffect(()=>{ run(); },[]);

  const d = data || buildFallback(42);
  const tempColor = t => parseFloat(t)<=1.5?'#10b981':parseFloat(t)<=1.8?'#3b82f6':parseFloat(t)<=2.5?'#f59e0b':'#ef4444';
  const statusColor = s => s==='Compliant'||s==='Validated'||s==='On Track'?'#10b981':s==='Partial'||s==='Committed'||s==='In Progress'?'#f59e0b':'#ef4444';
  const PIE_COLORS = ['#10b981','#3b82f6','#8b5cf6','#f59e0b'];

  return (
    <div style={{fontFamily:'Inter,system-ui,sans-serif',background:'#f9fafb',minHeight:'100vh',padding:24}}>
      <div style={{maxWidth:1100,margin:'0 auto'}}>
        {/* Header */}
        <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:20}}>
          <div>
            <div style={{display:'flex',alignItems:'center',gap:8}}>
              <h1 style={{margin:0,fontSize:22,fontWeight:700}}>Net Zero Target Setting</h1>
              <span style={{background:'#d1fae5',color:'#065f46',padding:'2px 10px',borderRadius:20,fontSize:11,fontWeight:700}}>NZ · SBTi · E33</span>
            </div>
            <p style={{margin:'4px 0 0',color:'#6b7280',fontSize:13}}>Science-based net zero pathway assessment — SBTi / NZBA / NZAMI / NZAoA</p>
          </div>
        </div>

        {/* KPIs */}
        <Row gap={12} style={{marginBottom:20}}>
          <KpiCard label="Temperature Score" value={`${d.temperature_score}°C`} sub="Implied warming trajectory" color={tempColor(d.temperature_score)}/>
          <KpiCard label="Pathway Gap" value={`${d.pathway_gap_pct}%`} sub="vs required reduction" color={d.pathway_gap_pct>20?'#ef4444':'#f59e0b'}/>
          <KpiCard label="SBTi Validation" value={d.sbti_status} sub="Science Based Targets initiative" color={statusColor(d.sbti_status)}/>
          <KpiCard label="Near-Term Reduction" value={`${d.near_term_reduction}%`} sub="Target by near-term year" color="#3b82f6"/>
        </Row>

        {/* Tab bar */}
        <div style={{display:'flex',gap:4,marginBottom:20,borderBottom:'2px solid #e5e7eb'}}>
          {TABS.map((t,i)=>(
            <button key={t} onClick={()=>setTab(i)} style={{padding:'8px 18px',border:'none',borderBottom:tab===i?'2px solid #10b981':'2px solid transparent',background:'none',fontWeight:tab===i?700:400,color:tab===i?'#10b981':'#6b7280',cursor:'pointer',fontSize:13,marginBottom:-2}}>{t}</button>
          ))}
        </div>

        {/* Tab 0 — Target Setup */}
        {tab===0 && (
          <Section title="Net Zero Target Configuration" sub="Define entity parameters, framework selection and scope coverage for assessment">
            <Row gap={12} style={{marginBottom:16}}>
              <Inp label="Entity ID" value={form.entity_id} onChange={e=>upd('entity_id',e.target.value)}/>
              <Sel label="Entity Type" options={ENTITY_TYPES} value={form.entity_type} onChange={e=>upd('entity_type',e.target.value)}/>
              <Sel label="Primary Framework" options={FRAMEWORKS} value={form.framework} onChange={e=>upd('framework',e.target.value)}/>
            </Row>
            <Row gap={12} style={{marginBottom:16}}>
              <Inp label="Base Year" type="number" value={form.base_year} onChange={e=>upd('base_year',e.target.value)}/>
              <Inp label="Net Zero Target Year" type="number" value={form.net_zero_year} onChange={e=>upd('net_zero_year',e.target.value)}/>
              <Inp label="Near-Term Target Year" type="number" value={form.near_term_year} onChange={e=>upd('near_term_year',e.target.value)}/>
              <Inp label="Near-Term Reduction %" type="number" value={form.near_term_reduction} onChange={e=>upd('near_term_reduction',e.target.value)}/>
            </Row>
            <div style={{marginBottom:16}}>
              <div style={{fontSize:13,fontWeight:600,marginBottom:8,color:'#374151'}}>GHG Scope Coverage</div>
              <Row gap={16}>
                {SCOPE_LABELS.map((s,i)=>(
                  <label key={i} style={{display:'flex',alignItems:'center',gap:8,fontSize:13,cursor:'pointer'}}>
                    <input type="checkbox" checked={scopes[i]} onChange={e=>{const ns=[...scopes];ns[i]=e.target.checked;setScopes(ns);}} style={{width:16,height:16,accentColor:'#10b981'}}/>
                    {s}
                  </label>
                ))}
              </Row>
            </div>
            <Btn onClick={run} style={{opacity:loading?0.6:1}}>{loading?'Running…':'Calculate Pathway'}</Btn>
            <div style={{marginTop:20,padding:16,background:'#f0fdf4',borderRadius:8,border:'1px solid #a7f3d0'}}>
              <div style={{fontSize:13,fontWeight:600,color:'#065f46',marginBottom:8}}>Assessment Summary</div>
              <Row gap={16}>
                <div style={{fontSize:13,color:'#374151'}}>Framework: <strong>{form.framework.toUpperCase()}</strong></div>
                <div style={{fontSize:13,color:'#374151'}}>Base Year: <strong>{form.base_year}</strong></div>
                <div style={{fontSize:13,color:'#374151'}}>Net Zero Year: <strong>{form.net_zero_year}</strong></div>
                <div style={{fontSize:13,color:'#374151'}}>Scopes Covered: <strong>{scopes.map((s,i)=>s?SCOPE_LABELS[i]:null).filter(Boolean).join(', ')}</strong></div>
              </Row>
            </div>
          </Section>
        )}

        {/* Tab 1 — Pathway */}
        {tab===1 && (
          <>
            <Section title="Emissions Pathway: Required vs Projected" sub="Science-based required reductions compared to current trajectory (2020-2050)">
              <ResponsiveContainer width="100%" height={270}>
                <AreaChart data={d.pathway_data}>
                  <CartesianGrid strokeDasharray="3 3"/>
                  <XAxis dataKey="year" style={{fontSize:12}}/>
                  <YAxis style={{fontSize:11}} tickFormatter={v=>`${(v/1000).toFixed(1)}kt`}/>
                  <Tooltip contentStyle={TT} formatter={(v,n)=>[`${Math.round(v).toLocaleString()} tCO2e`,n]}/>
                  <Legend/>
                  <Area type="monotone" dataKey="projected" name="Current Projection" stroke="#ef4444" fill="#fee2e2" fillOpacity={0.5}/>
                  <Area type="monotone" dataKey="required" name="Required Pathway" stroke="#10b981" fill="#d1fae5" fillOpacity={0.5}/>
                </AreaChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Year-by-Year Pathway Status" sub="On-track vs off-track assessment per milestone year">
              <table style={{width:'100%',borderCollapse:'collapse',fontSize:13}}>
                <thead><tr style={{background:'#f9fafb'}}>{['Year','Required (tCO2e)','Projected (tCO2e)','Gap','On Track?'].map(h=><th key={h} style={{padding:'8px 12px',textAlign:'left',fontWeight:600,borderBottom:'1px solid #e5e7eb'}}>{h}</th>)}</tr></thead>
                <tbody>{d.pathway_data.map((row,i)=>{
                  const onTrack = row.projected<=row.required*1.05;
                  return <tr key={i} style={{borderBottom:'1px solid #f3f4f6',background:i%2===0?'#fff':'#fafafa'}}>
                    <td style={{padding:'8px 12px',fontWeight:600}}>{row.year}</td>
                    <td style={{padding:'8px 12px'}}>{row.required.toLocaleString()}</td>
                    <td style={{padding:'8px 12px'}}>{row.projected.toLocaleString()}</td>
                    <td style={{padding:'8px 12px',color:row.gap>0?'#ef4444':'#10b981',fontWeight:600}}>{row.gap>0?`+${row.gap.toLocaleString()}`:'—'}</td>
                    <td style={{padding:'8px 12px'}}><span style={{background:onTrack?'#d1fae5':'#fee2e2',color:onTrack?'#065f46':'#991b1b',padding:'2px 8px',borderRadius:12,fontSize:11,fontWeight:600}}>{onTrack?'On Track':'Off Track'}</span></td>
                  </tr>;
                })}</tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 2 — Temperature Score */}
        {tab===2 && (
          <>
            <Section title="Implied Temperature Score" sub="Warming trajectory implied by current emissions pathway">
              <Row gap={20}>
                <div style={{flex:1,textAlign:'center'}}>
                  <div style={{position:'relative',width:160,height:160,margin:'0 auto'}}>
                    <svg width={160} height={160} viewBox="0 0 160 160">
                      <circle cx={80} cy={80} r={65} fill="none" stroke="#e5e7eb" strokeWidth={14}/>
                      <circle cx={80} cy={80} r={65} fill="none" stroke={tempColor(d.temperature_score)} strokeWidth={14}
                        strokeDasharray={`${Math.min((parseFloat(d.temperature_score)-1.0)/3.5,1)*408} 408`}
                        strokeLinecap="round" transform="rotate(-90 80 80)"/>
                    </svg>
                    <div style={{position:'absolute',top:'50%',left:'50%',transform:'translate(-50%,-50%)',textAlign:'center'}}>
                      <div style={{fontSize:30,fontWeight:700,color:tempColor(d.temperature_score)}}>{d.temperature_score}°C</div>
                      <div style={{fontSize:11,color:'#6b7280'}}>Implied warming</div>
                    </div>
                  </div>
                  <div style={{marginTop:12}}>
                    <span style={{background:parseFloat(d.temperature_score)<=1.5?'#d1fae5':parseFloat(d.temperature_score)<=2?'#dbeafe':'#fee2e2',color:parseFloat(d.temperature_score)<=1.5?'#065f46':parseFloat(d.temperature_score)<=2?'#1e40af':'#991b1b',padding:'4px 14px',borderRadius:20,fontSize:12,fontWeight:700}}>
                      {parseFloat(d.temperature_score)<=1.5?'1.5°C Aligned':parseFloat(d.temperature_score)<=2?'Below 2°C':'Above 2°C'}
                    </span>
                  </div>
                </div>
                <div style={{flex:2}}>
                  <div style={{marginBottom:8,fontSize:13,fontWeight:600}}>Temperature Benchmarks</div>
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={d.temp_comparison} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3"/>
                      <XAxis type="number" domain={[0,4]} tickFormatter={v=>`${v}°C`} style={{fontSize:11}}/>
                      <YAxis type="category" dataKey="framework" width={130} style={{fontSize:11}}/>
                      <Tooltip contentStyle={TT} formatter={v=>`${v}°C`}/>
                      <ReferenceLine x={1.5} stroke="#10b981" strokeDasharray="4 4" label={{value:'1.5°C',fill:'#10b981',fontSize:10}}/>
                      <Bar dataKey="temp" name="°C" radius={[0,4,4,0]}>
                        {d.temp_comparison.map((e,i)=><Cell key={i} fill={tempColor(e.temp)}/>)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Row>
            </Section>
          </>
        )}

        {/* Tab 3 — Framework Compliance */}
        {tab===3 && (
          <>
            <Section title="Per-Framework Compliance Status" sub="Compliance assessment across all major net zero frameworks">
              <table style={{width:'100%',borderCollapse:'collapse',fontSize:13,marginBottom:16}}>
                <thead><tr style={{background:'#f9fafb'}}>{['Framework','Score','Status','Open Gaps','Key Req'].map(h=><th key={h} style={{padding:'8px 12px',textAlign:'left',fontWeight:600,borderBottom:'1px solid #e5e7eb'}}>{h}</th>)}</tr></thead>
                <tbody>{d.fw_compliance.map((f,i)=><tr key={i} style={{borderBottom:'1px solid #f3f4f6'}}>
                  <td style={{padding:'8px 12px',fontWeight:700}}>{f.framework}</td>
                  <td style={{padding:'8px 12px'}}>
                    <div style={{display:'flex',alignItems:'center',gap:8}}>
                      <div style={{height:8,width:80,background:'#e5e7eb',borderRadius:4}}><div style={{height:8,background:f.score>=70?'#10b981':f.score>=50?'#f59e0b':'#ef4444',borderRadius:4,width:`${f.score}%`}}/></div>
                      <span style={{fontWeight:600}}>{f.score}</span>
                    </div>
                  </td>
                  <td style={{padding:'8px 12px'}}><span style={{background:f.status==='Compliant'?'#d1fae5':f.status==='Partial'?'#fff7ed':'#fee2e2',color:f.status==='Compliant'?'#065f46':f.status==='Partial'?'#92400e':'#991b1b',padding:'2px 8px',borderRadius:12,fontSize:11,fontWeight:600}}>{f.status}</span></td>
                  <td style={{padding:'8px 12px',color:f.gaps>3?'#ef4444':'#374151',fontWeight:f.gaps>3?700:400}}>{f.gaps}</td>
                  <td style={{padding:'8px 12px'}}><span style={{background:f.key_req==='Met'?'#d1fae5':'#fef3c7',color:f.key_req==='Met'?'#065f46':'#92400e',padding:'2px 8px',borderRadius:12,fontSize:11}}>{f.key_req}</span></td>
                </tr>)}</tbody>
              </table>
            </Section>
            <Section title="Framework Requirements Checklist" sub="Key requirement alignment across frameworks">
              <table style={{width:'100%',borderCollapse:'collapse',fontSize:12}}>
                <thead><tr style={{background:'#f9fafb'}}>{['Requirement','SBTi','NZBA','NZAMI','NZAoA'].map(h=><th key={h} style={{padding:'8px 12px',textAlign:'left',fontWeight:600,borderBottom:'1px solid #e5e7eb'}}>{h}</th>)}</tr></thead>
                <tbody>{d.fw_requirements.map((req,i)=><tr key={i} style={{borderBottom:'1px solid #f3f4f6',background:i%2===0?'#fff':'#fafafa'}}>
                  <td style={{padding:'8px 12px'}}>{req.req}</td>
                  {['sbti','nzba','nzami','nzaoa'].map(fw=><td key={fw} style={{padding:'8px 12px',textAlign:'center'}}>
                    <span style={{fontSize:16}}>{req[fw]?'✅':'❌'}</span>
                  </td>)}
                </tr>)}</tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 4 — Milestones */}
        {tab===4 && (
          <>
            <Section title="Net Zero Milestone Timeline" sub="Interim and long-term milestones with reduction targets">
              {d.milestones.map((m,i)=>(
                <div key={i} style={{display:'flex',gap:16,marginBottom:16,alignItems:'flex-start'}}>
                  <div style={{minWidth:50,textAlign:'center'}}>
                    <div style={{background:m.status==='On Track'?'#10b981':m.status==='In Progress'?'#3b82f6':'#e5e7eb',color:m.status==='Planned'?'#6b7280':'#fff',borderRadius:'50%',width:44,height:44,display:'flex',alignItems:'center',justifyContent:'center',fontWeight:700,fontSize:12}}>{m.year}</div>
                    {i<d.milestones.length-1&&<div style={{width:2,height:24,background:'#e5e7eb',margin:'4px auto'}}/>}
                  </div>
                  <div style={{flex:1,padding:'10px 14px',background:'#f9fafb',borderRadius:8,border:'1px solid #e5e7eb'}}>
                    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                      <span style={{fontWeight:600,fontSize:13}}>{m.target}</span>
                      <span style={{background:statusColor(m.status)==='#10b981'?'#d1fae5':statusColor(m.status)==='#f59e0b'?'#fff7ed':'#f3f4f6',color:statusColor(m.status),padding:'2px 8px',borderRadius:12,fontSize:11,fontWeight:600}}>{m.status}</span>
                    </div>
                    <div style={{marginTop:6,height:6,background:'#e5e7eb',borderRadius:3}}>
                      <div style={{height:6,background:'#10b981',borderRadius:3,width:`${m.reduction}%`}}/>
                    </div>
                    <div style={{fontSize:11,color:'#6b7280',marginTop:4}}>{m.reduction}% cumulative reduction target</div>
                  </div>
                </div>
              ))}
            </Section>
            <Row gap={20}>
              <div style={{flex:1}}>
                <Section title="Residual Emissions at Net Zero" sub="Breakdown of remaining emissions requiring offsets in 2050">
                  <ResponsiveContainer width="100%" height={220}>
                    <PieChart>
                      <Pie data={d.residual_emissions} cx="50%" cy="50%" innerRadius={45} outerRadius={80} dataKey="value" label={({name,percent})=>`${(percent*100).toFixed(0)}%`} style={{fontSize:10}}>
                        {d.residual_emissions.map((_,i)=><Cell key={i} fill={PIE_COLORS[i%PIE_COLORS.length]}/>)}
                      </Pie>
                      <Tooltip contentStyle={TT}/>
                      <Legend style={{fontSize:11}}/>
                    </PieChart>
                  </ResponsiveContainer>
                </Section>
              </div>
              <div style={{flex:1}}>
                <Section title="BVCM Plan Summary" sub="Beyond Value Chain Mitigation commitments">
                  <div style={{padding:16,background:'#f0fdf4',borderRadius:8,border:'1px solid #a7f3d0',fontSize:13,lineHeight:1.6,color:'#374151'}}>{d.bvcm_summary}</div>
                </Section>
              </div>
            </Row>
          </>
        )}
      </div>
    </div>
  );
}
