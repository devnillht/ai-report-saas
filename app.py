import streamlit as st
import pdfplumber
import docx
import pandas as pd
import json
from collections import Counter
from pathlib import Path

st.set_page_config(layout="wide")
st.title("📊 Consolidated Report Generator (III–V Format)")

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
                text += page.extract_text() + "\n"
        return text
    else:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

# =============================
# STRUCTURED PARSING (NO AI)
# =============================

def parse_report(text):

    lines = text.split("\n")
    data = {
        "teacher_name": "",
        "subject": "",
        "rating": 4.5,
        "glows": [],
        "grows": [],
        "teacher_talk_percentage": 50,
        "student_talk_percentage": 50
    }

    for i, line in enumerate(lines):

        if "Teacher Name" in line:
            data["teacher_name"] = line.split(":")[-1].strip()

        if "Subject" in line:
            data["subject"] = line.split(":")[-1].strip()

        if "Teacher Talk" in line:
            value = line.split(":")[-1].replace("%","").strip()
            if value.isdigit():
                data["teacher_talk_percentage"] = int(value)

        if "Student Talk" in line:
            value = line.split(":")[-1].replace("%","").strip()
            if value.isdigit():
                data["student_talk_percentage"] = int(value)

        if "Glows" in line or "GLOWS" in line:
            j = i + 1
            while j < len(lines) and lines[j].strip() != "":
                data["glows"].append(lines[j].strip())
                j += 1

        if "Grows" in line or "GROWS" in line:
            j = i + 1
            while j < len(lines) and lines[j].strip() != "":
                data["grows"].append(lines[j].strip())
                j += 1

    return data

# =============================
# TEMPLATE LOADING
# =============================

def load_template():
    return Path("templates/consolidated_template.html").read_text()

# =============================
# HTML GENERATOR
# =============================

def generate_final_html(df):

    template = load_template()

    total_teachers = len(df)
    avg_rating = round(df["rating"].mean(), 2)
    avg_student_talk = round(df["student_talk_percentage"].mean(), 1)

    all_glows = []
    for glows in df["glows"]:
        all_glows.extend(glows)

    most_common_glow = Counter(all_glows).most_common(1)[0][0] if all_glows else "N/A"

    template = template.replace("{{TOTAL_TEACHERS}}", str(total_teachers))
    template = template.replace("{{AVG_RATING}}", str(avg_rating))
    template = template.replace("{{AVG_STUDENT_TALK}}", str(avg_student_talk))
    template = template.replace("{{MOST_COMMON_GLOW}}", most_common_glow)

    teacher_json = df.to_dict(orient="records")
    template = template.replace("{{TEACHER_DATA_JSON}}", json.dumps(teacher_json))

    return template

# =============================
# MAIN
# =============================

if uploaded_files and st.button("Generate Final Dashboard Report"):

    reports = []

    for file in uploaded_files:
        raw = extract_text(file)
        structured = parse_report(raw)
        reports.append(structured)

    df = pd.DataFrame(reports)

    final_html = generate_final_html(df)

    st.success("Dashboard Generated Successfully")

    st.download_button(
        "Download Final Consolidated HTML",
        final_html,
        file_name="consolidated_dashboard_report.html",
        mime="text/html"
    )
