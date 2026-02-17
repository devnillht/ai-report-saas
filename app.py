import streamlit as st
import pdfplumber
import docx
import google.generativeai as genai
import pandas as pd
import json
from collections import Counter
from pathlib import Path

# =============================
# CONFIG
# =============================

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("models/gemini-1.0-pro")

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
# AI STRUCTURED PARSING
# =============================

def parse_with_ai(text):

    prompt = f"""
Extract structured JSON from this teacher observation.

Return ONLY valid JSON:

{{
  "teacher_name": "",
  "subject": "",
  "rating": 4.5,
  "glows": [],
  "grows": [],
  "teacher_talk_percentage": 50,
  "student_talk_percentage": 50
}}

Report:
{text}
"""

    response = model.generate_content(prompt)
    return json.loads(response.text)

# =============================
# TEMPLATE LOADING
# =============================

def load_template():
    template_path = Path("templates/consolidated_template.html")
    return template_path.read_text()

# =============================
# HTML INJECTION ENGINE
# =============================

def generate_final_html(df):

    template = load_template()

    total_teachers = len(df)
    avg_rating = round(df["rating"].mean(), 2)
    avg_student_talk = round(df["student_talk_percentage"].mean(), 1)

    all_glows = []
    for glows in df["glows"]:
        all_glows.extend(glows)

    most_common_glow = Counter(all_glows).most_common(1)[0][0]

    # Replace placeholders
    template = template.replace("{{TOTAL_TEACHERS}}", str(total_teachers))
    template = template.replace("{{AVG_RATING}}", str(avg_rating))
    template = template.replace("{{AVG_STUDENT_TALK}}", str(avg_student_talk))
    template = template.replace("{{MOST_COMMON_GLOW}}", most_common_glow)

    # Inject Teacher JSON
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
        structured = parse_with_ai(raw)
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


