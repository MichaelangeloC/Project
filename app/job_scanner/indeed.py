import os
import time
import uuid
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import trafilatura
from app.utils.logger import setup_logger
from app.utils.config import load_config
from app.job_scanner.job_data import JobData

logger = setup_logger()
config = load_config()

class IndeedJobScanner:
    """Class to scan Indeed for job postings"""
    
    def __init__(self):
        """Initialize the Indeed job scanner"""
        self.base_url = "https://www.indeed.com"
        self.search_url = f"{self.base_url}/jobs"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Referer": "https://www.indeed.com/",
            "DNT": "1",
        }
        # Rate limiting parameters
        self.request_delay = 2  # Delay between requests in seconds
        self.max_jobs = 50  # Maximum number of jobs to fetch
    
    def scan(self, keywords, location, min_salary=0, max_pages=3):
        """
        Scan Indeed for job postings
        
        Args:
            keywords (str): Job search keywords
            location (str): Job location
            min_salary (int): Minimum salary
            max_pages (int): Maximum number of pages to scan
            
        Returns:
            list: List of job postings as dictionaries
        """
        logger.info(f"Scanning Indeed for: {keywords} in {location} with min salary: {min_salary}")
        
        jobs = []
        formatted_keywords = keywords.replace(' ', '+')
        formatted_location = location.replace(' ', '+').replace(',', '%2C')
        
        # Check robots.txt compliance
        self._check_robots_txt()
        
        for page in range(max_pages):
            logger.info(f"Scanning Indeed page {page + 1}/{max_pages}")
            
            # Construct search URL with pagination
            start_param = page * 10
            search_query = f"{self.search_url}?q={formatted_keywords}&l={formatted_location}"
            if min_salary > 0:
                search_query += f"&salary=${min_salary}"
            if start_param > 0:
                search_query += f"&start={start_param}"
            
            try:
                # Get search results page
                logger.debug(f"Requesting URL: {search_query}")
                response = requests.get(search_query, headers=self.headers)
                
                if response.status_code != 200:
                    logger.warning(f"Received status code {response.status_code} from Indeed. Stopping scan.")
                    break
                
                # Parse job listings
                soup = BeautifulSoup(response.text, 'html.parser')
                job_listings = soup.select('div.job_seen_beacon')
                
                if not job_listings:
                    logger.info("No job listings found on this page. Moving to next page.")
                    continue
                
                # Process each job listing
                for job in job_listings:
                    if len(jobs) >= self.max_jobs:
                        logger.info(f"Reached maximum job limit ({self.max_jobs}). Stopping scan.")
                        return jobs
                    
                    try:
                        # Extract job details
                        job_id = job.get('id', f"indeed_{uuid.uuid4()}")
                        
                        # Find title
                        title_element = job.select_one('h2.jobTitle span:not([class])')
                        title = title_element.text.strip() if title_element else "Unknown Title"
                        
                        # Find company
                        company_element = job.select_one('span.companyName')
                        company = company_element.text.strip() if company_element else "Unknown Company"
                        
                        # Find location
                        location_element = job.select_one('div.companyLocation')
                        job_location = location_element.text.strip() if location_element else "Unknown Location"
                        
                        # Find job URL
                        job_link_element = job.select_one('h2.jobTitle a')
                        job_path = job_link_element.get('href', '') if job_link_element else ''
                        job_url = f"{self.base_url}{job_path}" if job_path.startswith('/') else job_path
                        
                        # Get job description by visiting the job page
                        description = self._get_job_description(job_url)
                        
                        # Calculate a basic matching score
                        # In a real app, this would be more sophisticated
                        matching_score = self._calculate_matching_score(title, description, keywords)
                        
                        # Create job data object
                        job_data = JobData(
                            id=job_id,
                            title=title,
                            company=company,
                            location=job_location,
                            description=description,
                            url=job_url,
                            source="Indeed",
                            date_found=datetime.now().strftime('%Y-%m-%d'),
                            status="Not Applied",
                            matching_score=matching_score
                        )
                        
                        jobs.append(job_data.to_dict())
                        logger.debug(f"Found job: {title} at {company}")
                        
                    except Exception as e:
                        logger.error(f"Error parsing job listing: {str(e)}", exc_info=True)
                    
                    # Respect rate limits
                    time.sleep(self.request_delay)
                
                logger.info(f"Processed {len(job_listings)} job listings from page {page + 1}")
                
                # Check if there are more pages
                next_button = soup.select_one('a[data-testid="pagination-page-next"]')
                if not next_button:
                    logger.info("No more pages available. Stopping scan.")
                    break
                
                # Respect rate limits between pages
                time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"Error scanning Indeed page {page + 1}: {str(e)}", exc_info=True)
        
        logger.info(f"Indeed scan complete. Found {len(jobs)} job postings.")
        return jobs
    
    def _get_job_description(self, job_url):
        """
        Get the job description from the job page
        
        Args:
            job_url (str): URL of the job posting
            
        Returns:
            str: Job description
        """
        try:
            logger.debug(f"Fetching job description from: {job_url}")
            
            # Get the job page
            downloaded = trafilatura.fetch_url(job_url)
            if not downloaded:
                logger.warning(f"Failed to download job page: {job_url}")
                return "No description available"
                
            # Extract the main content
            description = trafilatura.extract(downloaded)
            
            if not description:
                logger.warning(f"Failed to extract description from job page: {job_url}")
                return "No description available"
                
            return description
                
        except Exception as e:
            logger.error(f"Error fetching job description: {str(e)}", exc_info=True)
            return "Error fetching description"
        
    def _calculate_matching_score(self, title, description, keywords):
        """
        Calculate a matching score for the job based on keywords
        
        Args:
            title (str): Job title
            description (str): Job description
            keywords (str): Job search keywords
            
        Returns:
            int: Matching score (0-100)
        """
        try:
            # Basic scoring algorithm - count keyword occurrences
            # In a real app, this would use more sophisticated NLP
            keywords_list = keywords.lower().split()
            score = 0
            
            # Check title (higher weight)
            title_lower = title.lower()
            for keyword in keywords_list:
                if keyword in title_lower:
                    score += 15
            
            # Check description
            description_lower = description.lower()
            for keyword in keywords_list:
                # Count occurrences in description
                count = description_lower.count(keyword)
                # Cap the contribution from any single keyword
                score += min(count * 3, 15)
            
            # Normalize to 0-100
            score = min(score, 100)
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating matching score: {str(e)}", exc_info=True)
            return 50  # Default middle score
    
    def _check_robots_txt(self):
        """
        Check robots.txt to ensure compliance
        
        Raises:
            Exception: If robots.txt disallows access
        """
        try:
            robots_url = f"{self.base_url}/robots.txt"
            response = requests.get(robots_url, headers=self.headers)
            
            if response.status_code != 200:
                logger.warning(f"Could not fetch robots.txt, proceeding with caution: {response.status_code}")
                return
            
            # Check if our user agent is allowed to access jobs
            robots_txt = response.text
            
            # Very basic parsing - in a real app, use a proper robots.txt parser
            disallowed_paths = []
            current_agent = None
            
            for line in robots_txt.split('\n'):
                line = line.strip()
                
                if line.startswith('User-agent:'):
                    agent = line.split(':', 1)[1].strip()
                    if agent == '*' or agent in self.headers['User-Agent']:
                        current_agent = agent
                    else:
                        current_agent = None
                
                elif line.startswith('Disallow:') and current_agent:
                    path = line.split(':', 1)[1].strip()
                    disallowed_paths.append(path)
            
            # Check if /jobs or /viewjob paths are disallowed
            for path in disallowed_paths:
                if path == '/jobs' or path == '/viewjob':
                    error_msg = f"Access to {path} is disallowed by robots.txt. Stopping scan."
                    logger.error(error_msg)
                    raise Exception(error_msg)
            
            logger.info("Robots.txt checked, proceeding with scan")
            
        except Exception as e:
            logger.error(f"Error checking robots.txt: {str(e)}", exc_info=True)
            # Continue but with caution
