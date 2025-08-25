
import json, os, io, base64, datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

PRIMARY = "#CB202D"
PEACH = "#FFE3E3"
ACCENT = "#0D47A1"
st.set_page_config(page_title="BookYourCampus — Unified Career Assessment", page_icon="🎓", layout="wide")

@st.cache_data
def load_items():
    with open("assessment/items.json","r",encoding="utf-8") as f: return json.load(f)
@st.cache_data
def load_mapping():
    with open("assessment/mapping.json","r",encoding="utf-8") as f: return json.load(f)
ITEMS = load_items()
MAPPING = load_mapping()

def ensure_dir(p):
    if not os.path.exists(p): os.makedirs(p, exist_ok=True)

def norm_scores(d):
    if not d: return {}
    mx = max(d.values()) if max(d.values())>0 else 1
    return {k:v/mx for k,v in d.items()}

def score_pool(pool_key, group_key):
    scores = {}
    for it in ITEMS.get(pool_key, []):
        val = st.session_state["responses"].get(it["id"], 3)
        if "reverse" in it and it.get("reverse"): val = 6 - val
        scores[it[group_key]] = scores.get(it[group_key], 0) + val
    return scores

def composite_cluster_scores(domains):
    normalized = {k:norm_scores(v) for k,v in domains.items()}
    results = []
    for c in MAPPING["clusters"]:
        total = 0.0
        for group, weights in c["weights"].items():
            g = normalized.get(group, {})
            for facet, wt in weights.items():
                total += wt * g.get(facet, 0.0)
        results.append({"cluster":c["name"],"score":round(total,5),"description":c["description"],"suggestions":c["suggestions"]})
    results = sorted(results, key=lambda x:x["score"], reverse=True)
    mx = results[0]["score"] if results and results[0]["score"]>0 else 1.0
    for r in results: r["percent"] = int(round(100*(r["score"]/mx)))
    return results

def inject_css():
    st.markdown(f"""
    <style>
      .step-pill {{
        display:inline-flex; align-items:center; gap:8px;
        padding:6px 12px; border-radius:999px; margin:4px;
        background:{PEACH}; color:{PRIMARY}; font-weight:600;
        animation: fadeIn .5s ease-in;
      }}
      .step-pill.current {{ background:{PRIMARY}; color:white; box-shadow:0 4px 14px rgba(0,0,0,.12); }}
      .step-pill.done {{ background:#e6f4ea; color:#137333; }}
      @keyframes fadeIn {{ from {{opacity:0; transform:translateY(-3px)}} to {{opacity:1; transform:translateY(0)}} }}
    </style>
    """, unsafe_allow_html=True)

def stepper(steps, current_idx, completed):
    inject_css()
    icons = {
        "Intro":"🎓","Personality":"🧠","Interests":"🎯","Learning":"📚","Academics":"📐",
        "Skills":"🧰","Values & Life":"💖","AI, Creativity & Automation":"🤖",
        "Entrepreneurship":"🚀","Resilience, Ethics & Global":"🧭","Results":"📈","Dashboard":"📊"
    }
    html = "<div>"
    for i, s in enumerate(steps):
        cls = "step-pill current" if i==current_idx else ("step-pill done" if s in completed else "step-pill")
        html += f"<span class='{cls}'>{icons.get(s,'•')} {s}</span>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def photo_banner(slug):
    local = f"assets/photos/{slug}.png"
    if os.path.exists(local): st.image(local, use_column_width=True)

def header(slug, steps, current_idx, completed):
    c1,c2 = st.columns([3,7])
    with c1: st.image("assets/logo.png", width=220)
    with c2: stepper(steps, current_idx, completed)
    photo_banner(slug)

SECTIONS = ["Intro","Personality","Interests","Learning","Academics","Skills","Values & Life",
            "AI, Creativity & Automation","Entrepreneurship","Resilience, Ethics & Global","Results","Dashboard"]
if "responses" not in st.session_state: st.session_state["responses"] = {}
if "completed" not in st.session_state: st.session_state["completed"] = set()
if "current_idx" not in st.session_state: st.session_state["current_idx"] = 0
if "student" not in st.session_state: st.session_state["student"] = {}

current_idx = st.session_state["current_idx"]; completed = st.session_state["completed"]; key = SECTIONS[current_idx]

with st.sidebar:
    st.title("BYC Navigation")
    for i, s in enumerate(SECTIONS):
        prefix = "✅" if s in completed else ("➡️" if i==current_idx else "•")
        st.write(f"{prefix} {s}")
    st.markdown("---")
    blob = json.dumps({"student":st.session_state.get("student",{}),"responses":st.session_state.get("responses",{}),
                       "completed":list(st.session_state.get("completed",set())),"current_idx":st.session_state.get("current_idx",0)})
    st.download_button("⬇️ Save progress (.json)", data=blob, file_name="BYC_progress.json", mime="application/json")
    up = st.file_uploader("⬆️ Load progress (.json)", type=["json"])
    if up is not None:
        data = json.loads(up.getvalue().decode("utf-8"))
        st.session_state["student"] = data.get("student",{})
        st.session_state["responses"] = data.get("responses",{})
        st.session_state["completed"] = set(data.get("completed",[]))
        st.session_state["current_idx"] = data.get("current_idx",0)
        st.success("Progress loaded.")

header(key.split(",")[0].lower().replace(" &","").replace(" ",""), SECTIONS, current_idx, completed)

def radio_pool(pool_key):
    for it in ITEMS.get(pool_key, []):
        st.session_state["responses"][it["id"]] = st.radio(it["text"], [1,2,3,4,5], index=2, horizontal=True, key=it["id"])

if key == "Intro":
    st.subheader("Welcome to BYC Unified Career Assessment")
    with st.form("student_form"):
        c1,c2 = st.columns(2)
        name = c1.text_input("Student name")
        grade = c1.selectbox("Class/Grade", ["8","9","10","11","12","UG-1","UG-2","UG-3"])
        school = c2.text_input("School / College")
        contact = c2.text_input("Contact email / phone (optional)")
        consent = st.checkbox("I agree to share my responses with BookYourCampus for guidance purposes.")
        if st.form_submit_button("Save") and consent:
            st.session_state["student"] = {"name":name,"grade":grade,"school":school,"contact":contact}
            st.success("Saved student info.")
elif key == "Personality":
    st.subheader("🧠 Personality — Big Five"); radio_pool("big5")
elif key == "Interests":
    st.subheader("🎯 Interests — RIASEC"); radio_pool("riasec")
elif key == "Learning":
    st.subheader("📚 Learning Preferences"); radio_pool("learning")
elif key == "Academics":
    st.subheader("📐 Academics"); radio_pool("academic")
elif key == "Skills":
    st.subheader("🧰 Skills"); radio_pool("skills")
elif key == "Values & Life":
    st.subheader("💖 Values & Life"); radio_pool("values"); st.markdown("---"); radio_pool("extracurricular")
elif key == "AI, Creativity & Automation":
    st.subheader("🤖 AI, Creativity & Automation"); radio_pool("ai_future"); st.markdown("---"); radio_pool("creativity")
elif key == "Entrepreneurship":
    st.subheader("🚀 Entrepreneurship"); radio_pool("entrepreneurship")
elif key == "Resilience, Ethics & Global":
    st.subheader("🧭 Resilience, Ethics & Global"); radio_pool("resilience"); st.markdown("---"); radio_pool("ethics_global")
elif key == "Results":
    st.subheader("📈 Results")
    big5 = score_pool("big5","trait"); ria = score_pool("riasec","domain")
    learn = score_pool("learning","modality"); acad = score_pool("academic","subject")
    skl = score_pool("skills","skill"); val = score_pool("values","value")
    ai = score_pool("ai_future","facet"); cre = score_pool("creativity","facet")
    ent = score_pool("entrepreneurship","facet"); res = score_pool("resilience","facet"); eth = score_pool("ethics_global","facet")

    def radar_fig(d, title):
        if not d: return go.Figure()
        labels = list(d.keys()); values = list(norm_scores(d).values())
        values += values[:1]; labels += labels[:1]
        fig = go.Figure(); fig.add_trace(go.Scatterpolar(r=values, theta=labels, fill='toself', name=title))
        fig.update_layout(title=title, margin=dict(l=0,r=0,t=40,b=0)); return fig
    c1,c2 = st.columns(2)
    c1.plotly_chart(radar_fig(big5, "Personality (Big Five)"), use_container_width=True)
    c2.plotly_chart(radar_fig(ria, "Interests (RIASEC)"), use_container_width=True)

    clusters = composite_cluster_scores({"riasec": ria, "big5": big5, "academic": acad, "skills": skl, "values": val,
        "ai_future": ai, "creativity": cre, "entrepreneurship": ent, "resilience": res, "ethics_global": eth})
    top = clusters[:5]; labels = [x["cluster"] for x in top]; values = [x["percent"] for x in top]
    donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
    donut.update_layout(title="Top Career Clusters (relative)", margin=dict(l=0,r=0,t=40,b=0)); st.plotly_chart(donut, use_container_width=True)

    parts = [norm_scores(x) for x in [ai, cre, ent, res, eth]]
    avg = sum([(sum(d.values())/len(d) if d else 0) for d in parts]) / (len(parts) if parts else 1)
    ff = int(round(100*avg))
    gauge = go.Figure(go.Indicator(mode="gauge+number", value=ff, title={"text":"FutureFit Index"}, gauge={"axis":{"range":[0,100]}}))
    st.plotly_chart(gauge, use_container_width=True)

    st.markdown("### Recommendations")
    for i, r in enumerate(top, start=1):
        with st.expander(f"{i}. {r['cluster']} — {r['percent']}% fit"):
            st.write(r["description"]); st.write("**Next steps**"); 
            for s in r["suggestions"]: st.write("- " + s)

    os.makedirs("data", exist_ok=True)
    if st.button("Save my responses to cohort (CSV)"):
        row = {"timestamp": datetime.datetime.now().isoformat(), "name": st.session_state.get("student",{}).get("name","")}
        for d, prefix in [(big5,"BIG5"),(ria,"RIASEC"),(learn,"LEARN"),(acad,"ACAD"),(skl,"SKILL"),(val,"VALUE"),
                          (ai,"AI"),(cre,"CRE"),(ent,"ENT"),(res,"RES"),(eth,"ETH")]:
            for k,v in d.items(): row[f"{prefix}_{k}"] = v
        row["TopCluster"] = top[0]["cluster"] if top else ""
        row["FutureFit"] = ff
        import pandas as pd
        df = pd.DataFrame([row]); fp = "data/responses.csv"
        if os.path.exists(fp):
            old = pd.read_csv(fp); pd.concat([old, df], ignore_index=True).to_csv(fp, index=False)
        else:
            df.to_csv(fp, index=False)
        st.success("Saved to data/responses.csv")

elif key == "Dashboard":
    st.subheader("📊 Cohort Dashboard")
    fp = "data/responses.csv"
    if not os.path.exists(fp):
        st.info("No cohort data yet. Save some results from the Results page.")
    else:
        import pandas as pd
        df = pd.read_csv(fp); st.dataframe(df.tail(100))
        if "TopCluster" in df.columns:
            counts = df["TopCluster"].value_counts().reset_index()
            fig = go.Figure(data=[go.Bar(x=counts["index"], y=counts["TopCluster"])])
            fig.update_layout(title="Top Cluster Distribution", xaxis_title="", yaxis_title="Students")
            st.plotly_chart(fig, use_container_width=True)
        if "FutureFit" in df.columns:
            try:
                df["timestamp"]=pd.to_datetime(df["timestamp"])
                trend = df.groupby(df["timestamp"].dt.date)["FutureFit"].mean().reset_index()
                fig2 = go.Figure(data=[go.Scatter(x=trend["timestamp"], y=trend["FutureFit"], mode='lines+markers')])
                fig2.update_layout(title="Average FutureFit Over Time", xaxis_title="Date", yaxis_title="FutureFit")
                st.plotly_chart(fig2, use_container_width=True)
            except Exception as e:
                st.write("Trend not available:", e)

st.markdown("---")
c1,c2 = st.columns([1,2])
with c1:
    if st.button("💾 Save (server)"):
        os.makedirs("data", exist_ok=True)
        with open("data/_autosave.json","w",encoding="utf-8") as f:
            json.dump({"student":st.session_state.get("student",{}),"responses":st.session_state.get("responses",{}),
                       "completed":list(st.session_state.get("completed",set())),
                       "current_idx":st.session_state.get("current_idx",0)}, f, ensure_ascii=False)
        st.success("Saved (server session).")
with c2:
    if key not in ["Results","Dashboard"]:
        if st.button("➡️ Save & Continue to Next"):
            st.session_state["completed"].add(key)
            if st.session_state["current_idx"] < len(SECTIONS)-1:
                st.session_state["current_idx"] += 1
            st.experimental_rerun()
