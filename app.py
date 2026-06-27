import streamlit as st
from agent import scrape_job, analyse_fit
from rag import index_resume

st.set_page_config(page_title="Job Application Agent", page_icon="🤖")

st.title("🤖 Job Application Agent")
st.caption("Upload your resume, paste a job URL or job description, get a tailored application instantly")

with st.sidebar:
    st.header("Step 1 — Upload Resume")
    uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])

    if uploaded_file:
        file_type = uploaded_file.name.split(".")[-1].lower()
        temp_path = f"resume_temp.{file_type}"

        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Indexing your resume..."):
            result = index_resume(temp_path, file_type)
        st.success(f"✅ {result}")

st.header("Step 2 — Add Job")

tab1, tab2 = st.tabs(["Paste URL", "Paste Job Description"])

with tab1:
    job_url = st.text_input("Job listing URL", placeholder="https://au.seek.com.au/job/...")
    use_url = st.button("Fetch from URL ↗")

with tab2:
    job_text_manual = st.text_area("Paste the full job description here", height=300)
    use_manual = st.button("Use This Description ↗")

if use_url and job_url:
    if not uploaded_file:
        st.error("Please upload your resume first in the sidebar")
    else:
        with st.spinner("Scraping job listing..."):
            job_text = scrape_job(job_url)

        with st.expander("See extracted job text"):
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

if use_manual and job_text_manual:
    if not uploaded_file:
        st.error("Please upload your resume first in the sidebar")
    else:
        with st.spinner("Analysing fit and generating your application..."):
            analysis = analyse_fit(job_text_manual)

        st.subheader("🎯 Your Personalised Analysis")
        st.markdown(analysis)
        st.download_button(
            label="Download Analysis",
            data=analysis,
            file_name="job_analysis.txt",
            mime="text/plain"
        )