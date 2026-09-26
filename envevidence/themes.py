"""App-owned styles. No Streamlit private configuration APIs."""

import streamlit as st

PALETTES = {
    "forest": ("#147D73", "#F6F8F7", "#19312F"),
    "ocean": ("#1D4ED8", "#F4F7FB", "#172B4D"),
    "sand": ("#A84D18", "#FAF7F2", "#342D27"),
    "graphite": ("#6D4ACF", "#F7F5FB", "#292536"),
}
NOTE_COLORS = {"sage": "#E4F1E8", "sky": "#E5EEFA", "sand": "#FFF0D4", "lavender": "#EFE7FA"}


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
    if preferences.palette == "custom":
        accent, background = preferences.accent, preferences.background
        text = foreground(background)
    else:
        accent, background, text = PALETTES[preferences.palette]
    return {
        "accent": accent,
        "background": background,
        "text": text,
        "on_accent": foreground(accent),
    }


def apply_theme(preferences):
    c = colors(preferences)
    st.markdown(
        f"""<style>
    .stApp {{background:{c["background"]};color:{c["text"]}}}
    .block-container {{max-width:1200px;padding-top:2rem;padding-bottom:3rem}}
    [data-testid="stSidebar"] {{background:#fff;color:#25332F;border-right:1px solid #DFE5E2}}
    [data-testid="stSidebar"] p,[data-testid="stSidebar"] h2 {{color:#25332F}}
    h1,h2,h3 {{letter-spacing:-.035em;color:inherit}}
    .ee-hero {{padding:30px 34px;background:{c["accent"]};border-radius:18px;
        color:{c["on_accent"]};margin-bottom:24px}}
    .ee-hero h1 {{color:inherit!important;font-size:38px;margin:4px 0 8px}}
    .ee-hero p {{color:inherit;font-size:16px;margin:0}}
    .ee-eyebrow {{font-size:11px;letter-spacing:2.5px;text-transform:uppercase;margin-bottom:10px}}
    .ee-note {{padding:20px;border-radius:12px;color:#202A26;white-space:pre-wrap;
        overflow-wrap:anywhere;margin:8px 0 16px}}
    [class*="st-key-surface_"], [data-testid="stForm"], [data-testid="stExpander"],
    [data-testid="stMetric"] {{background:#fff;color:#25332F;border-radius:12px}}
    [data-testid="stMetric"] {{padding:12px;border:1px solid #DFE5E2}}
    [class*="st-key-surface_"] h3,[class*="st-key-surface_"] p,
    [data-testid="stForm"] p,[data-testid="stExpander"] p {{color:#25332F}}
    [data-testid="stForm"],[data-testid="stExpander"] {{color:#25332F}}
    [data-testid="stMain"] h2,[data-testid="stMain"] h3 {{color:{c['text']}}}
    [class*="st-key-surface_"] h3 {{color:#25332F}}
    [data-testid="stWidgetLabel"] {{background:#fff;color:#25332F;border-radius:4px;padding:2px 4px}}
    .stButton>button,.stDownloadButton>button {{border-radius:8px}}
    button[kind="secondary"],button[kind="secondary"] p,
    button[kind="secondaryFormSubmit"],button[kind="secondaryFormSubmit"] p,
    .stDownloadButton button,.stDownloadButton button p {{background:#fff;color:#25332F!important}}
    [data-testid="stHeader"] {{background:#fff;color:#25332F}}
    .stTextInput input,.stTextArea textarea,[role="combobox"] {{color:#25332F!important}}
    .stTabs [role="tab"] {{color:{c['text']}}}
    [data-testid="stAlert"] p {{color:#25332F}}
    button[kind="primary"],button[kind="primaryFormSubmit"] {{background:{c["accent"]}!important;
        color:{c["on_accent"]}!important;border-color:{c["accent"]}!important}}
    button[kind="primary"] p,button[kind="primaryFormSubmit"] p {{color:{c["on_accent"]}!important}}
    .stProgress [role="progressbar"]>div>div {{background:{c["accent"]}}}
    @media(max-width:700px) {{
      [data-testid="stHorizontalBlock"] {{flex-wrap:wrap}}
      [data-testid="stColumn"] {{width:100%!important;flex:1 1 100%!important;min-width:0!important}}
      .block-container {{padding:4.5rem 1rem 2rem}}
      .ee-hero {{padding:22px}} .ee-hero h1 {{font-size:29px}}
    }}
    </style>""",
        unsafe_allow_html=True,
    )
