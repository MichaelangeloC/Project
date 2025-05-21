import os
import time
from datetime import datetime
from app.utils.logger import setup_logger
from app.utils.config import load_config
from app.utils.ai_helper import generate_text
from app.resume_processor.parser import ResumeParser

logger = setup_logger()
config = load_config()

class CoverLetterGenerator:
    """Class to generate personalized cover letters"""
    
    def __init__(self):
        """Initialize the cover letter generator"""
        self.parser = ResumeParser()
        
        # Load template
        template_path = os.path.join("templates", "cover_letter_template.txt")
        try:
            if os.path.exists(template_path):
                with open(template_path, 'r') as file:
                    self.template = file.read()
            else:
                # Default template if file doesn't exist
                self.template = """
                [Your Name]
                [Your Address]
                [City, State ZIP]
                [Your Email]
                [Your Phone]
                [Date]
                
                [Hiring Manager's Name]
                [Company Name]
                [Company Address]
                [City, State ZIP]
                
                Dear [Hiring Manager's Name or "Hiring Manager"],
                
                I am writing to express my interest in the [Job Title] position at [Company Name]. With my background in [Your Background] and skills in [Key Skills], I am confident in my ability to contribute effectively to your team.
                
                [First Paragraph: Explain why you're interested in the role and company]
                
                [Second Paragraph: Highlight relevant experience and achievements]
                
                [Third Paragraph: Connect your skills to the job requirements]
                
                [Closing Paragraph: Thank them, express enthusiasm, and mention follow-up]
                
                Sincerely,
                
                [Your Name]
                """
        except Exception as e:
            logger.error(f"Error loading cover letter template: {str(e)}", exc_info=True)
            # Default template if there's an error
            self.template = "Dear Hiring Manager,\n\n[Cover letter content will be generated here]\n\nSincerely,\n[Your Name]"
    
    def generate(self, resume_path, job_title, company_name, job_description):
        """
        Generate a personalized cover letter
        
        Args:
            resume_path (str): Path to the resume file
            job_title (str): Job title
            company_name (str): Company name
            job_description (str): Job description
            
        Returns:
            str: Path to the generated cover letter
        """
        logger.info(f"Generating cover letter for {job_title} at {company_name}")
        
        try:
            # Parse resume to get relevant information
            resume_data = self.parser.parse(resume_path)
            
            # Extract key information
            contact_info = resume_data.get('contact_info', {})
            skills = resume_data.get('skills', [])
            experience = resume_data.get('experience', [])
            raw_text = resume_data.get('raw_text', '')
            
            # Check if Google Gemini API key is available
            api_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or config.get('GOOGLE_GEMINI_API_KEY')
            
            # Create a highly detailed prompt for the cover letter
            generate_prompt = f"""
            Generate a personalized cover letter for a job application based on the applicant's resume and the job details.
            
            Resume Summary:
            {raw_text[:2000]}
            
            Job Title: {job_title}
            Company: {company_name}
            Job Description:
            {job_description[:1500]}
            
            The cover letter should:
            1. Be professionally formatted with today's date: {datetime.now().strftime('%B %d, %Y')}
            2. Address the hiring manager generically if no name is provided
            3. Express specific interest in this role and company (research the company if specific details are in the job description)
            4. Highlight 4-5 relevant skills and experience that directly match the job requirements
            5. Include 2-3 specific achievements with measurable results that demonstrate value
            6. Show enthusiasm and explain precisely why the applicant is a good fit for this specific role
            7. Have a confident, professional closing paragraph that includes a call to action
            8. Be 350-450 words total (3-4 well-structured paragraphs)
            9. Use professional language but avoid overly generic phrases and clichés
            10. Include the applicant's contact information in the header

            Use the applicant's name in the signature if available in the resume. Format the letter professionally
            with proper spacing and alignment.
            """
            
            # Generate cover letter content with Google Gemini if available
            if api_key:
                try:
                    # Setup Gemini
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    
                    # Create the model
                    model = genai.GenerativeModel('gemini-pro')
                    
                    # Generate content
                    response = model.generate_content(generate_prompt)
                    cover_letter_content = response.text
                    
                    # Clean up the content if needed
                    if "```" in cover_letter_content:
                        cover_letter_content = cover_letter_content.replace("```", "").strip()
                        
                    logger.info("Successfully generated cover letter with Google Gemini")
                except Exception as e:
                    logger.error(f"Error using Google Gemini for cover letter: {str(e)}")
                    # Fall back to basic AI helper
                    cover_letter_content = generate_text(generate_prompt)
            else:
                # Use standard AI helper if Gemini not available
                logger.warning("Google Gemini API key not available for cover letter generation")
                cover_letter_content = generate_text(generate_prompt)
            
            if not cover_letter_content:
                logger.warning("Failed to generate cover letter content")
                cover_letter_content = "Error generating cover letter content. Please try again."
            
            # Create directory for cover letters if it doesn't exist
            cover_letters_dir = os.path.join("data", "cover_letters")
            os.makedirs(cover_letters_dir, exist_ok=True)
            
            # Create filename for cover letter
            sanitized_company = company_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            sanitized_title = job_title.replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f"{sanitized_company}_{sanitized_title}_{int(time.time())}.txt"
            
            # Save cover letter to file
            cover_letter_path = os.path.join(cover_letters_dir, filename)
            with open(cover_letter_path, 'w') as file:
                file.write(cover_letter_content)
            
            logger.info(f"Cover letter generated successfully: {cover_letter_path}")
            return cover_letter_path
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {str(e)}", exc_info=True)
            
            # Create error cover letter
            error_filename = f"error_cover_letter_{int(time.time())}.txt"
            error_path = os.path.join("data", "cover_letters", error_filename)
            
            os.makedirs(os.path.dirname(error_path), exist_ok=True)
            
            with open(error_path, 'w') as file:
                file.write(f"""
                ERROR GENERATING COVER LETTER
                
                Job Title: {job_title}
                Company: {company_name}
                
                Error: {str(e)}
                
                Please regenerate this cover letter manually.
                """)
            
            return error_path
    
    def customize_template(self, template_content, job_title, company_name, resume_data):
        """
        Customize a cover letter template with job and resume information
        
        Args:
            template_content (str): Cover letter template content
            job_title (str): Job title
            company_name (str): Company name
            resume_data (dict): Parsed resume data
            
        Returns:
            str: Customized cover letter content
        """
        try:
            # Extract information from resume data
            contact_info = resume_data.get('contact_info', {})
            name = contact_info.get('name', '[Your Name]')
            email = contact_info.get('email', '[Your Email]')
            phone = contact_info.get('phone', '[Your Phone]')
            
            # Get current date
            current_date = datetime.now().strftime('%B %d, %Y')
            
            # Replace template placeholders
            customized = template_content
            customized = customized.replace('[Your Name]', name)
            customized = customized.replace('[Your Email]', email)
            customized = customized.replace('[Your Phone]', phone)
            customized = customized.replace('[Date]', current_date)
            customized = customized.replace('[Job Title]', job_title)
            customized = customized.replace('[Company Name]', company_name)
            
            return customized
            
        except Exception as e:
            logger.error(f"Error customizing cover letter template: {str(e)}", exc_info=True)
            return template_content  # Return original template in case of error
