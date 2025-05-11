import time
from utils import extract_keywords, score_resume, format_results

def process_resumes_serial(job_description, resumes):
    """
    Process resumes serially (one by one).
    
    Args:
        job_description (str): Job description text
        resumes (list): List of dictionaries containing resume data
            Each dict should have 'text' and 'name' keys
            
    Returns:
        tuple: (DataFrame with results, execution time in seconds)
    """
    start_time = time.time()
    
    # Extract keywords from job description
    job_keywords = extract_keywords(job_description)
    
    # Process each resume
    results = []
    for resume in resumes:
        resume_text = resume['text']
        file_name = resume['name']
        
        # Score the resume
        result = score_resume(resume_text, job_keywords)
        result['file_name'] = file_name
        
        results.append(result)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Format results into a DataFrame
    results_df = format_results(results)
    
    return results_df, execution_time
