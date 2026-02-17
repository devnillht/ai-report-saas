import streamlit as st
import pdfplumber
import docx
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import json
from collections import Counter

# =============================
# CONFIG
# =============================

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(layout="wide")
st.title("📊 AI Consolidated Report Generator")

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
                text += page.extract_text() + "\n"
        return text
    else:
        doc = docx.Document(file)
        return "\n".join([p.text for p in doc.paragraphs])

# =============================
# AI PARSING
# =============================

def parse_with_ai(text):

    prompt = f"""
Extract structured JSON from this teacher observation report.

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
# MAIN PROCESS
# =============================

if uploaded_files and st.button("Generate Consolidated Report"):

    reports = []

    for file in uploaded_files:
        raw = extract_text(file)
        structured = parse_with_ai(raw)
        reports.append(structured)

    df = pd.DataFrame(reports)

    # =============================
    # ANALYTICS
    # =============================

    avg_rating = df["rating"].mean()
    avg_student_talk = df["student_talk_percentage"].mean()

    all_glows = []
    for glows in df["glows"]:
        all_glows.extend(glows)

    most_common_glow = Counter(all_glows).most_common(1)[0][0]

    st.subheader("📌 Key Metrics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Teachers", len(df))
    col2.metric("Average Rating", round(avg_rating, 2))
    col3.metric("Avg Student Talk %", round(avg_student_talk, 1))

    st.success(f"Most Frequent Strength: {most_common_glow}")

    # =============================
    # CHART
    # =============================

    glow_counts = Counter(all_glows)
    chart_df = pd.DataFrame(glow_counts.items(), columns=["Strength", "Count"])

    fig = px.bar(chart_df, x="Count", y="Strength", orientation="h")
    st.plotly_chart(fig, use_container_width=True)

    # =============================
    # EXPORT HTML
    # =============================

    html_output = df.to_html()

    st.download_button(
        "Download Raw HTML Data",
        html_output,
        file_name="consolidated_report.html"
    )
