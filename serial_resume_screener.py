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
    print("\n======== SERIAL RESUME PROCESSING ========")
    print(f"Job description length: {len(job_description)} characters")
    print(f"Number of resumes to process: {len(resumes)}")
    
    start_time = time.time()
    
    # Extract keywords from job description
    print("Extracting keywords from job description...")
    job_keywords = extract_keywords(job_description)
    
    # Process each resume
    results = []
    for i, resume in enumerate(resumes):
        resume_text = resume['text']
        file_name = resume['name']
        
        print(f"\nProcessing resume {i+1}/{len(resumes)}: {file_name}")
        print(f"Resume text length: {len(resume_text)} characters")
        
        # Score the resume
        result = score_resume(resume_text, job_keywords)
        result['file_name'] = file_name
        
        results.append(result)
        print(f"Completed scoring for {file_name}")
    
    # Calculate execution time
    execution_time = time.time() - start_time
    print(f"\nSerial processing completed in {execution_time:.4f} seconds")
    
    # Format results into a DataFrame
    print("Formatting results...")
    results_df = format_results(results)
    print(f"Formatted {len(results_df)} results")
    
    return results_df, execution_time
