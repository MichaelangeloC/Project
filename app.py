import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

from app.utils.config import load_config
from app.utils.logger import setup_logger
from app.job_scanner.job_data import JobData
from app.job_scanner.indeed import IndeedJobScanner
from app.job_scanner.linkedin import LinkedInJobScanner
from app.job_scanner.demo_jobs import DemoJobScanner
from app.resume_processor.parser import ResumeParser
from app.resume_processor.analyzer import ResumeAnalyzer
from app.cover_letter_generator.generator import CoverLetterGenerator
from app.application_bot.submitter import ApplicationSubmitter
from app.notification_manager.email_notifier import EmailNotifier

# Setup logger
logger = setup_logger()
config = load_config()

# Initialize session state variables if they don't exist
if 'jobs' not in st.session_state:
    st.session_state.jobs = pd.DataFrame(columns=[
        'id', 'title', 'company', 'location', 'description', 'url', 
        'source', 'date_found', 'status', 'matching_score'
    ])
    
if 'applications' not in st.session_state:
    st.session_state.applications = pd.DataFrame(columns=[
        'job_id', 'date_applied', 'status', 'resume_used', 'cover_letter_path', 
        'follow_up_date', 'notes'
    ])

if 'resume_path' not in st.session_state:
    st.session_state.resume_path = ""

if 'scanning_in_progress' not in st.session_state:
    st.session_state.scanning_in_progress = False

def main():
    st.title("AI-Powered Job Application Automator")
    
    # Sidebar for configuration and controls
    with st.sidebar:
        st.header("Configuration")
        
        # Resume options
        resume_option = st.radio(
            "Resume Options",
            ["Upload Your Resume", "Use Sample Resume"],
            index=1  # Default to sample resume for easier testing
        )
        
        if resume_option == "Upload Your Resume":
            # Upload resume
            uploaded_resume = st.file_uploader("Upload Resume (PDF/DOCX/TXT)", type=['pdf', 'docx', 'txt'])
            if uploaded_resume:
                # Save the uploaded resume
                resume_dir = os.path.join("data", "resumes")
                os.makedirs(resume_dir, exist_ok=True)
                
                # Get file extension
                file_extension = os.path.splitext(uploaded_resume.name)[1]
                resume_path = os.path.join(resume_dir, f"resume_{int(time.time())}{file_extension}")
                
                with open(resume_path, "wb") as f:
                    f.write(uploaded_resume.getbuffer())
                st.session_state.resume_path = resume_path
                st.success(f"Resume saved: {resume_path}")
        else:
            # Use sample resume
            sample_resume_path = os.path.join("data", "resumes", "sample_resume.txt")
            if os.path.exists(sample_resume_path):
                st.session_state.resume_path = sample_resume_path
                st.success("Using sample resume for testing")
                
                # Display sample resume details
                with st.expander("View Sample Resume Details"):
                    with open(sample_resume_path, "r") as f:
                        sample_content = f.read()
                    st.text_area("Sample Resume", sample_content, height=200)
            else:
                st.error("Sample resume not found. Please upload your own resume.")
        
        # Job search parameters
        st.subheader("Job Search Parameters")
        keywords = st.text_input("Job Keywords", "Software Engineer")
        location = st.text_input("Location", "New York, NY")
        min_salary = st.number_input("Minimum Salary ($)", min_value=0, value=70000, step=5000)
        
        # Job source selection
        job_sources = st.multiselect(
            "Job Sources", 
            ["Demo", "Indeed", "LinkedIn"],
            default=["Demo"]
        )
        
        # Start job scanning
        if st.button("Start Job Scan"):
            if not st.session_state.resume_path:
                st.error("Please upload a resume first.")
            else:
                with st.spinner("Scanning for jobs..."):
                    st.session_state.scanning_in_progress = True
                    
                    try:
                        # Initialize scanners based on selected sources
                        scanners = []
                        if "Demo" in job_sources:
                            scanners.append(DemoJobScanner())
                        if "Indeed" in job_sources:
                            scanners.append(IndeedJobScanner())
                        if "LinkedIn" in job_sources:
                            scanners.append(LinkedInJobScanner())
                        
                        # Scan for jobs
                        new_jobs = []
                        for scanner in scanners:
                            jobs = scanner.scan(keywords, location, min_salary)
                            new_jobs.extend(jobs)
                        
                        # Create DataFrame and save to session state
                        if new_jobs:
                            jobs_df = pd.DataFrame(new_jobs)
                            st.session_state.jobs = pd.concat([st.session_state.jobs, jobs_df], ignore_index=True)
                            # Drop duplicates based on job URL
                            st.session_state.jobs.drop_duplicates(subset=['url'], keep='first', inplace=True)
                            st.success(f"Found {len(new_jobs)} new job postings!")
                        else:
                            st.info("No new job postings found.")
                    except Exception as e:
                        st.error(f"Error scanning for jobs: {str(e)}")
                        logger.error(f"Job scanning error: {str(e)}", exc_info=True)
                    finally:
                        st.session_state.scanning_in_progress = False
        
        # Settings section
        st.subheader("Settings")
        auto_apply = st.checkbox("Enable Automatic Applications", value=False)
        notification_email = st.text_input("Notification Email", config.get("NOTIFICATION_EMAIL_RECEIVER", ""))
        
        # Save settings
        if st.button("Save Settings"):
            # Update configuration
            # In a production app, we would save this to a database or config file
            st.success("Settings saved successfully!")

    # Main content area - Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Job Listings", "Applications", "Resume Management", "Dashboard"])
    
    with tab1:
        st.header("Job Listings")
        
        # Filter options
        st.subheader("Filters")
        col1, col2 = st.columns(2)
        with col1:
            filter_keyword = st.text_input("Filter by keyword")
        with col2:
            filter_status = st.selectbox(
                "Filter by status",
                ["All", "Not Applied", "Applied", "Interview", "Rejected", "Offer"]
            )
        
        # Display job listings
        if not st.session_state.jobs.empty:
            # Apply filters
            filtered_jobs = st.session_state.jobs.copy()
            if filter_keyword:
                filtered_jobs = filtered_jobs[
                    filtered_jobs['title'].str.contains(filter_keyword, case=False) | 
                    filtered_jobs['company'].str.contains(filter_keyword, case=False) |
                    filtered_jobs['description'].str.contains(filter_keyword, case=False)
                ]
            if filter_status != "All":
                filtered_jobs = filtered_jobs[filtered_jobs['status'] == filter_status]
            
            # Display jobs
            for idx, job in filtered_jobs.iterrows():
                with st.expander(f"{job['title']} at {job['company']} - {job['location']}"):
                    st.write(f"**Source:** {job['source']}")
                    st.write(f"**Date Found:** {job['date_found']}")
                    st.write(f"**Status:** {job['status']}")
                    st.write(f"**Matching Score:** {job['matching_score']}")
                    st.write(f"**Description:**")
                    st.write(job['description'][:500] + "..." if len(job['description']) > 500 else job['description'])
                    st.markdown(f"[View Job]({job['url']})")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"Apply Now #{idx}"):
                            with st.spinner("Preparing application..."):
                                try:
                                    # Process application
                                    submitter = ApplicationSubmitter()
                                    resume_analyzer = ResumeAnalyzer()
                                    cover_letter_gen = CoverLetterGenerator()
                                    
                                    # Analyze resume and generate tailored materials
                                    tailored_resume = resume_analyzer.tailor_resume(
                                        st.session_state.resume_path, 
                                        job['description']
                                    )
                                    cover_letter = cover_letter_gen.generate(
                                        st.session_state.resume_path,
                                        job['title'],
                                        job['company'],
                                        job['description']
                                    )
                                    
                                    # Submit application
                                    result = submitter.submit_application(
                                        job['url'],
                                        tailored_resume,
                                        cover_letter
                                    )
                                    
                                    if result.get('success'):
                                        # Update job status
                                        st.session_state.jobs.at[idx, 'status'] = 'Applied'
                                        
                                        # Add to applications
                                        new_application = {
                                            'job_id': job['id'],
                                            'date_applied': datetime.now().strftime('%Y-%m-%d'),
                                            'status': 'Applied',
                                            'resume_used': tailored_resume,
                                            'cover_letter_path': result.get('cover_letter_path', ''),
                                            'follow_up_date': '',
                                            'notes': result.get('notes', '')
                                        }
                                        st.session_state.applications = pd.concat([
                                            st.session_state.applications, 
                                            pd.DataFrame([new_application])
                                        ], ignore_index=True)
                                        
                                        st.success("Application submitted successfully!")
                                    else:
                                        st.error(f"Failed to submit application: {result.get('error', 'Unknown error')}")
                                        
                                        # Send notification for manual intervention
                                        notifier = EmailNotifier()
                                        notifier.send_notification(
                                            subject=f"Manual Intervention Required - {job['title']} at {job['company']}",
                                            job_details=job,
                                            error=result.get('error', 'Unknown error')
                                        )
                                except Exception as e:
                                    st.error(f"Error applying to job: {str(e)}")
                                    logger.error(f"Application error: {str(e)}", exc_info=True)
                    with col2:
                        if st.button(f"Not Interested #{idx}"):
                            st.session_state.jobs.at[idx, 'status'] = 'Rejected'
                            st.info("Job marked as 'Not Interested'")
                    with col3:
                        if st.button(f"View Details #{idx}"):
                            # This would typically show a detailed view
                            # For now, we'll just display a message
                            st.info("Detailed view would open here")
        else:
            st.info("No job listings found. Start a job scan to find opportunities.")

    with tab2:
        st.header("Applications")
        
        if not st.session_state.applications.empty:
            # Group by status
            status_counts = st.session_state.applications['status'].value_counts()
            
            # Display status summary
            st.subheader("Application Status")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Applied", status_counts.get('Applied', 0))
            with col2:
                st.metric("Interview", status_counts.get('Interview', 0))
            with col3:
                st.metric("Rejected", status_counts.get('Rejected', 0))
            with col4:
                st.metric("Offer", status_counts.get('Offer', 0))
            
            # Display applications
            for idx, app in st.session_state.applications.iterrows():
                # Get job details
                job_details = st.session_state.jobs[st.session_state.jobs['id'] == app['job_id']].iloc[0]
                
                with st.expander(f"{job_details['title']} at {job_details['company']} - {app['date_applied']}"):
                    st.write(f"**Status:** {app['status']}")
                    st.write(f"**Date Applied:** {app['date_applied']}")
                    st.write(f"**Source:** {job_details['source']}")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"View Materials #{idx}"):
                            st.info("Would display resume and cover letter")
                    with col2:
                        if st.button(f"Update Status #{idx}"):
                            st.info("Would open status update form")
                    with col3:
                        if st.button(f"Add Notes #{idx}"):
                            st.info("Would open notes form")
        else:
            st.info("No applications submitted yet.")

    with tab3:
        st.header("Resume Management")
        
        if st.session_state.resume_path:
            st.success(f"Current resume: {os.path.basename(st.session_state.resume_path)}")
            
            # Resume analysis
            if st.button("Analyze Resume"):
                with st.spinner("Analyzing resume..."):
                    try:
                        parser = ResumeParser()
                        analyzer = ResumeAnalyzer()
                        
                        # Parse and analyze resume
                        resume_data = parser.parse(st.session_state.resume_path)
                        resume_analysis = analyzer.analyze(resume_data)
                        
                        # Display analysis
                        st.subheader("Resume Analysis")
                        st.write("**Skills Detected:**")
                        st.write(", ".join(resume_analysis.get('skills', [])))
                        
                        st.write("**Experience Summary:**")
                        for exp in resume_analysis.get('experience', []):
                            st.write(f"- {exp}")
                        
                        st.write("**Improvement Suggestions:**")
                        for suggestion in resume_analysis.get('suggestions', []):
                            st.write(f"- {suggestion}")
                    except Exception as e:
                        st.error(f"Error analyzing resume: {str(e)}")
                        logger.error(f"Resume analysis error: {str(e)}", exc_info=True)
        else:
            st.warning("No resume uploaded. Please upload your resume in the sidebar.")

    with tab4:
        st.header("Dashboard")
        
        # Progress metrics
        st.subheader("Application Progress")
        
        jobs_count = len(st.session_state.jobs)
        applications_count = len(st.session_state.applications)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Jobs Found", jobs_count)
        with col2:
            st.metric("Applications Submitted", applications_count)
        with col3:
            application_rate = 0 if jobs_count == 0 else round((applications_count / jobs_count) * 100, 1)
            st.metric("Application Rate", f"{application_rate}%")
        
        # Recent activity timeline
        st.subheader("Recent Activity")
        activity_data = []
        
        # Add recent job findings
        if not st.session_state.jobs.empty:
            recent_jobs = st.session_state.jobs.sort_values('date_found', ascending=False).head(5)
            for _, job in recent_jobs.iterrows():
                activity_data.append({
                    'date': job['date_found'],
                    'activity': f"Found: {job['title']} at {job['company']}",
                    'type': 'found'
                })
                
        # Add recent applications
        if not st.session_state.applications.empty:
            recent_applications = st.session_state.applications.sort_values('date_applied', ascending=False).head(5)
            for _, app in recent_applications.iterrows():
                job_details = st.session_state.jobs[st.session_state.jobs['id'] == app['job_id']].iloc[0]
                activity_data.append({
                    'date': app['date_applied'],
                    'activity': f"Applied: {job_details['title']} at {job_details['company']}",
                    'type': 'applied'
                })
        
        # Sort and display activity
        if activity_data:
            activity_df = pd.DataFrame(activity_data)
            activity_df = activity_df.sort_values('date', ascending=False)
            
            for _, activity in activity_df.iterrows():
                st.write(f"**{activity['date']}**: {activity['activity']}")
        else:
            st.info("No recent activity to display.")

if __name__ == "__main__":
    main()
