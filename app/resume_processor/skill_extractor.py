"""
Module for extracting and comparing skills from resumes and job descriptions
using NLP techniques.
"""
import os
import re
import string
import json
from collections import Counter
import spacy
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from app.utils.logger import setup_logger
from app.utils.config import load_config

# Initialize logger and config
logger = setup_logger()
config = load_config()

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
    logger.info("Loaded spaCy en_core_web_sm model")
except Exception as e:
    logger.error(f"Error loading spaCy model: {str(e)}")
    logger.warning("Will use basic pattern matching for skill extraction")
    nlp = None

# Initialize NLTK components
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

class SkillExtractor:
    """Class to extract skills from text using NLP techniques"""
    
    def __init__(self):
        """Initialize the skill extractor"""
        self.nlp = nlp
        self.skill_patterns = self._load_skill_patterns()
        
    def _load_skill_patterns(self):
        """
        Load skill patterns from JSON file or create a default set
        
        Returns:
            dict: Dictionary of skill categories and patterns
        """
        # Path to skill patterns file
        patterns_file = os.path.join("app", "data", "skill_patterns.json")
        
        # Try to load from file
        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'r') as f:
                    patterns = json.load(f)
                logger.info(f"Loaded skill patterns from {patterns_file}")
                return patterns
            except Exception as e:
                logger.error(f"Error loading skill patterns: {str(e)}")
                
        # Create default patterns if file doesn't exist or loading fails
        logger.info("Creating default skill patterns")
        return {
            "programming_languages": [
                "python", "java", "javascript", "typescript", "c\\+\\+", "c#", "ruby", 
                "php", "go", "rust", "swift", "kotlin", "scala", "perl", "r", "dart"
            ],
            "frameworks_libraries": [
                "react", "angular", "vue", "node.js", "express", "django", "flask", 
                "spring", "asp.net", "laravel", "symfony", "rails", "flutter", 
                "tensorflow", "pytorch", "keras", "scikit-learn", "jquery", "bootstrap"
            ],
            "databases": [
                "sql", "mysql", "postgresql", "mongodb", "sqlite", "oracle", "redis", 
                "cassandra", "dynamodb", "firestore", "elasticsearch", "neo4j"
            ],
            "cloud_devops": [
                "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "terraform", 
                "ansible", "ci/cd", "git", "github", "gitlab", "bitbucket", "aws lambda",
                "serverless", "microservices", "cloud computing"
            ],
            "software_tools": [
                "jira", "confluence", "trello", "slack", "figma", "sketch", "adobe", 
                "photoshop", "illustrator", "xd", "zeplin", "tableau", "power bi", 
                "excel", "powerpoint", "word", "linux", "unix", "windows", "macos"
            ],
            "methodologies": [
                "agile", "scrum", "kanban", "waterfall", "lean", "test-driven development", 
                "behavior-driven development", "devops", "continuous integration", 
                "continuous deployment", "continuous delivery", "pair programming"
            ],
            "machine_learning": [
                "machine learning", "deep learning", "artificial intelligence", "ai", 
                "natural language processing", "nlp", "computer vision", "neural networks",
                "data mining", "predictive modeling", "reinforcement learning",
                "supervised learning", "unsupervised learning", "classification", 
                "regression", "clustering"
            ],
            "soft_skills": [
                "communication", "teamwork", "problem solving", "leadership", "time management",
                "critical thinking", "adaptability", "collaboration", "presentation",
                "negotiation", "conflict resolution", "emotional intelligence"
            ]
        }
        
    def extract_skills(self, text):
        """
        Extract skills from text using NLP techniques
        
        Args:
            text (str): Text to extract skills from
            
        Returns:
            dict: Dictionary with skill categories and extracted skills
        """
        logger.info("Extracting skills from text using NLP")
        
        if not text:
            logger.warning("Empty text provided for skill extraction")
            return {}
            
        # Preprocess text
        preprocessed_text = self._preprocess_text(text)
        
        # Extract skills using pattern matching
        skills = self._extract_skills_with_patterns(preprocessed_text)
        
        # Extract skills using spaCy NER and POS tagging if available
        if self.nlp is not None:
            spacy_skills = self._extract_skills_with_spacy(text)
            
            # Merge skills from both methods
            for category, category_skills in spacy_skills.items():
                if category in skills:
                    skills[category] = list(set(skills[category] + category_skills))
                else:
                    skills[category] = category_skills
        
        # Calculate skill frequencies
        skill_frequencies = self._calculate_skill_frequencies(skills, preprocessed_text)
        
        # Return structured skills with frequencies
        result = {
            'skill_categories': skills,
            'all_skills': [skill for category_skills in skills.values() for skill in category_skills],
            'skill_frequencies': skill_frequencies
        }
        
        logger.info(f"Extracted {len(result['all_skills'])} unique skills from text")
        return result
    
    def _preprocess_text(self, text):
        """
        Preprocess text for skill extraction
        
        Args:
            text (str): Text to preprocess
            
        Returns:
            str: Preprocessed text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove punctuation and stop words, then lemmatize
        processed_tokens = []
        for token in tokens:
            # Remove punctuation
            token = token.translate(str.maketrans('', '', string.punctuation))
            
            # Skip empty tokens and stop words
            if token and token not in stop_words:
                # Lemmatize
                token = lemmatizer.lemmatize(token)
                processed_tokens.append(token)
        
        # Reconstruct text
        preprocessed_text = ' '.join(processed_tokens)
        
        return preprocessed_text
    
    def _extract_skills_with_patterns(self, preprocessed_text):
        """
        Extract skills from preprocessed text using pattern matching
        
        Args:
            preprocessed_text (str): Preprocessed text
            
        Returns:
            dict: Dictionary of skill categories and extracted skills
        """
        skills = {}
        
        for category, patterns in self.skill_patterns.items():
            category_skills = []
            
            for pattern in patterns:
                # Handle special regex characters in patterns
                search_pattern = pattern.replace('\\\\', '\\')
                
                # Look for pattern in text
                if re.search(r'\b' + search_pattern + r'\b', preprocessed_text):
                    # Format the skill name properly
                    skill_name = self._format_skill_name(pattern)
                    category_skills.append(skill_name)
            
            if category_skills:
                skills[category] = category_skills
        
        return skills
    
    def _extract_skills_with_spacy(self, text):
        """
        Extract skills from text using spaCy NER and POS tagging
        
        Args:
            text (str): Text to extract skills from
            
        Returns:
            dict: Dictionary of skill categories and extracted skills
        """
        if self.nlp is None:
            logger.warning("SpaCy model not available for skill extraction")
            return {
                "technical_terms": [],
                "tools_and_technologies": []
            }
            
        skills = {
            "technical_terms": [],
            "tools_and_technologies": []
        }
        
        try:
            # Process the text with spaCy
            doc = self.nlp(text)
            
            # Extract named entities that might be skills
            for ent in doc.ents:
                if ent.label_ in ["ORG", "PRODUCT"]:
                    skills["tools_and_technologies"].append(ent.text.lower())
            
            # Extract noun phrases as potential technical terms
            for chunk in doc.noun_chunks:
                # Skip very short phrases
                if len(chunk.text.split()) > 1:
                    skills["technical_terms"].append(chunk.text.lower())
            
            # Filter and clean up extracted skills
            for category in skills:
                # Remove duplicates
                skills[category] = list(set(skills[category]))
                
                # Filter out very common terms that aren't skills
                skills[category] = [
                    s for s in skills[category] 
                    if len(s) > 3 and s not in [
                        "the company", "the job", "the role", "the position", 
                        "the team", "the project", "the work", "the experience"
                    ]
                ]
        except Exception as e:
            logger.error(f"Error in spaCy skill extraction: {str(e)}")
        
        return skills
    
    def _calculate_skill_frequencies(self, skills, preprocessed_text):
        """
        Calculate frequency of each skill in the preprocessed text
        
        Args:
            skills (dict): Dictionary of skill categories and extracted skills
            preprocessed_text (str): Preprocessed text
            
        Returns:
            dict: Dictionary of skills and their frequencies
        """
        skill_frequencies = {}
        
        # Flatten skills list
        all_skills = [skill for category_skills in skills.values() for skill in category_skills]
        
        # Count occurrences of each skill
        for skill in all_skills:
            # Convert skill to search pattern
            search_pattern = skill.lower().replace('+', '\\+')
            
            # Count occurrences
            matches = re.findall(r'\b' + search_pattern + r'\b', preprocessed_text)
            skill_frequencies[skill] = len(matches)
        
        return skill_frequencies
    
    def _format_skill_name(self, skill_pattern):
        """
        Format skill pattern into proper display name
        
        Args:
            skill_pattern (str): Pattern used to match skill
            
        Returns:
            str: Properly formatted skill name
        """
        # Handle special cases
        if skill_pattern == 'python':
            return 'Python'
        elif skill_pattern == 'javascript':
            return 'JavaScript'
        elif skill_pattern == 'typescript':
            return 'TypeScript'
        elif skill_pattern == 'c\\+\\+':
            return 'C++'
        elif skill_pattern == 'c#':
            return 'C#'
        elif skill_pattern == 'node.js':
            return 'Node.js'
        elif skill_pattern == 'asp.net':
            return 'ASP.NET'
        elif skill_pattern == 'ci/cd':
            return 'CI/CD'
        
        # Default case: capitalize words
        return ' '.join(word.capitalize() for word in skill_pattern.split())
    
    def compare_skills(self, resume_skills, job_skills):
        """
        Compare skills extracted from resume and job description
        
        Args:
            resume_skills (dict): Skills extracted from resume
            job_skills (dict): Skills extracted from job description
            
        Returns:
            dict: Comparison results
        """
        logger.info("Comparing skills between resume and job description")
        
        # Get flattened lists of skills
        resume_all_skills = resume_skills.get('all_skills', [])
        job_all_skills = job_skills.get('all_skills', [])
        
        # Find matching and missing skills
        matching_skills = [skill for skill in resume_all_skills if skill in job_all_skills]
        missing_skills = [skill for skill in job_all_skills if skill not in resume_all_skills]
        
        # Calculate match percentage
        if job_all_skills:
            match_percentage = (len(matching_skills) / len(job_all_skills)) * 100
        else:
            match_percentage = 0
        
        # Create comparison result
        comparison = {
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'match_percentage': round(match_percentage, 2),
            'categories': {}
        }
        
        # Compare by category
        resume_categories = resume_skills.get('skill_categories', {})
        job_categories = job_skills.get('skill_categories', {})
        
        all_categories = set(list(resume_categories.keys()) + list(job_categories.keys()))
        
        for category in all_categories:
            resume_category_skills = set(resume_categories.get(category, []))
            job_category_skills = set(job_categories.get(category, []))
            
            category_matching = list(resume_category_skills.intersection(job_category_skills))
            category_missing = list(job_category_skills - resume_category_skills)
            
            if job_category_skills:
                category_match_percentage = (len(category_matching) / len(job_category_skills)) * 100
            else:
                category_match_percentage = 0
            
            comparison['categories'][category] = {
                'matching': category_matching,
                'missing': category_missing,
                'match_percentage': round(category_match_percentage, 2)
            }
        
        logger.info(f"Skill comparison complete: {comparison['match_percentage']}% match")
        return comparison
        
    def extract_and_compare(self, resume_text, job_description):
        """
        Extract skills from resume and job description and compare them
        
        Args:
            resume_text (str): Resume text
            job_description (str): Job description text
            
        Returns:
            dict: Comparison results
        """
        # Extract skills from resume
        resume_skills = self.extract_skills(resume_text)
        
        # Extract skills from job description
        job_skills = self.extract_skills(job_description)
        
        # Compare skills
        comparison = self.compare_skills(resume_skills, job_skills)
        
        # Create combined result
        result = {
            'resume_skills': resume_skills,
            'job_skills': job_skills,
            'comparison': comparison
        }
        
        return result