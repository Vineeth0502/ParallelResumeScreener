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
    if not text:
        return 0
        
    # Patterns specifically looking for years of experience phrases
    experience_patterns = [
        # Most common formats - only match these when specifically talking about "experience"
        r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|work\s+experience)',
        r'(?:with|having)\s+(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience)',
        r'(?:experience|work\s+experience)(?:\s+of)?\s+(\d+)\+?\s*(?:years?|yrs?)',
    ]
    
    # First check for explicit experience mentions
    for pattern in experience_patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            try:
                years = max([int(match.replace('+', '')) for match in matches if match])
                return min(years, 30)  # Cap at 30 years to be reasonable
            except (ValueError, TypeError):
                pass
                
    # If no explicit experience phrases found, try to determine from work history
    # Parse job dates to calculate total work history
    job_patterns = [
        # Job with year range
        r'(\d{4})\s*(?:-|–|to)\s*(?:present|current|now|till date|today|\d{4})',
    ]
    
    import datetime
    current_year = datetime.datetime.now().year
    years_list = []
    
    # Extract work experience from job listings with date ranges
    for pattern in job_patterns:
        matches = re.findall(pattern, text.lower())
        for match in matches:
            try:
                start_year = int(match)
                # Make sure the year is reasonable (not a random 4-digit number)
                if 1950 <= start_year <= current_year:
                    years = current_year - start_year
                    if 0 < years <= 40:  # Reasonable employment period
                        years_list.append(years)
            except (ValueError, TypeError):
                pass
    
    # If we found job date ranges, use the most recent one (not the sum, as jobs might overlap)
    if years_list:
        return max(years_list)
    
    # If no experience found through specific methods, look for any number near "years" 
    # (but be very cautious as this can lead to false positives)
    general_year_pattern = r'(\d+)\s*(?:years?|yrs?)'
    matches = re.findall(general_year_pattern, text.lower())
    if matches:
        # Filter out unreasonable values and prefer smaller numbers as they're more likely to be experience
        valid_years = [int(y) for y in matches if 1 <= int(y) <= 20]
        if valid_years:
            # For general patterns, we'll prefer numbers that are more likely to represent experience (1-15)
            for y in sorted(valid_years):
                if 1 <= y <= 15:
                    return y
            # If no values in the 1-15 range, use the smallest valid year found
            return min(valid_years)
    
    # No experience information found
    return 0

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
