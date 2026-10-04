"""EnvBench ZIPs remain immutable evidence; desktop import never executes media or timers."""
import hashlib
import io
import json
import zipfile

import pytest

from envevidence.analysis_data import AnalysisProject, AnalysisStore, import_mobile

PHOTO = f"photos/{'c' * 32}.jpg"
THUMB = f"photos/{'c' * 32}.thumb.jpg"
AUDIO = f"audio/{'d' * 32}.m4a"


def zipped(members):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, value in members.items():
            archive.writestr(name, value)
    return out.getvalue()


def modern_members():
    # Deliberately opaque synthetic bytes verify that import does not decode or run media.
    media = {PHOTO: b"original photo", THUMB: b"thumbnail", AUDIO: b"opaque m4a evidence"}
    def meta(name):
        return {"bytes": len(media[name]), "sha256": hashlib.sha256(media[name]).hexdigest()}

    workspace = {"format": "envevidence-android", "schema_version": 1, "lab": {
        "version": 2,
        "experiments": [{"id": "a" * 32, "title": "UV staged reactor",
                         "run": {"process": "UV/H2O2"}, "water": {"matrix": "mbr_effluent"}}],
        "timers": [{"id": "e" * 32, "experiment_id": "a" * 32, "kind": "staged",
                    "status": "running", "stages": [{"title": "UV", "duration_ms": 1000}],
                    "repeat_count": 3, "delay_ms": 100, "transition_mode": "manual"}],
        "samples": [{"id": "b" * 32, "experiment_id": "a" * 32, "timer_id": "e" * 32,
                     "elapsed_ms": 60000, "recorded_elapsed_ms": 61000, "c_over_c0": 0.8,
                     "quench": {"delay_ms": 200}, "revisions": [{"elapsed_ms": 61000}]}],
        "records": [{"id": "f" * 32, "experiment_id": "a" * 32, "body": "Pale yellow",
                     "photos": [{"id": "c" * 32, "ext": "jpg", "mime": "image/jpeg",
                                 **meta(PHOTO)}],
                     "audios": [{"id": "d" * 32, "name": "Observation.m4a", "ext": "m4a",
                                 "mime": "audio/mp4", "duration_ms": 4000, **meta(AUDIO)}]}],
        "events": [{"id": "1" * 32, "kind": "timer_stage_due", "timer_id": "e" * 32}],
        "counters": [],
        "workflows": [{"id": "2" * 32, "experiment_id": "a" * 32,
                       "template_id": "3" * 32,
                       "steps": [{"id": "4" * 32, "title": "Mix", "status": "active"}]}],
        "experiment_templates": [{"id": "3" * 32, "title": "UV template", "version": 2}],
        "observation_phrases": [{"id": "5" * 32, "text": "Pale yellow"}],
    }}
    members = {"workspace.json": json.dumps(workspace).encode(), **media}
    refresh_manifest(members)
    return members, workspace


def refresh_manifest(members):
    manifest = {"format": "envevidence-media", "version": 1,
                "workspace_sha256": hashlib.sha256(members["workspace.json"]).hexdigest(),
                "files": {name: {"bytes": len(value),
                                 "sha256": hashlib.sha256(value).hexdigest()}
                          for name, value in members.items()
                          if name.startswith(("photos/", "audio/"))}}
    members["media-manifest.json"] = json.dumps(manifest).encode()


def test_modern_zip_preserves_original_media_workflow_sample_relations_and_hashes(tmp_path):
    members, workspace = modern_members()
    data = zipped(members)
    project, store = AnalysisProject(name="Mobile 0.7.0"), AnalysisStore(tmp_path)
    series = import_mobile(project, store, "reactor.zip", data)
    assert project.sources[0].sha256 == hashlib.sha256(data).hexdigest()
    assert store.read_source(project, project.sources[0]) == data
    archive = project.mobile_archives[0]
    assert archive["workspace"] == workspace
    assert archive["workspace"]["lab"]["timers"][0]["status"] == "running"
    for collection in ("workflows", "experiment_templates", "observation_phrases", "records"):
        assert archive["workspace"]["lab"][collection] == workspace["lab"][collection]
    assert series[0].observations[0].metadata["mobile_sample"]["timer_id"] == "e" * 32
    assert series[0].observations[0].metadata["mobile_sample"]["recorded_elapsed_ms"] == 61000
    assert series[0].observations[0].x == 1
    for member in (PHOTO, THUMB, AUDIO, "media-manifest.json"):
        assert store.read_mobile_member(project, archive["source_id"], member) == members[member]
        assert (store.project_dir(project.id) / archive["members"][member]).read_bytes() == members[member]
    store.save(project)
    restored = store.load(project.id)
    assert restored.mobile_archives == project.mobile_archives
    assert import_mobile(project, store, "repeated.zip", data) == []


@pytest.mark.parametrize("member", ["workspace.json", PHOTO, THUMB, AUDIO])
def test_modern_zip_rejects_each_corrupted_member_before_persistence(tmp_path, member):
    members, _ = modern_members()
    members[member] += b" "  # Workspace still parses, so its separate hash must detect this.
    project, store = AnalysisProject(name="Bad checksum"), AnalysisStore(tmp_path)
    with pytest.raises(ValueError, match="checksum|byte count"):
        import_mobile(project, store, "bad.zip", zipped(members))
    assert not project.sources and not project.series and not project.mobile_archives
    assert not store.project_dir(project.id).exists()


@pytest.mark.parametrize("change", ["missing_file", "extra_file", "wrong_size", "wrong_hash",
                                    "wrong_workspace", "bad_version", "empty_manifest"])
def test_modern_zip_rejects_incomplete_or_malformed_manifest(tmp_path, change):
    members, _ = modern_members()
    manifest = json.loads(members["media-manifest.json"])
    if change == "missing_file":
        del manifest["files"][AUDIO]
    elif change == "extra_file":
        manifest["files"][f"audio/{'6' * 32}.m4a"] = manifest["files"][AUDIO]
    elif change == "wrong_size":
        manifest["files"][AUDIO]["bytes"] += 1
    elif change == "wrong_hash":
        manifest["files"][AUDIO]["sha256"] = "0" * 64
    elif change == "wrong_workspace":
        manifest["workspace_sha256"] = "0" * 64
    elif change == "bad_version":
        manifest["version"] = True
    else:
        manifest = []
    members["media-manifest.json"] = json.dumps(manifest).encode()
    project, store = AnalysisProject(name="Bad manifest"), AnalysisStore(tmp_path)
    with pytest.raises(ValueError):
        import_mobile(project, store, "bad.zip", zipped(members))
    assert not project.sources and not store.project_dir(project.id).exists()


@pytest.mark.parametrize("change", ["missing_audio_ref", "bad_audio_hash", "bad_photo_bytes",
                                    "missing_audio_file", "missing_thumb", "duplicate_audio_ref",
                                    "unsafe_ref"])
def test_modern_zip_rejects_incomplete_or_conflicting_record_references(tmp_path, change):
    members, workspace = modern_members()
    record = workspace["lab"]["records"][0]
    if change == "missing_audio_ref":
        record["audios"] = []
    elif change == "bad_audio_hash":
        record["audios"][0]["sha256"] = "0" * 64
    elif change == "bad_photo_bytes":
        record["photos"][0]["bytes"] += 1
    elif change == "missing_audio_file":
        del members[AUDIO]
    elif change == "missing_thumb":
        del members[THUMB]
    elif change == "duplicate_audio_ref":
        record["audios"].append(dict(record["audios"][0]))
    else:
        record["audios"][0]["id"] = "../outside"
    members["workspace.json"] = json.dumps(workspace).encode()
    refresh_manifest(members)  # Internal manifest hashes pass; record references must still fail.
    project, store = AnalysisProject(name="Bad reference"), AnalysisStore(tmp_path)
    with pytest.raises(ValueError):
        import_mobile(project, store, "bad.zip", zipped(members))
    assert not project.sources and not store.project_dir(project.id).exists()


@pytest.mark.parametrize("path", ["audio/../../outside.m4a", "audio\\bad.m4a",
                                 f"audio/{'d' * 32}.mp3", "/audio/absolute.m4a",
                                 "media-manifest.json/extra", "audio/run.sh"])
def test_modern_zip_rejects_unsafe_or_unexpected_audio_paths(tmp_path, path):
    members, _ = modern_members()
    members[path] = b"untrusted"
    project, store = AnalysisProject(name="Unsafe"), AnalysisStore(tmp_path)
    with pytest.raises(ValueError):
        import_mobile(project, store, "bad.zip", zipped(members))
    assert not project.sources and not store.project_dir(project.id).exists()


def test_audio_requires_manifest_but_legacy_photo_zip_still_imports(tmp_path):
    members, workspace = modern_members()
    del members["media-manifest.json"]
    project, store = AnalysisProject(name="Legacy"), AnalysisStore(tmp_path)
    with pytest.raises(ValueError, match="requires a complete media manifest"):
        import_mobile(project, store, "unverified-audio.zip", zipped(members))
    del members[AUDIO]
    workspace["lab"]["records"][0]["audios"] = []
    for key in ("sha256", "bytes"):
        del workspace["lab"]["records"][0]["photos"][0][key]
    members["workspace.json"] = json.dumps(workspace).encode()
    data = zipped(members)
    assert len(import_mobile(project, store, "legacy-photo.zip", data)) == 1
    assert store.read_source(project, project.sources[0]) == data


def test_manifest_rejects_duplicate_json_properties_and_duplicate_zip_members(tmp_path):
    members, _ = modern_members()
    members["media-manifest.json"] = b'{"format":"envevidence-media","format":"other"}'
    project, store = AnalysisProject(name="Duplicates"), AnalysisStore(tmp_path)
    with pytest.raises(ValueError, match="Duplicate mobile JSON"):
        import_mobile(project, store, "bad.zip", zipped(members))
    members, _ = modern_members()
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as archive:
        for name, value in members.items():
            archive.writestr(name, value)
        with pytest.warns(UserWarning, match="Duplicate name"):
            archive.writestr(AUDIO, members[AUDIO])
    with pytest.raises(ValueError, match="duplicate mobile archive path"):
        import_mobile(project, store, "bad.zip", out.getvalue())
    assert not project.sources and not store.project_dir(project.id).exists()


def test_corrupt_zip_container_fails_before_writing_any_original(tmp_path):
    project, store = AnalysisProject(name="Damaged ZIP"), AnalysisStore(tmp_path)
    for payload in (b"This is not a ZIP", b"PK\x03\x04\x00\x00"):
        with pytest.raises(ValueError, match="Invalid mobile ZIP archive"):
            import_mobile(project, store, "damaged.zip", payload)
    assert not project.sources and not project.series and not project.mobile_archives
    assert not store.project_dir(project.id).exists()
