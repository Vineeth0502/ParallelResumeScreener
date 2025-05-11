import re
import os
import pandas as pd
from io import StringIO
from pdfminer.high_level import extract_text
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import nltk
import string
import re

# Custom tokenizer to avoid NLTK tokenizer dependency
def custom_tokenize(text):
    """
    Simple tokenizer that splits text on whitespace and punctuation.
    """
    # Replace punctuation with spaces
    for punct in string.punctuation:
        text = text.replace(punct, ' ')
    # Split on whitespace and filter out empty strings
    return [token.lower() for token in text.split() if token.strip()]

# Download stopwords only since we're not using NLTK tokenizers
try:
    from nltk.corpus import stopwords
    stopwords.words('english')
except (LookupError, ImportError):
    nltk.download('stopwords', quiet=True)
    from nltk.corpus import stopwords

def extract_keywords(text):
    """
    Extract significant keywords from the provided text after removing stopwords and punctuation.
    
    Args:
        text (str): Text from which to extract keywords
        
    Returns:
        list: List of keywords
    """
    if not text:
        return set()
        
    # Convert to lowercase and tokenize using our custom tokenizer
    tokens = custom_tokenize(text)
    
    # Get stopwords
    stop_words = set(stopwords.words('english'))
    
    # Filter out stopwords and single characters
    keywords = [word for word in tokens if word not in stop_words and len(word) > 1]
    
    # Return unique keywords
    return set(keywords)

def extract_years_experience(text):
    """
    Extract years of experience from resume text using regex.
    
    Args:
        text (str): Resume text
        
    Returns:
        int: Years of experience (default 0 if not found)
    """
    # More comprehensive patterns to match different formats of experience
    patterns = [
        # Standard formats
        r'(\d+)\+?\s*(?:years?|yrs?)(?:\s*of\s*)?(?:experience|exp)',
        r'(?:experience|exp)(?:\s*of\s*)?(\d+)\+?\s*(?:years?|yrs?)',
        r'(?:work(?:ed|ing)?|profession(?:al)?)\s*(?:for|with)?\s*(\d+)\+?\s*(?:years?|yrs?)',
        
        # Date ranges (e.g., "2018 - Present" or "2015-2020")
        r'(\d{4})\s*(?:-|–|to)\s*(?:present|current|now)',
        r'(\d{4})\s*(?:-|–|to)\s*(\d{4})',
        
        # Experience mentioned in job titles
        r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:as|in)\s*\w+',
        
        # Specific job durations
        r'(?:position|role|job)(?:\s*for\s*)?(\d+)\+?\s*(?:years?|yrs?)',
        
        # Simple year mentions near experience words
        r'(?:experience|exp|work).{1,30}?(\d+)\+?\s*(?:years?|yrs?)',
        r'(\d+)\+?\s*(?:years?|yrs?).{1,30}?(?:experience|exp|work)'
    ]
    
    # Parse current year for date range calculations
    import datetime
    current_year = datetime.datetime.now().year
    
    max_years = 0
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            for match in matches:
                try:
                    # Handle tuple results from regex groups
                    if isinstance(match, tuple):
                        # Check if it's a year range pattern
                        if len(match) == 2 and len(match[0]) == 4 and (len(match[1]) == 4 or match[1] == ''):
                            # Calculate years between dates
                            start_year = int(match[0])
                            end_year = current_year if match[1] == '' else int(match[1])
                            years = end_year - start_year
                        else:
                            # Use the first group if not a year range
                            years = int(match[0])
                    else:
                        years = int(match)
                    
                    # Cap reasonable experience at 45 years
                    years = min(years, 45) 
                    
                    # Only use positive, reasonable experience values
                    if years > 0:
                        max_years = max(max_years, years)
                except (ValueError, IndexError):
                    continue
    
    return max_years

def extract_education_level(text):
    """
    Detect the highest education level mentioned in the resume.
    
    Args:
        text (str): Resume text
        
    Returns:
        float: Education score based on highest degree found
    """
    # Define education levels with corresponding scores
    education_patterns = {
        r'ph\.?d\.?|doctor(?:ate|al)|d\.?phil\.?': 1.0,       # PhD
        r'master|m\.?s\.?|m\.?b\.?a\.?|m\.?eng\.?|m\.?sc\.?': 0.8,  # Master's
        r'bachelor|b\.?s\.?|b\.?a\.?|b\.?eng\.?|b\.?sc\.?|b\.?tech\.?': 0.6,  # Bachelor's
        r'associate|a\.?s\.?|a\.?a\.?': 0.4,  # Associate's
        r'high school|diploma|ged': 0.2,      # High School
    }
    
    # Find the highest education level
    max_score = 0.0
    for pattern, score in education_patterns.items():
        if re.search(pattern, text.lower()):
            max_score = max(max_score, score)
    
    return max_score

def parse_resume_text(file_content, file_type):
    """
    Extract text from resume file (txt or pdf).
    
    Args:
        file_content: File content (bytes or string)
        file_type (str): File type ('txt' or 'pdf')
        
    Returns:
        str: Extracted text from the resume
    """
    if file_type == 'txt':
        # For text files, just decode if needed
        if isinstance(file_content, bytes):
            return file_content.decode('utf-8', errors='ignore')
        return file_content
    
    elif file_type == 'pdf':
        # For PDF files, extract text using pdfminer
        try:
            return extract_text(file_content)
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    return ""

def score_resume(resume_text, job_keywords):
    """
    Score a resume based on keyword matching, years of experience, and education level.
    
    Args:
        resume_text (str): Text content of the resume
        job_keywords (set): Set of keywords extracted from the job description
        
    Returns:
        dict: Dictionary containing scores and extracted information
    """
    # Extract resume keywords
    resume_keywords = extract_keywords(resume_text)
    
    # Calculate keyword match ratio
    if job_keywords:
        matching_keywords = resume_keywords.intersection(job_keywords)
        keyword_match_ratio = len(matching_keywords) / len(job_keywords)
    else:
        keyword_match_ratio = 0
        matching_keywords = set()
    
    # Extract years of experience and calculate experience score
    years_experience = extract_years_experience(resume_text)
    # Cap experience score at 1.0 (10+ years)
    experience_score = min(years_experience / 10.0, 1.0)
    
    # Extract education level
    education_score = extract_education_level(resume_text)
    
    # Calculate final score using the given formula
    # score = 0.5 * keyword_match_ratio + 0.3 * experience_score + 0.2 * education_score
    final_score = (0.5 * keyword_match_ratio) + (0.3 * experience_score) + (0.2 * education_score)
    
    # Return comprehensive results
    return {
        'final_score': final_score,
        'keyword_match_ratio': keyword_match_ratio,
        'matching_keywords': matching_keywords,
        'years_experience': years_experience,
        'experience_score': experience_score,
        'education_score': education_score
    }

def format_results(results):
    """
    Format the screening results into a pandas DataFrame.
    
    Args:
        results (list): List of dictionaries with resume scoring results
        
    Returns:
        pd.DataFrame: Formatted DataFrame with screening results
    """
    df = pd.DataFrame(results)
    
    # Sort by final score in descending order
    df = df.sort_values('final_score', ascending=False)
    
    # Convert matching_keywords to comma-separated strings
    df['matching_keywords'] = df['matching_keywords'].apply(lambda x: ', '.join(sorted(x)))
    
    # Format scores as percentages
    df['final_score'] = (df['final_score'] * 100).round(2)
    df['keyword_match_ratio'] = (df['keyword_match_ratio'] * 100).round(2)
    df['experience_score'] = (df['experience_score'] * 100).round(2)
    df['education_score'] = (df['education_score'] * 100).round(2)
    
    # Rename columns for better presentation
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
