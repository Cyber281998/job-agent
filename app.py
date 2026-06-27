import streamlit as st
from agent import scrape_job, analyse_fit, follow_up
from rag import index_resume, search_resume

st.set_page_config(page_title="Job Application Agent", page_icon="🤖")

st.title("🤖 Job Application Agent")
st.caption("Upload your resume, paste a job URL or description, get a tailored application instantly")

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "requirements" not in st.session_state:
    st.session_state.requirements = ""
if "scores" not in st.session_state:
    st.session_state.scores = ""
if "bullets" not in st.session_state:
    st.session_state.bullets = ""
if "cover_letter" not in st.session_state:
    st.session_state.cover_letter = ""
if "resume_chunks" not in st.session_state:
    st.session_state.resume_chunks = []
if "full_analysis" not in st.session_state:
    st.session_state.full_analysis = ""

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

def run_analysis(job_text):
    if not uploaded_file:
        st.error("Please upload your resume first in the sidebar")
        return

    st.subheader("🎯 Your Personalised Analysis")

    with st.status("Running multi-step analysis...", expanded=True) as status:
        st.write("Step 1 — Extracting job requirements...")
        st.write("Step 2 — Scoring requirements against your resume...")
        st.write("Step 3 — Writing tailored resume bullets...")
        st.write("Step 4 — Drafting cover letter...")

        full_analysis, requirements, scores, bullets, cover_letter = analyse_fit(job_text)

        status.update(label="✅ Analysis complete", state="complete")

    st.session_state.analysis_done = True
    st.session_state.full_analysis = full_analysis
    st.session_state.requirements = requirements
    st.session_state.scores = scores
    st.session_state.bullets = bullets
    st.session_state.cover_letter = cover_letter
    st.session_state.resume_chunks = search_resume(job_text)
    st.session_state.conversation_history = [{
        "role": "assistant",
        "content": "I've completed your job application analysis. What would you like to refine? You can ask me to adjust the cover letter tone, focus on specific skills, or rewrite any section."
    }]

if use_url and job_url:
    with st.spinner("Scraping job listing..."):
        job_text = scrape_job(job_url)
    run_analysis(job_text)

if use_manual and job_text_manual:
    run_analysis(job_text_manual)

if st.session_state.analysis_done:
    st.markdown(st.session_state.full_analysis)

    st.download_button(
        label="Download Analysis",
        data=st.session_state.full_analysis,
        file_name="job_analysis.txt",
        mime="text/plain"
    )

    st.divider()
    st.subheader("💬 Refine Your Application")
    st.caption("Ask me to adjust anything — tone, focus, length, specific sections")

    for message in st.session_state.conversation_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("e.g. Make the cover letter more casual, or focus on my Python skills..."):
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, updated_history = follow_up(
                    prompt,
                    st.session_state.requirements,
                    st.session_state.scores,
                    st.session_state.bullets,
                    st.session_state.cover_letter,
                    st.session_state.resume_chunks,
                    st.session_state.conversation_history
                )
                st.markdown(response)
                st.session_state.conversation_history = updated_history