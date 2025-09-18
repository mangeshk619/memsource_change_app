import streamlit as st
import requests
import xml.etree.ElementTree as ET
from io import BytesIO

BASE_URL = "https://cloud.memsource.com/web/api2"
API_TOKEN = st.secrets["memsource"]["api_token"]  # store your token in Streamlit secrets
HEADERS = {"Authorization": f"ApiToken {API_TOKEN}"}

# 🔎 Function to test API connection
def test_api_connection():
    url = f"{BASE_URL}/users/me"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        user = response.json()
        st.success(f"✅ Connected to Memsource as: {user.get('userName')}")
        return True
    else:
        st.error(f"❌ Connection failed: {response.status_code} - {response.text}")
        return False

# 📂 Function to extract text from XLIFF/mXLIFF
def read_xliff(uploaded_file):
    tree = ET.parse(uploaded_file)
    root = tree.getroot()
    ns = {'ns': 'urn:oasis:names:tc:xliff:document:1.2'}
    segments = []
    for trans_unit in root.findall('.//ns:trans-unit', ns):
        source = trans_unit.find('ns:source', ns)
        target = trans_unit.find('ns:target', ns)
        if source is not None and target is not None:
            segments.append((source.text or "", target.text or ""))
    return segments

# 🧮 Function to calculate Levenshtein distance
def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

# 📊 Function to calculate change %
def calculate_change(segments):
    total_change = 0
    total_length = 0
    for source, target in segments:
        distance = levenshtein_distance(source, target)
        total_change += distance
        total_length += len(source)
    if total_length == 0:
        return 0
    return round((total_change / total_length) * 100, 2)

# 🚀 Streamlit UI
st.title("Memsource Change % Checker")

if st.button("🔗 Test API Connection"):
    test_api_connection()

st.write("---")

uploaded_file = st.file_uploader("Upload PE XLIFF/mXLIFF file", type=["xliff", "mxliff"])

if uploaded_file:
    try:
        segments = read_xliff(uploaded_file)
        if not segments:
            st.warning("No trans-units found in the file.")
        else:
            change_percent = calculate_change(segments)
            st.success(f"Estimated Change %: {change_percent}%")
    except Exception as e:
        st.error(f"Error processing file: {e}")
