"""
Email Templates - Medical Appointment Scheduling System
====================================================

This module provides comprehensive email templates for appointment confirmations,
reminders, form distribution, and other communication needs. All templates are
professionally designed for medical practice use with responsive HTML styling.

Key Features:
- Professional medical-grade email templates
- HTML and plain text versions for all templates
- Responsive design for mobile and desktop
- Template variables for personalization
- Integration with LangGraph workflow system
- HIPAA-compliant communication standards

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import logging
from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from string import Template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# EMAIL TEMPLATE CONSTANTS
# ============================================================================

# Base CSS styling for all email templates
EMAIL_CSS = """
<style>
    body {
        font-family: Arial, sans-serif;
        line-height: 1.6;
        color: #333333;
        background-color: #f9f9f9;
        margin: 0;
        padding: 0;
    }
    .email-container {
        max-width: 600px;
        margin: 20px auto;
        background-color: #ffffff;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .header {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 30px 20px;
        text-align: center;
    }
    .header h1 {
        margin: 0;
        font-size: 28px;
        font-weight: bold;
    }
    .content {
        padding: 30px;
    }
    .appointment-details {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    }
    .appointment-details h3 {
        color: #4CAF50;
        margin-top: 0;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 10px;
    }
    .detail-row {
        display: flex;
        justify-content: space-between;
        margin: 10px 0;
        padding: 8px 0;
        border-bottom: 1px solid #eee;
    }
    .detail-label {
        font-weight: bold;
        color: #555;
    }
    .detail-value {
        color: #333;
    }
    .clinic-info {
        background-color: #e8f5e8;
        border-left: 4px solid #4CAF50;
        padding: 15px;
        margin: 20px 0;
    }
    .important-note {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 4px;
        padding: 15px;
        margin: 20px 0;
    }
    .footer {
        background-color: #f8f9fa;
        color: #6c757d;
        text-align: center;
        padding: 20px;
        font-size: 14px;
    }
    .button {
        display: inline-block;
        background-color: #4CAF50;
        color: white;
        padding: 12px 30px;
        text-decoration: none;
        border-radius: 5px;
        margin: 10px 0;
        font-weight: bold;
    }
    .button:hover {
        background-color: #45a049;
    }
    @media (max-width: 600px) {
        .email-container {
            margin: 10px;
        }
        .content {
            padding: 20px;
        }
        .detail-row {
            flex-direction: column;
        }
    }
</style>
"""

# ============================================================================
# APPOINTMENT CONFIRMATION TEMPLATES
# ============================================================================

CONFIRMATION_EMAIL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Appointment Confirmation</title>
    {css}
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🏥 Appointment Confirmed!</h1>
        </div>
        
        <div class="content">
            <p>Dear <strong>{patient_name}</strong>,</p>
            
            <p>Thank you for scheduling your appointment with {clinic_name}. We are pleased to confirm your upcoming visit.</p>
            
            <div class="appointment-details">
                <h3>📅 Appointment Details</h3>
                <div class="detail-row">
                    <span class="detail-label">Date:</span>
                    <span class="detail-value">{appointment_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Time:</span>
                    <span class="detail-value">{appointment_time}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Duration:</span>
                    <span class="detail-value">{appointment_duration} minutes</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Provider:</span>
                    <span class="detail-value">{doctor_name}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Specialty:</span>
                    <span class="detail-value">{doctor_specialty}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Confirmation ID:</span>
                    <span class="detail-value"><strong>{confirmation_id}</strong></span>
                </div>
            </div>
            
            <div class="clinic-info">
                <h3>🏥 Clinic Location</h3>
                <p><strong>{clinic_name}</strong><br>
                {clinic_address}<br>
                Phone: {clinic_phone}<br>
                Website: {clinic_website}</p>
            </div>
            
            <div class="important-note">
                <h3>📋 Important Reminders</h3>
                <ul>
                    <li><strong>Arrive 15 minutes early</strong> for check-in</li>
                    <li>Bring your <strong>insurance card and photo ID</strong></li>
                    <li>Complete any attached forms before your visit</li>
                    <li>For cancellations, please call <strong>24 hours in advance</strong></li>
                    {new_patient_instructions}
                </ul>
            </div>
            
            <p>We look forward to providing you with excellent healthcare service. If you have any questions or need to make changes to your appointment, please don't hesitate to contact us.</p>
            
            <p>Thank you for choosing {clinic_name}!</p>
        </div>
        
        <div class="footer">
            <p><strong>{clinic_name}</strong><br>
            {clinic_address}<br>
            Phone: {clinic_phone} | Email: {clinic_email}</p>
            <p><em>This email was sent from an automated system. Please do not reply directly to this email.</em></p>
        </div>
    </div>
</body>
</html>
""".replace("{css}", EMAIL_CSS)

CONFIRMATION_EMAIL_TEXT = """
🏥 APPOINTMENT CONFIRMED - {clinic_name}

Dear {patient_name},

Thank you for scheduling your appointment with {clinic_name}. We are pleased to confirm your upcoming visit.

📅 APPOINTMENT DETAILS:
Date: {appointment_date}
Time: {appointment_time}
Duration: {appointment_duration} minutes
Provider: {doctor_name}
Specialty: {doctor_specialty}
Confirmation ID: {confirmation_id}

🏥 CLINIC LOCATION:
{clinic_name}
{clinic_address}
Phone: {clinic_phone}
Website: {clinic_website}

📋 IMPORTANT REMINDERS:
• Arrive 15 minutes early for check-in
• Bring your insurance card and photo ID
• Complete any attached forms before your visit
• For cancellations, please call 24 hours in advance
{new_patient_instructions_text}

We look forward to providing you with excellent healthcare service. If you have any questions or need to make changes to your appointment, please contact us at {clinic_phone}.

Thank you for choosing {clinic_name}!

Best regards,
The {clinic_name} Team

---
{clinic_name}
{clinic_address}
Phone: {clinic_phone}
Email: {clinic_email}

This email was sent from an automated system.
"""

# ============================================================================
# REMINDER EMAIL TEMPLATES
# ============================================================================

REMINDER_EMAIL_HTML_24HR = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Appointment Reminder - 24 Hours</title>
    {css}
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>⏰ Appointment Reminder</h1>
        </div>
        
        <div class="content">
            <p>Dear <strong>{patient_name}</strong>,</p>
            
            <p>This is a friendly reminder that you have an appointment scheduled with {clinic_name} <strong>tomorrow</strong>.</p>
            
            <div class="appointment-details">
                <h3>📅 Tomorrow's Appointment</h3>
                <div class="detail-row">
                    <span class="detail-label">Date:</span>
                    <span class="detail-value">{appointment_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Time:</span>
                    <span class="detail-value">{appointment_time}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Provider:</span>
                    <span class="detail-value">{doctor_name}</span>
                </div>
            </div>
            
            <div class="important-note">
                <h3>📋 Please Remember</h3>
                <ul>
                    <li>Arrive <strong>15 minutes early</strong></li>
                    <li>Bring your <strong>insurance card and ID</strong></li>
                    <li>Complete any required forms in advance</li>
                </ul>
            </div>
            
            <p>If you need to cancel or reschedule, please call us at <strong>{clinic_phone}</strong> as soon as possible.</p>
            
            <p>We look forward to seeing you tomorrow!</p>
        </div>
        
        <div class="footer">
            <p><strong>{clinic_name}</strong><br>
            Phone: {clinic_phone}</p>
        </div>
    </div>
</body>
</html>
""".replace("{css}", EMAIL_CSS)

REMINDER_EMAIL_HTML_4HR = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Appointment Reminder - 4 Hours</title>
    {css}
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🕐 Your Appointment is in 4 Hours</h1>
        </div>
        
        <div class="content">
            <p>Dear <strong>{patient_name}</strong>,</p>
            
            <p>Your appointment with <strong>{doctor_name}</strong> is scheduled for <strong>today at {appointment_time}</strong>.</p>
            
            <div class="appointment-details">
                <h3>📅 Today's Appointment</h3>
                <div class="detail-row">
                    <span class="detail-label">Time:</span>
                    <span class="detail-value">{appointment_time}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Provider:</span>
                    <span class="detail-value">{doctor_name}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Location:</span>
                    <span class="detail-value">{clinic_address}</span>
                </div>
            </div>
            
            <div class="important-note">
                <h3>❓ Quick Confirmation Needed</h3>
                <p>Please confirm your attendance by <strong>replying to this email with "CONFIRMED"</strong> or call us at {clinic_phone}.</p>
                <p><strong>Have you completed your intake forms?</strong> If not, please complete them as soon as possible.</p>
            </div>
            
            <p>If you cannot attend, please call immediately at <strong>{clinic_phone}</strong> to avoid a cancellation fee.</p>
        </div>
        
        <div class="footer">
            <p><strong>{clinic_name}</strong><br>
            Phone: {clinic_phone}</p>
        </div>
    </div>
</body>
</html>
""".replace("{css}", EMAIL_CSS)

REMINDER_EMAIL_HTML_1HR = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Final Appointment Reminder - 1 Hour</title>
    {css}
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🚨 Final Reminder - 1 Hour</h1>
        </div>
        
        <div class="content">
            <p>Dear <strong>{patient_name}</strong>,</p>
            
            <p><strong>FINAL REMINDER:</strong> Your appointment is in <strong>1 hour</strong> at <strong>{appointment_time}</strong> with {doctor_name}.</p>
            
            <div class="appointment-details">
                <h3>📅 Your Appointment NOW</h3>
                <div class="detail-row">
                    <span class="detail-label">Time:</span>
                    <span class="detail-value">{appointment_time}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Provider:</span>
                    <span class="detail-value">{doctor_name}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Address:</span>
                    <span class="detail-value">{clinic_address}</span>
                </div>
            </div>
            
            <div class="important-note">
                <h3>🏃‍♂️ Action Required</h3>
                <p><strong>Please confirm by replying "YES" or calling {clinic_phone} immediately.</strong></p>
                <p>If you cannot attend, please call NOW to avoid charges.</p>
            </div>
            
            <p>We're looking forward to seeing you in 1 hour!</p>
        </div>
        
        <div class="footer">
            <p><strong>{clinic_name}</strong><br>
            Emergency Contact: {clinic_phone}</p>
        </div>
    </div>
</body>
</html>
""".replace("{css}", EMAIL_CSS)

# ============================================================================
# FORM DISTRIBUTION TEMPLATES
# ============================================================================

FORM_DISTRIBUTION_EMAIL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Patient Intake Forms</title>
    {css}
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>📋 Patient Intake Forms</h1>
        </div>
        
        <div class="content">
            <p>Dear <strong>{patient_name}</strong>,</p>
            
            <p>As a new patient at {clinic_name}, please complete the attached intake forms before your appointment on <strong>{appointment_date} at {appointment_time}</strong>.</p>
            
            <div class="important-note">
                <h3>📋 Required Forms</h3>
                <ul>
                    <li><strong>New Patient Intake Form</strong> - Personal and contact information</li>
                    <li><strong>Medical History Form</strong> - Past medical conditions and treatments</li>
                    <li><strong>Insurance Information Form</strong> - Insurance details and coverage</li>
                    <li><strong>Allergy & Wellness Form</strong> - Specific allergy and wellness information</li>
                </ul>
            </div>
            
            <div class="clinic-info">
                <h3>⏱️ Important Instructions</h3>
                <p><strong>Complete forms at least 24 hours before your appointment.</strong></p>
                <p>You can:</p>
                <ul>
                    <li>Fill out the attached forms and bring them to your appointment</li>
                    <li>Complete forms online at our patient portal: {patient_portal_url}</li>
                    <li>Arrive 30 minutes early to complete forms at our office</li>
                </ul>
            </div>
            
            <div class="appointment-details">
                <h3>📅 Your Upcoming Appointment</h3>
                <div class="detail-row">
                    <span class="detail-label">Date:</span>
                    <span class="detail-value">{appointment_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Time:</span>
                    <span class="detail-value">{appointment_time}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Provider:</span>
                    <span class="detail-value">{doctor_name}</span>
                </div>
            </div>
            
            <p>If you have any questions about completing these forms, please call us at <strong>{clinic_phone}</strong>.</p>
            
            <p>Thank you for choosing {clinic_name}. We look forward to providing you with excellent care!</p>
        </div>
        
        <div class="footer">
            <p><strong>{clinic_name}</strong><br>
            {clinic_address}<br>
            Phone: {clinic_phone} | Email: {clinic_email}</p>
        </div>
    </div>
</body>
</html>
""".replace("{css}", EMAIL_CSS)

# ============================================================================
# EMAIL TEMPLATE ENGINE CLASS
# ============================================================================

class EmailTemplateEngine:
    """
    Comprehensive email template engine for medical appointment communications.
    """
    
    def __init__(self):
        """Initialize the email template engine."""
        self.templates = {
            'confirmation_html': CONFIRMATION_EMAIL_HTML,
            'confirmation_text': CONFIRMATION_EMAIL_TEXT,
            'reminder_24hr_html': REMINDER_EMAIL_HTML_24HR,
            'reminder_4hr_html': REMINDER_EMAIL_HTML_4HR,
            'reminder_1hr_html': REMINDER_EMAIL_HTML_1HR,
            'form_distribution_html': FORM_DISTRIBUTION_EMAIL_HTML
        }
        
        # Default clinic information
        self.default_clinic_info = {
            'clinic_name': 'MediCare Allergy & Wellness Center',
            'clinic_address': '456 Healthcare Boulevard, Suite 300',
            'clinic_phone': '(555) 123-4567',
            'clinic_email': 'appointments@medicare-wellness.com',
            'clinic_website': 'www.medicare-wellness.com',
            'patient_portal_url': 'https://patient-portal.medicare-wellness.com'
        }
    
    def generate_confirmation_email(self, appointment_details: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Generate appointment confirmation email content.
        
        Args:
            appointment_details: Dictionary containing appointment information
            
        Returns:
            Tuple of (subject, text_body, html_body)
        """
        try:
            # Merge appointment details with default clinic info
            template_vars = {**self.default_clinic_info, **appointment_details}
            
            # Add new patient specific instructions
            if appointment_details.get('patient_type') == 'new':
                template_vars['new_patient_instructions'] = '<li><strong>New patients:</strong> Complete attached intake forms before your visit</li>'
                template_vars['new_patient_instructions_text'] = '• New patients: Complete attached intake forms before your visit'
            else:
                template_vars['new_patient_instructions'] = ''
                template_vars['new_patient_instructions_text'] = ''
            
            # Generate subject line
            subject = f"Appointment Confirmed - {template_vars.get('appointment_date', 'TBD')} at {template_vars.get('appointment_time', 'TBD')}"
            
            # Generate text and HTML content
            text_body = self.templates['confirmation_text'].format(**template_vars)
            html_body = self.templates['confirmation_html'].format(**template_vars)
            
            return subject, text_body, html_body
            
        except Exception as e:
            logger.error(f"Error generating confirmation email: {str(e)}")
            return self._generate_fallback_confirmation(appointment_details)
    
    def generate_reminder_email(self, appointment_details: Dict[str, Any], reminder_type: str) -> Tuple[str, str, str]:
        """
        Generate appointment reminder email content.
        
        Args:
            appointment_details: Dictionary containing appointment information
            reminder_type: Type of reminder ('24_hour', '4_hour', '1_hour')
            
        Returns:
            Tuple of (subject, text_body, html_body)
        """
        try:
            template_vars = {**self.default_clinic_info, **appointment_details}
            
            # Select appropriate template
            template_map = {
                '24_hour': ('reminder_24hr_html', 'Appointment Reminder - Tomorrow'),
                '4_hour': ('reminder_4hr_html', 'Your Appointment is in 4 Hours'),
                '1_hour': ('reminder_1hr_html', 'FINAL REMINDER - Your Appointment is in 1 Hour')
            }
            
            template_key, subject_prefix = template_map.get(reminder_type, template_map['24_hour'])
            
            subject = f"{subject_prefix} - {template_vars.get('appointment_date', 'TBD')}"
            html_body = self.templates[template_key].format(**template_vars)
            
            # Generate simple text version
            text_body = self._generate_reminder_text(template_vars, reminder_type)
            
            return subject, text_body, html_body
            
        except Exception as e:
            logger.error(f"Error generating reminder email: {str(e)}")
            return self._generate_fallback_reminder(appointment_details, reminder_type)
    
    def generate_form_distribution_email(self, appointment_details: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Generate form distribution email for new patients.
        
        Args:
            appointment_details: Dictionary containing appointment information
            
        Returns:
            Tuple of (subject, text_body, html_body)
        """
        try:
            template_vars = {**self.default_clinic_info, **appointment_details}
            
            subject = f"Patient Intake Forms - {template_vars.get('clinic_name', 'MediCare')}"
            html_body = self.templates['form_distribution_html'].format(**template_vars)
            
            # Generate simple text version
            text_body = self._generate_form_distribution_text(template_vars)
            
            return subject, text_body, html_body
            
        except Exception as e:
            logger.error(f"Error generating form distribution email: {str(e)}")
            return self._generate_fallback_form_email(appointment_details)
    
    def _generate_reminder_text(self, template_vars: Dict[str, Any], reminder_type: str) -> str:
        """Generate plain text reminder email."""
        reminders = {
            '24_hour': f"""
APPOINTMENT REMINDER - {template_vars['clinic_name']}

Dear {template_vars.get('patient_name', 'Patient')},

This is a friendly reminder that you have an appointment TOMORROW:

Date: {template_vars.get('appointment_date', 'TBD')}
Time: {template_vars.get('appointment_time', 'TBD')}
Provider: {template_vars.get('doctor_name', 'TBD')}

Location: {template_vars['clinic_address']}

Please remember to:
• Arrive 15 minutes early
• Bring your insurance card and ID
• Complete any required forms

If you need to cancel or reschedule, please call {template_vars['clinic_phone']}.

We look forward to seeing you tomorrow!

{template_vars['clinic_name']}
{template_vars['clinic_phone']}
            """,
            '4_hour': f"""
APPOINTMENT TODAY - {template_vars['clinic_name']}

Dear {template_vars.get('patient_name', 'Patient')},

Your appointment is in 4 HOURS at {template_vars.get('appointment_time', 'TBD')} with {template_vars.get('doctor_name', 'TBD')}.

PLEASE CONFIRM by replying "CONFIRMED" or calling {template_vars['clinic_phone']}.

Have you completed your intake forms? If not, please complete them now.

If you cannot attend, please call IMMEDIATELY to avoid charges.

{template_vars['clinic_name']}
{template_vars['clinic_phone']}
            """,
            '1_hour': f"""
FINAL REMINDER - {template_vars['clinic_name']}

Dear {template_vars.get('patient_name', 'Patient')},

FINAL REMINDER: Your appointment is in 1 HOUR at {template_vars.get('appointment_time', 'TBD')} with {template_vars.get('doctor_name', 'TBD')}.

URGENT: Please confirm by replying "YES" or calling {template_vars['clinic_phone']} NOW.

If you cannot attend, call immediately to avoid charges.

We're expecting you in 1 hour!

{template_vars['clinic_name']}
Emergency: {template_vars['clinic_phone']}
            """
        }
        
        return reminders.get(reminder_type, reminders['24_hour']).strip()
    
    def _generate_form_distribution_text(self, template_vars: Dict[str, Any]) -> str:
        """Generate plain text form distribution email."""
        return f"""
PATIENT INTAKE FORMS - {template_vars['clinic_name']}

Dear {template_vars.get('patient_name', 'Patient')},

As a new patient, please complete the attached intake forms before your appointment on {template_vars.get('appointment_date', 'TBD')} at {template_vars.get('appointment_time', 'TBD')}.

REQUIRED FORMS:
• New Patient Intake Form
• Medical History Form  
• Insurance Information Form
• Allergy & Wellness Form

INSTRUCTIONS:
Complete forms at least 24 hours before your appointment.

You can:
• Fill out attached forms and bring them
• Complete online at: {template_vars['patient_portal_url']}
• Arrive 30 minutes early to complete at our office

YOUR APPOINTMENT:
Date: {template_vars.get('appointment_date', 'TBD')}
Time: {template_vars.get('appointment_time', 'TBD')}
Provider: {template_vars.get('doctor_name', 'TBD')}

Questions? Call {template_vars['clinic_phone']}

Thank you for choosing {template_vars['clinic_name']}!

{template_vars['clinic_name']}
{template_vars['clinic_address']}
{template_vars['clinic_phone']}
        """.strip()
    
    def _generate_fallback_confirmation(self, appointment_details: Dict[str, Any]) -> Tuple[str, str, str]:
        """Generate simple fallback confirmation email."""
        patient_name = appointment_details.get('patient_name', 'Patient')
        appointment_date = appointment_details.get('appointment_date', 'TBD')
        appointment_time = appointment_details.get('appointment_time', 'TBD')
        
        subject = f"Appointment Confirmed - {appointment_date}"
        
        text_body = f"""
Dear {patient_name},

Your appointment has been confirmed for {appointment_date} at {appointment_time}.

Please arrive 15 minutes early and bring your insurance card and ID.

If you need to make changes, please call (555) 123-4567.

Thank you!
MediCare Allergy & Wellness Center
        """.strip()
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
        <h2>Appointment Confirmed!</h2>
        <p>Dear <strong>{patient_name}</strong>,</p>
        <p>Your appointment has been confirmed for {appointment_date} at {appointment_time}.</p>
        <p>Please arrive 15 minutes early and bring your insurance card and ID.</p>
        <p>If you need to make changes, please call (555) 123-4567.</p>
        <p>Thank you!<br>MediCare Allergy & Wellness Center</p>
        </body>
        </html>
        """
        
        return subject, text_body, html_body
    
    def _generate_fallback_reminder(self, appointment_details: Dict[str, Any], reminder_type: str) -> Tuple[str, str, str]:
        """Generate simple fallback reminder email."""
        patient_name = appointment_details.get('patient_name', 'Patient')
        appointment_time = appointment_details.get('appointment_time', 'TBD')
        
        subject = f"Appointment Reminder - {reminder_type}"
        
        text_body = f"""
Dear {patient_name},

Reminder: Your appointment is scheduled for {appointment_time}.

Please confirm your attendance by calling (555) 123-4567.

MediCare Allergy & Wellness Center
        """.strip()
        
        html_body = f"<html><body><h2>Appointment Reminder</h2><p>{text_body}</p></body></html>"
        
        return subject, text_body, html_body
    
    def _generate_fallback_form_email(self, appointment_details: Dict[str, Any]) -> Tuple[str, str, str]:
        """Generate simple fallback form distribution email."""
        patient_name = appointment_details.get('patient_name', 'Patient')
        
        subject = "Patient Intake Forms Required"
        
        text_body = f"""
Dear {patient_name},

Please complete the attached patient intake forms before your appointment.

Thank you!
MediCare Allergy & Wellness Center
        """.strip()
        
        html_body = f"<html><body><h2>Patient Forms</h2><p>{text_body}</p></body></html>"
        
        return subject, text_body, html_body

# ============================================================================
# CONVENIENCE FUNCTIONS FOR LANGGRAPH INTEGRATION
# ============================================================================

def get_email_template(template_type: str, appointment_details: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Get email template content for the specified type.
    
    Args:
        template_type: Type of email ('confirmation', 'reminder_24hr', 'reminder_4hr', 'reminder_1hr', 'forms')
        appointment_details: Appointment information
        
    Returns:
        Tuple of (subject, text_body, html_body)
    """
    engine = EmailTemplateEngine()
    
    if template_type == 'confirmation':
        return engine.generate_confirmation_email(appointment_details)
    elif template_type in ['reminder_24hr', 'reminder_4hr', 'reminder_1hr']:
        reminder_type = template_type.replace('reminder_', '').replace('hr', '_hour')
        return engine.generate_reminder_email(appointment_details, reminder_type)
    elif template_type == 'forms':
        return engine.generate_form_distribution_email(appointment_details)
    else:
        logger.error(f"Unknown template type: {template_type}")
        return engine._generate_fallback_confirmation(appointment_details)

def render_email_template(template_name: str, **kwargs) -> str:
    """
    Render email template with provided variables.
    
    Args:
        template_name: Name of the template
        **kwargs: Template variables
        
    Returns:
        Rendered template string
    """
    try:
        engine = EmailTemplateEngine()
        template_content = engine.templates.get(template_name, '')
        
        if not template_content:
            logger.error(f"Template not found: {template_name}")
            return ""
        
        # Merge with default clinic info
        template_vars = {**engine.default_clinic_info, **kwargs}
        
        return template_content.format(**template_vars)
        
    except Exception as e:
        logger.error(f"Error rendering template {template_name}: {str(e)}")
        return ""

def create_personalized_email(patient_details: Dict[str, Any], email_type: str) -> Tuple[str, str, str]:
    """
    Create personalized email content for a patient.
    
    Args:
        patient_details: Patient and appointment information
        email_type: Type of email to create
        
    Returns:
        Tuple of (subject, text_body, html_body)
    """
    try:
        return get_email_template(email_type, patient_details)
    except Exception as e:
        logger.error(f"Error creating personalized email: {str(e)}")
        return "Email Error", "Unable to generate email content", "<html><body>Email generation failed</body></html>"

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_email_templates():
    """Test function to validate email template generation."""
    
    print("Testing Email Template System")
    print("=" * 50)
    
    # Test data
    test_appointment = {
        'patient_name': 'John Test Patient',
        'patient_type': 'new',
        'appointment_date': '09/15/2025',
        'appointment_time': '10:00 AM',
        'appointment_duration': 60,
        'doctor_name': 'Dr. Johnson',
        'doctor_specialty': 'Family Medicine',
        'confirmation_id': 'TEST-123456'
    }
    
    engine = EmailTemplateEngine()
    
    # Test confirmation email
    print("\n1. Testing Confirmation Email:")
    subject, text, html = engine.generate_confirmation_email(test_appointment)
    print(f"✅ Subject: {subject}")
    print(f"✅ Text length: {len(text)} characters")
    print(f"✅ HTML length: {len(html)} characters")
    
    # Test reminder emails
    print("\n2. Testing Reminder Emails:")
    for reminder_type in ['24_hour', '4_hour', '1_hour']:
        subject, text, html = engine.generate_reminder_email(test_appointment, reminder_type)
        print(f"✅ {reminder_type} reminder generated - Subject: {subject}")
    
    # Test form distribution
    print("\n3. Testing Form Distribution:")
    subject, text, html = engine.generate_form_distribution_email(test_appointment)
    print(f"✅ Forms email generated - Subject: {subject}")
    
    print("\n" + "=" * 50)
    print("Email template system test completed!")

if __name__ == "__main__":
    # Run tests when executed directly
    test_email_templates()
