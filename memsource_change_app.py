import streamlit as st
import requests
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import difflib

st.title("📊 Memsource MT vs PE Change % Calculator (Project2 Jobs)")

# Inputs
username = st.text_input("Memsource Email / Username")
password = st.text_input("Memsource Password", type="password")
mt_job_id = st.text_input("MT Job ID")
pe_job_id = st.text_input("PE Job ID")

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

def fetch_file(job_id, file_type, token):
    """Fetch XLIFF file for a given job"""
    headers = {"Authorization": f"Bearer {token}"}
    target_url = f"{BASE_URL}/jobs/{job_id}/targetFile"
    params = {"type": "XLIFF", "version": file_type}
    response = requests.get(target_url, headers=headers, params=params)
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
    if not username or not password or not mt_job_id or not pe_job_id:
        st.error("Please fill in all fields.")
    else:
        try:
            token = login(username, password)
            st.success("🎉 Login successful!")
            
            # Fetch files
            mt_bytes = fetch_file(mt_job_id, "mt", token)
            pe_bytes = fetch_file(pe_job_id, "pe", token)

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
