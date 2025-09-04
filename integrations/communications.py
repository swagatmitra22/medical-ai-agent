"""
Communications Integration - Medical Appointment Scheduling System
==============================================================

This module handles all email and SMS communications for the appointment
scheduling system including confirmations, reminders, and form distribution.

Key Responsibilities:
- Send appointment confirmation emails with attachments
- Send SMS reminders and notifications using Twilio
- Handle 3-tier reminder system (24hr, 4hr, 1hr before appointment)
- Email patient intake forms for new patients
- Template-based messaging with personalization
- Comprehensive error handling and logging

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import Twilio (optional dependency)
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio not available. SMS functionality will be disabled.")

# ============================================================================
# COMMUNICATION MANAGER CLASS
# ============================================================================

class CommunicationManager:
    """
    Comprehensive communication manager for email and SMS messaging.
    """
    
    def __init__(self):
        """Initialize communication manager with SMTP and Twilio settings."""
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_email = os.getenv('SMTP_EMAIL')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        # Twilio configuration
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        # Initialize Twilio client if available
        self.twilio_client = None
        if TWILIO_AVAILABLE and self.twilio_sid and self.twilio_token:
            try:
                self.twilio_client = Client(self.twilio_sid, self.twilio_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {str(e)}")
        
        # Clinic information
        self.clinic_name = "MediCare Allergy & Wellness Center"
        self.clinic_address = "456 Healthcare Boulevard, Suite 300"
        self.clinic_phone = "(555) 123-4567"
        self.clinic_email = self.smtp_email
    
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   body: str, 
                   html_body: Optional[str] = None,
                   attachments: Optional[List[str]] = None,
                   cc_emails: Optional[List[str]] = None) -> bool:
        """
        Send email with optional HTML content and attachments.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            body: Plain text email body
            html_body: Optional HTML email body
            attachments: Optional list of file paths to attach
            cc_emails: Optional list of CC email addresses
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self.smtp_email or not self.smtp_password:
                logger.error("SMTP credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.clinic_name} <{self.smtp_email}>"
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
                    else:
                        logger.warning(f"Attachment file not found: {file_path}")
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_email, self.smtp_password)
                
                all_recipients = to_emails + (cc_emails or [])
                server.sendmail(self.smtp_email, all_recipients, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """
        Send SMS message using Twilio.
        
        Args:
            to_number: Recipient phone number (E.164 format)
            message: SMS message text (max 160 characters recommended)
            
        Returns:
            True if SMS sent successfully, False otherwise
        """
        try:
            if not self.twilio_client:
                logger.error("Twilio client not initialized")
                return False
            
            # Ensure message is within SMS limits
            if len(message) > 1600:  # Twilio's limit for long messages
                message = message[:1597] + "..."
                logger.warning("Message truncated to fit SMS limits")
            
            # Send SMS
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully to {to_number}, SID: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
            return False

# ============================================================================
# EMAIL TEMPLATES
# ============================================================================

def create_appointment_confirmation_email(appointment_details: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Create appointment confirmation email content.
    
    Args:
        appointment_details: Dictionary containing appointment information
        
    Returns:
        Tuple of (subject, text_body, html_body)
    """
    patient_name = appointment_details.get('patient_name', 'Patient')
    appointment_date = appointment_details.get('appointment_date', '')
    appointment_time = appointment_details.get('appointment_time', '')
    doctor_name = appointment_details.get('doctor_name', '')
    confirmation_id = appointment_details.get('confirmation_id', '')
    
    subject = f"Appointment Confirmation - {appointment_date} at {appointment_time}"
    
    text_body = f"""
Dear {patient_name},

Your appointment has been confirmed!

APPOINTMENT DETAILS:
Date: {appointment_date}
Time: {appointment_time}
Doctor: {doctor_name}
Confirmation ID: {confirmation_id}

LOCATION:
MediCare Allergy & Wellness Center
456 Healthcare Boulevard, Suite 300
Phone: (555) 123-4567

IMPORTANT REMINDERS:
• Please arrive 15 minutes early
• Bring your insurance card and photo ID
• Complete any attached forms before your visit
• For cancellations, please call 24 hours in advance

We look forward to seeing you!

Best regards,
MediCare Appointment Team
    """.strip()
    
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; }}
            .appointment-box {{ background-color: #f9f9f9; border: 1px solid #ddd; padding: 15px; margin: 15px 0; }}
            .clinic-info {{ background-color: #e8f5e8; padding: 15px; border-left: 4px solid #4CAF50; }}
            .footer {{ text-align: center; color: #666; padding: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏥 Appointment Confirmed!</h1>
        </div>
        
        <div class="content">
            <p>Dear <strong>{patient_name}</strong>,</p>
            
            <p>Your appointment has been successfully scheduled. Here are your appointment details:</p>
            
            <div class="appointment-box">
                <h3>📅 Appointment Details</h3>
                <p><strong>Date:</strong> {appointment_date}</p>
                <p><strong>Time:</strong> {appointment_time}</p>
                <p><strong>Doctor:</strong> {doctor_name}</p>
                <p><strong>Confirmation ID:</strong> {confirmation_id}</p>
            </div>
            
            <div class="clinic-info">
                <h3>🏥 Clinic Location</h3>
                <p><strong>MediCare Allergy & Wellness Center</strong><br>
                456 Healthcare Boulevard, Suite 300<br>
                Phone: (555) 123-4567</p>
            </div>
            
            <h3>📋 Important Reminders</h3>
            <ul>
                <li>Please arrive <strong>15 minutes early</strong></li>
                <li>Bring your <strong>insurance card and photo ID</strong></li>
                <li>Complete any attached forms before your visit</li>
                <li>For cancellations, please call <strong>24 hours in advance</strong></li>
            </ul>
            
            <p>We look forward to providing you with excellent care!</p>
        </div>
        
        <div class="footer">
            <p>Best regards,<br>
            <strong>MediCare Appointment Team</strong></p>
        </div>
    </body>
    </html>
    """.strip()
    
    return subject, text_body, html_body

def create_reminder_sms(appointment_details: Dict[str, Any], reminder_type: str) -> str:
    """
    Create SMS reminder message based on reminder type.
    
    Args:
        appointment_details: Appointment information
        reminder_type: '24_hour', '4_hour', or '1_hour'
        
    Returns:
        SMS message text
    """
    patient_name = appointment_details.get('patient_name', 'Patient')
    appointment_date = appointment_details.get('appointment_date', '')
    appointment_time = appointment_details.get('appointment_time', '')
    doctor_name = appointment_details.get('doctor_name', '')
    
    messages = {
        '24_hour': f"Hi {patient_name}, this is a reminder that you have an appointment tomorrow ({appointment_date}) at {appointment_time} with {doctor_name}. Please arrive 15 minutes early. MediCare Wellness - (555) 123-4567",
        
        '4_hour': f"Hi {patient_name}, your appointment with {doctor_name} is in 4 hours at {appointment_time}. Have you completed your intake forms? Please reply YES to confirm your attendance or call us at (555) 123-4567. MediCare Wellness",
        
        '1_hour': f"Final reminder: {patient_name}, your appointment is in 1 hour at {appointment_time} with {doctor_name}. Please confirm by replying YES or call (555) 123-4567 if you need to reschedule. See you soon! MediCare Wellness"
    }
    
    return messages.get(reminder_type, messages['24_hour'])

# ============================================================================
# MAIN COMMUNICATION FUNCTIONS FOR LANGGRAPH INTEGRATION
# ============================================================================

def send_appointment_notifications(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send appointment confirmation email and setup SMS reminders.
    
    Args:
        state: Current appointment state with confirmation details
        
    Returns:
        Updated state with communication status
    """
    logger.info("Sending appointment notifications")
    
    try:
        confirmation_details = state.get('confirmation_details', {})
        
        if not confirmation_details:
            return {
                **state,
                "error_message": "No confirmation details available for notifications",
                "notification_status": "failed"
            }
        
        comm_manager = CommunicationManager()
        notification_results = {}
        
        # Send confirmation email
        patient_email = confirmation_details.get('patient_email')
        if patient_email:
            subject, text_body, html_body = create_appointment_confirmation_email(confirmation_details)
            
            # Prepare attachments for new patients
            attachments = []
            if confirmation_details.get('requires_forms'):
                # Add intake form attachments
                form_files = [
                    "templates/intake_forms/new_patient_intake_form.html",
                    "templates/intake_forms/medical_history_form.html"
                ]
                # Only add files that exist
                attachments = [f for f in form_files if os.path.exists(f)]
            
            email_sent = comm_manager.send_email(
                to_emails=[patient_email],
                subject=subject,
                body=text_body,
                html_body=html_body,
                attachments=attachments
            )
            
            notification_results['email_sent'] = email_sent
            
            if email_sent:
                logger.info(f"Confirmation email sent to {patient_email}")
            else:
                logger.error(f"Failed to send confirmation email to {patient_email}")
        
        # Setup SMS reminders if phone number available
        patient_phone = confirmation_details.get('patient_phone')
        if patient_phone and comm_manager.twilio_client:
            reminder_schedule = confirmation_details.get('reminder_schedule', [])
            notification_results['sms_reminders_scheduled'] = len(reminder_schedule)
            
            # In a production system, you would schedule these reminders
            # For demo purposes, we'll just log the scheduled reminders
            for reminder in reminder_schedule:
                logger.info(f"SMS reminder scheduled: {reminder['reminder_type']} at {reminder['send_time']}")
        
        # Update state with notification results
        updated_state = {
            **state,
            "notification_results": notification_results,
            "notification_status": "success" if notification_results.get('email_sent') else "partial"
        }
        
        return updated_state
        
    except Exception as e:
        logger.error(f"Error sending appointment notifications: {str(e)}")
        return {
            **state,
            "error_message": f"Notification error: {str(e)}",
            "notification_status": "failed"
        }

def setup_reminder_system(appointment_details: Dict[str, Any]) -> Dict[str, Any]:
    """
    Setup the 3-tier reminder system for an appointment.
    
    Args:
        appointment_details: Complete appointment information
        
    Returns:
        Dictionary with reminder setup results
    """
    try:
        reminder_schedule = appointment_details.get('reminder_schedule', [])
        setup_results = {
            'reminders_scheduled': len(reminder_schedule),
            'reminder_details': []
        }
        
        for reminder in reminder_schedule:
            reminder_info = {
                'type': reminder['reminder_type'],
                'scheduled_time': reminder['send_time'],
                'method': reminder['method'],
                'includes_form_check': reminder.get('includes_form_check', False)
            }
            setup_results['reminder_details'].append(reminder_info)
            
            logger.info(f"Reminder scheduled: {reminder_info}")
        
        return setup_results
        
    except Exception as e:
        logger.error(f"Error setting up reminder system: {str(e)}")
        return {'error': str(e), 'reminders_scheduled': 0}

# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def send_email_confirmation(patient_email: str, appointment_details: Dict[str, Any]) -> bool:
    """
    Convenience function to send appointment confirmation email.
    
    Args:
        patient_email: Recipient email address
        appointment_details: Appointment information
        
    Returns:
        True if email sent successfully, False otherwise
    """
    comm_manager = CommunicationManager()
    subject, text_body, html_body = create_appointment_confirmation_email(appointment_details)
    
    return comm_manager.send_email(
        to_emails=[patient_email],
        subject=subject,
        body=text_body,
        html_body=html_body
    )

def send_sms_reminder(patient_phone: str, appointment_details: Dict[str, Any], reminder_type: str) -> bool:
    """
    Convenience function to send SMS reminder.
    
    Args:
        patient_phone: Recipient phone number
        appointment_details: Appointment information
        reminder_type: Type of reminder ('24_hour', '4_hour', '1_hour')
        
    Returns:
        True if SMS sent successfully, False otherwise
    """
    comm_manager = CommunicationManager()
    message = create_reminder_sms(appointment_details, reminder_type)
    
    return comm_manager.send_sms(patient_phone, message)

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_communication_system():
    """Test function to validate communication system functionality."""
    
    print("Testing Communication System")
    print("=" * 50)
    
    # Test email functionality
    print("\n1. Testing Email Configuration:")
    comm_manager = CommunicationManager()
    
    if comm_manager.smtp_email and comm_manager.smtp_password:
        print("✅ SMTP credentials configured")
    else:
        print("❌ SMTP credentials missing")
    
    # Test Twilio functionality
    print("\n2. Testing Twilio Configuration:")
    if comm_manager.twilio_client:
        print("✅ Twilio client initialized")
    else:
        print("❌ Twilio client not available")
    
    # Test template generation
    print("\n3. Testing Email Templates:")
    test_appointment = {
        'patient_name': 'John Test Patient',
        'appointment_date': '09/10/2025',
        'appointment_time': '10:00 AM',
        'doctor_name': 'Dr. Johnson',
        'confirmation_id': 'TEST-123456'
    }
    
    subject, text_body, html_body = create_appointment_confirmation_email(test_appointment)
    
    if subject and text_body and html_body:
        print("✅ Email templates generated successfully")
        print(f"   Subject: {subject}")
    else:
        print("❌ Email template generation failed")
    
    # Test SMS template
    print("\n4. Testing SMS Templates:")
    sms_message = create_reminder_sms(test_appointment, '24_hour')
    
    if sms_message and len(sms_message) <= 160:
        print("✅ SMS template generated successfully")
        print(f"   Message length: {len(sms_message)} characters")
    else:
        print("❌ SMS template generation failed or too long")
    
    print("\n" + "=" * 50)
    print("Communication system test completed!")

if __name__ == "__main__":
    # Run tests when executed directly
    test_communication_system()
