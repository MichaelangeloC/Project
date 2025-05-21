import os
import time
import uuid
from datetime import datetime
from app.utils.logger import setup_logger
from app.utils.config import load_config
from app.job_scanner.job_data import JobData

logger = setup_logger()
config = load_config()

class DemoJobScanner:
    """Class to provide demo job postings for testing"""
    
    def __init__(self):
        """Initialize the demo job scanner"""
        logger.info("Initializing Demo Job Scanner")
        
    def scan(self, keywords, location, min_salary=0, max_pages=3):
        """
        Provide demo job postings that match keywords
        
        Args:
            keywords (str): Job search keywords
            location (str): Job location
            min_salary (int): Minimum salary
            max_pages (int): Maximum number of pages to scan
            
        Returns:
            list: List of job postings as dictionaries
        """
        logger.info(f"Demo scanning for jobs: {keywords} in {location}")
        
        # Create sample jobs that match the keywords
        jobs = []
        
        # Extract main keywords for matching
        main_keywords = [k.strip().lower() for k in keywords.split(',')]
        if len(main_keywords) == 1 and ' ' in main_keywords[0]:
            main_keywords = main_keywords[0].split()
        
        # Generate relevant job titles based on keywords
        job_titles = self._generate_job_titles(main_keywords)
        companies = self._get_sample_companies()
        
        # Generate sample jobs
        for i in range(min(10, len(job_titles))):
            job_id = str(uuid.uuid4())
            title = job_titles[i]
            company = companies[i % len(companies)]
            description = self._generate_job_description(title, main_keywords)
            url = f"https://example.com/jobs/{job_id}"
            salary = min_salary + (i * 5000)
            matching_score = 100 - (i * 5)  # First job is best match
            
            # Create job data
            job = JobData(
                id=job_id,
                title=title,
                company=company,
                location=location,
                description=description,
                url=url,
                source="Demo",
                date_found=datetime.now().strftime("%Y-%m-%d"),
                status="Not Applied",
                matching_score=matching_score
            ).to_dict()
            
            jobs.append(job)
            
            # Add a small delay to make it feel more realistic
            time.sleep(0.5)
        
        logger.info(f"Demo scan complete, found {len(jobs)} jobs")
        return jobs
    
    def _generate_job_titles(self, keywords):
        """Generate job titles based on keywords"""
        base_titles = [
            "Software Engineer", 
            "Web Developer", 
            "Data Scientist",
            "Product Manager",
            "UX Designer",
            "DevOps Engineer",
            "Machine Learning Engineer",
            "QA Engineer",
            "Frontend Developer",
            "Backend Developer",
            "Full Stack Developer",
            "Mobile Developer"
        ]
        
        prefixes = ["Senior", "Lead", "Principal", "Staff", "Junior", "Associate"]
        suffixes = ["", "I", "II", "III", "IV", "V"]
        
        # Generate titles based on keywords
        titles = []
        for keyword in keywords:
            if keyword.lower() in [t.lower() for t in base_titles]:
                # If the keyword is already a job title
                titles.append(keyword)
                titles.append(f"Senior {keyword}")
                titles.append(f"Lead {keyword}")
            else:
                # Generate titles that incorporate the keyword
                for title in base_titles:
                    if len(titles) < 15:  # Limit number of titles
                        if keyword.lower() in ["python", "java", "javascript", "react", "node", "aws", "cloud"]:
                            titles.append(f"{title} ({keyword})")
                        else:
                            titles.append(f"{keyword} {title}")
        
        # If not enough titles were generated, add some generic ones
        while len(titles) < 10:
            prefix = prefixes[len(titles) % len(prefixes)]
            base = base_titles[len(titles) % len(base_titles)]
            suffix = suffixes[len(titles) % len(suffixes)]
            
            title = f"{prefix} {base}{(' ' + suffix) if suffix else ''}"
            if title not in titles:
                titles.append(title)
        
        return titles
    
    def _get_sample_companies(self):
        """Get a list of sample companies"""
        return [
            "TechCorp Inc.",
            "Innovate Solutions",
            "Digital Dynamics",
            "ByteWave Systems",
            "NextGen Software",
            "Cloud Pioneers",
            "DataSphere Analytics",
            "FutureTech Enterprises",
            "CodeCraft Labs",
            "Quantum Computing"
        ]
    
    def _generate_job_description(self, title, keywords):
        """Generate a job description based on title and keywords"""
        tech_stacks = {
            "frontend": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Angular", "Vue.js"],
            "backend": ["Node.js", "Python", "Java", "C#", ".NET", "Ruby", "PHP", "Go"],
            "database": ["SQL", "MongoDB", "PostgreSQL", "MySQL", "Redis", "DynamoDB"],
            "cloud": ["AWS", "Azure", "Google Cloud", "Kubernetes", "Docker", "Terraform"],
            "data": ["Python", "R", "SQL", "Pandas", "NumPy", "TensorFlow", "PyTorch", "Scikit-learn"]
        }
        
        # Determine relevant tech stack based on title
        relevant_stacks = []
        if any(term in title.lower() for term in ["frontend", "web", "ui", "ux"]):
            relevant_stacks.extend(["frontend", "backend"])
        elif any(term in title.lower() for term in ["backend", "server"]):
            relevant_stacks.extend(["backend", "database"])
        elif any(term in title.lower() for term in ["full stack", "fullstack"]):
            relevant_stacks.extend(["frontend", "backend", "database"])
        elif any(term in title.lower() for term in ["data", "scientist", "analyst"]):
            relevant_stacks.extend(["data", "database"])
        elif any(term in title.lower() for term in ["devops", "cloud", "infrastructure"]):
            relevant_stacks.extend(["cloud", "backend"])
        else:
            # Default to a mix of stacks
            relevant_stacks = list(tech_stacks.keys())
        
        # Generate required skills based on relevant stacks
        required_skills = []
        for stack in relevant_stacks:
            required_skills.extend(tech_stacks[stack][:3])  # Take first 3 from each relevant stack
        
        # Add keywords to required skills
        for keyword in keywords:
            if keyword.lower() not in [skill.lower() for skill in required_skills]:
                required_skills.append(keyword.capitalize())
        
        # Generate job description
        description = f"""
        # About the Role
        
        We are seeking a talented {title} to join our team. The ideal candidate will have experience with {', '.join(required_skills[:3])} and a passion for building high-quality software solutions.
        
        # Responsibilities
        
        - Design, develop, and maintain software applications using {', '.join(required_skills[:2])}
        - Collaborate with cross-functional teams to define, design, and ship new features
        - Ensure the performance, quality, and responsiveness of applications
        - Identify and correct bottlenecks and fix bugs
        - Help maintain code quality, organization, and automatization
        
        # Requirements
        
        - {3-7} years of experience with {', '.join(required_skills[:3])}
        - Bachelor's degree in Computer Science, Engineering or related field
        - Strong problem solving skills and attention to detail
        - Excellent communication and teamwork skills
        - Experience with {', '.join(required_skills[3:5])} is a plus
        
        # Benefits
        
        - Competitive salary and benefits package
        - Flexible work schedule and remote options
        - Professional development opportunities
        - Collaborative and innovative work environment
        - Health, dental, and vision insurance
        
        Join our team and help us build the next generation of technology solutions!
        """
        
        return description