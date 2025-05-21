import os
import tempfile
import textract
from app.utils.logger import setup_logger
from app.utils.config import load_config
from app.utils.ai_helper import generate_text
from app.resume_processor.parser import ResumeParser
from app.resume_processor.skill_extractor import SkillExtractor

logger = setup_logger()
config = load_config()

class ResumeAnalyzer:
    """Class to analyze and tailor resumes for specific job postings"""
    
    def __init__(self):
        """Initialize the resume analyzer"""
        self.parser = ResumeParser()
        self.skill_extractor = SkillExtractor()
    
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
            contact_info = resume_data.get('contact_info', {})
            raw_text = resume_data.get('raw_text', '')
            
            # Use Google Gemini to analyze the resume
            analysis_prompt = f"""
            Analyze this resume and provide detailed professional feedback:
            
            Resume Text:
            {raw_text[:3000]}  # Limit text to prevent token overflow
            
            Provide the following information:
            1. Key skills detected (list 8-12 key technical and soft skills)
            2. Experience summary (brief 2-3 sentence summary of overall experience level and key domains)
            3. Education overview (brief summary of educational background including degrees and institutions)
            4. Strengths (4-6 points highlighting what makes this candidate strong)
            5. Improvement suggestions (4-6 specific, actionable suggestions to make the resume more effective)
            6. Industry fit (list 3-5 industries or job types this resume would be well suited for)
            
            Format your response as JSON with the keys: "skills", "experience_summary", "education_summary", "strengths", "suggestions", "industry_fit"
            """
            
            # Generate analysis using Google Gemini
            api_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or config.get('GOOGLE_GEMINI_API_KEY')
            if api_key:
                try:
                    # Setup Gemini
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    
                    # Create the model
                    model = genai.GenerativeModel('gemini-pro')
                    
                    # Generate content
                    response = model.generate_content(analysis_prompt)
                    response_text = response.text
                    
                    # Process the response text to extract JSON
                    if "```json" in response_text:
                        json_text = response_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in response_text:
                        json_text = response_text.split("```")[1].strip()
                    else:
                        json_text = response_text
                        
                    # Parse the JSON response
                    import json
                    ai_analysis = json.loads(json_text)
                    
                    logger.info("Resume analysis completed successfully using Google Gemini")
                    return {
                        'skills': ai_analysis.get('skills', skills),
                        'experience_summary': ai_analysis.get('experience_summary', ''),
                        'education_summary': ai_analysis.get('education_summary', ''),
                        'strengths': ai_analysis.get('strengths', []),
                        'suggestions': ai_analysis.get('suggestions', []),
                        'industry_fit': ai_analysis.get('industry_fit', []),
                        'ai_powered': True
                    }
                except Exception as e:
                    logger.error(f"Error using Google Gemini for resume analysis: {str(e)}")
                    # Fall back to basic analysis if Gemini fails
            
            # If we reach here, either no API key is available or Gemini analysis failed
            logger.warning("AI analysis unavailable, returning basic analysis")
            return {
                'skills': skills,
                'experience_summary': ", ".join([exp.get('title', '') for exp in experience[:3]]),
                'education_summary': ", ".join([edu.get('degree', '') for edu in education]),
                'strengths': ['Technical expertise in ' + ", ".join(skills[:5])] if skills else [],
                'suggestions': [
                    'Add more quantifiable achievements',
                    'Enhance skills section with relevant technologies',
                    'Include more specific details about project impacts',
                    'Ensure formatting is consistent and professional'
                ],
                'industry_fit': [],
                'ai_powered': False
            }
                
        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}", exc_info=True)
            # Return basic structure in case of error
            return {
                'skills': [],
                'experience_summary': '',
                'education_summary': '',
                'strengths': [],
                'suggestions': [],
                'industry_fit': [],
                'ai_powered': False
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
            
            # Extract the file extension
            _, file_extension = os.path.splitext(resume_path)
            
            # Check if we have the Google Gemini API key
            api_key = os.environ.get('GOOGLE_GEMINI_API_KEY') or config.get('GOOGLE_GEMINI_API_KEY')
            
            if api_key:
                try:
                    # Setup Gemini
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    
                    # Create the model
                    model = genai.GenerativeModel('gemini-pro')
                    
                    # Create a highly structured prompt for resume tailoring
                    tailor_prompt = f"""
                    I need to tailor this resume to better match a specific job description.
                    
                    RESUME TEXT:
                    {raw_text[:2500]}
                    
                    JOB DESCRIPTION:
                    {job_description[:2500]}
                    
                    Please analyze the job description and tailor the resume content to highlight relevant skills and experience.
                    Follow these specific instructions:
                    
                    1. Keep the same resume structure and sections (contact info, summary, education, etc.)
                    2. Identify key requirements and skills from the job description
                    3. Reword the professional summary/objective to align with the job
                    4. Reorder skills to prioritize those mentioned in the job description
                    5. Revise job experiences to emphasize relevant responsibilities and achievements
                    6. Use terminology and keywords from the job description where authentic/honest
                    7. Do NOT invent or fabricate any experience, skills, or qualifications
                    8. Maintain a professional tone and formatting
                    9. Ensure tailored content is factual based on the original resume
                    
                    Return the complete tailored resume text that I can save directly to a file.
                    """
                    
                    # Generate tailored content
                    response = model.generate_content(tailor_prompt)
                    tailored_content = response.text
                    
                    # Clean up the content if needed
                    if "```" in tailored_content:
                        tailored_content = tailored_content.replace("```", "").strip()
                        
                    logger.info("Successfully generated tailored resume with Google Gemini")
                    
                except Exception as e:
                    logger.error(f"Error using Google Gemini for resume tailoring: {str(e)}")
                    # Create a basic tailored version if Gemini fails
                    tailored_content = self._basic_resume_tailoring(resume_data, job_description)
            else:
                # Create a basic tailored version if no API key
                logger.warning("Google Gemini API key not available for resume tailoring")
                tailored_content = self._basic_resume_tailoring(resume_data, job_description)
            
            if not tailored_content:
                logger.warning("Failed to generate tailored resume content")
                return resume_path  # Return original resume if tailoring fails
            
            # Create a timestamp for the new file
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create tailored resume filename using job keywords
            # Extract first 3 words from job description for filename
            job_words = job_description.split()[:3]
            job_keyword = "_".join(job_words).replace("/", "_").replace("\\", "_").replace(":", "_")[:30]
            
            # Create tailored resume path
            tailored_resume_path = os.path.join(
                "data/tailored_resumes",
                f"tailored_resume_{job_keyword}_{timestamp}{file_extension}"
            )
            
            # Make sure the directory exists
            os.makedirs(os.path.dirname(tailored_resume_path), exist_ok=True)
            
            # Write the tailored content to a file
            with open(tailored_resume_path, 'w') as file:
                file.write(tailored_content)
                
            logger.info(f"Tailored resume saved to: {tailored_resume_path}")
            return tailored_resume_path
            
        except Exception as e:
            logger.error(f"Error tailoring resume: {str(e)}", exc_info=True)
            return resume_path  # Return original resume in case of error
    
    def _basic_resume_tailoring(self, resume_data, job_description):
        """
        Create a basic tailored resume when AI is unavailable
        
        Args:
            resume_data (dict): Parsed resume data
            job_description (str): Job description text
            
        Returns:
            str: Tailored resume content
        """
        try:
            # Extract key information
            raw_text = resume_data.get('raw_text', '')
            
            # Simple keyword matching for basic tailoring
            job_keywords = self._extract_keywords(job_description)
            sections = self._split_resume_sections(raw_text)
            
            # Modify the summary/objective section if it exists
            if 'summary' in sections or 'objective' in sections:
                section_key = 'summary' if 'summary' in sections else 'objective'
                sections[section_key] = self._enhance_section_with_keywords(
                    sections[section_key], job_keywords, is_summary=True
                )
            
            # Modify the skills section if it exists
            if 'skills' in sections:
                sections['skills'] = self._enhance_section_with_keywords(
                    sections['skills'], job_keywords
                )
            
            # Rebuild the resume text
            tailored_content = ""
            for section, content in sections.items():
                tailored_content += f"{section.upper()}\n{content}\n\n"
            
            return tailored_content
        
        except Exception as e:
            logger.error(f"Error in basic resume tailoring: {str(e)}")
            return resume_data.get('raw_text', '')
            
    def _extract_keywords(self, job_description):
        """Extract key terms from job description"""
        # List of common job requirement keywords
        common_skill_indicators = [
            'required', 'requirements', 'qualifications', 'skills', 
            'proficient', 'experience with', 'knowledge of', 'familiar with',
            'ability to', 'understanding of', 'expertise in'
        ]
        
        # Split into lines and process
        keywords = []
        description_lower = job_description.lower()
        
        # Extract terms that follow skill indicators
        for indicator in common_skill_indicators:
            if indicator in description_lower:
                parts = description_lower.split(indicator)
                for part in parts[1:]:  # Skip the first part (before the indicator)
                    # Take the next 10 words as potential keywords
                    words = part.split()[:10]
                    keywords.extend(words)
        
        # Clean up and deduplicate
        cleaned_keywords = []
        for word in keywords:
            word = word.strip('.,;:()"\'')
            if word and len(word) > 2 and word not in cleaned_keywords:
                cleaned_keywords.append(word)
                
        return cleaned_keywords
    
    def _split_resume_sections(self, resume_text):
        """Split resume into different sections"""
        # Common section headers in resumes
        section_headers = [
            'summary', 'objective', 'experience', 'work experience', 
            'employment', 'education', 'skills', 'qualifications',
            'projects', 'certifications', 'awards', 'references'
        ]
        
        # Initialize sections dict
        sections = {}
        current_section = 'header'  # Default for content before first section
        sections[current_section] = ""
        
        # Split the resume into lines
        lines = resume_text.split('\n')
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if this line is a section header
            is_header = False
            for header in section_headers:
                if header in line_lower and len(line_lower) < 50:  # Avoid matching text within paragraphs
                    current_section = header
                    sections[current_section] = ""
                    is_header = True
                    break
            
            # If not a header, add content to current section
            if not is_header:
                sections[current_section] += line + "\n"
        
        return sections
    
    def _enhance_section_with_keywords(self, section_text, keywords, is_summary=False):
        """Enhance a section by incorporating job keywords"""
        if is_summary:
            # For summary, add a tailored sentence
            relevant_keywords = [k for k in keywords if k not in section_text.lower()][:5]
            if relevant_keywords:
                tailored_sentence = f"Experienced professional with expertise in {', '.join(relevant_keywords)}.\n"
                return tailored_sentence + section_text
            return section_text
        else:
            # For other sections, just highlight existing matching skills
            enhanced_text = section_text
            for keyword in keywords:
                if keyword in section_text.lower():
                    # Find the line containing the keyword
                    lines = section_text.split('\n')
                    for i, line in enumerate(lines):
                        if keyword in line.lower():
                            # Add an asterisk to highlight this line if not already there
                            if not line.strip().startswith('*'):
                                lines[i] = "* " + line.strip()
                    enhanced_text = '\n'.join(lines)
            return enhanced_text
            
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
            
            # First use NLP-based skill extraction
            logger.info("Using NLP-based skill extraction to match resume and job")
            skill_analysis = self.skill_extractor.extract_and_compare(raw_text, job_description)
            
            # Get the skill comparison results
            comparison = skill_analysis.get('comparison', {})
            match_percentage = comparison.get('match_percentage', 0)
            matching_skills = comparison.get('matching_skills', [])
            missing_skills = comparison.get('missing_skills', [])
            
            # Create detailed categories breakdown
            category_breakdown = {}
            for category, data in comparison.get('categories', {}).items():
                if data.get('matching') or data.get('missing'):
                    category_breakdown[category] = {
                        'match_percentage': data.get('match_percentage', 0),
                        'matching': data.get('matching', []),
                        'missing': data.get('missing', [])
                    }
            
            # Use AI to complement the NLP analysis with qualitative insights
            match_prompt = f"""
            Evaluate how well this resume matches the job description.
            
            Resume:
            {raw_text[:2000]}  # Reduced length to make room for NLP results
            
            Job Description:
            {job_description[:1000]}
            
            NLP Skill Analysis:
            * Match Percentage: {match_percentage}%
            * Matching Skills: {', '.join(matching_skills[:10])}
            * Missing Skills: {', '.join(missing_skills[:10])}
            
            Please provide:
            1. A qualitative assessment of the match (strengths and weaknesses)
            2. Suggestions for how to better align the resume with this job
            3. Brief explanation of overall fit
            
            Format your response as JSON with the keys: "qualitative_assessment", "suggestions", "explanation"
            """
            
            # Generate qualitative insights using AI
            ai_insights = generate_text(match_prompt, return_json=True)
            
            # Combine NLP and AI analysis for comprehensive results
            if ai_insights:
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
