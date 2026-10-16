import streamlit as st

st.title("Auto-patching")
f = st.file_uploader("Upload a Python or C file", type=["py", "c"])
if f:
    st.write(f"Received: {f.name}")