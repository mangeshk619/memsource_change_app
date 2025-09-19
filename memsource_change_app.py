import streamlit as st
import requests
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import difflib

st.title("📊 Memsource MT vs PE Change % Calculator (Project2)")

# Inputs
username = st.text_input("Memsource Email / Username")
password = st.text_input("Memsource Password", type="password")
project_id = st.text_input("Project ID (from URL or admin panel)")

BASE_URL = "https://cloud.memsource.com/api2"

def login(username, password):
    """Login and get Bearer token"""
    url = f"https://cloud.memsource.com/web/api2/v1/auth/login"
    payload = {"userName": username, "password": password}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    token = response.json().get("token")
    return token

def list_jobs(project_id, token):
    """List all jobs for a project"""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/projects/{project_id}/jobs"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("content", [])

def fetch_file(job_id, file_type, token):
    """Fetch XLIFF file for a job UID"""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}/jobs/{job_id}/targetFile"
    params = {"type": "XLIFF", "version": file_type}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.content

def read_xliff_text(file_bytes):
    """Extract all target text from XLIFF"""
    text = ""
    if file_bytes:
        try:
            with zipfile.ZipFile(BytesIO(file_bytes)) as z:
                for name in z.namelist():
                    if name.endswith(".xlf") or name.endswith(".xliff"):
                        with z.open(name) as f:
                            tree = ET.parse(f)
                            root = tree.getroot()
                            for t in root.findall(".//{*}target"):
                                if t.text:
                                    text += t.text + " "
        except zipfile.BadZipFile:
            text = file_bytes.decode("utf-8", errors="ignore")
    return text

def levenshtein_ratio(s1, s2):
    """Compute similarity ratio"""
    return difflib.SequenceMatcher(None, s1, s2).ratio() * 100

if st.button("Compute Change %"):
    if not username or not password or not project_id:
        st.error("Please fill in all fields.")
    else:
        try:
            token = login(username, password)
            st.success("🎉 Login successful!")
            
            jobs = list_jobs(project_id, token)
            if not jobs:
                st.error("❌ No jobs found for this project.")
            else:
                # Identify MT and PE jobs
                mt_job = None
                pe_job = None
                for job in jobs:
                    stage = job.get("workflowStepName", "").lower()
                    if "mt" in stage:
                        mt_job = job["id"]
                    elif "pe" in stage or "post-edit" in stage:
                        pe_job = job["id"]

                if not mt_job or not pe_job:
                    st.error("❌ Could not identify MT or PE jobs automatically.")
                else:
                    # Fetch files
                    mt_bytes = fetch_file(mt_job, "mt", token)
                    pe_bytes = fetch_file(pe_job, "pe", token)

                    # Extract text
                    mt_text = read_xliff_text(mt_bytes)
                    pe_text = read_xliff_text(pe_bytes)

                    # Compute change %
                    change_percent = 100 - levenshtein_ratio(mt_text, pe_text)
                    st.metric("Change % between MT and PE", f"{change_percent:.2f}%")

        except requests.HTTPError as e:
            st.error(f"❌ HTTP Error: {e}")
        except Exception as ex:
            st.error(f"⚠️ Error: {ex}")
