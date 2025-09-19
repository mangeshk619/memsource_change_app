# token_checker.py
import streamlit as st
import requests

st.title("Memsource API Token Checker")

API_TOKEN = st.secrets.get("MEMSOURCE_API_TOKEN", "")

if not API_TOKEN:
    st.error("❌ No API token found. Please add MEMSOURCE_API_TOKEN in your Streamlit secrets.")
else:
    st.success(f"✅ Token loaded (first 6 chars): {API_TOKEN[:6]}...")

    BASE_URL = "https://cloud.memsource.com/web/api2/v1"  # or us.cloud.memsource.com if US tenant
    url = f"{BASE_URL}/users/me"

    headers = {"Authorization": f"ApiToken {API_TOKEN}"}

    st.write(f"➡️ Testing: {url}")
    try:
        response = requests.get(url, headers=headers)
        st.write(f"📡 Status: {response.status_code}")
        st.code(response.text[:500])  # show first 500 chars

        if response.ok:
            st.success("🎉 Token is valid! API connection works.")
        else:
            st.error(f"❌ Token test failed: {response.status_code}")
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
