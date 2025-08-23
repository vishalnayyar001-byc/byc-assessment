
import json, os, io, base64, datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="BookYourCampus — Unified Career Assessment", page_icon="🎓", layout="wide")
PRIMARY = "#c62828"
ACCENT = "#0d47a1"

# ---------- UI helpers ----------
def byc_header():
    col1, col2 = st.columns([1,4])
    with col1:
        st.image("assets/logo.png", use_column_width=True)
    with col2:
        st.markdown(f"<h2 style='margin-bottom:0;color:{ACCENT}'>Unified Career Assessment</h2>", unsafe_allow_html=True)
        st.markdown("<p style='margin-top:0'>Interests • Personality • Learning • Academics • Skills • Values • Future‑Readiness → Career Fit</p>", unsafe_allow_html=True)
    st.markdown("---")

@st.cache_data
def load_items():
    with open("assessment/items.json","r", encoding="utf-8") as f:
        return json.load(f)
@st.cache_data
def load_mapping():
    with open("assessment/mapping.json","r", encoding="utf-8") as f:
        return json.load(f)

ITEMS = load_items()
MAPPING = load_mapping()

def ensure_dir(p):
    if not os.path.exists(p):
        os.makedirs(p, exist_ok=True)

def scale_radio(scale, label, key):
    if scale=="likert":
        labels = ["1 - Strongly Disagree","2 - Disagree","3 - Neutral","4 - Agree","5 - Strongly Agree"]
    elif scale=="like":
        labels = ["1 - Dislike","2 - Slightly Dislike","3 - Neutral","4 - Like","5 - Strongly Like"]
    elif scale=="freq":
        labels = ["1 - Rarely","2 - Occasionally","3 - Sometimes","4 - Often","5 - Very Often"]
    elif scale=="self":
        labels = ["1 - Very Low","2 - Low","3 - Medium","4 - High","5 - Very High"]
    elif scale=="importance":
        labels = ["1 - Not Important","2 - Slightly","3 - Moderately","4 - Very","5 - Extremely"]
    else:
        labels = ["1","2","3","4","5"]
    return st.radio(label, [1,2,3,4,5], index=2, format_func=lambda x: labels[x-1], horizontal=True, key=key)

def norm_scores(d):
    if not d: return {}
    mx = max(d.values()) if max(d.values())>0 else 1
    return {k:v/mx for k,v in d.items()}

# ---------- Scoring helpers ----------
def score_section(section_key, attr_field, reverse_key="reverse", default=3):
    scores = {}
    for it in ITEMS.get(section_key, []):
        raw = st.session_state["responses"].get(it["id"], default)
        if it.get(reverse_key):
            raw = 6-raw
        k = it[attr_field]
        scores[k] = scores.get(k, 0) + raw
    return scores

def composite_cluster_scores(domains):
    # domains is a dict of section-name -> dict scores
    normalized = {k: norm_scores(v) for k,v in domains.items()}
    results = []
    for c in MAPPING["clusters"]:
        total = 0.0
        w = c["weights"]
        for group, weights in w.items():
            group_scores = normalized.get(group, {})
            for facet, wt in weights.items():
                total += wt * group_scores.get(facet, 0.0)
        results.append({
            "cluster": c["name"],
            "score": round(total, 5),
            "description": c["description"],
            "suggestions": c["suggestions"]
        })
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    mx = results[0]["score"] if results and results[0]["score"]>0 else 1.0
    for r in results:
        r["percent"] = int(round(100 * (r["score"]/mx)))
    return results

def bar_chart(data, title):
    fig, ax = plt.subplots(figsize=(6,3.5))
    keys = list(data.keys())
    vals = [data[k] for k in keys]
    ax.bar(keys, vals)
    ax.set_title(title)
    ax.set_xticklabels(keys, rotation=30, ha="right")
    return fig

def report(student, charts, clusters, futurefit):
    # Build minimal HTML report with embedded charts
    def fig_to_b64(fig):
        buf = io.BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight"); buf.seek(0)
        import base64; return base64.b64encode(buf.read()).decode("utf-8")
    b64s = [fig_to_b64(fig) for fig in charts]
    today = datetime.date.today().strftime("%b %d, %Y")
    html = f"""
    <html><head><meta charset='utf-8'><title>BYC Assessment Report</title></head>
    <body style="font-family:Arial;margin:24px">
      <h1 style="color:{ACCENT}">BookYourCampus — Unified Career Assessment</h1>
      <p>Generated on {today}</p>
      <h3>Student</h3>
      <p><b>Name:</b> {student.get('name','-')} &nbsp; | &nbsp; <b>Class:</b> {student.get('grade','-')} &nbsp; | &nbsp; <b>School:</b> {student.get('school','-')}</p>
      <h3>Visual Summary</h3>
      {"".join([f"<img src='data:image/png;base64,{b}' style='max-width:48%;margin:6px'/>" for b in b64s])}
      <h3>FutureFit</h3>
      <p><b>FutureFit Index:</b> {futurefit}% — combines AI & Automation, Creativity, Entrepreneurship, Resilience, Ethics/Global.</p>
      <h3>Top Recommendations</h3>
      {"".join([f"<p><b>{i+1}. {c['cluster']}</b> — {c['percent']}% fit<br><i>{c['description']}</i></p><ul>" + "".join([f"<li>{s}</li>" for s in c['suggestions']]) + "</ul>" for i,c in enumerate(clusters[:5])])}
      <p style="color:#666">This report blends interests, personality, learning, academics, skills, values, and future‑readiness to guide choices. Use alongside marks, projects, and counseling.</p>
    </body></html>"""
    return html

# ---------- Pages ----------
def page_intro():
    byc_header()
    st.markdown(f"<h3 style='color:{ACCENT}'>Welcome!</h3>", unsafe_allow_html=True)
    st.write("This assessment blends your **Interests**, **Personality**, **Learning Preferences**, **Academics**, **Skills**, **Values**, and **Future‑Readiness** to recommend **career clusters**. It takes ~15–20 minutes.")
    with st.form("student_info"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Student name")
        grade = c1.selectbox("Class/Grade", ["8","9","10","11","12","UG - 1st year","UG - 2nd year","UG - 3rd year"])
        school = c2.text_input("School / College")
        country = c2.text_input("Preferred study destination (optional)")
        contact = st.text_input("Contact email / phone (optional)")
        consent = st.checkbox("I agree to share my responses with BookYourCampus for guidance purposes.")
        submitted = st.form_submit_button("Save & Continue")
        if submitted and consent:
            st.session_state["student"] = {"name":name,"grade":grade,"school":school,"country":country,"contact":contact}
            st.success("Saved. Use the sidebar to continue.")
        elif submitted:
            st.warning("Please provide consent to proceed.")

def page_render(section_key, title, caption, attr_field, scale):
    byc_header()
    st.subheader(title)
    st.caption(caption)
    cols = st.columns(1)
    for it in ITEMS.get(section_key, []):
        key = it["id"]
        st.session_state["responses"][key] = scale_radio(scale, it["text"], key)

def page_results():
    byc_header()
    st.subheader("Your Results")

    # Calculate all sections
    big5 = score_section("big5", "trait")
    ria  = score_section("riasec", "domain", reverse_key=None)  # no reverse
    learn = score_section("learning", "modality", reverse_key=None)
    academic = score_section("academic", "subject", reverse_key=None)
    skills = score_section("skills", "skill", reverse_key=None)
    values = score_section("values", "value", reverse_key=None)
    ai = score_section("ai_future", "facet", reverse_key=None)
    creat = score_section("creativity", "facet", reverse_key=None)
    entre = score_section("entrepreneurship", "facet", reverse_key=None)
    resil = score_section("resilience", "facet", reverse_key=None)
    ethics = score_section("ethics_global", "facet", reverse_key=None)
    extra = score_section("extracurricular", "area", reverse_key=None)

    domains = {
        "big5": big5, "riasec": ria, "learning": learn, "academic": academic, "skills": skills, "values": values,
        "ai_future": ai, "creativity": creat, "entrepreneurship": entre, "resilience": resil, "ethics_global": ethics,
        "extracurricular": extra
    }

    # Charts
    chart_list = []
    for title, data in [
        ("Personality (Big Five)", big5),
        ("Interests (RIASEC)", ria),
        ("Learning Preferences", learn),
        ("Academics", academic),
        ("Skills", skills),
        ("Work Values", values),
        ("AI & Automation Readiness", ai),
        ("Digital Creativity", creat),
        ("Entrepreneurship Mindset", entre),
        ("Resilience & Adaptability", resil),
        ("Ethics & Global Mindset", ethics),
    ]:
        fig = bar_chart(data, title)
        st.pyplot(fig, use_container_width=True)
        chart_list.append(fig)

    # Composite
    clusters = composite_cluster_scores({
        "riasec": ria, "big5": big5, "academic": academic, "skills": skills, "values": values,
        "ai_future": ai, "creativity": creat, "entrepreneurship": entre, "resilience": resil, "ethics_global": ethics
    })
    st.markdown("### Recommended Career Clusters")
    for i, r in enumerate(clusters[:5], start=1):
        with st.expander(f"{i}. {r['cluster']} — {r['percent']}% fit"):
            st.write(r["description"])
            st.write("**Suggested next steps:**")
            for s in r["suggestions"]:
                st.write("- " + s)

    # FutureFit index (simple aggregate)
    ff_parts = [norm_scores(x) for x in [ai, creat, entre, resil, ethics]]
    ff_avg = 0.0
    count = 0
    for d in ff_parts:
        if d:
            ff_avg += sum(d.values())/len(d)
            count += 1
    futurefit = int(round(100 * (ff_avg / count))) if count>0 else 0
    st.info(f"**FutureFit Index:** {futurefit}%  — combines AI & Automation, Creativity, Entrepreneurship, Resilience, Ethics/Global.")
    
    # Export report
    if st.button("Export Report (HTML → print to PDF)"):
        html = report(st.session_state.get("student", {}), chart_list[:4], clusters, futurefit)
        ensure_dir("exports")
        fname = f"exports/BYC_Assessment_Report_{st.session_state.get('student',{}).get('name','Student').replace(' ','_')}.html"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(html)
        with open(fname, "rb") as f:
            import base64; b64 = base64.b64encode(f.read()).decode()
        st.download_button("Download Report", data=b64, file_name=os.path.basename(fname), mime="text/html")

    # Save CSV (demo)
    ensure_dir("data")
    if st.button("Save my responses (CSV)"):
        row = {"timestamp": datetime.datetime.now().isoformat(), **{f"BIG5_{k}": v for k,v in big5.items()}}
        row.update({f"RIASEC_{k}": v for k,v in ria.items()})
        row.update({f"LEARN_{k}": v for k,v in learn.items()})
        row.update({f"ACAD_{k}": v for k,v in academic.items()})
        row.update({f"SKILL_{k}": v for k,v in skills.items()})
        row.update({f"VALUE_{k}": v for k,v in values.items()})
        row.update({f"AI_{k}": v for k,v in ai.items()})
        row.update({f"CRE_{k}": v for k,v in creat.items()})
        row.update({f"ENT_{k}": v for k,v in entre.items()})
        row.update({f"RES_{k}": v for k,v in resil.items()})
        row.update({f"ETH_{k}": v for k,v in ethics.items()})
        row.update({f"XC_{k}": v for k,v in extra.items()})
        df = pd.DataFrame([row])
        fp = "data/responses.csv"
        if os.path.exists(fp):
            df_old = pd.read_csv(fp); df_all = pd.concat([df_old, df], ignore_index=True); df_all.to_csv(fp, index=False)
        else:
            df.to_csv(fp, index=False)
        st.success("Saved to data/responses.csv (for demo).")

# ---------- App entry ----------
if "responses" not in st.session_state:
    st.session_state["responses"] = {}

st.sidebar.title("Assessment Steps")
page = st.sidebar.radio("Navigate", [
    "Intro",
    "Personality",
    "Interests",
    "Learning",
    "Academics",
    "Skills",
    "Values",
    "AI & Automation",
    "Digital Creativity",
    "Entrepreneurship",
    "Resilience",
    "Ethics & Global",
    "Extracurriculars",
    "Results"
])

if page == "Intro": page_intro()
elif page == "Personality": page_render("big5","Personality — Big Five (IPIP‑style)","Rate each statement honestly. There are no right/wrong answers.","trait","likert")
elif page == "Interests": page_render("riasec","Interests — RIASEC","How much do you enjoy these activities?","domain","like")
elif page == "Learning": page_render("learning","Learning Preferences","How often do these match your style?","modality","freq")
elif page == "Academics": page_render("academic","Academic Comfort","Self‑rate your current comfort or interest level.","subject","self")
elif page == "Skills": page_render("skills","Skills & Self‑Ratings","Self‑rate your current comfort or interest level.","skill","self")
elif page == "Values": page_render("values","Work Values","How important are these to you?","value","importance")
elif page == "AI & Automation": page_render("ai_future","AI & Automation Readiness","Your relationship with AI/automation and data.","facet","likert")
elif page == "Digital Creativity": page_render("creativity","Digital Creativity","Your creative habits and making.","facet","likert")
elif page == "Entrepreneurship": page_render("entrepreneurship","Entrepreneurship Mindset","Spotting opportunities and getting things done.","facet","likert")
elif page == "Resilience": page_render("resilience","Resilience & Adaptability","How you handle change and challenge.","facet","likert")
elif page == "Ethics & Global": page_render("ethics_global","Ethics & Global Mindset","Responsible, inclusive, sustainable choices.","facet","likert")
elif page == "Extracurriculars": page_render("extracurricular","Extracurriculars","Participation beyond academics.","area","freq")
else: page_results()
