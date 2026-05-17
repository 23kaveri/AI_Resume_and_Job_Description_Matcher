from datasets import load_dataset
import pandas as pd
import random

# ✅ Load a stable Hugging Face dataset (AG News)
dataset = load_dataset("ag_news", split="train[:2000]")

# Convert to DataFrame
df = pd.DataFrame(dataset)

# ✅ Define job titles
job_titles = [
    "Data Analyst", "HR Specialist", "AI Engineer", "Machine Learning Engineer",
    "Web Developer", "Software Engineer", "Python Developer", "Data Scientist",
    "Cloud Engineer", "HR Recruiter", "DevOps Engineer", "UI/UX Designer",
    "Business Analyst", "NLP Engineer", "Cybersecurity Specialist"
] * (len(df) // 15 + 1)

# ✅ Trim to same length
df = df[:len(job_titles)]
df["Job Title"] = job_titles[:len(df)]

# ✅ Skill pool for realistic variety
skill_pool = [
    "Python", "SQL", "TensorFlow", "Kubernetes", "Machine Learning",
    "Deep Learning", "NLP", "Communication", "Cloud", "Teamwork",
    "Leadership", "Data Analysis", "Problem Solving", "Statistics",
    "Java", "HTML", "CSS", "Docker", "AWS", "Azure", "Flask", "React"
]

# ✅ Generate random skills for each job
def random_skills():
    return ", ".join(random.sample(skill_pool, k=random.randint(5, 9)))

df["Skills"] = [random_skills() for _ in range(len(df))]

# ✅ Create unique job descriptions
df["Job Description"] = (
    "We are looking for a "
    + df["Job Title"]
    + " with expertise in "
    + df["Skills"]
    + ". Responsibilities include developing solutions, analyzing data, "
      "collaborating across teams, and implementing modern AI or software practices."
)

# ✅ Save to CSV
df[["Job Title", "Skills", "Job Description"]].to_csv("engineering_jobs.csv", index=False)

print("✅ Realistic job dataset created successfully as 'engineering_jobs.csv'")
print(f"Total jobs saved: {len(df)}")
