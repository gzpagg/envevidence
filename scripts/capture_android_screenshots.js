/* Playwright CLI: run-code --filename scripts/capture_android_screenshots.js
 * Serve android/app/src/main/assets over localhost first. Use an isolated
 * browser session: this script resets only its envevidence-preview storage.
 * All screenshots use synthetic records entered through the running UI.
 */
async page => {
  const browserProtocol=await page.context().newCDPSession(page);
  await browserProtocol.send('Network.enable');
  await browserProtocol.send('Network.setCacheDisabled',{cacheDisabled:true});
  await browserProtocol.send('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-transparency',value:'no-preference'}]});
  const assert = (ok, message) => { if (!ok) throw new Error(message); };
  const read = () => page.evaluate(() => JSON.parse(localStorage.getItem('envevidence-preview')));
  const dialog = () => page.locator('dialog[open]');
  const settle = () => page.waitForTimeout(200);
  const cancel = async zh => {
    await dialog().getByRole('button', { name: zh ? '取消' : 'Cancel', exact: true }).click();
    await dialog().waitFor({ state: 'hidden' });
  };
  const nav = async (en, zhName, zh) => {
    await page.locator('.lab-nav').getByRole('button', { name: zh ? zhName : en, exact: true }).click();
    await settle();
  };
  const shot = async name => {
    await page.locator('#notice').waitFor({ state: 'hidden', timeout: 10000 });
    await page.mouse.move(1, 1);
    await page.waitForTimeout(450);
    await page.screenshot({ path: `docs/images/${name}.png`, animations: 'disabled' });
  };
  const noOverflow = async name => {
    const widths = await page.evaluate(() => ({ viewport: innerWidth, body: document.body.scrollWidth, document: document.documentElement.scrollWidth }));
    assert(widths.body <= widths.viewport + 1 && widths.document <= widths.viewport + 1, `${name} has horizontal page overflow: ${JSON.stringify(widths)}`);
  };
  const checks = [];
  for (const language of ['en', 'zh']) {
    const zh = language === 'zh';
    await page.setViewportSize({ width: 390, height: 844 });
    await page.evaluate(() => localStorage.removeItem('envevidence-preview'));
    await page.reload();
    await page.locator('.lab-nav').waitFor();
    await nav('My space', '我的', false);
    await page.getByRole('button', { name: /Language & appearance/ }).click();
    await page.locator('#settings-form [name=language]').selectOption(language);
    await page.locator('#settings-form').getByRole('button', { name: 'Save', exact: true }).click();
    await settle();
    await nav('My space', '我的', zh);
    await page.getByRole('button', { name: zh ? '载入实验演示' : 'Load lab demo', exact: true }).click();
    await settle();
    assert((await read()).lab.samples.length === 5, `${language}: synthetic demo did not load`);
    await nav('Experiments', '实验', zh);
    await shot(`lab-home-${language}`);
    await page.locator('[data-lab=openExperiment]').first().click();
    await shot(`envbench-run-${language}`);
    await page.locator('.bench-focus [data-bench=takeSample]').first().click();
    assert(await dialog().locator('[name=ph_source]').inputValue() === 'carried', 'Inherited pH must be marked carried');
    await dialog().locator('[data-bench=confirmMeasured][data-for=bench-ph]').click();
    assert(await dialog().locator('[name=ph_source]').inputValue() === 'measured', 'Confirm measured must update provenance');
    await dialog().locator('[name=ph]').fill('7.81');
    await dialog().locator('[data-agent="Na₂S₂O₃"]').click();
    await shot(`envbench-sample-${language}`);
    await cancel(zh);
    await page.locator('.bench-fit').scrollIntoViewIfNeeded();
    await shot(`envbench-samples-${language}`);
    await page.getByRole('button', { name: zh ? '粘贴 LC 峰面积' : 'Paste LC peak areas', exact: true }).click();
    for (const text of ['10000\nbad\n6400', '10000\n\n6400']) {
      await dialog().locator('[name=areas]').fill(text);
      assert(await dialog().locator('[type=submit]').isDisabled(), 'Any invalid or empty interior row must disable Apply');
      const rows = await dialog().locator('[data-bench-preview] tbody tr').allTextContents();
      assert(rows.some(x => x.includes('S-003') && x.includes('6400')), 'The third peak area must remain assigned to S-003');
    }
    await dialog().locator('[name=areas]').fill('S-001\t12480\nS-002\t11482\nS-003\t10483\nS-004\t7987\nS-005\t5117');
    assert(await dialog().locator('[type=submit]').isEnabled(), 'Labelled valid peak areas should enable Apply');
    await shot(`envbench-paste-${language}`);
    await cancel(zh);
    const fitToggle = page.locator('.bench-infit').first();
    await fitToggle.click();
    assert(await dialog().locator('[name=fit_exclusion_reason]').evaluate(el => el.required), 'Excluding a fit point requires a reason');
    await cancel(zh);
    assert(await page.locator('.bench-infit').first().isChecked(), 'Cancelling exclusion must restore the checkbox');
    await page.locator('[data-bench=editSample]').first().click();
    await dialog().locator('[name=ph]').fill('7.813');
    await dialog().locator('[name=volume_ml]').fill('0.015');
    await dialog().locator('[type=submit]').click();
    await dialog().waitFor({ state: 'hidden' });
    await page.locator('[data-bench=editSample]').first().click();
    assert(await dialog().locator('[name=ph]').inputValue() === '7.813', 'Sample editing must preserve pH precision');
    assert(await dialog().locator('[name=volume_ml]').inputValue() === '0.015', 'Sample editing must preserve volume precision');
    await dialog().locator('[name=note]').fill(zh ? '自制界面回归样品' : 'Synthetic interface regression sample');
    await dialog().locator('[type=submit]').click();
    await dialog().waitFor({ state: 'hidden' });
    let sample = (await read()).lab.samples[0];
    assert(sample.ph === 7.813 && sample.volume_ml === 0.015 && sample.ph_source === 'measured' && sample.volume_ml_source === 'measured', 'A note-only revision must preserve precise values and sources');
    await page.locator('[data-bench=editSample]').first().click();
    await dialog().locator('.sample-time-correction summary').click();
    await dialog().locator('[name=elapsed_s]').fill('4');
    await dialog().locator('[type=submit]').click();
    assert(await dialog().isVisible(), 'Timing correction without a reason must remain in the form');
    sample = (await read()).lab.samples[0];
    assert(sample.elapsed_ms === 3000, 'Timing correction without a reason must not save');
    await dialog().locator('[name=time_revision_reason]').fill(zh ? '自制演示：根据取样录像校正' : 'Synthetic demo: corrected from sampling video');
    await dialog().locator('[type=submit]').click();
    await dialog().waitFor({ state: 'hidden' });
    sample = (await read()).lab.samples[0];
    assert(sample.elapsed_ms === 4000 && sample.recorded_elapsed_ms === 3000 && sample.pulled_time_source === 'corrected' && sample.revisions.length >= 3, 'Timing corrections must preserve original clicks and history');
    checks.push(`${language}: import alignment, provenance, fit exclusion cancellation, precise note revision, timing correction history`);
    await nav('Records', '记录', zh);
    await shot(`lab-records-${language}`);
    await nav('My space', '我的', zh);
    await shot(`lab-my-${language}`);
    await page.getByRole('button', { name: zh ? /语言与外观/ : /Language & appearance/ }).click();
    for (const palette of ['glacier', 'mineral', 'clay', 'forest', 'ocean', 'sand', 'graphite']) {
      await page.locator('#settings-form [name=palette]').selectOption(palette);
      await page.locator('#settings-form').getByRole('button', { name: zh ? '保存' : 'Save', exact: true }).click();
      await settle();
      for (const width of [390, 360, 768]) {
        await page.setViewportSize({ width, height: 844 });
        await noOverflow(`${language}/${palette}/${width}/appearance`);
        await nav('Experiments', '实验', zh);
        await noOverflow(`${language}/${palette}/${width}/home`);
        await page.locator('[data-lab=openExperiment]').first().click();
        await noOverflow(`${language}/${palette}/${width}/run`);
        await nav('Records', '记录', zh);
        await noOverflow(`${language}/${palette}/${width}/records`);
        await nav('My space', '我的', zh);
        await page.getByRole('button', { name: zh ? /语言与外观/ : /Language & appearance/ }).click();
      }
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator('#settings-form [name=palette]').selectOption('glacier');
    await page.locator('#settings-form').getByRole('button', { name: zh ? '保存' : 'Save', exact: true }).click();
    await nav('Timers', '计时', zh);
    await page.locator('[data-lab=newTimer]').first().click();
    await dialog().locator('[name=title]').fill(zh ? '搅拌 · 自制演示' : 'Mixing · synthetic demo');
    await dialog().locator('[name=kind]').selectOption('stopwatch');
    await dialog().locator('[type=submit]').click();
    await dialog().waitFor({ state: 'hidden' });
    const card = page.locator('.timer-card').filter({ hasText: zh ? '搅拌 · 自制演示' : 'Mixing · synthetic demo' });
    await card.locator('[data-lab=startTimer]').click();
    await page.evaluate(()=>window.scrollTo(0,0));
    await shot(`lab-timers-${language}`);
    checks.push(`${language}: seven palettes at 390px, 360px and 768px, no horizontal page overflow`);
  }
  return { screenshots: 16, checks };
}
