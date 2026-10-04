import base64
import hashlib
import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from envevidence.themes import ASSETS, PALETTES, colors, contrast, design_tokens, theme_css
from envevidence.workspace import Preferences, Workspace, WorkspaceStore

ROOT = Path(__file__).resolve().parents[1]


def test_shared_design_tokens_and_new_workspace_defaults_match_android(tmp_path):
    mobile = json.loads(
        (ROOT / "android/app/src/main/assets/design-tokens.json").read_text(encoding="utf-8-sig")
    )
    tokens = design_tokens()
    assert tokens == mobile
    workspace = WorkspaceStore(tmp_path).load()
    assert workspace.preferences.palette == "mineral"
    assert (workspace.preferences.accent, workspace.preferences.background) == PALETTES["mineral"][:2]
    assert tokens["type"]["body"] == 16
    assert tokens["type"]["line_height"] >= 1.5
    assert tokens["interaction"]["touch_min"] == 48
    assert tokens["radius"]["control"] == 10 and tokens["radius"]["card"] == 16


@pytest.mark.parametrize("palette", list(PALETTES) + ["custom"])
@pytest.mark.parametrize("accent,background", [("#FFFF00", "#001122"), ("#FFFFFF", "#FFFFFF")])
def test_saved_palettes_keep_readable_control_surface_and_focus_pairs(palette, accent, background):
    c = colors(Preferences(palette=palette, accent=accent, background=background))
    assert contrast(c["on_accent"], c["accent"]) >= 4.5
    assert contrast(c["text"], c["background"]) >= 4.5
    assert contrast(c["on_surface"], c["surface"]) >= 4.5
    assert contrast(c["muted"], c["surface"]) >= 4.5
    assert contrast(c["page_muted"], c["background"]) >= 4.5
    assert contrast(c["surface_link"], c["surface"]) >= 4.5
    assert contrast(c["page_link"], c["background"]) >= 4.5
    assert contrast(c["focus"], c["surface"]) >= 3
    assert contrast(c["control_border"], c["surface"]) >= 3


def test_theme_fonts_are_embedded_from_bundled_files_without_remote_requests():
    css = theme_css(Preferences())
    urls = re.findall(r"url\('([^']+)'\)", css)
    assert len(urls) == 3
    assert "@import" not in css and "https://" not in css and "http://" not in css
    metadata = json.loads((ASSETS / "fonts/UI-SOURCES.json").read_text(encoding="utf-8-sig"))
    for uri, source in zip(urls[:2], metadata["files"]):
        assert uri.startswith("data:font/ttf;base64,")
        embedded = base64.b64decode(uri.split(",", 1)[1])
        assert embedded == (ASSETS / "fonts" / source["name"]).read_bytes()
        assert hashlib.sha256(embedded).hexdigest() == source["sha256"]
    assert urls[2].startswith("data:font/woff2;base64,")
    chinese = base64.b64decode(urls[2].split(",", 1)[1])
    assert chinese == (ASSETS / "fonts/EnvSansCJK-UI.woff2").read_bytes()
    assert "'Source Sans 3','Env Sans CJK'" in css
    assert "font-display:swap" in css
    assert ':focus-visible' in css and "outline:3px solid" in css
    assert "prefers-reduced-motion:reduce" in css


@pytest.mark.parametrize("palette", ["clay", "forest", "ocean", "sand", "graphite", "custom"])
def test_existing_preferences_and_private_planning_data_survive_palette_update(tmp_path, palette):
    store = WorkspaceStore(tmp_path)
    existing = Workspace.model_validate(
        {
            "preferences": {
                "language": "zh", "palette": palette, "accent": "#A1B2C3",
                "background": "#182938", "order": ["notes", "tasks", "evidence", "learning"],
                "hidden": ["tasks"],
            },
            "notes": [{"id": "private", "title": "原始笔记", "body": "不可更改", "pinned": True}],
        }
    )
    store.save(existing)
    loaded = store.load()
    assert loaded.preferences == existing.preferences
    assert loaded.notes == existing.notes
    store.save(loaded)
    assert store.load().preferences == existing.preferences
    assert store.load().notes == existing.notes


@pytest.mark.parametrize("preferences", [None, {}, {"language": "zh"}])
def test_existing_files_without_color_fields_keep_original_forest_defaults(tmp_path, preferences):
    store = WorkspaceStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    raw = {} if preferences is None else {"preferences": preferences}
    store.path.write_text(json.dumps(raw), encoding="utf-8")
    prefs = store.load().preferences
    assert prefs.palette == "forest"
    assert (prefs.accent, prefs.background) == PALETTES["forest"][:2]


def test_explicit_invalid_preferences_are_rejected_without_rewriting(tmp_path):
    store = WorkspaceStore(tmp_path)
    store.path.parent.mkdir(parents=True)
    store.path.write_text('{"preferences":null}', encoding="utf-8")
    before = store.path.read_bytes()
    with pytest.raises(ValidationError):
        store.load()
    assert store.path.read_bytes() == before

