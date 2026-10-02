const {test}=require('node:test');
const assert=require('node:assert/strict');
const L=require('../app/src/main/assets/lab-domain.js');
const clock=n=>({wall:1700000000000+n,mono:10000+n,boot:'review-test'});
function samples(){const lab=L.empty(),e=L.experiment(lab,'UV/PDS','','',clock(0));
  for(const n of [0,60000,120000])L.sample(lab,e.id,{pulled:clock(n),quench:{agent:'None',at:clock(n)}},clock(n));
  return {lab,items:L.runSamples(lab,e.id)};}

test('invalid and missing LC rows keep their sample position and block the whole paste',()=>{
  const {lab,items}=samples();
  for(const input of ['10000\nBAD\n6400','10000\n\n6400']){
    const before=JSON.stringify(lab),parsed=L.parseAreas(input,items);
    assert.deepEqual(parsed.entries.map(x=>[x.sample.label,x.area]),[['S-001',10000],['S-003',6400]]);
    assert.equal(parsed.errors[0].line,2);
    assert.equal(L.canApplyAreas(parsed,10000),false);
    assert.equal(JSON.stringify(lab),before,'previewing a bad paste never edits data');
  }
  const fixed=L.parseAreas('10000\n8000\n6400',items);
  assert.equal(L.canApplyAreas(fixed,10000),true);
  L.applyAreas(lab,fixed.entries,10000,clock(180000));
  assert.deepEqual(items.map(x=>[x.label,x.c_over_c0]),[['S-001',1],['S-002',0.8],['S-003',0.64]]);
});

test('LC headers are recognised explicitly, unknown labels and mixed formats cannot be skipped',()=>{
  const {items}=samples();
  assert.equal(L.canApplyAreas(L.parseAreas('Sample\tPeak Area\nS-001\t10000\ns-003,6400',items),10000),true);
  assert.equal(L.parseAreas('S-999 BAD\nS-001 10000',items).errors[0].line,1);
  for(const input of ['10000\nS-002 8000\n6400','S-001 10000\n8000','S-001 1\nS-001 2','10000\n0x10','10000\nInfinity','10000\n-1'])
    assert.equal(L.canApplyAreas(L.parseAreas(input,items),10000),false,input);
  const wrapped=L.parseAreas('\n  10000\n8000\n6400\n\n',items);
  assert.equal(wrapped.errors.length,0);
  assert.equal(L.canApplyAreas(wrapped,0),false);
});

test('applying a malformed LC batch is atomic and cannot mix experiments',()=>{
  const {lab,items}=samples(),before=JSON.stringify(lab);
  assert.throws(()=>L.applyAreas(lab,[{sample:items[0],area:10000},{sample:items[1],area:-1}],10000,clock(180000)));
  assert.equal(JSON.stringify(lab),before);
  const other=L.experiment(lab,'Control','','',clock(0));
  const v=L.sample(lab,other.id,{pulled:clock(0),quench:{agent:'None',at:clock(0)}},clock(0)),both=JSON.stringify(lab);
  assert.throws(()=>L.applyAreas(lab,[{sample:items[0],area:10000},{sample:v,area:8000}],10000,clock(180000)));
  assert.equal(JSON.stringify(lab),both);
});

test('curvature diagnostics survive shifted time axes and tiny residuals',()=>{
  for(const offset of [0,1000,1000000]){
    const pts=[0,1,2,3,4,5,6].map(x=>({x:x+offset,y:-0.15*x}));
    assert.equal(L.curvature(pts).shape,'linear');
    const curved=pts.map((p,i)=>({...p,y:-0.15*i+0.006*i*i}));
    assert.equal(L.curvature(curved).shape,'tailing');
  }
  assert.equal(L.curvature(Array.from({length:5},()=>({x:1,y:0}))).reason,'degenerate');
});
