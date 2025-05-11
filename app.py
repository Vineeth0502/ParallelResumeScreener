import streamlit as st
import pandas as pd
import time
import io
import matplotlib.pyplot as plt
from io import StringIO, BytesIO
import os
import tempfile

# Import resume screeners
from serial_resume_screener import process_resumes_serial
from parallel_resume_screener import process_resumes_parallel
from utils import parse_resume_text

# Set page title
st.set_page_config(page_title="Resume Screening App", layout="wide")

def main():
    st.title("Resume Screening Application")
    st.write("""
    Upload a job description and multiple resumes to see which candidates match the job requirements best.
    The app will analyze and score each resume based on keyword matches, years of experience, and education level.
    """)

    # Create tabs for different sections
    tab1, tab2 = st.tabs(["Upload & Process", "About"])

    with tab1:
        col1, col2 = st.columns([1, 1])

        with col1:
            # Job Description input
            st.subheader("Job Description")
            job_desc_option = st.radio(
                "Choose input method for job description:",
                ["Upload a .txt file", "Enter text directly"]
            )

            job_description = ""
            if job_desc_option == "Upload a .txt file":
                job_desc_file = st.file_uploader("Upload Job Description (TXT)", type=["txt"])
                if job_desc_file is not None:
                    job_description = job_desc_file.getvalue().decode("utf-8")
                    st.success("Job description uploaded successfully!")
            else:
                job_description = st.text_area(
                    "Enter job description here:", 
                    height=300, 
                    placeholder="Paste the job description text here..."
                )

        with col2:
            # Resume uploads
            st.subheader("Resumes")
            resume_files = st.file_uploader(
                "Upload Resumes (TXT or PDF)", 
                type=["txt", "pdf"], 
                accept_multiple_files=True
            )

            st.write(f"Number of resumes uploaded: {len(resume_files)}")

            # Processing option
            processing_mode = st.radio(
                "Choose processing mode:",
                ["Serial", "Parallel", "Both (for comparison)"]
            )

        # Process button
        process_button = st.button("Process Resumes", type="primary")

        if process_button:
            if not job_description:
                st.error("Please provide a job description.")
            elif not resume_files:
                st.error("Please upload at least one resume.")
            else:
                # Process the resumes
                with st.spinner("Processing resumes..."):
                    # Parse resume files
                    resumes = []
                    for resume_file in resume_files:
                        file_type = resume_file.name.split('.')[-1].lower()

                        # Create a temporary file for PDF processing
                        if file_type == 'pdf':
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                                tmp.write(resume_file.getvalue())
                                tmp_path = tmp.name

                            resume_text = parse_resume_text(tmp_path, file_type)
                            # Remove the temporary file
                            os.unlink(tmp_path)
                        else:
                            resume_text = parse_resume_text(resume_file.getvalue(), file_type)

                        resumes.append({
                            'text': resume_text,
                            'name': resume_file.name
                        })

                    # Process based on selected mode
                    results_serial = None
                    results_parallel = None
                    time_serial = 0
                    time_parallel = 0

                    if processing_mode in ["Serial", "Both (for comparison)"]:
                        results_serial, time_serial = process_resumes_serial(job_description, resumes)

                    if processing_mode in ["Parallel", "Both (for comparison)"]:
                        results_parallel, time_parallel = process_resumes_parallel(job_description, resumes)

                # Display results
                st.subheader("Screening Results")

                if processing_mode == "Both (for comparison)":
                    st.write(f"Serial processing time: {time_serial:.4f} seconds")
                    st.write(f"Parallel processing time: {time_parallel:.4f} seconds")

                    if time_serial > 0:
                        speedup = time_serial / time_parallel
                        st.write(f"Speedup: {speedup:.2f}x")

                    st.write("Both processing methods produce identical results. Showing results from parallel processing:")
                    results_df = results_parallel

                    # Create a bar chart to compare processing times
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.bar(['Serial', 'Parallel'], [time_serial, time_parallel])
                    ax.set_ylabel('Processing Time (seconds)')
                    ax.set_title('Processing Time Comparison')
                    st.pyplot(fig)

                elif processing_mode == "Serial":
                    st.write(f"Processing time: {time_serial:.4f} seconds")
                    results_df = results_serial
                else:  # Parallel
                    st.write(f"Processing time: {time_parallel:.4f} seconds")
                    results_df = results_parallel

                # Display the results table
                st.dataframe(results_df)

                # Create a bar chart of resume scores
                st.subheader("Resume Scores Comparison")
                fig, ax = plt.subplots(figsize=(12, 6))

                # Extract top 10 resumes by score
                top_resumes = results_df.head(10)

                # Create horizontal bar chart
                ax.barh(top_resumes['Resume'], top_resumes['Final Score (%)'])
                ax.set_xlabel('Score (%)')
                ax.set_ylabel('Resume')
                ax.set_title('Top 10 Resume Scores')
                ax.invert_yaxis()  # Higher scores at the top

                # Set x-axis limit to 100%
                ax.set_xlim(0, 100)

                st.pyplot(fig)

                # Option to download results as CSV
                csv = results_df.to_csv(index=False)
                st.download_button(
                    label="Download Results as CSV",
                    data=csv,
                    file_name="resume_screening_results.csv",
                    mime="text/csv",
                )

                # Option to save top 10 resumes to a new CSV
                top10_csv = top_resumes.to_csv(index=False)
                st.download_button(
                    label="Download Top 10 Resumes as CSV",
                    data=top10_csv,
                    file_name="top10_resumes.csv",
                    mime="text/csv",
                )

    with tab2:
        st.subheader("About this App")
        st.write("""
        This resume screening application helps recruiters and hiring managers sift through large numbers of resumes 
        to find the best matches for job openings. The application uses a combination of keyword matching, 
        experience detection, and education level assessment to score each resume.

        ### How it works:

        1. **Keyword Matching (50% of score)**: The app extracts keywords from the job description and 
           matches them against each resume.

        2. **Experience Detection (30% of score)**: Using regular expressions, the app detects mentions of years 
           of experience in the resume text.

        3. **Education Level (20% of score)**: The app identifies the highest education level mentioned in the resume.

        4. **Final Score**: A weighted combination of these three factors determines the final score.

        ### Processing Modes:

        - **Serial Processing**: Processes each resume one after another (suitable for small batches).
        - **Parallel Processing**: Utilizes multiple CPU cores to process resumes simultaneously (faster for large batches).
        - **Both**: Runs both methods and compares performance.

        ### Tips for Best Results:

        - Ensure your job description contains specific keywords relevant to the position.
        - For PDFs, ensure the text is properly embedded (not scanned images).
        - The more specific the job description, the more accurate the screening will be.
        """)

if __name__ == "__main__":
    main()
