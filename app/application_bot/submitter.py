import os
import time
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from app.utils.logger import setup_logger
from app.utils.config import load_config

logger = setup_logger()
config = load_config()

class ApplicationSubmitter:
    """Class to automate job application submissions"""
    
    def __init__(self):
        """Initialize the application submitter"""
        self.timeout = 30  # Seconds to wait for elements to appear
        self.active_domains = self._load_supported_domains()
        
    def _load_supported_domains(self):
        """
        Load supported job board domains and their selectors
        
        Returns:
            dict: Mapping of domains to selector configurations
        """
        # In a real implementation, this would be loaded from a database or config file
        # For now, we'll hardcode a few common job boards
        return {
            'indeed.com': {
                'name': 'Indeed',
                'apply_button': ['a.jcs-JobTitle', 'button[id*="apply-button"]', 'a[id*="apply-button"]'],
                'form_indicators': ['input[id*="input-applicant"]', 'form[id*="application-form"]'],
                'resume_upload': ['input[type="file"][id*="resume-upload"]'],
                'email_field': ['input[type="email"]', 'input[id*="email"]'],
                'success_indicators': ['div[class*="applied-success"]', 'h1[class*="success"]']
            },
            'linkedin.com': {
                'name': 'LinkedIn',
                'apply_button': ['button.jobs-apply-button', 'a[data-control-name="jobdetails_topcard_inapply"]'],
                'form_indicators': ['div.jobs-easy-apply-content', 'form.jobs-apply-form'],
                'resume_upload': ['input[name="resume"]', 'input[type="file"][id*="upload"]'],
                'email_field': ['input[id*="email"]'],
                'success_indicators': ['h2.artdeco-banner__title--success', 'div.jobs-post-apply-success']
            },
            'glassdoor.com': {
                'name': 'Glassdoor',
                'apply_button': ['a[data-test="applyButton"]', 'button[data-test="applyButton"]'],
                'form_indicators': ['div[data-test="application-form"]'],
                'resume_upload': ['input[type="file"][id*="resume"]'],
                'email_field': ['input[id*="email"]'],
                'success_indicators': ['div[data-test="success-message"]']
            }
        }
    
    def submit_application(self, job_url, resume_path, cover_letter_path):
        """
        Attempt to submit a job application
        
        Args:
            job_url (str): URL of the job posting
            resume_path (str): Path to the resume file
            cover_letter_path (str): Path to the cover letter file
            
        Returns:
            dict: Result of the submission attempt
        """
        logger.info(f"Attempting to submit application for: {job_url}")
        
        # Validate inputs
        if not os.path.exists(resume_path):
            error_msg = f"Resume file not found: {resume_path}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        if not os.path.exists(cover_letter_path):
            error_msg = f"Cover letter file not found: {cover_letter_path}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        # Check if domain is supported
        domain = self._extract_domain(job_url)
        if domain not in self.active_domains:
            error_msg = f"Domain not supported for automation: {domain}"
            logger.warning(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'requires_manual': True,
                'resume_path': resume_path,
                'cover_letter_path': cover_letter_path
            }
        
        # Set up Selenium WebDriver
        driver = None
        try:
            # Set up Chrome options for headless operation
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Create the driver
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.timeout)
            
            # Navigate to job posting
            logger.info(f"Opening job URL: {job_url}")
            driver.get(job_url)
            
            # Wait for page to load
            WebDriverWait(driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get domain config
            domain_config = self.active_domains[domain]
            
            # Click apply button
            apply_button_found = False
            for selector in domain_config['apply_button']:
                try:
                    apply_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    apply_button.click()
                    apply_button_found = True
                    logger.info(f"Clicked apply button using selector: {selector}")
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not apply_button_found:
                logger.warning("Apply button not found")
                return {
                    'success': False,
                    'error': 'Apply button not found - likely not an active job post or requires login',
                    'requires_manual': True,
                    'resume_path': resume_path,
                    'cover_letter_path': cover_letter_path
                }
            
            # Wait for application form to appear
            form_found = False
            for selector in domain_config['form_indicators']:
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    form_found = True
                    logger.info(f"Application form found using selector: {selector}")
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not form_found:
                logger.warning("Application form not found")
                return {
                    'success': False,
                    'error': 'Application form not found - likely redirects to external ATS',
                    'requires_manual': True,
                    'resume_path': resume_path,
                    'cover_letter_path': cover_letter_path
                }
            
            # Try to upload resume
            resume_uploaded = False
            for selector in domain_config['resume_upload']:
                try:
                    resume_upload = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    resume_upload.send_keys(os.path.abspath(resume_path))
                    resume_uploaded = True
                    logger.info(f"Resume uploaded using selector: {selector}")
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
                except Exception as e:
                    logger.error(f"Error uploading resume: {str(e)}")
            
            # Try to fill email if available
            email_field_found = False
            for selector in domain_config['email_field']:
                try:
                    email_field = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    email_field.clear()
                    email_field.send_keys(config.get('NOTIFICATION_EMAIL_RECEIVER', 'test@example.com'))
                    email_field_found = True
                    logger.info(f"Email field filled using selector: {selector}")
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
                except Exception as e:
                    logger.error(f"Error filling email field: {str(e)}")
            
            # Take screenshot for logging
            screenshot_dir = os.path.join("logs", "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            screenshot_path = os.path.join(screenshot_dir, f"application_{int(time.time())}.png")
            driver.save_screenshot(screenshot_path)
            
            # At this point, we would normally continue filling out the form
            # and submit it, but since forms vary widely and we can't automate
            # all of them reliably, we'll return a manual intervention request
            
            logger.info("Application requires manual intervention to complete")
            return {
                'success': False,
                'error': 'Application requires manual intervention to complete',
                'requires_manual': True,
                'resume_uploaded': resume_uploaded,
                'email_field_found': email_field_found,
                'screenshot_path': screenshot_path,
                'resume_path': resume_path,
                'cover_letter_path': cover_letter_path,
                'notes': 'Initial form fields were filled automatically. Please complete and submit the application manually.'
            }
            
        except Exception as e:
            error_msg = f"Error submitting application: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Take error screenshot if driver is available
            if driver:
                screenshot_dir = os.path.join("logs", "screenshots")
                os.makedirs(screenshot_dir, exist_ok=True)
                error_screenshot = os.path.join(screenshot_dir, f"error_{int(time.time())}.png")
                try:
                    driver.save_screenshot(error_screenshot)
                    logger.info(f"Error screenshot saved to: {error_screenshot}")
                except:
                    pass
            
            return {
                'success': False,
                'error': error_msg,
                'requires_manual': True,
                'resume_path': resume_path,
                'cover_letter_path': cover_letter_path
            }
            
        finally:
            # Clean up WebDriver
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _extract_domain(self, url):
        """
        Extract domain from URL
        
        Args:
            url (str): URL to extract domain from
            
        Returns:
            str: Domain name
        """
        try:
            # Remove protocol
            if '://' in url:
                url = url.split('://', 1)[1]
            
            # Remove path
            if '/' in url:
                url = url.split('/', 1)[0]
            
            # Remove port and any remaining parts
            if ':' in url:
                url = url.split(':', 1)[0]
            
            # Remove subdomains except for www
            parts = url.split('.')
            if len(parts) > 2:
                if parts[0] == 'www':
                    domain = '.'.join(parts[1:])
                else:
                    # Try to get the main domain (usually last two parts)
                    domain = '.'.join(parts[-2:])
            else:
                domain = url
            
            # Check if domain is in supported domains
            for supported_domain in self.active_domains.keys():
                if supported_domain in domain:
                    return supported_domain
            
            return domain
            
        except Exception as e:
            logger.error(f"Error extracting domain from URL: {str(e)}", exc_info=True)
            return url  # Return original URL in case of error
