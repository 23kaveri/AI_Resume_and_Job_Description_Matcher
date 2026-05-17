from sentence_transformers import SentenceTransformer, util
import PyPDF2, pandas as pd, re, json

model = SentenceTransformer('all-MiniLM-L6-v2')

# 🧾 Read dataset (2000 jobs)
jobs = pd.read_csv("engineering_jobs.csv").dropna(subset=["job_description"])

# 🧠 Extract text from resume PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

# 🧹 Clean text
def clean_text(text):
    return re.sub(r'\s+', ' ', text.lower())

# 💡 Extract key skills
def extract_skills(text):
    common_skills = [
        'python','java','sql','machine learning','deep learning','nlp',
        'excel','power bi','tableau','cloud','aws','docker','kubernetes',
        'tensorflow','pytorch','communication','leadership','react','node.js'
    ]
    return [skill for skill in common_skills if skill in text]

# ⚡ Compare with dataset
def compare_resume_with_dataset(resume_path, top_k=10):
    resume_text = clean_text(extract_text_from_pdf(resume_path))
    resume_emb = model.encode(resume_text, convert_to_tensor=True)
    resume_skills = extract_skills(resume_text)

    results = []
    for _, row in jobs.iterrows():
        job_desc = clean_text(row["job_description"])
        job_emb = model.encode(job_desc, convert_to_tensor=True)
        similarity = util.cos_sim(resume_emb, job_emb).item() * 100

        job_skills = extract_skills(job_desc)
        missing_skills = [s for s in job_skills if s not in resume_skills]

        results.append({
            "job_title": row.get("job_title", "Unknown Job"),
            "match_score": round(similarity, 2),
            "missing_skills": missing_skills
        })

    # Sort top matches
    results = sorted(results, key=lambda x: x["match_score"], reverse=True)[:top_k]
    return {"results": results}

if __name__ == "__main__":
    output = compare_resume_with_dataset("uploads/resume.pdf", top_k=10)
    print(json.dumps(output, indent=2))
