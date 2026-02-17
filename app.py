import streamlit as st
import pdfplumber
import docx
import pandas as pd
import json
import re
from collections import Counter
from pathlib import Path

st.set_page_config(layout="wide")
st.title("📊 Consolidated Report Generator")

# =============================
# BLOCK SELECTOR
# =============================

selected_block = st.selectbox(
    "Select School Block",
    [
        "Primary (I-II)",
        "Primary (III-V)",
        "Middle School (VI-VIII)",
        "Senior School (IX-X)",
        "Senior Secondary (XI-XII)"
    ]
)

# =============================
# FILE UPLOAD
# =============================

uploaded_files = st.file_uploader(
    "Upload up to 80 Teacher Reports",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if uploaded_files and len(uploaded_files) > 80:
    st.error("Maximum 80 files allowed.")
    st.stop()

# =============================
# TEXT EXTRACTION
# =============================

def extract_text(file):
    if file.type == "application/pdf":
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        return text
    else:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

# =============================
# SMART PARSER
# =============================

def parse_report(text):

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    text_lower = text.lower()

    data = {
        "id": "",
        "name": "",
        "subject": "",
        "classes": "",
        "initials": "",
        "color": "blue",
        "rating": 4.5,
        "overview": "",
        "glows": [],
        "grows": [],
        "plan": "",
        "competency": [4,4,4,4,4],
        "talk": {"teacher": 50, "student": 50}
    }

    for line in lines:
        if "teacher name" in line.lower():
            data["name"] = line.split(":")[-1].strip()
            break

    if not data["name"]:
        for line in lines[:10]:
            if any(p in line for p in ["Mr.", "Ms.", "Mrs.", "Miss"]):
                data["name"] = line.strip()
                break

    data["initials"] = "".join([w[0] for w in data["name"].split()[:2]]).upper()

    for line in lines:
        if "subject" in line.lower():
            data["subject"] = line.split(":")[-1].strip()
            break

    talk_pattern = re.findall(r'(\d+)\s*%', text)
    if len(talk_pattern) >= 2:
        data["talk"]["teacher"] = int(talk_pattern[0])
        data["talk"]["student"] = int(talk_pattern[1])

    glow_keywords = ["glows", "strengths"]
    grow_keywords = ["grows", "improvement"]

    current = None

    for line in lines:
        lower = line.lower()

        if any(k in lower for k in glow_keywords):
            current = "glows"
            continue

        if any(k in lower for k in grow_keywords):
            current = "grows"
            continue

        bullet = re.match(r'^(\d+[\.\)]|\-|•)\s*(.*)', line)
        if bullet and current:
            data[current].append(bullet.group(2).strip())

    return data

# =============================
# TEMPLATE LOAD
# =============================

def load_template():
    return Path("templates/consolidated_template.html").read_text()

# =============================
# GENERATE HTML
# =============================

def generate_html(df):

    template = load_template()

    total = len(df)
    avg_rating = round(df["rating"].mean(), 2)
    avg_student = round(df["talk"].apply(lambda x: x["student"]).mean(), 1)

    all_glows = []
    for g in df["glows"]:
        all_glows.extend(g)

    most_common = Counter(all_glows).most_common(1)[0][0] if all_glows else "N/A"

    template = template.replace("{{TOTAL_TEACHERS}}", str(total))
    template = template.replace("{{AVG_RATING}}", str(avg_rating))
    template = template.replace("{{AVG_STUDENT_TALK}}", str(avg_student))
    template = template.replace("{{MOST_COMMON_GLOW}}", most_common)
    template = template.replace("{{SCHOOL_BLOCK}}", selected_block)
    template = template.replace("{{TEACHER_DATA_JSON}}", json.dumps(df.to_dict(orient="records")))

    return template

# =============================
# MAIN
# =============================

if uploaded_files and st.button("Generate Final Dashboard"):

    reports = []

    for file in uploaded_files:
        raw = extract_text(file)
        structured = parse_report(raw)
        reports.append(structured)

    df = pd.DataFrame(reports)

    final_html = generate_html(df)

    st.success("Dashboard Generated Successfully")

    st.download_button(
        "Download Final Dashboard HTML",
        final_html,
        file_name="consolidated_dashboard.html",
        mime="text/html"
    )
