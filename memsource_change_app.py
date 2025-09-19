import streamlit as st
import requests

# Load token from Streamlit secrets
API_TOKEN = st.secrets.get("MEMSOURCE_API_TOKEN", None)

BASE_URLS = [
    "https://cloud.memsource.com/web/api2/v1",  # sometimes used in docs
    "https://cloud.memsource.com/api2/v1"       # most common correct one
]

st.title("🔑 Memsource API Token Checker (Multi-URL)")

if not API_TOKEN:
    st.error("❌ No API token found. Please add MEMSOURCE_API_TOKEN in your Streamlit secrets.")
else:
    st.success(f"✅ Token loaded (first 6 chars): {API_TOKEN[:6]}...")

    def test_token(auth_type, base_url):
        """Test token with given auth type and base URL."""
        headers = {"Authorization": f"{auth_type} {API_TOKEN}"}
        url = f"{base_url}/projects?pageSize=1"
        st.write(f"➡️ Testing {auth_type} at: {url}")
        try:
            response = requests.get(url, headers=headers)
            st.write(f"📡 Status: {response.status_code}")
            try:
                st.json(response.json())
            except Exception:
                st.write(response.text[:300])  # raw if not JSON
            response.raise_for_status()
            return True
        except Exception as e:
            st.error(f"❌ {auth_type} test failed at {base_url}: {e}")
            return False

    # Try both base URLs with ApiToken and Bearer
    for base_url in BASE_URLS:
        st.subheader(f"🌍 Testing base URL: {base_url}")
        if test_token("ApiToken", base_url):
            st.success(f"🎉 Success! API token works with **ApiToken** at {base_url}")
        elif test_token("Bearer", base_url):
            st.success(f"🎉 Success! API token works with **Bearer** at {base_url}")
        else:
            st.warning(f"⚠️ Token failed with both ApiToken and Bearer at {base_url}")
