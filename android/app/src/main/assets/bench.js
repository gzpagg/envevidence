'use strict';
/* EnvBench: reaction runs at the bench. Checkpoints, quench-checked samples, water matrix and a k_obs fit. */
Object.assign(strings,{
  sampleTaken:['Take sample','取样'],sample_taken:['Sample taken','实际取样'],sample_skipped:['Checkpoint closed without a sample','取样点关闭，未取样'],run_edit:['Run details edited','修改反应条件'],water_edit:['Water details edited','修改水质信息'],
  newRun:['New reaction run','新建反应'],samples:['Samples','样品'],water:['Water matrix','水体基质']
});
const bb=(action,label,data='',cls='')=>`<button type="button" data-bench="${action}" ${data} class="${cls}">${label}</button>`;
const PROCESS_NAMES={'UV/H2O2':'UV/H₂O₂','O3':'O₃','O3/H2O2':'O₃/H₂O₂','Fenton':['Fenton','芬顿'],'Photo-Fenton':['Photo-Fenton','光芬顿'],'PMS/catalyst':['PMS/catalyst','PMS/催化剂'],'Electrochemical':['Electrochemical oxidation','电化学氧化'],'Photocatalysis':['Photocatalysis','光催化'],'Other':['Other','其他']};
function procName(p){const n=PROCESS_NAMES[p];return Array.isArray(n)?tr(n[0],n[1]):n||p;}
const MATRIX_NAMES={ultrapure:['Ultrapure water','超纯水'],buffer:['Buffered water','缓冲溶液'],nom_isolate:['NOM isolate (e.g. SRNOM)','NOM 标准品（如 SRNOM）'],surface_water:['Surface water','地表水'],secondary_effluent:['Secondary effluent','二级出水'],mbr_effluent:['MBR effluent','MBR 出水'],tertiary_effluent:['Tertiary effluent','深度处理出水'],industrial:['Industrial wastewater','工业废水'],other:['Other','其他']};
const matrixName=m=>tr(...(MATRIX_NAMES[m]||[m,m]));
const WATER_FIELDS={doc_mg_c_l:['DOC','DOC','mg C/L'],uv254_cm1:['UV₂₅₄','UV₂₅₄','cm⁻¹'],alkalinity_mg_caco3_l:['Alkalinity','碱度','mg/L CaCO₃'],chloride_mg_l:['Cl⁻','Cl⁻','mg/L'],nitrate_n_mg_l:['NO₃⁻-N','NO₃⁻-N','mg/L'],bromide_ug_l:['Br⁻','Br⁻','µg/L'],conductivity_ms_cm:['Conductivity','电导率','mS/cm'],ph:['pH','pH','']};
const QUENCHES=[['Na₂S₂O₃','Na₂S₂O₃'],['MeOH','MeOH'],['EtOH','EtOH'],['Catalase','过氧化氢酶'],['Ascorbic acid','抗坏血酸'],['None','不淬灭']];
const sheets=new WeakMap();

// Offsets under a minute read as seconds; longer ones as m:ss. Exports keep plain seconds.
function signedSeconds(ms){const s=Math.round(ms/1000),a=Math.abs(s);return `${s>=0?'+':'−'}${a<60?a+' s':Math.floor(a/60)+':'+String(a%60).padStart(2,'0')}`;}
function leftText(ms){return ms>0?L.time(ms):'+'+L.time(-ms);}
function minutesLabel(ms){const m=ms/60000;return `${Number.isInteger(m)?m:m.toFixed(2).replace(/0+$/,'')} min`;}
function parseNum(v){const s=String(v??'').trim().replace(',','.');if(!s)return null;const n=Number(s);L.assert(Number.isFinite(n));return n;}
function fmt(v,d){return v==null?'—':Number(v).toFixed(d);}
function nextLabel(e){return 'S-'+String(state.lab.samples.filter(v=>v.experiment_id===e.id).length+1).padStart(3,'0');}
function benchRun(id){return state.lab.experiments.find(e=>e.id===id);}

/* ---- Experiment page panel ---- */
/* The countdown sits right under the run title; samples and water follow the experiment actions. */
const hasBench=e=>!!e.run||state.lab.samples.some(v=>v.experiment_id===e.id);
function benchTop(e){return hasBench(e)?`${e.run?benchRunHead(e):''}${benchFocus(e)}${benchCheckpoints(e)}`:'';}
function benchBottom(e){return hasBench(e)?`${benchSamples(e,L.runSamples(state.lab,e.id))}${benchWater(e)}`:'';}
function benchRunHead(e){const r=e.run;const bits=[procName(r.process),r.target,r.oxidant&&r.oxidant_mm!=null?`${r.oxidant} ${r.oxidant_mm} mM`:r.oxidant,r.wavelength_nm!=null?`${r.wavelength_nm} nm`:'',r.fluence_rate_mw_cm2!=null?`${r.fluence_rate_mw_cm2} mW/cm²`:''].filter(Boolean);
  return `<div class="bench-runhead"><span class="bench-proc">${esc(bits.join(' · '))}</span>${bb('editRun',tr('Edit run','修改反应条件'),`data-id="${e.id}"`,'small')}</div>`;}
function benchFocus(e){if(e.ended||e.archived)return '';const n=L.nextSample(state.lab,e,labClock());
  if(!n)return `<section class="bench-focus none" data-bench-focus="${e.id}" data-state="none"><div class="bf-top"><b>${tr('No checkpoint waiting','没有待取样的时间点')}</b><span>${esc(nextLabel(e))}</span></div><p class="bf-hint">${tr('Add a sampling plan, or take a sample now, for example at t = 0.','添加取样时间表，或现在取样（例如 t = 0）。')}</p><div class="row">${bb('takeSample',tr('Take sample now','现在取样'),`data-experiment="${e.id}"`,'primary')}${lb('samplePlan',t('samplePlan'),`data-id="${e.id}"`)}</div></section>`;
  const title={wait:tr('Next sample','下一次取样'),ready:tr('Get ready','准备取样'),due:tr('Pull sample now','现在取样'),late:tr('Sample is late','取样已延迟')}[n.state];
  const hint={wait:tr('Countdown to the checkpoint.','距离取样时间点。'),ready:tr('Prepare the vial and the quench.','准备样品瓶和淬灭剂。'),due:tr('Pull, then quench right away.','取样后立即淬灭。'),late:tr('Take it anyway. The real time is recorded.','仍可取样，系统会记录实际时间。')}[n.state];
  return `<section class="bench-focus ${n.state}" data-bench-focus="${e.id}" data-state="${n.state}:${n.timer.id}"><div class="bf-top"><b>${title}</b><span>${esc(nextLabel(e))} · ${minutesLabel(n.timer.duration_ms)}</span></div><div class="bf-time" data-bench-left="${e.id}">${leftText(n.left_ms)}</div><p class="bf-hint">${hint}</p>${bb('takeSample',`${t('sampleTaken')} · ${esc(nextLabel(e))}`,`data-experiment="${e.id}" data-timer="${n.timer.id}"`,'primary big')}</section>`;}
function benchCheckpoints(e){const ts=state.lab.timers.filter(t=>t.experiment_id===e.id&&t.purpose==='sample'&&!t.archived).sort((a,b)=>a.duration_ms-b.duration_ms);if(!ts.length)return '';
  const next=L.nextSample(state.lab,e,labClock())?.timer.id;
  return `<div class="bench-rail" aria-label="${tr('Sampling checkpoints','取样时间点')}">${ts.map(t=>{const v=state.lab.samples.find(x=>x.timer_id===t.id);return `<span class="cp ${v?'done':t.id===next?'next':''}"><b>${minutesLabel(t.duration_ms)}</b>${v?`<small>${esc(v.label)} · Δ ${signedSeconds(v.elapsed_ms-t.duration_ms)}</small>`:t.id===next?`<small>${tr('next','下一个')}</small>`:t.status==='done'?`<small>${tr('no sample','未取样')}</small>`:''}</span>`;}).join('')}</div>`;}
function benchSamples(e,samples){return `<div class="sectionline"><h2>${t('samples')}</h2><span class="muted">${samples.length} ${tr('pulled','个已取样')}</span></div>
  <section class="bench-card bench-fit" data-bench-fit="${e.id}">${fitInner(e)}</section>
  ${samples.length?`<div class="bench-table-wrap"><table class="bench-table"><thead><tr><th>${tr('Sample','样品')}</th><th>t (min)</th><th>Δ</th><th>pH</th><th>°C</th><th>${tr('Quench','淬灭')}</th><th>C/C₀</th><th><span class="sr">${t('edit')}</span></th></tr></thead><tbody>${samples.map(v=>`<tr><td><b>${esc(v.label)}</b></td><td>${(v.elapsed_ms/60000).toFixed(2)}</td><td>${v.planned_ms==null?'—':`<span class="dl ${Math.abs(v.elapsed_ms-v.planned_ms)<=10000?'ok':'warn'}">${signedSeconds(v.elapsed_ms-v.planned_ms)}</span>`}</td><td>${fmt(v.ph,2)}</td><td>${fmt(v.temp_c,1)}</td><td>${esc(v.quench.agent)} <small>+${Math.round(v.quench.delay_ms/1000)} s</small></td><td><input class="bench-cc" data-sample="${v.id}" data-experiment="${e.id}" inputmode="decimal" value="${v.c_over_c0??''}" aria-label="C/C₀ · ${esc(v.label)}" placeholder="—"></td><td>${bb('editSample','✎',`data-id="${v.id}" aria-label="${t('edit')} ${esc(v.label)}"`,'small flat')}</td></tr>`).join('')}</tbody></table></div>
  <p class="muted">${tr('Enter C/C₀ after the LC run. Changes keep the earlier value in the sample history.','LC 测定后填写 C/C₀。修改会在样品历史中保留原值。')}</p>`:''}
  <div class="row">${bb('exportSamples',tr('Samples CSV','样品 CSV'),`data-id="${e.id}"`)}</div>`;}
function fitInner(e){const samples=L.runSamples(state.lab,e.id),f=L.fit(samples);
  const stats=f?`<div class="fit-stats"><div><span>k<sub>obs</sub></span><b>${f.k_per_min.toPrecision(3)}</b><small>min⁻¹ · 95% ${f.ci95[0].toPrecision(2)}–${f.ci95[1].toPrecision(2)}</small></div><div><span>t½</span><b>${f.half_life_min==null?'—':f.half_life_min.toPrecision(3)}</b><small>min</small></div><div><span>R²</span><b>${f.r2==null?'—':f.r2.toFixed(3)}</b><small>OLS</small></div><div><span>n</span><b>${f.n}</b><small>${tr('points','个点')}</small></div></div>${f.k_per_min<=0?`<p class="warning compact">${tr('These points do not show a decay. Check C/C₀ values.','这些点没有呈现衰减，请检查 C/C₀。')}</p>`:''}`:`<p class="muted">${tr('Enter C/C₀ for at least three samples to fit k_obs.','至少为 3 个样品填写 C/C₀ 后拟合 k_obs。')}</p>`;
  return `<div class="row between"><h3>${tr('Pseudo-first-order fit','准一级动力学拟合')}</h3><span class="computed">${tr('computed','计算值')}</span></div>${fitSvg(f)}${stats}<p class="muted">${tr('Least squares of ln(C/C₀) against the real pull time. Check for lag or tailing before reporting k_obs.','以实际取样时间对 ln(C/C₀) 做最小二乘拟合。报告 k_obs 前请检查滞后或拖尾。')}</p>`;}
function fitSvg(f){const pts=f?f.points:[],W=320,H=190,Lm=54,R=12,T=12,B=34;
  const xmax=Math.max(10,Math.ceil(Math.max(0,...pts.map(p=>p.x))/10)*10),ymin=Math.min(-1,Math.floor(Math.min(0,...pts.map(p=>p.y)))),ymax=0.2;
  const sx=x=>Lm+x/xmax*(W-Lm-R),sy=y=>T+(ymax-y)/(ymax-ymin)*(H-T-B);let g='';
  const ystep=-ymin<=2?0.5:Math.max(1,Math.ceil(-ymin/5));for(let y=0;y>=ymin;y-=ystep)g+=`<line class="gl" x1="${Lm}" x2="${W-R}" y1="${sy(y)}" y2="${sy(y)}"/><text class="ax" x="${Lm-6}" y="${sy(y)+3.5}" text-anchor="end">${y===0?'0':'−'+Math.abs(y)}</text>`;
  const xstep=xmax<=30?10:Math.ceil(xmax/40)*10;for(let x=0;x<=xmax;x+=xstep)g+=`<text class="ax" x="${sx(x)}" y="${H-B+15}" text-anchor="middle">${x}</text>`;
  g+=`<text class="ax" x="${(Lm+W-R)/2}" y="${H-3}" text-anchor="middle">t (min)</text><text class="ax" transform="translate(11 ${(T+H-B)/2}) rotate(-90)" text-anchor="middle">ln(C/C₀)</text>`;
  if(f){const x0=Math.min(...pts.map(p=>p.x)),x1=Math.max(...pts.map(p=>p.x));g+=`<line class="fl" x1="${sx(x0)}" y1="${sy(f.intercept-f.k_per_min*x0)}" x2="${sx(x1)}" y2="${sy(f.intercept-f.k_per_min*x1)}"/>`;
    pts.forEach((p,i)=>{g+=`<circle class="pt${i===pts.length-1?' last':''}" cx="${sx(p.x)}" cy="${sy(p.y)}" r="${i===pts.length-1?5:3.8}"/>`;});}
  return `<svg class="fit-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${tr('ln(C/C₀) against time with the fitted line','ln(C/C₀) 随时间变化及拟合直线')}">${g}</svg>`;}
function benchWater(e){const w=e.water;const head=`<div class="sectionline"><h2>${t('water')}</h2>${e.archived?'':bb('editWater',w?t('edit'):tr('Add water details','填写水质'),`data-id="${e.id}"`,'small')}</div>`;
  if(!w)return head+`<section class="bench-card"><p class="muted">${tr('Record the matrix this run used: DOC, UV₂₅₄, alkalinity and ions. Matrix effects are hard to compare without them.','记录本次反应的水体：DOC、UV₂₅₄、碱度和离子。缺少这些数据，基质效应难以比较。')}</p></section>`;
  const count=L.waterCount(w),sv=L.suva(w);
  return head+`<section class="bench-card"><div class="row between"><b>${esc(matrixName(w.matrix))}${w.lot?` · ${tr('lot','批次')} ${esc(w.lot)}`:''}</b><span class="muted">${count}/8 ${tr('recorded','已记录')}</span></div><div class="meter" aria-hidden="true">${L.WATER_NUMBERS.map((k,i)=>`<i class="${i<count?'on':''}"></i>`).join('')}</div>
    <dl class="water-grid">${L.WATER_NUMBERS.map(k=>{const f=WATER_FIELDS[k];return `<div><dt>${tr(f[0],f[1])}</dt><dd>${w[k]==null?`<span class="muted">${tr('not measured','未测')}</span>`:`${w[k]} <small>${f[2]}</small>`}</dd></div>`;}).join('')}</dl>
    <p class="muted">${[w.filtered===true?tr('Filtered, 0.45 µm','已过 0.45 µm 滤膜'):w.filtered===false?tr('Not filtered','未过滤'):'',w.spiked===true?tr('Target spiked','目标物为加标'):w.spiked===false?tr('Target native, not spiked','目标物为原有，未加标'):''].filter(Boolean).join(' · ')}</p>
    <div class="suva"><div class="row between"><b>SUVA₂₅₄</b><span class="computed">${tr('computed','计算值')}</span></div><div class="suva-v">${sv==null?'—':sv.toFixed(2)} <small>L mg⁻¹ m⁻¹</small></div><p class="muted">${suvaText(sv)}</p></div></section>`;}
function suvaText(sv){if(sv==null)return tr('Enter DOC and UV₂₅₄ to compute it.','填写 DOC 与 UV₂₅₄ 后计算。');const f=tr('= UV₂₅₄ ÷ DOC × 100.','= UV₂₅₄ ÷ DOC × 100。');
  return (sv<2?tr('Below 2: mostly non-aromatic, hydrophilic DOM. ','低于 2：以非芳香、亲水性 DOM 为主。'):sv<=4?tr('2 to 4: a mix of hydrophobic and hydrophilic DOM. ','2–4：疏水与亲水 DOM 混合。'):tr('Above 4: mostly aromatic, hydrophobic DOM. ','高于 4：以芳香、疏水性 DOM 为主。'))+f;}

/* ---- Dialogs ---- */
function benchDialog(title,body,onSave,{ok=t('save'),locked=false}={}){const d=document.createElement('dialog');d.className='bench-dialog';
  d.innerHTML=`<form class="stack"><h2>${esc(title)}</h2>${body}<div class="row actions"><button type="submit" class="primary" ${locked?'disabled':''}>${esc(ok)}</button>${button('close',t('cancel'))}</div></form>`;
  document.body.append(d);d.addEventListener('close',()=>d.remove());
  d.querySelector('form').onsubmit=async ev=>{ev.preventDefault();const submit=d.querySelector('[type=submit]');submit.disabled=true;try{const msg=await onSave(new FormData(ev.target),ev.target,d);d.close();render();notice(msg||t('saved'));}catch(err){notice(errorText(err),true);submit.disabled=!!d.dataset.locked;}};
  if(locked)d.dataset.locked='1';d.showModal();return d;}
function numField(name,label,value,unit,extra=''){return `<label>${esc(label)}${unit?` <small>${unit}</small>`:''}<input name="${name}" inputmode="decimal" autocomplete="off" value="${value??''}" ${extra}></label>`;}
function stepper(name,label,value,step,dec,unit,base){return `<div class="stepper-row"><label for="bench-${name}">${esc(label)}${unit?` <small>${unit}</small>`:''}</label><div class="stepper"><button type="button" data-bench="step" data-for="bench-${name}" data-step="${-step}" data-dec="${dec}" data-base="${base}" aria-label="${tr('Decrease','减少')} ${esc(label)}">−</button><input id="bench-${name}" name="${name}" inputmode="decimal" autocomplete="off" value="${value==null?'':Number(value).toFixed(dec)}" placeholder="—"><button type="button" data-bench="step" data-for="bench-${name}" data-step="${step}" data-dec="${dec}" data-base="${base}" aria-label="${tr('Increase','增加')} ${esc(label)}">+</button></div></div>`;}
function runFields(r={},title=''){return input('title',tr('Run name','反应名称'),title,'text',`required maxlength="300" placeholder="${tr('e.g. UV/PDS · target · MBR lot 0918','例如：UV/PDS · 目标物 · MBR 批次 0918')}"`)
  +`<label>${tr('Process','工艺')}<select name="process">${L.PROCESSES.map(p=>`<option value="${esc(p)}" ${p===(r.process||'UV/PDS')?'selected':''}>${esc(procName(p))}</option>`).join('')}</select></label>`
  +input('target',tr('Target compound','目标物'),r.target||'','text','maxlength="300"')
  +`<div class="formgrid">${input('oxidant',tr('Oxidant','氧化剂'),r.oxidant??'PDS','text','maxlength="100"')}${numField('oxidant_mm',tr('Oxidant dose','氧化剂剂量'),r.oxidant_mm,'mM')}${numField('wavelength_nm',tr('Wavelength','波长'),r.wavelength_nm,'nm')}${numField('fluence_rate_mw_cm2',tr('Fluence rate','辐照强度'),r.fluence_rate_mw_cm2,'mW/cm²')}</div>`;}
function runData(f){return {process:f.get('process'),target:f.get('target'),oxidant:f.get('oxidant'),oxidant_mm:parseNum(f.get('oxidant_mm')),wavelength_nm:parseNum(f.get('wavelength_nm')),fluence_rate_mw_cm2:parseNum(f.get('fluence_rate_mw_cm2'))};}
function runForm(id){const e=id&&benchRun(id);
  const body=runFields(e?.run||{},e?.title||'')+(e?'':input('minutes',`${t('samplePlan')} · ${t('sampleTimes')}`,'1, 2, 5, 10, 20, 30','text','maxlength="2000"')+`<p class="info">${tr('Saving starts the run clock at t = 0. Create the run when the lamp goes on or the oxidant goes in. Water details can be added at any time.','保存即开始反应计时（t = 0）。请在开灯或加入氧化剂时创建。水质信息可随时补充。')}</p>`);
  benchDialog(e?tr('Edit run','修改反应条件'):t('newRun'),body,async f=>{const run=runData(f),minutes=e?[]:String(f.get('minutes')||'').split(/[,，;；\s]+/).filter(Boolean).map(Number);await refreshClock();
    await commit(s=>{const c=labClock();if(e){const x=s.lab.experiments.find(x=>x.id===e.id);x.title=f.get('title').trim();L.setRun(s.lab,x,run,c);}else{const x=L.experiment(s.lab,f.get('title'),'','',c);L.setRun(s.lab,x,run,c);if(minutes.length)L.schedule(s.lab,x,minutes,c);experimentId=x.id;page='experiment';}});},{ok:e?t('save'):tr('Start run','开始反应')});}
async function sampleSheet(experiment_id,timer_id){await refreshClock();const e=benchRun(experiment_id),pulled=labClock(),timer=timer_id&&state.lab.timers.find(t=>t.id===timer_id);L.assert(e&&!e.ended&&!e.archived);
  const elapsed=L.experimentElapsed(e,pulled),last=L.runSamples(state.lab,e.id).at(-1),label=nextLabel(e);
  const timing=`<p class="bench-pull"><span>${tr('Pulled at','取样时刻')} <b>t = ${L.time(elapsed)}</b></span>${timer?`<span class="dl ${Math.abs(elapsed-timer.duration_ms)<=10000?'ok':'warn'}">Δ ${signedSeconds(elapsed-timer.duration_ms)} ${tr('vs plan','相对计划')}</span>`:`<span class="muted">${tr('Unplanned sample','计划外取样')}</span>`}</p>`;
  const body=timing+`<fieldset class="bench-quench"><legend>${tr('Quench','淬灭')} <em data-bench-qinfo>${tr('tap the agent you used','点选所用淬灭剂')}</em></legend><div class="chips">${QUENCHES.map(([en,zh])=>`<button type="button" class="chip" data-bench="quench" data-agent="${esc(en)}" aria-pressed="false">${esc(tr(en,zh))}</button>`).join('')}</div><input name="quench_other" maxlength="100" autocomplete="off" placeholder="${tr('Other agent and dose','其他淬灭剂及用量')}" aria-label="${tr('Other agent and dose','其他淬灭剂及用量')}"></fieldset>`
    +stepper('ph','pH',last?.ph??e.water?.ph??null,0.01,2,'',7)+stepper('temp_c',tr('Temperature','温度'),last?.temp_c??null,0.1,1,'°C',25)+stepper('volume_ml',tr('Volume','体积'),last?.volume_ml??null,0.1,1,'mL',1)
    +input('note',tr('Note','备注'),'','text',`maxlength="2000" placeholder="${tr('e.g. slight foaming, lamp flicker','例如：轻微起泡、灯管闪烁')}"`)
    +`<p class="muted" data-bench-savehint>${tr('Choose a quench to save. The moment you tap it is kept as the quench time.','选择淬灭剂后才能保存。点选的时刻即记录为淬灭时间。')}</p>`;
  const d=benchDialog(`${label} · ${timer?minutesLabel(timer.duration_ms):tr('now','现在')}`,body,async f=>{const sh=sheets.get(d);L.assert(!!sh.agent&&!!sh.at);
    const data={timer_id:timer?timer.id:null,pulled,quench:{agent:sh.agent,at:sh.at},ph:parseNum(f.get('ph')),temp_c:parseNum(f.get('temp_c')),volume_ml:parseNum(f.get('volume_ml')),note:f.get('note')};let v;
    await commit(s=>{v=L.sample(s.lab,e.id,data,labClock());});return `${v.label} ${tr('saved','已保存')} · ${tr('quench','淬灭')} +${Math.round(v.quench.delay_ms/1000)} s`;},{ok:tr('Save sample','保存样品'),locked:true});
  sheets.set(d,{agent:null,at:null});
  d.querySelector('[name=quench_other]').addEventListener('input',ev=>{const v=ev.target.value.trim();if(v){d.querySelectorAll('.chip').forEach(c=>c.setAttribute('aria-pressed','false'));chooseQuench(d,v);}});}
function chooseQuench(d,agent){const sh=sheets.get(d);if(!sh.at)sh.at=labClock();sh.agent=agent;delete d.dataset.locked;d.querySelector('[type=submit]').disabled=false;
  d.querySelector('[data-bench-qinfo]').textContent=tr('quench time recorded','已记录淬灭时间');d.querySelector('[data-bench-savehint]').textContent=tr('Ready to save.','可以保存。');}
function sampleForm(id){const v=state.lab.samples.find(x=>x.id===id);if(!v)return;
  const body=`<p class="bench-pull"><span>t = <b>${L.time(v.elapsed_ms)}</b></span><span class="muted">${esc(v.quench.agent)} +${Math.round(v.quench.delay_ms/1000)} s</span></p>`
    +numField('c_over_c0','C/C₀',v.c_over_c0,'')+`<div class="formgrid">${numField('ph','pH',v.ph,'')}${numField('temp_c',tr('Temperature','温度'),v.temp_c,'°C')}${numField('volume_ml',tr('Volume','体积'),v.volume_ml,'mL')}</div>`+input('note',tr('Note','备注'),v.note,'text','maxlength="2000"')
    +`<p class="muted">${tr('Pull time and quench stay as recorded. Earlier values are kept in the history below.','取样与淬灭时间保持原记录。修改前的数值保留在下方历史中。')}</p>`
    +(v.revisions.length?`<details><summary>${t('history')} · ${v.revisions.length}</summary>${v.revisions.slice().reverse().map(r=>`<p class="muted">${when(r.at)} · C/C₀ ${r.c_over_c0??'—'} · pH ${r.ph??'—'} · ${r.temp_c??'—'} °C · ${r.volume_ml??'—'} mL${r.note?' · '+esc(r.note):''}</p>`).join('')}</details>`:'');
  benchDialog(v.label,body,async f=>{const changes={c_over_c0:parseNum(f.get('c_over_c0')),ph:parseNum(f.get('ph')),temp_c:parseNum(f.get('temp_c')),volume_ml:parseNum(f.get('volume_ml')),note:f.get('note')};await commit(s=>L.editSample(s.lab.samples.find(x=>x.id===id),changes,labClock()));});}
function waterForm(id){const e=benchRun(id),w=e.water||{matrix:'mbr_effluent',lot:'',filtered:null,spiked:null};const tri=(name,label,v)=>`<label>${esc(label)}<select name="${name}"><option value="" ${v==null?'selected':''}>—</option><option value="yes" ${v===true?'selected':''}>${tr('Yes','是')}</option><option value="no" ${v===false?'selected':''}>${tr('No','否')}</option></select></label>`;
  const body=`<label>${tr('Matrix','水体类型')}<select name="matrix">${L.MATRICES.map(m=>`<option value="${m}" ${m===w.matrix?'selected':''}>${esc(matrixName(m))}</option>`).join('')}</select></label>`
    +`<div class="formgrid">${input('lot',tr('Lot or sampling date','批次或采样日期'),w.lot,'text','maxlength="100"')}${tri('filtered',tr('Filtered, 0.45 µm','过 0.45 µm 滤膜'),w.filtered)}${tri('spiked',tr('Target spiked','目标物为加标'),w.spiked)}</div>`
    +`<div class="formgrid">${L.WATER_NUMBERS.map(k=>{const f=WATER_FIELDS[k];return numField(k,tr(f[0],f[1]),w[k],f[2],`placeholder="${tr('not measured','未测')}"`);}).join('')}</div>`
    +`<div class="suva"><div class="row between"><b>SUVA₂₅₄</b><span class="computed">${tr('computed','计算值')}</span></div><div class="suva-v" data-bench-suva></div><p class="muted" data-bench-suvatext></p></div>`;
  const d=benchDialog(t('water'),body,async f=>{const yn=v=>v==='yes'?true:v==='no'?false:null,water={matrix:f.get('matrix'),lot:f.get('lot'),filtered:yn(f.get('filtered')),spiked:yn(f.get('spiked'))};for(const k of L.WATER_NUMBERS)water[k]=parseNum(f.get(k));
    await refreshClock();await commit(s=>L.setWater(s.lab,s.lab.experiments.find(x=>x.id===id),water,labClock()));});
  const live=()=>{let sv=null;try{sv=L.suva({doc_mg_c_l:parseNum(d.querySelector('[name=doc_mg_c_l]').value),uv254_cm1:parseNum(d.querySelector('[name=uv254_cm1]').value)});}catch(_){sv=null;}d.querySelector('[data-bench-suva]').innerHTML=`${sv==null?'—':sv.toFixed(2)} <small>L mg⁻¹ m⁻¹</small>`;d.querySelector('[data-bench-suvatext]').textContent=suvaText(sv);};
  d.addEventListener('input',live);live();}

/* ---- Demo: a synthetic UV/PDS run. Values are invented. ---- */
labDemo=async function(){if(state.lab.demo_loaded){notice(t('demoDone'));return;}await refreshClock();await commit(s=>{const c=labClock(),at=ms=>({wall:c.wall-12*60000+ms,mono:ms,boot:'synthetic-demo'});
  const e=L.experiment(s.lab,tr('Demo run · UV/PDS','演示反应 · UV/PDS'),tr('Synthetic demo. All values are invented, not measured.','自制演示，所有数值均为虚构，并非实测。'),'',at(0));
  L.setRun(s.lab,e,{process:'UV/PDS',target:tr('Synthetic target A','自制目标物 A'),oxidant:'PDS',oxidant_mm:1,wavelength_nm:254,fluence_rate_mw_cm2:null},at(0));
  L.setWater(s.lab,e,{matrix:'mbr_effluent',lot:'DEMO-01',filtered:true,spiked:true,doc_mg_c_l:6.8,uv254_cm1:0.142,alkalinity_mg_caco3_l:210,chloride_mg_l:85,nitrate_n_mg_l:12,bromide_ug_l:null,conductivity_ms_cm:1.1,ph:7.8},at(0));
  const first=L.sample(s.lab,e.id,{pulled:at(3000),quench:{agent:'Na₂S₂O₃',at:at(8000)},ph:7.8,temp_c:24.1,volume_ml:1},at(8000));L.editSample(first,{c_over_c0:1},at(700000));
  L.schedule(s.lab,e,[1,2,5,10,20,30],at(5000));
  for(const [ms,d,ph,tc,cc] of [[60000,2000,7.81,24.3,0.92],[120000,-3000,7.8,24.5,0.84],[300000,4000,7.79,24.8,0.64],[600000,14000,7.77,25.1,0.41]]){const tm=s.lab.timers.find(x=>x.experiment_id===e.id&&x.duration_ms===ms);
    const v=L.sample(s.lab,e.id,{timer_id:tm.id,pulled:at(ms+d),quench:{agent:'Na₂S₂O₃',at:at(ms+d+6000)},ph,temp_c:tc,volume_ml:1},at(ms+d+6000));L.editSample(v,{c_over_c0:cc},at(700000));}
  const counter=L.counter(s.lab,tr('Syringe filters used','已用针头滤器'),e.id,at(0));L.count(s.lab,counter,'add',at(1000));L.count(s.lab,counter,'add',at(61000));
  L.record(s.lab,e.id,tr('Pale yellow at 5 min. No precipitate. Lamp output steady.','5 分钟时溶液呈浅黄色，未见沉淀，灯管输出稳定。'),'',at(320000));s.lab.demo_loaded=true;});render();notice(t('saved'));};

/* ---- Events ---- */
document.addEventListener('click',async event=>{const el=event.target.closest('[data-bench]');if(!el||el.disabled||busy||fatal)return;const a=el.dataset.bench;try{
  if(a==='newRun'){runForm();return;}
  if(a==='editRun'){runForm(el.dataset.id);return;}
  if(a==='takeSample'){await sampleSheet(el.dataset.experiment,el.dataset.timer||null);return;}
  if(a==='editSample'){sampleForm(el.dataset.id);return;}
  if(a==='editWater'){waterForm(el.dataset.id);return;}
  if(a==='exportSamples'){await saveChain;const e=el.dataset.id&&benchRun(el.dataset.id);await exportFile(`envbench-samples-${e?e.id.slice(0,8):D.day()}.csv`,L.samplesCsv(state.lab,e?e.id:null),'text/csv');return;}
  if(a==='quench'){const d=el.closest('dialog');d.querySelectorAll('.chip').forEach(c=>c.setAttribute('aria-pressed',c===el?'true':'false'));d.querySelector('[name=quench_other]').value='';chooseQuench(d,el.dataset.agent);return;}
  if(a==='step'){const field=document.getElementById(el.dataset.for),dec=Number(el.dataset.dec);let v;try{v=parseNum(field.value);}catch(_){v=null;}field.value=(v==null?Number(el.dataset.base):v+Number(el.dataset.step)).toFixed(dec);return;}
}catch(e){if(e.message!=='cancelled')notice(errorText(e),true);}});
document.addEventListener('change',async event=>{const el=event.target;if(!el.matches?.('.bench-cc')||busy||fatal)return;const v=state.lab.samples.find(x=>x.id===el.dataset.sample);
  try{const value=parseNum(el.value);await commit(s=>L.editSample(s.lab.samples.find(x=>x.id===v.id),{c_over_c0:value},labClock()));const box=document.querySelector(`[data-bench-fit="${el.dataset.experiment}"]`);if(box)box.innerHTML=fitInner(benchRun(el.dataset.experiment));}
  catch(e){el.value=v?.c_over_c0??'';notice(errorText(e),true);}});
setInterval(()=>{if(document.hidden||fatal||!state.lab)return;const c=labClock();document.querySelectorAll('[data-bench-focus]').forEach(el=>{const e=benchRun(el.dataset.benchFocus);if(!e)return;const n=L.nextSample(state.lab,e,c),key=n?`${n.state}:${n.timer.id}`:'none';
  if(key!==el.dataset.state){el.outerHTML=benchFocus(e);return;}const left=el.querySelector('[data-bench-left]');if(left&&n)left.textContent=leftText(n.left_ms);});},250);
