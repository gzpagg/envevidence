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
  function empty(){return {version:1,experiments:[],timers:[],counters:[],records:[],events:[],demo_loaded:false};}
  function migrate(s){if(!s.lab){s.lab=empty();const p=s.workspace.preferences;if(p.palette==='forest'&&p.accent.toUpperCase()==='#147D73'&&p.background.toUpperCase()==='#F6F8F7'){p.palette='clay';[p.accent,p.background]=palettes.clay;}}validate(s.lab);return s;}
  function validate(l){assert(l&&l.version===1);for(const k of ['experiments','timers','counters','records','events']){assert(list(l[k]));for(const x of l[k])assert(typeof x.id==='string'&&/^[a-f0-9]{32}$/.test(x.id));}
    const parent=x=>x.experiment_id===null||l.experiments.some(e=>e.id===x.experiment_id);
    for(const e of l.experiments)assert(name(e.title)&&txt(e.description)&&txt(e.sample,300)&&stamp(e.started)&&(e.ended===null||stamp(e.ended))&&typeof e.archived==='boolean');
    for(const t of l.timers)assert(name(t.title)&&parent(t)&&['stopwatch','countdown'].includes(t.kind)&&['idle','running','paused','done'].includes(t.status)&&number(t.elapsed_ms)&&number(t.duration_ms)&&(t.kind!=='countdown'||t.duration_ms>0)&&(t.anchor===null||stamp(t.anchor))&&(t.status!=='running'||stamp(t.anchor))&&Number.isSafeInteger(t.cycle)&&t.cycle>=0&&typeof t.archived==='boolean'&&/^#[a-f\d]{6}$/i.test(t.color)&&['timer','sample'].includes(t.purpose));
    for(const c of l.counters)assert(name(c.title)&&parent(c)&&Number.isSafeInteger(c.value)&&c.value>=0&&Number.isSafeInteger(c.round)&&c.round>=1&&typeof c.archived==='boolean');
    const photo=p=>p&&/^[a-f\d]{32}$/.test(p.id)&&txt(p.name,300)&&['jpg','png','webp'].includes(p.ext)&&/^image\/(jpeg|png|webp)$/.test(p.mime)&&number(p.bytes);
    for(const r of l.records){assert(parent(r)&&txt(r.body)&&txt(r.sample,300)&&stamp(r.at)&&number(r.elapsed_ms)&&typeof r.archived==='boolean'&&Array.isArray(r.photos)&&r.photos.every(photo)&&Array.isArray(r.revisions));for(const v of r.revisions)assert(txt(v.body)&&txt(v.sample,300)&&stamp(v.at));}
    for(const e of l.events)assert(parent(e)&&stamp(e.at)&&name(e.kind)&&txt(e.label,300)&&number(e.elapsed_ms));
    return l;
  }
  function delta(a,b){return Math.max(0,a.boot===b.boot?b.mono-a.mono:b.wall-a.wall);}
  function elapsed(t,c){return t.elapsed_ms+(t.status==='running'?delta(t.anchor,c):0);}
  function experimentElapsed(e,c){return e?delta(e.started,e.ended||c):0;}
  function remaining(t,c){return t.duration_ms-elapsed(t,c);}
  function event(l,experiment_id,kind,label,c,extra={}){const e=l.experiments.find(x=>x.id===experiment_id);const v={id:id(),experiment_id,kind,label,at:clone(c),elapsed_ms:experimentElapsed(e,c),...extra};l.events.push(v);return v;}
  function experiment(l,title,description,sample,c){assert(name(title)&&stamp(c));const e={id:id(),title:title.trim(),description,sample,started:clone(c),ended:null,archived:false};l.experiments.unshift(e);event(l,e.id,'experiment_start',e.title,c);return e;}
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
  function finishExperiment(l,e,c){assert(!e.ended);for(const t of l.timers.filter(t=>t.experiment_id===e.id&&['running','paused'].includes(t.status)))operate(l,t,'finish',c);e.ended=clone(c);event(l,e.id,'experiment_finish',e.title,c);}
  function counter(l,title,experiment_id,c){assert(name(title));const v={id:id(),title:title.trim(),experiment_id,value:0,round:1,archived:false};l.counters.unshift(v);event(l,experiment_id,'counter_create',v.title,c);return v;}
  function count(l,v,action,c){const previous=v.value;if(action==='add'){assert(Number.isSafeInteger(previous+1));v.value++;}else if(action==='undo'){assert(previous>0);v.value--;}else if(action==='reset'){v.round++;v.value=0;}else throw new Error('invalid');return event(l,v.experiment_id,'counter_'+action,v.title,c,{counter_id:v.id,previous,value:v.value,round:v.round});}
  function record(l,experiment_id,body,sample,c){const e=l.experiments.find(x=>x.id===experiment_id);const r={id:id(),experiment_id,body,sample,at:clone(c),elapsed_ms:experimentElapsed(e,c),photos:[],revisions:[],archived:false};l.records.unshift(r);return r;}
  function editRecord(r,body,sample,c){r.revisions.push({body:r.body,sample:r.sample,at:clone(c)});r.body=body;r.sample=sample;}
  function schedule(l,e,minutes,c){assert(!e.ended&&!e.archived&&minutes.length&&minutes.every(n=>Number.isFinite(n)&&n>0&&n<=525600));for(const m of [...new Set(minutes)].sort((a,b)=>a-b)){const t=timer(l,{title:`${e.title} · ${m} min`,kind:'countdown',duration_ms:m*60000,experiment_id:e.id,purpose:'sample'},c);t.anchor=clone(e.started);t.status='running';event(l,e.id,'timer_start',t.title,c,{timer_id:t.id,planned_ms:t.duration_ms});}}
  function time(ms,decimal=false){const n=Math.floor(Math.abs(ms)/1000),h=Math.floor(n/3600),m=Math.floor(n%3600/60),s=n%60;return `${h?String(h).padStart(2,'0')+':':''}${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}${decimal?'.'+Math.floor(Math.abs(ms)%1000/100):''}`;}
  function merge(current,incoming,c){validate(incoming);const l=clone(current);let added=0;for(const k of ['experiments','timers','counters','records','events'])for(const v of incoming[k])if(!l[k].some(x=>x.id===v.id)){const item=clone(v);if(k==='timers'&&item.status==='running'){item.elapsed_ms=elapsed(item,c);item.anchor=null;item.status='paused';}l[k].push(item);added++;}validate(l);return {lab:l,added};}
  function csv(l,experiment_id=null){const rows=[['experiment_id','experiment','kind','recorded_at','elapsed_seconds','label','note','sample','timer_seconds','count','photo_files']];const title=id=>l.experiments.find(e=>e.id===id)?.title||'';for(const e of l.events.filter(e=>!experiment_id||e.experiment_id===experiment_id))rows.push([e.experiment_id,title(e.experiment_id),e.kind,new Date(e.at.wall).toISOString(),e.elapsed_ms/1000,e.label,'','',e.timer_elapsed_ms==null?'':e.timer_elapsed_ms/1000,e.value??'','']);for(const r of l.records.filter(r=>!experiment_id||r.experiment_id===experiment_id))rows.push([r.experiment_id,title(r.experiment_id),'observation',new Date(r.at.wall).toISOString(),r.elapsed_ms/1000,'',r.body,r.sample,'','',r.photos.map(p=>`${p.id}.${p.ext}`).join(';')]);const safe=v=>{let s=String(v??'');if(/^[\s]*[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};return '\ufeff'+rows.map(r=>r.map(safe).join(',')).join('\r\n');}
  return {id,clone,assert,palettes,empty,migrate,validate,delta,elapsed,experimentElapsed,remaining,event,experiment,timer,operate,archiveTimer,finishExperiment,counter,count,record,editRecord,schedule,time,merge,csv};
});
