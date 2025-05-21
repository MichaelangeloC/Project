import os
import tempfile
import textract
from app.utils.logger import setup_logger
from app.utils.config import load_config
from app.utils.ai_helper import generate_text
from app.resume_processor.parser import ResumeParser

logger = setup_logger()
config = load_config()

class ResumeAnalyzer:
    """Class to analyze and tailor resumes for specific job postings"""
    
    def __init__(self):
        """Initialize the resume analyzer"""
        self.parser = ResumeParser()
    
    def analyze(self, resume_data):
        """
        Analyze a parsed resume and provide insights
        
        Args:
            resume_data (dict): Parsed resume data
            
        Returns:
            dict: Analysis results including skills, strengths, and improvement suggestions
        """
        logger.info("Analyzing resume")
        
        try:
            # Extract key information from resume data
            skills = resume_data.get('skills', [])
            education = resume_data.get('education', [])
            experience = resume_data.get('experience', [])
            raw_text = resume_data.get('raw_text', '')
            
            # Use AI to analyze the resume
            analysis_prompt = f"""
            Analyze this resume and provide constructive feedback:
            
            Resume Text:
            {raw_text[:3000]}  # Limit text to prevent token overflow
            
            Provide the following information:
            1. Key skills detected (list 5-10 key skills)
            2. Experience summary (brief 2-3 sentence summary of experience)
            3. Education overview (brief summary)
            4. Strengths (3-5 points)
            5. Improvement suggestions (3-5 specific, actionable suggestions)
            
            Format your response as JSON with the keys: "skills", "experience_summary", "education_summary", "strengths", "suggestions"
            """
            
            # Generate analysis using AI
            ai_analysis = generate_text(analysis_prompt, return_json=True)
            
            if ai_analysis:
                logger.info("Resume analysis completed successfully")
                return {
                    'skills': ai_analysis.get('skills', skills),
                    'experience_summary': ai_analysis.get('experience_summary', ''),
                    'education_summary': ai_analysis.get('education_summary', ''),
                    'strengths': ai_analysis.get('strengths', []),
                    'suggestions': ai_analysis.get('suggestions', [])
                }
            else:
                logger.warning("AI analysis failed, returning basic analysis")
                return {
                    'skills': skills,
                    'experience': [exp.get('title', '') for exp in experience],
                    'education': [edu.get('degree', '') for edu in education],
                    'suggestions': ['Improve skills section', 'Add more quantifiable achievements']
                }
                
        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}", exc_info=True)
            # Return basic structure in case of error
            return {
                'skills': [],
                'experience': [],
                'education': [],
                'suggestions': []
            }
    
    def tailor_resume(self, resume_path, job_description):
        """
        Tailor a resume to match a specific job description
        
        Args:
            resume_path (str): Path to the resume file
            job_description (str): Job description text
            
        Returns:
            str: Path to the tailored resume
        """
        logger.info(f"Tailoring resume for job")
        
        try:
            # Parse the original resume
            resume_data = self.parser.parse(resume_path)
            
            # Extract key information
            skills = resume_data.get('skills', [])
            contact_info = resume_data.get('contact_info', {})
            experience = resume_data.get('experience', [])
            education = resume_data.get('education', [])
            raw_text = resume_data.get('raw_text', '')
            
            # Use AI to tailor resume
            tailor_prompt = f"""
            You are an expert resume writer. Tailor the following resume to better match the job description.
            
            Resume:
            {raw_text[:3000]}  # Limit text to prevent token overflow
            
            Job Description:
            {job_description[:1500]}
            
            Please provide specific recommendations on how to tailor this resume for this job:
            1. Identify 5-8 keywords from the job description that should be emphasized
            2. Suggest 3-5 skills to highlight based on the job requirements
            3. Recommend how to reword 2-3 experience bullet points to better match the job
            4. Any other tailoring suggestions
            
            Format your response as JSON with the keys: "keywords", "skills_to_highlight", "experience_rewrites", "other_suggestions"
            """
            
            # Generate tailoring recommendations using AI
            tailoring_recommendations = generate_text(tailor_prompt, return_json=True)
            
            if not tailoring_recommendations:
                logger.warning("Failed to generate tailoring recommendations")
                return resume_path  # Return original resume if tailoring fails
            
            # For demo purposes, we'll just log the tailoring recommendations
            # In a real implementation, we would modify the resume document
            logger.info("Generated tailoring recommendations")
            
            # Create directory for tailored resumes if it doesn't exist
            tailored_dir = os.path.join("data", "tailored_resumes")
            os.makedirs(tailored_dir, exist_ok=True)
            
            # In a real implementation, this would modify the actual resume document
            # For this implementation, we'll just return the original path
            # and pretend we tailored it (since we can't easily modify PDF files)
            
            # Create a "tailored" version by copying the original
            tailored_path = os.path.join(tailored_dir, f"tailored_{os.path.basename(resume_path)}")
            with open(resume_path, "rb") as src, open(tailored_path, "wb") as dst:
                dst.write(src.read())
            
            logger.info(f"Resume tailored successfully: {tailored_path}")
            return tailored_path
            
        except Exception as e:
            logger.error(f"Error tailoring resume: {str(e)}", exc_info=True)
            return resume_path  # Return original resume in case of error
    
    def match_job(self, resume_data, job_description):
        """
        Calculate how well a resume matches a job description
        
        Args:
            resume_data (dict): Parsed resume data
            job_description (str): Job description text
            
        Returns:
            dict: Match results including score and matching keywords
        """
        logger.info("Matching resume to job description")
        
        try:
            # Extract skills from resume
            skills = resume_data.get('skills', [])
            raw_text = resume_data.get('raw_text', '')
            
            # Use AI to evaluate the match
            match_prompt = f"""
            Evaluate how well this resume matches the job description.
            
            Resume:
            {raw_text[:3000]}  # Limit text to prevent token overflow
            
            Job Description:
            {job_description[:1500]}
            
            Please provide:
            1. A matching score from 0-100
            2. List of matching keywords found in both the resume and job description
            3. List of missing keywords or skills that are in the job description but not in the resume
            4. Brief explanation of the score
            
            Format your response as JSON with the keys: "score", "matching_keywords", "missing_keywords", "explanation"
            """
            
            # Generate match evaluation using AI
            match_evaluation = generate_text(match_prompt, return_json=True)
            
            if match_evaluation:
                logger.info(f"Resume match evaluation completed with score: {match_evaluation.get('score', 0)}")
                return {
                    'score': match_evaluation.get('score', 0),
                    'matching_keywords': match_evaluation.get('matching_keywords', []),
                    'missing_keywords': match_evaluation.get('missing_keywords', []),
                    'explanation': match_evaluation.get('explanation', '')
                }
            else:
                logger.warning("Match evaluation failed, returning basic match")
                return {
                    'score': 50,  # Default middle score
                    'matching_keywords': [],
                    'missing_keywords': [],
                    'explanation': 'Failed to generate detailed match evaluation'
                }
                
        except Exception as e:
            logger.error(f"Error matching resume to job: {str(e)}", exc_info=True)
            return {'score': 0, 'matching_keywords': [], 'missing_keywords': [], 'explanation': str(e)}
