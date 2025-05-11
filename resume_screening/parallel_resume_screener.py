import time
import multiprocessing
from functools import partial
from utils import extract_keywords, score_resume, format_results

def process_single_resume(resume, job_keywords):
    """
    Process a single resume - to be used by parallel processor.
    
    Args:
        resume (dict): Dictionary containing resume data with 'text' and 'name' keys
        job_keywords (set): Set of keywords extracted from job description
        
    Returns:
        dict: Dictionary with scoring results
    """
    resume_text = resume['text']
    file_name = resume['name']
    
    # Score the resume
    result = score_resume(resume_text, job_keywords)
    result['file_name'] = file_name
    
    return result

def process_resumes_parallel(job_description, resumes):
    """
    Process resumes in parallel using multiprocessing.
    
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
    
    # Set up the process pool with as many workers as there are CPU cores
    num_cores = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(processes=num_cores)
    
    # Create a partial function with the job keywords
    process_resume_with_keywords = partial(process_single_resume, job_keywords=job_keywords)
    
    # Process resumes in parallel
    results = pool.map(process_resume_with_keywords, resumes)
    
    # Clean up
    pool.close()
    pool.join()
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Format results into a DataFrame
    results_df = format_results(results)
    
    return results_df, execution_time
