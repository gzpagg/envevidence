"""Physical-size figures and self-contained, replayable analysis archives."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import platform
import re
import zipfile
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path, PurePosixPath
from uuid import uuid4

from openpyxl import Workbook

from .exporting import safe_cell, xlsx_cell

MAX_PIXELS = 50_000_000
CONFIG_SCHEMA = "envbench-analysis-config-v1"
FONT_PATH = Path(__file__).parent / "assets" / "fonts" / "NotoSansCJKsc-Regular.otf"
MODEL_LABELS = {
    "zero_order": "Zero order", "first_order": "First order", "second_order": "Second order",
    "plateau_first": "Plateau first order", "adsorption_pfo": "Adsorption PFO",
    "adsorption_pso": "Adsorption PSO", "intraparticle": "Intraparticle", "monod": "Monod",
}


class ExportError(ValueError):
    """An export or replay cannot be made without changing its meaning."""


def _mapping(value):
    return value.model_dump(mode="json") if hasattr(value, "model_dump") else dict(value)


def _json(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode("utf-8")


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _versions():
    versions = {"python": platform.python_version()}
    for package in ("envevidence", "numpy", "scipy", "matplotlib", "openpyxl"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "not-installed"
    return versions


def raster_dimensions(config) -> tuple[int, int]:
    """Return rounded raster dimensions, checking allocation before rendering."""
    config = _mapping(config)
    width, height, dpi = (
        config.get("width_mm", 90), config.get("height_mm", 65), config.get("dpi", 300)
    )
    if any(not _number(x) or x <= 0 for x in (width, height, dpi)):
        raise ExportError("Figure width, height and DPI must be positive finite numbers.")
    if width * height * (dpi / 25.4) ** 2 > MAX_PIXELS:
        raise ExportError("The figure exceeds the 50 million pixel limit.")
    pixels = (round(width / 25.4 * dpi), round(height / 25.4 * dpi))
    if min(pixels) < 1 or pixels[0] * pixels[1] > MAX_PIXELS:
        raise ExportError("Invalid figure raster dimensions.")
    return pixels


def _font(config):
    from matplotlib.font_manager import FontProperties, findfont

    name = config.get("font", "Noto Sans CJK SC")
    if name == "Noto Sans CJK SC":
        if not FONT_PATH.is_file():
            raise ExportError("The bundled Noto Sans CJK SC font is missing.")
        return FontProperties(fname=str(FONT_PATH))
    try:
        return FontProperties(fname=findfont(name, fallback_to_default=False))
    except ValueError as exc:
        raise ExportError(f"Font is not installed: {name}") from exc


def _plot_rows(project):
    from .analysis_data import process_series

    return {series.id: process_series(series) for series in project.series}


def _legend_groups(project, sources):
    groups = list(dict.fromkeys((r.get("series_id") or (
        project.series[0].id if len(project.series) == 1 else None
    ), r.get("run_id")) for r in sources))
    labels = {}
    for sid, run in groups:
        item = next((s for s in project.series if s.id == sid), None)
        series_number = next((i + 1 for i, s in enumerate(project.series) if s.id == sid), 1)
        runs = sorted({str(r) for s, r in groups if s == sid})
        code = f"S{series_number}"
        if len(runs) > 1:
            code += f"/R{runs.index(str(run)) + 1}"
        alias = str(item.conditions.get("plot_label", "")).strip() if item else ""
        label = alias or ("Measurements" if len(groups) == 1 else code)
        if alias and len(groups) > 1:
            label = code + " · " + alias
        labels[(sid, run)] = {
            "group_label": code, "display_label": label, "series_id": sid,
            "series_name": item.name if item else "", "run_id": run, "custom_alias": alias,
        }
    return labels


def legend_mapping(project, results=None, series_ids=None):
    """Resolve compact plot groups to complete scientific series and run identities."""
    sources = list(project.fit_results if results is None else results)
    if not sources:
        sources = [{"series_id": s.id, "run_id": None} for s in project.series]
    if series_ids is not None:
        sources = [r for r in sources if r.get("series_id") in series_ids]
    groups = _legend_groups(project, sources)
    mapping = []
    for group in groups.values():
        mapping.append({"kind": "measurements", **group, "model": None, "method": None})
    for result in sources:
        if result.get("model"):
            key = (result.get("series_id") or (project.series[0].id if len(project.series) == 1
                                              else None), result.get("run_id"))
            mapping.append({"kind": "curve", **groups[key], "model": result["model"],
                            "method": result.get("method"),
                            "accepted": result.get("accepted", False),
                            "model_label": MODEL_LABELS.get(result["model"], result["model"])})
    return mapping


def _wrap_legend(label, font, renderer, max_width):
    """Limit labels to two measured lines; full aliases remain in the mapping table."""
    lines, current = [], ""
    for char in label:
        if renderer.get_text_width_height_descent(current + char, font, False)[0] > max_width:
            lines.append(current.strip())
            current = char
            if len(lines) == 2:
                lines[-1] = lines[-1].rstrip()[:-1] + "…"
                return "\n".join(lines)
        else:
            current += char
    if current:
        lines.append(current.strip())
    return "\n".join(lines)


def render_plot(project, kind="curve", output_format=None, results=None, series_ids=None) -> bytes:
    """Render curve, residual or transformed data using the saved plot configuration.

    Raster sizes round millimetres to the nearest pixel. SVG keeps the specified
    physical dimensions. SVG text is converted to glyph paths for portable Chinese.
    """
    from matplotlib import rc_context
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.colors import is_color_like
    from matplotlib.figure import Figure

    if kind not in {"curve", "residual", "transformed"}:
        raise ExportError("Unknown plot kind.")
    config = _mapping(project.plot)
    px, py = raster_dimensions(config)
    fmt = output_format or config.get("format", "png")
    if fmt not in {"png", "tiff", "svg"}:
        raise ExportError("Plot format must be png, tiff or svg.")
    dpi = config.get("dpi", 300)
    size = (config.get("width_mm", 90) / 25.4, config.get("height_mm", 65) / 25.4)
    if fmt != "svg":
        size = (px / dpi, py / dpi)
    colors = config.get("colors") or ["#147D73", "#A65338", "#1D4ED8", "#6D4ACF"]
    if any(not is_color_like(color) for color in colors):
        raise ExportError("Invalid plot color.")
    font = _font(config)
    fontsize = config.get("font_size", 9)
    if not _number(fontsize) or fontsize <= 0:
        raise ExportError("Font size must be positive.")
    font.set_size(fontsize)
    rows = _plot_rows(project)
    series = {item.id: item for item in project.series}
    fit_results = project.fit_results if results is None else results
    sources = list(fit_results) or [
        {"series_id": item.id, "series_name": item.name, "predictions": rows[item.id]}
        for item in project.series
    ]
    if results is None and fit_results and kind == "curve":
        fitted_ids = {result.get("series_id") for result in fit_results}
        sources.extend({"series_id": item.id, "series_name": item.name,
                        "predictions": rows[item.id]}
                       for item in project.series if item.id not in fitted_ids)
    if series_ids is not None:
        sources = [result for result in sources if result.get("series_id") in series_ids]
    if kind == "transformed":
        sources = [result for result in sources if result.get("transformed_metrics")]
        transforms = {str(result["transformed_metrics"].get("transform")) for result in sources}
        if len(transforms) > 1:
            raise ExportError("Different transformations require separate plots.")
    selected_ids = {result.get("series_id") for result in sources}
    if selected_ids == {None} and len(project.series) == 1:
        selected_ids = {project.series[0].id}
    units = {(row.get("x_unit", series[sid].x_unit), row.get("y_unit", series[sid].y_unit))
             for sid in selected_ids if sid in series for row in rows[sid]}
    observables = {"qt" if series[sid].processing.compute_qt else series[sid].observable
                   for sid in selected_ids if sid in series}
    axes = {"substrate" if series[sid].kind == "monod" else "time"
            for sid in selected_ids if sid in series}
    if len(units) > 1 or len(observables) > 1 or len(axes) > 1:
        raise ExportError("Select series with the same processed units and observable for an overlay.")
    with rc_context({"svg.fonttype": "path", "axes.unicode_minus": False, "text.usetex": False}):
        fig = Figure(figsize=size, dpi=dpi)
        FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        # Fixed margins preserve output dimensions, unlike bbox_inches='tight'.
        fig.subplots_adjust(left=0.22, bottom=0.25, right=0.97, top=0.94)
        plotted = set()
        groups = _legend_groups(project, sources)
        group_keys = list(groups)
        model_keys = list(dict.fromkeys((r.get("model"), r.get("method")) for r in sources))
        legend_entries = []
        for result in sources:
            sid = result.get("series_id")
            if sid is None and len(project.series) == 1:
                sid = project.series[0].id
            source_rows = rows.get(sid, [])
            group_key = (sid, result.get("run_id"))
            name = groups[group_key]["display_label"]
            label = MODEL_LABELS.get(result.get("model"), result.get("model", name))
            if result.get("method"):
                label += " (" + str(result["method"]) + ")"
            if len(groups) > 1:
                label = name + " · " + label
            group_number = group_keys.index(group_key)
            model_number = model_keys.index((result.get("model"), result.get("method")))
            color = colors[(model_number if len(groups) == 1 else group_number) % len(colors)]
            point_color = "#454545" if len(groups) == 1 else color
            base_style = config.get("line_style", "-")
            styles = [base_style] + [style for style in ["-", "--", "-.", ":"]
                                     if style != base_style]
            linestyle = styles[model_number % len(styles)]
            points = result.get("predictions") or source_rows
            xkey = "transformed_x" if kind == "transformed" else "x"
            ykey = "residual" if kind == "residual" else (
                "transformed_y" if kind == "transformed" else "y"
            )
            valid = [p for p in points if _number(p.get(xkey)) and _number(p.get(ykey))]
            included = [p for p in valid if p.get("included", True)]
            excluded = [p for p in valid if not p.get("included", True)]
            point_key = ((sid, result.get("run_id")) if kind == "curve" else
                         (sid, result.get("run_id"), result.get("model"), result.get("method")))
            if point_key not in plotted:
                marker = config.get("marker", "o")
                marker_size = config.get("marker_size", 4)
                x, y = [p[xkey] for p in included], [p[ykey] for p in included]
                sigmas = []
                technical_sd_used = False
                for point in included:
                    matching = next((r for r in source_rows if r.get("sample_ids") ==
                                     point.get("sample_ids") and r.get("x") == point.get("x")), {})
                    sigma = point.get("sigma", matching.get("sigma"))
                    if sigma is None:
                        sigma = matching.get("technical_sd", point.get("technical_sd"))
                        technical_sd_used |= _number(sigma)
                    sigmas.append(sigma if _number(sigma) and sigma >= 0 else 0)
                point_label = name if kind == "curve" else label
                if kind == "curve" and config.get("error_bars", True) and technical_sd_used:
                    point_label = ("Technical mean ± SD" if len(groups) == 1 else
                                   name + " (technical SD)")
                points_handle = ax.errorbar(
                    x, y, yerr=sigmas if kind == "curve" and config.get("error_bars", True)
                    and any(sigma > 0 for sigma in sigmas)
                    else None, fmt=marker, markersize=marker_size,
                    color=point_color if kind == "curve" else color,
                    linewidth=config.get("line_width", 1.4), capsize=2,
                    label=point_label,
                )
                legend_entries.append((points_handle, point_label))
                if excluded:
                    excluded_handle, = ax.plot([p[xkey] for p in excluded], [p[ykey] for p in excluded],
                            linestyle="none", marker=marker, markersize=marker_size,
                            markerfacecolor="none", markeredgecolor=point_color,
                            label=name + " (excluded)")
                    legend_entries.append((excluded_handle, name + " (excluded)"))
                plotted.add(point_key)
            if kind == "curve" and config.get("show_curve", True) and result.get("curve"):
                curve = [p for p in result["curve"] if _number(p.get("x")) and _number(p.get("y"))]
                curve_handle, = ax.plot([p["x"] for p in curve], [p["y"] for p in curve], color=color,
                        linewidth=config.get("line_width", 1.4),
                        linestyle=linestyle, label=label)
                legend_entries.append((curve_handle, label))
            elif kind == "transformed" and config.get("show_curve", True):
                curve = sorted([p for p in valid if p.get("included", True) and
                                _number(p.get("transformed_predicted"))], key=lambda p: p[xkey])
                curve_handle, = ax.plot([p[xkey] for p in curve], [p["transformed_predicted"] for p in curve],
                        color=color, linewidth=config.get("line_width", 1.4),
                        linestyle=linestyle, label=label)
                legend_entries.append((curve_handle, label))
        if kind == "residual":
            ax.axhline(0, color="#737373", linewidth=0.7, linestyle="--")
        first = next((item for item in project.series if item.id in selected_ids), None)
        xunit, yunit = next(iter(units)) if units else (
            (first.x_unit, first.y_unit) if first else ("", "")
        )
        xname = "Substrate concentration" if first and first.kind == "monod" else "Time"
        xlabel = config.get("x_label") or (f"{xname} ({xunit})" if xunit else "x")
        ylabel = config.get("y_label") or (
            f"{next(iter(observables))} ({yunit})" if first and yunit else "Response"
        )
        if kind == "residual":
            ylabel = f"Residual ({yunit})" if yunit else "Residual"
        elif kind == "transformed":
            xlabel, ylabel = "Transformed x", "Transformed response"
            transforms = {str(r.get("transformed_metrics", {}).get("transform", ""))
                          for r in sources if r.get("transformed_metrics")}
            if len(transforms) == 1 and next(iter(transforms)):
                ylabel = next(iter(transforms))
        ax.set_xlabel(xlabel, fontproperties=font, parse_math=False)
        ax.set_ylabel(ylabel, fontproperties=font, parse_math=False)
        for axis, lo, hi in (("x", config.get("x_min"), config.get("x_max")),
                             ("y", config.get("y_min"), config.get("y_max"))):
            if (lo is not None and not _number(lo)) or (hi is not None and not _number(hi)):
                raise ExportError("Axis bounds must be finite.")
            if lo is not None and hi is not None and lo >= hi:
                raise ExportError("Axis minimum must be smaller than its maximum.")
            if lo is not None or hi is not None:
                (ax.set_xlim if axis == "x" else ax.set_ylim)(lo, hi)
        for tick in ax.get_xticklabels() + ax.get_yticklabels():
            tick.set_fontproperties(font)
        if config.get("legend", True) and legend_entries:
            fig.canvas.draw()
            renderer = fig.canvas.get_renderer()
            legend_font = font.copy()
            legend_font.set_size(min(fontsize, 8) if len(legend_entries) > 4 else fontsize)
            max_width = ax.get_window_extent(renderer).width * 0.82
            handles = [entry[0] for entry in legend_entries]
            labels = [_wrap_legend(entry[1], legend_font, renderer, max_width)
                      for entry in legend_entries]
            legend = ax.legend(handles, labels, prop=legend_font, frameon=False, loc="best",
                               handlelength=1.6, borderaxespad=0.4, labelspacing=0.3)
            for text in legend.get_texts():
                text.set_parse_math(False)
            fig.canvas.draw()
            bounds = legend.get_window_extent(fig.canvas.get_renderer())
            if (bounds.width > ax.get_window_extent().width or
                    bounds.height > ax.get_window_extent().height * 0.65):
                raise ExportError("This figure is too small for the legend. Increase its size, "
                                  "select fewer curves, or hide the legend.")
        buffer = io.BytesIO()
        fig.savefig(buffer, format=fmt, dpi=dpi, facecolor="white", bbox_inches=None)
        fig.clear()
        return buffer.getvalue()


def _cell(value):
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    return value


def _columns(rows):
    return list(dict.fromkeys(key for row in rows for key in row)) or ["status"]


def table_csv(rows) -> bytes:
    stream = io.StringIO(newline="")
    columns = _columns(rows)
    writer = csv.writer(stream, lineterminator="\r\n")
    writer.writerow([safe_cell(key) for key in columns])
    writer.writerows([[safe_cell(_cell(row.get(key))) for key in columns] for row in rows])
    return stream.getvalue().encode("utf-8-sig")


def _workbook(tables) -> bytes:
    workbook = Workbook()
    workbook.remove(workbook.active)
    for name, rows in tables.items():
        sheet = workbook.create_sheet(name)
        columns = _columns(rows)
        sheet.append([xlsx_cell(key) for key in columns])
        for row in rows:
            sheet.append([xlsx_cell(_cell(row.get(key))) for key in columns])
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
    stream = io.BytesIO()
    workbook.save(stream)
    return stream.getvalue()


def _filename(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(name)).strip(" .")
    if re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", name.split(".")[0]):
        name = "_" + name
    return (name[:120] or "source.bin")


def _tables(project):
    rows = _plot_rows(project)
    processed, parameters, predictions, comparison, curves = [], [], [], [], []
    for series in project.series:
        processed.extend({"series_id": series.id, "series_name": series.name,
                          "x_unit": series.x_unit, "y_unit": series.y_unit, **row}
                         for row in rows[series.id])
    for result in project.fit_results:
        info = {key: result.get(key) for key in (
            "series_id", "series_name", "run_id", "request_id", "request_index", "accepted",
            "model", "method",
        )}
        comparison.append({**info, "status": result.get("status"),
                           **result.get("metrics", {}), "errors": result.get("errors", []),
                           "warnings": result.get("warnings", []),
                           "transformed_metrics": result.get("transformed_metrics"),
                           "diagnostics": result.get("diagnostics", {}),
                           "uncertainty_basis": result.get("uncertainty_basis") or {
                               "confidence_level": 0.95,
                               "interval_estimator": ("normal_known_sigma_conditional"
                                                      if result.get("weighted") else
                                                      "student_t_residual_local_covariance"),
                               "covariance_response_scale": ("transformed" if
                                    result.get("method") == "linearized" else "raw"),
                               "parameter_mapping": "physical_parameter_jacobian_delta_method",
                               "fixed_parameter_uncertainty_propagated": False,
                               "preprocessing_reference_uncertainty_propagated": False,
                           }})
        for name, parameter in result.get("parameters", {}).items():
            parameters.append({**info, "parameter": name, **parameter})
        predictions.extend({**info, **point} for point in result.get("predictions", []))
        curves.extend({**info, "x_unit": result.get("x_unit"), "y_unit": result.get("y_unit"),
                       **point} for point in result.get("curve", []))
    return {"Processed": processed, "Parameters": parameters,
            "Predictions": predictions, "Comparison": comparison, "Curves": curves,
            "LegendMapping": legend_mapping(project)}


def _sop():
    return """# EnvBench analysis SOP · template v1

1. Keep originals/ unchanged; manifest.json records hashes and software versions.
2. Review project_snapshot.json and manual_snapshot.json for inputs and audit history.
3. Review processed.csv: exclusions, transformations, corrections and aggregation.
4. Review parameters.csv, predictions.csv and comparison.csv with each model's warnings.
5. Inspect plots/ curves, residuals and transformed views before interpreting a fit.
6. Replay from the extracted folder:
   envevidence analyze --config analysis_config.json --output NEW_FOLDER

analysis_config.json includes the full analysis snapshot, processing and fit requests,
plot settings and relative original paths. Replay validates original SHA-256 hashes.
The replay command recalculates from the snapshot; saved fit_results are audit records.
Record the final scientific interpretation and deviations below; a fit alone does
not establish a mechanism.

## Confidence interval basis

Unweighted intervals use a local covariance estimate scaled by residual variance
and a Student-t critical value. Weighted intervals use the supplied positive
measurement sigma as absolute uncertainty and a normal critical value; they are
conditional on that sigma. These are local, approximate parameter intervals,
not prediction intervals. Linearized fits estimate covariance on their transformed
response scale and map it to physical parameters by a Jacobian (delta method).
Fixed parameters and preprocessing references are treated as known: their
measurement uncertainty, as well as uncertainty in blank/dilution/mass/volume,
is not propagated. Comparison tables retain the interval basis, fit diagnostics
and reasons when intervals are withheld.

## Researcher interpretation

## Deviations and reasons
""".encode("utf-8")


def _mobile_members(project, payloads):
    from .analysis_data import _read_mobile_zip

    sources = {source.id: source for source in project.sources}
    members = {}
    for recorded in project.mobile_archives:
        source = sources.get(recorded.get("source_id"))
        if source is None or source.id not in payloads:
            raise ExportError("Mobile archive source is missing.")
        workspace, originals = _read_mobile_zip(payloads[source.id])
        expected = {name: f"mobile/{source.sha256}/{name}" for name in originals}
        if workspace != recorded.get("workspace") or expected != recorded.get("members"):
            raise ExportError("Mobile archive metadata differs from its original ZIP.")
        members.update({expected[name]: content for name, content in originals.items()})
    return members


def bundle_bytes(project, store) -> bytes:
    """Create a ZIP containing immutable originals, configuration, tables and figures."""
    snapshot = _mapping(project)
    files = {}
    original_payloads = {}
    for source, dumped in zip(project.sources, snapshot["sources"]):
        if not re.fullmatch(r"[a-f0-9]{32}", source.id):
            raise ExportError("Original source IDs must be 32 hexadecimal characters.")
        payload = store.read_source(project, source)
        original_payloads[source.id] = payload
        path = f"originals/{source.id}/{_filename(source.name)}"
        dumped["relative_path"] = path
        files[path] = payload
    files.update(_mobile_members(project, original_payloads))
    config = {"schema": CONFIG_SCHEMA, "created_at": datetime.now(timezone.utc).isoformat(),
              "software": _versions(), "project": snapshot}
    files["analysis_config.json"] = _json(config)
    files["project_snapshot.json"] = _json(snapshot)
    files["manual_snapshot.json"] = _json({
        "schema": "envbench-manual-snapshot-v1", "history": snapshot.get("history", []),
        "series": [{"series_id": s["id"], "name": s["name"],
                    "observations": s.get("observations", []), "processing": s.get("processing")}
                   for s in snapshot.get("series", [])],
        "mobile_archives": snapshot.get("mobile_archives", []),
    })
    tables = _tables(project)
    for name, rows in tables.items():
        filename = "legend_mapping.csv" if name == "LegendMapping" else name.lower() + ".csv"
        files[filename] = table_csv(rows)
    files["analysis.xlsx"] = _workbook(tables)
    files["SOP.md"] = _sop()
    plot = snapshot["plot"]
    accepted_results = [result for result in project.fit_results if result.get("accepted")]
    figure_results = accepted_results or project.fit_results
    formats = list(dict.fromkeys(plot.get("formats") or [plot.get("format", "png")]))
    kinds = ["curve"]
    if project.fit_results and plot.get("show_residual", True):
        kinds.append("residual")
    groups = {}
    processed_rows = _plot_rows(project)
    for series in project.series:
        rows = processed_rows[series.id]
        units = ((rows[0].get("x_unit", series.x_unit), rows[0].get("y_unit", series.y_unit))
                 if rows else (series.x_unit, series.y_unit))
        observable = "qt" if series.processing.compute_qt else series.observable
        key = (observable, "substrate" if series.kind == "monod" else "time", *units)
        groups.setdefault(key, []).append(series.id)
    for index, selected in enumerate(groups.values()):
        prefix = "" if len(groups) == 1 else f"group-{index + 1}-"
        for kind in kinds:
            plotted_results = list(figure_results)
            if kind == "curve":
                fitted_ids = {result.get("series_id") for result in figure_results}
                plotted_results.extend({"series_id": item.id, "series_name": item.name,
                                        "predictions": processed_rows[item.id]}
                                       for item in project.series if item.id not in fitted_ids)
            for fmt in formats:
                files[f"plots/{prefix}{kind}.{fmt}"] = render_plot(
                    project, kind=kind, output_format=fmt, series_ids=selected,
                    results=plotted_results,
                )
        if plot.get("show_transformed", True):
            transformations = {}
            for result in figure_results:
                if result.get("series_id") in selected and result.get("transformed_metrics"):
                    transform = str(result["transformed_metrics"].get("transform"))
                    transformations.setdefault(transform, []).append(result)
            for transform_index, transform_results in enumerate(transformations.values()):
                transformed_name = ("transformed" if len(transformations) == 1 else
                                    f"transformed-{transform_index + 1}")
                for fmt in formats:
                    files[f"plots/{prefix}{transformed_name}.{fmt}"] = render_plot(
                        project, kind="transformed", output_format=fmt,
                        series_ids=selected, results=transform_results,
                    )
    files["manifest.json"] = _json({
        "schema": "envbench-analysis-manifest-v1", "project_id": project.id,
        "config_schema": CONFIG_SCHEMA, "software": config["software"],
        "sources": snapshot["sources"],
        "files": {path: {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
                  for path, payload in sorted(files.items())},
        "font": json.loads((FONT_PATH.parent / "SOURCE.json").read_text(encoding="utf-8-sig")),
    })
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, payload in sorted(files.items()):
            archive.writestr(path, payload)
    return stream.getvalue()


def export_bundle(project, store, output_dir) -> Path:
    """Write to a unique file; an existing export is never overwritten."""
    payload = bundle_bytes(project, store)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    while True:
        target = output_dir / f"envbench-analysis-{project.id[:8]}-{uuid4().hex[:12]}.zip"
        try:
            with target.open("xb") as handle:
                handle.write(payload)
            return target
        except FileExistsError:
            continue


def replay_config(config_path):
    """Read an extracted SOP configuration and hash-verified source payloads.

    Return ``(AnalysisProject, {source_id: bytes})``; this function never writes
    to a project store or trusts saved fit results as recalculated results.
    """
    from .analysis_data import AnalysisProject

    config_path = Path(config_path)
    try:
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
        if config.get("schema") != CONFIG_SCHEMA:
            raise ExportError("Unsupported analysis configuration schema.")
        project = AnalysisProject.model_validate(config["project"])
    except (OSError, KeyError, json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, ExportError):
            raise
        raise ExportError("Cannot read the analysis configuration.") from exc
    root = config_path.parent.resolve()
    payloads = {}
    for source in project.sources:
        path = PurePosixPath(source.relative_path)
        if path.is_absolute() or ".." in path.parts or "\\" in str(path) or ":" in str(path):
            raise ExportError("Original paths must be relative to the configuration folder.")
        resolved = (root / Path(*path.parts)).resolve()
        if not resolved.is_relative_to(root):
            raise ExportError("Original path leaves the configuration folder.")
        try:
            payload = resolved.read_bytes()
        except OSError as exc:
            raise ExportError(f"Cannot read original: {source.name}") from exc
        if hashlib.sha256(payload).hexdigest() != source.sha256:
            raise ExportError(f"Original SHA-256 mismatch: {source.name}")
        payloads[source.id] = payload
    _mobile_members(project, payloads)
    return project, payloads


def restore_replay_sources(project, payloads, store):
    """Restore verified originals and photo members into a separate replay store.

    Existing differing originals are rejected. The caller saves the project after
    rerunning processing and fits. Source IDs and scientific observations stay intact.
    """
    from .analysis_data import _atomic_write

    base = store.project_dir(project.id).resolve()
    files = _mobile_members(project, payloads)
    for source in project.sources:
        payload = payloads.get(source.id)
        if payload is None or hashlib.sha256(payload).hexdigest() != source.sha256:
            raise ExportError(f"Original SHA-256 mismatch: {source.name}")
        path = PurePosixPath(source.relative_path)
        if path.is_absolute() or ".." in path.parts or "\\" in str(path) or ":" in str(path):
            raise ExportError("Original paths must be relative to the configuration folder.")
        files[str(path)] = payload
    targets = []
    for relative, payload in files.items():
        target = (base / Path(*PurePosixPath(relative).parts)).resolve()
        if not target.is_relative_to(base):
            raise ExportError("Original path leaves the replay store.")
        if target.exists() and target.read_bytes() != payload:
            raise ExportError("Replay would overwrite a different original file.")
        targets.append((target, payload))
    for target, payload in targets:
        if not target.exists():
            _atomic_write(target, payload)
