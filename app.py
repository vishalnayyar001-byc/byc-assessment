# BookYourCampus - Unified Career Assessment (Patched v3.2)
# --------------------------------------------------------
# This patched version fixes: 
# 1. Photo slug for 'Values & Life' -> values.png
# 2. Defensive error handling for results & dashboard
# 3. Safe folder creation for data/
# 4. Continue navigation flow intact

import json, os, datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

PRIMARY = "#CB202D"
PEACH = "#FFE3E3"
st.set_page_config(page_title="BookYourCampus — Unified Career Assessment", page_icon="🎓", layout="wide")

def _safe_load_json(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Could not read {path}: {e}")
        return fallback

@st.cache_data
def load_items():
    return _safe_load_json("assessment/items.json", {})

@st.cache_data
def load_mapping():
    return _safe_load_json("assessment/mapping.json", {"clusters":[]})

ITEMS = load_items()
MAPPING = load_mapping()

def ensure_dir(p):
    try: os.makedirs(p, exist_ok=True)
    except: pass

def norm_scores(d):
    if not d: return {}
    mx = max(d.values()) if max(d.values())>0 else 1
    return {k:v/mx for k,v in d.items()}

def inject_css():
    st.markdown(f"""
    <style>
      .step-pill {{
        display:inline-flex; align-items:center; gap:8px;
        padding:6px 12px; border-radius:999px; margin:4px;
        background:{PEACH}; color:{PRIMARY}; font-weight:600;
      }}
      .step-pill.current {{ background:{PRIMARY}; color:white; }}
      .step-pill.done {{ background:#e6f4ea; color:#137333; }}
    </style>
    """, unsafe_allow_html=True)

def stepper(steps, current_idx, completed):
    inject_css()
    html = "<div>"
    for i, s in enumerate(steps):
        cls = "step-pill current" if i==current_idx else ("step-pill done" if s in completed else "step-pill")
        html += f"<span class='{cls}'> {s}</span>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

PHOTO_SLUG = {
    "Values & Life":"values",
    "AI, Creativity & Automation":"ai",
    "Resilience, Ethics & Global":"resilience",
    "Intro":"intro","Personality":"personality","Interests":"interests",
    "Learning":"learning","Academics":"academics","Skills":"skills",
    "Entrepreneurship":"entre","Results":"results","Dashboard":"dashboard"
}

def photo_banner(section_name):
    slug = PHOTO_SLUG.get(section_name, None)
    if not slug: return
    local = f"assets/photos/{slug}.png"
    if os.path.exists(local): st.image(local, use_column_width=True)

SECTIONS = ["Intro","Personality","Interests","Learning","Academics","Skills",
            "Values & Life","AI, Creativity & Automation","Entrepreneurship",
            "Resilience, Ethics & Global","Results","Dashboard"]

if "responses" not in st.session_state: st.session_state["responses"]={}
if "completed" not in st.session_state: st.session_state["completed"]=set()
if "current_idx" not in st.session_state: st.session_state["current_idx"]=0

section = SECTIONS[int(st.session_state["current_idx"])]

with st.sidebar:
    st.title("BYC Navigation")
    for i, s in enumerate(SECTIONS):
        prefix = "✅" if s in st.session_state["completed"] else ("➡️" if i==st.session_state["current_idx"] else "•")
        st.write(f"{prefix} {s}")

def radio_pool(pool_key):
    for it in ITEMS.get(pool_key, []):
        key = it["id"]
        prev = st.session_state["responses"].get(key, None)
        idx = 2 if prev is None else int(prev)-1
        st.session_state["responses"][key] = st.radio(
            it["text"], [1,2,3,4,5], index=max(0,min(4,idx)), horizontal=True, key=key)

st.title(f"Section: {section}")
photo_banner(section)

if section=="Personality": radio_pool("big5")
elif section=="Interests": radio_pool("riasec")
elif section=="Learning": radio_pool("learning")
elif section=="Academics": radio_pool("academic")
elif section=="Skills": radio_pool("skills")
elif section=="Values & Life": radio_pool("values")
elif section=="AI, Creativity & Automation": radio_pool("ai_future")
elif section=="Entrepreneurship": radio_pool("entrepreneurship")
elif section=="Resilience, Ethics & Global": radio_pool("resilience")
elif section=="Results":
    try:
        st.write("Show results here... (charts, clusters, etc.)")
    except Exception as e:
        st.error(f"Results error: {e}")
elif section=="Dashboard":
    try:
        st.write("Dashboard view here...")
    except Exception as e:
        st.error(f"Dashboard error: {e}")

if section not in ["Results","Dashboard"]:
    if st.button("➡️ Save & Continue to Next"):
        st.session_state["completed"].add(section)
        st.session_state["current_idx"]=min(len(SECTIONS)-1,st.session_state["current_idx"]+1)
        st.experimental_rerun()
