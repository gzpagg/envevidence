# EnvBench samples CSV · schema v1

[EnvBench Android guide](../android/README.md) · [简体中文说明](#简体中文)

**My space → Export all samples CSV** and the **Samples CSV** button on a run both write this file. It has one row per sample, and every row repeats the run's process and water details, so the file can be loaded into R, Python or Excel without joins. The EnvEvidence desktop app will read the same columns when it imports bench runs (planned, not yet implemented).

The file is UTF-8 with a byte-order mark and CRLF line endings. Text cells are quoted; numbers are not. Text that starts with `=`, `+`, `-` or `@` gets a leading `'` so spreadsheets do not run it as a formula. An empty cell means "not recorded".

## Columns

| Column | Unit / values | Meaning |
|---|---|---|
| `schema` | `envbench-samples-v1` | Format identifier. A future change to column meaning gets a new identifier. |
| `run_id` | 32 hex characters | Stable experiment ID. Survives backups and imports. |
| `run_title` | text | Name typed by the user. |
| `process` | `UV/PDS`, `UV/PMS`, `UV/H2O2`, `UV/chlorine`, `O3`, `O3/H2O2`, `Fenton`, `Photo-Fenton`, `PMS/catalyst`, `Electrochemical`, `Photocatalysis`, `Other` | Treatment process. |
| `target` | text | Target compound. |
| `oxidant` | text | Oxidant name, for example `PDS`. |
| `oxidant_mm` | mM | Initial oxidant dose. |
| `wavelength_nm` | nm | Lamp wavelength. |
| `fluence_rate_mw_cm2` | mW/cm² | Fluence rate, if measured (for example by actinometry). |
| `matrix` | `ultrapure`, `buffer`, `nom_isolate`, `surface_water`, `secondary_effluent`, `mbr_effluent`, `tertiary_effluent`, `industrial`, `other` | Water matrix class. |
| `matrix_lot` | text | Lot or sampling date of the water. |
| `filtered_0_45um` | `true` / `false` / empty | Filtered through 0.45 µm before use. |
| `target_spiked` | `true` / `false` / empty | Target was spiked rather than native. |
| `doc_mg_c_l` | mg C/L | Dissolved organic carbon. |
| `uv254_cm1` | cm⁻¹ | UV absorbance at 254 nm per cm path length. |
| `alkalinity_mg_caco3_l` | mg/L as CaCO₃ | Alkalinity. |
| `chloride_mg_l` | mg/L | Cl⁻. |
| `nitrate_n_mg_l` | mg/L as N | NO₃⁻-N. |
| `bromide_ug_l` | µg/L | Br⁻. |
| `conductivity_ms_cm` | mS/cm | Conductivity. |
| `matrix_ph` | pH units | pH of the matrix before reaction. |
| `suva254_l_mg_m` | L mg⁻¹ m⁻¹ | **Computed**: `uv254_cm1 ÷ doc_mg_c_l × 100`, rounded to 3 decimals. Empty when either input is missing. |
| `sample_id` | 32 hex characters | Stable sample ID. |
| `sample_label` | `S-001`, `S-002`, … | Label in pull order within the run. |
| `planned_s` | s | Planned checkpoint after run start. Empty for unplanned samples. |
| `pulled_s` | s | Real pull time after run start. Run start (t = 0) is when the run was created in the app. |
| `delta_s` | s | `pulled_s − planned_s`. Negative means pulled early. |
| `pulled_at_utc` | ISO 8601 | Wall-clock time of the pull. |
| `quench_agent` | text | Quench agent chosen at the bench, or `None`. Always present: the app does not save a sample without it. |
| `quench_delay_s` | s | Time from pull to the quench tap. |
| `ph`, `temp_c`, `volume_ml` | pH units, °C, mL | Readings recorded with the sample. |
| `fluence_mj_cm2` | mJ/cm² | **Computed**: `fluence_rate_mw_cm2 × pulled_s`, rounded to 0.1. Empty without a fluence rate. Assumes a constant fluence rate over the run. |
| `peak_area` | instrument units | LC peak area, when C/C₀ came from pasted areas. |
| `c_over_c0` | dimensionless | C/C₀ entered after analysis, or `peak_area` ÷ the chosen reference area (rounded to 6 decimals). Earlier values are kept in the app's sample history and the full backup, not in this file. |
| `fit_excluded` | `true` / `false` | The user left this point out of the in-app fit. |
| `note` | text | Free note. |

Times are measured with Android's monotonic clock within one device boot, so changing the phone's clock during a run does not move them. After a reboot the app falls back to wall-clock time.

## What the app computes and what it does not

The app shows a pseudo-first-order fit: ordinary least squares of ln(C/C₀) against `pulled_s`, with k_obs, a 95% confidence interval from the t distribution, t½ and R². It needs at least three samples with C/C₀ > 0 that are not excluded. With five or more points it fits a quadratic in time and tests the squared term at 95%: a negative term (accelerating decay) is reported as a possible lag phase, a positive one (slowing decay) as possible tailing. When a fluence rate is set it also shows k′E = k_obs (s⁻¹) ÷ E₀ (mW cm⁻²) in cm² mJ⁻¹, and with an oxidant dose k_obs ÷ [oxidant]₀ for comparing doses; the latter is not a second-order rate constant. The fit is a check at the bench and is not exported as a value. Fit your own model from the raw columns for reporting.

SUVA₂₅₄ bands shown in the app (below 2, 2 to 4, above 4) are the commonly used rough guide for DOM character, not a classification.

## 简体中文

“我的 → 导出全部样品 CSV”与反应页的“样品 CSV”导出此格式：每个样品一行，并在每行重复该反应的工艺与水质信息，可直接导入 R、Python 或 Excel。电脑版 EnvEvidence 计划读取相同的列（尚未实现）。

- 时间列单位均为秒，以创建反应的时刻为 t = 0；`delta_s` 为实际取样时间减计划时间，负值表示提前。
- `quench_agent` 必填，未选择淬灭剂时应用不允许保存样品；`quench_delay_s` 为从取样到点选淬灭剂的时间。
- `suva254_l_mg_m` 为计算值（UV₂₅₄ ÷ DOC × 100），任一输入缺失时为空。
- 新增 `fluence_mj_cm2`（辐照强度 × 取样时间，计算值）、`peak_area`（粘贴的 LC 峰面积）和 `fit_excluded`（是否排除在应用内拟合之外）。
- `c_over_c0` 为分析后填写的 C/C₀，或峰面积 ÷ 参比峰面积；修改前的数值保留在应用内样品历史和完整备份中，不在此文件中。
- 应用中的准一级拟合只用于现场检查，不导出：5 个点以上时用二次项检验提示滞后或拖尾，设置辐照强度时显示 k′E（cm² mJ⁻¹）。正式报告请根据原始列自行拟合。
