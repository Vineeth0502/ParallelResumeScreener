
# 🚀 Parallel Resume Screening App (with Streamlit + Python)

This repository contains a full-featured resume screening application that allows users to upload multiple resumes and score them based on job relevance. It uses both **serial** and **parallel (multiprocessing)** processing modes to demonstrate the benefits of concurrent execution.

---

## 📌 Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [How It Works](#how-it-works)
- [Directory Structure](#directory-structure)
- [Setup Instructions](#setup-instructions)
- [Parallel Processing Explained](#parallel-processing-explained)
- [Resume Scoring Logic](#resume-scoring-logic)
- [Education and Experience Detection](#education-and-experience-detection)
- [Keyword Extraction](#keyword-extraction)
- [Sample Output](#sample-output)
- [Contributors](#contributors)
- [License](#license)

---

## 📖 Project Overview
The Resume Screening App evaluates resumes by matching them with a job description. It calculates a relevance score using:
- **Keyword match ratio**
- **Years of experience**
- **Education level**

It also allows the comparison of performance between **serial** and **parallel** execution strategies using Python’s `concurrent.futures`.

---

## ✨ Features
- Upload multiple resumes (PDF or TXT)
- Keyword extraction from job description
- Education level detection (PhD, Master's, Bachelor's, etc.)
- Automatic experience detection from resume text
- Serial vs. Parallel resume screening comparison
- Scoring breakdown (Keyword %, Experience %, Education %)
- Speedup metrics

---

## ⚙️ Tech Stack
- Python 3.10+
- Streamlit for UI
- PDFMiner for PDF parsing
- pandas for tabular reporting
- NLTK for stopword filtering
- concurrent.futures for multiprocessing
- dateutil for experience calculation

---

## 🔍 How It Works
1. **User uploads a job description and resumes**
2. **App extracts keywords from the job description**
3. **Each resume is parsed to extract relevant text**
4. **Education and experience are parsed from resume**
5. **Resume score is calculated**
6. **Parallel and Serial performance is benchmarked**

---

## 📁 Directory Structure
```
.
├── app.py                      # Streamlit UI entry point
├── utils.py                    # Resume scoring logic
├── serial_resume_screener.py   # Serial resume processor
├── parallel_resume_screener.py # Parallel (multiprocessing) processor
├── sample_resumes/             # Folder containing generated dummy resumes
├── generate_resumes.py         # Script to generate fake resumes
├── README.md                   # Project documentation
└── .gitignore                  # Git ignored files
```

---

## 🖥️ Setup Instructions
```bash
# Clone the repo
git clone https://github.com/your-username/parallel-resume-screener.git
cd parallel-resume-screener

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

---

## ⚡ Parallel Processing Explained

We use Python’s built-in `concurrent.futures.ProcessPoolExecutor` to:
- Spawn multiple worker processes across CPU cores
- Distribute resume scoring jobs in parallel
- Return results and compare speed with serial execution

```python
with concurrent.futures.ProcessPoolExecutor() as executor:
    results = list(executor.map(score_resume, resume_data_list))
```

You will also see a live **speedup ratio** like:
```
Speedup: 3.42x
```

---

## 📊 Resume Scoring Logic

| Factor            | Weight |
|------------------|--------|
| Keyword Match     | 50%    |
| Experience        | 30%    |
| Education Level   | 20%    |

---

## 🎓 Education and Experience Detection

- Uses regex to detect **dates**, **phrases** like "5+ years of experience", and date ranges like "2016–2020"
- Education patterns include:
  - `PhD`, `Doctoral`, `MS`, `MBA`, `B.Tech`, `BSc`, `Diploma`, `GED`, etc.

---

## 🧠 Keyword Extraction
- Converts all text to lowercase
- Tokenizes using a custom tokenizer
- Removes punctuation and stopwords
- Returns the top matches between job description and resume

---

## 📸 Sample Output (Screenshots)

<img width="1494" alt="Screenshot 2025-05-11 at 12 20 19 AM" src="https://github.com/user-attachments/assets/5e206cc2-0526-48a6-bfc9-c0dbc5ff1c69" />



---

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.
