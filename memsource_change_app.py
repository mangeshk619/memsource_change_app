import streamlit as st
import requests
import xml.etree.ElementTree as ET

# ------------------------------
# Config
# ------------------------------
API_TOKEN = st.secrets.get("MEMSOURCE_API_TOKEN")
BASE_URL = "https://cloud.memsource.com/web/api2"  # Legacy Memsource API

# ------------------------------
# Helpers
# ------------------------------
def get_headers():
    if not API_TOKEN:
        st.error("❌ No API token found. Please add MEMSOURCE_API_TOKEN in Streamlit secrets.")
        return None
    return {"Authorization": f"ApiToken {API_TOKEN}"}


def list_projects(page_size=20):
    headers = get_headers()
    if not headers:
        return []

    url = f"{BASE_URL}/projects"
    response = requests.get(url, headers=headers, params={"pageSize": page_size})
    response.raise_for_status()
    return response.json().get("content", [])


def list_jobs(project_uid):
    headers = get_headers()
    if not headers:
        return []

    url = f"{BASE_URL}/projects/{project_uid}/jobs"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("content", [])


def levenshtein(a, b):
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
st.title("Memsource (Legacy) Change % App 🚀")

if API_TOKEN:
    st.success(f"✅ Token loaded (first 6 chars): {API_TOKEN[:6]}...")
else:
    st.error("❌ No API token found. Please add MEMSOURCE_API_TOKEN in Streamlit secrets.")

# Step 1: Select Project
projects = []
try:
    projects = list_projects()
except requests.exceptions.HTTPError as e:
    st.error(f"❌ Could not fetch projects: {e}")

if projects:
    project_names = [f"{p['name']} ({p['uid']})" for p in projects]
    project_choice = st.selectbox("📂 Select a project", project_names)
    selected_project = projects[project_names.index(project_choice)]

    # Step 2: List Jobs
    try:
        jobs = list_jobs(selected_project["uid"])
        if jobs:
            job_names = [f"{j['filename']} ({j['uid']})" for j in jobs]
            st.selectbox("📝 Select a job", job_names)
        else:
            st.warning("⚠️ No jobs found for this project.")
    except Exception as e:
        st.error(f"❌ Could not fetch jobs: {e}")

    # Step 3: Upload PE XLIFF
    uploaded_file = st.file_uploader("📤 Upload Post-Edited XLIFF/MXLIFF", type=["xliff", "mxliff"])
    if uploaded_file:
        sources, targets = parse_xliff(uploaded_file)
        if sources and targets:
            change_percent = calculate_change_percent(sources, targets)
            st.success(f"✅ Change Percentage: {change_percent:.2f}%")
else:
    st.info("ℹ️ No projects available. Check API token and permissions.")
