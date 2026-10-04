const {test}=require('node:test');
const a=require('node:assert/strict'),L=require('../app/src/main/assets/lab-domain.js'),F=require('../app/src/main/assets/flow-domain.js');
const clock=(n=0,wall=n,boot='boot1')=>({wall:1700000000000+wall,mono:10000+n,boot});
const clone=x=>JSON.parse(JSON.stringify(x));
const def=(changes={})=>({title:'UV/PDS standard',description:'Check water then illuminate',run:{process:'UV/PDS',target:'A',oxidant:'PDS',oxidant_mm:1,wavelength_nm:254,fluence_rate_mw_cm2:2},water:{matrix:'mbr_effluent',lot:'L1',doc_mg_c_l:6,ph:7.8},planned_minutes:[5,1,5],steps:[{title:'Prepare water',description:'Measure pH',duration_ms:0},{title:'Mix oxidant',description:'Mix before UV',duration_ms:60000},{title:'Illuminate',description:'Start UV',duration_ms:120000}],...changes});
function setup(){const l=L.empty();F.ensure(l);const t=F.createTemplate(l,def(),clock());const {experiment:e,workflow:w}=F.startExperiment(l,t,{sample:'New lot'},clock());return {l,t,e,w};}
function identicalOnFailure(l,fn){const before=JSON.stringify(l);a.throws(fn);a.equal(JSON.stringify(l),before,'failed action leaves every collection unchanged');}

test('missing extension collections upgrade atomically at version 2 without changing records',()=>{
  const l=L.empty(),e=L.experiment(l,'Original','kept','Old sample',clock()),r=L.record(l,e.id,'Turbid','Old sample',clock(1000));L.editRecord(r,'Clear','Old sample',clock(2000));const originals=clone(l),recordReference=r;
  F.ensure(l);a.equal(l.version,2);a.deepEqual(l.workflows,[]);a.deepEqual(l.experiment_templates,[]);a.deepEqual(l.observation_phrases,[]);for(const k of Object.keys(originals))a.deepEqual(l[k],originals[k]);a.equal(l.records[0],recordReference);F.validate(l);L.validate(l);
  const invalid=L.empty();invalid.experiments=[{id:'a'.repeat(32)}];identicalOnFailure(invalid,()=>F.ensure(invalid));a.equal('workflows' in invalid,false);
});

test('template copies get new IDs and each workflow keeps its template version snapshot',()=>{
  const {l,t,e,w}=setup(),second=F.createTemplate(l,t,clock(1000));a.notEqual(second.id,t.id);a.notEqual(second.steps[0].id,t.steps[0].id);a.equal(t.version,1);
  a.equal(w.template_snapshot.steps[0].id,t.steps[0].id);const before=clone(w.template_snapshot);
  F.updateTemplate(l,t,{title:'Revised',steps:[...t.steps.slice(0,2),{title:'Long UV',description:'Longer run',duration_ms:180000}]},clock(2000));a.equal(t.version,2);a.deepEqual(w.template_snapshot,before);a.equal(w.template_version,1);
  const next=F.startExperiment(l,t,{},clock(3000));a.equal(next.workflow.template_version,2);a.equal(next.workflow.steps[2].duration_ms,180000);a.notEqual(next.workflow.steps[0].id,w.steps[0].id);a.equal(next.experiment.sample,'');a.equal(e.sample,'New lot');
});

test('saving an experiment copies conditions and planned times but excludes observations, photos, samples and timer history',()=>{
  const {l,e,w}=setup();const stopwatch=L.timer(l,{title:'Independent stopwatch',experiment_id:e.id},clock());L.operate(l,stopwatch,'start',clock());L.operate(l,stopwatch,'lap',clock(4000));
  const r=L.record(l,e.id,'Cloudy','Old sample',clock(1000));r.photos.push({id:L.id(),name:'photo',ext:'jpg',mime:'image/jpeg',bytes:4});L.sample(l,e.id,{pulled:clock(1000),quench:{agent:'None',at:clock(1000)}},clock(1000));
  F.operateStep(l,w,w.steps[0],'start',clock(10000));F.operateStep(l,w,w.steps[0],'complete',clock(12000));F.operateStep(l,w,w.steps[1],'start',clock(20000));const oldFlowTimer=w.steps[1].timer_id;
  const saved=F.createTemplate(l,F.fromExperiment(l,e,{title:'Saved run'}),clock(25000));a.deepEqual(saved.planned_minutes,[1,5]);a.equal(saved.timer_presets.length,1);a.equal(saved.timer_presets[0].title,'Independent stopwatch');
  const next=F.startExperiment(l,saved,{},clock(30000)),newTimers=l.timers.filter(t=>t.experiment_id===next.experiment.id&&t.purpose==='timer');a.equal(next.experiment.sample,'');a.deepEqual(next.experiment.run,e.run);a.deepEqual(next.experiment.water,e.water);a.equal(l.samples.filter(v=>v.experiment_id===next.experiment.id).length,0);a.equal(l.records.filter(v=>v.experiment_id===next.experiment.id).length,0);a.equal(newTimers.length,1);a.notEqual(newTimers[0].id,stopwatch.id);a.equal(newTimers[0].status,'idle');a.equal(newTimers[0].elapsed_ms,0);a.equal(next.workflow.steps[1].timer_id,null);a.equal(l.timers.find(t=>t.id===oldFlowTimer).status,'running');a.ok(next.workflow.steps.every(s=>s.status==='pending'&&s.history.length===0));
});

test('step clocks start at the step while sampling stays anchored to the original reaction start',()=>{
  const {l,e,w}=setup();const reaction=clone(e.started),sampleTimer=l.timers.find(t=>t.experiment_id===e.id&&t.purpose==='sample'&&t.duration_ms===300000);
  F.operateStep(l,w,w.steps[0],'skip',clock(30000),'Already prepared');F.operateStep(l,w,w.steps[1],'start',clock(60000));const stepTimer=l.timers.find(t=>t.id===w.steps[1].timer_id);
  a.equal(stepTimer.kind,'countdown');a.equal(stepTimer.purpose,'timer');a.deepEqual(stepTimer.anchor,clock(60000));a.equal(L.remaining(stepTimer,clock(90000)),30000);a.equal(L.remaining(sampleTimer,clock(90000)),210000);a.deepEqual(e.started,reaction);a.equal(F.activeStep(l,e),w.steps[1]);
});

test('zero duration steps create no timer and invalid transitions never leave partial changes',()=>{
  const {l,w}=setup(),timerCount=l.timers.length;F.operateStep(l,w,w.steps[0],'start',clock(1000));a.equal(l.timers.length,timerCount);a.equal(w.steps[0].timer_id,null);
  identicalOnFailure(l,()=>F.operateStep(l,w,w.steps[1],'start',clock(2000)));identicalOnFailure(l,()=>F.operateStep(l,w,w.steps[0],'skip',clock(2000),' '));identicalOnFailure(l,()=>F.operateStep(l,w,w.steps[1],'complete',clock(2000)));identicalOnFailure(l,()=>F.createTemplate(l,def({steps:[{title:'Invalid',duration_ms:-1}]}),clock()));identicalOnFailure(l,()=>F.startExperiment(l,l.experiment_templates[0],{run:{process:'invalid'}},clock()));
  F.operateStep(l,w,w.steps[0],'complete',clock(3000));a.equal(F.activeStep(l,w.experiment_id),null);F.validate(l);
});

test('restarts and wall-clock adjustments preserve active countdowns and wall/mono audit anchors',()=>{
  const {l,e,w}=setup();F.operateStep(l,w,w.steps[0],'skip',clock(1000),'Measured earlier');F.operateStep(l,w,w.steps[1],'start',clock(10000));
  const restarted=clone(l),flow=F.workflow(restarted,e.id),step=flow.steps[1],timer=restarted.timers.find(t=>t.id===step.timer_id);F.ensure(restarted);a.equal(L.elapsed(timer,clock(35000,-3600000)),25000);a.equal(L.elapsed(timer,clock(4000,70000,'boot2')),60000);
  F.operateStep(restarted,flow,step,'complete',clock(40000,-3600000));a.equal(timer.status,'done');a.equal(timer.elapsed_ms,30000);a.deepEqual(step.history.at(-1).at,clock(40000,-3600000));a.equal(step.history.at(-1).status_before,'active');
  const oldTimer=timer.id;F.operateStep(restarted,flow,step,'reopen',clock(50000));a.equal(step.status,'pending');a.equal(step.timer_id,null);a.equal(step.history.length,3);F.operateStep(restarted,flow,step,'start',clock(60000));a.notEqual(step.timer_id,oldTimer);a.equal(restarted.timers.find(t=>t.id===oldTimer).status,'done');a.equal(step.history[1].timer_id,oldTimer);F.validate(restarted);
});

test('finishing an experiment closes pending and active steps while retaining completed history',()=>{
  const {l,e,w}=setup();F.operateStep(l,w,w.steps[0],'start',clock(1000));F.operateStep(l,w,w.steps[0],'complete',clock(2000));const completed=clone(w.steps[0]);F.operateStep(l,w,w.steps[1],'start',clock(3000));const timer=l.timers.find(t=>t.id===w.steps[1].timer_id);F.finishExperiment(l,e,clock(40000));
  a.deepEqual(w.steps[0],completed);a.equal(timer.status,'done');a.equal(timer.elapsed_ms,37000);a.equal(w.steps[1].status,'skipped');a.equal(w.steps[2].status,'skipped');a.ok(w.steps.slice(1).every(s=>s.skip_reason&&s.history.at(-1).action==='cancel'));a.deepEqual(w.ended,e.ended);a.equal(F.activeStep(l,e),null);const history=clone(w);F.cancelWorkflow(l,e,clock(60000));a.deepEqual(w,history);identicalOnFailure(l,()=>F.operateStep(l,w,w.steps[2],'reopen',clock(60000)));
});

test('legacy Lab finish synchronization uses the original experiment end clock and is idempotent',()=>{
  const {l,e,w}=setup();F.operateStep(l,w,w.steps[1],'start',clock(1000));L.finishExperiment(l,e,clock(5000));F.cancelWorkflow(l,e,clock(10000));a.deepEqual(w.ended,clock(5000));a.deepEqual(w.steps[1].ended,clock(5000));a.deepEqual(w.steps[1].history.at(-1).at,clock(5000));const before=JSON.stringify(l);F.cancelWorkflow(l,e,clock(11000));a.equal(JSON.stringify(l),before);
});

test('phrases trim and deduplicate while retaining existing phrase IDs',()=>{
  const l=L.empty();F.setPhrases(l,['  Clear  ','Turbid','Clear'],clock());a.deepEqual(l.observation_phrases.map(p=>p.text),['Clear','Turbid']);const old=l.observation_phrases[0];F.setPhrases(l,['Clear','Pale yellow'],clock(1000));a.equal(l.observation_phrases[0],old);a.deepEqual(old.created,clock());identicalOnFailure(l,()=>F.setPhrases(l,[''],clock()));F.validate(l);
});

test('additive extension merge preserves local IDs and pauses imported active linked timers',()=>{
  const local=L.empty();F.ensure(local);F.setPhrases(local,['Clear'],clock());const {l:incoming,e,w}=setup();F.setPhrases(incoming,['Clear','Turbid'],clock());F.operateStep(incoming,w,w.steps[1],'start',clock(1000));const original=clone(incoming);
  const base=L.merge(local,incoming,clock(11000)),result=F.merge(base.lab,incoming,clock(11000)),imported=F.workflow(result.lab,e.id),timer=result.lab.timers.find(t=>t.id===imported.steps[1].timer_id);
  a.equal(timer.status,'paused');a.equal(timer.elapsed_ms,10000);a.equal(imported.steps[1].status,'active');a.equal(imported.steps[1].history.at(-1).action,'import_pause');a.equal(result.lab.observation_phrases.length,2);a.deepEqual(incoming,original);F.validate(result.lab);L.validate(result.lab);
  const replay=F.merge(L.merge(result.lab,incoming,clock(21000)).lab,incoming,clock(21000));a.equal(replay.added,0);a.deepEqual(F.workflow(replay.lab,e.id),imported);a.equal(replay.lab.timers.find(t=>t.id===timer.id).elapsed_ms,10000);
  const incomingChanged=clone(incoming);incomingChanged.experiment_templates[0].title='Remote changed';const preserve=F.merge(result.lab,incomingChanged,clock(21000));a.equal(preserve.lab.experiment_templates[0].title,'UV/PDS standard');
});

test('merge rejects broken links and orphan workflows without mutating either side',()=>{
  const {l,e,w}=setup();F.operateStep(l,w,w.steps[1],'start',clock(1000));const damaged=clone(l);damaged.workflows[0].steps[1].timer_id='f'.repeat(32);const before=JSON.stringify(l),badBefore=JSON.stringify(damaged);a.throws(()=>F.merge(l,damaged,clock(2000)));a.equal(JSON.stringify(l),before);a.equal(JSON.stringify(damaged),badBefore);
  const empty=L.empty();F.ensure(empty);a.throws(()=>F.merge(empty,l,clock(2000)),'Lab.merge must install base parents before extension merge');a.equal(empty.workflows.length,0);
});

test('standalone staged timer presets copy fresh idle state, separate from procedure timers',()=>{
  const {l,e,w}=setup();const original=L.timer(l,{title:'UV phases',kind:'staged',experiment_id:e.id,stages:[{title:'Mix',duration_ms:1000},{title:'UV',duration_ms:2000}],repeat_count:2,delay_ms:500,transition_mode:'manual'},clock());L.operate(l,original,'start',clock());
  const t=F.createTemplate(l,F.fromExperiment(l,e),clock(1000)),next=F.startExperiment(l,t,{},clock(2000)),copied=l.timers.find(x=>x.experiment_id===next.experiment.id&&x.kind==='staged');a.ok(copied);a.notEqual(copied.id,original.id);a.equal(copied.status,'idle');a.equal(copied.elapsed_ms,0);a.deepEqual(copied.stages,original.stages);a.equal(copied.repeat_count,2);a.equal(copied.delay_ms,500);a.equal(copied.transition_mode,'manual');a.equal(next.workflow.steps.length,w.steps.length);F.validate(l);L.validate(l);
});

test('per-run overrides become the workflow snapshot without modifying its source template',()=>{
  const {l,t}=setup(),original=clone(t),run={...t.run,target:'Run-specific target'},water={...t.water,lot:'Fresh matrix',ph:6.5};const result=F.startExperiment(l,t,{title:'Adjusted run',description:'Adjusted conditions',sample:'Fresh sample',run,water,planned_minutes:[2,7]},clock(90000));
  a.deepEqual(t,original);a.equal(result.workflow.template_id,t.id);a.equal(result.workflow.template_version,t.version);const snap=result.workflow.template_snapshot;a.equal(snap.title,result.experiment.title);a.equal(snap.description,result.experiment.description);a.deepEqual(snap.run,result.experiment.run);a.deepEqual(snap.water,result.experiment.water);a.deepEqual(snap.planned_minutes,[2,7]);a.equal(snap.steps[0].id,t.steps[0].id);a.deepEqual(l.timers.filter(x=>x.experiment_id===result.experiment.id&&x.purpose==='sample').map(x=>x.duration_ms/60000).sort((a,b)=>a-b),[2,7]);F.validate(l);
});

test('record step links accept absent, null and matching experiment workflow steps',()=>{
  const {l,e,w}=setup(),plain=L.record(l,e.id,'General observation','',clock(1000)),linked=L.record(l,e.id,'Step observation','',clock(2000));plain.step_id=null;linked.step_id=w.steps[1].id;L.record(l,null,'Independent observation','',clock(3000));a.equal(F.validateRecordLinks(l),l);
});

test('record step link final-state validation rejects cross-experiment and missing step IDs',()=>{
  const {l,e,w}=setup(),other=F.startExperiment(l,l.experiment_templates[0],{},clock()),r=L.record(l,e.id,'Observation','',clock());r.step_id=other.workflow.steps[0].id;identicalOnFailure(l,()=>F.validateRecordLinks(l));r.step_id='f'.repeat(32);identicalOnFailure(l,()=>F.validateRecordLinks(l));r.step_id=w.steps[0].id;F.validateRecordLinks(l);r.experiment_id=null;identicalOnFailure(l,()=>F.validateRecordLinks(l));
});

test('record links validate after both merge stages while extension validation accepts the midpoint',()=>{
  const {l:incoming,e,w}=setup(),r=L.record(incoming,e.id,'Linked observation','',clock());r.step_id=w.steps[0].id;const local=L.empty();F.ensure(local);const base=L.merge(local,incoming,clock(1000));F.validate(base.lab);a.throws(()=>F.validateRecordLinks(base.lab));const merged=F.merge(base.lab,incoming,clock(1000));F.validateRecordLinks(merged.lab);a.equal(merged.lab.records[0].step_id,merged.lab.workflows[0].steps[0].id);
});
