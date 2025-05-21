from app.job_scanner.indeed import IndeedJobScanner
from app.job_scanner.linkedin import LinkedInJobScanner
from app.job_scanner.demo_jobs import DemoJobScanner
from app.job_scanner.filter import JobFilter
from app.resume_processor.parser import ResumeParser
from app.resume_processor.analyzer import ResumeAnalyzer
from app.cover_letter_generator.generator import CoverLetterGenerator
from app.application_bot.submitter import ApplicationSubmitter
from app.notification_manager.email_notifier import EmailNotifier
from app.utils.logger import setup_logger
from app.utils.config import load_config

logger = setup_logger()

def run_application_workflow(job_details, resume_path):
    """
    Runs the entire application workflow for a job:
    1. Analyzes the resume
    2. Tailors the resume to the job
    3. Generates a cover letter
    4. Submits the application
    5. Sends notification if needed
    
    Args:
        job_details (dict): Contains job information
        resume_path (str): Path to the resume file
        
    Returns:
        dict: Results of the application process
    """
    logger.info(f"Starting application workflow for job: {job_details['title']} at {job_details['company']}")
    
    try:
        # Initialize components
        resume_analyzer = ResumeAnalyzer()
        cover_letter_gen = CoverLetterGenerator()
        submitter = ApplicationSubmitter()
        notifier = EmailNotifier()
        
        # 1. Analyze and tailor resume
        logger.info("Tailoring resume...")
        tailored_resume_path = resume_analyzer.tailor_resume(resume_path, job_details['description'])
        
        # 2. Generate cover letter
        logger.info("Generating cover letter...")
        cover_letter_path = cover_letter_gen.generate(
            resume_path, 
            job_details['title'], 
            job_details['company'], 
            job_details['description']
        )
        
        # 3. Submit application
        logger.info("Submitting application...")
        result = submitter.submit_application(
            job_details['url'],
            tailored_resume_path,
            cover_letter_path
        )
        
        # 4. Handle result
        if result.get('success'):
            logger.info("Application submitted successfully!")
            return {
                'success': True,
                'resume_path': tailored_resume_path,
                'cover_letter_path': cover_letter_path,
                'notes': result.get('notes', '')
            }
        else:
            logger.warning(f"Application submission failed: {result.get('error', 'Unknown error')}")
            
            # 5. Send notification for manual intervention
            notification_sent = notifier.send_notification(
                subject=f"Manual Intervention Required - {job_details['title']} at {job_details['company']}",
                job_details=job_details,
                error=result.get('error', 'Unknown error')
            )
            
            return {
                'success': False, 
                'error': result.get('error', 'Unknown error'),
                'resume_path': tailored_resume_path,
                'cover_letter_path': cover_letter_path,
                'notification_sent': notification_sent
            }
            
    except Exception as e:
        logger.error(f"Error in application workflow: {str(e)}", exc_info=True)
        return {'success': False, 'error': str(e)}

def scan_jobs(keywords, location, min_salary, sources=None, resume_path=None):
    """
    Scans for jobs using the specified sources and applies programmatic filtering
    
    Args:
        keywords (str): Job search keywords
        location (str): Job location
        min_salary (int): Minimum salary
        sources (list): List of job sources to use
        resume_path (str, optional): Path to resume file for filtering
        
    Returns:
        dict: Dictionary containing all_jobs and filtered_jobs lists
    """
    logger.info(f"Starting job scan for '{keywords}' in '{location}'")
    
    if sources is None:
        sources = ["Demo", "Indeed", "LinkedIn"]
    
    all_jobs = []
    
    try:
        # Initialize scanners based on selected sources
        scanners = []
        if "Demo" in sources:
            scanners.append(DemoJobScanner())
        if "Indeed" in sources:
            scanners.append(IndeedJobScanner())
        if "LinkedIn" in sources:
            scanners.append(LinkedInJobScanner())
        
        # Scan for jobs
        for scanner in scanners:
            logger.info(f"Scanning {scanner.__class__.__name__}...")
            jobs = scanner.scan(keywords, location, min_salary)
            all_jobs.extend(jobs)
            logger.info(f"Found {len(jobs)} jobs from {scanner.__class__.__name__}")
        
        logger.info(f"Total jobs found: {len(all_jobs)}")
        
        # Apply programmatic filtering if a resume is provided
        filtered_jobs = all_jobs
        if resume_path:
            filtered_jobs = filter_jobs_with_resume(all_jobs, resume_path)
        
        return {
            'all_jobs': all_jobs,
            'filtered_jobs': filtered_jobs
        }
        
    except Exception as e:
        logger.error(f"Error scanning for jobs: {str(e)}", exc_info=True)
        return {
            'all_jobs': [],
            'filtered_jobs': []
        }

def filter_jobs_with_resume(jobs, resume_path):
    """
    Apply programmatic filtering to jobs using resume text
    
    Args:
        jobs (list): List of job postings from scanners
        resume_path (str): Path to the resume file
        
    Returns:
        list: Filtered list of job postings
    """
    try:
        # Parse resume
        parser = ResumeParser()
        resume_data = parser.parse(resume_path)
        
        # Get full resume text for keyword matching
        resume_text = resume_data.get('raw_text', '')
        
        if not resume_text:
            logger.warning("Unable to extract text from resume, skipping filtering")
            return jobs
        
        # Apply programmatic filtering
        job_filter = JobFilter()
        filtered_jobs = job_filter.filter_jobs(jobs, resume_text)
        
        logger.info(f"Filtered {len(jobs)} jobs to {len(filtered_jobs)} relevant matches")
        return filtered_jobs
        
    except Exception as e:
        logger.error(f"Error during job filtering: {str(e)}", exc_info=True)
        return jobs  # Return all jobs if filtering fails
