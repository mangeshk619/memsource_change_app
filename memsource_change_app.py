import streamlit as st
import requests

# Load token from Streamlit secrets
API_TOKEN = st.secrets.get("MEMSOURCE_API_TOKEN", None)
BASE_URL = "https://cloud.memsource.com/web/api2/v1"

st.title("🔑 Memsource API Token Checker")

if not API_TOKEN:
    st.error("❌ No API token found. Please add MEMSOURCE_API_TOKEN in your Streamlit secrets.")
else:
    st.success(f"✅ Token loaded (first 6 chars): {API_TOKEN[:6]}...")

    def test_token(auth_type):
        """Test token with given auth type (ApiToken or Bearer)."""
        headers = {"Authorization": f"{auth_type} {API_TOKEN}"}
        url = f"{BASE_URL}/projects?pageSize=1"
        st.write(f"➡️ Testing {auth_type} at: {url}")
        try:
            response = requests.get(url, headers=headers)
            st.write(f"📡 Status: {response.status_code}")
            st.json(response.json())
            response.raise_for_status()
            return True
        except Exception as e:
            st.error(f"❌ {auth_type} test failed: {e}")
            return False

    # Try ApiToken first
    if test_token("ApiToken"):
        st.success("🎉 API token works with **ApiToken** header!")
    elif test_token("Bearer"):
        st.success("🎉 API token works with **Bearer** header!")
    else:
        st.error("❌ Token failed with both ApiToken and Bearer. Please re-check your token.")
