import requests
import streamlit as st

# Candidate Memsource API base URLs to test
CANDIDATE_URLS = [
    "https://cloud.memsource.com/web/api2/v1",
    "https://cloud.memsource.com/web/api2",
    "https://cloud.memsource.com/api2/v1",
    "https://cloud.memsource.com/api2",
    "https://us.cloud.memsource.com/web/api2/v1",
    "https://us.cloud.memsource.com/web/api2",
    "https://us.cloud.memsource.com/api2/v1",
    "https://us.cloud.memsource.com/api2",
]

st.title("🔎 Memsource API Base URL Tester")

# Load API Token from Streamlit secrets
API_TOKEN = st.secrets.get("MEMSOURCE_API_TOKEN", "")
if not API_TOKEN:
    st.error("❌ No API token found. Please add MEMSOURCE_API_TOKEN in Streamlit secrets.")
    st.stop()

headers = {"Authorization": f"ApiToken {API_TOKEN}"}

if st.button("Test All Candidate URLs"):
    for base in CANDIDATE_URLS:
        url = f"{base}/projects?pageSize=1"
        st.write(f"➡️ Testing: {url}")
        try:
            resp = requests.get(url, headers=headers)
            st.write(f"📡 Status: {resp.status_code}")
            st.write(f"📦 Response (first 300 chars): {resp.text[:300]} ...")
            if resp.ok:
                st.success(f"✅ SUCCESS → Base URL works: {base}")
        except Exception as e:
            st.error(f"❌ Error for {base}: {str(e)}")
