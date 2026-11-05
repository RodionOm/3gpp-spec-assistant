"""Streamlit demo: ask a question about TS 38.300 and get a cited answer."""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src" / "spec_assistant"))
from answer import Assistant  # noqa: E402

st.set_page_config(page_title="3GPP Spec Assistant", page_icon="📡")
st.title("3GPP Spec Assistant")
st.caption("Answers questions about 5G NR from TS 38.300 V18.11.0, citing the section it used.")


@st.cache_resource
def get_assistant():
    return Assistant()


question = st.text_input("Question", placeholder="e.g. What is the RRC_INACTIVE state?")

if question:
    with st.spinner("Searching the specification..."):
        result = get_assistant().answer(question)
    st.markdown(result["answer"])
    st.subheader("Retrieved sections")
    for section, title, score in result["sources"]:
        st.write(f"§{section} {title}  ·  reranker score {score:.2f}")
