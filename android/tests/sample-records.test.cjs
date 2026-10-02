const {test}=require('node:test');
const a=require('node:assert/strict'),L=require('../app/src/main/assets/lab-domain.js');
const clock=(n=0,boot='boot1')=>({wall:1700000000000+n,mono:10000+n,boot});
function run(){const l=L.empty(),e=L.experiment(l,'UV/PDS','','',clock());return {l,e};}
function pull(l,e,n=60000,data={}){return L.sample(l,e.id,{pulled:clock(n),quench:{agent:'Na₂S₂O₃',at:clock(n+5000)},...data},clock(n+5000));}
function csvRow(l,e){const [head,row]=L.samplesCsv(l,e.id).replace('\ufeff','').split('\r\n').map(s=>s.split(',').map(x=>x.replace(/^"|"$/g,'')));return Object.fromEntries(head.map((k,i)=>[k,row[i]]));}

test('samples record measurement sources and unchanged values can be confirmed measured',()=>{
  const {l,e}=run(),v=pull(l,e,60000,{ph:7.8,ph_source:'carried',temp_c:24,temp_c_source:'measured'});
  a.equal(v.ph_source,'carried');a.equal(v.temp_c_source,'measured');a.equal(v.volume_ml_source,'unmeasured');
  L.editSample(v,{ph:7.8,ph_source:'measured'},clock(80000));a.equal(v.ph_source,'measured');a.equal(v.revisions[0].ph_source,'carried');
  L.editSample(v,{temp_c:25},clock(81000));a.equal(v.temp_c_source,'measured');
  L.editSample(v,{ph:null},clock(82000));a.equal(v.ph_source,'unmeasured');
  a.throws(()=>L.editSample(v,{temp_c_source:'unmeasured'},clock(83000)));L.validate(l);
});

test('old sample values and history upgrade with unknown rather than assumed measured sources',()=>{
  const {l,e}=run(),v=pull(l,e,1000,{ph:7.7});L.editSample(v,{ph:7.8},clock(7000));
  const old=L.clone(l),s=old.samples[0];
  for(const x of [s,...s.revisions])for(const k of ['ph_source','temp_c_source','volume_ml_source','fit_exclusion_reason','pulled_time_source','quench_time_source','time_revision_reason'])delete x[k];
  delete s.recorded_elapsed_ms;delete s.recorded_quench_delay_ms;for(const r of s.revisions){delete r.elapsed_ms;delete r.quench_delay_ms;}
  L.upgrade(old);a.equal(s.ph_source,'unknown');a.equal(s.temp_c_source,'unmeasured');a.equal(s.pulled_time_source,'unknown');a.equal(s.recorded_elapsed_ms,1000);
  a.equal(s.revisions[0].ph,7.7);a.equal(s.revisions[0].ph_source,'unknown');a.equal(s.revisions[0].elapsed_ms,1000);L.validate(old);
  const merged=L.merge(L.empty(),old,clock(10000));a.equal(merged.lab.samples[0].ph_source,'unknown');
});

test('timing corrections need a reason and preserve clicks, original offsets and earlier timing',()=>{
  const {l,e}=run(),v=pull(l,e),original=L.clone(v);
  a.throws(()=>L.correctSampleTimes(l,v,{elapsed_ms:59000},clock(90000)));
  a.throws(()=>L.correctSampleTimes(l,v,{elapsed_ms:59000,time_revision_reason:' '},clock(90000)));
  a.throws(()=>L.editSample(v,{elapsed_ms:59000,time_revision_reason:'Button pressed late'},clock(90000)),'run bounds required');
  L.correctSampleTimes(l,v,{elapsed_ms:59000,quench_delay_ms:4000,time_revision_reason:'Button pressed 1 s after pull; quench completed 4 s later'},clock(90000));
  a.equal(v.elapsed_ms,59000);a.equal(v.quench.delay_ms,4000);a.equal(v.pulled_time_source,'corrected');a.equal(v.quench_time_source,'corrected');
  a.deepEqual(v.pulled,original.pulled);a.deepEqual(v.quench.at,original.quench.at);a.equal(v.recorded_elapsed_ms,60000);a.equal(v.recorded_quench_delay_ms,5000);
  a.equal(v.revisions[0].elapsed_ms,60000);a.equal(v.revisions[0].quench_delay_ms,5000);a.equal(v.revisions[0].pulled_time_source,'click');a.ok(v.revisions[0].reason.includes('Button'));
  L.validate(l);
});

test('quench cannot precede pull and corrected offsets must fit the ended run',()=>{
  const {l,e}=run();a.throws(()=>pull(l,e,1000,{quench:{agent:'MeOH',at:clock(500)}}));
  a.throws(()=>pull(l,e,-1000));const v=pull(l,e,60000);L.finishExperiment(l,e,clock(120000));
  for(const changes of [{elapsed_ms:-1},{quench_delay_ms:-1},{elapsed_ms:120001},{elapsed_ms:119000,quench_delay_ms:2000}])a.throws(()=>L.correctSampleTimes(l,v,{...changes,time_revision_reason:'Timing correction'},clock(130000)));
  a.equal(v.elapsed_ms,60000);a.equal(v.revisions.length,0);
  L.correctSampleTimes(l,v,{elapsed_ms:115000,quench_delay_ms:5000,time_revision_reason:'Corrected from bench notes'},clock(130000));L.validate(l);
});

test('new fit exclusions require a reason and restored samples retain it in history',()=>{
  const {l,e}=run(),v=pull(l,e);a.throws(()=>L.editSample(v,{fit_excluded:true},clock(80000)));
  a.throws(()=>L.editSample(v,{fit_excluded:true,fit_exclusion_reason:'  '},clock(80000)));
  L.editSample(v,{fit_excluded:true,fit_exclusion_reason:'Vial dropped before analysis'},clock(80000));a.equal(v.fit_exclusion_reason,'Vial dropped before analysis');
  a.throws(()=>L.editSample(v,{fit_exclusion_reason:''},clock(81000)));
  L.editSample(v,{fit_excluded:false},clock(82000));a.equal(v.fit_exclusion_reason,'');a.equal(v.revisions.at(-1).fit_exclusion_reason,'Vial dropped before analysis');L.validate(l);
});

test('legacy exclusions stay excluded without inventing reasons',()=>{
  const {l,e}=run(),v=pull(l,e);v.fit_excluded=true;delete v.fit_exclusion_reason;L.upgrade(l);
  a.equal(v.fit_exclusion_reason,'');L.editSample(v,{note:'Retained imported exclusion'},clock(80000));a.equal(v.fit_excluded,true);L.validate(l);
});

test('corrected timing is used by fitting and CSV while original click timing remains exported',()=>{
  const {l,e}=run();L.setRun(l,e,{process:'UV/PDS',target:'A',oxidant:'PDS',fluence_rate_mw_cm2:2},clock());
  for(const [i,t] of [0,1,2].entries()){const v=pull(l,e,(t+1)*60000,{ph:7.8,ph_source:'measured',temp_c:24,temp_c_source:'carried'});L.editSample(v,{c_over_c0:Math.exp(-0.2*t)},clock(300000));L.correctSampleTimes(l,v,{elapsed_ms:t*60000,time_revision_reason:'Aligned to written sample time'},clock(300000));}
  const fit=L.fit(L.runSamples(l,e.id));a.ok(Math.abs(fit.k_per_min-0.2)<1e-10);a.equal(fit.points[0].x,0);
  const row=csvRow(l,e);a.equal(row.pulled_s,'0');a.equal(row.recorded_pulled_s,'60');a.equal(row.recorded_quench_delay_s,'5');a.equal(row.ph_source,'measured');a.equal(row.temp_c_source,'carried');a.equal(row.volume_ml_source,'unmeasured');a.equal(row.pulled_time_source,'corrected');a.equal(row.fluence_mj_cm2,'0');a.equal(row.pulled_at_utc,new Date(clock(60000).wall).toISOString());a.equal(row.quench_at_utc,new Date(clock(65000).wall).toISOString());L.validate(l);
});

test('unplanned t0 sample leaves all scheduled checkpoints waiting',()=>{
  const {l,e}=run();L.schedule(l,e,[1,5],clock());const v=pull(l,e,0);
  a.equal(v.planned_ms,null);a.equal(v.timer_id,null);a.equal(L.nextSample(l,e,clock(5000)).timer.duration_ms,60000);a.equal(l.timers.filter(t=>t.status==='running').length,2);L.validate(l);
});

test('backup validation checks source consistency and revision value types',()=>{
  const {l,e}=run(),v=pull(l,e,60000,{ph:7.8,ph_source:'measured'});L.editSample(v,{ph:7.9},clock(80000));
  const bad=L.clone(l);bad.samples[0].revisions[0].ph='<img src=x>';a.throws(()=>L.validate(bad));
  const badSource=L.clone(l);badSource.samples[0].ph_source='unmeasured';a.throws(()=>L.validate(badSource));
});

test('measurement fields preserve stored precision when opening an edit form',()=>{
  const source=require('node:fs').readFileSync(require('node:path').join(__dirname,'../app/src/main/assets/bench.js'),'utf8');
  const render=require('node:vm').runInNewContext(source.slice(source.indexOf('function stepper('),source.indexOf('function runFields('))+';stepper;',{esc:String,tr:x=>x,sourceBadge:x=>x,bb:()=>''});
  a.ok(render('volume_ml','Volume',0.015,0.1,1,'mL',1,'measured').includes('value="0.015"'));
  a.ok(render('ph','pH',7.813,0.01,2,'',7,'carried').includes('value="7.813"'));
  const {l,e}=run(),v=pull(l,e,60123,{ph:7.813,ph_source:'carried',volume_ml:0.015,volume_ml_source:'measured'});
  L.editSample(v,{ph:7.813,ph_source:'carried',volume_ml:0.015,volume_ml_source:'measured',note:'Changed note only'},clock(80000));
  a.equal(v.ph,7.813);a.equal(v.volume_ml,0.015);a.equal(v.elapsed_ms,60123);a.equal(v.pulled_time_source,'click');a.equal(v.ph_source,'carried');L.validate(l);
});

test('active-run corrections reject future samples and accept offsets within the current run',()=>{
  const {l,e}=run(),v=pull(l,e);
  a.throws(()=>L.correctSampleTimes(l,v,{elapsed_ms:79000,quench_delay_ms:2000,time_revision_reason:'Written times'},clock(80000)));
  a.equal(v.revisions.length,0);L.correctSampleTimes(l,v,{elapsed_ms:75000,quench_delay_ms:2000,time_revision_reason:'Written times'},clock(80000));a.equal(v.elapsed_ms,75000);L.validate(l);
});
