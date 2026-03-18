/**
 * RegulatoryPenaltiesPage.jsx
 * Route: /regulatory-penalties
 * Badge: REG · ENF · E35
 *
 * Tab 1 — Penalty Calculator   POST /api/v1/regulatory-penalties/assess
 * Tab 2 — By Regulation
 * Tab 3 — Enforcement Timeline
 * Tab 4 — Whistleblower Risk
 * Tab 5 — Remediation
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  AreaChart, Area, PieChart, Pie, Cell, ReferenceLine,
} from 'recharts';

const rng = (seed) => { let s = seed; return () => { s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 0xffffffff; }; };

const Section = ({title,sub,children})=><div style={{background:'#fff',border:'1px solid #e5e7eb',borderRadius:8,padding:24,marginBottom:20}}><div style={{marginBottom:16}}><h3 style={{margin:0,fontWeight:700,fontSize:16}}>{title}</h3>{sub&&<p style={{margin:'4px 0 0',color:'#6b7280',fontSize:13}}>{sub}</p>}</div>{children}</div>;
const KpiCard = ({label,value,sub,color='#10b981'})=><div style={{flex:1,minWidth:160,background:'#f9fafb',border:'1px solid #e5e7eb',borderRadius:8,padding:16}}><div style={{fontSize:12,color:'#6b7280',marginBottom:4}}>{label}</div><div style={{fontSize:22,fontWeight:700,color}}>{value}</div>{sub&&<div style={{fontSize:11,color:'#9ca3af',marginTop:2}}>{sub}</div>}</div>;
const Row = ({children,gap=12})=><div style={{display:'flex',flexWrap:'wrap',gap}}>{children}</div>;
const Inp = ({label,...p})=><label style={{display:'flex',flexDirection:'column',gap:4,fontSize:13,color:'#374151'}}>{label}<input {...p} style={{padding:'6px 10px',border:'1px solid #d1d5db',borderRadius:6,fontSize:13,...p.style}}/></label>;
const Sel = ({label,options,...p})=><label style={{display:'flex',flexDirection:'column',gap:4,fontSize:13,color:'#374151'}}>{label}<select {...p} style={{padding:'6px 10px',border:'1px solid #d1d5db',borderRadius:6,fontSize:13,...p.style}}>{options.map(o=><option key={o.value??o} value={o.value??o}>{o.label??o}</option>)}</select></label>;
const Btn = ({children,...p})=><button {...p} style={{padding:'8px 18px',background:'#10b981',color:'#fff',border:'none',borderRadius:6,fontWeight:600,fontSize:13,cursor:'pointer',...p.style}}>{children}</button>;

const TABS = ['Penalty Calculator','By Regulation','Enforcement Timeline','Whistleblower Risk','Remediation'];
const TT = {backgroundColor:'#fff',border:'1px solid #e5e7eb',fontSize:11};

const REGS = [
  {key:'csrd',label:'CSRD',authority:'ESMA / National CA',maxPct:2,color:'#10b981'},
  {key:'sfdr',label:'SFDR',authority:'ESMA',maxPct:1.5,color:'#3b82f6'},
  {key:'taxonomy',label:'EU Taxonomy',authority:'ESMA / ECB',maxPct:1,color:'#8b5cf6'},
  {key:'eudr',label:'EUDR',authority:'Customs / NCA',maxPct:4,color:'#f59e0b'},
  {key:'csddd',label:'CSDDD',authority:'National CA',maxPct:5,color:'#ef4444'},
];

const TIMELINE = [
  {year:'2024',event:'EUDR Art 29 traceability enforcement begins',reg:'EUDR',urgency:'High'},
  {year:'2025',event:'CSRD first wave reporting (FY2024 data)',reg:'CSRD',urgency:'High'},
  {year:'2025',event:'SFDR RTS principal adverse impacts full application',reg:'SFDR',urgency:'High'},
  {year:'2026',event:'CSRD second wave (250+ employees)',reg:'CSRD',urgency:'Medium'},
  {year:'2026',event:'EU Taxonomy full alignment reporting required',reg:'EU Taxonomy',urgency:'Medium'},
  {year:'2027',event:'CSDDD Phase 1 enforcement (>5000 employees)',reg:'CSDDD',urgency:'High'},
  {year:'2028',event:'CSDDD Phase 2 (>3000 employees)',reg:'CSDDD',urgency:'Medium'},
  {year:'2029',event:'CSDDD Phase 3 (>1000 employees)',reg:'CSDDD',urgency:'Medium'},
  {year:'2030',event:'Full regulatory convergence — all frameworks active',reg:'All',urgency:'Critical'},
];

function buildFallback(seed, compliance) {
  const r = rng(seed);
  const turnover = compliance.turnover_mn || 5000;
  const complyMap = {csrd:compliance.csrd||65,sfdr:compliance.sfdr||72,taxonomy:compliance.taxonomy||58,eudr:compliance.eudr||80,csddd:compliance.csddd||45};
  const regDetails = REGS.map(reg => {
    const comp = complyMap[reg.key];
    const gap = Math.max(0, 100 - comp);
    const violations = Math.round(gap / 20 * (1 + r()*0.5));
    const maxPenalty = Math.round(turnover * reg.maxPct / 100 * (1 + r()*0.3));
    const expectedPenalty = Math.round(maxPenalty * (gap / 100) * (0.3 + r()*0.3));
    return {...reg, compliance:comp, gap, violations, maxPenalty, expectedPenalty};
  });
  const totalMax = regDetails.reduce((s,r)=>s+r.maxPenalty,0);
  const totalExpected = regDetails.reduce((s,r)=>s+r.expectedPenalty,0);
  const totalViolations = regDetails.reduce((s,r)=>s+r.violations,0);
  const wbRisk = totalViolations > 8 ? 'High' : totalViolations > 4 ? 'Medium' : 'Low';
  const wbFactors = [
    {factor:'CSRD greenwashing exposure',severity:complyMap.csrd<60?'High':'Medium'},
    {factor:'Supply chain EUDR non-compliance',severity:complyMap.eudr<70?'High':'Low'},
    {factor:'SFDR PAI misclassification risk',severity:complyMap.sfdr<65?'Medium':'Low'},
    {factor:'CSDDD adverse impact disclosure gap',severity:complyMap.csddd<60?'High':'Medium'},
    {factor:'Internal reporting channel adequacy',severity:r()>0.5?'Low':'Medium'},
  ];
  const remActions = [
    {reg:'CSRD',gap:'Material impact disclosure gaps',action:'Implement double materiality assessment',priority:'Critical',deadline:'Q2 2025',effort:4,impact:5},
    {reg:'CSDDD',gap:'Value chain mapping incomplete',action:'Conduct Tier 1 supplier due diligence',priority:'High',deadline:'Q3 2025',effort:5,impact:5},
    {reg:'EUDR',gap:'Geolocation data missing',action:'Deploy GPS/plot traceability system',priority:'High',deadline:'Q1 2025',effort:3,impact:4},
    {reg:'SFDR',gap:'PAI indicators partially reported',action:'Expand data collection for all 18 PAIs',priority:'Medium',deadline:'Q4 2025',effort:2,impact:3},
    {reg:'EU Taxonomy',gap:'Taxonomy alignment not quantified',action:'Calculate turnover/capex/opex KPIs',priority:'Medium',deadline:'Q2 2025',effort:3,impact:3},
  ];
  const roadmap = [2024,2025,2026,2027,2028].map((yr,i)=>({
    year:yr,
    csrd: Math.min(95,complyMap.csrd + i*6 + Math.round(r()*4)),
    sfdr: Math.min(95,complyMap.sfdr + i*4 + Math.round(r()*3)),
    eudr: Math.min(98,complyMap.eudr + i*3 + Math.round(r()*3)),
    csddd: Math.min(90,complyMap.csddd + i*9 + Math.round(r()*5)),
  }));
  return {totalMax, totalExpected, totalViolations, wbRisk, wbFactors, regDetails, remActions, roadmap};
}

export default function RegulatoryPenaltiesPage() {
  const [tab, setTab] = useState(0);
  const [form, setForm] = useState({entity_id:'CORP-REG-001',entity_name:'Meridian Holdings GmbH',turnover_mn:8500});
  const [compliance, setCompliance] = useState({csrd:65,sfdr:72,taxonomy:58,eudr:80,csddd:45});
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const upd = (k,v) => setForm(f=>({...f,[k]:v}));
  const updC = (k,v) => setCompliance(c=>({...c,[k]:parseInt(v)||0}));

  const run = async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/regulatory-penalties/assess', {...form,...compliance});
      setData(res.data);
    } catch {
      const seed = form.entity_id.split('').reduce((a,c)=>a+c.charCodeAt(0),0)||42;
      setData(buildFallback(seed,{...compliance,turnover_mn:form.turnover_mn}));
    }
    setLoading(false);
  };

  useEffect(()=>{ run(); },[]);

  const d = data || buildFallback(42,{...compliance,turnover_mn:form.turnover_mn});
  const prioColor = p => p==='Critical'?'#ef4444':p==='High'?'#f59e0b':p==='Medium'?'#3b82f6':'#10b981';
  const wbColor = r => r==='High'?'#ef4444':r==='Medium'?'#f59e0b':'#10b981';
  const urgColor = u => u==='Critical'?'#ef4444':u==='High'?'#f59e0b':u==='Medium'?'#3b82f6':'#10b981';

  return (
    <div style={{fontFamily:'Inter,system-ui,sans-serif',background:'#f9fafb',minHeight:'100vh',padding:24}}>
      <div style={{maxWidth:1100,margin:'0 auto'}}>
        {/* Header */}
        <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:20}}>
          <div>
            <div style={{display:'flex',alignItems:'center',gap:8}}>
              <h1 style={{margin:0,fontSize:22,fontWeight:700}}>Regulatory Penalty & Enforcement</h1>
              <span style={{background:'#fee2e2',color:'#991b1b',padding:'2px 10px',borderRadius:20,fontSize:11,fontWeight:700}}>REG · ENF · E35</span>
            </div>
            <p style={{margin:'4px 0 0',color:'#6b7280',fontSize:13}}>EU sustainability regulation penalty exposure — CSRD / SFDR / EU Taxonomy / EUDR / CSDDD</p>
          </div>
        </div>

        {/* KPIs */}
        <Row gap={12} style={{marginBottom:20}}>
          <KpiCard label="Max Penalty Exposure" value={`€${(d.totalMax/1000).toFixed(1)}M`} sub="Across all EU regulations" color="#ef4444"/>
          <KpiCard label="Expected Penalty" value={`€${(d.totalExpected/1000).toFixed(1)}M`} sub="Probability-weighted estimate" color="#f59e0b"/>
          <KpiCard label="Violations Found" value={d.totalViolations} sub="Total regulatory breaches identified" color="#ef4444"/>
          <KpiCard label="Whistleblower Risk" value={d.wbRisk} sub="EUWD 2019/1937 exposure tier" color={wbColor(d.wbRisk)}/>
        </Row>

        {/* Tab bar */}
        <div style={{display:'flex',gap:4,marginBottom:20,borderBottom:'2px solid #e5e7eb'}}>
          {TABS.map((t,i)=>(
            <button key={t} onClick={()=>setTab(i)} style={{padding:'8px 18px',border:'none',borderBottom:tab===i?'2px solid #10b981':'2px solid transparent',background:'none',fontWeight:tab===i?700:400,color:tab===i?'#10b981':'#6b7280',cursor:'pointer',fontSize:13,marginBottom:-2}}>{t}</button>
          ))}
        </div>

        {/* Tab 0 — Penalty Calculator */}
        {tab===0 && (
          <>
            <Section title="Entity & Compliance Configuration" sub="Enter entity details and drag compliance sliders to calculate penalty exposure">
              <Row gap={12} style={{marginBottom:16}}>
                <Inp label="Entity ID" value={form.entity_id} onChange={e=>upd('entity_id',e.target.value)}/>
                <Inp label="Entity Name" value={form.entity_name} onChange={e=>upd('entity_name',e.target.value)}/>
                <Inp label="Annual Turnover (€M)" type="number" value={form.turnover_mn} onChange={e=>upd('turnover_mn',parseInt(e.target.value)||0)}/>
              </Row>
              <div style={{marginBottom:16}}>
                <div style={{fontSize:13,fontWeight:600,marginBottom:12,color:'#374151'}}>Compliance Level by Regulation</div>
                {REGS.map(reg=>(
                  <div key={reg.key} style={{marginBottom:12}}>
                    <div style={{display:'flex',justifyContent:'space-between',marginBottom:4,fontSize:13}}>
                      <span><strong>{reg.label}</strong> — {compliance[reg.key]}% compliant</span>
                      <span style={{color:compliance[reg.key]>=75?'#10b981':compliance[reg.key]>=50?'#f59e0b':'#ef4444',fontWeight:700}}>{compliance[reg.key]>=75?'Low Risk':compliance[reg.key]>=50?'Medium Risk':'High Risk'}</span>
                    </div>
                    <input type="range" min={0} max={100} value={compliance[reg.key]} onChange={e=>updC(reg.key,e.target.value)}
                      style={{width:'100%',accentColor:reg.color,cursor:'pointer'}}/>
                  </div>
                ))}
              </div>
              <Btn onClick={run} style={{opacity:loading?0.6:1}}>{loading?'Calculating…':'Calculate Penalties'}</Btn>
            </Section>
            <Row gap={16}>
              <div style={{flex:1,padding:20,background:'#fff5f5',borderRadius:8,border:'1px solid #fecaca',textAlign:'center'}}>
                <div style={{fontSize:13,color:'#6b7280',marginBottom:4}}>Maximum Penalty Exposure</div>
                <div style={{fontSize:36,fontWeight:700,color:'#ef4444'}}>€{(d.totalMax/1000).toFixed(1)}M</div>
                <div style={{fontSize:12,color:'#6b7280'}}>Statutory maximum across all 5 regulations</div>
              </div>
              <div style={{flex:1,padding:20,background:'#fffbeb',borderRadius:8,border:'1px solid #fde68a',textAlign:'center'}}>
                <div style={{fontSize:13,color:'#6b7280',marginBottom:4}}>Expected Penalty</div>
                <div style={{fontSize:36,fontWeight:700,color:'#f59e0b'}}>€{(d.totalExpected/1000).toFixed(1)}M</div>
                <div style={{fontSize:12,color:'#6b7280'}}>Probability-weighted enforcement estimate</div>
              </div>
              <div style={{flex:1,padding:20,background:'#f0fdf4',borderRadius:8,border:'1px solid #a7f3d0',textAlign:'center'}}>
                <div style={{fontSize:13,color:'#6b7280',marginBottom:4}}>Penalty Reduction Potential</div>
                <div style={{fontSize:36,fontWeight:700,color:'#10b981'}}>€{Math.round((d.totalMax-d.totalExpected)/1000*10)/10}M</div>
                <div style={{fontSize:12,color:'#6b7280'}}>Savings from full remediation</div>
              </div>
            </Row>
          </>
        )}

        {/* Tab 1 — By Regulation */}
        {tab===1 && (
          <>
            <Section title="Penalty Exposure by Regulation" sub="Maximum and expected penalties per EU regulation">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={d.regDetails}>
                  <CartesianGrid strokeDasharray="3 3"/>
                  <XAxis dataKey="label" style={{fontSize:12}}/>
                  <YAxis tickFormatter={v=>`€${v/1000}M`} style={{fontSize:11}}/>
                  <Tooltip contentStyle={TT} formatter={v=>`€${(v/1000).toFixed(1)}M`}/>
                  <Legend/>
                  <Bar dataKey="maxPenalty" name="Max Penalty" fill="#ef4444" radius={[4,4,0,0]}/>
                  <Bar dataKey="expectedPenalty" name="Expected Penalty" fill="#f59e0b" radius={[4,4,0,0]}/>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:16}}>
              {d.regDetails.map(reg=>(
                <div key={reg.key} style={{padding:16,background:'#f9fafb',borderRadius:8,border:`2px solid ${reg.color}20`}}>
                  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
                    <span style={{fontWeight:700,fontSize:16,color:reg.color}}>{reg.label}</span>
                    <span style={{background:reg.compliance>=75?'#d1fae5':reg.compliance>=50?'#fff7ed':'#fee2e2',color:reg.compliance>=75?'#065f46':reg.compliance>=50?'#92400e':'#991b1b',padding:'2px 8px',borderRadius:12,fontSize:11,fontWeight:600}}>{reg.compliance}%</span>
                  </div>
                  <div style={{fontSize:12,color:'#6b7280',marginBottom:6}}>{reg.authority}</div>
                  <div style={{marginBottom:4}}><span style={{fontSize:12,color:'#6b7280'}}>Violations: </span><span style={{fontWeight:700,color:reg.violations>3?'#ef4444':'#374151'}}>{reg.violations}</span></div>
                  <div style={{marginBottom:4}}><span style={{fontSize:12,color:'#6b7280'}}>Max: </span><span style={{fontWeight:700,color:'#ef4444'}}>€{(reg.maxPenalty/1000).toFixed(1)}M</span></div>
                  <div><span style={{fontSize:12,color:'#6b7280'}}>Expected: </span><span style={{fontWeight:700,color:'#f59e0b'}}>€{(reg.expectedPenalty/1000).toFixed(1)}M</span></div>
                  <div style={{height:4,background:'#e5e7eb',borderRadius:2,marginTop:8}}><div style={{height:4,background:reg.color,borderRadius:2,width:`${reg.compliance}%`}}/></div>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Tab 2 — Enforcement Timeline */}
        {tab===2 && (
          <>
            <Section title="EU Regulatory Enforcement Milestones" sub="Key enforcement and reporting deadlines 2024-2030">
              {TIMELINE.map((item,i)=>(
                <div key={i} style={{display:'flex',gap:12,marginBottom:10,alignItems:'flex-start'}}>
                  <div style={{minWidth:44,textAlign:'center'}}>
                    <div style={{background:urgColor(item.urgency),color:'#fff',borderRadius:6,padding:'3px 6px',fontSize:11,fontWeight:700,textAlign:'center'}}>{item.year}</div>
                  </div>
                  <div style={{flex:1,padding:'8px 12px',background:'#f9fafb',borderRadius:6,border:'1px solid #e5e7eb'}}>
                    <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                      <span style={{fontSize:13,fontWeight:500}}>{item.event}</span>
                      <div style={{display:'flex',gap:6}}>
                        <span style={{background:REGS.find(r=>r.label===item.reg)?.color?`${REGS.find(r=>r.label===item.reg).color}20`:'#f3f4f6',color:REGS.find(r=>r.label===item.reg)?.color||'#6b7280',padding:'1px 8px',borderRadius:10,fontSize:10,fontWeight:700,border:`1px solid ${REGS.find(r=>r.label===item.reg)?.color||'#e5e7eb'}`}}>{item.reg}</span>
                        <span style={{background:`${urgColor(item.urgency)}20`,color:urgColor(item.urgency),padding:'1px 8px',borderRadius:10,fontSize:10,fontWeight:700}}>{item.urgency}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </Section>
            <Section title="Phase-In Schedule by Regulation" sub="Applicable entity thresholds and application dates">
              <table style={{width:'100%',borderCollapse:'collapse',fontSize:13}}>
                <thead><tr style={{background:'#f9fafb'}}>{['Regulation','Phase','Threshold','Date','Status'].map(h=><th key={h} style={{padding:'8px 12px',textAlign:'left',fontWeight:600,borderBottom:'1px solid #e5e7eb'}}>{h}</th>)}</tr></thead>
                <tbody>
                  {[
                    {reg:'CSRD',phase:'Wave 1',threshold:'PIE + >500 employees',date:'FY 2024',status:'Active'},
                    {reg:'CSRD',phase:'Wave 2',threshold:'>250 employees or €40M+ turnover',date:'FY 2025',status:'Upcoming'},
                    {reg:'CSRD',phase:'Wave 3',threshold:'Listed SMEs',date:'FY 2026',status:'Upcoming'},
                    {reg:'CSDDD',phase:'Phase 1',threshold:'>5,000 employees / €1.5Bn turnover',date:'2027',status:'Upcoming'},
                    {reg:'CSDDD',phase:'Phase 2',threshold:'>3,000 employees',date:'2028',status:'Upcoming'},
                    {reg:'EUDR',phase:'Full application',threshold:'All operators and traders',date:'Dec 2024',status:'Active'},
                  ].map((row,i)=><tr key={i} style={{borderBottom:'1px solid #f3f4f6'}}>
                    <td style={{padding:'8px 12px',fontWeight:700,color:REGS.find(r=>r.label===row.reg)?.color||'#374151'}}>{row.reg}</td>
                    <td style={{padding:'8px 12px'}}>{row.phase}</td>
                    <td style={{padding:'8px 12px',color:'#6b7280',fontSize:12}}>{row.threshold}</td>
                    <td style={{padding:'8px 12px',fontWeight:500}}>{row.date}</td>
                    <td style={{padding:'8px 12px'}}><span style={{background:row.status==='Active'?'#fee2e2':'#fef3c7',color:row.status==='Active'?'#991b1b':'#92400e',padding:'2px 8px',borderRadius:12,fontSize:11,fontWeight:600}}>{row.status}</span></td>
                  </tr>)}
                </tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 3 — Whistleblower Risk */}
        {tab===3 && (
          <>
            <Section title="Whistleblower Risk Assessment" sub="EU Whistleblower Directive (2019/1937) exposure analysis">
              <div style={{display:'flex',alignItems:'center',gap:24,padding:20,background:d.wbRisk==='High'?'#fff5f5':d.wbRisk==='Medium'?'#fffbeb':'#f0fdf4',borderRadius:8,border:`1px solid ${wbColor(d.wbRisk)}40`,marginBottom:16}}>
                <div style={{textAlign:'center'}}>
                  <div style={{fontSize:13,color:'#6b7280',marginBottom:4}}>Risk Tier</div>
                  <div style={{fontSize:36,fontWeight:700,color:wbColor(d.wbRisk)}}>{d.wbRisk}</div>
                  <div style={{fontSize:12,color:'#6b7280'}}>Whistleblower Risk</div>
                </div>
                <div style={{flex:1,fontSize:13,color:'#374151',lineHeight:1.6}}>
                  {d.wbRisk==='High'?'Material regulatory violations identified. High probability of internal/external whistleblower reports. Immediate remediation and channel establishment required under EU Directive 2019/1937.':d.wbRisk==='Medium'?'Moderate compliance gaps present. Whistleblower channels must be established and publicised. Named contact officer required for entities >250 employees.':'Compliance posture acceptable. Maintain internal reporting channels and conduct annual review of effectiveness and accessibility.'}
                </div>
              </div>
            </Section>
            <Section title="Whistleblower Risk Factors" sub="Individual factors contributing to whistleblower exposure">
              {d.wbFactors.map((f,i)=>(
                <div key={i} style={{display:'flex',justifyContent:'space-between',alignItems:'center',padding:'10px 14px',background:'#f9fafb',borderRadius:6,marginBottom:8,border:'1px solid #e5e7eb'}}>
                  <span style={{fontSize:13}}>{f.factor}</span>
                  <span style={{background:f.severity==='High'?'#fee2e2':f.severity==='Medium'?'#fff7ed':'#d1fae5',color:f.severity==='High'?'#991b1b':f.severity==='Medium'?'#92400e':'#065f46',padding:'2px 10px',borderRadius:12,fontSize:11,fontWeight:700}}>{f.severity}</span>
                </div>
              ))}
            </Section>
            <Row gap={16}>
              <div style={{flex:1}}>
                <Section title="Mitigation Actions" sub="Steps to reduce whistleblower exposure">
                  {['Establish confidential reporting hotline (EUWD Art 9)','Appoint dedicated compliance officer','Conduct staff training on reporting obligations','Implement non-retaliation policy in writing','Document all reports and follow-up actions'].map((a,i)=>(
                    <div key={i} style={{display:'flex',gap:10,marginBottom:8,alignItems:'flex-start'}}>
                      <span style={{background:'#e5e7eb',color:'#6b7280',borderRadius:'50%',width:20,height:20,display:'flex',alignItems:'center',justifyContent:'center',fontSize:10,fontWeight:700,flexShrink:0}}>{i+1}</span>
                      <span style={{fontSize:13,color:'#374151'}}>{a}</span>
                    </div>
                  ))}
                </Section>
              </div>
              <div style={{flex:1}}>
                <Section title="Regulatory Reporting Obligations" sub="Key whistleblower channel requirements by entity size">
                  {[
                    {threshold:'>50 employees',req:'Internal reporting channel required'},
                    {threshold:'>250 employees',req:'Named officer + annual reporting'},
                    {threshold:'All entities',req:'External channel via national CA'},
                    {threshold:'Financial sector',req:'FCA/NCAs enhanced requirements'},
                  ].map((r,i)=>(
                    <div key={i} style={{padding:'8px 12px',borderBottom:'1px solid #f3f4f6',display:'flex',gap:12}}>
                      <span style={{fontSize:11,fontWeight:700,color:'#6b7280',minWidth:110}}>{r.threshold}</span>
                      <span style={{fontSize:13,color:'#374151'}}>{r.req}</span>
                    </div>
                  ))}
                </Section>
              </div>
            </Row>
          </>
        )}

        {/* Tab 4 — Remediation */}
        {tab===4 && (
          <>
            <Section title="Remediation Priority Matrix" sub="Action priorities by effort vs compliance impact">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={d.remActions}>
                  <CartesianGrid strokeDasharray="3 3"/>
                  <XAxis dataKey="reg" style={{fontSize:12}}/>
                  <YAxis domain={[0,6]} style={{fontSize:11}}/>
                  <Tooltip contentStyle={TT}/>
                  <Legend/>
                  <Bar dataKey="effort" name="Effort (1-5)" fill="#f59e0b" radius={[4,4,0,0]}/>
                  <Bar dataKey="impact" name="Impact (1-5)" fill="#10b981" radius={[4,4,0,0]}/>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Action Plan" sub="Regulation-specific remediation actions with priority and deadlines">
              <table style={{width:'100%',borderCollapse:'collapse',fontSize:12}}>
                <thead><tr style={{background:'#f9fafb'}}>{['Regulation','Gap','Recommended Action','Priority','Deadline'].map(h=><th key={h} style={{padding:'8px 10px',textAlign:'left',fontWeight:600,borderBottom:'1px solid #e5e7eb'}}>{h}</th>)}</tr></thead>
                <tbody>{d.remActions.map((a,i)=><tr key={i} style={{borderBottom:'1px solid #f3f4f6',background:i%2===0?'#fff':'#fafafa'}}>
                  <td style={{padding:'7px 10px',fontWeight:700,color:REGS.find(r=>r.label===a.reg)?.color||'#374151'}}>{a.reg}</td>
                  <td style={{padding:'7px 10px',color:'#6b7280'}}>{a.gap}</td>
                  <td style={{padding:'7px 10px'}}>{a.action}</td>
                  <td style={{padding:'7px 10px'}}><span style={{background:`${prioColor(a.priority)}20`,color:prioColor(a.priority),padding:'2px 8px',borderRadius:12,fontSize:11,fontWeight:700}}>{a.priority}</span></td>
                  <td style={{padding:'7px 10px',fontWeight:500,color:'#374151'}}>{a.deadline}</td>
                </tr>)}</tbody>
              </table>
            </Section>
            <Section title="Projected Compliance Improvement Roadmap" sub="Estimated compliance score trajectory following remediation actions">
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={d.roadmap}>
                  <CartesianGrid strokeDasharray="3 3"/>
                  <XAxis dataKey="year" style={{fontSize:12}}/>
                  <YAxis domain={[0,100]} tickFormatter={v=>`${v}%`} style={{fontSize:11}}/>
                  <Tooltip contentStyle={TT} formatter={v=>`${v}%`}/>
                  <Legend/>
                  <ReferenceLine y={80} stroke="#10b981" strokeDasharray="4 4" label={{value:'Target 80%',fill:'#10b981',fontSize:10}}/>
                  <Line type="monotone" dataKey="csrd" name="CSRD" stroke="#10b981" strokeWidth={2} dot={{r:4}}/>
                  <Line type="monotone" dataKey="sfdr" name="SFDR" stroke="#3b82f6" strokeWidth={2} dot={{r:4}}/>
                  <Line type="monotone" dataKey="eudr" name="EUDR" stroke="#f59e0b" strokeWidth={2} dot={{r:4}}/>
                  <Line type="monotone" dataKey="csddd" name="CSDDD" stroke="#ef4444" strokeWidth={2} dot={{r:4}}/>
                </LineChart>
              </ResponsiveContainer>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
