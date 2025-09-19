import streamlit as st
import requests
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import difflib

st.title("📊 Memsource MT vs PE Change % Calculator (Project2 API)")

# Input
username = st.text_input("Memsource Email / Username")
password = st.text_input("Memsource Password", type="password")
project_id = st.text_input("Project ID")

BASE_URL = "https://cloud.memsource.com/api2"  # Project2 API base URL

def login(username, password):
    """Log in and get Bearer token"""
    url = f"https://cloud.memsource.com/web/api2/v1/auth/login"
    payload = {"userName": username, "password": password}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    token = response.json().get("token")
    return token

def fetch_file(project_id, file_type, token):
    """
    Fetch MT or PE XLIFF file from a Memsource Project2 project.
    file_type: "mt" or "pe"
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 1: Get all jobs for the project
    jobs_url = f"{BASE_URL}/projects/{project_id}/jobs"
    jobs_resp = requests.get(jobs_url, headers=headers)
    jobs_resp.raise_for_status()
    jobs = jobs_resp.json().get("content", [])
    
    if not jobs:
        st.warning(f"No jobs found for project {project_id}")
        return None
    
    # Pick the **latest job** (assuming sorted by creation date)
    job_id = jobs[-1]["id"]
    
    # Step 2: Download target file
    target_url = f"{BASE_URL}/jobs/{job_id}/targetFile"
    params = {"type": "XLIFF", "version": file_type}
    target_resp = requests.get(target_url, headers=headers, params=params)
    target_resp.raise_for_status()
    
    return target_resp.content

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
            st.warning("File is not a zip/XLIFF file, attempting to read raw content")
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
            
            # Fetch latest MT and PE files
            mt_bytes = fetch_file(project_id, "mt", token)
            pe_bytes = fetch_file(project_id, "pe", token)

            if mt_bytes and pe_bytes:
                mt_text = read_xliff_text(mt_bytes)
                pe_text = read_xliff_text(pe_bytes)

                change_percent = 100 - levenshtein_ratio(mt_text, pe_text)
                st.metric("Change % between MT and PE", f"{change_percent:.2f}%")
            else:
                st.error("❌ Could not fetch MT or PE files. Check project ID and permissions.")

        except requests.HTTPError as e:
            st.error(f"❌ HTTP Error: {e}")
        except Exception as ex:
            st.error(f"⚠️ Error: {ex}")
