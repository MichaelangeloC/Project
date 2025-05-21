import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from app.utils.logger import setup_logger
from app.utils.config import load_config

logger = setup_logger()
config = load_config()

class EmailNotifier:
    """Class to send email notifications"""
    
    def __init__(self):
        """Initialize the email notifier"""
        self.smtp_host = config.get('SMTP_HOST', '')
        self.smtp_port = int(config.get('SMTP_PORT', 587))
        self.smtp_user = config.get('SMTP_USER', '')
        self.smtp_password = config.get('SMTP_PASSWORD', '')
        self.sender_email = config.get('SMTP_USER', 'noreply@jobapplication.app')
        self.receiver_email = config.get('NOTIFICATION_EMAIL_RECEIVER', '')
        
        # Load email template
        template_path = os.path.join("templates", "email_notification.html")
        try:
            if os.path.exists(template_path):
                with open(template_path, 'r') as file:
                    self.template = file.read()
            else:
                # Default template if file doesn't exist
                self.template = """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Job Application Notification</title>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background-color: #4285f4; color: white; padding: 15px; text-align: center; }
                        .content { padding: 20px; background-color: #f9f9f9; }
                        .job-details { margin-top: 20px; padding: 15px; background-color: #fff; border-left: 4px solid #4285f4; }
                        .footer { margin-top: 20px; font-size: 12px; color: #777; text-align: center; }
                        .button { display: inline-block; background-color: #4285f4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Job Application Notification</h1>
                    </div>
                    <div class="content">
                        <p>Hello,</p>
                        <p>{{message}}</p>
                        
                        <div class="job-details">
                            <h3>Job Details:</h3>
                            <p><strong>Title:</strong> {{job_title}}</p>
                            <p><strong>Company:</strong> {{company_name}}</p>
                            <p><strong>Location:</strong> {{job_location}}</p>
                            <p><strong>Source:</strong> {{job_source}}</p>
                            <p><strong>Date Found:</strong> {{date_found}}</p>
                            <p><strong>URL:</strong> <a href="{{job_url}}">View Job Posting</a></p>
                        </div>
                        
                        {% if error %}
                        <div style="margin-top: 20px; padding: 15px; background-color: #ffebee; border-left: 4px solid #f44336;">
                            <h3>Error Details:</h3>
                            <p>{{error}}</p>
                        </div>
                        {% endif %}
                        
                        <p>Please take appropriate action at your earliest convenience.</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message from your Job Application Automator.</p>
                        <p>Sent on {{timestamp}}</p>
                    </div>
                </body>
                </html>
                """
        except Exception as e:
            logger.error(f"Error loading email template: {str(e)}", exc_info=True)
            # Default template if there's an error
            self.template = "Job Application Notification\n\n{{message}}\n\nJob Details:\nTitle: {{job_title}}\nCompany: {{company_name}}\nLocation: {{job_location}}\nURL: {{job_url}}\n\n{{error}}"
    
    def send_notification(self, subject, job_details, error=None, attachments=None):
        """
        Send email notification
        
        Args:
            subject (str): Email subject
            job_details (dict): Job details
            error (str, optional): Error message
            attachments (list, optional): List of file paths to attach
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not self.smtp_host or not self.receiver_email:
            logger.warning("SMTP configuration missing. Email notification skipped.")
            return False
        
        logger.info(f"Sending email notification: {subject}")
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email
            msg['Subject'] = subject
            
            # Prepare email content
            message = "Manual intervention is required for the following job application."
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Fill template
            html_content = self.template
            html_content = html_content.replace('{{message}}', message)
            html_content = html_content.replace('{{job_title}}', job_details.get('title', 'Unknown Title'))
            html_content = html_content.replace('{{company_name}}', job_details.get('company', 'Unknown Company'))
            html_content = html_content.replace('{{job_location}}', job_details.get('location', 'Unknown Location'))
            html_content = html_content.replace('{{job_source}}', job_details.get('source', 'Unknown Source'))
            html_content = html_content.replace('{{date_found}}', job_details.get('date_found', 'Unknown Date'))
            html_content = html_content.replace('{{job_url}}', job_details.get('url', '#'))
            html_content = html_content.replace('{{timestamp}}', timestamp)
            
            if error:
                html_content = html_content.replace('{{error}}', error)
                html_content = html_content.replace('{% if error %}', '')
                html_content = html_content.replace('{% endif %}', '')
            else:
                # Remove error section if no error
                if '{% if error %}' in html_content and '{% endif %}' in html_content:
                    start_idx = html_content.find('{% if error %}')
                    end_idx = html_content.find('{% endif %}') + len('{% endif %}')
                    html_content = html_content[:start_idx] + html_content[end_idx:]
            
            # Attach HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Attach files if provided
            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, 'rb') as f:
                            attachment = MIMEApplication(f.read())
                            attachment.add_header(
                                'Content-Disposition', 
                                'attachment', 
                                filename=os.path.basename(attachment_path)
                            )
                            msg.attach(attachment)
                    else:
                        logger.warning(f"Attachment not found: {attachment_path}")
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent successfully to: {self.receiver_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}", exc_info=True)
            return False
