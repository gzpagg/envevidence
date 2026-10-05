"""App-owned, offline styles shared with the Android workbench."""

import base64
import json
from functools import lru_cache
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent / "assets"


@lru_cache(maxsize=1)
def design_tokens():
    return json.loads((ASSETS / "design-tokens.json").read_text(encoding="utf-8-sig"))


PALETTES = {
    "glacier": (
        design_tokens()["colors"]["accent"],
        design_tokens()["colors"]["paper"],
        design_tokens()["colors"]["ink"],
    ),
    "mineral": ("#186B62", "#F4F7F6", "#243638"),
    "clay": ("#A65338", "#F7F5F0", "#302E29"),
    "forest": ("#147D73", "#F6F8F7", "#19312F"),
    "ocean": ("#1D4ED8", "#F4F7FB", "#172B4D"),
    "sand": ("#A84D18", "#FAF7F2", "#342D27"),
    "graphite": ("#6D4ACF", "#F7F5FB", "#292536"),
}


def luminance(color):
    channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    channels = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return sum(c * w for c, w in zip(channels, (0.2126, 0.7152, 0.0722)))


def contrast(a, b):
    high, low = sorted([luminance(a), luminance(b)], reverse=True)
    return (high + 0.05) / (low + 0.05)


def foreground(background):
    return (
        "#FFFFFF"
        if contrast(background, "#FFFFFF") > contrast(background, "#000000")
        else "#000000"
    )


def colors(preferences):
    tokens = design_tokens()["colors"]
    if preferences.palette == "custom":
        accent, background = preferences.accent, preferences.background
        text = foreground(background)
    else:
        accent, background, text = PALETTES[preferences.palette]
    surface = tokens["surface"]
    return {
        "accent": accent,
        "background": background,
        "text": text,
        "on_accent": foreground(accent),
        "surface": surface,
        "on_surface": tokens["ink"],
        "muted": tokens["muted"],
        "page_muted": tokens["muted"] if contrast(background, tokens["muted"]) >= 4.5 else text,
        "line": tokens["line"],
        "control_border": tokens["control_border"],
        "focus": accent if contrast(accent, surface) >= 3 else tokens["accent"],
        "page_link": accent if contrast(accent, background) >= 4.5 else text,
        "surface_link": accent if contrast(accent, surface) >= 4.5 else tokens["ink"],
    }


@lru_cache(maxsize=1)
def font_faces():
    """Embed bundled Latin fonts and a Chinese UI subset without a font service."""
    faces = []
    for family, filename in (
        ("Source Sans 3", "SourceSans3-Variable.ttf"),
        ("Source Serif 4", "SourceSerif4-Variable.ttf"),
    ):
        payload = base64.b64encode((ASSETS / "fonts" / filename).read_bytes()).decode("ascii")
        faces.append(
            f"@font-face {{font-family:'{family}';font-style:normal;font-weight:200 900;"
            f"font-display:swap;src:url('data:font/ttf;base64,{payload}') format('truetype');}}"
        )
    chinese = base64.b64encode((ASSETS / "fonts" / "EnvSansCJK-UI.woff2").read_bytes()).decode("ascii")
    faces.append(
        "@font-face {font-family:'Env Sans CJK';font-style:normal;font-weight:400;"
        f"font-display:swap;src:url('data:font/woff2;base64,{chinese}') format('woff2');}}"
    )
    return "\n".join(faces)


def theme_css(preferences):
    """Generate one token-driven stylesheet while keeping saved palette semantics."""
    c, tokens = colors(preferences), design_tokens()
    glass = tokens["materials"]["glass"]
    gradient = tokens["gradients"]["focus"]
    translucent = preferences.visual_style == "glass" and not preferences.reduce_transparency
    fill = glass["fill"] if translucent else tokens["materials"]["solid"]["fill"]
    blur = f"blur({glass['blur_px']}px) saturate({glass['saturation']})" if translucent else "none"
    return f"""<style>
    {font_faces()}
    :root {{
      --ee-paper:{c['background']};--ee-surface:{c['surface']};--ee-ink:{c['text']};
      --ee-on-surface:{c['on_surface']};--ee-muted:{c['muted']};--ee-page-muted:{c['page_muted']};
      --ee-accent:{c['accent']};--ee-on-accent:{c['on_accent']};--ee-line:{c['line']};
      --ee-control-border:{c['control_border']};--ee-focus:{c['focus']};
      --ee-font-body:'{tokens['fonts']['body']}','Env Sans CJK','Microsoft YaHei','PingFang SC',system-ui,sans-serif;
      --ee-font-heading:'{tokens['fonts']['heading']}','Env Sans CJK','Microsoft YaHei','PingFang SC',system-ui,sans-serif;
      --ee-body:{tokens['type']['body']}px;--ee-caption:{tokens['type']['caption']}px;
      --ee-leading:{tokens['type']['line_height']};--ee-control-radius:{tokens['radius']['control']}px;
      --ee-card-radius:{tokens['radius']['card']}px;--ee-touch-min:{tokens['interaction']['touch_min']}px;
      --ee-transition:{tokens['interaction']['transition_ms']}ms;
      --ee-glass:{fill};--ee-glass-filter:{blur};--ee-glass-border:{glass['border']};
      --ee-floating-shadow:{tokens['elevation']['floating']};--ee-card-shadow:{tokens['elevation']['card']};
      --ee-focus-gradient:linear-gradient({gradient['angle']}deg,{gradient['from']},{gradient['to']});
    }}
    .stApp {{background:var(--ee-paper);color:var(--ee-ink);
      font-family:var(--ee-font-body);font-size:var(--ee-body);line-height:var(--ee-leading)}}
    .block-container {{max-width:1480px;padding-top:24px;padding-bottom:48px}}
    [data-testid="stMain"] {{color:var(--ee-ink)}}
    [data-testid="stMarkdownContainer"],[data-testid="stCaptionContainer"],p,label,input,textarea,select,button,
    [role="combobox"],[role="tab"],[role="listbox"],[role="option"],[data-testid="stMetric"]
      {{font-family:var(--ee-font-body)!important}}
    [data-testid="stMarkdownContainer"] p,[data-testid="stWidgetLabel"] p,
    input,textarea,select,button p,[role="combobox"] {{font-size:var(--ee-body);line-height:var(--ee-leading)}}
    [data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input,[data-testid="stSelectbox"] input
      {{font-size:var(--ee-body)!important}}
    h1,h2,h3,h4,h5,h6 {{font-family:var(--ee-font-body)!important;color:inherit;
      letter-spacing:-.01em;text-wrap:balance;font-weight:600}}
    [data-testid="stMain"] h1,[data-testid="stMain"] h2 {{font-family:var(--ee-font-heading)!important;
      font-size:28px;font-weight:650;line-height:1.25;letter-spacing:-.02em}}
    [data-testid="stCaptionContainer"] {{opacity:1!important}}
    [data-testid="stCaptionContainer"] p {{font-size:var(--ee-caption);
      line-height:var(--ee-leading);letter-spacing:.015em;color:var(--ee-page-muted)}}
    [data-testid="stSidebar"] {{background:var(--ee-focus-gradient);color:var(--ee-on-surface);
      border-right:1px solid var(--ee-line)}}
    [data-testid="stSidebar"] h2,[data-testid="stSidebar"] p {{color:var(--ee-on-surface)}}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{color:var(--ee-muted)}}
    [data-testid="stSidebar"] [data-testid="stButton"] button {{justify-content:flex-start;padding-inline:16px}}
    .ee-hero {{padding:24px;background:var(--ee-focus-gradient);color:var(--ee-on-surface);
      border:1px solid var(--ee-line);border-radius:var(--ee-card-radius);margin-bottom:24px}}
    .ee-hero h1 {{font-family:var(--ee-font-heading)!important;font-size:28px;line-height:1.2;
      color:inherit!important;margin:0 0 12px}}
    .ee-hero h3 {{font-size:24px;color:inherit!important;margin:0 0 12px}}
    .ee-hero p {{font-size:var(--ee-body);color:var(--ee-muted);margin:0;max-width:65ch}}
    [class*="st-key-surface_"],[data-testid="stForm"],[data-testid="stExpander"],
    [data-testid="stMetric"] {{background:var(--ee-surface);color:var(--ee-on-surface);
      border-radius:var(--ee-card-radius);border-color:var(--ee-line)}}
    [data-testid="stForm"] {{padding:20px;border:1px solid var(--ee-line)}}
    [data-testid="stMetric"] {{padding:10px 14px;border:1px solid var(--ee-line);
      font-variant-numeric:tabular-nums}}
    [class*="st-key-surface_"] h3,[class*="st-key-surface_"] p,
    [data-testid="stForm"] p,[data-testid="stExpander"] p,[data-testid="stAlert"] p
      {{color:var(--ee-on-surface)}}
    [class*="st-key-surface_"] [data-testid="stCaptionContainer"] p,
    [data-testid="stForm"] [data-testid="stCaptionContainer"] p,
    [data-testid="stExpander"] [data-testid="stCaptionContainer"] p {{color:var(--ee-muted)}}
    [data-testid="stWidgetLabel"] {{background:transparent;color:inherit;padding:0}}
    .stButton>button,.stDownloadButton>button,.stFormSubmitButton>button,
    [data-testid="stFileUploader"] button {{min-height:var(--ee-touch-min);
      border-radius:var(--ee-control-radius);font-weight:600;letter-spacing:.01em;
      transition:background-color var(--ee-transition),border-color var(--ee-transition);
      touch-action:manipulation}}
    button[kind="secondary"],button[kind="secondaryFormSubmit"],.stDownloadButton button
      {{background:var(--ee-surface);color:var(--ee-on-surface)!important;
      border-color:var(--ee-control-border)}}
    button[kind="secondary"] p,button[kind="secondaryFormSubmit"] p,.stDownloadButton button p
      {{color:var(--ee-on-surface)!important}}
    button[kind="secondary"]:hover,button[kind="secondaryFormSubmit"]:hover,
    .stDownloadButton button:hover {{background:{tokens['colors']['paper']};border-color:var(--ee-focus)}}
    button[kind="primary"],button[kind="primaryFormSubmit"] {{background:var(--ee-accent)!important;
      color:var(--ee-on-accent)!important;border-color:var(--ee-accent)!important}}
    button[kind="primary"] p,button[kind="primaryFormSubmit"] p {{color:var(--ee-on-accent)!important}}
    button:disabled {{cursor:not-allowed}}
    [data-testid="stHeader"] {{background:transparent;color:var(--ee-on-surface)}}
    .stTextInput input,.stTextArea textarea,.stNumberInput input,[role="combobox"]
      {{background:var(--ee-surface);color:var(--ee-on-surface)!important;min-height:var(--ee-touch-min)}}
    [data-baseweb="input"],[data-baseweb="textarea"],[data-baseweb="select"]>div,
    [data-baseweb="popover"] {{background:var(--ee-surface);color:var(--ee-on-surface);
      border-color:var(--ee-control-border);border-radius:var(--ee-control-radius)}}
    input::placeholder,textarea::placeholder {{color:var(--ee-muted);opacity:1}}
    [data-testid="stDataFrame"],[data-testid="stTable"] {{font-variant-numeric:tabular-nums}}
    .stTabs [role="tab"] {{color:var(--ee-ink);min-height:var(--ee-touch-min)}}
    a {{color:{c['page_link']};text-underline-offset:3px}}
    [data-testid="stSidebar"] a,[data-testid="stForm"] a,[data-testid="stExpander"] a,
    [class*="st-key-surface_"] a {{color:{c['surface_link']}}}
    [data-testid="stTextInputRootElement"],[data-testid="stTextAreaRootElement"],
    [data-testid="stNumberInputContainer"],[data-testid="stSelectbox"] [role="group"],
    [data-testid="stMultiselect"] [role="group"]
      {{background:var(--ee-surface)!important;border:1px solid var(--ee-control-border)!important;
      border-radius:var(--ee-control-radius)!important;min-height:var(--ee-touch-min)}}
    [data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,
    [data-testid="stNumberInput"] input,[data-testid="stSelectbox"] input
      {{background:var(--ee-surface);color:var(--ee-on-surface)!important}}
    button:focus-visible,input:focus-visible,textarea:focus-visible,select:focus-visible,
    a:focus-visible,[role="combobox"]:focus-visible,[role="tab"]:focus-visible,
    [data-baseweb="input"]:has(input:focus-visible),
    [data-baseweb="select"]:has(input:focus-visible),
    [data-testid="stTextInputRootElement"]:has(input:focus-visible),
    [data-testid="stSelectbox"] [role="group"]:has(input:focus-visible)
      {{outline:3px solid var(--ee-focus)!important;outline-offset:3px;
      box-shadow:0 0 0 2px var(--ee-surface)}}
    .stProgress [role="progressbar"]>div>div {{background:var(--ee-accent)}}
    .ee-brand {{display:flex;align-items:center;gap:10px;color:var(--ee-on-surface);font-size:23px;font-weight:700}}
    .ee-brand svg {{width:32px;height:32px;flex:none}}
    .st-key-analysis_toolbar button p {{white-space:normal;text-overflow:clip;overflow:visible;line-height:1.25}}
    .ee-context-title {{font-size:19px;font-weight:650;line-height:1.35;margin:0;overflow-wrap:anywhere}}
    .ee-context-summary {{font-size:13px;color:var(--ee-muted);margin:4px 0 0}}
    .ee-empty {{padding:20px;border:1px dashed var(--ee-control-border);border-radius:var(--ee-card-radius);
      background:var(--ee-surface);color:var(--ee-muted)}}
    [class*="st-key-glass_"] {{background:var(--ee-surface);border:1px solid var(--ee-line);
      border-radius:24px;padding:12px;color:var(--ee-on-surface);box-shadow:var(--ee-floating-shadow)}}
    @supports ((backdrop-filter:blur(1px)) or (-webkit-backdrop-filter:blur(1px))) {{
      [class*="st-key-glass_"] {{background:var(--ee-glass);border-color:var(--ee-glass-border);
        backdrop-filter:var(--ee-glass-filter);-webkit-backdrop-filter:var(--ee-glass-filter)}}
    }}
    [class*="st-key-glass_"] p {{color:var(--ee-on-surface)}}
    [class*="st-key-surface_"] {{padding:20px;border:1px solid var(--ee-line);box-shadow:var(--ee-card-shadow)}}
    .st-key-surface_analysis_context,.st-key-surface_evidence_context {{background:var(--ee-focus-gradient);padding:14px 18px}}
    .st-key-surface_evidence_metrics {{padding:0;border:0;box-shadow:none;background:transparent}}
    .st-key-surface_evidence_metrics [data-testid="stMetricValue"] {{font-size:23px}}
    [class*="st-key-surface_"] [data-testid="stImage"],
    [data-testid="stDataFrame"],[data-testid="stTable"] {{background:var(--ee-surface);color:var(--ee-on-surface)}}
    [class*="st-key-workflow_"] [role="tablist"] {{gap:4px;border-bottom:1px solid var(--ee-line);padding-bottom:6px}}
    [class*="st-key-workflow_"] [role="tab"] {{padding:10px 14px;border-radius:12px;transition:background-color var(--ee-transition)}}
    [class*="st-key-workflow_"] [role="tab"][aria-selected="true"] {{background:var(--ee-accent);color:var(--ee-on-accent)}}
    [class*="st-key-workflow_"] [role="tab"][aria-selected="true"] p {{color:var(--ee-on-accent)}}
    [class*="st-key-workflow_"] [data-baseweb="tab-highlight"] {{display:none}}
    @media(max-width:900px) {{
      [class*="st-key-split_"]>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"] {{flex-wrap:wrap}}
      [class*="st-key-split_"]>[data-testid="stLayoutWrapper"]>[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]
        {{width:100%!important;flex:1 1 100%!important;min-width:0!important}}
    }}
    @media(max-width:700px) {{
      [data-testid="stHorizontalBlock"] {{flex-wrap:wrap}}
      [data-testid="stColumn"] {{width:100%!important;flex:1 1 100%!important;min-width:0!important}}
      .block-container {{padding:72px 16px 32px}}
      .ee-hero {{padding:20px}} .ee-hero h1 {{font-size:26px}}
      [class*="st-key-surface_"] {{padding:14px}}
      .st-key-surface_evidence_metrics {{padding:0}}
    }}
    @media(prefers-reduced-transparency:reduce) {{
      [class*="st-key-glass_"] {{background:var(--ee-surface)!important;
        backdrop-filter:none!important;-webkit-backdrop-filter:none!important}}
    }}
    @media(prefers-reduced-motion:reduce) {{
      button,a,[role="tab"] {{transition:none!important;scroll-behavior:auto!important}}
    }}
    </style>"""


def apply_theme(preferences):
    st.markdown(theme_css(preferences), unsafe_allow_html=True)
