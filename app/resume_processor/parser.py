import os
import re
from datetime import datetime
import textract
from app.utils.logger import setup_logger
from app.utils.config import load_config

logger = setup_logger()
config = load_config()

class ResumeParser:
    """Class to parse and extract information from resumes"""
    
    def __init__(self):
        """Initialize the resume parser"""
        pass
    
    def parse(self, resume_path):
        """
        Parse a resume and extract structured information
        
        Args:
            resume_path (str): Path to the resume file
            
        Returns:
            dict: Structured information extracted from the resume
        """
        logger.info(f"Parsing resume: {resume_path}")
        
        try:
            # Check if file exists
            if not os.path.exists(resume_path):
                logger.error(f"Resume file not found: {resume_path}")
                raise FileNotFoundError(f"Resume file not found: {resume_path}")
            
            # Extract text from PDF
            text = self._extract_text(resume_path)
            
            # Extract structured information
            result = {
                'contact_info': self._extract_contact_info(text),
                'skills': self._extract_skills(text),
                'education': self._extract_education(text),
                'experience': self._extract_experience(text),
                'raw_text': text
            }
            
            logger.info(f"Resume parsed successfully: {resume_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}", exc_info=True)
            raise
    
    def _extract_text(self, resume_path):
        """
        Extract text from a resume file
        
        Args:
            resume_path (str): Path to the resume file
            
        Returns:
            str: Extracted text
        """
        try:
            # Extract text from PDF or Word document
            text = textract.process(resume_path).decode('utf-8')
            
            # Clean up the text
            text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace with single space
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from resume: {str(e)}", exc_info=True)
            raise
    
    def _extract_contact_info(self, text):
        """
        Extract contact information from resume text
        
        Args:
            text (str): Resume text
            
        Returns:
            dict: Contact information
        """
        contact_info = {
            'name': '',
            'email': '',
            'phone': '',
            'linkedin': '',
            'github': '',
            'portfolio': ''
        }
        
        try:
            # Extract email
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_match = re.search(email_pattern, text)
            if email_match:
                contact_info['email'] = email_match.group()
            
            # Extract phone number
            phone_pattern = r'(?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'
            phone_match = re.search(phone_pattern, text)
            if phone_match:
                contact_info['phone'] = phone_match.group()
            
            # Extract LinkedIn URL
            linkedin_pattern = r'linkedin\.com/in/[a-zA-Z0-9-]+'
            linkedin_match = re.search(linkedin_pattern, text)
            if linkedin_match:
                contact_info['linkedin'] = linkedin_match.group()
            
            # Extract GitHub URL
            github_pattern = r'github\.com/[a-zA-Z0-9-]+'
            github_match = re.search(github_pattern, text)
            if github_match:
                contact_info['github'] = github_match.group()
            
            # Extract portfolio URL
            portfolio_pattern = r'https?://(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
            portfolio_matches = re.findall(portfolio_pattern, text)
            for url in portfolio_matches:
                if 'linkedin.com' not in url and 'github.com' not in url:
                    contact_info['portfolio'] = url
                    break
            
            return contact_info
            
        except Exception as e:
            logger.error(f"Error extracting contact info: {str(e)}", exc_info=True)
            return contact_info
    
    def _extract_skills(self, text):
        """
        Extract skills from resume text
        
        Args:
            text (str): Resume text
            
        Returns:
            list: Skills extracted from the resume
        """
        try:
            # Look for skills section
            skills_section = self._extract_section(text, ['skills', 'technical skills', 'expertise', 'technologies'])
            
            # If no dedicated skills section, use entire text
            if not skills_section:
                skills_section = text
            
            # Common programming languages, frameworks, tools
            tech_skills = [
                'python', 'java', 'javascript', 'typescript', 'c\\+\\+', 'c#', 'ruby', 'php', 'go', 'rust', 'swift',
                'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring', 'asp.net',
                'html', 'css', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'oracle', 'azure', 'aws', 'gcp',
                'kubernetes', 'docker', 'jenkins', 'ci/cd', 'git', 'github', 'gitlab', 'bitbucket',
                'agile', 'scrum', 'kanban', 'jira', 'confluence', 'devops', 'machine learning', 'ai',
                'data science', 'data analysis', 'data visualization', 'tableau', 'power bi',
                'tensorflow', 'pytorch', 'keras', 'pandas', 'numpy', 'scipy', 'scikit-learn'
            ]
            
            # Extract skills
            skills = []
            for skill in tech_skills:
                if re.search(r'\b' + skill + r'\b', skills_section.lower()):
                    # Convert to proper case for display
                    if skill == 'python':
                        skills.append('Python')
                    elif skill == 'javascript':
                        skills.append('JavaScript')
                    elif skill == 'typescript':
                        skills.append('TypeScript')
                    elif skill == 'c\\+\\+':
                        skills.append('C++')
                    elif skill == 'node.js':
                        skills.append('Node.js')
                    elif skill == 'asp.net':
                        skills.append('ASP.NET')
                    elif skill == 'ci/cd':
                        skills.append('CI/CD')
                    else:
                        skills.append(skill.title())
            
            return skills
            
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}", exc_info=True)
            return []
    
    def _extract_education(self, text):
        """
        Extract education information from resume text
        
        Args:
            text (str): Resume text
            
        Returns:
            list: Education entries
        """
        try:
            # Look for education section
            education_section = self._extract_section(text, ['education', 'academic background', 'academic credentials'])
            
            # If no dedicated education section, use entire text
            if not education_section:
                education_section = text
            
            # Extract degree information
            education = []
            
            # Common degree patterns
            degree_patterns = [
                r'(B\.?S\.?|Bachelor of Science|Bachelor\'?s?)\s(?:in|of)?\s?([^,\n]+)',
                r'(B\.?A\.?|Bachelor of Arts|Bachelor\'?s?)\s(?:in|of)?\s?([^,\n]+)',
                r'(M\.?S\.?|Master of Science|Master\'?s?)\s(?:in|of)?\s?([^,\n]+)',
                r'(M\.?A\.?|Master of Arts|Master\'?s?)\s(?:in|of)?\s?([^,\n]+)',
                r'(Ph\.?D\.?|Doctor of Philosophy|Doctorate)\s(?:in|of)?\s?([^,\n]+)',
                r'(MBA|Master of Business Administration)',
                r'(MD|Doctor of Medicine)',
                r'(JD|Juris Doctor|Doctor of Law)'
            ]
            
            for pattern in degree_patterns:
                matches = re.finditer(pattern, education_section, re.IGNORECASE)
                for match in matches:
                    # Try to find university name near the degree
                    surrounding_text = education_section[max(0, match.start() - 100):min(len(education_section), match.end() + 100)]
                    university_patterns = [
                        r'(University of [A-Za-z\s]+)',
                        r'([A-Za-z\s]+) University',
                        r'([A-Za-z\s]+) College',
                        r'(College of [A-Za-z\s]+)',
                        r'(Institute of [A-Za-z\s]+)',
                        r'([A-Za-z\s]+) Institute'
                    ]
                    
                    university = None
                    for uni_pattern in university_patterns:
                        uni_match = re.search(uni_pattern, surrounding_text)
                        if uni_match:
                            university = uni_match.group(1)
                            break
                    
                    # Try to find graduation year
                    year_match = re.search(r'(19|20)\d{2}', surrounding_text)
                    year = year_match.group() if year_match else 'Present'
                    
                    # Extract the degree and field
                    degree_type = match.group(1) if len(match.groups()) > 0 else ''
                    field = match.group(2) if len(match.groups()) > 1 else ''
                    
                    education.append({
                        'degree': f"{degree_type} {field}".strip(),
                        'university': university or 'Unknown University',
                        'year': year
                    })
            
            return education
            
        except Exception as e:
            logger.error(f"Error extracting education: {str(e)}", exc_info=True)
            return []
    
    def _extract_experience(self, text):
        """
        Extract work experience from resume text
        
        Args:
            text (str): Resume text
            
        Returns:
            list: Work experience entries
        """
        try:
            # Look for experience section
            experience_section = self._extract_section(text, ['experience', 'work experience', 'professional experience', 'employment'])
            
            # If no dedicated experience section, use entire text
            if not experience_section:
                experience_section = text
            
            # Extract job titles and companies
            job_patterns = [
                r'((?:Senior|Junior|Lead|Principal|Staff|Chief)?\s?(?:Software|Developer|Frontend|Backend|Full Stack|Full-Stack|Web|Mobile|iOS|Android|Cloud|DevOps|ML|AI|Data|QA|Test|Project|Product|Program|Technical|Solutions|Systems|Security|Network|Database|Infrastructure)\s?(?:Engineer|Developer|Architect|Specialist|Analyst|Scientist|Manager|Lead|Consultant|Administrator))',
                r'((?:Director|VP|Vice President|Manager|Head)\s?(?:of|,)?\s?(?:Engineering|Software|Development|Technology|IT|Product|Program|Project))'
            ]
            
            experience = []
            
            for pattern in job_patterns:
                matches = re.finditer(pattern, experience_section)
                for match in matches:
                    # Look for surrounding text to extract company and dates
                    surrounding_text = experience_section[max(0, match.start() - 100):min(len(experience_section), match.end() + 100)]
                    
                    # Try to extract company name
                    company_match = re.search(r'at\s+([A-Za-z0-9\s&.,]+)', surrounding_text)
                    company = company_match.group(1).strip() if company_match else 'Unknown Company'
                    
                    # Try to extract dates
                    date_pattern = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\s*[-–—]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|Present|Current'
                    date_match = re.search(date_pattern, surrounding_text)
                    dates = date_match.group() if date_match else 'Unknown Dates'
                    
                    # Extract responsibilities
                    bullets = []
                    bullet_section = surrounding_text[match.end():]
                    bullet_matches = re.finditer(r'[•\-*]\s+([^•\-*\n]+)', bullet_section)
                    for bullet_match in bullet_matches:
                        if len(bullets) < 3:  # Limit to 3 bullet points
                            bullets.append(bullet_match.group(1).strip())
                    
                    experience.append({
                        'title': match.group(1),
                        'company': company,
                        'dates': dates,
                        'responsibilities': bullets
                    })
            
            return experience
            
        except Exception as e:
            logger.error(f"Error extracting experience: {str(e)}", exc_info=True)
            return []
    
    def _extract_section(self, text, section_names):
        """
        Extract a section from the resume text
        
        Args:
            text (str): Resume text
            section_names (list): Possible section names
            
        Returns:
            str: Extracted section text
        """
        try:
            # Create regex pattern for section headers
            pattern = '|'.join(section_names)
            section_headers = re.finditer(r'(?i)(?:^|\n)((?:' + pattern + r')[\s:]*)\n', text)
            
            for match in section_headers:
                section_start = match.end()
                
                # Find the next section header
                next_section_match = re.search(r'(?:^|\n)([A-Z][A-Za-z\s]+:?\s*)\n', text[section_start:])
                if next_section_match:
                    section_end = section_start + next_section_match.start()
                else:
                    section_end = len(text)
                
                # Extract the section text
                section_text = text[section_start:section_end].strip()
                return section_text
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting section: {str(e)}", exc_info=True)
            return None
