/* Playwright CLI run-code; isolated localhost preview, synthetic UI input only. */
async page => {
  const assert=(value,message)=>{if(!value)throw new Error(message);};
  const read=()=>page.evaluate(()=>JSON.parse(localStorage.getItem('envevidence-preview')));
  const sheet=()=>page.locator('dialog[open]');
  const settle=()=>page.waitForTimeout(250);
  const nav=async(name)=>{await page.locator('.lab-nav').getByRole('button',{name,exact:true}).click();await settle();};
  const save=async()=>{await sheet().locator('[type=submit]').click();await sheet().waitFor({state:'hidden'});await settle();};
  const shot=async(name)=>{await page.locator('#notice').waitFor({state:'hidden',timeout:10000});await page.mouse.move(1,1);await page.screenshot({path:`docs/images/${name}.png`,animations:'disabled'});};
  const results=[];
  for(const language of ['en','zh']){
    const zh=language==='zh';
    await page.setViewportSize({width:390,height:844});
    await page.evaluate(()=>localStorage.removeItem('envevidence-preview'));await page.reload();await page.locator('.lab-nav').waitFor();
    await nav('My space');await page.locator('[data-lab=nav][data-to=appearance]').click();
    await page.locator('#settings-form [name=language]').selectOption(language);await page.locator('#settings-form [type=submit]').click();await settle();
    await nav(zh?'我的':'My space');await page.locator('[data-lab=labDemo]').click();await settle();
    await nav(zh?'实验':'Experiments');await page.locator('[data-lab=openExperiment]').click();await settle();
    let before=(await read()).lab;const source=before.experiments[0],origin=JSON.stringify(source.started),workflow=before.workflows[0];
    await page.locator('.workflow-current [data-flow=complete]').click();await settle();
    await page.locator('.workflow-current [data-flow=start]').click();await settle();
    let lab=(await read()).lab;assert(lab.workflows[0].steps[1].status==='active','Second step should start');
    assert(lab.timers.some(t=>t.id===lab.workflows[0].steps[1].timer_id&&t.status==='running'),'Starting a timed step must create its linked countdown');
    await shot(`envbench-steps-${language}`);
    await page.locator('.quick-bar [data-lab=newRecord]').click();
    await sheet().locator('[name=body]').fill(zh?'自制测试：轻微起泡，未见沉淀。':'Synthetic test: slight foaming, no precipitate.');
    await shot(`envbench-observation-${language}`);await save();
    lab=(await read()).lab;assert(lab.records[0].step_id===workflow.steps[1].id,'Observation must link to the active step');
    await page.locator('.workflow-current [data-flow=skip]').click();await sheet().locator('[name=reason]').fill(zh?'自制测试：改用下一步。':'Synthetic test: proceed with the next step.');await save();
    await page.locator('.workflow-current [data-flow=start]').click();await settle();await page.locator('.workflow-current [data-flow=complete]').click();await settle();
    await page.locator('.workflow-panel>details>summary').click();await page.locator('.workflow-steps [data-flow=reopen]').first().click();await settle();
    lab=(await read()).lab;assert(lab.workflows[0].steps[0].status==='pending'&&lab.workflows[0].steps[0].history.length===3,'Repeat step must preserve all earlier actions');
    assert(JSON.stringify(lab.experiments[0].started)===origin,'Step changes must not move reaction t=0');
    await page.locator('.workflow-panel [data-flow=saveTemplate]').click();await sheet().locator('[name=title]').fill(zh?'自制可复用流程':'Synthetic reusable procedure');await save();
    const saved=(await read()).lab.experiment_templates.at(-1),sourceRecordIds=lab.records.map(r=>r.id);
    await nav(zh?'实验':'Experiments');await page.locator('[data-flow=templates]').click();await shot(`envbench-templates-${language}`);
    await sheet().locator(`[data-flow=useTemplate][data-id="${saved.id}"]`).click();await sheet().locator('[name=title]').fill(zh?'流程重复实验 B':'Procedure repeat B');await save();
    lab=(await read()).lab;const newRun=lab.experiments.find(e=>e.title===(zh?'流程重复实验 B':'Procedure repeat B')),newFlow=lab.workflows.find(w=>w.experiment_id===newRun.id);
    assert(newRun.id!==source.id&&newFlow.steps.every(s=>s.status==='pending'),'Template run must have new IDs and ready steps');
    assert(lab.records.filter(r=>r.experiment_id===newRun.id).length===0&&sourceRecordIds.every(id=>lab.records.some(r=>r.id===id)),'Repeat run must not copy results or erase source records');
    await page.locator('[data-lab=newTimer][data-experiment]').click();await sheet().locator('[name=title]').fill(zh?'自制循环计时':'Synthetic cycle timer');
    await sheet().locator('[name=kind]').selectOption('staged');
    await sheet().locator('[name=stage_title]').nth(0).fill(zh?'混合':'Mix');await sheet().locator('[name=stage_title]').nth(1).fill(zh?'静置':'Rest');
    for(const el of await sheet().locator('[name=stage_minutes]').all())await el.fill('0');for(const el of await sheet().locator('[name=stage_seconds]').all())await el.fill('1');
    await sheet().locator('.timer-plan-options>summary').click();await sheet().locator('[name=repeat_count]').fill('2');await sheet().locator('[name=delay_seconds]').fill('1');await sheet().locator('[name=transition_mode]').selectOption('manual');
    await shot(`envbench-stage-setup-${language}`);await save();
    lab=(await read()).lab;const timer=lab.timers.find(t=>t.title===(zh?'自制循环计时':'Synthetic cycle timer'));
    await page.locator(`[data-lab=startTimer][data-id="${timer.id}"]`).click();await page.waitForTimeout(3300);
    lab=(await read()).lab;const waiting=lab.timers.find(t=>t.id===timer.id);assert(waiting.status==='waiting'&&waiting.completed_steps===0,'Manual deadline must wait without advancing');
    await page.waitForTimeout(1500);assert((await read()).lab.timers.find(t=>t.id===timer.id).completed_steps===0,'Waiting time cannot advance a cycle');
    await page.locator(`[data-lab=confirmTimer][data-id="${timer.id}"]`).click();await settle();assert((await read()).lab.timers.find(t=>t.id===timer.id).completed_steps===1,'Manual confirmation must advance exactly one stage');
    await page.waitForTimeout(1400);await page.locator(`[data-lab=confirmTimer][data-id="${timer.id}"]`).click();await settle();assert((await read()).lab.timers.find(t=>t.id===timer.id).completed_steps===2,'Next confirmation should start the second cycle');
    await nav(zh?'计时':'Timers');await shot(`envbench-stage-timers-${language}`);
    await nav(zh?'记录':'Records');await page.locator('[data-flow=phrases]').click();await sheet().locator('[name=phrases]').fill(zh?'出现气泡\n颜色变浅':'Bubbles appeared\nColour became lighter');await save();
    await page.locator('[data-lab=newRecord]').first().click();await sheet().locator('[data-flow=insertPhrase]').first().click();assert(await sheet().locator('[name=body]').inputValue()===(zh?'出现气泡':'Bubbles appeared'),'Phrase should insert editable original text');await save();
    const stable=await read();await page.reload();await page.locator('.lab-nav').waitFor();const restored=await read();
    assert(restored.lab.workflows.length===stable.lab.workflows.length&&restored.lab.records.length===stable.lab.records.length&&restored.workspace.preferences.language===language,'Restart must preserve procedures, notes and language');
    for(const width of [360,390,768]){await page.setViewportSize({width,height:844});const sizes=await page.evaluate(()=>[innerWidth,document.documentElement.scrollWidth]);assert(sizes[1]<=sizes[0]+1,`${language}/${width}: horizontal overflow`);}
    results.push(`${language}: template copy, timed steps, observation link, skip/repeat history, manual cycles, phrases, restart and widths`);
  }
  return results;
}
