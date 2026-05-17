import os
import re
import pdfplumber
from sentence_transformers import SentenceTransformer, util

# ----------------------------------------------------
# OFFLINE MODEL
# ----------------------------------------------------
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

MODEL_PATH = "models/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_PATH)

# ----------------------------------------------------
# EXTRACT TEXT FROM PDF
# ----------------------------------------------------
def extract_text_from_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                t = page.extract_text()
            except:
                t = ""
            if t:
                text += t + "\n"
    return text.strip()

# ----------------------------------------------------
# EXTRACT SKILLS
# ----------------------------------------------------
def extract_skills(text):
    skill_keywords = [
        "python", "sql", "java", "react", "cloud", "aws", "html", "css",
        "javascript", "nlp", "deep learning", "machine learning", "ml",
        "communication", "teamwork", "problem solving"
    ]
    found = []
    text_lower = text.lower()
    for skill in skill_keywords:
        if skill in text_lower:
            found.append(skill)
    return list(set(found))

# ----------------------------------------------------
# SPLIT MULTIPLE JOBS INSIDE A SINGLE PDF
# ----------------------------------------------------
def split_multiple_jobs(text):

    # Ensure consistent formatting
    text = text.replace("JOB TITLE", "Job Title").replace("JOB TITLE:", "Job Title:")

    # Split when "Job Title:" appears
    raw_jobs = re.split(r"(?i)job title\s*:", text)
    jobs = []

    for block in raw_jobs:
        block = block.strip()
        if len(block) < 30:
            continue

        # ----- Extract job title -----
        title_match = re.match(r"([^\n]+)", block)
        job_title = title_match.group(1).strip() if title_match else "Unknown"
        job_title = job_title.replace("Job Title", "").strip()

        # ----- Extract company -----
        company_match = re.search(r"(?i)company\s*[:\-]\s*([^\n]+)", block)
        company = company_match.group(1).strip() if company_match else "Not Provided"
        company = company.replace("Company Name", "").strip()

        jobs.append({
            "job_title": job_title,
            "company": company,
            "full_text": block
        })

    return jobs

# ----------------------------------------------------
# COMPARE RESUME VS ONE JOB
# ----------------------------------------------------
def compare_resume_job(resume_text, job_text):
    resume_emb = model.encode(resume_text, convert_to_tensor=True)
    job_emb = model.encode(job_text, convert_to_tensor=True)

    similarity = float(util.cos_sim(resume_emb, job_emb))

    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(job_text)

    return {
        "match_score": round(similarity * 100, 2),
        "matching_skills": list(set(resume_skills) & set(jd_skills)),
        "missing_skills": list(set(jd_skills) - set(resume_skills))
    }

# ----------------------------------------------------
# MAIN FUNCTION → RESUME vs ALL JOBS
# ----------------------------------------------------
def analyze_resume_vs_jobs(resume_path, job_pdf_path):
    resume_text = extract_text_from_pdf(resume_path)
    jobs_pdf_text = extract_text_from_pdf(job_pdf_path)

    job_list = split_multiple_jobs(jobs_pdf_text)

    final_results = []

    for job in job_list:
        comparison = compare_resume_job(resume_text, job["full_text"])

        final_results.append({
            "job_title": job["job_title"],
            "company": job["company"],
            "match_score": comparison["match_score"],
            "matching_skills": comparison["matching_skills"],
            "missing_skills": comparison["missing_skills"]
        })

    return final_results