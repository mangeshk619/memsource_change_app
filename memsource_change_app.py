```python


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
```
