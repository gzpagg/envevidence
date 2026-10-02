/* Use an isolated synthetic Streamlit session with playwright-cli run-code. */
async page => {
  const ready = async () => {
    await page.getByRole('img', { name: 'Running...', exact: true }).waitFor({ state: 'hidden', timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(700);
    if (await page.locator('[data-testid="stException"]').count()) throw new Error('Application exception');
  };
  const choose = async (label, value) => {
    const widget = page.getByRole('combobox', { name: label, exact: true });
    await widget.click();
    await widget.fill(value);
    await page.getByRole('option', { name: value, exact: true }).click();
    await ready();
  };
  await page.setViewportSize({ width: 1440, height: 1080 });
  await page.reload();
  await ready();
  await page.getByText('◈ Experiment analysis', { exact: true }).click();
  await ready();
  await page.getByRole('button', { name: 'Open analysis project', exact: true }).click();
  await ready();
  for (const lang of ['en', 'zh']) {
    const zh = lang === 'zh';
    await choose('Language / 语言', zh ? '简体中文' : 'English');
    for (const palette of [['Forest', '森林绿'], ['Ocean', '海洋蓝'], ['Sand', '暖灰橙'], ['Graphite', '石墨紫']]) {
      await page.getByText(zh ? '⚙ 外观' : '⚙ Appearance', { exact: true }).click();
      await ready();
      await choose(zh ? '配色方案' : 'Palette', palette[zh ? 1 : 0]);
      await page.getByRole('button', { name: zh ? '保存外观' : 'Save appearance', exact: true }).click();
      await ready();
      await page.getByText(zh ? '◈ 实验分析' : '◈ Experiment analysis', { exact: true }).click();
      await ready();
      for (const tab of zh ? ['反应条件', '测量数据', '数据处理', '动力学拟合', '图表格式', 'SOP 导出'] : ['Conditions', 'Measurements', 'Processing', 'Fitting', 'Charts', 'SOP export']) {
        await page.getByRole('tab', { name: tab, exact: true }).click();
        await ready();
      }
    }
    await page.setViewportSize({ width: 390, height: 844 });
    for (const tab of zh ? ['反应条件', '测量数据', '数据处理', '动力学拟合', '图表格式', 'SOP 导出'] : ['Conditions', 'Measurements', 'Processing', 'Fitting', 'Charts', 'SOP export']) {
      await page.getByRole('tab', { name: tab, exact: true }).click();
      await ready();
      const overflow = await page.locator('[data-testid="stMain"]').evaluate(el => el.scrollWidth > el.clientWidth + 2);
      if (overflow) throw new Error(`Page overflow: ${lang} ${tab}`);
    }
    await page.getByRole('tab', { name: zh ? '图表格式' : 'Charts', exact: true }).click();
    await page.locator('[data-testid="stMain"]').evaluate(el => el.scrollTo(0, 0));
    await page.screenshot({ path: `output/playwright/analysis-narrow-${lang}.png` });
    await page.setViewportSize({ width: 1440, height: 1080 });
  }
  await choose('Language / 语言', 'English');
  await page.getByText('⚙ Appearance', { exact: true }).click();
  await ready();
  await choose('Palette', 'Forest');
  await page.getByRole('button', { name: 'Save appearance', exact: true }).click();
  await ready();
  await page.getByText('◈ Experiment analysis', { exact: true }).click();
  await ready();
  console.log('Both languages, four palettes, six analysis tabs and narrow layouts passed.');
}
