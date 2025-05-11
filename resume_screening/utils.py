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
    print("\n===== KEYWORD EXTRACTION =====")
    print(f"Input text length: {len(text) if text else 0} characters")
    
    if not text:
        print("No text provided. Returning empty set.")
        return set()
        
    # Convert to lowercase and tokenize using our custom tokenizer
    tokens = custom_tokenize(text)
    print(f"Tokenized into {len(tokens)} tokens")
    
    # Get stopwords
    stop_words = set(stopwords.words('english'))
    print(f"Using {len(stop_words)} stopwords for filtering")
    
    # Filter out stopwords and single characters
    keywords = [word for word in tokens if word not in stop_words and len(word) > 1]
    unique_keywords = set(keywords)
    
    print(f"Extracted {len(unique_keywords)} unique keywords")
    print(f"Sample keywords (up to 10): {list(unique_keywords)[:10]}")
    
    # Return unique keywords
    return unique_keywords

def extract_years_experience(text):
    """
    Extract years of experience from resume text using regex.
    
    Args:
        text (str): Resume text
        
    Returns:
        int: Years of experience (default 0 if not found)
    """
    print("\n===== EXPERIENCE EXTRACTION =====")
    print(f"Input text length: {len(text) if text else 0} characters")
    
    if not text:
        print("No text provided. Returning 0 years.")
        return 0
        
    # Patterns specifically looking for years of experience phrases
    experience_patterns = [
        # Most common formats - only match these when specifically talking about "experience"
        r'(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|work\s+experience)',
        r'(?:with|having)\s+(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience)',
        r'(?:experience|work\s+experience)(?:\s+of)?\s+(\d+)\+?\s*(?:years?|yrs?)',
    ]
    
    # First check for explicit experience mentions
    print("Checking for explicit experience mentions...")
    for pattern in experience_patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            print(f"Found experience matches with pattern '{pattern}': {matches}")
            try:
                years = max([int(match.replace('+', '')) for match in matches if match])
                final_years = min(years, 30)  # Cap at 30 years to be reasonable
                print(f"Extracted {years} years, capped to {final_years} years")
                return final_years
            except (ValueError, TypeError) as e:
                print(f"Error processing matches: {e}")
                
    # If no explicit experience phrases found, try to determine from work history
    print("No explicit experience mentions found. Checking job history date ranges...")
    
    # Parse job dates to calculate total work history
    job_patterns = [
        # Job with year range
        r'(\d{4})\s*(?:-|–|to)\s*(?:present|current|now|till date|today|\d{4})',
    ]
    
    import datetime
    current_year = datetime.datetime.now().year
    print(f"Current year for calculations: {current_year}")
    years_list = []
    
    # Extract work experience from job listings with date ranges
    for pattern in job_patterns:
        matches = re.findall(pattern, text.lower())
        print(f"Found job date range matches: {matches}")
        for match in matches:
            try:
                start_year = int(match)
                print(f"Processing start year: {start_year}")
                # Make sure the year is reasonable (not a random 4-digit number)
                if 1950 <= start_year <= current_year:
                    years = current_year - start_year
                    print(f"Calculated {years} years from {start_year} to present")
                    if 0 < years <= 40:  # Reasonable employment period
                        years_list.append(years)
                    else:
                        print(f"Years value {years} outside reasonable range (1-40)")
                else:
                    print(f"Start year {start_year} outside reasonable range (1950-{current_year})")
            except (ValueError, TypeError) as e:
                print(f"Error processing year match: {e}")
    
    print(f"All calculated years from job history: {years_list}")
    # If we found job date ranges, use the most recent one (not the sum, as jobs might overlap)
    if years_list:
        max_years = max(years_list)
        print(f"Using maximum years from job history: {max_years}")
        return max_years
    
    # If no experience found through specific methods, look for any number near "years" 
    print("No job history experience found. Searching for general year mentions...")
    # (but be very cautious as this can lead to false positives)
    general_year_pattern = r'(\d+)\s*(?:years?|yrs?)'
    matches = re.findall(general_year_pattern, text.lower())
    print(f"Found general year mentions: {matches}")
    
    if matches:
        try:
            # Filter out unreasonable values and prefer smaller numbers as they're more likely to be experience
            valid_years = [int(y) for y in matches if 1 <= int(y) <= 20]
            print(f"Valid year values (1-20 range): {valid_years}")
            
            if valid_years:
                # For general patterns, we'll prefer numbers that are more likely to represent experience (1-15)
                for y in sorted(valid_years):
                    if 1 <= y <= 15:
                        print(f"Selecting most likely experience value: {y} years")
                        return y
                
                # If no values in the 1-15 range, use the smallest valid year found
                min_years = min(valid_years)
                print(f"No values in ideal range, using minimum: {min_years} years")
                return min_years
            else:
                print("No valid years found in reasonable range")
        except Exception as e:
            print(f"Error processing general year mentions: {e}")
    
    # No experience information found
    print("No experience information found in resume. Returning 0 years.")
    return 0

def extract_education_level(text):
    """
    Detect the highest education level mentioned in the resume.
    
    Args:
        text (str): Resume text
        
    Returns:
        float: Education score based on highest degree found
    """
    print("\n===== EDUCATION LEVEL EXTRACTION =====")
    print(f"Input text length: {len(text) if text else 0} characters")
    
    if not text:
        print("No text provided. Returning 0.0 score.")
        return 0.0
        
    # Define education levels with corresponding scores
    education_patterns = {
        # Doctorate level
        r'ph\.?d\.?|doctor(?:ate|al)|d\.?phil\.?': 1.0,       
        
        # Master's level - expanded with more variations
        r'master|m\.?s\.?|m\.?b\.?a\.?|m\.?eng\.?|m\.?sc\.?|m\.?c\.?a\.?|post.?graduate|graduate degree': 0.8,  
        
        # Bachelor's level - expanded with more variations
        r'bachelor|b\.?s\.?|b\.?a\.?|b\.?eng\.?|b\.?sc\.?|b\.?tech\.?|b\.?c\.?a\.?|college degree|undergraduate|university degree': 0.6,  
        
        # Associate's level
        r'associate|a\.?s\.?|a\.?a\.?|a\.?a\.?s\.?|community college|technical college': 0.4,  
        
        # High School level - expanded with international equivalents
        r'high school|diploma|ged|secondary school|higher secondary|12th|hsc': 0.2,      
    }
    
    # Search for education-related sections to narrow the context
    education_sections = [
        "education", "academic background", "academic qualification", 
        "qualification", "academic history", "academic profile"
    ]
    
    print(f"Checking for education section headers: {education_sections}")
    
    # Check if any education section headers exist
    has_education_section = any(re.search(r'^\s*' + section + r'[:\s]*$', text.lower(), re.MULTILINE) 
                               for section in education_sections)
    
    print(f"Resume has education section: {has_education_section}")
    
    # Find the highest education level
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
        
        # If no education level is found but the resume is substantial
        # assign a default score of bachelor's degree (most common)
        if len(text) > 500:
            max_score = 0.6  # Default to bachelor's level
            print(f"Assigning default education score for substantial resume: {max_score} (Bachelor's level)")
    
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
    print("\n\n========== RESUME SCORING PROCESS ==========")
    print(f"Resume text length: {len(resume_text) if resume_text else 0} characters")
    print(f"Job keywords: {len(job_keywords)} keywords provided")
    
    # Extract resume keywords
    resume_keywords = extract_keywords(resume_text)
    
    # Calculate keyword match ratio
    if job_keywords:
        matching_keywords = resume_keywords.intersection(job_keywords)
        keyword_match_ratio = len(matching_keywords) / len(job_keywords)
        print(f"Found {len(matching_keywords)} matching keywords out of {len(job_keywords)}")
        print(f"Keyword match ratio: {keyword_match_ratio:.4f} ({keyword_match_ratio*100:.2f}%)")
    else:
        keyword_match_ratio = 0
        matching_keywords = set()
        print("No job keywords provided. Keyword match ratio set to 0.")
    
    # Extract years of experience and calculate experience score
    years_experience = extract_years_experience(resume_text)
    
    # If no experience was detected but we have resume text, assign a default value
    # This ensures we don't penalize resumes where the experience format isn't recognized
    if years_experience == 0 and len(resume_text) > 500:  # Only for substantial resumes
        # Default to a moderate 5 years experience if not detected (middle of range)
        print("Assigning default experience value (5 years) for substantial resume with no detected experience")
        years_experience = 5
        
    # Cap experience score at 1.0 (10+ years)
    experience_score = min(years_experience / 10.0, 1.0)
    print(f"Years of experience: {years_experience}")
    print(f"Experience score: {experience_score:.4f} ({experience_score*100:.2f}%)")
    
    # Extract education level
    education_score = extract_education_level(resume_text)
    print(f"Education score: {education_score:.4f} ({education_score*100:.2f}%)")
    
    # Calculate final score using the given formula
    # score = 0.5 * keyword_match_ratio + 0.3 * experience_score + 0.2 * education_score
    final_score = (0.5 * keyword_match_ratio) + (0.3 * experience_score) + (0.2 * education_score)
    print(f"Final score calculation: 0.5 * {keyword_match_ratio:.4f} + 0.3 * {experience_score:.4f} + 0.2 * {education_score:.4f}")
    print(f"Final score: {final_score:.4f} ({final_score*100:.2f}%)")
    print("============================================\n")
    
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
