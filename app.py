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

uploaded_files =_
