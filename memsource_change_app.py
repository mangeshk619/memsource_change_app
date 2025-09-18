import streamlit as st
import requests
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
import Levenshtein

# -----------------------------
# Memsource API Configuration
# -----------------------------
API_TOKEN = 'SWY3OEhkSjJOYi9IRVhKTU5QZFVVd2dmT1kvR0tpZ0w2K29TVkt0NjhqQT06d1I5M2JTSDZnb000WktvZXVSejlCQzoxeWVVdmtmajA1cVRtYVA2OTVISWln'
BASE_URL = 'https://cloud.memsource.com/web/api2/v1'
HEADERS = {'Authorization': f'ApiToken {API_TOKEN}'}

# -----------------------------
# Functions
# -----------------------------
def list_projects():
    url = f'{BASE_URL}/projects'
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    projects = response.json()
    return [(p['id'], p['name']) for p in projects]

def list_jobs(project_id):
    url = f'{BASE_URL}/projects/{project_id}/jobs'
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    jobs = response.json()
    return [(job['id'], job['name']) for job in jobs]

def download_mt_file_from_job(job_id):
    url = f'{BASE_URL}/jobs/{job_id}/files'
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    files_data = response.json()

    for f in files_data:
        if 'MT' in f['fileName'].upper():
            r = requests.get(f['downloadUrl'])
            r.raise_for_status()
            return r.content
    st.warning("No MT file found in this job.")
    return None

def read_xliff_content(file_bytes):
    try:
        if file_bytes[:4] == b'PK\x03\x04':
            z = zipfile.ZipFile(BytesIO(file_bytes))
            text_segments = []
            for name in z.namelist():
                if name.endswith(('.xlf', '.xliff')):
                    with z.open(name) as f:
                        text_segments.append(read_xlf(f))
            return '\n'.join(text_segments)
        else:
            return read_xlf(BytesIO(file_bytes))
    except Exception as e:
        st.error(f'Error reading file: {e}')
        return ''

def read_xlf(f):
    tree = ET.parse(f)
    root = tree.getroot()
    ns = {"xliff": "urn:oasis:names:tc:xliff:document:1.2"}
    text_segments = []
    for elem in root.findall('.//xliff:target', ns):
        text_segments.append(elem.text or '')
    return '\n'.join(text_segments)

def calculate_change_percent(original_text, edited_text):
    distance = Levenshtein.distance(original_text, edited_text)
    change_percent = (distance / max(1, len(original_text))) * 100
    return distance, change_percent

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("Memsource Change % Calculator (Upload PE Only)")
st.write("Select a project and job, then upload the Post-Edited (PE) XLIFF. The app will fetch the MT file automatically.")

# Projects dropdown
projects = list_projects()
project_names = [name for (_, name) in projects]
selected_project_name = st.selectbox("Choose a project", project_names)

if selected_project_name:
    project_id = [id for (id, name) in projects if name == selected_project_name][0]

    # Jobs dropdown
    jobs = list_jobs(project_id)
    if not jobs:
        st.warning("No jobs found in this project.")
    else:
        job_names = [name for (_, name) in jobs]
        selected_job_name = st.selectbox("Choose a job", job_names)

        # Upload PE file
        pe_file = st.file_uploader("Upload Post-Edited XLIFF", type=["xlf", "xliff", "mxliff"])

        if selected_job_name and pe_file:
            job_id = [id for (id, name) in jobs if name == selected_job_name][0]

            # Download MT file
            mt_bytes = download_mt_file_from_job(job_id)
            if mt_bytes:
                pe_bytes = pe_file.read()
                mt_text = read_xliff_content(mt_bytes)
                pe_text = read_xliff_content(pe_bytes)

                distance, change_percent = calculate_change_percent(mt_text, pe_text)

                st.subheader("Results")
                st.write(f"Levenshtein Distance: **{distance} edits**")
                st.write(f"Change %: **{change_percent:.2f}%**")

                with st.expander("Show Extracted Texts"):
                    st.text_area("MT Text", mt_text, height=200)
                    st.text_area("PE Text", pe_text, height=200)
