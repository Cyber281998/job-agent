import streamlit as st
from agent import scrape_job, analyse_fit
from rag import index_resume

st.set_page_config(page_title="Job Application Agent", page_icon="🤖")

st.title("🤖 Job Application Agent")
st.caption("Upload your resume, paste a job URL, get a tailored application instantly")

with st.sidebar:
    st.header("Step 1 — Upload Resume")
    uploaded_file = st.file_uploader("Upload your resume PDF", type="pdf")
    
    if uploaded_file:
        with open("resume_temp.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        with st.spinner("Indexing your resume..."):
            result = index_resume("resume_temp.pdf")
        st.success(f"✅ {result}")

st.header("Step 2 — Paste Job URL")
job_url = st.text_input("Job listing URL", placeholder="https://au.seek.com.au/job/...")

if st.button("Analyse Job & Generate Application ↗", disabled=not job_url):
    if not uploaded_file:
        st.error("Please upload your resume first in the sidebar")
    else:
        with st.spinner("Scraping job listing..."):
            job_text = scrape_job(job_url)
        
        st.subheader("📋 Job Listing Extracted")
        with st.expander("See raw job text"):
            st.text(job_text[:1000] + "...")
        
        with st.spinner("Analysing fit and generating your application..."):
            analysis = analyse_fit(job_text)
        
        st.subheader("🎯 Your Personalised Analysis")
        st.markdown(analysis)
        
        st.download_button(
            label="Download Analysis",
            data=analysis,
            file_name="job_analysis.txt",
            mime="text/plain"
        )