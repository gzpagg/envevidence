/* Playwright CLI run-code --filename scripts/check_glacier_ui.js
 * Isolated localhost preview only. Synthetic records and browser asset mocks verify
 * layout; they do not claim Android microphone, camera, audio playback or alarm tests.
 */
async page => {
  const protocol=await page.context().newCDPSession(page);
  await protocol.send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-transparency',value:'no-preference'}]});
  await protocol.send('Network.enable');await protocol.send('Network.setCacheDisabled',{cacheDisabled:true});
  // Native appassets is same-origin in the APK. The localhost preview uses a scoped
  // thumbnail mock; CSP is bypassed for this browser test, never in shipped assets.
  await protocol.send('Page.setBypassCSP',{enabled:true});
  await page.route('https://appassets.androidplatform.net/photos/**',route=>route.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j4mQAAAAASUVORK5CYII=','base64')}));
  const assert=(ok,message)=>{if(!ok)throw new Error(message);};
  const read=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('envevidence-preview')));
  const settle=()=>page.waitForTimeout(150);
  const nav=async key=>{await page.locator(`.lab-nav [data-to=${key}]`).click();await settle();};
  const noOverflow=async label=>{const sizes=await page.evaluate(()=>({inner:innerWidth,body:document.body.scrollWidth,html:document.documentElement.scrollWidth}));assert(Math.max(sizes.body,sizes.html)<=sizes.inner+1,`${label} horizontal overflow ${JSON.stringify(sizes)}`);};
  const results=[];
  await page.goto('http://127.0.0.1:8765/');await page.locator('.lab-nav').waitFor();
  for(const language of ['en','zh']){
    await page.setViewportSize({width:390,height:844});
    await page.evaluate(()=>localStorage.removeItem('envevidence-preview'));await page.reload();await page.locator('.lab-nav').waitFor();
    for(const key of ['experiments','timers','records','my']){await nav(key);await noOverflow(`${language} empty ${key}`);}
    const fixture=await page.evaluate(language=>{
      const s=EE.empty();s.workspace.preferences.language=language;s.lab=Lab.empty();Flow.ensure(s.lab);
      const c={wall:Date.now(),mono:performance.now(),boot:String(performance.timeOrigin)};
      const long=language==='zh'?'合成测试 · 连续氧化实验与水体条件比较，记录重复实验的每一次变化。'.repeat(4):'Synthetic reactor A · '+('LongExperimentLabelWithoutSpaces'.repeat(4));
      const e=Lab.experiment(s.lab,long,'Synthetic interface fixture; no real observations.','SYN-A',c),other=Lab.experiment(s.lab,language==='zh'?'合成反应器 B':'Synthetic reactor B','','SYN-B',c);
      const past=Lab.experiment(s.lab,language==='zh'?'已结束的合成反应器':'Completed synthetic reactor','','SYN-C',c);Lab.finishExperiment(s.lab,past,c);
      Flow.attachWorkflow(s.lab,e.id,{title:'Synthetic steps',description:'',run:null,water:null,planned_minutes:[],timer_presets:[],steps:[{title:language==='zh'?'检查反应条件并记录初始现象':'Check conditions and record the initial observation',description:'Synthetic step',duration_ms:0}]},c);
      const timerIds=[];for(let i=0;i<19;i++){const options={title:(language==='zh'?'并行秒表 ':'Parallel stopwatch ')+String(i+1).padStart(2,'0'),kind:'stopwatch',duration_ms:0,experiment_id:e.id,color:'#176BDA'};if(i===18)Object.assign(options,{title:language==='zh'?'手动阶段到期检查':'Manual stage boundary',kind:'staged',stages:[{title:'Mix',duration_ms:6000},{title:'Rest',duration_ms:6000}],repeat_count:2,delay_ms:0,transition_mode:'manual'});const t=Lab.timer(s.lab,options,c);Lab.operate(s.lab,t,'start',c);timerIds.push(t.id);}
      Lab.schedule(s.lab,e,[5],c);timerIds.push(s.lab.timers.find(t=>t.purpose==='sample').id);
      const record=Lab.record(s.lab,e.id,language==='zh'?'自制测试记录：照片、录音与文字排列在同一条记录中。':'Synthetic observation: photo, audio and text in one dated record.','SYN-A',c);
      record.photos=[{id:Lab.id(),name:'Synthetic thumbnail.png',ext:'png',mime:'image/png',bytes:100}];
      record.audios=[{id:Lab.id(),name:'Synthetic audio layout.m4a',ext:'m4a',mime:'audio/mp4',bytes:100,duration_ms:5000,sha256:'0'.repeat(64),recorded_at:Lab.clone(c),elapsed_ms:0}];
      const prior={...c,wall:c.wall-86400000,mono:c.mono};const note=Lab.record(s.lab,other.id,'Synthetic text-only record from previous date.','SYN-B',c);note.at=prior;
      EE.validateState(s);Lab.validate(s.lab);Flow.validate(s.lab);localStorage.setItem('envevidence-preview',JSON.stringify(s));return {timerIds,experimentIds:[e.id,other.id],recordId:record.id};
    },language);
    await page.reload();await page.locator('.experiment-focus').waitFor();
    assert((await read()).lab.timers.filter(t=>t.status==='running').length===20,`${language}: 20 timers must start together`);
    await page.locator('#home-experiment').selectOption(fixture.experimentIds[1]);assert(await page.locator('.experiment-focus h2').innerText()===(language==='zh'?'合成反应器 B':'Synthetic reactor B'),'Current experiment switch did not update');
    await page.locator('#home-experiment').selectOption(fixture.experimentIds[0]);const sampleClock=page.locator('[data-home-next]'),sampleBefore=await sampleClock.innerText();await page.waitForTimeout(1200);assert(await sampleClock.innerText()!==sampleBefore,`${language}: home sample countdown must advance without a rerender`);
    await nav('timers');await page.locator(`[data-flow=focusTimer][data-id="${fixture.timerIds[0]}"]`).click();await settle();const first=page.locator(`[data-timer-clock="${fixture.timerIds[0]}"]`),before=await first.innerText();await page.waitForTimeout(1200);assert(await first.innerText()!==before,`${language}: visible stopwatch must advance`);
    const frames=await page.evaluate(()=>new Promise(resolve=>{const samples=[];let last=performance.now();const tick=now=>{samples.push(now-last);last=now;if(samples.length>=90){samples.sort((a,b)=>a-b);resolve({p95_ms:Number(samples[Math.floor(samples.length*.95)].toFixed(1)),max_ms:Number(samples.at(-1).toFixed(1)),over100:samples.filter(x=>x>100).length});}else requestAnimationFrame(tick);};requestAnimationFrame(tick);}));
    assert(frames.over100<18,`${language}: browser frame updates repeatedly stalled ${JSON.stringify(frames)}`);
    const focusTarget=fixture.timerIds[10];await page.locator(`[data-flow=focusTimer][data-id="${focusTarget}"]`).click();await settle();assert(await page.locator(`.timer-focus [data-timer-clock="${focusTarget}"]`).count()===1,'Focus timer click did not promote selected timer');
    await page.locator(`.timer-focus [data-lab=pauseTimer]`).click();await settle();assert((await read()).lab.timers.find(t=>t.id===focusTarget).status==='paused','Focused timer pause did not save');
    const paused=await page.locator(`.timer-focus [data-timer-clock="${focusTarget}"]`).innerText();await page.waitForTimeout(300);assert(await page.locator(`.timer-focus [data-timer-clock="${focusTarget}"]`).innerText()===paused,'Paused visible clock moved');
    await page.locator(`.timer-focus [data-lab=startTimer]`).click();await settle();assert((await read()).lab.timers.find(t=>t.id===focusTarget).status==='running','Focused timer resume did not save');
    await page.waitForTimeout(3000);assert((await read()).lab.timers.find(t=>t.id===fixture.timerIds[18]).status==='waiting','Manual boundary must update status and wait');
    for(const width of [360,390,768]){
      await page.setViewportSize({width,height:844});
      for(const key of ['experiments','timers','records','my']){await nav(key);await noOverflow(`${language}/${width}/${key}`);}
      await nav('experiments');await page.locator('.experiment-focus [data-lab=openExperiment]').click();await settle();await noOverflow(`${language}/${width}/detail`);
      await page.locator('.quick-bar [data-lab=newRecord]').click();await page.locator('dialog[open]').waitFor();await page.locator('dialog[open] [name=body]').fill('Synthetic keyboard viewport test');await page.setViewportSize({width,height:460});
      await page.locator('dialog[open] [type=submit]').scrollIntoViewIfNeeded();await noOverflow(`${language}/${width}/keyboard-dialog`);assert(await page.locator('dialog[open] [type=submit]').isVisible(),'Dialog save inaccessible in keyboard viewport');await page.locator('dialog[open] [data-action=close]').click();await page.setViewportSize({width,height:844});
      await nav('experiments');await page.locator('[data-flow=templates]').click();await noOverflow(`${language}/${width}/templates`);await page.locator('dialog[open] [data-action=close]').click();
    }
    await page.setViewportSize({width:390,height:844});await nav('records');assert(await page.locator('.record-day').count()===2,'Records should have two date sections');assert(await page.locator('.record-card.has-media .photo-button img').count()===1,'Mixed record lost photo');assert(await page.locator('.record-card.has-media audio[controls]').count()===1,'Mixed record lost audio control');await page.screenshot({path:`output/playwright/glacier-records-${language}.png`,animations:'disabled'});
    for(const preference of [{style:'solid',reduce:false},{style:'glass',reduce:true},{style:'glass',reduce:false}]){
      await nav('my');await page.locator('[data-to=appearance]').click();await page.locator('[name=visual_style]').selectOption(preference.style);await page.locator('[name=reduce_transparency]').setChecked(preference.reduce);await page.locator('#settings-form [type=submit]').click();await settle();await page.reload();await page.locator('.lab-nav').waitFor();
      const saved=(await read()).workspace.preferences;assert(saved.visual_style===preference.style&&saved.reduce_transparency===preference.reduce,'Material preferences lost after reload');
      const actual=await page.locator('.lab-nav').evaluate(el=>({material:document.documentElement.dataset.material,blur:getComputedStyle(el).backdropFilter,background:getComputedStyle(el).backgroundColor}));const solid=preference.style==='solid'||preference.reduce;assert(actual.material===(solid?'solid':'glass'),'Material preference applied incorrectly');assert(solid?actual.blur==='none':actual.blur.includes('16px'),'Material blur does not match selected preference');
    }
    await nav('experiments');await page.screenshot({path:`output/playwright/glacier-home-${language}.png`,animations:'disabled'});await nav('timers');await page.screenshot({path:`output/playwright/glacier-timers-${language}.png`,animations:'disabled'});
    results.push({language,parallelTimers:20,widths:[360,390,768],keyboardHeight:460,materialRestartCases:3,mixedMediaLayout:true,frames});
  }
  await protocol.send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'},{name:'prefers-reduced-transparency',value:'reduce'}]});
  assert(await page.locator('.lab-nav').evaluate(el=>getComputedStyle(el).backdropFilter)==='none','System reduced transparency must use solid navigation');
  const reduced=await page.locator('.lab-nav button').first().evaluate(el=>getComputedStyle(el).transitionDuration);assert(reduced==='0s','Reduced motion did not remove transitions');
  return {status:'passed',scope:'Browser layout and interactions; media thumbnail mocked, native hardware not tested',results,reducedMotion:true,reducedTransparency:true,homeClockUpdates:true};
}