/**
 * ESGDataQualityPage.jsx
 * Route: /esg-data-quality
 * Badge: DQ · ESG · E34
 *
 * Tab 1 — Quality Overview   POST /api/v1/esg-data-quality/report
 * Tab 2 — Indicators         POST /api/v1/esg-data-quality/report
 * Tab 3 — Provider Divergence
 * Tab 4 — BCBS 239
 * Tab 5 — Improvement Plan
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  AreaChart, Area, PieChart, Pie, Cell,
} from 'recharts';

const rng = (seed) => { let s = seed; return () => { s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 0xffffffff; }; };

const Section = ({title,sub,children})=><div style={{background:'#fff',border:'1px solid #e5e7eb',borderRadius:8,padding:24,marginBottom:20}}><div style={{marginBottom:16}}><h3 style={{margin:0,fontWeight:700,fontSize:16}}>{title}</h3>{sub&&<p style={{margin:'4px 0 0',color:'#6b7280',fontSize:13}}>{sub}</p>}</div>{children}</div>;
const KpiCard = ({label,value,sub,color='#10b981'})=><div style={{flex:1,minWidth:160,background:'#f9fafb',border:'1px solid #e5e7eb',borderRadius:8,padding:16}}><div style={{fontSize:12,color:'#6b7280',marginBottom:4}}>{label}</div><div style={{fontSize:22,fontWeight:700,color}}>{value}</div>{sub&&<div style={{fontSize:11,color:'#9ca3af',marginTop:2}}>{sub}</div>}</div>;
const Row = ({children,gap=12})=><div style={{display:'flex',flexWrap:'wrap',gap}}>{children}</div>;
const Inp = ({label,...p})=><label style={{display:'flex',flexDirection:'column',gap:4,fontSize:13,color:'#374151'}}>{label}<input {...p} style={{padding:'6px 10px',border:'1px solid #d1d5db',borderRadius:6,fontSize:13,...p.style}}/></label>;
const Sel = ({label,options,...p})=><label style={{display:'flex',flexDirection:'column',gap:4,fontSize:13,color:'#374151'}}>{label}<select {...p} style={{padding:'6px 10px',border:'1px solid #d1d5db',borderRadius:6,fontSize:13,...p.style}}>{options.map(o=><option key={o.value??o} value={o.value??o}>{o.label??o}</option>)}</select></label>;
const Btn = ({children,...p})=><button {...p} style={{padding:'8px 18px',background:'#10b981',color:'#fff',border:'none',borderRadius:6,fontWeight:600,fontSize:13,cursor:'pointer',...p.style}}>{children}</button>;

const TABS = ['Quality Overview','Indicators','Provider Divergence','BCBS 239','Improvement Plan'];
const PERIODS = [{value:'2024',label:'FY 2024'},{value:'2023',label:'FY 2023'},{value:'2022',label:'FY 2022'}];
const TT = {backgroundColor:'#fff',border:'1px solid #e5e7eb',fontSize:11};
const PIE_COLORS = ['#10b981','#f59e0b','#ef4444','#3b82f6','#8b5cf6'];

const BCBS_PRINCIPLES = [
  {id:'P1',name:'Governance',cat:'Overarching'},
  {id:'P2',name:'Data architecture',cat:'Overarching'},
  {id:'P3',name:'Accuracy & Integrity',cat:'Risk Data Aggregation'},
  {id:'P4',name:'Completeness',cat:'Risk Data Aggregation'},
  {id:'P5',name:'Timeliness',cat:'Risk Data Aggregation'},
  {id:'P6',name:'Adaptability',cat:'Risk Data Aggregation'},
  {id:'P7',name:'Accuracy (reporting)',cat:'Risk Reporting'},
  {id:'P8',name:'Comprehensiveness',cat:'Risk Reporting'},
  {id:'P9',name:'Clarity & Usefulness',cat:'Risk Reporting'},
  {id:'P10',name:'Frequency',cat:'Risk Reporting'},
  {id:'P11',name:'Distribution',cat:'Risk Reporting'},
  {id:'P12',name:'Supervisory review',cat:'Supervisory'},
  {id:'P13',name:'Remedial actions',cat:'Supervisory'},
  {id:'P14',name:'Home-host cooperation',cat:'Supervisory'},
];

function buildFallback(seed) {
  const r = rng(seed);
  const indicators = [
    {indicator:'GHG Emissions (Scope 1)',pillar:'E',source:'CDP',coverage:Math.round(70+r()*25),quality:Math.round(60+r()*35),dqs:Math.ceil(r()*3+1),material:true},
    {indicator:'GHG Emissions (Scope 2)',pillar:'E',source:'Reported',coverage:Math.round(65+r()*30),quality:Math.round(55+r()*40),dqs:Math.ceil(r()*3+1),material:true},
    {indicator:'Energy Consumption',pillar:'E',source:'Utility bills',coverage:Math.round(60+r()*35),quality:Math.round(50+r()*45),dqs:Math.ceil(r()*3+1),material:true},
    {indicator:'Water Withdrawal',pillar:'E',source:'Internal',coverage:Math.round(45+r()*40),quality:Math.round(40+r()*50),dqs:Math.ceil(r()*4+1),material:false},
    {indicator:'Board Diversity',pillar:'G',source:'Annual Report',coverage:Math.round(80+r()*18),quality:Math.round(70+r()*28),dqs:1,material:true},
    {indicator:'CEO Pay Ratio',pillar:'G',source:'Proxy Statement',coverage:Math.round(70+r()*25),quality:Math.round(60+r()*35),dqs:2,material:true},
    {indicator:'Employee Turnover',pillar:'S',source:'HR System',coverage:Math.round(55+r()*40),quality:Math.round(45+r()*50),dqs:Math.ceil(r()*3+1),material:false},
    {indicator:'Health & Safety LTIFR',pillar:'S',source:'HSE Report',coverage:Math.round(75+r()*20),quality:Math.round(65+r()*30),dqs:2,material:true},
    {indicator:'Supply Chain Audit',pillar:'S',source:'Third Party',coverage:Math.round(30+r()*40),quality:Math.round(25+r()*50),dqs:Math.ceil(r()*4+2),material:false},
    {indicator:'Biodiversity Impact',pillar:'E',source:'Estimated',coverage:Math.round(20+r()*35),quality:Math.round(15+r()*45),dqs:5,material:false},
  ];
  const dqsDist = [1,2,3,4,5].map(d=>({dqs:`DQS ${d}`,count:indicators.filter(i=>i.dqs===d).length}));
  const estBkdn = [{name:'Verified',value:Math.round(35+r()*25)},{name:'Calculated',value:Math.round(25+r()*20)},{name:'Estimated',value:Math.round(15+r()*20)},{name:'Proxied',value:Math.round(5+r()*15)}];
  const pillarScores = {E:Math.round(45+r()*40),S:Math.round(40+r()*45),G:Math.round(55+r()*35)};
  const bcbsScores = BCBS_PRINCIPLES.map(p=>({...p,score:Math.round(30+r()*65),status:r()>0.5?'Green':r()>0.25?'Amber':'Red'}));
  const providers = ['Bloomberg','MSCI','Sustainalytics'];
  const pvdData = ['Environmental','Social','Governance'].map(pillar=>({
    pillar,
    Bloomberg: Math.round(40+r()*45),
    MSCI: Math.round(35+r()*50),
    Sustainalytics: Math.round(38+r()*48),
  }));
  const gaps = [
    {gap:'Scope 3 category data missing',severity:'High',effort:3,impact:5},
    {gap:'Water data estimated — no metering',severity:'Medium',effort:2,impact:3},
    {gap:'No independent verification for E data',severity:'High',effort:4,impact:5},
    {gap:'Supply chain coverage <40%',severity:'High',effort:5,impact:4},
    {gap:'Biodiversity metrics absent',severity:'Medium',effort:4,impact:3},
  ];
  const radarData = ['Environmental','Social','Governance','Governance2','Coverage','Timeliness'].map(d=>({
    metric:d.replace('2',''),
    score:Math.round(35+r()*55),
  }));
  return {
    overall_quality: Math.round(45+r()*40),
    overall_coverage: Math.round(50+r()*40),
    bcbs_score: Math.round(40+r()*45),
    estimated_pct: Math.round(15+r()*35),
    pillar_scores: pillarScores,
    quality_tier: ['Insufficient','Basic','Intermediate','Advanced'][Math.floor(r()*4)],
    indicators,
    dqs_dist: dqsDist,
    est_breakdown: estBkdn,
    pvd_data: pvdData,
    bcbs_scores: bcbsScores,
    bcbs_agg: Math.round(40+r()*40),
    gaps,
    radar_data: radarData,
    improvement_roadmap: YEARS_ROADMAP.map((yr,i)=>({year:yr,quality:Math.min(95,Math.round(45+r()*10+i*8))})),
    coverage_bar: [{pillar:'Environmental',coverage:Math.round(45+r()*40)},{pillar:'Social',coverage:Math.round(40+r()*45)},{pillar:'Governance',coverage:Math.round(60+r()*30)}],
  };
}

const YEARS_ROADMAP = [2024,2025,2026,2027,2028];

export default function ESGDataQualityPage() {
  const [tab, setTab] = useState(0);
  const [form, setForm] = useState({entity_id:'CORP-001',entity_name:'Acme Corp',reporting_period:'2024'});
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const upd = (k,v) => setForm(f=>({...f,[k]:v}));

  const run = async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/esg-data-quality/report', form);
      setData(res.data);
    } catch {
      const seed = form.entity_id.split('').reduce((a,c)=>a+c.charCodeAt(0),0)||42;
      setData(buildFallback(seed));
    }
    setLoading(false);
  };

  useEffect(()=>{ run(); },[]);

  const d = data || buildFallback(42);
  const scoreColor = s => s>=70?'#10b981':s>=50?'#f59e0b':'#ef4444';
  const tlColor = s => s==='Green'?'#10b981':s==='Amber'?'#f59e0b':'#ef4444';
  const sevColor = s => s==='High'?'#ef4444':s==='Medium'?'#f59e0b':'#10b981';

  return (
    <div style={{fontFamily:'Inter,system-ui,sans-serif',background:'#f9fafb',minHeight:'100vh',padding:24}}>
      <div style={{maxWidth:1100,margin:'0 auto'}}>
        {/* Header */}
        <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:20}}>
          <div>
            <div style={{display:'flex',alignItems:'center',gap:8}}>
              <h1 style={{margin:0,fontSize:22,fontWeight:700}}>ESG Data Quality & Coverage</h1>
              <span style={{background:'#d1fae5',color:'#065f46',padding:'2px 10px',borderRadius:20,fontSize:11,fontWeight:700}}>DQ · ESG · E34</span>
            </div>
            <p style={{margin:'4px 0 0',color:'#6b7280',fontSize:13}}>ESG indicator quality, coverage, provider divergence, BCBS 239 data governance</p>
          </div>
        </div>

        {/* KPIs */}
        <Row gap={12} style={{marginBottom:20}}>
          <KpiCard label="Overall Quality Score" value={`${d.overall_quality}/100`} sub="Composite data quality" color={scoreColor(d.overall_quality)}/>
          <KpiCard label="Overall Coverage" value={`${d.overall_coverage}%`} sub="Indicators with data" color={d.overall_coverage>=70?'#10b981':'#f59e0b'}/>
          <KpiCard label="BCBS 239 Score" value={`${d.bcbs_score}/100`} sub="Data governance principles" color={scoreColor(d.bcbs_score)}/>
          <KpiCard label="Estimated Indicators" value={`${d.estimated_pct}%`} sub="Proxied or estimated data" color={d.estimated_pct>30?'#ef4444':'#f59e0b'}/>
        </Row>

        {/* Tab bar */}
        <div style={{display:'flex',gap:4,marginBottom:20,borderBottom:'2px solid #e5e7eb'}}>
          {TABS.map((t,i)=>(
            <button key={t} onClick={()=>setTab(i)} style={{padding:'8px 18px',border:'none',borderBottom:tab===i?'2px solid #10b981':'2px solid transparent',background:'none',fontWeight:tab===i?700:400,color:tab===i?'#10b981':'#6b7280',cursor:'pointer',fontSize:13,marginBottom:-2}}>{t}</button>
          ))}
        </div>

        {/* Tab 0 — Quality Overview */}
        {tab===0 && (
          <>
            <Section title="Entity Configuration" sub="Run quality assessment for a given entity and reporting period">
              <Row gap={12} style={{marginBottom:16}}>
                <Inp label="Entity ID" value={form.entity_id} onChange={e=>upd('entity_id',e.target.value)}/>
                <Inp label="Entity Name" value={form.entity_name} onChange={e=>upd('entity_name',e.target.value)}/>
                <Sel label="Reporting Period" options={PERIODS} value={form.reporting_period} onChange={e=>upd('reporting_period',e.target.value)}/>
                <div style={{display:'flex',alignItems:'flex-end'}}><Btn onClick={run} style={{opacity:loading?0.6:1}}>{loading?'Running…':'Run Assessment'}</Btn></div>
              </Row>
            </Section>
            <Row gap={16}>
              {['E','S','G'].map(pillar=>(
                <div key={pillar} style={{flex:1,padding:20,background:'#f9fafb',borderRadius:8,border:'1px solid #e5e7eb',textAlign:'center'}}>
                  <div style={{fontSize:13,color:'#6b7280',marginBottom:4}}>{pillar==='E'?'Environmental':pillar==='S'?'Social':'Governance'} Score</div>
                  <div style={{fontSize:32,fontWeight:700,color:scoreColor(d.pillar_scores[pillar])}}>{d.pillar_scores[pillar]}</div>
                  <div style={{height:6,background:'#e5e7eb',borderRadius:3,marginTop:8}}><div style={{height:6,background:scoreColor(d.pillar_scores[pillar]),borderRadius:3,width:`${d.pillar_scores[pillar]}%`}}/></div>
                </div>
              ))}
              <div style={{flex:1,padding:20,background:'#f9fafb',borderRadius:8,border:'1px solid #e5e7eb',textAlign:'center'}}>
                <div style={{fontSize:13,color:'#6b7280',marginBottom:4}}>Quality Tier</div>
                <div style={{fontSize:20,fontWeight:700,color:'#374151'}}>{d.quality_tier}</div>
                <span style={{background:d.quality_tier==='Advanced'?'#d1fae5':d.quality_tier==='Intermediate'?'#dbeafe':d.quality_tier==='Basic'?'#fff7ed':'#fee2e2',color:d.quality_tier==='Advanced'?'#065f46':d.quality_tier==='Intermediate'?'#1e40af':d.quality_tier==='Basic'?'#92400e':'#991b1b',padding:'4px 12px',borderRadius:20,fontSize:11,fontWeight:700}}>{d.quality_tier}</span>
              </div>
            </Row>
            <Row gap={20} style={{marginTop:20}}>
              <div style={{flex:1}}>
                <Section title="E/S/G Quality Radar" sub="Multi-dimensional quality profile">
                  <ResponsiveContainer width="100%" height={240}>
                    <RadarChart data={d.radar_data}>
                      <PolarGrid/>
                      <PolarAngleAxis dataKey="metric" style={{fontSize:11}}/>
                      <Radar name="Quality" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.3}/>
                      <Tooltip contentStyle={TT}/>
                    </RadarChart>
                  </ResponsiveContainer>
                </Section>
              </div>
              <div style={{flex:1}}>
                <Section title="Coverage by Pillar" sub="Indicator coverage percentage">
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={d.coverage_bar}>
                      <CartesianGrid strokeDasharray="3 3"/>
                      <XAxis dataKey="pillar" style={{fontSize:12}}/>
                      <YAxis domain={[0,100]} tickFormatter={v=>`${v}%`} style={{fontSize:11}}/>
                      <Tooltip contentStyle={TT} formatter={v=>`${v}%`}/>
                      <Bar dataKey="coverage" name="Coverage" radius={[4,4,0,0]}>
                        {d.coverage_bar.map((_,i)=><Cell key={i} fill={['#10b981','#3b82f6','#8b5cf6'][i]}/>)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </div>
            </Row>
          </>
        )}

        {/* Tab 1 — Indicators */}
        {tab===1 && (
          <>
            <Section title="Per-Indicator Quality Table" sub="Coverage, quality score, DQS and materiality by indicator">
              <div style={{overflowX:'auto'}}>
                <table style={{width:'100%',borderCollapse:'collapse',fontSize:12}}>
                  <thead><tr style={{background:'#f9fafb'}}>{['Indicator','Pillar','Source','Coverage','Quality','DQS','Material'].map(h=><th key={h} style={{padding:'7px 10px',textAlign:'left',fontWeight:600,borderBottom:'1px solid #e5e7eb',whiteSpace:'nowrap'}}>{h}</th>)}</tr></thead>
                  <tbody>{d.indicators.map((ind,i)=><tr key={i} style={{borderBottom:'1px solid #f3f4f6',background:i%2===0?'#fff':'#fafafa'}}>
                    <td style={{padding:'7px 10px',fontWeight:500}}>{ind.indicator}</td>
                    <td style={{padding:'7px 10px'}}><span style={{background:ind.pillar==='E'?'#d1fae5':ind.pillar==='S'?'#dbeafe':'#ede9fe',color:ind.pillar==='E'?'#065f46':ind.pillar==='S'?'#1e40af':'#5b21b6',padding:'2px 8px',borderRadius:12,fontSize:10,fontWeight:700}}>{ind.pillar}</span></td>
                    <td style={{padding:'7px 10px',color:'#6b7280'}}>{ind.source}</td>
                    <td style={{padding:'7px 10px'}}>
                      <div style={{display:'flex',alignItems:'center',gap:6}}>
                        <div style={{height:6,width:60,background:'#e5e7eb',borderRadius:3}}><div style={{height:6,background:scoreColor(ind.coverage),borderRadius:3,width:`${ind.coverage}%`}}/></div>
                        <span style={{fontSize:11}}>{ind.coverage}%</span>
                      </div>
                    </td>
                    <td style={{padding:'7px 10px',fontWeight:600,color:scoreColor(ind.quality)}}>{ind.quality}</td>
                    <td style={{padding:'7px 10px'}}><span style={{background:ind.dqs<=2?'#d1fae5':ind.dqs<=3?'#fef3c7':'#fee2e2',color:ind.dqs<=2?'#065f46':ind.dqs<=3?'#92400e':'#991b1b',padding:'2px 6px',borderRadius:8,fontSize:10,fontWeight:700}}>DQS-{ind.dqs}</span></td>
                    <td style={{padding:'7px 10px'}}>{ind.material?'✅':'—'}</td>
                  </tr>)}</tbody>
                </table>
              </div>
            </Section>
            <Row gap={20}>
              <div style={{flex:1}}>
                <Section title="DQS Distribution" sub="PCAF Data Quality Score levels (1=best, 5=worst)">
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={d.dqs_dist}>
                      <CartesianGrid strokeDasharray="3 3"/>
                      <XAxis dataKey="dqs" style={{fontSize:12}}/>
                      <YAxis style={{fontSize:11}}/>
                      <Tooltip contentStyle={TT}/>
                      <Bar dataKey="count" name="Indicators" radius={[4,4,0,0]}>
                        {d.dqs_dist.map((_,i)=><Cell key={i} fill={['#10b981','#84cc16','#f59e0b','#f97316','#ef4444'][i]}/>)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </div>
              <div style={{flex:1}}>
                <Section title="Estimation Method Breakdown" sub="How indicators are sourced or derived">
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={d.est_breakdown} cx="50%" cy="50%" innerRadius={40} outerRadius={72} dataKey="value" label={({name,percent})=>`${name} ${(percent*100).toFixed(0)}%`} style={{fontSize:10}}>
                        {d.est_breakdown.map((_,i)=><Cell key={i} fill={PIE_COLORS[i]}/>)}
                      </Pie>
                      <Tooltip contentStyle={TT}/>
                    </PieChart>
                  </ResponsiveContainer>
                </Section>
              </div>
            </Row>
          </>
        )}

        {/* Tab 2 — Provider Divergence */}
        {tab===2 && (
          <>
            <Section title="Bloomberg vs MSCI vs Sustainalytics — Score Comparison" sub="ESG ratings divergence by pillar across major data providers">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={d.pvd_data}>
                  <CartesianGrid strokeDasharray="3 3"/>
                  <XAxis dataKey="pillar" style={{fontSize:12}}/>
                  <YAxis domain={[0,100]} style={{fontSize:11}}/>
                  <Tooltip contentStyle={TT}/>
                  <Legend/>
                  <Bar dataKey="Bloomberg" fill="#10b981" radius={[4,4,0,0]}/>
                  <Bar dataKey="MSCI" fill="#3b82f6" radius={[4,4,0,0]}/>
                  <Bar dataKey="Sustainalytics" fill="#8b5cf6" radius={[4,4,0,0]}/>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Divergence Heatmap" sub="Colour-coded score divergence by pillar and provider">
              <table style={{width:'100%',borderCollapse:'collapse',fontSize:13}}>
                <thead><tr style={{background:'#f9fafb'}}>{['Pillar','Bloomberg','MSCI','Sustainalytics','Max Divergence'].map(h=><th key={h} style={{padding:'8px 12px',textAlign:'left',fontWeight:600,borderBottom:'1px solid #e5e7eb'}}>{h}</th>)}</tr></thead>
                <tbody>{d.pvd_data.map((row,i)=>{
                  const vals = [row.Bloomberg,row.MSCI,row.Sustainalytics];
                  const div = Math.max(...vals)-Math.min(...vals);
                  const divColor = div>25?'#ef4444':div>15?'#f59e0b':'#10b981';
                  return <tr key={i} style={{borderBottom:'1px solid #f3f4f6'}}>
                    <td style={{padding:'8px 12px',fontWeight:600}}>{row.pillar}</td>
                    {vals.map((v,j)=><td key={j} style={{padding:'8px 12px',background:`rgba(16,185,129,${v/200})`,fontWeight:600}}>{v}</td>)}
                    <td style={{padding:'8px 12px',color:divColor,fontWeight:700}}>{div} pts</td>
                  </tr>;
                })}</tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 3 — BCBS 239 */}
        {tab===3 && (
          <>
            <Section title="BCBS 239 Principles Assessment" sub="14 principles for effective risk data aggregation and risk reporting">
              <div style={{overflowX:'auto'}}>
                <table style={{width:'100%',borderCollapse:'collapse',fontSize:12}}>
                  <thead><tr style={{background:'#f9fafb'}}>{['ID','Principle','Category','Score','Status'].map(h=><th key={h} style={{padding:'7px 10px',textAlign:'left',fontWeight:600,borderBottom:'1px solid #e5e7eb'}}>{h}</th>)}</tr></thead>
                  <tbody>{d.bcbs_scores.map((p,i)=><tr key={i} style={{borderBottom:'1px solid #f3f4f6',background:i%2===0?'#fff':'#fafafa'}}>
                    <td style={{padding:'7px 10px',fontWeight:700,color:'#6b7280'}}>{p.id}</td>
                    <td style={{padding:'7px 10px',fontWeight:500}}>{p.name}</td>
                    <td style={{padding:'7px 10px',color:'#6b7280',fontSize:11}}>{p.cat}</td>
                    <td style={{padding:'7px 10px'}}>
                      <div style={{display:'flex',alignItems:'center',gap:6}}>
                        <div style={{height:6,width:70,background:'#e5e7eb',borderRadius:3}}><div style={{height:6,background:tlColor(p.status),borderRadius:3,width:`${p.score}%`}}/></div>
                        <span style={{fontWeight:600,fontSize:11}}>{p.score}</span>
                      </div>
                    </td>
                    <td style={{padding:'7px 10px'}}><span style={{display:'inline-block',width:10,height:10,borderRadius:'50%',background:tlColor(p.status),marginRight:6}}/>{p.status}</td>
                  </tr>)}</tbody>
                </table>
              </div>
            </Section>
            <Row gap={20}>
              <div style={{flex:1}}>
                <Section title="Aggregate BCBS Score" sub="Composite governance score">
                  <div style={{textAlign:'center',padding:20}}>
                    <div style={{fontSize:48,fontWeight:700,color:scoreColor(d.bcbs_agg)}}>{d.bcbs_agg}</div>
                    <div style={{fontSize:13,color:'#6b7280',marginTop:4}}>out of 100 — BCBS 239 Compliance</div>
                    <div style={{height:12,background:'#e5e7eb',borderRadius:6,marginTop:16}}><div style={{height:12,background:scoreColor(d.bcbs_agg),borderRadius:6,width:`${d.bcbs_agg}%`,transition:'width 0.5s'}}/></div>
                  </div>
                </Section>
              </div>
              <div style={{flex:1}}>
                <Section title="Data Governance Maturity" sub="Key governance dimensions">
                  <ResponsiveContainer width="100%" height={200}>
                    <RadarChart data={d.radar_data.slice(0,6)}>
                      <PolarGrid/>
                      <PolarAngleAxis dataKey="metric" style={{fontSize:10}}/>
                      <Radar name="Score" dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.25}/>
                      <Tooltip contentStyle={TT}/>
                    </RadarChart>
                  </ResponsiveContainer>
                </Section>
              </div>
            </Row>
          </>
        )}

        {/* Tab 4 — Improvement Plan */}
        {tab===4 && (
          <>
            <Section title="Data Gaps by Severity" sub="Identified data quality and coverage gaps prioritised by severity">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={d.gaps} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3"/>
                  <XAxis type="number" domain={[0,6]} style={{fontSize:11}}/>
                  <YAxis type="category" dataKey="gap" width={200} style={{fontSize:10}}/>
                  <Tooltip contentStyle={TT}/>
                  <Legend/>
                  <Bar dataKey="effort" name="Effort (1-5)" fill="#f59e0b" radius={[0,4,4,0]}/>
                  <Bar dataKey="impact" name="Impact (1-5)" fill="#10b981" radius={[0,4,4,0]}/>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Material Gaps — Priority Actions" sub="Highest priority remediation actions ordered by impact">
              {d.gaps.map((g,i)=>(
                <div key={i} style={{display:'flex',gap:12,padding:'12px 14px',background:'#f9fafb',borderRadius:8,marginBottom:8,border:'1px solid #e5e7eb',alignItems:'flex-start'}}>
                  <span style={{background:sevColor(g.severity),color:'#fff',borderRadius:'50%',width:22,height:22,display:'flex',alignItems:'center',justifyContent:'center',fontSize:11,fontWeight:700,flexShrink:0}}>{i+1}</span>
                  <div style={{flex:1}}>
                    <div style={{fontWeight:600,fontSize:13}}>{g.gap}</div>
                    <div style={{fontSize:12,color:'#6b7280',marginTop:2}}>Severity: <span style={{color:sevColor(g.severity),fontWeight:600}}>{g.severity}</span> · Effort: {g.effort}/5 · Impact: {g.impact}/5</div>
                  </div>
                </div>
              ))}
            </Section>
            <Section title="Quality Improvement Roadmap" sub="Projected quality score improvement over implementation horizon">
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={d.improvement_roadmap}>
                  <CartesianGrid strokeDasharray="3 3"/>
                  <XAxis dataKey="year" style={{fontSize:12}}/>
                  <YAxis domain={[0,100]} tickFormatter={v=>`${v}`} style={{fontSize:11}}/>
                  <Tooltip contentStyle={TT} formatter={v=>`${v}/100`}/>
                  <ReferenceLine y={75} stroke="#10b981" strokeDasharray="4 4" label={{value:'Target 75',fill:'#10b981',fontSize:10}}/>
                  <Line type="monotone" dataKey="quality" name="Quality Score" stroke="#10b981" strokeWidth={2} dot={{r:5,fill:'#10b981'}}/>
                </LineChart>
              </ResponsiveContainer>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
