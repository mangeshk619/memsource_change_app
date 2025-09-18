import streamlit as st
import xml.etree.ElementTree as ET
import re
from rapidfuzz import fuzz

# ------------------------------
# Helper functions
# ------------------------------

def clean_text(text):
    """Remove placeholders/tags and normalize whitespace."""
    if not text:
        return ""
    # Remove inline tags like <ph id="1"/>, <x id="1"/>
    text = re.sub(r"<[^>]+>", "", text)
    # Normalize whitespace
    text = " ".join(text.split())
    return text


def parse_xliff(uploaded_file):
    """Extract and clean <source> and <target> segments from XLIFF/MXLIFF."""
    try:
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        ns = {"x": "urn:oasis:names:tc:xliff:document:1.2"}

        sources, targets = [], []
        for unit in root.findall(".//x:trans-unit", ns):
            source = unit.find("x:source", ns)
            target = unit.find("x:target", ns)
            if source is not None and target is not None:
                sources.append(clean_text(source.text))
                targets.append(clean_text(target.text))
        return sources, targets
    except Exception as e:
        st.error(f"❌ Failed to parse XLIFF: {e}")
        return [], []


def calculate_change_percent_rapidfuzz(mt_texts, pe_texts):
    """Compute Change % using RapidFuzz similarity."""
    if not mt_texts or not pe_texts or len(mt_texts) != len(pe_texts):
        return 0.0

    total_similarity = 0
    for mt, pe in zip(mt_texts, pe_texts):
        score = fuzz.ratio(mt, pe)  # 0-100 similarity
        total_similarity += score

    avg_similarity = total_similarity / len(mt_texts)
    change_percent = 100 - avg_similarity
    return change_percent


# ------------------------------
# Streamlit UI
# ------------------------------
st.title("Memsource Legacy PE Change % Tool 🚀")

st.info("For legacy Memsource tenants, projects cannot be fetched via API. Paste the Project UID manually.")

# Step 1: Enter Project UID
project_uid = st.text_input("📂 Enter Project UID (from Memsource URL)")

if project_uid:
    st.write(f"Project UID: `{project_uid}`")

    # Step 2: Upload PE XLIFF/MXLIFF
    uploaded_file = st.file_uploader("📤 Upload Post-Edited XLIFF/MXLIFF", type=["xliff", "mxliff"])
    
    if uploaded_file:
        sources, targets = parse_xliff(uploaded_file)
        if sources and targets:
            change_percent = calculate_change_percent_rapidfuzz(sources, targets)
            st.success(f"✅ Change Percentage for project `{project_uid}`: {change_percent:.2f}%")
        else:
            st.warning("⚠️ No translatable segments found in the XLIFF.")
