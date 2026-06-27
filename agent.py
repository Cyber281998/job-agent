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

def analyse_fit(job_text):
    relevant_resume_chunks = search_resume(job_text)
    resume_context = "\n".join(relevant_resume_chunks)

    prompt = f"""You are an expert career coach and AI engineer hiring specialist.

JOB LISTING:
{job_text}

CANDIDATE'S RESUME (relevant sections):
{resume_context}

Your tasks:
1. SKILLS MATCH: List which job requirements the candidate meets and which they are missing
2. FIT SCORE: Give a score out of 10 with a one-line reason
3. TAILORED RESUME BULLETS: Rewrite 3-5 resume bullet points to better match this job
4. COVER LETTER: Write a concise, genuine cover letter (3 paragraphs max)

Be honest and specific. Don't be generic."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text