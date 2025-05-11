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
    
    # Note: in parallel mode, we can't use print statements from worker processes
    # as they will not be displayed properly in the main process output
    
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
    print("\n======== PARALLEL RESUME PROCESSING ========")
    print(f"Job description length: {len(job_description)} characters")
    print(f"Number of resumes to process: {len(resumes)}")
    
    start_time = time.time()
    
    # Extract keywords from job description
    print("Extracting keywords from job description...")
    job_keywords = extract_keywords(job_description)
    
    # Set up the process pool with as many workers as there are CPU cores
    num_cores = multiprocessing.cpu_count()
    print(f"Initializing process pool with {num_cores} CPU cores")
    pool = multiprocessing.Pool(processes=num_cores)
    
    # Create a partial function with the job keywords
    process_resume_with_keywords = partial(process_single_resume, job_keywords=job_keywords)
    
    # Process resumes in parallel
    print(f"Starting parallel processing of {len(resumes)} resumes...")
    results = pool.map(process_resume_with_keywords, resumes)
    print(f"Completed parallel processing of {len(results)} resumes")
    
    # Clean up
    print("Cleaning up process pool...")
    pool.close()
    pool.join()
    
    # Calculate execution time
    execution_time = time.time() - start_time
    print(f"Parallel processing completed in {execution_time:.4f} seconds")
    
    # Format results into a DataFrame
    print("Formatting results...")
    results_df = format_results(results)
    print(f"Formatted {len(results_df)} results")
    
    return results_df, execution_time
