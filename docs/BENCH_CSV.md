# EnvBench samples CSV · schema v1

[Android guide](../android/README.md) · [简体中文说明](#简体中文)

**My space → Export all samples CSV** and the **Samples CSV** button on a run export one row per sample. Each row repeats the run and water-matrix properties, so the file can be opened directly in R, Python or Excel.

The file uses UTF-8 with a byte-order mark and CRLF line endings. Text is quoted; numeric cells remain numeric. Formula-like text beginning with `=`, `+`, `-` or `@` gets a leading apostrophe. Empty cells mean not recorded. Version 0.6.1 adds audit columns while retaining the `envbench-samples-v1` identifier and existing column names.

## Columns

| Column | Unit / values | Meaning |
|---|---|---|
| `schema` | `envbench-samples-v1` | Format identifier. |
| `run_id`, `sample_id` | 32 hex characters | Stable IDs retained through backup and import. |
| `run_title`, `target`, `oxidant` | text | User-entered run name, target and oxidant. |
| `process` | process preset | UV/PDS, UV/PMS, UV/H2O2, UV/chlorine, O3, O3/H2O2, Fenton, Photo-Fenton, PMS/catalyst, Electrochemical, Photocatalysis or Other. |
| `oxidant_mm` | mM | Initial oxidant dose. |
| `wavelength_nm` | nm | Lamp wavelength. |
| `fluence_rate_mw_cm2` | mW/cm² | Recorded fluence rate. |
| `matrix` | matrix preset | ultrapure, buffer, nom_isolate, surface_water, secondary_effluent, mbr_effluent, tertiary_effluent, industrial or other. |
| `matrix_lot` | text | Matrix lot or collection date. |
| `filtered_0_45um`, `target_spiked` | true / false / empty | Recorded filtration and spiking states. |
| `doc_mg_c_l` | mg C/L | Dissolved organic carbon. |
| `uv254_cm1` | cm⁻¹ | UV₂₅₄ absorbance per cm optical path. |
| `alkalinity_mg_caco3_l` | mg/L as CaCO₃ | Alkalinity. |
| `chloride_mg_l` | mg/L | Chloride. |
| `nitrate_n_mg_l` | mg/L as N | Nitrate-N. |
| `bromide_ug_l` | µg/L | Bromide. |
| `conductivity_ms_cm` | mS/cm | Conductivity. |
| `matrix_ph` | pH | Matrix pH before reaction. |
| `suva254_l_mg_m` | L mg⁻¹ m⁻¹ | Computed as `uv254_cm1 / doc_mg_c_l * 100`, rounded to 3 decimals; blank without both valid inputs. |
| `sample_label` | S-001, S-002, … | Sample label within the run. |
| `planned_s` | s | Scheduled checkpoint relative to run start; blank for unplanned samples. |
| `pulled_s` | s | Current sample elapsed time, including a recorded correction if present. Run creation is t = 0. |
| `delta_s` | s | `pulled_s - planned_s`; negative means earlier than planned. |
| `pulled_at_utc` | ISO 8601 | Original sample button-event wall-clock timestamp. |
| `quench_agent` | text | Chosen agent or an explicit `None`. |
| `quench_delay_s` | s | Current delay from sample to quench, including a recorded correction if present. |
| `quench_at_utc` | ISO 8601 | Original quench button-event wall-clock timestamp. |
| `recorded_pulled_s`, `recorded_quench_delay_s` | s | Original sample elapsed time and quench delay, retained when current timings are corrected. |
| `pulled_time_source`, `quench_time_source` | click / corrected / unknown | Source of the currently used timing. Legacy timing without a confirmed source is unknown. |
| `time_revision_reason` | text | Reason for the latest timing correction. |
| `ph`, `temp_c`, `volume_ml` | pH, °C, mL | Current sample values. |
| `ph_source`, `temp_c_source`, `volume_ml_source` | measured / carried / unmeasured / unknown / synthetic | Confirmed measurement, carried-over value, no measurement, legacy unknown source or synthetic demo value. |
| `fluence_mj_cm2` | mJ/cm² | Computed as fluence rate × current `pulled_s`, rounded to 0.1. Assumes constant fluence rate. |
| `peak_area` | instrument units | Recorded LC peak area. |
| `c_over_c0` | dimensionless | Entered C/C₀ or peak area / reference area, rounded to 6 decimals. |
| `fit_excluded` | true / false | User exclusion from the in-app fit. |
| `fit_exclusion_reason` | text | Recorded reason for exclusion. Legacy exclusions may have an empty reason. |
| `note` | text | Sample note. |

The CSV contains the current sample values plus original timing and source columns. Full backups contain the complete revision history. Original timestamps describe app operations; a timing correction changes the elapsed-time value used by the fit without rewriting those original events.

## Peak-area import

Use one format throughout a batch:

```text
Sample Area
S-001 10000
S-002 8200
S-003 6400
```

Or paste one area per row in sample order. Labelled rows accept tab, comma, semicolon or whitespace separators. Explicit Sample/Area or Sample/Peak Area headers are recognized. Internal empty rows and invalid rows are reported, and their positions remain intact. Any parse error blocks applying the whole batch; mixed formats, duplicate assignments and excess values must be corrected first.

The selected reference area must be positive. Interpreting the area ratio as C/C₀ assumes consistent analytical response and sample preparation; use directly entered, processed C/C₀ when your quantification uses calibration, internal-standard correction or dilution factors.

## Calculations

The pseudo-first-order check fits `ln(C/C₀) = a - k_obs × t`, using ordinary least squares and current sample elapsed time in minutes. It reports k_obs in min⁻¹, a t-based 95% confidence interval, t½ and R². At least three positive C/C₀ values are required. Zero values remain recorded but do not enter a logarithmic fit. The interface shows the fitted interval and point exclusions.

With five or more eligible points, a centered and scaled quadratic fit tests curvature at 95%. Its direction describes deviation from a single first-order model; it does not identify a reaction mechanism. Excluding a point requires a recorded reason.

When fluence rate is present, `k′E = k_obs (s⁻¹) / E₀ (mW cm⁻²)` is shown in cm² mJ⁻¹. When initial oxidant dose is present, `k_obs / [oxidant]₀` is shown for dose comparisons; that quotient is not a measured second-order rate constant. Fit summaries are displayed in the app; raw sample CSV columns support further analysis with your chosen model.

SUVA₂₅₄ is computed from recorded DOC and UV₂₅₄. The displayed bands provide a descriptive guide to DOM character.

## 简体中文

“我的 → 导出全部样品 CSV”与反应页“样品 CSV”导出此格式。每个样品一行，每行附带反应和水质信息；可直接导入 R、Python 或 Excel。

- `pulled_s`、`quench_delay_s` 为当前使用的取样时长和淬灭延迟；`recorded_pulled_s`、`recorded_quench_delay_s` 保留原始按钮事件间隔。`pulled_at_utc`、`quench_at_utc` 始终为原始操作的系统时间。
- 时间来源列为 click（点击）、corrected（已修订）或 unknown（旧数据来源未知）；时间修订说明在 `time_revision_reason`。拟合、取样偏差与辐照剂量均使用当前取样时长。
- `ph_source`、`temp_c_source`、`volume_ml_source` 区分 measured（实测）、carried（沿用）、unmeasured（未测）、unknown（旧数据来源未知）与 synthetic（演示）。不会将旧版非空数据自动标成实测。
- 峰面积导入可用样品编号格式或纯数值顺序格式，同批数据不混用。内部空行、无效行、重复对应和多余数值必须修正；有任一错误时不会应用整批数据。
- 峰面积比视为 C/C₀ 的前提是分析响应与样品处理可比；使用校准、内标或稀释校正时，可直接填写处理后的 C/C₀。
- 准一级拟合使用至少三个正的 C/C₀；零值保留在记录中，不参与对数拟合。五点以上可作曲率检验，提示偏离单一一级模型。排除点时记录理由。
- `fit_exclusion_reason` 保存排除说明，完整 ZIP 保留所有修订历史。CSV 导出当前值、来源和原始时间，便于继续分析。
- `suva254_l_mg_m`、`fluence_mj_cm2` 是计算值；归一化 k′E 与剂量比值的公式和单位见上方计算说明。
