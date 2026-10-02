"""Researcher workflows through the actual Streamlit interface."""
import io
import json
import math
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

from envevidence.analysis_data import AnalysisStore

ENTRY = str(Path(__file__).parents[1] / "app.py")


def find(elements, label):
    return next(element for element in elements if element.label == label)


def click(app, label):
    find(app.button, label).click().run()
    assert not app.exception


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVEVIDENCE_DATA_DIR", str(tmp_path))
    return AppTest.from_file(ENTRY, default_timeout=60).run()


def saved(app, tmp_path):
    return AnalysisStore(tmp_path).load(app.session_state.analysis_project_id)


def load_demo(app):
    app.button(key="analysis_demo").click().run()
    assert not app.exception


def fit_first(app, tmp_path):
    project = saved(app, tmp_path)
    app.multiselect(key=f"models_{project.series[0].id}").set_value(["first_order"])
    app.button(key="analysis_fit").click().run()
    assert not app.exception
    project = saved(app, tmp_path)
    assert project.fit_results[0]["status"] != "failed"
    return project


def create_manual(app, text=None, kind="decay", observable=None):
    click(app, "Create analysis project")
    if kind != "decay":
        app.selectbox(key="input_kind").select(kind).run()
    if observable:
        app.selectbox(key=f"input_observable_{kind}").select(observable).run()
    if text:
        app.text_area(key="analysis_paste").set_value(text).run()
    app.button(key="analysis_import").click().run()
    assert not app.exception


def test_demo_fit_accept_export_keeps_records_and_reload(app, tmp_path):
    load_demo(app)
    project = fit_first(app, tmp_path)
    assert project.fit_results[0]["parameters"]["k1"]["value"] == pytest.approx(0.12)
    app.multiselect(key=f"accepted_{project.id}").set_value([0])
    app.checkbox(key="analysis_confirm").check().run()
    app.button(key="analysis_export").click().run()
    assert not app.exception
    output = Path(app.session_state.analysis_export_path)
    assert output.exists()
    with zipfile.ZipFile(output) as archive:
        assert {"analysis_config.json", "processed.csv", "parameters.csv", "analysis.xlsx",
                "plots/curve.png", "plots/residual.png", "manifest.json"} <= set(archive.namelist())
        snapshot = json.loads(archive.read("project_snapshot.json"))
        assert snapshot["fit_results"][0]["accepted"]
        assert len(snapshot["series"][0]["observations"]) == 7
    restored = AppTest.from_file(ENTRY, default_timeout=60).run()
    restored.button(key="analysis_open").click().run()
    assert not restored.exception
    assert saved(restored, tmp_path).fit_results[0]["accepted"]


def test_manual_paste_mapping_and_duplicate_import_preserve_original(app, tmp_path):
    click(app, "Create analysis project")
    text = "elapsed,concentration,vial,batch\n0,10,A,R1\n2,8,B,R1\n4,6,C,R1\n6,4,D,R1\n"
    app.text_area(key="analysis_paste").set_value(text).run()
    for key, value in {"x": "elapsed", "y": "concentration", "sample_id": "vial", "run_id": "batch"}.items():
        app.selectbox(key=f"map_{key}").select(value)
    app.button(key="analysis_import").click().run()
    assert not app.exception
    project = saved(app, tmp_path)
    assert project.series[0].observations[1].sample_id == "B"
    assert project.series[0].observations[1].y == 8
    assert project.series[0].conditions["column_mapping"]["x"] == "elapsed"
    original = AnalysisStore(tmp_path).read_source(project, project.sources[0])
    app.button(key="analysis_import").click().run()
    assert not app.exception
    assert len(saved(app, tmp_path).series) == 1
    assert AnalysisStore(tmp_path).read_source(project, project.sources[0]) == original


def test_generic_csv_upload_preview_mapping_and_hash(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVEVIDENCE_DATA_DIR", str(tmp_path))
    original_uploader = st.file_uploader

    class Upload(io.BytesIO):
        name = "instrument-values.csv"

    data = b"minutes,TOC,sample\n0,5,A\n2,4,B\n4,3,C\n6,2,D\n"

    def upload(*args, **kwargs):
        return Upload(data) if kwargs.get("key") == "analysis_upload" else original_uploader(*args, **kwargs)

    monkeypatch.setattr(st, "file_uploader", upload)
    app = AppTest.from_file(ENTRY, default_timeout=60).run()
    click(app, "Create analysis project")
    app.radio(key="analysis_input").set_value("file").run()
    app.selectbox(key="input_observable_decay").select("TOC").run()
    for key, value in {"x": "minutes", "y": "TOC", "sample_id": "sample"}.items():
        app.selectbox(key=f"map_{key}").select(value)
    app.button(key="analysis_import").click().run()
    assert not app.exception
    project = saved(app, tmp_path)
    assert project.series[0].observable == "TOC"
    assert project.sources[0].name == Upload.name
    assert AnalysisStore(tmp_path).read_source(project, project.sources[0]) == data


def test_data_editor_revision_invalidates_fits_and_preserves_source(app, tmp_path):
    load_demo(app)
    project = fit_first(app, tmp_path)
    series = project.series[0]
    original = AnalysisStore(tmp_path).read_source(project, project.sources[0])
    app.session_state[f"observations_{series.id}"] = {
        "edited_rows": {0: {"y": 9.75}}, "added_rows": [], "deleted_rows": [],
    }
    app.text_input(key=f"revision_reason_{series.id}").set_value("Corrected assay transcription")
    app.button(key="analysis_revision").click().run()
    assert not app.exception
    revised = saved(app, tmp_path)
    assert revised.series[0].observations[0].y == 9.75
    assert revised.fit_results == []
    assert AnalysisStore(tmp_path).read_source(revised, revised.sources[0]) == original
    history = next(h for h in revised.history if h["action"] == "revise_observation")
    assert history["before"]["y"] == 10


def test_processing_changes_invalidate_fits_and_survive_restart(app, tmp_path):
    load_demo(app)
    project = fit_first(app, tmp_path)
    find(app.number_input, "Blank (measured units)").set_value(0.5)
    find(app.number_input, "Dilution factor").set_value(2)
    click(app, "Save processing rules")
    changed = saved(app, tmp_path)
    assert changed.fit_results == []
    assert changed.series[0].processing.blank == 0.5
    assert changed.series[0].observations == project.series[0].observations
    assert any(h["action"] == "invalidate_fits" for h in changed.history)
    processing_history = next(h for h in changed.history if h["action"] == "processing_rules")
    assert processing_history["before"]["blank"] == 0
    assert processing_history["after"]["blank"] == 0.5
    restored = AppTest.from_file(ENTRY, default_timeout=60).run()
    restored.button(key="analysis_open").click().run()
    assert find(restored.number_input, "Blank (measured units)").value == 0.5
    assert find(restored.number_input, "Dilution factor").value == 2


def test_reaction_conditions_name_and_values_persist_on_selected_series(app, tmp_path):
    load_demo(app)
    original = saved(app, tmp_path).series[0].observations
    next(e for e in app.text_input if e.label == "Series name" and e.key != "input_name").set_value("My treatment")
    find(app.text_input, "Compound / substrate").set_value("Model A")
    find(app.text_input, "Reactor liquid volume (with unit)").set_value("250 mL")
    click(app, "Save conditions")
    changed = saved(app, tmp_path)
    assert changed.series[0].name == "My treatment"
    assert changed.series[0].conditions["pollutant"] == "Model A"
    assert changed.series[0].conditions["reactor_volume"] == "250 mL"
    assert changed.series[0].observations == original


def test_empty_conditions_name_cannot_corrupt_saved_project(app, tmp_path):
    load_demo(app)
    original = saved(app, tmp_path)
    next(e for e in app.text_input if e.label == "Series name" and e.key != "input_name").set_value(" ")
    click(app, "Save conditions")
    assert app.error
    assert saved(app, tmp_path).series[0].name == original.series[0].name


def test_sop_template_apply_restores_settings_without_replacing_data(app, tmp_path):
    load_demo(app)
    find(app.number_input, "Dilution factor").set_value(3)
    click(app, "Save processing rules")
    find(app.number_input, "DPI").set_value(600)
    click(app, "Save plot style")
    app.text_input(key="analysis_template_name").set_value("My SOP")
    app.button(key="analysis_template_save").click().run()
    assert not app.exception
    app.selectbox(key="analysis_template_select").select(AnalysisStore(tmp_path).templates()[0]).run()
    original_observations = saved(app, tmp_path).series[0].observations
    find(app.number_input, "Dilution factor").set_value(1)
    click(app, "Save processing rules")
    find(app.number_input, "DPI").set_value(300)
    click(app, "Save plot style")
    click(app, "Apply SOP to matching series")
    project = saved(app, tmp_path)
    assert project.plot.dpi == 600
    assert project.series[0].processing.dilution_factor == 3
    assert project.series[0].observations == original_observations
    template = AnalysisStore(tmp_path).templates()[0]
    assert template["name"] == "My SOP"
    assert "observations" not in template["payload"]["series"][0]
    restored = AppTest.from_file(ENTRY, default_timeout=60).run()
    restored.button(key="analysis_open").click().run()
    assert saved(restored, tmp_path).series[0].processing.dilution_factor == 3
    assert saved(restored, tmp_path).plot.dpi == 600


def test_sop_unit_mismatch_keeps_project_and_blocks_wrong_import(app, tmp_path):
    load_demo(app)
    find(app.number_input, "DPI").set_value(600)
    click(app, "Save plot style")
    app.button(key="analysis_template_save").click().run()
    template = AnalysisStore(tmp_path).templates()[0]
    app.button(key="analysis_new").click().run()
    click(app, "Create analysis project")
    app.text_input(key="input_unit_concentration").set_value("ug/L").run()
    app.selectbox(key="import_sop").select(template).run()
    assert app.button(key="analysis_import").disabled
    assert app.warning
    app.selectbox(key="import_sop").select(None).run()
    app.button(key="analysis_import").click().run()
    assert not app.exception
    project = saved(app, tmp_path)
    assert project.series[0].y_unit == "ug/L"
    before = project.model_dump()
    app.selectbox(key="analysis_template_select").select(template).run()
    click(app, "Apply SOP to matching series")
    assert app.warning
    assert saved(app, tmp_path).model_dump() == before


def test_sop_import_reuses_mapping_processing_and_plot(app, tmp_path):
    click(app, "Create analysis project")
    text = "elapsed,concentration,sample\n0,10,A\n2,8,B\n4,6,C\n6,4,D\n"
    app.text_area(key="analysis_paste").set_value(text).run()
    for key, value in {"x": "elapsed", "y": "concentration", "sample_id": "sample"}.items():
        app.selectbox(key=f"map_{key}").select(value)
    app.button(key="analysis_import").click().run()
    find(app.number_input, "Dilution factor").set_value(2)
    click(app, "Save processing rules")
    find(app.number_input, "DPI").set_value(600)
    click(app, "Save plot style")
    app.button(key="analysis_template_save").click().run()
    template = AnalysisStore(tmp_path).templates()[0]
    app.button(key="analysis_new").click().run()
    click(app, "Create analysis project")
    app.text_area(key="analysis_paste").set_value(text).run()
    app.selectbox(key="import_sop").select(template).run()
    assert app.selectbox(key="map_x").value == "elapsed"
    assert app.selectbox(key="map_y").value == "concentration"
    app.button(key="analysis_import").click().run()
    assert not app.exception
    project = saved(app, tmp_path)
    assert project.series[0].processing.dilution_factor == 2
    assert project.plot.dpi == 600
    assert project.series[0].observations[0].y == 10


@pytest.mark.parametrize("locale,header", [("en", "Experiment analysis"), ("zh", "实验分析")])
def test_bilingual_navigation_does_not_translate_research_data(app, tmp_path, locale, header):
    load_demo(app)
    original = saved(app, tmp_path).series[0].observations
    app.selectbox(key="locale").select(locale).run()
    assert not app.exception
    assert app.header[0].value == header
    assert saved(app, tmp_path).series[0].observations == original
    restored = AppTest.from_file(ENTRY, default_timeout=60).run()
    assert restored.header[0].value == header


def test_adsorption_qt_requires_confirmed_mass_balance(app, tmp_path):
    create_manual(app, kind="adsorption", observable="concentration")
    find(app.checkbox, "Calculate qt from concentrations").check()
    click(app, "Save processing rules")
    assert any("mass balance" in e.value for e in app.error)
    assert not saved(app, tmp_path).series[0].processing.compute_qt
    find(app.checkbox, "Constant-volume / separate-bottle mass balance applies; no other removal process").check()
    click(app, "Save processing rules")
    assert saved(app, tmp_path).series[0].processing.compute_qt
    assert find(app.number_input, "Reactor liquid volume (L)")
    assert find(app.number_input, "Adsorbent dry mass (g)")


def test_monod_template_uses_substrate_rate_axis_and_disables_timezero(app, tmp_path):
    concentrations = [0, 1, 2, 4, 8, 16, 32]
    text = "x,y\n" + "\n".join(f"{x},{0.6*x/(3+x)}" for x in concentrations)
    create_manual(app, text=text, kind="monod", observable="growth_rate")
    assert find(app.number_input, "Time zero offset (input time unit)").disabled
    assert app.text_input(key="input_xunit_monod").value == "mg/L"
    project = saved(app, tmp_path)
    assert project.series[0].y_unit == "1/h"
    app.button(key="analysis_fit").click().run()
    assert not app.exception
    result = saved(app, tmp_path).fit_results[0]
    assert result["parameters"]["rate_max"]["value"] == pytest.approx(0.6)
    assert result["parameters"]["Ks"]["value"] == pytest.approx(3)


def test_tiff_dpi_axes_style_persist_and_respect_physical_dimensions(app, tmp_path):
    load_demo(app)
    find(app.selectbox, "Format").select("tiff")
    find(app.number_input, "DPI").set_value(600)
    find(app.number_input, "Width (mm)").set_value(120)
    find(app.number_input, "Height (mm)").set_value(80)
    find(app.text_input, "X axis label (empty = automatic)").set_value("Reaction time (min)")
    find(app.text_input, "Y axis label (empty = automatic)").set_value("TOC (mg C/L)")
    find(app.checkbox, "Set axis ranges").check()
    for label, value in [("X minimum", 0), ("X maximum", 20), ("Y minimum", 0), ("Y maximum", 12)]:
        find(app.number_input, label).set_value(value)
    click(app, "Save plot style")
    project = saved(app, tmp_path)
    assert project.plot.formats == ["tiff"]
    assert project.plot.dpi == 600
    assert (project.plot.width_mm, project.plot.height_mm) == (120, 80)
    assert project.plot.x_max == 20
    assert project.plot.y_label == "TOC (mg C/L)"
    restored = AppTest.from_file(ENTRY, default_timeout=60).run()
    restored.button(key="analysis_open").click().run()
    assert find(restored.selectbox, "Format").value == "tiff"
    assert find(restored.number_input, "DPI").value == 600


def test_remove_measurement_requires_reason_and_keeps_audit(app, tmp_path):
    load_demo(app)
    original = saved(app, tmp_path)
    app.button(key="analysis_remove").click().run()
    assert not app.exception
    assert app.error
    assert len(saved(app, tmp_path).series[0].observations) == 7
    app.text_input(key="analysis_remove_reason").set_value("Duplicate vial entry")
    app.button(key="analysis_remove").click().run()
    assert not app.exception
    project = saved(app, tmp_path)
    assert len(project.series[0].observations) == 6
    assert any(h["action"] == "remove_observation" for h in project.history)
    assert AnalysisStore(tmp_path).read_source(project, project.sources[0]) == AnalysisStore(tmp_path).read_source(original, original.sources[0])


def test_invalid_processing_unit_keeps_previous_saved_configuration(app, tmp_path):
    load_demo(app)
    find(app.text_input, "Processed response unit (empty = unchanged)").set_value("mmol/L")
    click(app, "Save processing rules")
    assert any("Unsupported unit conversion" in e.value for e in app.error)
    assert saved(app, tmp_path).series[0].processing.target_y_unit == ""


def test_cli_replays_export_with_parameters_and_accepted_selection(app, tmp_path):
    load_demo(app)
    project = fit_first(app, tmp_path)
    app.multiselect(key=f"accepted_{project.id}").set_value([0])
    app.checkbox(key="analysis_confirm").check().run()
    app.button(key="analysis_export").click().run()
    assert not app.exception
    extracted = tmp_path / "extracted"
    with zipfile.ZipFile(app.session_state.analysis_export_path) as archive:
        archive.extractall(extracted)
    output = tmp_path / "rerun"
    environment = {**os.environ, "PYTHONUTF8": "1"}
    result = subprocess.run([sys.executable, "-m", "envevidence", "analyze", "--config",
                             str(extracted / "analysis_config.json"), "--output", str(output)],
                            cwd=Path(ENTRY).parent, env=environment, capture_output=True,
                            text=True, encoding="utf-8", timeout=60)
    assert result.returncode == 0, result.stderr
    restored = AnalysisStore(output).load(project.id)
    assert restored.fit_results[0]["accepted"]
    for parameter, entry in project.fit_results[0]["parameters"].items():
        assert math.isclose(restored.fit_results[0]["parameters"][parameter]["value"],
                            entry["value"], rel_tol=1e-10, abs_tol=1e-12)
    assert list(output.glob("*.zip"))
