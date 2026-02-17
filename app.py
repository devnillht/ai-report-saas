import streamlit as st
import pdfplumber
import docx
import pandas as pd
import json
import re
from collections import Counter
from pathlib import Path

# =============================
# PAGE CONFIG
# =============================

st.set_page_config(layout="wide")
st.title("📊 Consolidated Report Generator")

# =============================
# SCHOOL BLOCK SELECTOR
# =============================

st.subheader("Select School Block / Section")

selected_block = st.selectbox(
    "Select the school block...",
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
    "Upload up to 80 Teacher Reports (PDF/DOCX)",
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
# SMART PARSER (EDGE-CASE READY)
# =============================

def parse_report(text):

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    text_lower = text.lower()

    data = {
        "teacher_name": "",
        "subject": "",
        "rating": 4.5,
        "glows": [],
        "grows": [],
        "teacher_talk_percentage": 50,
        "student_talk_percentage": 50
    }

    # --- Teacher Name ---
    for line in lines:
        if "teacher name" in line.lower() or "name of teacher" in line.lower():
            data["teacher_name"] = line.split(":")[-1].strip()
            break

    if not data["teacher_name"]:
        for line in lines[:10]:
            if any(prefix in line for prefix in ["Mr.", "Ms.", "Mrs.", "Miss"]):
                data["teacher_name"] = line.strip()
                break

    # --- Subject ---
    for line in lines:
        if "subject" in line.lower():
            data["subject"] = line.split(":")[-1].strip()
            break

    # --- Talk Ratio ---
    talk_pattern = re.findall(r'(\d+)\s*%', text)
    if len(talk_pattern) >= 2:
        data["teacher_talk_percentage"] = int(talk_pattern[0])
        data["student_talk_percentage"] = int(talk_pattern[1])

    # --- Glows & Grows ---
    glow_keywords = ["glows", "strengths", "strong points"]
    grow_keywords = ["grows", "areas for improvement", "improvement", "action points"]

    current_section = None

    for line in lines:
        lower = line.lower()

        if any(k in lower for k in glow_keywords):
            current_section = "glows"
            continue

        if any(k in lower for k in grow_keywords):
            current_section = "grows"
            continue

        bullet_match = re.match(r'^(\d+[\.\)]|\-|•)\s*(.*)', line)
        if bullet_match and current_section:
            content = bullet_match.group(2).strip()
            if content:
                data[current_section].append(content)
            continue

        if current_section and len(line) > 5 and not any(k in lower for k in glow_keywords + grow_keywords):
            data[current_section].append(line)

    # --- Auto Rating Based on Positive Language ---
    positive_words = ["excellent", "strong", "effective", "confident", "engaging"]
    score = sum(word in text_lower for word in positive_words)

    if score >= 4:
        data["rating"] = 4.8
    elif score >= 2:
        data["rating"] = 4.5
    else:
        data["rating"] = 4.2

    return data

# =============================
# LOAD TEMPLATE
# =============================

def load_template():
    return Path("templates/consolidated_template.html").read_text()

# =============================
# GENERATE FINAL HTML
# =============================

def generate_final_html(df, selected_block):

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
    template = template.replace("{{SCHOOL_BLOCK}}", selected_block)

    teacher_json = df.to_dict(orient="records")
    template = template.replace("{{TEACHER_DATA_JSON}}", json.dumps(teacher_json))

    return template

# =============================
# MAIN EXECUTION
# =============================

if uploaded_files and st.button("Generate Final Dashboard Report"):

    reports = []

    for file in uploaded_files:
        raw = extract_text(file)
        structured = parse_report(raw)
        reports.append(structured)

    df = pd.DataFrame(reports)

    final_html = generate_final_html(df, selected_block)

    st.success("Dashboard Generated Successfully")

    st.download_button(
        "Download Final Consolidated HTML",
        final_html,
        file_name="consolidated_dashboard_report.html",
        mime="text/html"
    )
