"""
Module for filtering job postings based on basic criteria before detailed analysis.
This implements the initial programmatic filtering step from the development plan.
"""
import re
from collections import Counter
import string
from app.utils.logger import setup_logger
from app.utils.config import load_config

logger = setup_logger()
config = load_config()

class JobFilter:
    """Class to filter job postings based on resume and configuration parameters"""
    
    def __init__(self):
        """Initialize the job filter"""
        self.config = load_config()
        self.min_salary = int(self.config.get('TARGET_PAY_GRADE_MIN', '70000'))
        self.target_location = self.config.get('TARGET_LOCATION', 'New York, NY')
        
    def filter_jobs(self, jobs, resume_text):
        """
        Filter jobs based on basic criteria:
        1. Keyword matching between resume and job description
        2. Pay grade comparison with TARGET_PAY_GRADE_MIN config
        3. Location matching with TARGET_LOCATION config
        
        Args:
            jobs (list): List of job posting dictionaries
            resume_text (str): Full text of the parsed resume
            
        Returns:
            list: Filtered list of job postings
        """
        logger.info(f"Filtering {len(jobs)} jobs using programmatic criteria")
        
        if not jobs:
            logger.warning("No jobs to filter")
            return []
            
        # Extract high-frequency terms from resume
        resume_keywords = self._extract_keywords_from_text(resume_text)
        logger.info(f"Extracted {len(resume_keywords)} high-frequency keywords from resume")
        
        filtered_jobs = []
        
        for job in jobs:
            # Initialize match score
            match_score = 0
            match_reasons = []
            
            # 1. Keyword matching
            if 'description' in job and job['description']:
                keyword_score = self._calculate_keyword_match(resume_keywords, job['description'])
                if keyword_score > 0.2:  # At least 20% keyword match
                    match_score += 1
                    match_reasons.append(f"Keyword match: {int(keyword_score * 100)}%")
            
            # 2. Pay grade matching
            if 'salary' in job and job['salary']:
                salary_match = self._check_salary_match(job['salary'])
                if salary_match:
                    match_score += 1
                    match_reasons.append("Salary meets minimum requirement")
            
            # 3. Location matching
            if 'location' in job and job['location']:
                location_match = self._check_location_match(job['location'])
                if location_match:
                    match_score += 1
                    match_reasons.append("Location match")
            
            # A job passes the filter if it matches at least 2 criteria
            # or has a very strong keyword match (> 0.5)
            if match_score >= 2 or ('description' in job and job['description'] and 
                                    self._calculate_keyword_match(resume_keywords, job['description']) > 0.5):
                # Add filtering metadata to the job
                job['filter_match_score'] = match_score
                job['filter_match_reasons'] = match_reasons
                filtered_jobs.append(job)
        
        logger.info(f"Filtered to {len(filtered_jobs)} jobs after initial programmatic filtering")
        return filtered_jobs
    
    def _extract_keywords_from_text(self, text, max_keywords=30):
        """
        Extract the most frequent meaningful words from text
        
        Args:
            text (str): Text to extract keywords from
            max_keywords (int): Maximum number of keywords to extract
            
        Returns:
            list: List of keywords
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Split into words
        words = text.split()
        
        # Remove common stop words
        stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'in', 'on', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'of', 'off',
            'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
            'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'some', 'such', 'no',
            'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will',
            'just', 'don', 'should', 'now', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
            'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs',
            'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am',
            'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'would', 'could', 'should',
            'might', 'must', 'much', 'many'
        }
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Count word frequencies
        word_counts = Counter(filtered_words)
        
        # Get the most common words
        top_words = [word for word, count in word_counts.most_common(max_keywords)]
        
        return top_words
    
    def _calculate_keyword_match(self, keywords, job_description):
        """
        Calculate the keyword match score between resume keywords and job description
        
        Args:
            keywords (list): List of keywords from resume
            job_description (str): Job description text
            
        Returns:
            float: Match score (0-1)
        """
        if not keywords or not job_description:
            return 0
            
        # Convert job description to lowercase
        job_description = job_description.lower()
        
        # Count how many keywords appear in the job description
        matches = sum(1 for keyword in keywords if keyword in job_description)
        
        # Calculate match score (ratio of matching keywords)
        return matches / len(keywords)
    
    def _check_salary_match(self, salary_text):
        """
        Check if the salary in the job posting meets the minimum requirement
        
        Args:
            salary_text (str): Salary information from job posting
            
        Returns:
            bool: True if salary meets or exceeds minimum, False otherwise
        """
        if not salary_text:
            return False
            
        # Try to extract salary numbers from text
        salary_numbers = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)', salary_text)
        
        if not salary_numbers:
            return False
            
        # Convert extracted numbers to integers
        extracted_salaries = []
        for num in salary_numbers:
            # Remove commas
            num = num.replace(',', '')
            
            try:
                value = float(num)
                
                # Convert hourly rate to annual (assuming 40hrs/week, 52 weeks)
                if value < 1000:  # Probably hourly rate
                    value = value * 40 * 52
                    
                extracted_salaries.append(value)
            except ValueError:
                continue
        
        if not extracted_salaries:
            return False
            
        # Check if any extracted salary meets the minimum
        return any(salary >= self.min_salary for salary in extracted_salaries)
    
    def _check_location_match(self, job_location):
        """
        Check if the job location matches the target location
        
        Args:
            job_location (str): Location from job posting
            
        Returns:
            bool: True if locations match, False otherwise
        """
        if not job_location or not self.target_location:
            return False
            
        # Normalize locations for comparison
        job_loc = job_location.lower()
        target_loc = self.target_location.lower()
        
        # Split locations into components (city, state)
        job_components = job_loc.replace(',', ' ').split()
        target_components = target_loc.replace(',', ' ').split()
        
        # Check for component matches
        for component in target_components:
            if component in job_components:
                return True
                
        # Also check for substring match (e.g., "New York" in "New York City")
        if target_loc in job_loc or job_loc in target_loc:
            return True
            
        return False