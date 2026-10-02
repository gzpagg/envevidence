/* Offline lab records. Time is derived from clock anchors, never interval ticks. */
(function(root,factory){const api=factory();if(typeof module==='object')module.exports=api;else root.Lab=api;})(globalThis,function(){
  'use strict';
  const id=()=>crypto.randomUUID().replaceAll('-','');
  const clone=x=>JSON.parse(JSON.stringify(x));
  const assert=(ok)=>{if(!ok)throw new Error('invalid');};
  const txt=(x,n=20000)=>typeof x==='string'&&x.length<=n;
  const name=x=>txt(x,300)&&!!x.trim();
  const number=x=>Number.isFinite(x)&&x>=0;
  const stamp=x=>x&&number(x.wall)&&number(x.mono)&&txt(x.boot,100);
  const list=x=>Array.isArray(x)&&new Set(x.map(v=>v.id)).size===x.length;
  const palettes={clay:['#A65338','#F7F5F0'],forest:['#147D73','#F6F8F7'],ocean:['#1D4ED8','#F4F7FB'],graphite:['#6D4ACF','#F7F5FB']};
  function empty(){return {version:2,experiments:[],timers:[],counters:[],records:[],events:[],samples:[],demo_loaded:false};}
  // Version 2 adds bench runs: process and water details on experiments, and pulled samples.
  function upgrade(l){if(l&&l.version===1){l.version=2;l.samples=[];for(const e of l.experiments||[]){e.run=null;e.water=null;}}
    // 0.5.0 previews wrote version 2 without peak areas or fit exclusion.
    if(l&&l.version===2&&Array.isArray(l.samples))for(const v of l.samples){
      if(!('recorded_elapsed_ms' in v))v.recorded_elapsed_ms=v.elapsed_ms;
      if(!('recorded_quench_delay_ms' in v))v.recorded_quench_delay_ms=v.quench?.delay_ms;
      for(const x of [v,...(Array.isArray(v.revisions)?v.revisions:[])]){
        if(!('peak_area' in x))x.peak_area=null;if(!('fit_excluded' in x))x.fit_excluded=false;
        for(const k of ['ph','temp_c','volume_ml'])if(!(k+'_source' in x))x[k+'_source']=x[k]===null?'unmeasured':'unknown';
        if(!('fit_exclusion_reason' in x))x.fit_exclusion_reason='';
        if(!('elapsed_ms' in x))x.elapsed_ms=v.recorded_elapsed_ms;
        if(x!==v&&!('quench_delay_ms' in x))x.quench_delay_ms=v.recorded_quench_delay_ms;
        for(const k of ['pulled_time_source','quench_time_source'])if(!(k in x))x[k]='unknown';
        if(!('time_revision_reason' in x))x.time_revision_reason='';
      }
    }
    return l;}
  function migrate(s){if(!s.lab){s.lab=empty();const p=s.workspace.preferences;if(p.palette==='forest'&&p.accent.toUpperCase()==='#147D73'&&p.background.toUpperCase()==='#F6F8F7'){p.palette='clay';[p.accent,p.background]=palettes.clay;}}else upgrade(s.lab);validate(s.lab);return s;}
  function validate(l){assert(l&&l.version===2);for(const k of ['experiments','timers','counters','records','events','samples']){assert(list(l[k]));for(const x of l[k])assert(typeof x.id==='string'&&/^[a-f0-9]{32}$/.test(x.id));}
    const parent=x=>x.experiment_id===null||l.experiments.some(e=>e.id===x.experiment_id);
    for(const e of l.experiments)assert(name(e.title)&&txt(e.description)&&txt(e.sample,300)&&stamp(e.started)&&(e.ended===null||stamp(e.ended))&&typeof e.archived==='boolean'&&(e.run===null||validRun(e.run))&&(e.water===null||validWater(e.water)));
    for(const t of l.timers)assert(name(t.title)&&parent(t)&&['stopwatch','countdown'].includes(t.kind)&&['idle','running','paused','done'].includes(t.status)&&number(t.elapsed_ms)&&number(t.duration_ms)&&(t.kind!=='countdown'||t.duration_ms>0)&&(t.anchor===null||stamp(t.anchor))&&(t.status!=='running'||stamp(t.anchor))&&Number.isSafeInteger(t.cycle)&&t.cycle>=0&&typeof t.archived==='boolean'&&/^#[a-f\d]{6}$/i.test(t.color)&&['timer','sample'].includes(t.purpose));
    for(const c of l.counters)assert(name(c.title)&&parent(c)&&Number.isSafeInteger(c.value)&&c.value>=0&&Number.isSafeInteger(c.round)&&c.round>=1&&typeof c.archived==='boolean');
    const photo=p=>p&&/^[a-f\d]{32}$/.test(p.id)&&txt(p.name,300)&&['jpg','png','webp'].includes(p.ext)&&/^image\/(jpeg|png|webp)$/.test(p.mime)&&number(p.bytes);
    for(const r of l.records){assert(parent(r)&&txt(r.body)&&txt(r.sample,300)&&stamp(r.at)&&number(r.elapsed_ms)&&typeof r.archived==='boolean'&&Array.isArray(r.photos)&&r.photos.every(photo)&&Array.isArray(r.revisions));for(const v of r.revisions)assert(txt(v.body)&&txt(v.sample,300)&&stamp(v.at));}
    for(const e of l.events)assert(parent(e)&&stamp(e.at)&&name(e.kind)&&txt(e.label,300)&&number(e.elapsed_ms));
    for(const v of l.samples){const e=l.experiments.find(e=>e.id===v.experiment_id);assert(validSample(v)&&e&&(v.timer_id===null||l.timers.some(t=>t.id===v.timer_id&&t.experiment_id===e.id)));
      assert(clockDifference(e.started,v.pulled)>=0&&clockDifference(v.pulled,v.quench.at)>=0);
      if(e.ended)assert(v.elapsed_ms+v.quench.delay_ms<=experimentElapsed(e,e.ended));
      for(const r of v.revisions)assert(stamp(r.at)&&SAMPLE_FIELDS.every(k=>k in r)&&validSampleValues(r)&&number(r.elapsed_ms)&&number(r.quench_delay_ms)&&validTimeSources(r)&&(r.reason===undefined||txt(r.reason,2000)));}
    return l;
  }
  function clockDifference(a,b){return a.boot===b.boot?b.mono-a.mono:b.wall-a.wall;}
  function delta(a,b){return Math.max(0,clockDifference(a,b));}
  function elapsed(t,c){return t.elapsed_ms+(t.status==='running'?delta(t.anchor,c):0);}
  function experimentElapsed(e,c){return e?delta(e.started,e.ended||c):0;}
  function remaining(t,c){return t.duration_ms-elapsed(t,c);}
  function event(l,experiment_id,kind,label,c,extra={}){const e=l.experiments.find(x=>x.id===experiment_id);const v={id:id(),experiment_id,kind,label,at:clone(c),elapsed_ms:experimentElapsed(e,c),...extra};l.events.push(v);return v;}
  function experiment(l,title,description,sample,c){assert(name(title)&&stamp(c));const e={id:id(),title:title.trim(),description,sample,started:clone(c),ended:null,archived:false,run:null,water:null};l.experiments.unshift(e);event(l,e.id,'experiment_start',e.title,c);return e;}
  function timer(l,{title,kind='stopwatch',duration_ms=0,experiment_id=null,color='#A65338',purpose='timer'},c){assert(name(title)&&['stopwatch','countdown'].includes(kind)&&number(duration_ms)&&(kind!=='countdown'||duration_ms>0));if(experiment_id)assert(l.experiments.some(e=>e.id===experiment_id&&!e.ended&&!e.archived));const t={id:id(),title:title.trim(),kind,duration_ms,experiment_id,color,purpose,status:'idle',elapsed_ms:0,anchor:null,cycle:0,archived:false};l.timers.unshift(t);event(l,experiment_id,'timer_create',t.title,c,{timer_id:t.id});return t;}
  function operate(l,t,action,c){const before=elapsed(t,c);assert(stamp(c));if(action==='start'){const e=l.experiments.find(e=>e.id===t.experiment_id);assert(!t.archived&&(!e||(!e.ended&&!e.archived))&&['idle','paused'].includes(t.status));t.anchor=clone(t.purpose==='sample'&&e?e.started:c);if(t.purpose==='sample')t.elapsed_ms=0;t.status='running';}
    else if(action==='pause'){assert(t.status==='running');t.elapsed_ms=before;t.anchor=null;t.status='paused';}
    else if(action==='finish'){assert(t.status==='running'||t.status==='paused');t.elapsed_ms=before;t.anchor=null;t.status='done';}
    else if(action==='reset'){assert(t.purpose!=='sample');t.elapsed_ms=0;t.anchor=null;t.status='idle';t.cycle++;}
    else if(action==='lap'){assert(t.status==='running'||t.status==='paused');}
    else throw new Error('invalid');
    return event(l,t.experiment_id,t.purpose==='sample'&&action==='finish'?'sample_taken':'timer_'+action,t.title,c,{timer_id:t.id,cycle:t.cycle,timer_elapsed_ms:before,planned_ms:t.purpose==='sample'?t.duration_ms:null});
  }
  function archiveTimer(l,t,c){if(!t.archived&&t.status==='running')operate(l,t,'pause',c);t.archived=!t.archived;event(l,t.experiment_id,t.archived?'timer_archive':'timer_restore',t.title,c);}
  // Checkpoints still open when a run ends were never pulled; log them as skipped, not as samples.
  function finishExperiment(l,e,c){assert(!e.ended);for(const t of l.timers.filter(t=>t.experiment_id===e.id&&['running','paused'].includes(t.status))){const ev=operate(l,t,'finish',c);if(t.purpose==='sample')ev.kind='sample_skipped';}e.ended=clone(c);event(l,e.id,'experiment_finish',e.title,c);}
  function counter(l,title,experiment_id,c){assert(name(title));const v={id:id(),title:title.trim(),experiment_id,value:0,round:1,archived:false};l.counters.unshift(v);event(l,experiment_id,'counter_create',v.title,c);return v;}
  function count(l,v,action,c){const previous=v.value;if(action==='add'){assert(Number.isSafeInteger(previous+1));v.value++;}else if(action==='undo'){assert(previous>0);v.value--;}else if(action==='reset'){v.round++;v.value=0;}else throw new Error('invalid');return event(l,v.experiment_id,'counter_'+action,v.title,c,{counter_id:v.id,previous,value:v.value,round:v.round});}
  function record(l,experiment_id,body,sample,c){const e=l.experiments.find(x=>x.id===experiment_id);const r={id:id(),experiment_id,body,sample,at:clone(c),elapsed_ms:experimentElapsed(e,c),photos:[],revisions:[],archived:false};l.records.unshift(r);return r;}
  function editRecord(r,body,sample,c){r.revisions.push({body:r.body,sample:r.sample,at:clone(c)});r.body=body;r.sample=sample;}
  function schedule(l,e,minutes,c){assert(!e.ended&&!e.archived&&minutes.length&&minutes.every(n=>Number.isFinite(n)&&n>0&&n<=525600));for(const m of [...new Set(minutes)].sort((a,b)=>a-b)){const t=timer(l,{title:`${e.title} · ${m} min`,kind:'countdown',duration_ms:m*60000,experiment_id:e.id,purpose:'sample'},c);t.anchor=clone(e.started);t.status='running';event(l,e.id,'timer_start',t.title,c,{timer_id:t.id,planned_ms:t.duration_ms});}}
  function time(ms,decimal=false){const n=Math.floor(Math.abs(ms)/1000),h=Math.floor(n/3600),m=Math.floor(n%3600/60),s=n%60;return `${h?String(h).padStart(2,'0')+':':''}${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}${decimal?'.'+Math.floor(Math.abs(ms)%1000/100):''}`;}
  function merge(current,incoming,c){incoming=upgrade(clone(incoming));validate(incoming);const l=clone(current);let added=0;for(const k of ['experiments','timers','counters','records','events','samples'])for(const v of incoming[k])if(!l[k].some(x=>x.id===v.id)){const item=clone(v);if(k==='timers'&&item.status==='running'){item.elapsed_ms=elapsed(item,c);item.anchor=null;item.status='paused';}l[k].push(item);added++;}validate(l);return {lab:l,added};}
  function csv(l,experiment_id=null){const rows=[['experiment_id','experiment','kind','recorded_at','elapsed_seconds','label','note','sample','timer_seconds','count','photo_files']];const title=id=>l.experiments.find(e=>e.id===id)?.title||'';for(const e of l.events.filter(e=>!experiment_id||e.experiment_id===experiment_id))rows.push([e.experiment_id,title(e.experiment_id),e.kind,new Date(e.at.wall).toISOString(),e.elapsed_ms/1000,e.label,'','',e.timer_elapsed_ms==null?'':e.timer_elapsed_ms/1000,e.value??'','']);for(const r of l.records.filter(r=>!experiment_id||r.experiment_id===experiment_id))rows.push([r.experiment_id,title(r.experiment_id),'observation',new Date(r.at.wall).toISOString(),r.elapsed_ms/1000,'',r.body,r.sample,'','',r.photos.map(p=>`${p.id}.${p.ext}`).join(';')]);const safe=v=>{let s=String(v??'');if(/^[\s]*[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};return '\ufeff'+rows.map(r=>r.map(safe).join(',')).join('\r\n');}

  /* ---- Bench runs: process, water matrix and pulled samples ---- */
  const PROCESSES=['UV/PDS','UV/PMS','UV/H2O2','UV/chlorine','O3','O3/H2O2','Fenton','Photo-Fenton','PMS/catalyst','Electrochemical','Photocatalysis','Other'];
  const MATRICES=['ultrapure','buffer','nom_isolate','surface_water','secondary_effluent','mbr_effluent','tertiary_effluent','industrial','other'];
  const WATER_NUMBERS=['doc_mg_c_l','uv254_cm1','alkalinity_mg_caco3_l','chloride_mg_l','nitrate_n_mg_l','bromide_ug_l','conductivity_ms_cm','ph'];
  const MEASUREMENT_SOURCES=['measured','carried','unmeasured','unknown','synthetic'];
  const SAMPLE_FIELDS=['ph','ph_source','temp_c','temp_c_source','volume_ml','volume_ml_source','note','peak_area','c_over_c0','fit_excluded','fit_exclusion_reason','elapsed_ms','quench_delay_ms','pulled_time_source','quench_time_source','time_revision_reason'];
  const READY_MS=30000,LATE_MS=30000;
  const opt=x=>x===null||(Number.isFinite(x)&&x>=0);
  const optPh=x=>x===null||(Number.isFinite(x)&&x>=0&&x<=14);
  const optTemp=x=>x===null||(Number.isFinite(x)&&x>=-20&&x<=150);
  const optBool=x=>x===null||typeof x==='boolean';
  function validRun(r){return !!r&&PROCESSES.includes(r.process)&&txt(r.target,300)&&txt(r.oxidant,100)&&opt(r.oxidant_mm)&&opt(r.wavelength_nm)&&opt(r.fluence_rate_mw_cm2);}
  function validWater(w){return !!w&&MATRICES.includes(w.matrix)&&txt(w.lot,100)&&optBool(w.filtered)&&optBool(w.spiked)&&WATER_NUMBERS.every(k=>k==='ph'?optPh(w[k]):opt(w[k]));}
  function validSampleValues(v){return optPh(v.ph)&&optTemp(v.temp_c)&&(v.volume_ml===null||(Number.isFinite(v.volume_ml)&&v.volume_ml>0))
    &&['ph','temp_c','volume_ml'].every(k=>MEASUREMENT_SOURCES.includes(v[k+'_source'])&&(v[k]===null?v[k+'_source']==='unmeasured':v[k+'_source']!=='unmeasured'))
    &&txt(v.note)&&opt(v.peak_area)&&opt(v.c_over_c0)&&typeof v.fit_excluded==='boolean'&&txt(v.fit_exclusion_reason,2000);}
  function validTimeSources(v){return ['click','corrected','unknown'].includes(v.pulled_time_source)&&['click','corrected','unknown'].includes(v.quench_time_source)&&txt(v.time_revision_reason,2000)
    &&(![v.pulled_time_source,v.quench_time_source].includes('corrected')||!!v.time_revision_reason.trim());}
  function validSample(v){return !!v&&typeof v.experiment_id==='string'&&(v.timer_id===null||typeof v.timer_id==='string')&&name(v.label)&&(v.planned_ms===null||number(v.planned_ms))&&stamp(v.pulled)&&number(v.elapsed_ms)&&number(v.recorded_elapsed_ms)&&number(v.recorded_quench_delay_ms)
    &&!!v.quench&&name(v.quench.agent)&&txt(v.quench.agent,100)&&stamp(v.quench.at)&&number(v.quench.delay_ms)&&validSampleValues(v)&&validTimeSources(v)&&typeof v.archived==='boolean'&&Array.isArray(v.revisions);}
  function runFrom(x){return {process:x.process,target:(x.target||'').trim(),oxidant:(x.oxidant||'').trim(),oxidant_mm:x.oxidant_mm??null,wavelength_nm:x.wavelength_nm??null,fluence_rate_mw_cm2:x.fluence_rate_mw_cm2??null};}
  function setRun(l,e,run,c){const r=runFrom(run);assert(validRun(r)&&stamp(c));e.run=r;event(l,e.id,'run_edit',`${r.process}${r.target?' · '+r.target:''}`,c);return r;}
  function setWater(l,e,water,c){const w={matrix:water.matrix,lot:(water.lot||'').trim(),filtered:water.filtered??null,spiked:water.spiked??null};for(const k of WATER_NUMBERS)w[k]=water[k]??null;assert(validWater(w)&&stamp(c));e.water=w;event(l,e.id,'water_edit',w.matrix,c);return w;}
  function suva(w){return w&&w.doc_mg_c_l>0&&w.uv254_cm1!=null?w.uv254_cm1/w.doc_mg_c_l*100:null;}
  function waterCount(w){return w?WATER_NUMBERS.filter(k=>w[k]!==null).length:0;}
  /* Record a sample pulled at `pulled`. A quench is required; its delay is measured from the pull. */
  function sample(l,experiment_id,{timer_id=null,pulled,quench,ph=null,temp_c=null,volume_ml=null,ph_source,temp_c_source,volume_ml_source,note=''},c){
    const e=l.experiments.find(x=>x.id===experiment_id);assert(e&&!e.archived&&!e.ended&&stamp(pulled)&&stamp(c)&&quench&&stamp(quench.at)&&clockDifference(e.started,pulled)>=0&&clockDifference(pulled,quench.at)>=0);
    const label='S-'+String(l.samples.filter(v=>v.experiment_id===e.id).length+1).padStart(3,'0');
    let ev,planned=null;
    if(timer_id){const t=l.timers.find(x=>x.id===timer_id);assert(t&&t.experiment_id===e.id&&t.purpose==='sample'&&!t.archived);planned=t.duration_ms;ev=operate(l,t,'finish',pulled);}
    else ev=event(l,e.id,'sample_taken',label,pulled,{planned_ms:null});
    const elapsed_ms=experimentElapsed(e,pulled),delay_ms=delta(pulled,quench.at);
    const v={id:id(),experiment_id:e.id,timer_id,label,planned_ms:planned,pulled:clone(pulled),elapsed_ms,recorded_elapsed_ms:elapsed_ms,quench:{agent:String(quench.agent).trim(),at:clone(quench.at),delay_ms},recorded_quench_delay_ms:delay_ms,
      pulled_time_source:'click',quench_time_source:'click',time_revision_reason:'',ph,temp_c,volume_ml,ph_source:ph===null?'unmeasured':ph_source||'unknown',temp_c_source:temp_c===null?'unmeasured':temp_c_source||'unknown',volume_ml_source:volume_ml===null?'unmeasured':volume_ml_source||'unknown',note,peak_area:null,c_over_c0:null,fit_excluded:false,fit_exclusion_reason:'',archived:false,revisions:[]};
    assert(validSample(v));ev.sample_id=v.id;ev.label=(timer_id?`${label} · ${ev.label}`:label).slice(0,300);l.samples.push(v);return v;}
  /* The original button-click anchors stay unchanged. Corrected offsets need a reason and the run bounds. */
  function sampleValues(v){const out={};for(const k of SAMPLE_FIELDS)out[k]=k==='quench_delay_ms'?v.quench.delay_ms:v[k];return out;}
  function editSample(v,changes,c,experiment=null){const next={...v,quench:{...v.quench}};
    for(const k of SAMPLE_FIELDS)if(k in changes&&k!=='quench_delay_ms'&&k!=='pulled_time_source'&&k!=='quench_time_source')next[k]=changes[k];
    if('quench_delay_ms' in changes)next.quench.delay_ms=changes.quench_delay_ms;
    for(const k of ['ph','temp_c','volume_ml']){if(k in changes&&next[k]!==v[k]&&!(k+'_source' in changes))next[k+'_source']=next[k]===null?'unmeasured':'measured';if(next[k]===null)next[k+'_source']='unmeasured';}
    const pullChanged=next.elapsed_ms!==v.elapsed_ms,quenchChanged=next.quench.delay_ms!==v.quench.delay_ms;
    if(pullChanged||quenchChanged){assert(experiment&&experiment.id===v.experiment_id&&name(changes.time_revision_reason)&&txt(changes.time_revision_reason,2000));
      assert(next.elapsed_ms+next.quench.delay_ms<=experimentElapsed(experiment,c));
      if(pullChanged)next.pulled_time_source='corrected';if(pullChanged||quenchChanged)next.quench_time_source='corrected';next.time_revision_reason=changes.time_revision_reason.trim();}
    if(next.fit_excluded&&(!v.fit_excluded||!!v.fit_exclusion_reason.trim()))assert(name(next.fit_exclusion_reason));
    if(!next.fit_excluded)next.fit_exclusion_reason='';
    assert(validSample(next)&&stamp(c));const before=sampleValues(v),after=sampleValues(next);
    if(SAMPLE_FIELDS.some(k=>after[k]!==before[k])){const old={...clone(before),at:clone(c),reason:pullChanged||quenchChanged?next.time_revision_reason:next.fit_excluded?next.fit_exclusion_reason:''};v.revisions.push(old);for(const k of SAMPLE_FIELDS)if(k!=='quench_delay_ms')v[k]=next[k];v.quench.delay_ms=next.quench.delay_ms;}return v;}
  function correctSampleTimes(l,v,changes,c){const e=l.experiments.find(e=>e.id===v.experiment_id);return editSample(v,changes,c,e);}
  function runSamples(l,experiment_id){return l.samples.filter(v=>v.experiment_id===experiment_id&&!v.archived).sort((a,b)=>a.elapsed_ms-b.elapsed_ms);}
  /* The earliest sampling checkpoint that has not been pulled, with a timing state for the bench. */
  function nextSample(l,e,c){const pending=l.timers.filter(t=>t.experiment_id===e.id&&t.purpose==='sample'&&!t.archived&&['running','paused'].includes(t.status)).sort((a,b)=>a.duration_ms-b.duration_ms);
    if(!pending.length)return null;const t=pending[0],left=t.duration_ms-experimentElapsed(e,c);
    return {timer:t,left_ms:left,state:left>READY_MS?'wait':left>0?'ready':-left<=LATE_MS?'due':'late'};}
  const T95=[[1,12.706],[2,4.303],[3,3.182],[4,2.776],[5,2.571],[6,2.447],[7,2.365],[8,2.306],[9,2.262],[10,2.228],[12,2.179],[15,2.131],[20,2.086],[25,2.06],[30,2.042],[40,2.021],[60,2],[120,1.98]];
  // Two-sided 95% t values; between tabulated rows the smaller df is used, which widens the interval.
  const tcrit=df=>{if(df>120)return 1.96;let v=T95[0][1];for(const [d,t] of T95)if(df>=d)v=t;return v;};
  /* Pseudo-first-order fit: ordinary least squares of ln(C/C0) against pulled time in minutes. */
  function fit(samples){const pts=samples.filter(v=>!v.archived&&!v.fit_excluded&&v.c_over_c0>0).map(v=>({x:v.elapsed_ms/60000,y:Math.log(v.c_over_c0)}));const n=pts.length;if(n<3)return null;
    const mx=pts.reduce((s,p)=>s+p.x,0)/n,my=pts.reduce((s,p)=>s+p.y,0)/n;let sxx=0,sxy=0,syy=0;for(const p of pts){sxx+=(p.x-mx)**2;sxy+=(p.x-mx)*(p.y-my);syy+=(p.y-my)**2;}if(sxx===0)return null;
    const b=sxy/sxx,a=my-b*mx,ssr=pts.reduce((s,p)=>s+(p.y-a-b*p.x)**2,0),se=Math.sqrt(ssr/(n-2)/sxx),k=-b,half=tcrit(n-2)*se;
    return {n,k_per_min:k,ci95:[k-half,k+half],half_life_min:k>0?Math.LN2/k:null,r2:syy>0?1-ssr/syy:null,intercept:a,points:pts,curvature:curvature(pts)};}
  /* Curvature diagnostic: test the quadratic term in ln(C/C0), with centred/scaled time.
     The sign describes the curve; it does not identify a reaction mechanism or select points. */
  function curvature(pts){const n=pts.length;if(n<5)return {shape:null,reason:'too_few'};
    const centre=pts.reduce((s,p)=>s+p.x,0)/n,scale=Math.max(...pts.map(p=>Math.abs(p.x-centre)));if(!Number.isFinite(scale)||scale===0)return {shape:null,reason:'degenerate'};
    const scaled=pts.map(p=>({x:(p.x-centre)/scale,y:p.y}));
    const s=[0,0,0,0,0],r=[0,0,0];for(const p of scaled){let xp=1;for(let k=0;k<5;k++){s[k]+=xp;if(k<3)r[k]+=xp*p.y;xp*=p.x;}}
    const M=[[s[0],s[1],s[2]],[s[1],s[2],s[3]],[s[2],s[3],s[4]]],inv=inverse3(M);if(!inv)return {shape:null,reason:'degenerate'};
    const beta=inv.map(row=>row[0]*r[0]+row[1]*r[1]+row[2]*r[2]),ssr=scaled.reduce((t,p)=>t+(p.y-beta[0]-beta[1]*p.x-beta[2]*p.x*p.x)**2,0);
    const tolerance=64*Number.EPSILON*Math.max(1,...pts.map(p=>Math.abs(p.y)));
    const se=Math.sqrt(Math.max(0,ssr/(n-3)*inv[2][2])),c=beta[2]/scale**2,tval=Math.abs(beta[2])<=tolerance?0:se>0?beta[2]/se:Infinity*Math.sign(c);
    const significant=Math.abs(tval)>tcrit(n-3);return {shape:significant?(c<0?'lag':'tailing'):'linear',c,t:tval};}
  function inverse3(m){const [a,b,c]=m[0],[d,e,f]=m[1],[g,h,i]=m[2],A=e*i-f*h,B=-(d*i-f*g),C=d*h-e*g,det=a*A+b*B+c*C;if(!Number.isFinite(det)||Math.abs(det)<1e-12*Math.max(1,Math.abs(a*e*i)))return null;
    return [[A,-(b*i-c*h),b*f-c*e],[B,a*i-c*g,-(a*f-c*d)],[C,-(a*h-b*g),a*e-b*d]].map(row=>row.map(x=>x/det));}
  /* Rate constants normalised to the run's conditions. Fluence-based k'_E = k_obs(s⁻¹) / E₀(mW cm⁻² = mJ cm⁻² s⁻¹). */
  function normalised(f,run){if(!f||!run)return {};const ks=f.k_per_min/60,out={k_per_s:ks};
    if(run.fluence_rate_mw_cm2>0){out.k_fluence_cm2_mj=ks/run.fluence_rate_mw_cm2;out.ci_fluence=f.ci95.map(k=>k/60/run.fluence_rate_mw_cm2);}
    if(run.oxidant_mm>0)out.k_per_min_per_mm=f.k_per_min/run.oxidant_mm;return out;}
  /* Paste from an LC export: "S-003 12345" (tab, comma, semicolon or spaces) or one area per line in sample order. */
  function parseAreas(text,samples){const entries=[],errors=[],lines=String(text??'').split(/\r?\n/).map((text,i)=>({text:text.trim(),line:i+1}));
    // Outer whitespace is harmless. An empty row inside ordered data represents a missing sample.
    while(lines.length&&!lines[0].text)lines.shift();while(lines.length&&!lines.at(-1).text)lines.pop();
    if(!lines.length)return {entries,errors};
    const parts=line=>line.split(/[\t,;]+|\s{1,}/).filter(Boolean);
    const header=/^(?:sample(?:[ _-]?id)?|样品(?:号|编号)?)\s*[,;\t ]+\s*(?:area|peak[ _]?area|峰面积)$/i;
    let labelled=parts(lines[0].text).length>1;if(header.test(lines[0].text)){labelled=true;lines.shift();}
    const num=x=>{if(!/^[+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(x??''))return null;const n=Number(x);return Number.isFinite(n)&&n>=0?n:null;};
    for(const [i,row] of lines.entries()){const p=parts(row.text);if(!row.text){errors.push({...row,reason:'missing'});continue;}
      if(labelled){if(p.length!==2){errors.push({...row,reason:'format'});continue;}
        const v=samples.find(x=>x.label.toUpperCase()===p[0].toUpperCase()),area=num(p[1]);
        if(!v||area==null){errors.push({...row,reason:v?'number':'label'});continue;}entries.push({sample:v,area});
      }else{const v=samples[i],area=p.length===1?num(p[0]):null;
        if(p.length!==1){errors.push({...row,reason:'mixed'});continue;}if(area==null){errors.push({...row,reason:'number'});continue;}
        if(!v){errors.push({...row,reason:'extra'});continue;}entries.push({sample:v,area});}}
    const seen=new Set();for(const e of entries){if(seen.has(e.sample.id))errors.push({line:0,text:e.sample.label,reason:'duplicate'});seen.add(e.sample.id);}
    return {entries,errors};}
  const canApplyAreas=(parsed,reference)=>Number.isFinite(reference)&&reference>0&&parsed.entries.length>0&&parsed.errors.length===0;
  /* Apply peak areas: C/C0 = area ÷ reference area. Each sample's earlier values stay in its history. */
  function applyAreas(l,entries,reference,c){assert(Number.isFinite(reference)&&reference>0&&entries.length&&stamp(c));const ids=new Set(entries.map(e=>e.sample.id));assert(ids.size===entries.length);
    // Validate the entire batch before changing a sample; malformed data must not leave a partial import.
    const values=entries.map(({sample,area})=>{const v=l.samples.find(x=>x.id===sample.id),ratio=area/reference;assert(v&&!v.archived&&number(area)&&Number.isFinite(ratio));const cc=ratio<Number.MAX_SAFE_INTEGER/1e6?Math.round(ratio*1e6)/1e6:ratio;assert(validSample({...v,peak_area:area,c_over_c0:cc}));return {v,area,cc};});
    assert(new Set(values.map(x=>x.v.experiment_id)).size===1);
    return values.map(({v,area,cc})=>editSample(v,{peak_area:area,c_over_c0:cc},c));}
  const SAMPLE_COLUMNS=['schema','run_id','run_title','process','target','oxidant','oxidant_mm','wavelength_nm','fluence_rate_mw_cm2','matrix','matrix_lot','filtered_0_45um','target_spiked',...WATER_NUMBERS.map(k=>k==='ph'?'matrix_ph':k),'suva254_l_mg_m','sample_id','sample_label','planned_s','pulled_s','delta_s','pulled_at_utc','quench_agent','quench_delay_s','ph','temp_c','volume_ml','fluence_mj_cm2','peak_area','c_over_c0','fit_excluded','note','ph_source','temp_c_source','volume_ml_source','pulled_time_source','quench_time_source','recorded_pulled_s','recorded_quench_delay_s','quench_at_utc','time_revision_reason','fit_exclusion_reason'];
  /* Tidy export, one row per sample, in the shared EnvBench CSV schema v1. */
  function samplesCsv(l,experiment_id=null){const rows=[SAMPLE_COLUMNS];const s1=x=>x==null?'':Math.round(x/100)/10;
    for(const e of l.experiments.filter(e=>!experiment_id||e.id===experiment_id))for(const v of runSamples(l,e.id)){const r=e.run||{},w=e.water||{},sv=suva(e.water);
      rows.push(['envbench-samples-v1',e.id,e.title,r.process,r.target,r.oxidant,r.oxidant_mm,r.wavelength_nm,r.fluence_rate_mw_cm2,w.matrix,w.lot,w.filtered,w.spiked,...WATER_NUMBERS.map(k=>w[k]),sv==null?'':Math.round(sv*1000)/1000,v.id,v.label,s1(v.planned_ms),s1(v.elapsed_ms),v.planned_ms==null?'':s1(v.elapsed_ms-v.planned_ms),new Date(v.pulled.wall).toISOString(),v.quench.agent,s1(v.quench.delay_ms),v.ph,v.temp_c,v.volume_ml,r.fluence_rate_mw_cm2>0?Math.round(r.fluence_rate_mw_cm2*v.elapsed_ms/100)/10:'',v.peak_area,v.c_over_c0,v.fit_excluded,v.note,v.ph_source,v.temp_c_source,v.volume_ml_source,v.pulled_time_source,v.quench_time_source,s1(v.recorded_elapsed_ms),s1(v.recorded_quench_delay_ms),new Date(v.quench.at.wall).toISOString(),v.time_revision_reason,v.fit_exclusion_reason]);}
    const safe=v=>{if(typeof v==='number')return String(v);let s=String(v??'');if(/^[\s]*[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};return '﻿'+rows.map(r=>r.map(safe).join(',')).join('\r\n');}
  return {id,clone,assert,palettes,empty,upgrade,migrate,validate,delta,elapsed,experimentElapsed,remaining,event,experiment,timer,operate,archiveTimer,finishExperiment,counter,count,record,editRecord,schedule,time,merge,csv,
    PROCESSES,MATRICES,WATER_NUMBERS,MEASUREMENT_SOURCES,READY_MS,LATE_MS,setRun,setWater,suva,waterCount,sample,editSample,correctSampleTimes,runSamples,nextSample,fit,curvature,normalised,parseAreas,canApplyAreas,applyAreas,samplesCsv};
});
