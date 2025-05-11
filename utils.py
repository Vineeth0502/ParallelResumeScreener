import re
import os
import pandas as pd
from io import StringIO
from pdfminer.high_level import extract_text
from dateutil import parser
from datetime import datetime
import nltk
import string

# Custom tokenizer to avoid NLTK tokenizer dependency
def custom_tokenize(text):
    for punct in string.punctuation:
        text = text.replace(punct, ' ')
    return [token.lower() for token in text.split() if token.strip()]

try:
    from nltk.corpus import stopwords
    stopwords.words('english')
except (LookupError, ImportError):
    nltk.download('stopwords', quiet=True)
    from nltk.corpus import stopwords

def extract_keywords(text):
    print("\n===== KEYWORD EXTRACTION =====")
    print(f"Input text length: {len(text) if text else 0} characters")
    if not text:
        print("No text provided. Returning empty set.")
        return set()
    tokens = custom_tokenize(text)
    print(f"Tokenized into {len(tokens)} tokens")
    stop_words = set(stopwords.words('english'))
    print(f"Using {len(stop_words)} stopwords for filtering")
    keywords = [word for word in tokens if word not in stop_words and len(word) > 1]
    unique_keywords = set(keywords)
    print(f"Extracted {len(unique_keywords)} unique keywords")
    print(f"Sample keywords (up to 10): {list(unique_keywords)[:10]}")
    return unique_keywords

def extract_years_experience(text):
    text = text.lower()
    max_years = 0
    patterns = [
        r'(\d{1,2})\+?\s*(?:years?|yrs?)(?:\s+of\s+)?(?:experience|exp)?',
        r'(?:experience|exp)(?:\s+of\s+)?(\d{1,2})\+?\s*(?:years?|yrs?)'
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                years = int(match)
                max_years = max(max_years, years)
            except:
                continue
    range_patterns = re.findall(r'(\b\d{4}\b)[\s–\-to]{1,5}(\b\d{4}\b)', text)
    for start, end in range_patterns:
        try:
            start, end = int(start), int(end)
            if 1980 < start < end <= datetime.now().year:
                max_years = max(max_years, end - start)
        except:
            continue
    full_date_ranges = re.findall(r'([a-zA-Z]{3,9}\s\d{4})\s*(?:to|–|-)\s*([a-zA-Z]{3,9}\s\d{4})', text)
    for start_str, end_str in full_date_ranges:
        try:
            start = parser.parse(start_str)
            end = parser.parse(end_str)
            diff_years = (end - start).days / 365.0
            if 0 < diff_years < 50:
                max_years = max(max_years, round(diff_years))
        except:
            continue
    return int(max_years)

def extract_education_level(text):
    print("\n===== EDUCATION LEVEL EXTRACTION =====")
    print(f"Input text length: {len(text) if text else 0} characters")
    if not text:
        print("No text provided. Returning 0.0 score.")
        return 0.0
    education_patterns = {
        r'ph\.?d\.?|doctor(?:ate|al)|d\.?phil\.?': 1.0,
        r'master|m\.?s\.?|m\.?b\.?a\.?|m\.?eng\.?|m\.?sc\.?|m\.?c\.?a\.?|post.?graduate|graduate degree': 0.8,
        r'bachelor|b\.?s\.?|b\.?a\.?|b\.?eng\.?|b\.?sc\.?|b\.?tech\.?|b\.?c\.?a\.?|college degree|undergraduate|university degree': 0.6,
        r'associate|a\.?s\.?|a\.?a\.?|a\.?a\.?s\.?|community college|technical college': 0.4,
        r'high school|diploma|ged|secondary school|higher secondary|12th|hsc': 0.2,
    }
    education_sections = [
        "education", "academic background", "academic qualification",
        "qualification", "academic history", "academic profile"
    ]
    print(f"Checking for education section headers: {education_sections}")
    has_education_section = any(re.search(r'^\s*' + section + r'[:\s]*$', text.lower(), re.MULTILINE) for section in education_sections)
    print(f"Resume has education section: {has_education_section}")
    max_score = 0.0
    print("Checking for education level patterns:")
    for pattern, score in education_patterns.items():
        if re.search(pattern, text.lower()):
            print(f"Found education pattern '{pattern}' with score {score}")
            max_score = max(max_score, score)
    if max_score > 0:
        print(f"Highest education level found with score: {max_score}")
    else:
        print("No specific education level detected")
        if len(text) > 500:
            max_score = 0.6
            print(f"Assigning default education score for substantial resume: {max_score} (Bachelor's level)")
    return max_score

def parse_resume_text(file_content, file_type):
    if file_type == 'txt':
        if isinstance(file_content, bytes):
            return file_content.decode('utf-8', errors='ignore')
        return file_content
    elif file_type == 'pdf':
        try:
            return extract_text(file_content)
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    return ""

def score_resume(resume_text, job_keywords):
    print("\n\n========== RESUME SCORING PROCESS ==========")
    print(f"Resume text length: {len(resume_text) if resume_text else 0} characters")
    print(f"Job keywords: {len(job_keywords)} keywords provided")
    resume_keywords = extract_keywords(resume_text)
    if job_keywords:
        matching_keywords = resume_keywords.intersection(job_keywords)
        keyword_match_ratio = len(matching_keywords) / len(job_keywords)
        print(f"Found {len(matching_keywords)} matching keywords out of {len(job_keywords)}")
        print(f"Keyword match ratio: {keyword_match_ratio:.4f} ({keyword_match_ratio*100:.2f}%)")
    else:
        keyword_match_ratio = 0
        matching_keywords = set()
        print("No job keywords provided. Keyword match ratio set to 0.")
    years_experience = extract_years_experience(resume_text)
    if years_experience == 0 and len(resume_text) > 500:
        print("Assigning default experience value (5 years) for substantial resume with no detected experience")
        years_experience = 5
    experience_score = min(years_experience / 10.0, 1.0)
    print(f"Years of experience: {years_experience}")
    print(f"Experience score: {experience_score:.4f} ({experience_score*100:.2f}%)")
    education_score = extract_education_level(resume_text)
    print(f"Education score: {education_score:.4f} ({education_score*100:.2f}%)")
    final_score = (0.5 * keyword_match_ratio) + (0.3 * experience_score) + (0.2 * education_score)
    print(f"Final score calculation: 0.5 * {keyword_match_ratio:.4f} + 0.3 * {experience_score:.4f} + 0.2 * {education_score:.4f}")
    print(f"Final score: {final_score:.4f} ({final_score*100:.2f}%)")
    print("============================================\n")
    return {
        'final_score': final_score,
        'keyword_match_ratio': keyword_match_ratio,
        'matching_keywords': matching_keywords,
        'years_experience': years_experience,
        'experience_score': experience_score,
        'education_score': education_score
    }

def format_results(results):
    df = pd.DataFrame(results)
    df = df.sort_values('final_score', ascending=False)
    df['matching_keywords'] = df['matching_keywords'].apply(lambda x: ', '.join(sorted(x)))
    df['final_score'] = (df['final_score'] * 100).round(2)
    df['keyword_match_ratio'] = (df['keyword_match_ratio'] * 100).round(2)
    df['experience_score'] = (df['experience_score'] * 100).round(2)
    df['education_score'] = (df['education_score'] * 100).round(2)
    df = df.rename(columns={
        'final_score': 'Final Score (%)',
        'keyword_match_ratio': 'Keyword Match (%)',
        'matching_keywords': 'Matching Keywords',
        'years_experience': 'Years of Experience',
        'experience_score': 'Experience Score (%)',
        'education_score': 'Education Score (%)',
        'file_name': 'Resume'
    })
    return df
