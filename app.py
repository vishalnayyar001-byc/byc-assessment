
# BookYourCampus — Unified Career Assessment
# Version: v3.3 Full (next‑gen, patched)

import os, json, datetime, base64, io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# ---------- THEME ----------
PRIMARY = "#CB202D"    # BYC Red
PEACH   = "#FFE3E3"    # BYC Peach
ACCENT  = "#0D47A1"    # BYC Navy

st.set_page_config(page_title="BookYourCampus — Unified Career Assessment",
                   page_icon="🎓", layout="wide")

# ---------- LOADERS (defensive) ----------
def _safe_load_json(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Could not read {path}: {e}")
        return fallback

@st.cache_data(show_spinner=False)
def load_items():
    return _safe_load_json("assessment/items.json",
        {"big5":[], "riasec":[], "learning":[], "academic":[], "skills":[], "values":[],
         "extracurricular":[], "ai_future":[], "creativity":[], "entrepreneurship":[],
         "resilience":[], "ethics_global":[]})

@st.cache_data(show_spinner=False)
def load_mapping():
    return _safe_load_json("assessment/mapping.json", {"clusters":[], "notes":""})

ITEMS = load_items()
MAPPING = load_mapping()

# ---------- UTIL ----------
def ensure_dir(p):
    try: os.makedirs(p, exist_ok=True)
    except: pass

def norm_scores(d):
    if not d: return {}
    mx = max(d.values()) if max(d.values())>0 else 1
    return {k: (v/mx) for k,v in d.items()}

def score_pool(pool_key, group_key):
    """Aggregate Likert responses for a pool by its facet/group key."""
    scores = {}
    for it in ITEMS.get(pool_key, []):
        val = st.session_state["responses"].get(it["id"], 3)
        if it.get("reverse"):  # reverse scoring support
            val = 6 - val
        scores[it[group_key]] = scores.get(it[group_key], 0) + float(val)
    return scores

def composite_cluster_scores(domains):
    """Weighted composite across many domains -> sorted career clusters."""
    normalized = {k:norm_scores(v) for k,v in domains.items()}
    results = []
    for c in MAPPING.get("clusters", []):
        total = 0.0
        for group, weights in c.get("weights", {}).items():
            g = normalized.get(group, {})
            for facet, wt in weights.items():
                total += float(wt) * float(g.get(facet, 0.0))
        results.append({
            "cluster": c.get("name", "(Unnamed)"),
            "score": round(total, 5),
            "description": c.get("description", ""),
            "suggestions": c.get("suggestions", [])
        })
    if not results: return []
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    mx = results[0]["score"] if results[0]["score"]>0 else 1.0
    for r in results: r["percent"] = int(round(100*(r["score"]/mx)))
    return results

# ---------- BRAND UI ----------
def inject_css():
    css = """
    <style>
      .step-pill {{
        display:inline-flex; align-items:center; gap:8px;
        padding:6px 12px; border-radius:999px; margin:4px 6px 6px 0;
        background:{PEACH}; color:{PRIMARY}; font-weight:600; letter-spacing:.2px;
      }}
      .step-pill.current {{ background:{PRIMARY}; color:white; box-shadow:0 4px 14px rgba(0,0,0,.12); }}
      .step-pill.done {{ background:#e6f4ea; color:#137333; }}
      .metric-card {{
        background: white; border-radius:14px; padding:14px 16px; border:1px solid #eee;
        box-shadow:0 2px 10px rgba(0,0,0,.06);
      }}
      .byc-title {{ color:{PRIMARY}; }}
    </style>
    """.format(PRIMARY=PRIMARY, PEACH=PEACH)
    st.markdown(css, unsafe_allow_html=True)

def stepper(steps, current_idx, completed):
    inject_css()
    icons = {
        "Intro":"🎓","Personality":"🧠","Interests":"🎯","Learning":"📚","Academics":"📐",
        "Skills":"🧰","Values & Life":"💖","AI, Creativity & Automation":"🤖",
        "Entrepreneurship":"🚀","Resilience, Ethics & Global":"🧭","Results":"📈","Dashboard":"📊"
    }
    # Build HTML with status per step
    html = "<div>"
    for i, s in enumerate(steps):
        cls = "step-pill current" if i==current_idx else ("step-pill done" if s in completed else "step-pill")
        html += f"<span class='{cls}'>{icons.get(s,'•')} {s}</span>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

PHOTO_SLUG = {
    "Intro":"intro",
    "Personality":"personality",
    "Interests":"interests",
    "Learning":"learning",
    "Academics":"academics",
    "Skills":"skills",
    "Values & Life":"values",
    "AI, Creativity & Automation":"ai",
    "Entrepreneurship":"entre",
    "Resilience, Ethics & Global":"resilience",
    "Results":"results",
    "Dashboard":"dashboard"
}

def photo_banner(section_name):
    slug = PHOTO_SLUG.get(section_name, None)
    if not slug: return
    img_path = f"assets/photos/{slug}.png"
    if os.path.exists(img_path): st.image(img_path, use_column_width=True)
    vid_path = f"assets/videos/{slug}.mp4"
    if os.path.exists(vid_path): st.video(vid_path)

def header(section_name, steps, current_idx, completed):
    c1,c2 = st.columns([3,7])
    with c1:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=220)
        st.markdown(f"<h2 class='byc-title'>BookYourCampus — Unified Career Assessment</h2>", unsafe_allow_html=True)
    with c2:
        stepper(steps, current_idx, completed)
    photo_banner(section_name)

# ---------- NAV ----------
SECTIONS = [
    "Intro","Personality","Interests","Learning","Academics","Skills","Values & Life",
    "AI, Creativity & Automation","Entrepreneurship","Resilience, Ethics & Global","Results","Dashboard"
]

if "responses" not in st.session_state: st.session_state["responses"] = {}
if "completed" not in st.session_state: st.session_state["completed"] = set()
if "current_idx" not in st.session_state: st.session_state["current_idx"] = 0
if "student" not in st.session_state: st.session_state["student"] = {}
if "points" not in st.session_state: st.session_state["points"] = 0

current_idx = int(st.session_state["current_idx"])
completed = st.session_state["completed"]
section = SECTIONS[current_idx]

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("BYC Navigation")
    for i, s in enumerate(SECTIONS):
        prefix = "✅" if s in completed else ("➡️" if i==current_idx else "•")
        st.write(f"{prefix} {s}")
    st.markdown(f"**Points:** {st.session_state['points']}")
    st.markdown("---")
    # Save & load progress
    blob = json.dumps({
        "student": st.session_state.get("student", {}),
        "responses": st.session_state.get("responses", {}),
        "completed": list(st.session_state.get("completed", set())),
        "current_idx": st.session_state.get("current_idx", 0),
        "points": st.session_state.get("points", 0)
    }, ensure_ascii=False)
    st.download_button("⬇️ Save progress (.json)", data=blob, file_name="BYC_progress.json", mime="application/json")
    up = st.file_uploader("⬆️ Load progress (.json)", type=["json"])
    if up is not None:
        try:
            data = json.loads(up.getvalue().decode("utf-8"))
            st.session_state["student"] = data.get("student", {})
            st.session_state["responses"] = data.get("responses", {})
            st.session_state["completed"] = set(data.get("completed", []))
            st.session_state["current_idx"] = int(data.get("current_idx", 0))
            st.session_state["points"] = int(data.get("points", 0))
            st.success("Progress loaded.")
        except Exception as e:
            st.error(f"Could not load saved file: {e}")
    if st.button("💾 Save to server"):
        ensure_dir("data")
        with open("data/_autosave.json","w",encoding="utf-8") as f:
            json.dump({"student":st.session_state["student"],
                       "responses":st.session_state["responses"],
                       "completed":list(st.session_state["completed"]),
                       "current_idx":st.session_state["current_idx"],
                       "points":st.session_state["points"]}, f, ensure_ascii=False)
        st.success("Saved temporarily on server.")

# ---------- HEADER ----------
header(section, SECTIONS, current_idx, completed)

# ---------- QUESTION RENDER ----------
def radio_pool(pool_key):
    """Display Likert 1–5 for each item in the pool."""
    for it in ITEMS.get(pool_key, []):
        key = it["id"]
        prev = st.session_state["responses"].get(key, None)
        idx = 2 if prev is None else int(prev)-1
        st.session_state["responses"][key] = st.radio(
            it["text"], [1,2,3,4,5], index=max(0, min(4, idx)),
            horizontal=True, key=key
        )

# ---------- PAGES ----------
if section == "Intro":
    st.subheader("Welcome to BYC Unified Career Assessment")
    with st.form("student_form"):
        c1,c2 = st.columns(2)
        name = c1.text_input("Student name", value=st.session_state["student"].get("name",""))
        grade = c1.selectbox("Class/Grade", ["8","9","10","11","12","UG-1","UG-2","UG-3"],
                             index=2 if not st.session_state["student"].get("grade") else  ["8","9","10","11","12","UG-1","UG-2","UG-3"].index(st.session_state["student"].get("grade","10")))
        school = c2.text_input("School / College", value=st.session_state["student"].get("school",""))
        contact = c2.text_input("Contact email / phone (optional)", value=st.session_state["student"].get("contact",""))
        consent = st.checkbox("I agree to share my responses with BookYourCampus for guidance purposes.", value=True)
        if st.form_submit_button("Save") and consent:
            st.session_state["student"] = {"name":name,"grade":grade,"school":school,"contact":contact}
            st.success("Saved student info.")

elif section == "Personality":
    st.subheader("🧠 Personality — Big Five"); radio_pool("big5")

elif section == "Interests":
    st.subheader("🎯 Interests — RIASEC"); radio_pool("riasec")

elif section == "Learning":
    st.subheader("📚 Learning Preferences"); radio_pool("learning")

elif section == "Academics":
    st.subheader("📐 Academics"); radio_pool("academic")

elif section == "Skills":
    st.subheader("🧰 Skills"); radio_pool("skills")

elif section == "Values & Life":
    st.subheader("💖 Values & Life"); radio_pool("values"); st.markdown("---"); radio_pool("extracurricular")

elif section == "AI, Creativity & Automation":
    st.subheader("🤖 AI, Creativity & Automation"); radio_pool("ai_future"); st.markdown("---"); radio_pool("creativity")

elif section == "Entrepreneurship":
    st.subheader("🚀 Entrepreneurship"); radio_pool("entrepreneurship")

elif section == "Resilience, Ethics & Global":
    st.subheader("🧭 Resilience, Ethics & Global"); radio_pool("resilience"); st.markdown("---"); radio_pool("ethics_global")

elif section == "Results":
    st.subheader("📈 Results")
    try:
        big5 = score_pool("big5","trait"); ria = score_pool("riasec","domain")
        learn = score_pool("learning","modality"); acad = score_pool("academic","subject")
        skl = score_pool("skills","skill"); val = score_pool("values","value")
        ai = score_pool("ai_future","facet"); cre = score_pool("creativity","facet")
        ent = score_pool("entrepreneurship","facet"); res = score_pool("resilience","facet"); eth = score_pool("ethics_global","facet")

        # Radar charts
        def radar_fig(d, title):
            if not d: return go.Figure()
            labels = list(d.keys()); values = list(norm_scores(d).values())
            values += values[:1]; labels += labels[:1]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=values, theta=labels, fill='toself', name=title))
            fig.update_layout(title=title, margin=dict(l=0,r=0,t=40,b=0))
            return fig

        col1,col2 = st.columns(2)
        col1.plotly_chart(radar_fig(big5, "Personality (Big Five)"), use_container_width=True)
        col2.plotly_chart(radar_fig(ria, "Interests (RIASEC)"), use_container_width=True)

        # Composite clusters
        clusters = composite_cluster_scores({"riasec": ria, "big5": big5, "academic": acad, "skills": skl, "values": val,
            "ai_future": ai, "creativity": cre, "entrepreneurship": ent, "resilience": res, "ethics_global": eth})

        if clusters:
            top = clusters[:5]; labels = [x["cluster"] for x in top]; values = [x["percent"] for x in top]
            donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.55)])
            donut.update_layout(title="Top Career Clusters (relative)", margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(donut, use_container_width=True)

            # FutureFit Index (AI + Creativity + Entrepreneurship + Resilience + Ethics)
            parts = [norm_scores(x) for x in [ai, cre, ent, res, eth]]
            avg = sum([(sum(d.values())/len(d) if d else 0) for d in parts]) / (len(parts) if parts else 1)
            ff = int(round(100*avg))
            gauge = go.Figure(go.Indicator(mode="gauge+number", value=ff, title={"text":"FutureFit Index"},
                                           gauge={"axis":{"range":[0,100]}}))
            st.plotly_chart(gauge, use_container_width=True)

            st.markdown("### Recommendations & Next Steps")
            for i, r in enumerate(top, start=1):
                with st.expander(f"{i}. {r['cluster']} — {r['percent']}% fit"):
                    st.write(r["description"])
                    if r["suggestions"]:
                        st.write("**Try this next:**")
                        for s in r["suggestions"]:
                            st.write("- " + s)
        else:
            st.info("Answer more questions to generate your career clusters.")

        # Cohort CSV export
        ensure_dir("data")
        if st.button("Save my responses to cohort (CSV)"):
            row = {"timestamp": datetime.datetime.now().isoformat(),
                   "name": st.session_state.get("student",{}).get("name","")}
            for d, prefix in [(big5,"BIG5"),(ria,"RIASEC"),(learn,"LEARN"),(acad,"ACAD"),(skl,"SKILL"),(val,"VALUE"),
                              (ai,"AI"),(cre,"CRE"),(ent,"ENT"),(res,"RES"),(eth,"ETH")]:
                for k,v in d.items(): row[f"{prefix}_{k}"] = v
            row["TopCluster"] = top[0]["cluster"] if clusters else ""
            row["FutureFit"] = ff if clusters else ""
            fp = "data/responses.csv"
            df = pd.DataFrame([row])
            if os.path.exists(fp):
                old = pd.read_csv(fp); pd.concat([old, df], ignore_index=True).to_csv(fp, index=False)
            else:
                df.to_csv(fp, index=False)
            st.success("Saved to data/responses.csv")

        # Download simple HTML report
        if clusters:
            html = f"""
            <html><head><meta charset='utf-8'><title>BYC Report</title></head>
            <body style='font-family:Arial,sans-serif'>
              <h2 style='color:{PRIMARY}'>BookYourCampus — Career Snapshot</h2>
              <p><b>Name:</b> {st.session_state.get('student',{}).get('name','')}</p>
              <p><b>Grade:</b> {st.session_state.get('student',{}).get('grade','')}</p>
              <h3>Top Recommendations</h3>
              <ol>
                {''.join([f"<li><b>{r['cluster']}</b> — {r['percent']}% fit</li>" for r in top])}
              </ol>
              <p style='font-size:12px;color:#666'>Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </body></html>
            """
            st.download_button("⬇️ Download Summary (HTML)", html, file_name="BYC_report.html", mime="text/html")

    except Exception as e:
        st.error(f"Results rendering error: {e}")

elif section == "Dashboard":
    st.subheader("📊 Cohort Dashboard")
    fp = "data/responses.csv"
    if not os.path.exists(fp):
        st.info("No cohort data yet. Save some results from the Results page.")
    else:
        try:
            df = pd.read_csv(fp); st.dataframe(df.tail(100))
            if "TopCluster" in df.columns:
                counts = df["TopCluster"].value_counts().reset_index()
                fig = go.Figure(data=[go.Bar(x=counts["index"], y=counts["TopCluster"])])
                fig.update_layout(title="Top Cluster Distribution", xaxis_title="", yaxis_title="Students")
                st.plotly_chart(fig, use_container_width=True)
            if "FutureFit" in df.columns:
                df["timestamp"]=pd.to_datetime(df["timestamp"])
                trend = df.groupby(df["timestamp"].dt.date)["FutureFit"].mean().reset_index()
                fig2 = go.Figure(data=[go.Scatter(x=trend["timestamp"], y=trend["FutureFit"], mode='lines+markers')])
                fig2.update_layout(title="Average FutureFit Over Time", xaxis_title="Date", yaxis_title="FutureFit")
                st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(f"Dashboard error: {e}")

# ---------- ACTION BAR (bottom) ----------
st.markdown("---")
c1,c2 = st.columns([1,2])
with c1:
    if st.button("💾 Save (server)"):
        ensure_dir("data")
        with open("data/_autosave.json","w",encoding="utf-8") as f:
            json.dump({"student":st.session_state.get("student",{}),
                       "responses":st.session_state.get("responses",{}),
                       "completed":list(st.session_state.get("completed",set())),
                       "current_idx":int(st.session_state.get("current_idx",0)),
                       "points":int(st.session_state.get("points",0))}, f, ensure_ascii=False)
        st.success("Saved (server session).")
with c2:
    if section not in ["Results","Dashboard"]:
        if st.button("➡️ Save & Continue to Next"):
            # award gamified points
            answered = sum(1 for k,v in st.session_state["responses"].items() if v is not None)
            st.session_state["points"] = int(st.session_state.get("points",0)) + max(1, answered//10)
            st.session_state["completed"].add(section)
            st.session_state["current_idx"] = min(len(SECTIONS)-1, int(st.session_state["current_idx"])+1)
            st.rerun()
