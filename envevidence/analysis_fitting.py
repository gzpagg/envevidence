"""Auditable kinetic fits on original or explicitly transformed response scales.

Every input row is retained in the output. Only rows already marked excluded, or
outside an explicitly selected interval, are omitted from the objective. Invalid
included values fail the fit rather than being silently filtered.
"""

from __future__ import annotations

import math
import warnings
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from scipy.optimize import OptimizeWarning, curve_fit
from scipy.stats import norm
from scipy.stats import t as student_t

MODEL_SPECS = {
    "zero_order": {
        "family": "decay", "parameters": ["C0", "k0"], "methods": ["raw"],
        "equation": "C = C0 - k0*t",
    },
    "first_order": {
        "family": "decay", "parameters": ["C0", "k1"], "methods": ["raw", "linearized"],
        "equation": "C = C0*exp(-k1*t)",
    },
    "second_order": {
        "family": "decay", "parameters": ["C0", "k2"], "methods": ["raw", "linearized"],
        "equation": "C = C0/(1 + k2*C0*t)",
    },
    "plateau_first": {
        "family": "decay", "parameters": ["C0", "Cinf", "k1"], "methods": ["raw"],
        "equation": "C = Cinf + (C0-Cinf)*exp(-k1*t)",
    },
    "adsorption_pfo": {
        "family": "adsorption", "parameters": ["qe", "k1"],
        "methods": ["raw", "linearized"], "equation": "qt = qe*(1-exp(-k1*t))",
    },
    "adsorption_pso": {
        "family": "adsorption", "parameters": ["qe", "k2"],
        "methods": ["raw", "linearized"], "equation": "qt = k2*qe^2*t/(1+k2*qe*t)",
    },
    "intraparticle": {
        "family": "adsorption", "parameters": ["kid", "b"], "methods": ["raw"],
        "equation": "qt = kid*sqrt(t) + b",
    },
    "monod": {
        "family": "biological", "parameters": ["rate_max", "Ks"], "methods": ["raw"],
        "equation": "rate = rate_max*S/(Ks+S)",
    },
}

_EPS = np.finfo(np.float64).eps
_TIME_UNITS = {
    "s", "sec", "secs", "second", "seconds", "min", "mins", "minute", "minutes",
    "h", "hr", "hrs", "hour", "hours", "d", "day", "days",
}


def available_models(family: str) -> list[str]:
    """Biological time-series indicators use decay models as a separate input type."""
    if family in {"degradation", "removal", "indicator", "biological_decay"}:
        family = "decay"
    return [key for key, spec in MODEL_SPECS.items() if spec["family"] == family]


def predict(model: str, x: Any, parameters: Mapping[str, Any]) -> np.ndarray:
    """Evaluate a model; parameter dictionaries may be values or result entries."""
    p = {
        key: float(value["value"] if isinstance(value, Mapping) else value)
        for key, value in parameters.items()
    }
    x = np.asarray(x, dtype=np.float64)
    if model == "zero_order":
        return p["C0"] - p["k0"] * x
    if model == "first_order":
        return p["C0"] * np.exp(-p["k1"] * x)
    if model == "second_order":
        return p["C0"] / (1.0 + p["k2"] * p["C0"] * x)
    if model == "plateau_first":
        return p["Cinf"] + (p["C0"] - p["Cinf"]) * np.exp(-p["k1"] * x)
    if model == "adsorption_pfo":
        return -p["qe"] * np.expm1(-p["k1"] * x)
    if model == "adsorption_pso":
        return p["k2"] * p["qe"] ** 2 * x / (1.0 + p["k2"] * p["qe"] * x)
    if model == "intraparticle":
        return p["kid"] * np.sqrt(x) + p["b"]
    if model == "monod":
        return p["rate_max"] * x / (p["Ks"] + x)
    raise ValueError(f"Unknown model: {model}")


def parameter_units(model: str, x_unit: str, y_unit: str) -> dict[str, str]:
    units = {
        "C0": y_unit, "Cinf": y_unit, "qe": y_unit, "b": y_unit,
        "k0": f"{y_unit}/{x_unit}", "k1": f"1/{x_unit}",
        "k2": f"1/({y_unit}*{x_unit})", "kid": f"{y_unit}/sqrt({x_unit})",
        "rate_max": y_unit, "Ks": x_unit,
    }
    return {key: units[key] for key in MODEL_SPECS[model]["parameters"]}


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def _issue(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _metrics(y: np.ndarray, fitted: np.ndarray) -> dict[str, float | None]:
    residual = y - fitted
    sst = float(np.sum((y - np.mean(y)) ** 2))
    return {
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "mae": float(np.mean(np.abs(residual))),
        "r2": 1.0 - float(np.sum(residual**2)) / sst if sst > 0 else None,
    }


def _transformed(model: str, x: np.ndarray, y: np.ndarray, fixed: dict) -> np.ndarray:
    if model == "first_order":
        if np.any(y <= 0):
            raise ValueError("ln(C) requires every included response to be positive.")
        return np.log(y)
    if model == "second_order":
        if np.any(y <= 0):
            raise ValueError("1/C requires every included response to be positive.")
        return 1.0 / y
    if model == "adsorption_pfo":
        if "qe" not in fixed:
            raise ValueError("PFO linearization requires an independently supplied fixed qe.")
        if np.any(y >= fixed["qe"]):
            raise ValueError("ln(qe-qt) requires every included qt to be less than fixed qe.")
        return np.log(fixed["qe"] - y)
    if model == "adsorption_pso":
        if np.any(x <= 0) or np.any(y <= 0):
            raise ValueError("t/qt requires every included time and qt to be positive.")
        return x / y
    raise ValueError("This model does not have a supported linearization.")


def _transformed_prediction(model: str, x: np.ndarray, p: dict) -> np.ndarray:
    if model == "first_order":
        return np.log(p["C0"]) - p["k1"] * x
    if model == "second_order":
        return 1.0 / p["C0"] + p["k2"] * x
    if model == "adsorption_pfo":
        return np.log(p["qe"]) - p["k1"] * x
    return 1.0 / (p["k2"] * p["qe"] ** 2) + x / p["qe"]


def _initial(model: str, x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    xmax = max(float(np.ptp(x)), float(np.max(x)), 1e-12)
    ymax = max(float(np.max(y)), 1e-12)
    slope = float(np.polyfit(x, y, 1)[0])
    kguess = 1.0 / xmax
    if np.all(y > 0):
        kguess = max(-float(np.polyfit(x, np.log(y), 1)[0]), 0.01 / xmax)
    guesses = {
        "C0": ymax, "Cinf": float(np.min(y)) * 0.5, "qe": ymax * 1.2,
        "k0": max(-slope, ymax * 0.01 / xmax), "k1": kguess,
        "k2": 1.0 / (ymax * xmax), "kid": ymax / np.sqrt(xmax),
        "b": max(float(np.min(y)), 0.0), "rate_max": ymax * 1.5,
        "Ks": max(float(np.median(x)), 1e-12),
    }
    if model == "second_order" and np.all(y > 0):
        guesses["k2"] = max(float(np.polyfit(x, 1.0 / y, 1)[0]), 1e-12)
    if model.startswith("adsorption"):
        guesses["k1"] = 2.0 / xmax
    return {key: guesses[key] for key in MODEL_SPECS[model]["parameters"]}


def _parameterization(model: str, fixed: dict, initial: dict):
    """Parameterize free plateau Cinf as a fraction of C0 to enforce its bound."""
    keys = [key for key in MODEL_SPECS[model]["parameters"] if key not in fixed]
    fraction = model == "plateau_first" and "C0" in keys and "Cinf" in keys
    internal_keys = ["fraction" if fraction and key == "Cinf" else key for key in keys]
    lower, upper, start = [], [], []
    for key in internal_keys:
        lo, hi = 0.0, np.inf
        value = initial.get(key, initial.get("Cinf", 0.0) / initial.get("C0", 1.0))
        if key == "fraction":
            hi = 1.0
        if key in {"C0", "qe", "Ks", "rate_max"} or (
            key == "k2" and model == "adsorption_pso"
        ):
            lo = 1e-15
        if key == "C0" and model == "plateau_first" and "Cinf" in fixed:
            lo = max(lo, fixed["Cinf"])
        if key == "Cinf" and "C0" in fixed:
            hi = fixed["C0"]
        if key == "b":
            lo = -np.inf
        if not lo < hi:
            raise ValueError("The fixed parameters leave no feasible free-parameter interval.")
        if np.isfinite(lo):
            margin = max(abs(value), abs(lo), 1e-15) * 1e-8
            value = max(value, lo + margin)
        if np.isfinite(hi):
            margin = max(abs(value), abs(hi), 1e-15) * 1e-8
            value = min(value, hi - margin)
        lower.append(lo)
        upper.append(hi)
        start.append(value)

    def unpack(values):
        p = dict(fixed)
        p.update(dict(zip(internal_keys, values, strict=True)))
        if fraction:
            p["Cinf"] = p.pop("fraction") * p["C0"]
        return p

    def physical_jac(values):
        jac = np.zeros((len(keys), len(keys)), dtype=np.float64)
        for i, key in enumerate(keys):
            if fraction and key == "Cinf":
                jac[i, internal_keys.index("C0")] = values[internal_keys.index("fraction")]
                jac[i, internal_keys.index("fraction")] = values[internal_keys.index("C0")]
            else:
                jac[i, internal_keys.index(key)] = 1.0
        return jac

    return keys, unpack, physical_jac, np.array(start), np.array(lower), np.array(upper)


def fit_series(
    rows: Sequence[Mapping[str, Any]],
    model: str,
    method: str = "raw",
    fixed: Mapping[str, float] | None = None,
    x_unit: str = "min",
    y_unit: str = "mg/L",
    x_range: Sequence[float | None] | None = None,
    weighted: bool = False,
) -> dict[str, Any]:
    """Return a JSON-safe fit, diagnostics, row mask, and original-scale predictions."""
    fixed = dict(fixed or {})
    result: dict[str, Any] = {
        "model": model, "method": method, "status": "failed", "parameters": {},
        "metrics": {}, "transformed_metrics": None, "predictions": [], "curve": [],
        "errors": [], "warnings": [], "x_unit": x_unit, "y_unit": y_unit,
        "fixed": fixed, "weighted": weighted, "x_range": list(x_range) if x_range else None,
    }
    if model not in MODEL_SPECS:
        result["errors"].append(_issue("unknown_model", f"Unknown model: {model}"))
        return result
    if model == "monod" and x_unit.strip().lower() in _TIME_UNITS:
        result["errors"].append(_issue(
            "monod_requires_substrate_axis",
            "Monod requires a substrate concentration axis, not elapsed time.",
        ))
        return result
    if method not in MODEL_SPECS[model]["methods"]:
        result["errors"].append(_issue("unsupported_method", "Unsupported fitting method."))
        return result
    if weighted and method != "raw":
        result["errors"].append(_issue("invalid_weighting", "Weights are supported on raw scale only."))
        return result
    parameter_keys = MODEL_SPECS[model]["parameters"]
    for key, value in fixed.items():
        numeric = _number(value)
        if key not in parameter_keys or numeric is None or (key != "b" and numeric < 0):
            result["errors"].append(_issue("invalid_fixed", f"Invalid fixed parameter: {key}"))
        else:
            fixed[key] = numeric
    if any(fixed.get(key) == 0 for key in {"C0", "qe", "Ks"} & fixed.keys()):
        result["errors"].append(_issue("invalid_fixed", "Fixed C0, qe and Ks must be positive."))
    if model == "adsorption_pso" and fixed.get("k2") == 0 and method == "linearized":
        result["errors"].append(_issue("invalid_fixed", "PSO linearization requires positive k2."))
    if model == "plateau_first" and fixed.get("Cinf", 0) > fixed.get("C0", np.inf):
        result["errors"].append(_issue("invalid_fixed", "Cinf cannot exceed C0."))
    interval = (None, None)
    if x_range is not None:
        if len(x_range) != 2:
            result["errors"].append(_issue("invalid_interval", "Interval needs lower and upper limits."))
        else:
            interval = tuple(x_range)
            if any(v is not None and _number(v) is None for v in interval):
                result["errors"].append(_issue("invalid_interval", "Interval limits must be finite."))
            elif all(v is not None for v in interval) and interval[0] > interval[1]:
                result["errors"].append(_issue("invalid_interval", "Interval lower limit exceeds upper."))
    if result["errors"]:
        return result
    selected: list[int] = []
    for i, row in enumerate(rows):
        x, y, sigma = (_number(row.get(key)) for key in ("x", "y", "sigma"))
        included = bool(row.get("included", True))
        reason = row.get("exclusion_reason") or ""
        if not included and not reason:
            result["errors"].append(_issue("missing_exclusion_reason", f"Row {i+1} has no exclusion reason."))
        if included and x is not None and (
            (interval[0] is not None and x < interval[0])
            or (interval[1] is not None and x > interval[1])
        ):
            included, reason = False, "outside_selected_fit_interval"
        record = {
            "x": x, "y": y, "sigma": sigma, "predicted": None, "residual": None,
            "included": included, "sample_ids": list(row.get("sample_ids") or []),
            "run_id": row.get("run_id"), "exclusion_reason": reason,
            "transformed_x": None, "transformed_y": None, "transformed_predicted": None,
        }
        result["predictions"].append(record)
        if included:
            if x is None or y is None or x < 0 or y < 0:
                result["errors"].append(_issue("invalid_row", f"Row {i+1} requires finite nonnegative x and y."))
            if weighted and (sigma is None or sigma <= 0):
                result["errors"].append(_issue("invalid_sigma", f"Row {i+1} requires a positive measured sigma."))
            selected.append(i)
    n_parameters = len(parameter_keys) - len(fixed)
    result["metrics"].update(n_points=len(selected), n_parameters=n_parameters)
    if len(selected) < max(4, n_parameters + 2):
        result["errors"].append(_issue("insufficient_points", "At least 4 points and p+2 points are required."))
    if result["errors"]:
        return result
    x = np.array([result["predictions"][i]["x"] for i in selected], dtype=np.float64)
    y = np.array([result["predictions"][i]["y"] for i in selected], dtype=np.float64)
    sigma = np.array([result["predictions"][i]["sigma"] for i in selected], dtype=np.float64) if weighted else None
    if np.ptp(x) == 0:
        result["errors"].append(_issue("identical_x", "At least two distinct x values are required."))
        return result
    try:
        objective_y = _transformed(model, x, y, fixed) if method == "linearized" else y
        free, unpack, physical_jac, start, lower, upper = _parameterization(
            model, fixed, _initial(model, x, y)
        )

        def objective(xvalues, *values):
            params = unpack(values)
            if method == "linearized":
                return _transformed_prediction(model, xvalues, params)
            return predict(model, xvalues, params)

        # Keep solver stopping tolerances independent of response units. Scaling
        # both response and supplied sigma leaves the weighted objective and its
        # absolute covariance unchanged; residual scaling cancels in unweighted
        # covariance because curve_fit estimates residual variance in that scale.
        response_scale = max(float(np.max(np.abs(objective_y))), 1e-15)

        def scaled_objective(xvalues, *values):
            return objective(xvalues, *values) / response_scale

        if free:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", OptimizeWarning)
                optimum, covariance = curve_fit(
                    scaled_objective, x, objective_y / response_scale,
                    p0=start, bounds=(lower, upper),
                    sigma=sigma / response_scale if weighted else None,
                    absolute_sigma=weighted, method="trf", x_scale="jac",
                    max_nfev=20000, ftol=1e-11, xtol=1e-11, gtol=1e-11,
                )
            if caught:
                result["warnings"].append(_issue("covariance_warning", str(caught[0].message)))
            jac = physical_jac(optimum)
            physical_covariance = jac @ covariance @ jac.T
        else:
            optimum = np.array([], dtype=np.float64)
            covariance = physical_covariance = np.empty((0, 0))
        params = unpack(optimum)
        fitted = predict(model, x, params)
        if not np.all(np.isfinite(fitted)):
            raise ValueError("Nonfinite predictions from fitted parameters.")
        result["metrics"].update(_metrics(y, fitted))
        objective_fit = objective(x, *optimum)
        if method == "linearized":
            labels = {
                "first_order": "ln(C)", "second_order": "1/C",
                "adsorption_pfo": "ln(qe-qt)", "adsorption_pso": "t/qt",
            }
            result["transformed_metrics"] = {
                **_metrics(objective_y, objective_fit), "transform": labels[model],
            }
        reliable = True
        if free:
            # Use a scaled numerical objective Jacobian: covariance alone hides exact
            # degeneracy when the residual variance is almost zero.
            steps = np.maximum.reduce([
                np.abs(optimum) * 1e-5, np.abs(start) * 1e-7,
                np.full(len(free), 1e-18),
            ])
            jacobian = np.column_stack([
                (objective(x, *(optimum + np.eye(len(free))[j] * steps[j])) - objective_fit)
                / steps[j] for j in range(len(free))
            ])
            if weighted:
                jacobian = jacobian / sigma[:, None]
            scale = np.linalg.norm(jacobian, axis=0)
            normalized = jacobian / np.where(scale > 0, scale, 1.0)
            rank = int(np.linalg.matrix_rank(normalized))
            condition = float(np.linalg.cond(normalized))
            result["diagnostics"] = {
                "jacobian_rank": rank,
                "jacobian_condition": condition if math.isfinite(condition) else None,
            }
            if rank < len(free) or condition > 1e8 or not np.all(np.isfinite(covariance)):
                reliable = False
                result["warnings"].append(_issue("not_identifiable", "Parameters are not reliably identifiable; intervals are withheld."))
            if np.all(np.isfinite(physical_covariance)) and len(free) > 1:
                standard_errors = np.sqrt(np.maximum(np.diag(physical_covariance), 0))
                divisor = np.outer(standard_errors, standard_errors)
                correlation = np.divide(
                    physical_covariance, divisor, out=np.zeros_like(physical_covariance),
                    where=divisor > 0,
                )
                np.fill_diagonal(correlation, 0)
                max_correlation = float(np.max(np.abs(correlation)))
                result["diagnostics"]["max_parameter_correlation"] = max_correlation
                if max_correlation > 0.995:
                    reliable = False
                    result["warnings"].append(_issue("parameter_correlation", "Fitted parameters are strongly correlated; intervals are withheld."))
            bound_tolerance = 1e-7 * np.maximum.reduce([
                np.abs(optimum), np.abs(start), np.full(len(free), 1e-15),
            ])
            bound = np.any(
                (np.isfinite(lower) & (optimum - lower <= bound_tolerance))
                | (np.isfinite(upper) & (upper - optimum <= bound_tolerance))
            )
            if bound:
                reliable = False
                result["warnings"].append(_issue("parameter_at_bound", "A fitted parameter is at its physical bound; symmetric intervals are withheld."))
        if model == "zero_order" and np.any(fitted < 0):
            result["warnings"].append(_issue("negative_prediction", "The zero-order curve predicts negative responses in the fitted interval."))
        if np.ptp(y) == 0:
            reliable = False
            result["warnings"].append(_issue("constant_response", "Original-scale R² is undefined for a constant response; parameter intervals are withheld."))
        units = parameter_units(model, x_unit, y_unit)
        critical = float(norm.ppf(0.975) if weighted else student_t.ppf(0.975, len(x) - len(free)))
        for key in parameter_keys:
            ci = None
            if key in free and reliable:
                variance = float(physical_covariance[free.index(key), free.index(key)])
                if variance >= 0 and math.isfinite(variance):
                    error = critical * math.sqrt(variance)
                    ci = [float(params[key] - error), float(params[key] + error)]
            result["parameters"][key] = {
                "value": float(params[key]), "unit": units[key], "ci95": ci, "fixed": key in fixed,
            }
        for index, row_index in enumerate(selected):
            record = result["predictions"][row_index]
            record["predicted"] = float(fitted[index])
            record["residual"] = float(y[index] - fitted[index])
            if method == "linearized":
                record["transformed_x"] = float(x[index])
                record["transformed_y"] = float(objective_y[index])
                record["transformed_predicted"] = float(objective_fit[index])
        grid = np.linspace(float(np.min(x)), float(np.max(x)), 200, dtype=np.float64)
        result["curve"] = [{"x": float(a), "y": float(b)} for a, b in zip(grid, predict(model, grid, params), strict=True)]
        result["status"] = "warning" if result["warnings"] else "ok"
    except (ValueError, RuntimeError, FloatingPointError, np.linalg.LinAlgError) as exc:
        result["errors"].append(_issue("fit_failed", str(exc)))
    return result


def batch_fit(
    rows: Sequence[Mapping[str, Any]], requests: Sequence[Mapping[str, Any]], **common: Any,
) -> list[dict[str, Any]]:
    """Fit each explicit request independently, preserving request order and failures."""
    return [fit_series(rows, **{**common, **dict(request)}) for request in requests]


def run_project_fits(project: Any) -> list[dict[str, Any]]:
    """Process each series and fit independent runs separately, updating the project.

    Acceptance belongs to an explicit FitRequest. Failed results cannot be accepted.
    Files and immutable input observations are not modified by this function.
    """
    from .analysis_data import process_series, processed_units

    series_by_id = {series.id: series for series in project.series}
    results = []
    for request_index, request in enumerate(project.fit_requests):
        series = series_by_id.get(request.series_id)
        interval = (request.x_min, request.x_max)
        common = {
            "model": request.model, "method": request.method, "fixed": request.fixed,
            "weighted": request.weighted,
            "x_range": interval if any(v is not None for v in interval) else None,
        }
        if series is None:
            result = fit_series([], **common)
            result["errors"] = [_issue("missing_series", "The requested data series does not exist.")]
            result.update(series_id=request.series_id, series_name="", run_id=None,
                          request_index=request_index, request_id=str(request_index), accepted=False)
            results.append(result)
            continue
        try:
            processed = process_series(series)
            x_unit, y_unit = processed_units(series)
            groups: dict[str, list[dict]] = defaultdict(list)
            for row in processed:
                groups[row.get("run_id") or "run-1"].append(row)
            if not groups:
                groups["run-1"] = []
            family = "biological" if series.kind == "monod" else series.kind
            domain_issue = None
            if series.kind == "adsorption" and not (
                series.observable == "qt" or series.processing.compute_qt
            ):
                domain_issue = _issue(
                    "adsorption_requires_qt",
                    "Adsorption models require measured qt or a confirmed concentration-to-qt mass balance.",
                )
            if series.kind == "monod":
                if series.observable not in {
                    "growth_rate", "specific_uptake_rate", "volumetric_rate",
                }:
                    domain_issue = _issue(
                        "monod_requires_rate",
                        "Monod requires substrate concentration versus a biological rate observable.",
                    )
                elif x_unit.strip().lower() in _TIME_UNITS:
                    domain_issue = _issue(
                        "monod_requires_substrate_axis",
                        "Monod requires a substrate concentration axis, not elapsed time.",
                    )
            for run_id, rows in groups.items():
                if domain_issue:
                    result = fit_series([], **common, x_unit=x_unit, y_unit=y_unit)
                    result["errors"] = [domain_issue]
                    result["predictions"] = [{**row, "predicted": None, "residual": None}
                                             for row in rows]
                    result["metrics"] = {
                        "n_points": sum(bool(row.get("included", True)) for row in rows),
                        "n_parameters": len(MODEL_SPECS.get(request.model, {}).get(
                            "parameters", [])) - len(request.fixed),
                    }
                else:
                    result = fit_series(rows, **common, x_unit=x_unit, y_unit=y_unit)
                if request.model not in available_models(family):
                    result["status"] = "failed"
                    result["errors"].append(_issue("model_family_mismatch", "The selected model does not match this series type."))
                    result["parameters"] = {}
                    result["curve"] = []
                result.update(
                    series_id=series.id, series_name=series.name, run_id=run_id,
                    request_index=request_index,
                    request_id=f"{request_index}:{run_id}",
                    accepted=bool(request.accepted and result["status"] != "failed"),
                )
                results.append(result)
        except ValueError as exc:
            result = fit_series([], **common)
            result["errors"] = [_issue("processing_failed", str(exc))]
            result.update(series_id=series.id, series_name=series.name, run_id=None,
                          request_index=request_index, request_id=str(request_index), accepted=False)
            results.append(result)
    project.fit_results = results
    return results
