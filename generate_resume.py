import os
import random
from datetime import datetime

# Directory to store generated resumes
output_dir = "sample_resumes"
os.makedirs(output_dir, exist_ok=True)

# Base templates
roles = [
    "Backend Developer", "Frontend Developer", "Data Scientist", "DevOps Engineer", "Machine Learning Engineer",
    "Full Stack Developer", "Cloud Engineer", "Database Administrator", "Cybersecurity Analyst", "AI Researcher"
]

skills_by_role = {
    "Backend Developer": ["Node.js", "Express", "PostgreSQL", "Docker", "REST API", "Git"],
    "Frontend Developer": ["React", "Redux", "JavaScript", "HTML", "CSS", "Figma"],
    "Data Scientist": ["Python", "scikit-learn", "SQL", "Pandas", "Tableau", "Machine Learning"],
    "DevOps Engineer": ["AWS", "Terraform", "Jenkins", "Kubernetes", "CI/CD", "Linux"],
    "Machine Learning Engineer": ["TensorFlow", "PyTorch", "NLP", "OpenCV", "Python", "AWS SageMaker"],
    "Full Stack Developer": ["React", "Node.js", "MongoDB", "GraphQL", "Docker", "GitHub Actions"],
    "Cloud Engineer": ["AWS", "Azure", "GCP", "Terraform", "Docker", "CloudFormation"],
    "Database Administrator": ["MySQL", "PostgreSQL", "MongoDB", "Backup", "Query Optimization", "Shell Scripting"],
    "Cybersecurity Analyst": ["SIEM", "Nmap", "Wireshark", "Splunk", "Firewall", "Python"],
    "AI Researcher": ["Deep Learning", "Reinforcement Learning", "TensorFlow", "Python", "Matplotlib", "OpenAI Gym"]
}

education_levels = [
    "Bachelor of Technology in Computer Science, 2019",
    "Master of Science in Artificial Intelligence, 2021",
    "Ph.D. in Computer Science, 2022",
    "Bachelor of Engineering in Information Technology, 2020",
    "Master of Computer Applications, 2018"
]

names = [
    "Amit Roy", "Sarah Bennett", "Marcus Lee", "Linda Zhao", "Daniel Green", "Priya Sharma", "Ethan Wang", "Sophia Kim",
    "Mohammed Ali", "Emily Davis", "Jake Robinson", "Anika Patel", "Lucas Smith", "Olivia Brown", "Arjun Verma",
    "Hannah Nguyen", "Chen Wei", "Isabella Thomas", "Ravi Deshmukh", "Grace Johnson", "Leo Martinez", "Mei Chen",
    "Noah Harris", "Kavya Rao", "Max Müller", "Harper Singh", "Zara Wilson", "Ahmad Nasser", "Elena Petrova", "Kenji Takahashi"
]

def random_date(start_year=2014, end_year=2023):
    start = random.randint(start_year, end_year - 1)
    end = start + random.randint(1, 3)
    return f"{start}", f"{min(end, 2024)}"

def format_resume(index, name, role):
    skills = skills_by_role[role]
    edu = random.choice(education_levels)
    start1, end1 = random_date(2017, 2020)
    start2, end2 = random_date(2020, 2023)

    lines = [
        f"Name: {name}",
        f"Title: {role}",
        "\nExperience:",
        f"- {role} ({start2} – {end2})",
        f"  Worked on {skills[0]}, {skills[1]}, and developed scalable features using {skills[2]}.",
        f"- Intern ({start1} – {end1})",
        f"  Assisted with {skills[3]} and collaborated with teams on {skills[4]}.",
        "\nSkills:",
        ", ".join(skills),
        "\nEducation:",
        edu
    ]
    return "\n".join(lines)

# Generate and save 30 resumes
for i in range(30):
    name = names[i % len(names)]
    role = roles[i % len(roles)]
    content = format_resume(i, name, role)
    filename = f"resume_{i+1:02d}_{role.replace(' ', '_')}.txt"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w") as f:
        f.write(content)

print("30 resumes generated in the 'sample_resumes/' folder.")
