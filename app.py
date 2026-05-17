from flask import Flask, request, jsonify, render_template, redirect, url_for, make_response
import fitz
from sentence_transformers import SentenceTransformer, util
import re
import sqlite3
import datetime
from datetime import datetime   # <-- needed for job validity calculation
from database import init_db

init_db()

# Flask App
app = Flask(__name__, template_folder="ui/templates", static_folder="ui/static")

# AI Model
model = SentenceTransformer("all-MiniLM-L6-v2")


# ============================ PDF TEXT READER ============================
def extract_text_from_pdf(file_stream):
    text = ""
    with fitz.open(stream=file_stream, filetype="pdf") as pdf:
        for page in pdf:
            t = page.get_text()
            if t:
                text += t + "\n"
    return text.strip()


# ======================= MULTI JOB DESCRIPTION SPLITTER ==================
def split_job_descriptions(jd_text):
    parts = jd_text.split("Job Title:")
    jobs = []
    for p in parts:
        p = p.strip()
        if len(p) > 30:
            jobs.append("Job Title: " + p)
    return jobs


# ============================ JOB TITLE EXTRACTOR ========================
def extract_job_title(text):
    for line in text.split("\n"):
        if "Job Title:" in line:
            return line.replace("Job Title:", "").strip()
        if any(k in line.lower() for k in ["engineer", "developer", "scientist", "analyst"]):
            return line.strip()
    return "Unknown Job"


# ============================ SKILL EXTRACTION ===========================
def semantic_skills_from_text(text):
    text_lower = text.lower()

    tech_tokens = [
        "python", "java", "c++", "sql", "mysql", "mongodb",
        "html", "css", "javascript", "react", "angular", "node",
        "nlp", "machine learning", "ml", "deep learning", "ai",
        "cloud", "aws", "azure", "gcp", "cloud computing",
        "docker", "kubernetes", "devops", "ci cd",
        "linux", "tensorflow", "pytorch", "sklearn",
        "data analysis", "data visualization", "pandas", "numpy",
        "matplotlib", "power bi", "tableau",
        "spark", "hadoop", "git", "github"
    ]

    return sorted(list(set([token for token in tech_tokens if token in text_lower])))


# ===================== JOB VALIDITY EXTRACTOR (Hiring Duration) ===========
def extract_job_validity(text):
    text_lower = text.lower()

    # Direct format used in your job.pdf (THIS MAKES IT WORK NOW)
    direct = re.search(r"hiring validity[:\- ]+([a-z0-9 ]+)", text_lower)
    if direct:
        return direct.group(1).strip()

    # Detect numbers like "valid for 30 days"
    days = re.search(r"(\d+)\s+days", text_lower)
    if days:
        return f"{days.group(1)} days"

    # Expired job support
    if "expired" in text_lower:
        return "Expired ❌"

    return "Not mentioned"



# ======================= MATCHING / MISSING SKILLS ======================
def compute_matching_and_missing(jd_skills, resume_skills):
    jd_set = set(jd_skills)
    resume_set = set(resume_skills)
    return sorted(jd_set & resume_set), sorted(jd_set - resume_set)


# ============================= ROUTES ===================================
@app.route("/")
def dashboard_page():
    return render_template("dashboard.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_user():
    username = request.form.get("username")
    resp = make_response(redirect("/"))
    resp.set_cookie("ai_user", username, max_age=60*60*24*30)
    return resp


@app.route("/profile")
def profile_page():
    return render_template("profile.html")


@app.route("/resume-enhancer")
def resume_enhancer_page():
    return render_template("resume_enhancer.html")


@app.route("/market-insights")
def market_insights_page():
    return render_template("market_insights.html")


@app.route("/settings")
def settings_page():
    return render_template("settings.html")


@app.route("/help")
def help_page():
    return render_template("help_center.html")


# ===================== COMPARE ENGINE ==================
@app.route("/compare", methods=["POST"])
def compare():
    resume_file = request.files.get("resume")
    job_pdf = request.files.get("job_pdf")

    if not resume_file or not job_pdf:
        return jsonify({"error": "Both Resume and JD PDFs required"}), 400

    resume_text = extract_text_from_pdf(resume_file.read())
    jd_text = extract_text_from_pdf(job_pdf.read())

    job_blocks = split_job_descriptions(jd_text)
    resume_emb = model.encode(resume_text, convert_to_tensor=True)
    resume_skills = semantic_skills_from_text(resume_text)

    results = []

    for job in job_blocks:
        jd_emb = model.encode(job, convert_to_tensor=True)
        similarity = util.cos_sim(resume_emb, jd_emb).item()
        match_percent = round(similarity * 100, 2)

        jd_skills = semantic_skills_from_text(job)
        matching_skills, missing_skills = compute_matching_and_missing(jd_skills, resume_skills)

        title = extract_job_title(job)
        company = "Not Provided"

        for line in job.split("\n"):
            if "company" in line.lower():
                company = line.split(":")[-1].strip()

        validity = extract_job_validity(job)

        results.append({
            "job_title": title,
            "company": company,
            "validity": validity,
            "match_score": match_percent,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills
        })

        username = request.cookies.get("ai_user") or "guest"
        conn = sqlite3.connect("matcher.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO match_history(username, resume_name, job_title, company, match_percent, matched_skills, missing_skills, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, resume_file.filename, title, company, match_percent,
              ", ".join(matching_skills), ", ".join(missing_skills),
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

    results = sorted(results, key=lambda x: x["match_score"], reverse=True)

    return jsonify({
        "top_match": results[0]["job_title"],
        "total_jobs_compared": len(results),
        "results": results
    })


# ============================= HISTORY PAGE =============================
@app.route("/reports")
def reports_page():
    username = request.cookies.get("ai_user") or "guest"
    conn = sqlite3.connect("matcher.db")
    cur = conn.cursor()
    cur.execute("SELECT resume_name, job_title, company, match_percent, matched_skills, missing_skills, created_at FROM match_history WHERE username=?", (username,))
    rows = cur.fetchall()
    conn.close()
    return render_template("job_reports.html", history=rows, user=username)


@app.route("/clear-history", methods=["POST"])
def clear_history():
    username = request.cookies.get("ai_user") or "guest"
    conn = sqlite3.connect("matcher.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM match_history WHERE username=?", (username,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ========================= RESUME ENHANCER ENGINE =======================
from nltk.tokenize import sent_tokenize
import nltk
nltk.download('punkt')


def analyze_resume(text):
    suggestions = []

    if len(text) < 400:
        suggestions.append("Resume is short — try 1+ page with detailed sections.")

    skills_list = [
        "python","java","aws","ml","ai","deep learning","nlp","sql","tensorflow","pytorch",
        "excel","html","css","javascript","docker","kubernetes","mongodb","react","flask","django"
    ]

    found = [s for s in skills_list if s.lower() in text.lower()]
    missing = [s for s in skills_list if s not in found]

    if missing:
        suggestions.append("Missing Important Skills ➝ " + ", ".join(missing[:8]))
    if "project" not in text.lower():
        suggestions.append("Add technical projects with measurable outcome.")
    if "experience" not in text.lower():
        suggestions.append("Add internships / work experience if available.")
    if "•" not in text and "-" not in text:
        suggestions.append("Use bullet points format.")
    if "%" not in text and "improved" not in text.lower():
        suggestions.append("Include impact using numbers — % accuracy, speed improvement.")

    rewritten = rewrite_resume(text, found)
    return found, missing, suggestions, rewritten


def rewrite_resume(text, found_skills):
    points = sent_tokenize(text)[:6]
    return "\n".join(f"• {p.strip()}" for p in points if len(p.strip()) > 5)


@app.route("/enhance-resume", methods=["POST"])
def enhance_resume():
    pdf = request.files.get("resume")
    if not pdf:
        return jsonify({"error": "Upload a resume first"}), 400

    text = extract_text_from_pdf(pdf.read())
    found, missing, suggestions, rewritten = analyze_resume(text)

    return jsonify({
        "skills_found": found,
        "skills_missing": missing[:10],
        "suggestions": suggestions,
        "rewrite": rewritten
    })


# ============================= RUN SERVER =================================
if __name__ == "__main__":
    app.run(debug=True)
