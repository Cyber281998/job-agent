import anthropic
import requests
from bs4 import BeautifulSoup
from rag import search_resume
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()

def scrape_job(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines[:200])

def step1_extract_requirements(job_text):
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Extract the key requirements from this job listing.
Return them as a clean numbered list under these categories:
- Technical Skills
- Experience Required
- Nice to Have

JOB LISTING:
{job_text}

Return only the structured list, nothing else."""
        }]
    )
    return message.content[0].text

def step2_score_requirements(requirements, resume_chunks):
    resume_context = "\n".join(resume_chunks)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""You are a recruiter scoring a candidate against job requirements.

JOB REQUIREMENTS:
{requirements}

CANDIDATE RESUME:
{resume_context}

For each requirement, respond with:
MET ✅ or GAP ❌ — one line of evidence from the resume

Be ruthlessly honest. If it's not clearly in the resume, mark it as GAP."""
        }]
    )
    return message.content[0].text

def step3_generate_bullets(requirements, scores, resume_chunks):
    resume_context = "\n".join(resume_chunks)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""You are an expert resume writer.

JOB REQUIREMENTS:
{requirements}

CANDIDATE SCORES:
{scores}

CANDIDATE RESUME:
{resume_context}

Rewrite 5 resume bullet points that directly address the MET requirements.
Use strong action verbs and include specific metrics where possible.
Draw only from real experience in the resume — do not invent anything."""
        }]
    )
    return message.content[0].text

def step4_write_cover_letter(requirements, scores, bullets, resume_chunks):
    resume_context = "\n".join(resume_chunks)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Write a genuine, specific cover letter based on this analysis.

JOB REQUIREMENTS:
{requirements}

CANDIDATE FIT SCORES:
{scores}

TAILORED RESUME BULLETS:
{bullets}

CANDIDATE BACKGROUND:
{resume_context}

Rules:
- 3 paragraphs max
- Open with a specific reason why this role, not generic flattery
- Middle paragraph: 2-3 concrete examples from their real experience
- Close: confident, not desperate
- Do not use the phrase "I am writing to apply"
- Sound like a human, not a template"""
        }]
    )
    return message.content[0].text

def analyse_fit(job_text, conversation_history=None):
    resume_chunks = search_resume(job_text)

    requirements = step1_extract_requirements(job_text)
    scores = step2_score_requirements(requirements, resume_chunks)
    bullets = step3_generate_bullets(requirements, scores, resume_chunks)
    cover_letter = step4_write_cover_letter(requirements, scores, bullets, resume_chunks)

    full_analysis = f"""## 📋 Step 1 — Job Requirements Extracted

{requirements}

---

## ✅ Step 2 — Requirement Scoring

{scores}

---

## 💼 Step 3 — Tailored Resume Bullets

{bullets}

---

## ✉️ Step 4 — Cover Letter

{cover_letter}"""

    return full_analysis, requirements, scores, bullets, cover_letter

def follow_up(question, requirements, scores, bullets, cover_letter, resume_chunks, conversation_history):
    resume_context = "\n".join(resume_chunks)
    
    conversation_history.append({
        "role": "user",
        "content": question
    })

    system = f"""You are a career coach helping a candidate refine their job application.

You have already completed this analysis:

JOB REQUIREMENTS:
{requirements}

CANDIDATE SCORES:
{scores}

TAILORED BULLETS:
{bullets}

COVER LETTER:
{cover_letter}

CANDIDATE RESUME:
{resume_context}

Answer the candidate's questions and refine any part of the application they ask about.
Be specific, draw from real resume content only."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=system,
        messages=conversation_history
    )

    response = message.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": response
    })

    return response, conversation_history