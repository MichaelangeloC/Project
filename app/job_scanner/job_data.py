import uuid
from datetime import datetime

class JobData:
    """Class to represent job posting data"""
    
    def __init__(self, id=None, title="", company="", location="", description="", 
                 url="", source="", date_found=None, status="Not Applied", matching_score=0):
        """
        Initialize a job data object
        
        Args:
            id (str): Unique identifier for the job
            title (str): Job title
            company (str): Company name
            location (str): Job location
            description (str): Job description
            url (str): URL to the job posting
            source (str): Source of the job posting (e.g., Indeed, LinkedIn)
            date_found (str): Date the job was found (YYYY-MM-DD)
            status (str): Current status (Not Applied, Applied, Interview, Rejected, Offer)
            matching_score (int): Score indicating how well the job matches user preferences (0-100)
        """
        self.id = id if id else str(uuid.uuid4())
        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.url = url
        self.source = source
        self.date_found = date_found if date_found else datetime.now().strftime('%Y-%m-%d')
        self.status = status
        self.matching_score = matching_score
    
    def to_dict(self):
        """
        Convert job data to dictionary
        
        Returns:
            dict: Dictionary representation of job data
        """
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'url': self.url,
            'source': self.source,
            'date_found': self.date_found,
            'status': self.status,
            'matching_score': self.matching_score
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create job data object from dictionary
        
        Args:
            data (dict): Dictionary containing job data
            
        Returns:
            JobData: New job data object
        """
        return cls(
            id=data.get('id'),
            title=data.get('title', ''),
            company=data.get('company', ''),
            location=data.get('location', ''),
            description=data.get('description', ''),
            url=data.get('url', ''),
            source=data.get('source', ''),
            date_found=data.get('date_found'),
            status=data.get('status', 'Not Applied'),
            matching_score=data.get('matching_score', 0)
        )
