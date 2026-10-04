/* Experiment procedures are immutable template snapshots; reaction clocks stay in Lab. */
(function(root,factory){const api=factory(typeof module==='object'?require('./lab-domain.js'):root.Lab);if(typeof module==='object')module.exports=api;else root.Flow=api;})(globalThis,function(L){
  'use strict';
  const COLLECTIONS=['workflows','experiment_templates','observation_phrases'];
  const STATES=['pending','active','completed','skipped'];
  const ACTIONS=['start','complete','reopen','skip','cancel','import_pause'];
  const assert=ok=>{if(!ok)throw new Error('invalid');};
  const clone=L.clone,id=L.id;
  const isId=x=>typeof x==='string'&&/^[a-f0-9]{32}$/.test(x);
  const txt=(x,n=20000)=>typeof x==='string'&&x.length<=n;
  const name=x=>txt(x,300)&&!!x.trim();
  const num=x=>Number.isFinite(x)&&x>=0;
  const stamp=x=>!!x&&num(x.wall)&&num(x.mono)&&txt(x.boot,100);
  const unique=x=>Array.isArray(x)&&new Set(x.map(v=>v.id)).size===x.length;
  const difference=(a,b)=>a.boot===b.boot?b.mono-a.mono:b.wall-a.wall;
  function defaults(l){assert(l&&l.version===2);for(const k of COLLECTIONS)if(!(k in l))l[k]=[];return l;}
  function checkedCopy(l){const d=defaults(clone(l));validate(d);L.validate(d);return d;}
  // Reconcile by ID so existing experiment/record references survive an atomic commit.
  function reconcile(target,source){
    if(Array.isArray(source)){
      const old=target.slice(),byId=new Map(old.filter(x=>x&&typeof x==='object'&&isId(x.id)).map(x=>[x.id,x]));
      const next=source.map((s,i)=>{if(s&&typeof s==='object'){const t=isId(s.id)?byId.get(s.id):old[i];if(t&&typeof t==='object'&&Array.isArray(t)===Array.isArray(s)){reconcile(t,s);return t;}return clone(s);}return s;});
      target.splice(0,target.length,...next);return target;
    }
    for(const k of Object.keys(target))if(!(k in source))delete target[k];
    for(const [k,s] of Object.entries(source))if(s&&typeof s==='object'){
      if(target[k]&&typeof target[k]==='object'&&Array.isArray(target[k])===Array.isArray(s))reconcile(target[k],s);else target[k]=clone(s);
    }else target[k]=s;
    return target;
  }
  function transaction(l,build,read){const d=checkedCopy(l),result=build(d);validate(d);L.validate(d);reconcile(l,d);return read?read(l,result):result;}
  function ensure(l){return reconcile(l,checkedCopy(l));}
  function item(l,key,x){const v=l[key].find(v=>v.id===(typeof x==='string'?x:x?.id));assert(v);return v;}
  function experiment(l,x){return item(l,'experiments',x);}
  function template(l,x){return (l.experiment_templates||[]).find(t=>t.id===(typeof x==='string'?x:x?.id))||null;}
  function workflow(l,e){const experimentId=typeof e==='string'?e:e?.id;return (l.workflows||[]).find(w=>w.experiment_id===experimentId)||null;}
  function activeStep(l,e){return workflow(l,e)?.steps.find(s=>s.status==='active')||null;}
  function runFrom(x){if(x===null)return null;assert(x&&typeof x==='object');const r={process:x.process,target:x.target??'',oxidant:x.oxidant??'',oxidant_mm:x.oxidant_mm??null,wavelength_nm:x.wavelength_nm??null,fluence_rate_mw_cm2:x.fluence_rate_mw_cm2??null};assert(L.PROCESSES.includes(r.process)&&txt(r.target,300)&&txt(r.oxidant,100));for(const k of ['oxidant_mm','wavelength_nm','fluence_rate_mw_cm2'])assert(r[k]===null||num(r[k]));r.target=r.target.trim();r.oxidant=r.oxidant.trim();return r;}
  function waterFrom(x){if(x===null)return null;assert(x&&typeof x==='object');const w={matrix:x.matrix,lot:x.lot??'',filtered:x.filtered??null,spiked:x.spiked??null};assert(L.MATRICES.includes(w.matrix)&&txt(w.lot,100));for(const k of ['filtered','spiked'])assert(w[k]===null||typeof w[k]==='boolean');for(const k of L.WATER_NUMBERS){w[k]=x[k]??null;assert(w[k]===null||(num(w[k])&&(k!=='ph'||w[k]<=14)));}w.lot=w.lot.trim();return w;}
  function minutesFrom(x){assert(Array.isArray(x)&&x.every(n=>Number.isFinite(n)&&n>0&&n<=525600));return [...new Set(x)].sort((a,b)=>a-b);}
  function presetFrom(x){
    assert(x&&typeof x==='object');const options={title:x.title,kind:x.kind??'stopwatch',duration_ms:x.duration_ms??0,color:x.color??'#186B62',purpose:'timer'};
    for(const k of ['stages','repeat_count','delay_ms','transition_mode'])if(k in x)options[k]=clone(x[k]);
    const l=defaults(L.empty()),c={wall:0,mono:0,boot:'template'};if(options.kind==='staged')options.experiment_id=L.experiment(l,'Template validation','','',c).id;const t=L.timer(l,options,c);L.validate(l);
    const p={title:t.title,kind:t.kind,duration_ms:t.duration_ms,color:t.color};for(const k of ['stages','repeat_count','delay_ms','transition_mode'])if(k in t)p[k]=clone(t[k]);return p;
  }
  function definition(x,preserveIds=false){
    assert(x&&typeof x==='object'&&name(x.title)&&txt(x.description??''));
    const d={title:x.title.trim(),description:x.description??'',run:runFrom(x.run??null),water:waterFrom(x.water??null),planned_minutes:minutesFrom(x.planned_minutes??[]),timer_presets:(x.timer_presets??[]).map(presetFrom),steps:[]};
    assert(Array.isArray(x.steps??[])&&Array.isArray(x.timer_presets??[]));
    d.steps=(x.steps??[]).map(s=>{assert(s&&name(s.title)&&txt(s.description??'')&&num(s.duration_ms??0));return {id:preserveIds&&isId(s.id)?s.id:id(),title:s.title.trim(),description:s.description??'',duration_ms:s.duration_ms??0};});assert(unique(d.steps));return d;
  }
  function validDefinition(t){
    assert(t&&name(t.title)&&txt(t.description)&&unique(t.steps)&&Array.isArray(t.planned_minutes)&&Array.isArray(t.timer_presets??[]));
    runFrom(t.run);waterFrom(t.water);assert(JSON.stringify(minutesFrom(t.planned_minutes))===JSON.stringify(t.planned_minutes));
    for(const s of t.steps)assert(isId(s.id)&&name(s.title)&&txt(s.description)&&num(s.duration_ms));
    for(const p of t.timer_presets??[])presetFrom(p);return true;
  }
  function validate(l){
    assert(l&&l.version===2);for(const k of COLLECTIONS){assert(unique(l[k]));for(const v of l[k])assert(isId(v.id));}
    for(const t of l.experiment_templates){validDefinition(t);assert(Number.isSafeInteger(t.version)&&t.version>=1&&stamp(t.created)&&stamp(t.updated)&&typeof t.archived==='boolean');}
    const parents=new Set();
    for(const w of l.workflows){
      assert(isId(w.experiment_id)&&l.experiments.some(e=>e.id===w.experiment_id)&&!parents.has(w.experiment_id));parents.add(w.experiment_id);
      assert((w.template_id===null||isId(w.template_id))&&(w.template_version===null||(Number.isSafeInteger(w.template_version)&&w.template_version>=1))&&stamp(w.created)&&(w.ended===null||stamp(w.ended))&&unique(w.steps));
      validDefinition(w.template_snapshot);assert(w.template_snapshot.id===w.template_id&&w.template_snapshot.version===w.template_version&&w.steps.length===w.template_snapshot.steps.length);
      assert(w.steps.filter(s=>s.status==='active').length<=1);
      for(const [i,s] of w.steps.entries()){
        const original=w.template_snapshot.steps[i];assert(isId(s.id)&&s.template_step_id===original.id&&s.title===original.title&&s.description===original.description&&s.duration_ms===original.duration_ms&&STATES.includes(s.status));
        assert((s.timer_id===null||isId(s.timer_id))&&(s.started===null||stamp(s.started))&&(s.ended===null||stamp(s.ended))&&txt(s.skip_reason,2000)&&unique(s.history));
        if(s.status==='pending')assert(s.started===null&&s.ended===null&&s.timer_id===null&&!s.skip_reason);
        if(s.status==='active')assert(stamp(s.started)&&s.ended===null&&!s.skip_reason&&(s.duration_ms===0?s.timer_id===null:isId(s.timer_id)));
        if(s.status==='completed')assert(stamp(s.started)&&stamp(s.ended)&&!s.skip_reason);
        if(s.status==='skipped')assert(stamp(s.ended)&&!!s.skip_reason.trim());
        if(s.timer_id!==null){const t=l.timers.find(t=>t.id===s.timer_id);assert(t&&t.experiment_id===w.experiment_id&&t.purpose==='timer'&&t.kind==='countdown'&&t.duration_ms===s.duration_ms);}
        for(const h of s.history){assert(isId(h.id)&&ACTIONS.includes(h.action)&&STATES.includes(h.status_before)&&STATES.includes(h.status_after)&&stamp(h.at)&&txt(h.reason,2000)&&(h.timer_id===null||isId(h.timer_id)));if(['skip','cancel'].includes(h.action))assert(!!h.reason.trim());if(h.timer_id!==null)assert(l.timers.some(t=>t.id===h.timer_id&&t.experiment_id===w.experiment_id));}
      }
      if(w.ended!==null)assert(w.steps.every(s=>['completed','skipped'].includes(s.status)));
    }
    const phrases=new Set();for(const p of l.observation_phrases){assert(txt(p.text,2000)&&!!p.text.trim()&&stamp(p.created)&&stamp(p.updated)&&!phrases.has(p.text.trim()));phrases.add(p.text.trim());}
    return l;
  }
  /* Run only after base records and workflows have both been loaded or merged. */
  function validateRecordLinks(l){assert(l&&Array.isArray(l.records)&&Array.isArray(l.workflows));for(const r of l.records)if('step_id' in r&&r.step_id!==null){const w=workflow(l,r.experiment_id);assert(isId(r.step_id)&&w&&w.steps.some(s=>s.id===r.step_id));}return l;}
  function createTemplate(l,x,c){assert(stamp(c));return transaction(l,d=>{const t={id:id(),version:1,...definition(x),created:clone(c),updated:clone(c),archived:false};d.experiment_templates.push(t);return t.id;},(l,key)=>template(l,key));}
  function updateTemplate(l,t,changes,c){assert(stamp(c)&&changes&&typeof changes==='object');return transaction(l,d=>{const old=item(d,'experiment_templates',t),next=definition({...old,...changes},true);assert(old.version<Number.MAX_SAFE_INTEGER);Object.assign(old,next,{version:old.version+1,updated:clone(c)});return old.id;},(l,key)=>template(l,key));}
  function fromExperiment(l,e,overrides={}){
    const d=checkedCopy(l),source=experiment(d,e),w=workflow(d,source),related=new Set((w?.steps||[]).flatMap(s=>[s.timer_id,...s.history.map(h=>h.timer_id)]).filter(Boolean));
    const values={title:source.title,description:source.description,run:clone(source.run),water:clone(source.water),planned_minutes:minutesFrom(d.timers.filter(t=>t.experiment_id===source.id&&t.purpose==='sample'&&!t.archived).map(t=>t.duration_ms/60000)),timer_presets:d.timers.filter(t=>t.experiment_id===source.id&&t.purpose==='timer'&&!t.archived&&!related.has(t.id)).map(presetFrom),steps:(w?.template_snapshot.steps||[]).map(s=>({title:s.title,description:s.description,duration_ms:s.duration_ms})),...overrides};
    return definition(values);
  }
  function snapshot(l,x){const t=typeof x==='string'?template(l,x):x?.id?template(l,x.id):null;if(typeof x==='string')assert(t);if(t){assert(!t.archived);return {id:t.id,version:t.version,...definition(t,true)};}return {id:null,version:null,...definition(x)};}
  function attachSnapshot(l,e,snap,c){assert(stamp(c)&&!e.ended&&!e.archived&&!workflow(l,e));validDefinition(snap);const w={id:id(),experiment_id:e.id,template_id:snap.id,template_version:snap.version,template_snapshot:clone(snap),created:clone(c),ended:null,steps:snap.steps.map(s=>({id:id(),template_step_id:s.id,title:s.title,description:s.description,duration_ms:s.duration_ms,status:'pending',timer_id:null,started:null,ended:null,skip_reason:'',history:[]}))};l.workflows.push(w);L.event(l,e.id,'workflow_attach',snap.title,c,{workflow_id:w.id,template_id:w.template_id,template_version:w.template_version});return w;}
  function attach(l,e,x,c){return attachSnapshot(l,e,snapshot(l,x),c);}
  function attachWorkflow(l,e,x,c){return transaction(l,d=>attach(d,experiment(d,e),x,c).id,(l,key)=>item(l,'workflows',key));}
  function startExperiment(l,x,options={},c){
    assert(options&&typeof options==='object'&&stamp(c));return transaction(l,d=>{const snap=snapshot(d,x),values=definition({...snap,...options},true),sample=options.sample??'';assert(txt(sample,300));const e=L.experiment(d,values.title,values.description,sample,c);if(values.run)L.setRun(d,e,values.run,c);if(values.water)L.setWater(d,e,values.water,c);if(values.planned_minutes.length)L.schedule(d,e,values.planned_minutes,c);for(const p of values.timer_presets)L.timer(d,{...clone(p),experiment_id:e.id,purpose:'timer'},c);
      // Conditions may be adjusted for this run; its snapshot is the exact starting definition.
      const w=attachSnapshot(d,e,{id:snap.id,version:snap.version,...values},c);return {experiment_id:e.id,workflow_id:w.id};},(l,r)=>({experiment:item(l,'experiments',r.experiment_id),workflow:item(l,'workflows',r.workflow_id)}));
  }
  function audit(l,w,s,action,before,c,reason=''){
    const h={id:id(),action,status_before:before,status_after:s.status,at:clone(c),reason,timer_id:s.timer_id};s.history.push(h);L.event(l,w.experiment_id,'step_'+action,s.title,c,{workflow_id:w.id,step_id:s.id,status_before:before,status_after:s.status,reason,timer_id:s.timer_id});return h;
  }
  function stopTimer(l,s,c){if(s.timer_id!==null){const t=item(l,'timers',s.timer_id);if(['running','paused','waiting'].includes(t.status))L.operate(l,t,'finish',c);}}
  function operateStep(l,w,s,action,c,reason=''){
    assert(stamp(c)&&ACTIONS.includes(action)&&!['cancel','import_pause'].includes(action)&&txt(reason,2000));return transaction(l,d=>{const flow=item(d,'workflows',w),step=item(flow,'steps',s),e=experiment(d,flow.experiment_id),before=step.status;assert(!e.ended&&!e.archived&&flow.ended===null&&difference(e.started,c)>=0);if(step.started)assert(difference(step.started,c)>=0);
      if(action==='start'){assert(before==='pending'&&!flow.steps.some(s=>s.status==='active'));step.status='active';step.started=clone(c);if(step.duration_ms>0){const t=L.timer(d,{title:step.title,kind:'countdown',duration_ms:step.duration_ms,experiment_id:e.id,purpose:'timer'},c);L.operate(d,t,'start',c);step.timer_id=t.id;}}
      else if(action==='complete'){assert(before==='active');stopTimer(d,step,c);step.status='completed';step.ended=clone(c);}
      else if(action==='skip'){assert(['pending','active'].includes(before)&&!!reason.trim());stopTimer(d,step,c);step.status='skipped';step.skip_reason=reason.trim();step.ended=clone(c);}
      else {assert(['completed','skipped'].includes(before));step.status='pending';step.timer_id=null;step.started=null;step.ended=null;step.skip_reason='';}
      audit(d,flow,step,action,before,c,action==='skip'?reason.trim():reason);return {workflow_id:flow.id,step_id:step.id};},(l,r)=>item(item(l,'workflows',r.workflow_id),'steps',r.step_id));
  }
  function cancel(l,e,c){const w=workflow(l,e);if(!w||w.ended!==null)return w;for(const s of w.steps)if(['pending','active'].includes(s.status)){const before=s.status;stopTimer(l,s,c);s.status='skipped';s.skip_reason='实验结束，步骤未完成';s.ended=clone(c);audit(l,w,s,'cancel',before,c,s.skip_reason);}w.ended=clone(c);return w;}
  function cancelWorkflow(l,e,c){assert(stamp(c));return transaction(l,d=>{const source=experiment(d,e);const end=source.ended||c;assert(difference(source.started,end)>=0);return cancel(d,source,end)?.id||null;},(l,key)=>key?item(l,'workflows',key):null);}
  function finishExperiment(l,e,c){assert(stamp(c));return transaction(l,d=>{const source=experiment(d,e);assert(!source.ended&&difference(source.started,c)>=0);cancel(d,source,c);L.finishExperiment(d,source,c);return source.id;},(l,key)=>item(l,'experiments',key));}
  function setPhrases(l,phrases,c){assert(Array.isArray(phrases)&&phrases.every(x=>txt(x,2000)&&!!x.trim())&&stamp(c));return transaction(l,d=>{const texts=[...new Set(phrases.map(x=>x.trim()))];d.observation_phrases=texts.map(text=>d.observation_phrases.find(p=>p.text===text)||{id:id(),text,created:clone(c),updated:clone(c)});return null;},l=>l.observation_phrases);}
  /* Lab.merge imports base records first. This stage preserves local objects with equal IDs. */
  function merge(current,incoming,c){
    assert(stamp(c));const source=checkedCopy(incoming),d=checkedCopy(current);let added=0;
    for(const k of COLLECTIONS)for(const v of source[k])if(!d[k].some(x=>x.id===v.id)){
      if(k==='observation_phrases'&&d[k].some(x=>x.text===v.text))continue;
      const next=clone(v);
      if(k==='workflows')for(const s of next.steps)if(s.status==='active'&&s.timer_id){const t=item(d,'timers',s.timer_id);if(t.status==='running'){t.elapsed_ms=L.elapsed(t,c);t.anchor=null;t.status='paused';}const original=source.timers.find(t=>t.id===s.timer_id);if(original?.status==='running')s.history.push({id:id(),action:'import_pause',status_before:'active',status_after:'active',at:clone(c),reason:'导入后暂停关联计时器',timer_id:s.timer_id});}
      d[k].push(next);added++;
    }
    validate(d);L.validate(d);return {lab:d,added};
  }
  function forExperiment(l,experimentId){
    const d=checkedCopy(l);assert(d.experiments.some(e=>e.id===experimentId));
    for(const k of ['experiments','timers','counters','records','events','samples','workflows'])d[k]=d[k].filter(x=>(k==='experiments'?x.id:x.experiment_id)===experimentId);
    const references=new Set(d.workflows.map(w=>w.template_id).filter(Boolean));
    d.experiment_templates=d.experiment_templates.filter(x=>references.has(x.id));
    d.observation_phrases=[];d.demo_loaded=false;L.validate(d);validate(d);validateRecordLinks(d);return d;
  }
  return {ensure,validate,validateRecordLinks,template,createTemplate,updateTemplate,fromExperiment,startExperiment,attachWorkflow,workflow,operateStep,activeStep,cancelWorkflow,finishExperiment,setPhrases,merge,forExperiment,STATES};
});


