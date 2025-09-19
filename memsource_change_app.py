import streamlit as st
import requests

st.title("🔑 Memsource Login Fallback Checker")

# Input fields for username & password
username = st.text_input("Email / Username")
password = st.text_input("Password", type="password")

BASE_URL = "https://cloud.memsource.com/web/api2/v1"

if st.button("Login"):
    if not username or not password:
        st.error("Please enter both username and password.")
    else:
        url = f"{BASE_URL}/auth/login"
        payload = {"userName": username, "password": password}
        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            st.write(f"📡 Status: {response.status_code}")
            
            if response.ok:
                token_data = response.json()
                access_token = token_data.get("token")
                st.success("🎉 Login successful!")
                st.write("Use this token for API requests:")
                st.code(f"Bearer {access_token}")
            else:
                st.error(f"❌ Login failed: {response.text}")
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
