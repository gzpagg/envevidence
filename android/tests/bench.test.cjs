const {test}=require('node:test');
const a=require('node:assert/strict'),L=require('../app/src/main/assets/lab-domain.js');
const clock=(n=0,wall=n,boot='boot1')=>({wall:1700000000000+wall,mono:10000+n,boot});
const quench=(n,agent='Na2S2O3 10 mM')=>({agent,at:clock(n)});
function run(){const l=L.empty(),e=L.experiment(l,'UV/PDS run','','',clock());L.setRun(l,e,{process:'UV/PDS',target:'Target A',oxidant:'PDS',oxidant_mm:1,wavelength_nm:254,fluence_rate_mw_cm2:null},clock());return {l,e};}

test('version 1 notebooks upgrade to bench runs and still merge',()=>{
  const v1={version:1,experiments:[{id:'a'.repeat(32),title:'Old',description:'',sample:'',started:clock(),ended:null,archived:false}],timers:[],counters:[],records:[],events:[],demo_loaded:false};
  const s={workspace:{preferences:{palette:'clay',accent:'#A65338',background:'#F7F5F0'}},lab:JSON.parse(JSON.stringify(v1))};
  L.migrate(s);a.equal(s.lab.version,2);a.deepEqual(s.lab.samples,[]);a.equal(s.lab.experiments[0].run,null);a.equal(s.lab.experiments[0].water,null);
  const m=L.merge(L.empty(),v1,clock());a.equal(m.added,1);a.equal(m.lab.experiments[0].water,null);a.equal(v1.version,1,'the imported object is not modified');
});

test('a sample pulled at a checkpoint keeps planned time, real pull time and quench delay',()=>{
  const {l,e}=run();L.schedule(l,e,[5],clock());const t=l.timers[0];
  const v=L.sample(l,e.id,{timer_id:t.id,pulled:clock(302000),quench:quench(308000),ph:7.81,temp_c:24.3,volume_ml:1},clock(330000));
  a.equal(v.label,'S-001');a.equal(v.planned_ms,300000);a.equal(v.elapsed_ms,302000);a.equal(v.quench.delay_ms,6000);a.equal(t.status,'done');
  const ev=l.events.find(x=>x.sample_id===v.id);a.equal(ev.kind,'sample_taken');a.equal(ev.planned_ms,300000);a.equal(ev.elapsed_ms,302000);
  const adhoc=L.sample(l,e.id,{pulled:clock(400000),quench:quench(401000,'None')},clock(401000));a.equal(adhoc.label,'S-002');a.equal(adhoc.planned_ms,null);
  a.throws(()=>L.sample(l,e.id,{timer_id:t.id,pulled:clock(500000),quench:quench(500000)},clock(500000)),'a checkpoint is pulled once');
  L.validate(l);
});

test('a sample cannot be saved without a quench or after the run ends',()=>{
  const {l,e}=run();
  a.throws(()=>L.sample(l,e.id,{pulled:clock(1000)},clock(1000)));
  a.throws(()=>L.sample(l,e.id,{pulled:clock(1000),quench:{agent:' ',at:clock(1000)}},clock(1000)));
  a.throws(()=>L.sample(l,e.id,{pulled:clock(1000),quench:quench(1000),ph:15},clock(1000)));
  L.finishExperiment(l,e,clock(2000));a.throws(()=>L.sample(l,e.id,{pulled:clock(3000),quench:quench(3000)},clock(3000)));
  a.equal(l.samples.length,0);
});

test('sample corrections keep earlier values and never move the pull time',()=>{
  const {l,e}=run(),v=L.sample(l,e.id,{pulled:clock(60000),quench:quench(65000),ph:7.8},clock(65000));
  L.editSample(v,{c_over_c0:0.92,ph:7.79,pulled:clock(1)},clock(90000));
  a.equal(v.c_over_c0,0.92);a.equal(v.ph,7.79);a.equal(v.elapsed_ms,60000);a.equal(v.pulled.wall,clock(60000).wall);
  a.equal(v.revisions.length,1);a.equal(v.revisions[0].ph,7.8);a.equal(v.revisions[0].c_over_c0,null);
  L.editSample(v,{c_over_c0:0.92},clock(95000));a.equal(v.revisions.length,1,'unchanged values add no revision');
  a.throws(()=>L.editSample(v,{c_over_c0:-1},clock(96000)));a.equal(v.c_over_c0,0.92);
});

test('next checkpoint moves from waiting to ready, due and late',()=>{
  const {l,e}=run();a.equal(L.nextSample(l,e,clock()),null);L.schedule(l,e,[5,1],clock());
  a.equal(L.nextSample(l,e,clock(0)).timer.duration_ms,60000);
  a.equal(L.nextSample(l,e,clock(20000)).state,'wait');
  a.equal(L.nextSample(l,e,clock(45000)).state,'ready');
  a.equal(L.nextSample(l,e,clock(75000)).state,'due');
  const late=L.nextSample(l,e,clock(95000));a.equal(late.state,'late');a.equal(late.left_ms,-35000);
  L.sample(l,e.id,{timer_id:late.timer.id,pulled:clock(95000),quench:quench(96000)},clock(96000));
  a.equal(L.nextSample(l,e,clock(96000)).timer.duration_ms,300000);
});

test('pseudo-first-order fit recovers k, half-life and a confidence interval',()=>{
  const {l,e}=run();const k=0.1;
  for(const m of [0,1,2,5,10,20]){const v=L.sample(l,e.id,{pulled:clock(m*60000),quench:quench(m*60000+5000)},clock(m*60000+5000));L.editSample(v,{c_over_c0:Math.exp(-k*m)},clock());}
  const f=L.fit(L.runSamples(l,e.id));a.equal(f.n,6);a.ok(Math.abs(f.k_per_min-k)<1e-9);a.ok(Math.abs(f.half_life_min-Math.LN2/k)<1e-6);a.ok(f.r2>0.999999);a.ok(f.ci95[0]<=f.k_per_min&&f.ci95[1]>=f.k_per_min);
  const noisy=[1,0.9,0.85,0.58,0.4,0.12];L.runSamples(l,e.id).forEach((v,i)=>L.editSample(v,{c_over_c0:noisy[i]},clock()));
  const g=L.fit(L.runSamples(l,e.id));a.ok(g.ci95[1]-g.ci95[0]>0.001);a.ok(g.r2<1);
  L.runSamples(l,e.id).slice(2).forEach(v=>L.editSample(v,{c_over_c0:null},clock()));a.equal(L.fit(L.runSamples(l,e.id)),null,'fewer than three points do not fit');
});

test('water characterisation validates ranges and computes SUVA254',()=>{
  const {l,e}=run();
  a.throws(()=>L.setWater(l,e,{matrix:'seawater-ish'},clock()));
  a.throws(()=>L.setWater(l,e,{matrix:'mbr_effluent',ph:15},clock()));
  a.throws(()=>L.setWater(l,e,{matrix:'mbr_effluent',doc_mg_c_l:-1},clock()));
  L.setWater(l,e,{matrix:'mbr_effluent',lot:'0918',filtered:true,spiked:true,doc_mg_c_l:6.8,uv254_cm1:0.142,ph:7.8},clock());
  a.ok(Math.abs(L.suva(e.water)-2.0882)<1e-3);a.equal(L.waterCount(e.water),3);a.equal(e.water.bromide_ug_l,null);
  a.equal(L.suva({...e.water,doc_mg_c_l:null}),null);L.validate(l);
});

test('samples CSV is tidy, keeps negative numbers and neutralises formulas',()=>{
  const {l,e}=run(),other=L.experiment(l,'Other','','',clock());L.schedule(l,e,[1],clock());
  L.setWater(l,e,{matrix:'secondary_effluent',lot:'L1',doc_mg_c_l:5,uv254_cm1:0.1},clock());
  const v=L.sample(l,e.id,{timer_id:l.timers[0].id,pulled:clock(58000),quench:quench(64000),note:'=HYPERLINK("x")'},clock(64000));L.editSample(v,{c_over_c0:0.91},clock());
  L.sample(l,other.id,{pulled:clock(1000),quench:quench(2000)},clock(2000));
  const lines=L.samplesCsv(l,e.id).replace('﻿','').split('\r\n'),head=lines[0].split(',').map(x=>x.replaceAll('"','')),row=lines[1].split(',');
  a.equal(lines.length,2);const col=k=>row[head.indexOf(k)];
  a.equal(col('delta_s'),'-2');a.equal(col('quench_delay_s'),'6');a.equal(col('suva254_l_mg_m'),'2');a.equal(col('c_over_c0'),'0.91');a.equal(col('process'),'"UV/PDS"');
  a.ok(lines[1].includes(`"'=HYPERLINK(""x"")"`));a.equal(L.samplesCsv(l).split('\r\n').length,3);
});

test('validation rejects samples that point at missing runs or timers',()=>{
  const {l,e}=run(),v=L.sample(l,e.id,{pulled:clock(1000),quench:quench(2000)},clock(2000));
  v.timer_id='f'.repeat(32);a.throws(()=>L.validate(l));v.timer_id=null;v.experiment_id='0'.repeat(32);a.throws(()=>L.validate(l));
});

test('finishing a run closes unpulled checkpoints as skipped, never as samples',()=>{
  const {l,e}=run();L.schedule(l,e,[1,5],clock());const [t1]=l.timers.filter(t=>t.duration_ms===60000);
  L.sample(l,e.id,{timer_id:t1.id,pulled:clock(61000),quench:quench(62000)},clock(62000));L.finishExperiment(l,e,clock(120000));
  a.equal(l.events.filter(x=>x.kind==='sample_taken').length,1);a.equal(l.events.filter(x=>x.kind==='sample_skipped').length,1);a.equal(l.samples.length,1);
});

function series(ms,values,run_={}){const {l,e}=run();if(Object.keys(run_).length)L.setRun(l,e,{process:'UV/PDS',target:'',oxidant:'PDS',...run_},clock());
  for(const [i,m] of ms.entries()){const v=L.sample(l,e.id,{pulled:clock(m*60000),quench:quench(m*60000+1000)},clock(m*60000+1000));if(values[i]!=null)L.editSample(v,{c_over_c0:values[i]},clock());}
  return {l,e,samples:L.runSamples(l,e.id)};}

test('0.5.0 samples without peak areas or fit exclusion are upgraded',()=>{
  const {l,e}=run(),v=L.sample(l,e.id,{pulled:clock(1000),quench:quench(2000)},clock(2000));L.editSample(v,{c_over_c0:0.5},clock(3000));
  const old=JSON.parse(JSON.stringify(l));for(const x of [old.samples[0],...old.samples[0].revisions]){delete x.peak_area;delete x.fit_excluded;}
  a.throws(()=>L.validate(JSON.parse(JSON.stringify(old))));
  const s={workspace:{preferences:{palette:'clay',accent:'#A65338',background:'#F7F5F0'}},lab:old};L.migrate(s);
  a.equal(s.lab.samples[0].peak_area,null);a.equal(s.lab.samples[0].fit_excluded,false);a.equal(s.lab.samples[0].revisions[0].peak_area,null);
  a.equal(L.merge(L.empty(),JSON.parse(JSON.stringify(old)),clock()).lab.samples[0].fit_excluded,false);
});

test('curvature flags a lag phase and tailing but not clean first-order decay',()=>{
  const t=[0,1,2,4,6,8,10];
  a.equal(L.fit(series(t,t.map(m=>Math.exp(-0.15*m))).samples).curvature.shape,'linear');
  a.equal(L.fit(series(t,t.map(m=>Math.exp(-0.15*Math.max(0,m-2.5)))).samples).curvature.shape,'lag');
  a.equal(L.fit(series(t,t.map(m=>0.5*Math.exp(-0.6*m)+0.5*Math.exp(-0.02*m))).samples).curvature.shape,'tailing');
  a.equal(L.fit(series([0,1,2,5],[1,0.9,0.8,0.6]).samples).curvature.shape,null,'four points are not enough');
});

test('excluded points leave the fit, and the exclusion is kept in history',()=>{
  const lagged=[0,1,2,4,6,8,10].map(m=>Math.exp(-0.15*Math.max(0,m-2.5)));const {samples}=series([0,1,2,4,6,8,10],lagged);
  for(const v of samples.slice(0,3))L.editSample(v,{fit_excluded:true,fit_exclusion_reason:'Synthetic early-point exclusion'},clock(1));
  const f=L.fit(samples);a.equal(f.n,4);a.ok(Math.abs(f.k_per_min-0.15)<1e-9);a.equal(samples[0].revisions.at(-1).fit_excluded,false);
});

test('rate constants are normalised to fluence rate and oxidant dose',()=>{
  const {samples}=series([0,2,4,6],[1,Math.exp(-0.6),Math.exp(-1.2),Math.exp(-1.8)]),f=L.fit(samples);
  const n=L.normalised(f,{fluence_rate_mw_cm2:2,oxidant_mm:0.5});a.ok(Math.abs(n.k_per_s-0.005)<1e-12);a.ok(Math.abs(n.k_fluence_cm2_mj-0.0025)<1e-12);a.ok(Math.abs(n.k_per_min_per_mm-0.6)<1e-9);
  a.deepEqual(L.normalised(f,{fluence_rate_mw_cm2:null,oxidant_mm:null}),{k_per_s:f.k_per_min/60});a.deepEqual(L.normalised(null,{}),{});
});

test('pasted peak areas become C/C0 against a reference, by label or in order',()=>{
  const {l,samples}=series([0,1,5],[null,null,null]);
  const byLabel=L.parseAreas('Sample\tArea\nS-002\t9 200\ns-001,10000\nS-003; 6400\n',samples);
  a.equal(byLabel.entries.length,2,'"9 200" is rejected rather than read as 200');a.deepEqual(byLabel.errors.map(e=>e.reason),['format'],'the header row is skipped');
  a.deepEqual(L.parseAreas('S-001 ten\nS-009 5',samples).errors.map(e=>e.reason),['number','label']);
  const clean=L.parseAreas('S-002\t9200\ns-001,10000\nS-003; 6400',samples);a.equal(clean.errors.length,0);
  L.applyAreas(l,clean.entries,10000,clock(5000));a.deepEqual(samples.map(v=>v.c_over_c0),[1,0.92,0.64]);a.deepEqual(samples.map(v=>v.peak_area),[10000,9200,6400]);
  const ordered=L.parseAreas('10000\n8000\n5000\n4000',samples);a.equal(ordered.entries[2].sample.label,'S-003');a.equal(ordered.errors[0].reason,'extra');
  a.equal(L.parseAreas('S-001 1\nS-001 2',samples).errors[0].reason,'duplicate');
  a.throws(()=>L.applyAreas(l,clean.entries,0,clock()));a.throws(()=>L.applyAreas(l,[...clean.entries,clean.entries[0]],10000,clock()));
  a.equal(samples[1].revisions.at(-1).c_over_c0,null);
});

test('samples CSV carries fluence, peak area and fit exclusion',()=>{
  const {l,e,samples}=series([0,2],[1,0.5],{fluence_rate_mw_cm2:1.5});L.editSample(samples[1],{peak_area:5000,fit_excluded:true,fit_exclusion_reason:'Sample handling deviation'},clock());
  const lines=L.samplesCsv(l,e.id).replace('﻿','').split('\r\n'),head=lines[0].split(',').map(x=>x.replaceAll('"','')),row=lines[2].split(','),col=k=>row[head.indexOf(k)];
  a.equal(col('fluence_mj_cm2'),'180');a.equal(col('peak_area'),'5000');a.equal(col('fit_excluded'),'"true"');
});
