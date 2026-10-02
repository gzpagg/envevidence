from __future__ import annotations

import json

import numpy as np
import pytest

from envevidence.analysis_fitting import (
    available_models,
    batch_fit,
    fit_series,
    predict,
    run_project_fits,
)


def rows_for(model, parameters, x=None):
    if x is None:
        x = np.linspace(0, 40, 15)
    y = predict(model, x, parameters)
    return [
        {"x": float(a), "y": float(b), "sample_ids": [f"sample-{i}"], "run_id": "run-A"}
        for i, (a, b) in enumerate(zip(x, y, strict=True))
    ]


@pytest.mark.parametrize(
    ("model", "parameters"),
    [
        ("zero_order", {"C0": 10.0, "k0": 0.15}),
        ("first_order", {"C0": 10.0, "k1": 0.05}),
        ("second_order", {"C0": 10.0, "k2": 0.01}),
        ("plateau_first", {"C0": 10.0, "Cinf": 2.0, "k1": 0.08}),
        ("adsorption_pfo", {"qe": 8.0, "k1": 0.08}),
        ("adsorption_pso", {"qe": 8.0, "k2": 0.02}),
        ("intraparticle", {"kid": 1.4, "b": 0.6}),
        ("monod", {"rate_max": 5.0, "Ks": 12.0}),
    ],
)
def test_raw_recovers_known_parameters(model, parameters):
    result = fit_series(rows_for(model, parameters), model,
                        x_unit="mg/L" if model == "monod" else "min")
    assert not result["errors"]
    assert result["status"] == "ok"
    for name, expected in parameters.items():
        assert result["parameters"][name]["value"] == pytest.approx(expected, rel=2e-5)
    assert result["metrics"]["rmse"] < 1e-7
    assert result["metrics"]["r2"] == pytest.approx(1)
    assert len(result["curve"]) == 200
    assert all(row["residual"] is not None for row in result["predictions"])
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize(
    ("model", "parameters", "fixed"),
    [
        ("first_order", {"C0": 10.0, "k1": 0.05}, {}),
        ("second_order", {"C0": 10.0, "k2": 0.01}, {}),
        ("adsorption_pfo", {"qe": 8.0, "k1": 0.08}, {"qe": 8.0}),
        ("adsorption_pso", {"qe": 8.0, "k2": 0.02}, {}),
    ],
)
def test_linearization_recovers_parameters_and_separate_metrics(model, parameters, fixed):
    data = rows_for(model, parameters, x=np.linspace(1, 40, 15))
    result = fit_series(data, model, method="linearized", fixed=fixed)
    assert not result["errors"]
    for name, expected in parameters.items():
        assert result["parameters"][name]["value"] == pytest.approx(expected, rel=2e-5)
    assert result["transformed_metrics"]["r2"] == pytest.approx(1)
    assert result["metrics"]["r2"] == pytest.approx(1)
    assert all(row["transformed_y"] is not None for row in result["predictions"])


def test_original_metrics_match_independent_calculation_after_linearization():
    data = rows_for("first_order", {"C0": 10, "k1": 0.05})
    data[3]["y"] *= 1.25
    result = fit_series(data, "first_order", method="linearized")
    x = np.array([r["x"] for r in data])
    y = np.array([r["y"] for r in data])
    slope, intercept = np.polyfit(x, np.log(y), 1)
    predicted = np.exp(intercept + slope * x)
    assert result["parameters"]["k1"]["value"] == pytest.approx(-slope, rel=1e-6)
    rmse = np.sqrt(np.mean((y - predicted) ** 2))
    assert result["metrics"]["rmse"] == pytest.approx(rmse, rel=1e-6)
    assert result["metrics"]["r2"] != result["transformed_metrics"]["r2"]


def test_explicit_fixed_parameters_are_not_counted_as_free():
    data = rows_for("plateau_first", {"C0": 10, "Cinf": 2, "k1": 0.08})[:4]
    result = fit_series(data, "plateau_first", fixed={"C0": 10})
    assert not result["errors"]
    assert result["metrics"]["n_parameters"] == 2
    assert result["parameters"]["C0"] == {
        "value": 10.0, "unit": "mg/L", "ci95": None, "fixed": True,
    }
    assert result["parameters"]["Cinf"]["value"] == pytest.approx(2, rel=1e-5)
    assert fit_series(data, "plateau_first")["errors"][0]["code"] == "insufficient_points"


def test_weighted_fit_matches_direct_weighted_least_squares():
    data = rows_for("zero_order", {"C0": 10, "k0": 0.15})
    for i, row in enumerate(data):
        row["sigma"] = 0.1 if i < 8 else 5.0
    data[-1]["y"] += 3
    result = fit_series(data, "zero_order", weighted=True)
    x = np.array([r["x"] for r in data])
    y = np.array([r["y"] for r in data])
    sigma = np.array([r["sigma"] for r in data])
    expected = np.linalg.lstsq(np.column_stack([np.ones(len(x)), -x]) / sigma[:, None], y / sigma, rcond=None)[0]
    assert result["parameters"]["C0"]["value"] == pytest.approx(expected[0], rel=1e-6)
    assert result["parameters"]["k0"]["value"] == pytest.approx(expected[1], rel=1e-6)
    assert result["parameters"]["k0"]["ci95"] is not None
    data[0]["sigma"] = 0
    assert fit_series(data, "zero_order", weighted=True)["errors"][0]["code"] == "invalid_sigma"
    assert fit_series(data, "first_order", method="linearized", weighted=True)["errors"][0]["code"] == "invalid_weighting"


def test_invalid_values_cannot_be_silently_dropped():
    data = rows_for("first_order", {"C0": 10, "k1": 0.05})
    data[0]["y"] = 0
    result = fit_series(data, "first_order", method="linearized")
    assert result["status"] == "failed"
    assert len(result["predictions"]) == len(data)
    assert result["errors"][0]["code"] == "fit_failed"
    data[0].update(included=False, exclusion_reason="below_quantification_limit")
    result = fit_series(data, "first_order", method="linearized")
    assert not result["errors"]
    assert result["predictions"][0]["predicted"] is None
    assert result["metrics"]["n_points"] == len(data) - 1
    data[0]["exclusion_reason"] = ""
    assert fit_series(data, "first_order")["errors"][0]["code"] == "missing_exclusion_reason"


def test_missing_rows_and_same_x_have_explicit_failures():
    data = rows_for("first_order", {"C0": 10, "k1": 0.05})
    data[1]["y"] = None
    assert fit_series(data, "first_order")["errors"][0]["code"] == "invalid_row"
    for row in data:
        row.update(x=2, y=3)
    assert fit_series(data, "first_order")["errors"][0]["code"] == "identical_x"


def test_adsorption_linearization_requires_explicit_equilibrium_and_positive_pso_time():
    pfo = rows_for("adsorption_pfo", {"qe": 8, "k1": 0.08})
    result = fit_series(pfo, "adsorption_pfo", method="linearized")
    assert "fixed qe" in result["errors"][0]["message"]
    result = fit_series(pfo, "adsorption_pfo", method="linearized", fixed={"qe": 2})
    assert "less than fixed qe" in result["errors"][0]["message"]
    pso = rows_for("adsorption_pso", {"qe": 8, "k2": 0.02})
    assert fit_series(pso, "adsorption_pso", method="linearized")["status"] == "failed"
    result = fit_series(pso, "adsorption_pso", method="linearized", x_range=(1, 40))
    assert not result["errors"]
    assert result["predictions"][0]["exclusion_reason"] == "outside_selected_fit_interval"


def test_units_bound_diagnostics_and_constant_response():
    data = rows_for("first_order", {"C0": 10, "k1": 0})
    result = fit_series(data, "first_order")
    assert result["metrics"]["r2"] is None
    assert "constant_response" in {issue["code"] for issue in result["warnings"]}
    assert result["parameters"]["k1"]["ci95"] is None
    monod = fit_series(rows_for("monod", {"rate_max": 0.5, "Ks": 12}), "monod", x_unit="mg COD/L", y_unit="1/day")
    assert monod["parameters"]["Ks"]["unit"] == "mg COD/L"
    assert monod["parameters"]["rate_max"]["unit"] == "1/day"
    second = fit_series(rows_for("second_order", {"C0": 1, "k2": 0.1}), "second_order", y_unit="C/C0")
    assert second["parameters"]["k2"]["unit"] == "1/(C/C0*min)"


def test_models_batch_order_and_physical_plateau_validation():
    assert "monod" in available_models("biological")
    assert "first_order" in available_models("biological_decay")
    data = rows_for("first_order", {"C0": 10, "k1": 0.05})
    results = batch_fit(data, [{"model": "first_order"}, {"model": "invalid"}])
    assert results[0]["status"] == "ok"
    assert results[1]["errors"][0]["code"] == "unknown_model"
    assert fit_series(data, "plateau_first", fixed={"C0": 1, "Cinf": 2})["errors"][0]["code"] == "invalid_fixed"


def test_rank_deficient_parameters_withhold_intervals():
    data = [{"x": float(x), "y": 0.0} for x in np.linspace(0, 40, 15)]
    result = fit_series(data, "adsorption_pfo")
    assert result["status"] == "warning"
    assert any(issue["code"] in {"not_identifiable", "parameter_at_bound", "constant_response"} for issue in result["warnings"])
    assert all(p["ci95"] is None for p in result["parameters"].values())
    json.dumps(result, allow_nan=False)


def test_project_fits_never_pool_independent_runs():
    from envevidence.analysis_data import AnalysisProject, FitRequest, Observation, Series

    series = Series(name="COD", observable="COD")
    for run_id, k in (("A", 0.02), ("B", 0.1)):
        series.observations.extend(
            Observation(x=row["x"], y=row["y"], run_id=run_id)
            for row in rows_for("first_order", {"C0": 10, "k1": k})
        )
    project = AnalysisProject(name="Two reactors", series=[series], fit_requests=[
        FitRequest(series_id=series.id, model="first_order", accepted=True),
    ])
    results = run_project_fits(project)
    assert project.fit_results is results
    assert len(results) == 2
    assert {fit["run_id"] for fit in results} == {"A", "B"}
    assert results[0]["parameters"]["k1"]["value"] == pytest.approx(0.02)
    assert results[1]["parameters"]["k1"]["value"] == pytest.approx(0.1)
    assert all(fit["accepted"] for fit in results)
    assert all(fit["metrics"]["n_points"] == 15 for fit in results)


def test_project_reports_missing_series_and_model_family_mismatch():
    from envevidence.analysis_data import AnalysisProject, FitRequest, Observation, Series

    series = Series(name="COD", observations=[
        Observation(x=row["x"], y=row["y"])
        for row in rows_for("first_order", {"C0": 10, "k1": 0.05})
    ])
    project = AnalysisProject(name="Validation", series=[series], fit_requests=[
        FitRequest(series_id="deleted", model="first_order", accepted=True),
        FitRequest(series_id=series.id, model="monod", accepted=True),
    ])
    results = run_project_fits(project)
    assert results[0]["errors"][0]["code"] == "missing_series"
    assert "model_family_mismatch" in {i["code"] for i in results[1]["errors"]}
    assert all(not fit["accepted"] for fit in results)


def test_nonconvergent_fit_has_no_parameters_or_predictions(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("Maximum evaluations exceeded")

    monkeypatch.setattr("envevidence.analysis_fitting.curve_fit", fail)
    data = rows_for("first_order", {"C0": 10, "k1": 0.05})
    result = fit_series(data, "first_order")
    assert result["status"] == "failed"
    assert result["parameters"] == {}
    assert result["curve"] == []
    assert result["errors"][0]["code"] == "fit_failed"
    assert all(row["predicted"] is None for row in result["predictions"])


def test_weakly_saturated_monod_withholds_false_confidence():
    expected = {"rate_max": 5.0, "Ks": 1e6}
    data = rows_for("monod", expected, x=np.linspace(1, 40, 15))
    result = fit_series(data, "monod", x_unit="mg/L", y_unit="1/h")
    assert result["status"] == "warning"
    assert result["metrics"]["rmse"] < 1e-12
    for name, value in expected.items():
        assert result["parameters"][name]["value"] == pytest.approx(value, rel=1e-4)
        assert result["parameters"][name]["ci95"] is None
    assert result["diagnostics"]["max_parameter_correlation"] > 0.995


def test_small_response_and_slow_rates_are_not_false_bound_hits():
    result = fit_series(
        rows_for("monod", {"rate_max": 5e-8, "Ks": 12}), "monod",
        x_unit="mg/L", y_unit="1/h",
    )
    assert result["status"] == "ok"
    assert result["parameters"]["rate_max"]["value"] == pytest.approx(5e-8, rel=1e-5)
    assert result["parameters"]["Ks"]["value"] == pytest.approx(12, rel=1e-5)
    result = fit_series(
        rows_for("first_order", {"C0": 10, "k1": 5e-9}, x=np.linspace(0, 4e8, 15)),
        "first_order",
    )
    assert result["status"] == "ok"
    assert result["parameters"]["k1"]["value"] == pytest.approx(5e-9, rel=1e-5)
    assert result["parameters"]["k1"]["ci95"] is not None


def test_scaled_weighted_covariance_matches_independent_matrix_calculation():
    data = rows_for("zero_order", {"C0": 1e-6, "k0": 1e-8})
    for i, row in enumerate(data):
        row["sigma"] = 2e-8 if i < 8 else 8e-8
    data[-1]["y"] += 1e-8
    result = fit_series(data, "zero_order", weighted=True)
    x = np.array([row["x"] for row in data])
    sigma = np.array([row["sigma"] for row in data])
    design = np.column_stack([np.ones(len(x)), -x]) / sigma[:, None]
    covariance = np.linalg.inv(design.T @ design)
    for i, key in enumerate(("C0", "k0")):
        low, high = result["parameters"][key]["ci95"]
        assert (high - low) / 2 == pytest.approx(1.959963984540054 * np.sqrt(covariance[i, i]), rel=1e-5)


def test_fixed_qe_pso_linearization_retains_physical_rate_units():
    expected = {"qe": 8.0, "k2": 0.02}
    result = fit_series(
        rows_for("adsorption_pso", expected, x=np.linspace(1, 40, 15)),
        "adsorption_pso", method="linearized", fixed={"qe": 8}, y_unit="mg/g",
    )
    assert result["status"] == "ok"
    assert result["parameters"]["qe"]["fixed"]
    assert result["parameters"]["k2"]["value"] == pytest.approx(0.02)
    assert result["parameters"]["k2"]["unit"] == "1/(mg/g*min)"
    assert result["metrics"]["n_parameters"] == 1


def test_adsorption_concentrations_require_qt_conversion_without_mutating_inputs():
    from envevidence.analysis_data import AnalysisProject, FitRequest, Observation, Series

    series = Series(name="Residual concentration", kind="adsorption", observable="concentration",
                    observations=[Observation(x=row["x"], y=row["y"])
                                  for row in rows_for("first_order", {"C0": 10, "k1": 0.05})])
    project = AnalysisProject(name="Adsorption", series=[series], fit_requests=[
        FitRequest(series_id=series.id, model="adsorption_pfo", accepted=True),
    ])
    original = series.model_dump()
    result = run_project_fits(project)[0]
    assert result["status"] == "failed"
    assert result["errors"][0]["code"] == "adsorption_requires_qt"
    assert result["parameters"] == {}
    assert len(result["predictions"]) == len(series.observations)
    assert not result["accepted"]
    assert series.model_dump() == original


def test_confirmed_adsorption_mass_balance_feeds_capacity_to_fit():
    from envevidence.analysis_data import (
        AnalysisProject,
        FitRequest,
        Observation,
        ProcessingConfig,
        Series,
    )

    expected = {"qe": 8.0, "k1": 0.08}
    rows = rows_for("adsorption_pfo", expected)
    series = Series(
        name="Mass balance", kind="adsorption", observable="concentration", y_unit="mg/L",
        observations=[Observation(x=row["x"], y=10 - row["y"]) for row in rows],
        processing=ProcessingConfig(compute_qt=True, adsorption_c0=10,
                                    reactor_volume_l=0.1, adsorbent_mass_g=0.1,
                                    mass_balance_confirmed=True),
    )
    project = AnalysisProject(name="Adsorption", series=[series], fit_requests=[
        FitRequest(series_id=series.id, model="adsorption_pfo"),
    ])
    result = run_project_fits(project)[0]
    assert result["status"] == "ok"
    assert result["y_unit"] == "mg/g"
    assert result["parameters"]["qe"]["value"] == pytest.approx(8)
    assert result["parameters"]["k1"]["value"] == pytest.approx(0.08)


@pytest.mark.parametrize("x_unit", ["s", "min", "h", "d", "days"])
def test_monod_rejects_time_axis_and_non_rate_observables(x_unit):
    from envevidence.analysis_data import AnalysisProject, FitRequest, Observation, Series

    series = Series(name="Biology", kind="monod", observable="growth_rate", x_unit=x_unit,
                    y_unit="1/h", observations=[Observation(x=row["x"], y=row["y"])
                                                for row in rows_for("monod", {"rate_max": 5, "Ks": 12})])
    project = AnalysisProject(name="Biology", series=[series], fit_requests=[
        FitRequest(series_id=series.id, model="monod", accepted=True),
    ])
    result = run_project_fits(project)[0]
    assert result["status"] == "failed"
    assert result["errors"][0]["code"] == "monod_requires_substrate_axis"
    assert not result["accepted"]
    series.x_unit = "mg/L"
    series.observable = "COD"
    result = run_project_fits(project)[0]
    assert result["errors"][0]["code"] == "monod_requires_rate"


def test_monod_kernel_requires_explicit_substrate_unit():
    rows = rows_for("monod", {"rate_max": 5.0, "Ks": 12.0})
    result = fit_series(rows, "monod")
    assert result["status"] == "failed"
    assert result["errors"][0]["code"] == "monod_requires_substrate_axis"
    assert result["parameters"] == {}
    assert fit_series(rows, "monod", x_unit="mg/L", y_unit="1/h")["status"] == "ok"
