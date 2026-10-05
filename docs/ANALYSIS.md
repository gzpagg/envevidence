# Experiment analysis · desktop 0.5.0

[简体中文](ANALYSIS.zh-CN.md) · [Installation](../README.md#install-the-desktop-app) · [Validation](VALIDATION.md)

EnvEvidence organizes a complete analysis around an experiment: conditions, quantified measurements, processing rules, model fits, figures and a reproducible SOP package. The Android app supplies sampling times and bench records; the desktop connects these records to analytical results and compares kinetic descriptions.

## Try the complete workflow

1. Start the desktop app and open **Experiment analysis → Load analysis demo**. This creates a separate project containing self-created UV/H₂O₂ measurements with `C = 10 exp(−0.12t)` and clearly labelled synthetic conditions.
2. Inspect **Conditions** and **Measurements**. Each measurement has a sample ID and independent run ID.
3. In **Processing**, keep the default rules to preserve the entered values, or set an explicit correction and inspect its stages in the preview.
4. In **Fitting**, select candidate models and an original-scale or applicable linearized method. Click **Fit selected models**, then review the comparison, parameters and diagnostics.
5. In **Charts**, inspect curves and residuals, choose physical dimensions and DPI, and save the figure style.
6. In **SOP export**, select the results to use in the accepted figures, confirm your review and click **Create SOP package**. Download the ZIP and keep it with the experiment.

![Experiment analysis](images/analysis-en.png)

## Bring in measurements and bench records

Choose **Import / add data** and select an experiment type: degradation/removal, adsorption or biological rate. Choose the observable and specify the independent-variable and response units. For Monod, the independent variable is substrate concentration; for decay and adsorption it is elapsed reaction/contact time.

Paste a CSV or tab-separated table, or upload a CSV/Excel workbook and select a worksheet. Map the time/substrate and response columns, then optionally map sample ID, independent run ID, standard deviation, detection flag, exclusion and replicate type. Excel input should contain recorded numeric values; export a values-only worksheet when formulas were used upstream.

Example concentration table:

```csv
x,y,sample_id,run_id
0,10,S0,R1
5,7.4,S1,R1
10,5.5,S2,R1
15,4.1,S3,R1
20,3.0,S4,R1
30,1.65,S5,R1
```

The headers are examples; column mapping accepts your own names. Units belong to the series, so split columns or series when their units differ. Each independent run is fitted separately. Mark repeated analytical measurements of one sample as `technical`, give them the same sample ID and time, then enable technical aggregation to obtain the mean and sample SD. Aggregation preserves every member measurement; that SD is displayed as spread and is not automatically treated as the uncertainty of the mean for weighted fitting.

Detection flags are `valid`, `missing`, `below_lod` and `below_loq`; `<LOD`, `<LOQ` and `ND` aliases are accepted in the flag column. A censored value may be entered as `<0.02` with the corresponding flag. These rows remain in the data record with their exclusion reason. Corrections and explicit exclusions require a reason.

For phone records, import an EnvBench samples CSV or ZIP. The ZIP keeps the experiment snapshot, sample metadata, events, photos and revision history. In **Measurements → Link quantified results by sample ID**, upload assay results, map the sample and measured-value columns, specify the assay unit and record its source. This links laboratory measurements to the recorded sampling times. Phone C/C₀ values stay relative until an explicit absolute concentration reference is supplied. The recorded sample volume is separate from the reactor liquid volume used in an adsorption balance.

## Explicit processing rules

The preview records the raw value and each calculation stage. The order is:

1. For time-series experiments, subtract the analysis time-zero offset and convert the time unit.
2. Calculate `(measurement − blank) × dilution factor` in the entered measurement unit.
3. Apply an optional absolute reference to a relative concentration, then convert compatible units.
4. Optionally divide by a stated normalization reference, or calculate adsorption capacity.

Blank correction defaults to zero and dilution to one. Molar and mass units are separate conversion families; TOC carbon and COD oxygen bases are retained. Normalization uses a reference in the processed response unit; fitting C₀ is a separate choice.

For concentration-to-adsorption conversion:

`qt = (C0 − Ct) × V / m`

Here C₀ and Cₜ are in mg/L, reactor liquid volume V in L, adsorbent dry mass m in g and qₜ in mg/g. Confirm that a constant-volume/separate-bottle adsorption mass balance applies and that there is no other removal process. Enter independently corrected qₜ when serial withdrawal changes the balance or degradation contributes to concentration loss.

## Models and fitting decisions

| Model | Original-scale equation | Applicable linearization |
|---|---|---|
| Zero-order decay | `C = C0 − k0t` | Original scale |
| First-order decay | `C = C0 exp(−k1t)` | `ln(C) = ln(C0) − k1t` |
| Integrated second-order decay | `C = C0 / (1 + k2C0t)` | `1/C = 1/C0 + k2t` |
| First-order with plateau | `C = Cinf + (C0 − Cinf) exp(−k1t)` | Original scale |
| Adsorption pseudo-first order | `qt = qe[1 − exp(−k1t)]` | `ln(qe − qt) = ln(qe) − k1t`, with independently supplied fixed qₑ |
| Adsorption pseudo-second order | `qt = k2qe²t / (1 + k2qet)` | `t/qt = 1/(k2qe²) + t/qe` |
| Intraparticle diffusion | `qt = kid√t + b` | Original-scale fit over a user-selected interval |
| Monod substrate–rate | `rate = rate_max S / (Ks + S)` | Original scale |

Adsorption PFO/PSO start from q₀ = 0 and suit fresh adsorbent. A diffusion interval is chosen explicitly; its fitted line is a description of that interval. TOC/COD time series use apparent decay models. Monod uses a separate substrate–rate table: select specific growth rate, specific uptake rate or volumetric removal rate, and record how the rates were obtained.

Every parameter carries its dimensional unit. For example, decay k₀ is response/time; k₁ is 1/time; concentration-decay k₂ is 1/(concentration·time). Adsorption k₂ is 1/(capacity·time), or g/(mg·min) when q is mg/g and time is min. Monod Kₛ has the substrate unit, while `rate_max` has the selected rate unit. A fit to C/C₀ has coefficients on that relative scale; an absolute concentration reference is needed to interpret a dimensional second-order coefficient.

**Original-scale least squares is the default.** C₀ and qₑ are estimated unless you fix an independently measured value in the processed response unit. The plateau model enforces `0 ≤ Cinf ≤ C0`; kinetic rates are constrained to their physical range. Supplied positive measurement SDs can weight raw fits by `1/σ²`. Linearized fits use unweighted transformed residuals.

Each fit needs at least four included points and `n ≥ p + 2`, where p is the number of free parameters, plus at least two distinct independent-variable values. Invalid logarithms, reciprocals or t/qₜ transforms stop that fit and identify the required correction; explicitly exclude a point with a reason or choose another method. PFO linearization requires fixed qₑ, and PSO linearization requires positive time and capacity.

![Candidate fits and diagnostics](images/fitting-en.png)

Compare original-scale RMSE, MAE and R², the point count, fitted interval and residuals. Transformed-scale R² is shown separately. Results using different point sets have different masks in the predictions table. You select the accepted fits; the application does not assign a winning mechanism from the comparison.

Parameter intervals are local 95% covariance approximations: residual-based Student t for unweighted fits, or conditional normal intervals when measurement SDs are supplied. Linearized objectives estimate covariance on their transformed scale. Strong parameter correlation, rank deficiency, boundaries or constant responses withhold unreliable intervals. Fixed parameter and preprocessing-reference uncertainties are not automatically propagated. Check experimental support alongside the numerical diagnostics when interpreting a kinetic model.

## Figures and SOP packages

The default figure is **90 × 65 mm, 300 DPI, PNG**. Set width, height, DPI, axes, font size, line/marker style, colors, legend and error bars; save these choices with the project or SOP template. PNG and TIFF carry raster resolution; SVG stores scalable vector graphics and physical dimensions. Noto Sans CJK SC is bundled with its license for portable Chinese labels; SVG embeds glyph outlines. A 50-million-pixel limit applies before rendering large images.

![Figure dimensions and style](images/charts-en.png)

Save a named SOP template to reuse processing, field mappings, selected models and figure settings with matching experiment/observable series. Applying a template preserves measurements and requires a fresh review of the resulting fits.

The ZIP package contains:

| Contents | Purpose |
|---|---|
| `originals/` | Byte-preserved uploads or initial manual-input snapshots |
| `processed.csv` | Processing stages, units, technical repeats, masks and exclusions |
| `parameters.csv`, `predictions.csv`, `comparison.csv`, `curves.csv` | Parameters, uncertainty basis, point predictions/residuals, candidate comparison and plotting coordinates |
| `analysis.xlsx` | The same tables in one editable workbook |
| `plots/` | Accepted curves, residuals and applicable transformed views in the selected format |
| `analysis_config.json`, `project_snapshot.json`, `manual_snapshot.json` | Replay settings, the full project and audit history |
| `manifest.json`, `SOP.md` | File hashes, software/font sources and a procedure record with space for interpretation |

Candidate fit tables stay complete while accepted results determine the final figures. Every package receives a unique filename; earlier packages stay intact.

To replay, extract the ZIP and run from your installed repository directory:

```bash
envevidence analyze --config "path/to/extracted/analysis_config.json" --output data/replayed
```

With an unactivated virtual environment on Windows, use `.\.venv\Scripts\python.exe -m envevidence analyze` with the same arguments; on macOS/Linux use `.venv/bin/python -m envevidence analyze`. Replay validates original SHA-256 hashes, recalculates processing and fits from the snapshot, and writes a separate project and package. Recorded software versions allow you to reproduce the numerical environment; comparison across versions should use numerical tolerances.

Experiment projects are saved atomically under `data/analysis/` (or the configured data root). Back up the complete directory, including originals. Existing evidence projects retain their schema and review history. Scientific and interface checks are recorded in [validation](VALIDATION.md).
