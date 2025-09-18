import streamlit as st
import xml.etree.ElementTree as ET

# ------------------------------
# Levenshtein distance helpers
# ------------------------------
def levenshtein(a, b):
    """Compute Levenshtein distance between two strings."""
    if len(a) < len(b):
        return levenshtein(b, a)
    if len(b) == 0:
        return len(a)

    prev_row = range(len(b) + 1)
    for i, c1 in enumerate(a):
        curr_row = [i + 1]
        for j, c2 in enumerate(b):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def calculate_change_percent(mt_texts, pe_texts):
    """Compute average change % between MT and PE texts."""
    total_distance = 0
    total_length = 0

    for mt, pe in zip(mt_texts, pe_texts):
        distance = levenshtein(mt, pe)
        total_distance += distance
        total_length += max(len(mt), len(pe))

    if total_length == 0:
        return 0.0

    return (total_distance / total_length) * 100


def parse_xliff(uploaded_file):
    """Extract <source> and <target> segments from XLIFF/MXLIFF."""
    try:
        tree = ET.parse(uploaded_file)
        root = tree.getroot()
        ns = {"x": "urn:oasis:names:tc:xliff:document:1.2"}

        sources, targets = [], []
        for unit in root.findall(".//x:trans-unit", ns):
            source = unit.find("x:source", ns)
            target = unit.find("x:target", ns)
            if source is not None and target is not None:
                sources.append(source.text or "")
                targets.append(target.text or "")
        return sources, targets
    except Exception as e:
        st.error(f"❌ Failed to parse XLIFF: {e}")
        return [], []


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
            change_percent = calculate_change_percent(sources, targets)
            st.success(f"✅ Change Percentage for project `{project_uid}`: {change_percent:.2f}%")
        else:
            st.warning("⚠️ No translatable segments found in the XLIFF.")
