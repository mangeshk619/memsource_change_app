import streamlit as st
import requests

BASE_URL = "https://cloud.memsource.com/web/api2/v1"

# Load API token from Streamlit secrets
API_TOKEN = st.secrets.get("MEMSOURCE_API_TOKEN", None)

if not API_TOKEN:
    st.error("❌ No API token found. Please add MEMSOURCE_API_TOKEN in your Streamlit secrets.")
else:
    st.write(f"✅ Token loaded (first 6 chars): {API_TOKEN[:6]}...")

HEADERS = {"Authorization": f"ApiToken {API_TOKEN}"}


def list_projects():
    url = f"{BASE_URL}/projects?pageSize=1"
    st.write(f"🔎 Sending request to: {url}")
    st.write(f"🔎 Using headers: {HEADERS}")  # Debugging
    response = requests.get(url, headers=HEADERS)
    st.write(f"📡 Raw response status: {response.status_code}")
    st.write(f"📡 Raw response text: {response.text}")
    response.raise_for_status()
    return response.json()


# Try connection
try:
    projects = list_projects()
    st.success("✅ Connection successful! Retrieved project data.")
    st.json(projects)
except requests.exceptions.HTTPError as e:
    st.error(f"❌ Connection failed: {e}")
