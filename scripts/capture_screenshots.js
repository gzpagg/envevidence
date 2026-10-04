/* Run with playwright-cli run-code --filename scripts/capture_screenshots.js.
 * Open the Android assets or Streamlit UI in an isolated browser session first.
 * Desktop: ENVEVIDENCE_DATA_DIR=data/screenshots-demo streamlit run app.py.
 * The script uses only the bundled synthetic demo. Never point it at a personal
 * browser profile or a data directory containing research records.
 * Images show the running source interface; native camera and alarm behavior
 * is exercised separately on Android.
 */
async page => {
  const shot = async (name) => {
    await page.mouse.move(2, 2);
    await page.waitForTimeout(500);
    await page.screenshot({ path: `docs/images/${name}.png`, animations: 'disabled' });
  };
  const ready = async () => {
    await page.getByRole('img', { name: 'Running...', exact: true }).waitFor({ state: 'hidden', timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(700);
  };
  if (await page.getByRole('heading', { name: 'EnvEvidence' }).count()) {
    await page.setViewportSize({ width: 1440, height: 1080 });
    for (const language of ['en', 'zh']) {
      const zh = language === 'zh';
      const locale = page.getByRole('combobox', { name: 'Language / 语言', exact: true });
      await locale.fill(zh ? '简体中文' : 'English');
      await locale.press('Enter');
      await ready();
      await page.locator('[data-testid=stSidebar]').getByText(zh ? '实验分析' : 'Experiment analysis', { exact: true }).click();
      await ready();
      await page.getByText(zh ? '载入分析演示' : 'Load analysis demo', { exact: true }).click();
      await ready();
      await page.getByRole('tab', { name: zh ? '反应条件' : 'Conditions', exact: true }).click();
      await page.locator('[data-testid="stMain"]').evaluate(el => el.scrollTo(0, 0));
      await shot(`analysis-${language}`);
      await page.getByRole('tab', { name: zh ? '动力学拟合' : 'Fitting', exact: true }).click();
      await page.getByRole('button', { name: zh ? '拟合所选模型' : 'Fit selected models', exact: true }).click();
      await ready();
      await page.getByRole('tab', { name: zh ? '动力学拟合' : 'Fitting', exact: true }).click();
      await page.getByText(zh ? '候选模型' : 'Candidate models', { exact: true }).scrollIntoViewIfNeeded();
      await page.locator('[data-testid="stMain"]').evaluate(el => {
        const label = [...el.querySelectorAll('p')].find(p => /^(Candidate models|候选模型)$/.test(p.textContent));
        if (label) el.scrollTop += label.getBoundingClientRect().top - 100;
      });
      await shot(`fitting-${language}`);
      await page.getByRole('tab', { name: zh ? '图表格式' : 'Charts', exact: true }).click();
      await page.getByText(zh ? '格式' : 'Format', { exact: true }).scrollIntoViewIfNeeded();
      await page.locator('[data-testid="stMain"]').evaluate(el => {
        const label = [...el.querySelectorAll('p')].find(p => /^(Format|格式)$/.test(p.textContent));
        if (label) el.scrollTop += label.getBoundingClientRect().top - 100;
      });
      await shot(`charts-${language}`);
      await page.locator('[data-testid=stSidebar]').getByText(zh ? '文献证据' : 'Literature evidence', { exact: true }).click();
      await ready();
      await page.getByText(zh ? '载入离线演示' : 'Load evidence demo', { exact: true }).click();
      await ready();
      await page.getByRole('tab', { name: zh ? '资料与提取' : 'Documents & extraction', exact: true }).click();
      await page.locator('[data-testid="stMain"]').evaluate(el => el.scrollTo(0, 0));
      await shot(`workspace-${language}`);
      await page.getByRole('tab', { name: zh ? '证据核验' : 'Evidence review', exact: true }).click();
      const field = page.getByRole('combobox', { name: zh ? '选择字段' : 'Select field', exact: true });
      await field.fill(zh ? '污染物去除率' : 'Pollutant removal');
      await field.press('Enter');
      await ready();
      const select = page.getByRole('combobox', { name: zh ? '选择实验条件' : 'Select experimental condition', exact: true });
      await select.scrollIntoViewIfNeeded();
      await page.locator('[data-testid="stMain"]').evaluate(el => {
        const label = [...el.querySelectorAll('p')].find(p => /^(Select experimental condition|选择实验条件)$/.test(p.textContent));
        if (label) el.scrollTop += label.getBoundingClientRect().top - 105;
      });
      await shot(`review-${language}`);
      await page.locator('[data-testid=stSidebar]').getByText(zh ? '外观' : 'Appearance', { exact: true }).click();
      await ready();
      await page.locator('[data-testid="stMain"]').evaluate(el => el.scrollTo(0, 0));
      await shot(`settings-${language}`);
    }
    console.log('Captured twelve desktop screenshots from synthetic analysis and evidence data.');
    return;
  }
  throw new Error('Open the EnvEvidence desktop app before running the desktop capture script. Android screenshots use the companion capture_android_screenshots.js script.');
}
