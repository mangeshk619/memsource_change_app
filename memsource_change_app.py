import streamlit as st
import requests
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import difflib

st.title("📊 Memsource MT vs PE Change % Calculator")

# Input
username = st.text_input("Memsource Email / Username")
password = st.text_input("Memsource Password", type="password")
project_id = st.text_input("Project ID")

BASE_URL = "https://cloud.memsource.com/web/api2/v1"

def login(username, password):
    """Log in and get Bearer token"""
    url = f"{BASE_URL}/auth/login"
    payload = {"userName": username, "password": password}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    token = response.json().get("token")
    return token

def fetch_file(project_id, file_type, token):
    """
    Fetch XLIFF file from Memsource project.
    file_type: 'mt' or 'pe'
    """
    # For simplicity, assuming a structure like:
    # GET /projects/{projectId}/jobs -> get job IDs
    # GET /jobs/{jobId}/targetFile?type=XLIFF&version={mt/pe}
    # You might need to adjust endpoints depending on your tenant
    # Here we will mock download
    st.warning(f"⚠️ File fetching not implemented. This is where you would fetch {file_type} file for project {project_id}")
    return None  # Replace with actual file bytes

def read_xliff_text(file_bytes):
    """Extract all target text from XLIFF"""
    text = ""
    if file_bytes:
        with zipfile.ZipFile(BytesIO(file_bytes)) as z:
            for name in z.namelist():
                if name.endswith(".xlf") or name.endswith(".xliff"):
                    with z.open(name) as f:
                        tree = ET.parse(f)
                        root = tree.getroot()
                        for t in root.findall(".//{*}target"):
                            if t.text:
                                text += t.text + " "
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
            
            # Fetch files
            mt_bytes = fetch_file(project_id, "mt", token)
            pe_bytes = fetch_file(project_id, "pe", token)

            if mt_bytes and pe_bytes:
                mt_text = read_xliff_text(mt_bytes)
                pe_text = read_xliff_text(pe_bytes)

                change_percent = 100 - levenshtein_ratio(mt_text, pe_text)
                st.metric("Change % between MT and PE", f"{change_percent:.2f}%")
            else:
                st.warning("Files could not be fetched. Implement fetch_file() with your Memsource endpoints.")

        except requests.HTTPError as e:
            st.error(f"❌ HTTP Error: {e}")
        except Exception as ex:
            st.error(f"⚠️ Error: {ex}")
