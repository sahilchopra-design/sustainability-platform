/**
 * TNFDLEAPPage.jsx
 * Route: /tnfd-leap
 * Badge: TNFD · LEAP · E32
 *
 * Tab 1 — Locate       POST /api/v1/tnfd-leap/assess
 * Tab 2 — Evaluate     POST /api/v1/tnfd-leap/assess
 * Tab 3 — Assess       POST /api/v1/tnfd-leap/assess
 * Tab 4 — Prepare      POST /api/v1/tnfd-leap/assess
 * Tab 5 — Full LEAP    POST /api/v1/tnfd-leap/assess
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

const TABS = ['Locate','Evaluate','Assess','Prepare','Full LEAP'];
const SECTORS = [{value:'agriculture',label:'Agriculture'},{value:'forestry',label:'Forestry'},{value:'mining',label:'Mining'},{value:'manufacturing',label:'Manufacturing'},{value:'utilities',label:'Utilities'},{value:'construction',label:'Construction'},{value:'finance',label:'Financial Services'},{value:'real_estate',label:'Real Estate'}];
const COLORS = ['#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6','#06b6d4','#ec4899','#84cc16'];
const TT = {backgroundColor:'#fff',border:'1px solid #e5e7eb',fontSize:11};

function buildFallback(seed) {
  const r = rng(seed);
  const ecosvcs = ['Provisioning','Regulating','Habitat','Cultural','Water Cycle','Climate Reg','Soil Health','Pollination'];
  const impactDrivers = ['Land Use','Water Use','GHG Emissions','Pollution','Species Exploitation','Invasive Species','Climate Change','Soil Degradation'];
  const regulations = ['ESRS E4','EU Taxonomy','CSRD','SFDR','GRI 304'];
  return {
    overall_leap_score: Math.round(55 + r() * 30),
    maturity: ['Initial','Developing','Established','Advanced'][Math.floor(r()*4)],
    risk_magnitude: ['Low','Moderate','High','Very High'][Math.floor(r()*4)],
    disclosure_completeness: Math.round(40 + r() * 50),
    locate_score: Math.round(50 + r() * 40),
    priority_locations: [
      {location:'Amazon Basin',biome:'Tropical Forest',sensitivity:'Very High'},
      {location:'Cerrado Savannah',biome:'Savannah',sensitivity:'High'},
      {location:'Atlantic Coast',biome:'Marine Coastal',sensitivity:'High'},
      {location:'Pantanal',biome:'Wetland',sensitivity:'Very High'},
    ],
    value_chain: [
      {scope:'Upstream',coverage: Math.round(40+r()*40)},
      {scope:'Operations',coverage: Math.round(60+r()*35)},
      {scope:'Downstream',coverage: Math.round(25+r()*40)},
    ],
    sensitive_ecosystems: ['Tropical Rainforest – High dependency','Freshwater Wetland – Critical habitat','Coastal Mangrove – Erosion buffer','Grassland – Pollination corridor'],
    encore_scores: ecosvcs.map(s=>({service:s.substring(0,12),score:Math.round(30+r()*65)})),
    impact_drivers: impactDrivers.map(d=>({driver:d.substring(0,14),magnitude:Math.round(10+r()*85)})),
    ecosystem_condition: [{biome:'Forest',condition:'Declining',index:Math.round(40+r()*30)},{biome:'Wetland',condition:'Stable',index:Math.round(55+r()*30)},{biome:'Marine',condition:'Improving',index:Math.round(60+r()*30)}],
    material_risks: [
      {risk:'Water availability shock',type:'Physical',horizon:'Near',likelihood:'High',magnitude:'High'},
      {risk:'Biodiversity regulation change',type:'Transition',horizon:'Medium',likelihood:'Medium',magnitude:'High'},
      {risk:'Supply chain nature dependency',type:'Physical',horizon:'Near',likelihood:'High',magnitude:'Moderate'},
      {risk:'Ecosystem service loss',type:'Physical',horizon:'Long',likelihood:'Medium',magnitude:'Very High'},
    ],
    opportunities: ['Nature-based solutions investment','Sustainable sourcing premium','Green finance access','Ecosystem service payments'],
    risk_vs_opp: [{name:'Material Risks',risk:Math.round(60+r()*30),opp:Math.round(40+r()*40)},{name:'Near-Term',risk:Math.round(70+r()*25),opp:Math.round(35+r()*40)},{name:'Long-Term',risk:Math.round(50+r()*40),opp:Math.round(55+r()*35)}],
    strategy_responses: ['Transition to regenerative agriculture','Implement no-deforestation policy','Water stewardship programme','Biodiversity offset strategy'],
    nature_targets: [
      {target:'Zero net deforestation by 2030',progress:35},
      {target:'30% water use reduction',progress:52},
      {target:'50% sustainable sourcing',progress:61},
      {target:'Net positive biodiversity impact',progress:18},
    ],
    disclosure_breakdown: [{name:'Complete',value:Math.round(30+r()*30)},{name:'Partial',value:Math.round(20+r()*25)},{name:'Missing',value:Math.round(10+r()*25)}],
    priority_actions: ['Conduct site-level biodiversity assessment','Engage tier-1 suppliers on nature policy','Develop internal carbon & nature pricing','Commission TNFD-aligned reporting',  'Establish Nature Advisory Committee'],
    leap_breakdown: [{step:'Locate',score:Math.round(50+r()*40)},{step:'Evaluate',score:Math.round(45+r()*45)},{step:'Assess',score:Math.round(40+r()*50)},{step:'Prepare',score:Math.round(35+r()*50)}],
    cross_framework: regulations.map(f=>({framework:f,aligned:r()>0.4?'Yes':'Partial',gaps:Math.round(r()*4)})),
  };
}

export default function TNFDLEAPPage() {
  const [tab, setTab] = useState(0);
  const [form, setForm] = useState({entity_id:'ENT-001',sector:'agriculture',reporting_period:'2024'});
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const upd = (k,v) => setForm(f=>({...f,[k]:v}));

  const run = async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/tnfd-leap/assess', form);
      setData(res.data);
    } catch {
      const seed = form.entity_id.split('').reduce((a,c)=>a+c.charCodeAt(0),0);
      setData(buildFallback(seed || 42));
    }
    setLoading(false);
  };

  useEffect(()=>{ run(); },[]);

  const d = data || buildFallback(42);
  const riskColor = m => m==='Very High'?'#ef4444':m==='High'?'#f59e0b':m==='Moderate'?'#3b82f6':'#10b981';
  const PIE_COLORS = ['#10b981','#f59e0b','#ef4444'];

  return (
    <div style={{fontFamily:'Inter,system-ui,sans-serif',background:'#f9fafb',minHeight:'100vh',padding:24}}>
      <div style={{maxWidth:1100,margin:'0 auto'}}>
        {/* Header */}
        <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:20}}>
          <div>
            <div style={{display:'flex',alignItems:'center',gap:8}}>
              <h1 style={{margin:0,fontSize:22,fontWeight:700}}>TNFD LEAP Process Assessment</h1>
              <span style={{background:'#d1fae5',color:'#065f46',padding:'2px 10px',borderRadius:20,fontSize:11,fontWeight:700}}>TNFD · LEAP · E32</span>
            </div>
            <p style={{margin:'4px 0 0',color:'#6b7280',fontSize:13}}>Locate · Evaluate · Assess · Prepare — nature risk & opportunity framework</p>
          </div>
        </div>

        {/* KPIs */}
        <Row gap={12} style={{marginBottom:20}}>
          <KpiCard label="Overall LEAP Score" value={`${d.overall_leap_score}/100`} sub="Composite LEAP maturity" color="#10b981"/>
          <KpiCard label="LEAP Maturity" value={d.maturity} sub="Current maturity level" color="#3b82f6"/>
          <KpiCard label="Risk Magnitude" value={d.risk_magnitude} sub="Nature-related risk level" color={riskColor(d.risk_magnitude)}/>
          <KpiCard label="Disclosure Completeness" value={`${d.disclosure_completeness}%`} sub="TNFD recommended disclosures" color="#8b5cf6"/>
        </Row>

        {/* Tab bar */}
        <div style={{display:'flex',gap:4,marginBottom:20,borderBottom:'2px solid #e5e7eb',paddingBottom:0}}>
          {TABS.map((t,i)=>(
            <button key={t} onClick={()=>setTab(i)} style={{padding:'8px 18px',border:'none',borderBottom:tab===i?'2px solid #10b981':'2px solid transparent',background:'none',fontWeight:tab===i?700:400,color:tab===i?'#10b981':'#6b7280',cursor:'pointer',fontSize:13,marginBottom:-2}}>{t}</button>
          ))}
        </div>

        {/* Tab 0 — Locate */}
        {tab===0 && (
          <>
            <Section title="Locate — Where does nature interface with the business?" sub="Identify business units, value chains and assets intersecting with nature">
              <Row gap={12} style={{marginBottom:16}}>
                <Inp label="Entity ID" value={form.entity_id} onChange={e=>upd('entity_id',e.target.value)}/>
                <Sel label="Sector" options={SECTORS} value={form.sector} onChange={e=>upd('sector',e.target.value)}/>
                <Inp label="Reporting Period" value={form.reporting_period} onChange={e=>upd('reporting_period',e.target.value)}/>
                <div style={{display:'flex',alignItems:'flex-end'}}><Btn onClick={run} style={{opacity:loading?0.6:1}}>{loading?'Running…':'Run Assessment'}</Btn></div>
              </Row>
              <Row gap={24}>
                <div style={{flex:1}}>
                  <div style={{marginBottom:8,fontSize:13,fontWeight:600}}>Locate Score</div>
                  <div style={{position:'relative',width:140,height:140,margin:'0 auto'}}>
                    <svg width={140} height={140} viewBox="0 0 140 140">
                      <circle cx={70} cy={70} r={58} fill="none" stroke="#e5e7eb" strokeWidth={12}/>
                      <circle cx={70} cy={70} r={58} fill="none" stroke="#10b981" strokeWidth={12}
                        strokeDasharray={`${(d.locate_score/100)*364} 364`} strokeLinecap="round"
                        transform="rotate(-90 70 70)"/>
                    </svg>
                    <div style={{position:'absolute',top:'50%',left:'50%',transform:'translate(-50%,-50%)',textAlign:'center'}}>
                      <div style={{fontSize:26,fontWeight:700,color:'#10b981'}}>{d.locate_score}</div>
                      <div style={{fontSize:11,color:'#6b7280'}}>/100</div>
                    </div>
                  </div>
                </div>
                <div style={{flex:2}}>
                  <div style={{marginBottom:8,fontSize:13,fontWeight:600}}>Value Chain Coverage</div>
                  <ResponsiveContainer width="100%" height={120}>
                    <BarChart data={d.value_chain} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3"/>
                      <XAxis type="number" domain={[0,100]} tickFormatter={v=>`${v}%`} style={{fontSize:11}}/>
                      <YAxis type="category" dataKey="scope" width={80} style={{fontSize:11}}/>
                      <Tooltip contentStyle={TT} formatter={v=>`${v}%`}/>
                      <Bar dataKey="coverage" fill="#10b981" radius={[0,4,4,0]}/>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Row>
            </Section>
            <Section title="Priority Locations" sub="Locations with highest nature sensitivity intersecting operations">
              <table style={{width:'100%',borderCollapse:'collapse',fontSize:13}}>
                <thead><tr style={{background:'#f9fafb'}}>{['Location','Biome','Sensitivity'].map(h=><th key={h} style={{padding:'8px 12px',textAlign:'left',fontWeight:600,borderBottom:'1px solid #e5e7eb'}}>{h}</th>)}</tr></thead>
                <tbody>{d.priority_locations.map((l,i)=><tr key={i} style={{borderBottom:'1px solid #f3f4f6'}}>
                  <td style={{padding:'8px 12px'}}>{l.location}</td>
                  <td style={{padding:'8px 12px',color:'#6b7280'}}>{l.biome}</td>
                  <td style={{padding:'8px 12px'}}><span style={{background:l.sensitivity==='Very High'?'#fef2f2':l.sensitivity==='High'?'#fff7ed':'#ecfdf5',color:l.sensitivity==='Very High'?'#991b1b':l.sensitivity==='High'?'#92400e':'#065f46',padding:'2px 8px',borderRadius:12,fontSize:11,fontWeight:600}}>{l.sensitivity}</span></td>
                </tr>)}</tbody>
              </table>
            </Section>
            <Section title="Sensitive Ecosystems" sub="Key ecosystems identified within operational footprint">
              {d.sensitive_ecosystems.map((e,i)=><div key={i} style={{padding:'8px 12px',background:'#f0fdf4',borderRadius:6,marginBottom:8,fontSize:13,borderLeft:'3px solid #10b981'}}>{e}</div>)}
            </Section>
          </>
        )}

        {/* Tab 1 — Evaluate */}
        {tab===1 && (
          <>
            <Section title="Evaluate — ENCORE Ecosystem Service Dependencies" sub="Scores reflect degree of business dependency on each ecosystem service (0-100)">
              <ResponsiveContainer width="100%" height={260}>
                <RadarChart data={d.encore_scores}>
                  <PolarGrid/>
                  <PolarAngleAxis dataKey="service" style={{fontSize:11}}/>
                  <Radar name="Dependency" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.3}/>
                  <Tooltip contentStyle={TT}/>
                </RadarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Impact Drivers" sub="Business activities contributing to nature impact by category">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={d.impact_drivers}>
                  <CartesianGrid strokeDasharray="3 3"/>
                  <XAxis dataKey="driver" style={{fontSize:10}} angle={-20} textAnchor="end" height={50}/>
                  <YAxis domain={[0,100]} style={{fontSize:11}}/>
                  <Tooltip contentStyle={TT}/>
                  <Bar dataKey="magnitude" name="Magnitude" radius={[4,4,0,0]}>
                    {d.impact_drivers.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Ecosystem Condition" sub="State of key biomes in operational areas">
              <Row gap={12}>
                {d.ecosystem_condition.map((ec,i)=>(
                  <div key={i} style={{flex:1,padding:16,background:'#f9fafb',borderRadius:8,border:'1px solid #e5e7eb',textAlign:'center'}}>
                    <div style={{fontWeight:700,fontSize:15,marginBottom:4}}>{ec.biome}</div>
                    <div style={{fontSize:24,fontWeight:700,color:ec.condition==='Improving'?'#10b981':ec.condition==='Stable'?'#3b82f6':'#ef4444',marginBottom:4}}>{ec.index}</div>
                    <div style={{fontSize:12,color:'#6b7280'}}>{ec.condition}</div>
                  </div>
                ))}
              </Row>
            </Section>
          </>
        )}

        {/* Tab 2 — Assess */}
        {tab===2 && (
          <>
            <Section title="Assess — Material Nature-Related Risks" sub="Risks identified through LEAP dependency and impact evaluation">
              <table style={{width:'100%',borderCollapse:'collapse',fontSize:13}}>
                <thead><tr style={{background:'#f9fafb'}}>{['Risk','Type','Horizon','Likelihood','Magnitude'].map(h=><th key={h} style={{padding:'8px 12px',textAlign:'left',fontWeight:600,borderBottom:'1px solid #e5e7eb'}}>{h}</th>)}</tr></thead>
                <tbody>{d.material_risks.map((r,i)=><tr key={i} style={{borderBottom:'1px solid #f3f4f6'}}>
                  <td style={{padding:'8px 12px',fontWeight:500}}>{r.risk}</td>
                  <td style={{padding:'8px 12px'}}><span style={{background:r.type==='Physical'?'#eff6ff':'#fff7ed',color:r.type==='Physical'?'#1e40af':'#92400e',padding:'2px 8px',borderRadius:12,fontSize:11}}>{r.type}</span></td>
                  <td style={{padding:'8px 12px',color:'#6b7280'}}>{r.horizon}</td>
                  <td style={{padding:'8px 12px'}}><span style={{color:riskColor(r.likelihood),fontWeight:600}}>{r.likelihood}</span></td>
                  <td style={{padding:'8px 12px'}}><span style={{background:'#f9fafb',border:`1px solid ${riskColor(r.magnitude)}`,color:riskColor(r.magnitude),padding:'2px 8px',borderRadius:12,fontSize:11,fontWeight:600}}>{r.magnitude}</span></td>
                </tr>)}</tbody>
              </table>
            </Section>
            <Section title="Risk vs Opportunity Comparison" sub="Magnitude of material risks against identified opportunities">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={d.risk_vs_opp}>
                  <CartesianGrid strokeDasharray="3 3"/>
                  <XAxis dataKey="name" style={{fontSize:12}}/>
                  <YAxis domain={[0,100]} style={{fontSize:11}}/>
                  <Tooltip contentStyle={TT}/>
                  <Legend/>
                  <Bar dataKey="risk" name="Risk Magnitude" fill="#ef4444" radius={[4,4,0,0]}/>
                  <Bar dataKey="opp" name="Opportunity" fill="#10b981" radius={[4,4,0,0]}/>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Material Opportunities" sub="Nature-positive business opportunities identified">
              {d.opportunities.map((o,i)=><div key={i} style={{padding:'10px 14px',background:'#ecfdf5',borderRadius:6,marginBottom:8,fontSize:13,borderLeft:'3px solid #10b981',color:'#065f46'}}>{o}</div>)}
            </Section>
          </>
        )}

        {/* Tab 3 — Prepare */}
        {tab===3 && (
          <>
            <Section title="Prepare — Strategy Responses" sub="Actions to address material nature risks and capture opportunities">
              {d.strategy_responses.map((s,i)=><div key={i} style={{padding:'10px 14px',background:'#f0fdf4',borderRadius:6,marginBottom:8,fontSize:13,borderLeft:'3px solid #10b981'}}>{s}</div>)}
            </Section>
            <Section title="Nature Targets" sub="Commitments and progress against nature-positive goals">
              {d.nature_targets.map((t,i)=>(
                <div key={i} style={{marginBottom:14}}>
                  <div style={{display:'flex',justifyContent:'space-between',marginBottom:4,fontSize:13}}>
                    <span>{t.target}</span><span style={{fontWeight:700,color:'#10b981'}}>{t.progress}%</span>
                  </div>
                  <div style={{height:8,background:'#e5e7eb',borderRadius:4}}>
                    <div style={{height:8,background:'#10b981',borderRadius:4,width:`${t.progress}%`,transition:'width 0.5s'}}/>
                  </div>
                </div>
              ))}
            </Section>
            <Row gap={20}>
              <div style={{flex:1}}>
                <Section title="Disclosure Completeness" sub="Status of TNFD recommended disclosures">
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={d.disclosure_breakdown} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({name,value})=>`${name}: ${value}%`} labelLine={false} style={{fontSize:11}}>
                        {d.disclosure_breakdown.map((_,i)=><Cell key={i} fill={PIE_COLORS[i]}/>)}
                      </Pie>
                      <Tooltip contentStyle={TT}/>
                    </PieChart>
                  </ResponsiveContainer>
                </Section>
              </div>
              <div style={{flex:1}}>
                <Section title="Priority Actions" sub="Top recommendations for TNFD alignment">
                  {d.priority_actions.map((a,i)=>(
                    <div key={i} style={{display:'flex',gap:10,marginBottom:10,alignItems:'flex-start'}}>
                      <span style={{background:'#10b981',color:'#fff',borderRadius:'50%',width:22,height:22,display:'flex',alignItems:'center',justifyContent:'center',fontSize:11,fontWeight:700,flexShrink:0}}>{i+1}</span>
                      <span style={{fontSize:13,color:'#374151'}}>{a}</span>
                    </div>
                  ))}
                </Section>
              </div>
            </Row>
          </>
        )}

        {/* Tab 4 — Full LEAP */}
        {tab===4 && (
          <>
            <Section title="Full LEAP Assessment" sub="Run the complete four-step LEAP process and view consolidated results">
              <Row gap={12} style={{marginBottom:16}}>
                <Inp label="Entity ID" value={form.entity_id} onChange={e=>upd('entity_id',e.target.value)}/>
                <Sel label="Sector" options={SECTORS} value={form.sector} onChange={e=>upd('sector',e.target.value)}/>
                <div style={{display:'flex',alignItems:'flex-end'}}><Btn onClick={run} style={{opacity:loading?0.6:1,background:'#065f46'}}>{loading?'Processing…':'Run Full LEAP'}</Btn></div>
              </Row>
              <div style={{display:'flex',gap:16,marginBottom:20}}>
                {d.leap_breakdown.map((s,i)=>(
                  <div key={i} style={{flex:1,textAlign:'center',padding:16,background:'#f9fafb',borderRadius:8,border:'1px solid #e5e7eb'}}>
                    <div style={{fontSize:11,color:'#6b7280',marginBottom:4,fontWeight:600}}>Step {i+1}</div>
                    <div style={{fontSize:18,fontWeight:700,color:'#10b981'}}>{s.step}</div>
                    <div style={{fontSize:26,fontWeight:700,color:s.score>=65?'#10b981':s.score>=45?'#f59e0b':'#ef4444'}}>{s.score}</div>
                  </div>
                ))}
              </div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={d.leap_breakdown}>
                  <CartesianGrid strokeDasharray="3 3"/>
                  <XAxis dataKey="step" style={{fontSize:12}}/>
                  <YAxis domain={[0,100]} style={{fontSize:11}}/>
                  <Tooltip contentStyle={TT}/>
                  <Bar dataKey="score" name="LEAP Score" radius={[4,4,0,0]}>
                    {d.leap_breakdown.map((s,i)=><Cell key={i} fill={s.score>=65?'#10b981':s.score>=45?'#f59e0b':'#ef4444'}/>)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Overall Maturity" sub="TNFD LEAP maturity classification based on composite score">
              <div style={{display:'flex',alignItems:'center',gap:20,padding:16,background:'#f0fdf4',borderRadius:8,border:'1px solid #a7f3d0'}}>
                <div style={{fontSize:48,fontWeight:700,color:'#10b981'}}>{d.overall_leap_score}</div>
                <div>
                  <div style={{fontSize:20,fontWeight:700,color:'#065f46'}}>{d.maturity}</div>
                  <div style={{fontSize:13,color:'#6b7280',marginTop:4}}>Maturity Level · TNFD v1.0 Framework</div>
                  <div style={{fontSize:13,color:'#6b7280'}}>Disclosure Completeness: <strong>{d.disclosure_completeness}%</strong></div>
                </div>
              </div>
            </Section>
            <Section title="Cross-Framework Mapping" sub="LEAP alignment with related regulatory and voluntary frameworks">
              <table style={{width:'100%',borderCollapse:'collapse',fontSize:13}}>
                <thead><tr style={{background:'#f9fafb'}}>{['Framework','Aligned','Open Gaps'].map(h=><th key={h} style={{padding:'8px 12px',textAlign:'left',fontWeight:600,borderBottom:'1px solid #e5e7eb'}}>{h}</th>)}</tr></thead>
                <tbody>{d.cross_framework.map((f,i)=><tr key={i} style={{borderBottom:'1px solid #f3f4f6'}}>
                  <td style={{padding:'8px 12px',fontWeight:600}}>{f.framework}</td>
                  <td style={{padding:'8px 12px'}}><span style={{background:f.aligned==='Yes'?'#d1fae5':'#fff7ed',color:f.aligned==='Yes'?'#065f46':'#92400e',padding:'2px 10px',borderRadius:12,fontSize:11,fontWeight:600}}>{f.aligned}</span></td>
                  <td style={{padding:'8px 12px',color:f.gaps>2?'#ef4444':'#374151',fontWeight:f.gaps>2?700:400}}>{f.gaps}</td>
                </tr>)}</tbody>
              </table>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
