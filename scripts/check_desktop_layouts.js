/* Run with playwright-cli run-code --filename scripts/check_desktop_layouts.js.
 * Use only an isolated Streamlit instance with a dedicated synthetic data directory.
 */
async page => {
  const ready = async () => {
    await page.getByRole('img', { name: 'Running...', exact: true }).waitFor({ state: 'hidden', timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(900);
    await page.locator('[data-testid=stStatusWidget]').waitFor({ state: 'hidden', timeout: 60000 });
    await page.waitForTimeout(250);
    if (await page.locator('[data-testid="stException"]').count()) throw new Error('Application exception');
  };
  const choose = async (label, value) => {
    const widget = page.getByRole('combobox', { name: label, exact: true });
    await widget.click();
    await widget.fill(value);
    await page.getByRole('option', { name: value, exact: true }).click();
    await ready();
  };
  const navigation = async (en, zh, isChinese) => {
    await page.locator('[data-testid=stSidebar]').getByText(isChinese ? zh : en, { exact: true }).click();
    await ready();
  };
  const overflow = async context => {
    const value = await page.locator('[data-testid="stMain"]').evaluate(el => ({ width: el.clientWidth, scroll: el.scrollWidth }));
    if (value.scroll > value.width + 2) throw new Error(`Page overflow: ${context} ${JSON.stringify(value)}`);
  };
  const glassStyle = () => page.locator('.st-key-glass_navigation').evaluate(el => {
    const style = getComputedStyle(el);
    return { blur: style.backdropFilter || style.webkitBackdropFilter, background: style.backgroundColor };
  });
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.setCacheDisabled', { cacheDisabled: true });
    await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-transparency', value: 'no-preference' }] });
  await page.setViewportSize({ width: 1440, height: 1080 });
  await page.reload();
  await ready();
  await choose('Language / 语言', 'English');
  await navigation('Experiment analysis', '实验分析', false);
  await page.getByText('Load analysis demo', { exact: true }).click();
  await ready();
  for (const lang of ['en', 'zh']) {
    const zh = lang === 'zh';
    await choose('Language / 语言', zh ? '简体中文' : 'English');
    for (const palette of [['Glacier · blue & cyan', '冰川 · 蓝青'], ['Mineral · teal', '矿物青 · 浅灰'], ['Clay', '陶土色'], ['Forest', '森林绿'], ['Ocean', '海洋蓝'], ['Sand', '暖灰橙'], ['Graphite', '石墨紫']]) {
      await navigation('Appearance', '外观', zh);
      await choose(zh ? '配色方案' : 'Palette', palette[zh ? 1 : 0]);
      await page.getByRole('button', { name: zh ? '保存外观' : 'Save appearance', exact: true }).click();
      await ready();
      await navigation('Experiment analysis', '实验分析', zh);
      for (const tab of zh ? ['反应条件', '测量数据', '数据处理', '动力学拟合', '图表格式', 'SOP 导出'] : ['Conditions', 'Measurements', 'Processing', 'Fitting', 'Charts', 'SOP export']) {
        await page.getByRole('tab', { name: tab, exact: true }).click();
        await ready();
        await overflow(`${lang} ${palette[0]} ${tab}`);
      }
    }
    await navigation('Appearance', '外观', zh);
    await page.getByRole('button', { name: zh ? '恢复默认外观' : 'Restore default appearance', exact: true }).click();
    await ready();
    await page.waitForFunction(expected => [...document.querySelectorAll('input[role=combobox]')].some(el => el.value === expected), zh ? '冰川 · 蓝青' : 'Glacier · blue & cyan');
    const selectedPalette = await page.getByRole('combobox', { name: zh ? '配色方案' : 'Palette', exact: true }).inputValue();
    if (selectedPalette !== (zh ? '冰川 · 蓝青' : 'Glacier · blue & cyan')) throw new Error(`Reset left stale palette: ${selectedPalette}`);
    const glass = await glassStyle();
    if (!glass.blur.includes('blur(16px)')) throw new Error(`Glass not applied: ${JSON.stringify(glass)}`);
    await page.getByRole('radiogroup', { name: zh ? '导航材质' : 'Navigation material', exact: true }).getByText(zh ? '实色' : 'Solid', { exact: true }).click();
    await ready();
    if ((await glassStyle()).blur !== 'none') throw new Error('Solid material still uses blur');
    await page.getByRole('button', { name: zh ? '保存外观' : 'Save appearance', exact: true }).click();
    await ready();
    await page.reload();
    await ready();
    if ((await glassStyle()).blur !== 'none') throw new Error('Solid material did not persist');
    await navigation('Appearance', '外观', zh);
    await page.getByRole('radiogroup', { name: zh ? '导航材质' : 'Navigation material', exact: true }).getByText(zh ? '磨砂玻璃' : 'Frosted glass', { exact: true }).click();
    await page.getByText(zh ? '减少透明效果' : 'Reduce transparency', { exact: true }).click();
    await ready();
    await page.getByRole('button', { name: zh ? '保存外观' : 'Save appearance', exact: true }).click();
    await ready();
    await page.reload();
    await ready();
    if ((await glassStyle()).blur !== 'none') throw new Error('Reduced transparency did not persist');
    await navigation('Appearance', '外观', zh);
    await page.getByRole('button', { name: zh ? '恢复默认外观' : 'Restore default appearance', exact: true }).click();
    await ready();
    if (!(await glassStyle()).blur.includes('blur(16px)')) throw new Error('Default reset did not restore glass');
    if (await page.getByRole('checkbox', { name: zh ? '减少透明效果' : 'Reduce transparency', exact: true }).isChecked()) throw new Error('Reset left stale reduced-transparency control');
    await navigation('Experiment analysis', '实验分析', zh);
    await page.getByRole('button', { name: zh ? '打开分析项目' : 'Open analysis project', exact: true }).click();
    await ready();
    for (const width of [360, 390, 768]) {
      await page.setViewportSize({ width, height: 900 });
      for (const tab of zh ? ['反应条件', '测量数据', '数据处理', '动力学拟合', '图表格式', 'SOP 导出'] : ['Conditions', 'Measurements', 'Processing', 'Fitting', 'Charts', 'SOP export']) {
        await page.getByRole('tab', { name: tab, exact: true }).click();
        await ready();
        await overflow(`${lang} ${width}px ${tab}`);
        const split = /^(Fitting|动力学拟合)$/.test(tab) ? 'split_fitting' : /^(Charts|图表格式)$/.test(tab) ? 'split_charts' : null;
        if (split) {
          const stacked = await page.locator(`.st-key-${split} [data-testid=stHorizontalBlock]`).first().evaluate(el => {
            const columns = [...el.children].filter(child => child.getAttribute('data-testid') === 'stColumn').map(child => child.getBoundingClientRect());
            return columns.length === 2 && Math.abs(columns[0].x - columns[1].x) < 2 && columns[1].top >= columns[0].bottom - 2;
          });
          if (!stacked) throw new Error(`Split did not stack: ${lang} ${width}px ${tab}`);
        }
      }
      await page.getByRole('tab', { name: zh ? '图表格式' : 'Charts', exact: true }).click();
      await ready();
      await page.mouse.move(2, 2);
      await page.locator('[data-testid="stMain"]').evaluate(el => el.scrollTo(0, 0));
      await page.screenshot({ path: `output/playwright/analysis-${width}-${lang}.png` });
    }
    await page.setViewportSize({ width: 1440, height: 1080 });
    await navigation('Literature evidence', '文献证据', zh);
    await page.getByText(zh ? '载入离线演示' : 'Load evidence demo', { exact: true }).click();
    await ready();
    await page.getByRole('tab', { name: zh ? '证据核验' : 'Evidence review', exact: true }).click();
    for (const width of [360, 768]) {
      await page.setViewportSize({ width, height: 1000 });
      await ready();
      await overflow(`${lang} evidence ${width}px`);
      const stacked = await page.locator('.st-key-split_evidence_review [data-testid=stHorizontalBlock]').first().evaluate(el => {
        const cols = [...el.children].filter(child => child.getAttribute('data-testid') === 'stColumn').map(child => child.getBoundingClientRect());
        return cols.length === 2 && Math.abs(cols[0].x - cols[1].x) < 2 && cols[1].top >= cols[0].bottom - 2;
      });
      if (!stacked) throw new Error(`Evidence split did not stack: ${lang} ${width}px`);
    }
    await page.setViewportSize({ width: 1440, height: 1080 });
  }
  await choose('Language / 语言', 'English');
  await navigation('Appearance', '外观', false);
  await page.getByRole('button', { name: 'Restore default appearance', exact: true }).click();
  await ready();
  await navigation('Experiment analysis', '实验分析', false);
  await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-transparency', value: 'reduce' }] });
  await page.waitForTimeout(200);
  const systemReduced = await glassStyle();
  if (systemReduced.blur !== 'none' || systemReduced.background !== 'rgb(255, 255, 255)') throw new Error(`System transparency preference ignored: ${JSON.stringify(systemReduced)}`);
  await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-transparency', value: 'no-preference' }] });
  if (!(await glassStyle()).blur.includes('blur(16px)')) throw new Error('Glass did not return after system preference reset');
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const duration = await page.locator('.st-key-glass_navigation button').first().evaluate(el => getComputedStyle(el).transitionDuration);
  if (duration.split(',').some(value => parseFloat(value) !== 0)) throw new Error(`Reduced motion still animates: ${duration}`);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  return { languages: ['en', 'zh'], palettes: 7, analysisTabs: 6, widths: [1440, 360, 390, 768], materials: ['glass', 'solid', 'reduced-transparency'], persistence: true, reset: true, reducedMotion: true, systemReducedTransparency: true, evidenceStacking: true, result: 'passed' };
}
