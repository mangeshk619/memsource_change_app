import streamlit as st
import requests
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import difflib
import re

st.title("📊 Memsource MT vs PE Change % Calculator (Project2 URL → API)")

# Input
username = st.text_input("Memsource Email / Username")
password = st.text_input("Memsource Password", type="password")
project_url_id = st.text_input("Project URL ID (the string in /show/...)")

BASE_URL = "https://cloud.memsource.com/api2"  # API base

def login(username, password):
    """Log in and get Bearer token"""
    url = f"https://cloud.memsource.com/web/api2/v1/auth/login"
    payload = {"userName": username, "password": password}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    token = response.json().get("token")
    return token

def resolve_numeric_project_id(project_url_id, token):
    """
    Resolve the numeric project ID from the external URL ID
    """
    headers = {"Authorization": f"Bearer {token}"}
    projects_url = f"{BASE_URL}/projects?pageSize=500"
    resp = requests.get(projects_url, headers=headers)
    resp.raise_for_status()
    projects = resp.json().get("content", [])
    
    for proj in projects:
        # Match external URL ID
        if proj.get("uid") == project_url_id:
            return proj["id"]
    st.warning(f"Could not find numeric project ID for {project_url_id}")
    return None

def fetch_file(numeric_project_id, file_type, token):
    """
    Fetch MT or PE XLIFF file from numeric project ID
    """
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all jobs
    jobs_url = f"{BASE_URL}/projects/{numeric_project_id}/jobs"
    jobs_resp = requests.get(jobs_url, headers=headers)
    jobs_resp.raise_for_status()
    jobs = jobs_resp.json().get("content", [])
    
    if not jobs:
        st.warning(f"No jobs found for project {numeric_project_id}")
        return None
    
    # Pick latest job
    job_id = jobs[-1]["id"]
    
    # Download target file
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
    if not username or not password or not project_url_id:
        st.error("Please fill in all fields.")
    else:
        try:
            token = login(username, password)
            st.success("🎉 Login successful!")
            
            # Resolve numeric project ID
            numeric_project_id = resolve_numeric_project_id(project_url_id, token)
            if not numeric_project_id:
                st.error("❌ Could not resolve project ID. Check URL ID.")
            else:
                # Fetch MT and PE files
                mt_bytes = fetch_file(numeric_project_id, "mt", token)
                pe_bytes = fetch_file(numeric_project_id, "pe", token)

                if mt_bytes and pe_bytes:
                    mt_text = read_xliff_text(mt_bytes)
                    pe_text = read_xliff_text(pe_bytes)

                    change_percent = 100 - levenshtein_ratio(mt_text, pe_text)
                    st.metric("Change % between MT and PE", f"{change_percent:.2f}%")
                else:
                    st.error("❌ Could not fetch MT or PE files. Check project permissions.")

        except requests.HTTPError as e:
            st.error(f"❌ HTTP Error: {e}")
        except Exception as ex:
            st.error(f"⚠️ Error: {ex}")
